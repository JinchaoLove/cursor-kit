#!/bin/bash
# Cursor Agent CLI installer (dev-machine / headless friendly)
# Pattern aligned with install-mf.sh: proxy + PATH + BROWSER=echo
#
# Also installs this repo's skills/rules/hooks into ~/.cursor via install.sh.
# Cursor only loads from ~/.cursor (and project ./.cursor) — you cannot point
# it at this repo path as a drop-in ~/.cursor. Symlinks are unreliable for
# skill discovery; copy/sync via install.sh is the supported path.
# Skip kit sync: SKIP_KIT_INSTALL=1 ./install-cc.sh
# Pre-downloaded installer: CC_INSTALL_SCRIPT=/path/to/cursor-install.sh
#   (default cache: <repo>/.cache/cursor-install.sh; delete it to re-fetch)
# Autonomous hooks (opt-in): AUTONOMOUS_HOOKS=1 ./install-cc.sh
# Force re-sync of skills/rules/hooks: -f / --force (shorthand for FORCE_KIT_INSTALL=1)

set -e

for arg in "$@"; do
    case "$arg" in
        -f|--force) export FORCE_KIT_INSTALL=1 ;;
    esac
done

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Config/skills dir for the Cursor CLI. Defaults to <repo parent>/.cursor because
# ~/.cursor lives on a read-only ceph mount here, so both the kit rsync and the
# CLI's own state writes (projects/, chats/) fail with EROFS / Read-only fs.
# The CLI honours CURSOR_CONFIG_DIR, so agent-proxy exports it too.
#
# IMPORTANT: this dir is namespaced by hostname. When several machines share
# the same ceph parent dir, a flat <repo parent>/.cursor is written
# concurrently by every machine's chats/*.db (SQLite) and corrupts with
# "database disk image is malformed". Keeping state under
# .cursor-hosts/<hostname> gives every machine its own writable tree (still
# on ceph, but no longer shared file-for-file) while skills/rules/hooks stay
# in sync per host via the normal install.sh copy.
HOST_TAG="$(hostname -s 2>/dev/null || hostname 2>/dev/null || echo unknown-host)"
KIT_DEST="${CURSOR_KIT_DEST:-$(cd "${ROOT}/.." && pwd)/.cursor-hosts/${HOST_TAG}}"
export CURSOR_KIT_DEST="$KIT_DEST"

# One-time migration: if the old flat shared dir exists and this host's dir
# is new, carry over auth/config so you don't have to log in again. Chat
# history/state is intentionally NOT migrated (it's what was corrupting).
LEGACY_KIT_DEST="$(cd "${ROOT}/.." && pwd)/.cursor"
if [ -d "$LEGACY_KIT_DEST" ] && [ ! -e "$KIT_DEST" ] && [ "$LEGACY_KIT_DEST" != "$KIT_DEST" ]; then
    echo "Migrating auth/config from legacy shared dir -> ${KIT_DEST}"
    mkdir -p "$KIT_DEST"
    for f in auth.json cli-config.json; do
        [ -f "${LEGACY_KIT_DEST}/${f}" ] && cp -a "${LEGACY_KIT_DEST}/${f}" "${KIT_DEST}/${f}"
    done
fi

PROXY_HOST=oversea-squid4.sgp.txyun
PROXY_PORT=11080

export http_proxy=http://${PROXY_HOST}:${PROXY_PORT}
export https_proxy=http://${PROXY_HOST}:${PROXY_PORT}
export no_proxy=localhost,127.0.0.1,localaddress,localdomain.com,internal,corp.kuaishou.com,test.gifshow.com,staging.kuaishou.com

profile_file="${HOME}/.bashrc"
pc_conf="${HOME}/.proxychains-cursor.conf"
wrapper="${HOME}/.local/bin/agent-proxy"

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Debian's ~/.bashrc starts with `[ -z "$PS1" ] && return`, so anything appended
# at the end never runs in non-interactive shells. Prepend instead.
prepend_profile() {
    local marker="$1" block="$2"
    grep -q "$marker" "$profile_file" 2>/dev/null && return 1
    local tmp
    tmp=$(mktemp)
    printf '%s\n' "$block" > "$tmp"
    [ -f "$profile_file" ] && cat "$profile_file" >> "$tmp"
    cat "$tmp" > "$profile_file"
    rm -f "$tmp"
}

echo "=========================================="
echo "   Cursor Agent CLI Installation"
echo "=========================================="
echo ""

# Pre-downloaded installer wins; otherwise fetch once and cache it for re-runs.
install_script="${CC_INSTALL_SCRIPT:-${ROOT}/.cache/cursor-install.sh}"
if [ -s "$install_script" ]; then
    echo "Using cached installer: $install_script"
else
    mkdir -p "$(dirname "$install_script")"
    curl https://cursor.com/install -fsS -o "$install_script"
    echo "Downloaded installer -> $install_script"
fi
bash "$install_script"

# Ensure ~/.local/bin is on PATH (idempotent)
if prepend_profile 'install-cc.sh: PATH' '# Cursor Agent CLI (added by install-cc.sh: PATH)
export PATH="$HOME/.local/bin:$PATH"'; then
    echo "Added ~/.local/bin to PATH in $profile_file"
fi
export PATH="$HOME/.local/bin:$PATH"

# Same headless fix as install-mf.sh:
# without DISPLAY, xdg-open may invoke lynx/w3m and hang the CLI login.
if [ "$(uname -s)" = "Linux" ] && [ -z "${DISPLAY:-}" ]; then
    if command_exists xdg-open && (command_exists lynx || command_exists w3m || command_exists links || command_exists elinks); then
        if prepend_profile 'BROWSER=echo' '# Prevent xdg-open from hanging on headless servers (added by install-cc.sh)
export BROWSER=echo'; then
            echo "Detected headless Linux with text browser — set BROWSER=echo in $profile_file"
        fi
        export BROWSER=echo
    fi
fi

# Persist proxy for later agent sessions (idempotent)
if prepend_profile "${PROXY_HOST}:${PROXY_PORT}" "# Outbound proxy for Cursor / external HTTPS (added by install-cc.sh)
export http_proxy=http://${PROXY_HOST}:${PROXY_PORT}
export https_proxy=http://${PROXY_HOST}:${PROXY_PORT}
export no_proxy=${no_proxy}"; then
    echo "Added proxy exports to $profile_file"
fi

# Agent/Chat requests use a separate HTTP/2 transport that ignores http_proxy,
# so they fail with "Error: [unavailable]". proxychains hooks connect() and
# forces every TCP connection through the proxy, which covers that path too.
setup_proxychains() {
    if ! command_exists proxychains4; then
        echo "Installing proxychains4..."
        local sudo_cmd=""
        [ "$(id -u)" -ne 0 ] && sudo_cmd="sudo"
        # A fresh container has no package lists, so a bare install fails with
        # "Unable to locate package" — always update first.
        if ! ($sudo_cmd apt-get update && $sudo_cmd apt-get install -y proxychains4); then
            echo "ERROR: could not install proxychains4 — 'agent' would fail with [unavailable]"
            exit 1
        fi
    fi

    # proxychains only accepts an IP in [ProxyList], not a hostname.
    local proxy_ip
    proxy_ip=$(getent hosts "$PROXY_HOST" 2>/dev/null | awk '{print $1; exit}')
    if [ -z "$proxy_ip" ]; then
        echo "WARNING: cannot resolve $PROXY_HOST — skipping proxychains setup"
        return 1
    fi

    cat > "$pc_conf" << EOF
strict_chain
quiet_mode
proxy_dns
tcp_read_time_out 15000
tcp_connect_time_out 8000
[ProxyList]
http ${proxy_ip} ${PROXY_PORT}
EOF
    echo "Wrote $pc_conf ($PROXY_HOST -> $proxy_ip:$PROXY_PORT)"

    # A wrapper script (not an alias) so non-interactive shells, scripts and
    # editor-spawned processes go through the proxy too.
    mkdir -p "$(dirname "$wrapper")"
    cat > "$wrapper" << EOF
#!/bin/bash
# http_proxy on top of proxychains double-proxies and fails; proxychains alone is enough.
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
# quiet_mode in the config is parsed too late to suppress the per-child
# "[proxychains] DLL init" banner; this env var is checked first.
export PROXYCHAINS_QUIET_MODE=1
# ~/.cursor is read-only on this host; keep CLI state on a writable path.
export CURSOR_CONFIG_DIR="${KIT_DEST}"
exec proxychains4 -f ${pc_conf} "\${HOME}/.local/bin/agent" "\$@"
EOF
    chmod +x "$wrapper"
    echo "Wrote $wrapper"

    if ! grep -q "alias app=" "$profile_file" 2>/dev/null; then
        cat >> "$profile_file" << 'EOF'

# Shorthand for the proxied Cursor Agent (added by install-cc.sh)
alias app='agent-proxy'
EOF
        echo "Added 'app' alias to $profile_file"
    fi
}

setup_proxychains || true

install_cursor_kit() {
    if [ "${SKIP_KIT_INSTALL:-0}" = "1" ]; then
        echo "SKIP_KIT_INSTALL=1 - skipped cursor-kit -> ${KIT_DEST}"
        return 0
    fi
    if [ -d "${KIT_DEST}/skills" ] && [ "${FORCE_KIT_INSTALL:-0}" != "1" ]; then
        echo "cursor-kit already present at ${KIT_DEST} - skipped (FORCE_KIT_INSTALL=1 to re-sync)"
        return 0
    fi
    if [ ! -w "$(dirname "${KIT_DEST}")" ]; then
        echo "WARNING: $(dirname "${KIT_DEST}") is not writable - skills not installed"
        return 1
    fi
    if [ ! -x "${ROOT}/install.sh" ]; then
        echo "WARNING: ${ROOT}/install.sh missing — skills not installed"
        return 1
    fi
    echo ""
    echo "=========================================="
    echo "   Installing cursor-kit -> ${KIT_DEST}"
    echo "=========================================="
    # --force keeps skills (e.g. agent-wake-poll) in sync with this checkout
    # Autonomous hooks only when explicitly requested: AUTONOMOUS_HOOKS=1
    local kit_args=(--global --force)
    if [ "${AUTONOMOUS_HOOKS:-0}" = "1" ]; then
        kit_args+=(--autonomous)
    fi
    bash "${ROOT}/install.sh" "${kit_args[@]}"
}

install_cursor_kit || true

source "$profile_file" || true

echo ""
echo "=========================================="
echo "Cursor installed successfully!"
echo "=========================================="
echo ""
echo "  source ~/.bashrc   # needed if you ran this with 'bash', not 'source'"
echo "  agent-proxy login"
echo "  agent-proxy"
echo ""
echo "On headless machines: open the printed URL in your laptop browser."
echo "Use 'agent-proxy' to run under proxychains4; plain 'agent' bypasses it."
echo ""
echo "Skills/rules/hooks: ${KIT_DEST} (synced from ${ROOT}/pack)."
echo "  Re-sync: FORCE_KIT_INSTALL=1 ${ROOT}/install-cc.sh  (override dir: CURSOR_KIT_DEST=...)"
echo "  Autonomous hooks (opt-in): AUTONOMOUS_HOOKS=1 ./install-cc.sh"
echo "  Skip on next install-cc: SKIP_KIT_INSTALL=1"
echo ""
