#!/usr/bin/env bash
# cursor-kit — one-click Cursor skills, rules, hooks, and ECC slim data
# Usage:
#   ./install.sh                      # global (~/.cursor)
#   ./install.sh --project            # current repo ./.cursor
#   ./install.sh --global --with-settings
#   ./install.sh --test
#   ./install.sh --uninstall
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACK="${ROOT}/pack"
MODE="global"
WITH_SETTINGS=0
DO_TEST=0
DO_UNINSTALL=0
FORCE=0
SKIP_ECC_DATA=0
HOOKS_PROFILE="default"  # default | autonomous

usage() {
  cat <<'EOF'
cursor-kit installer

Installs the full local Cursor pack:
  - skills/   (research + engineering + ECC slim)
  - rules/    (always-apply routers + ECC baselines)
  - hooks/    (shell security + session memory)
  - ecc/      (instincts/memory layout; preserves your local notes)

Options:
  --global           Install to ~/.cursor (default)
  --project          Install to ./.cursor in the current directory
  --with-settings    Patch Cursor user settings (Workspace Trust + disable auto tasks)
  --force            Overwrite conflicting managed files
  --skip-ecc-data    Do not copy seed instincts/memory (still creates dirs)
  --autonomous       Use hooks.autonomous*.json (deny-only shell gate, failClosed=false; no session hooks)
  --test             Run security hook self-test and exit
  --uninstall        Remove kit-managed hooks entries + optional purge (see below)
  -h, --help         Show help

Examples:
  ./install.sh --global --with-settings
  ./install.sh --global --autonomous --force
  ./install.sh --project --force
  ./install.sh --test
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --global) MODE="global"; shift ;;
    --project) MODE="project"; shift ;;
    --with-settings) WITH_SETTINGS=1; shift ;;
    --force) FORCE=1; shift ;;
    --skip-ecc-data) SKIP_ECC_DATA=1; shift ;;
    --autonomous) HOOKS_PROFILE="autonomous"; shift ;;
    --test) DO_TEST=1; shift ;;
    --uninstall) DO_UNINSTALL=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

need_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

detect_settings_path() {
  case "$(uname -s)" in
    Darwin) echo "${HOME}/Library/Application Support/Cursor/User/settings.json" ;;
    Linux) echo "${HOME}/.config/Cursor/User/settings.json" ;;
    MINGW*|MSYS*|CYGWIN*|Windows_NT) echo "${APPDATA:-}/Cursor/User/settings.json" ;;
    *) echo "${HOME}/.config/Cursor/User/settings.json" ;;
  esac
}

backup_file() {
  local f="$1"
  if [[ -f "$f" ]]; then
    local ts
    ts="$(date +%Y%m%d-%H%M%S)"
    cp "$f" "${f}.bak.${ts}"
    echo "Backup: ${f}.bak.${ts}"
  fi
}

run_test() {
  need_cmd python3
  echo "Running security hook self-test..."
  python3 "${ROOT}/hooks/self-test.py"
}

resolve_targets() {
  if [[ "$MODE" == "global" ]]; then
    # CURSOR_KIT_DEST overrides the default when ~/.cursor is not writable
    # (e.g. a symlink into a read-only network mount).
    DEST_DIR="${CURSOR_KIT_DEST:-${HOME}/.cursor}"
    if [[ "$HOOKS_PROFILE" == "autonomous" ]]; then
      TEMPLATE="${ROOT}/templates/hooks.autonomous.json"
    else
      TEMPLATE="${ROOT}/templates/hooks.global.json"
    fi
  else
    DEST_DIR="$(pwd)/.cursor"
    if [[ "$HOOKS_PROFILE" == "autonomous" ]]; then
      TEMPLATE="${ROOT}/templates/hooks.autonomous.project.json"
    else
      TEMPLATE="${ROOT}/templates/hooks.project.json"
    fi
  fi
  HOOKS_JSON="${DEST_DIR}/hooks.json"
}

copy_dir_merge() {
  local src="$1"
  local dest="$2"
  mkdir -p "$dest"
  if command -v rsync >/dev/null 2>&1; then
    if [[ "$FORCE" -eq 1 ]]; then
      rsync -a "$src/" "$dest/"
    else
      rsync -a --ignore-existing "$src/" "$dest/"
    fi
  else
    # portable fallback
    need_cmd python3
    python3 - "$src" "$dest" "$FORCE" <<'PY'
import os, shutil, sys
src, dest, force = sys.argv[1], sys.argv[2], sys.argv[3] == "1"
for dirpath, _, filenames in os.walk(src):
    rel = os.path.relpath(dirpath, src)
    out = dest if rel == "." else os.path.join(dest, rel)
    os.makedirs(out, exist_ok=True)
    for name in filenames:
        s = os.path.join(dirpath, name)
        d = os.path.join(out, name)
        if os.path.exists(d) and not force:
            continue
        shutil.copy2(s, d)
PY
  fi
}

install_skills_rules_hooks() {
  echo "Installing skills → ${DEST_DIR}/skills"
  copy_dir_merge "${PACK}/skills" "${DEST_DIR}/skills"

  echo "Installing rules → ${DEST_DIR}/rules"
  copy_dir_merge "${PACK}/rules" "${DEST_DIR}/rules"

  echo "Installing hooks scripts → ${DEST_DIR}/hooks"
  mkdir -p "${DEST_DIR}/hooks"
  for f in before-shell-execution.py ecc-session-start.py ecc-session-stop.py self-test.py; do
    if [[ -f "${PACK}/hooks/${f}" ]]; then
      if [[ -f "${DEST_DIR}/hooks/${f}" && "$FORCE" -ne 1 ]]; then
        if ! cmp -s "${PACK}/hooks/${f}" "${DEST_DIR}/hooks/${f}"; then
          echo "Exists (different): ${DEST_DIR}/hooks/${f} (use --force)"
          continue
        fi
      fi
      cp "${PACK}/hooks/${f}" "${DEST_DIR}/hooks/${f}"
      chmod +x "${DEST_DIR}/hooks/${f}" 2>/dev/null || true
    fi
  done
  # Drop legacy Node hook scripts if present (migrated to Python).
  for legacy in before-shell-execution.js ecc-session-start.js ecc-session-stop.js self-test.js; do
    if [[ -f "${DEST_DIR}/hooks/${legacy}" ]]; then
      python3 - "${DEST_DIR}/hooks/${legacy}" <<'PY'
import os, sys
os.remove(sys.argv[1])
print("Removed legacy", sys.argv[1])
PY
    fi
  done
}

install_ecc_data() {
  mkdir -p "${DEST_DIR}/ecc/instincts" "${DEST_DIR}/ecc/memory/project" "${DEST_DIR}/ecc/sessions"
  if [[ -f "${PACK}/ecc/README.md" ]]; then
    cp "${PACK}/ecc/README.md" "${DEST_DIR}/ecc/README.md"
  fi
  if [[ -f "${PACK}/ecc/.gitignore" ]]; then
    cp "${PACK}/ecc/.gitignore" "${DEST_DIR}/ecc/.gitignore"
  fi
  if [[ "$SKIP_ECC_DATA" -eq 1 ]]; then
    echo "Skipped seed ecc data"
    return
  fi
  # Seed instincts only if missing (never clobber user instincts unless --force)
  if [[ -d "${PACK}/ecc/instincts" ]]; then
    copy_dir_merge "${PACK}/ecc/instincts" "${DEST_DIR}/ecc/instincts"
  fi
  if [[ -d "${PACK}/ecc/memory/project" ]]; then
    copy_dir_merge "${PACK}/ecc/memory/project" "${DEST_DIR}/ecc/memory/project"
  fi
  # never sync sessions from pack
}

write_hooks_json() {
  mkdir -p "$(dirname "$HOOKS_JSON")"
  if [[ ! -f "$HOOKS_JSON" ]]; then
    cp "$TEMPLATE" "$HOOKS_JSON"
    echo "Wrote ${HOOKS_JSON}"
    return
  fi
  backup_file "$HOOKS_JSON"
  need_cmd python3
  python3 - "$HOOKS_JSON" "$TEMPLATE" <<'PY'
import json, sys
path, template = sys.argv[1], sys.argv[2]
with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)
with open(template, "r", encoding="utf-8") as f:
    want = json.load(f)
data.setdefault("version", 1)
hooks = data.setdefault("hooks", {})
managed_cmds = set()
for arr in want.get("hooks", {}).values():
    for h in arr:
        if isinstance(h, dict) and h.get("command"):
            managed_cmds.add(h["command"])
            # also match by script basename
            managed_cmds.add(h["command"].split("/")[-1])

def is_managed(h):
    if not isinstance(h, dict):
        return False
    cmd = str(h.get("command", ""))
    base = cmd.split("/")[-1]
    return (
        cmd in managed_cmds
        or base in managed_cmds
        or "before-shell-execution." in base
        or base.startswith("ecc-session-")
    )

for event, want_arr in want.get("hooks", {}).items():
    cur = [h for h in hooks.get(event, []) if not is_managed(h)]
    # append wanted entries
    for h in want_arr:
        cur.append(h)
    hooks[event] = cur

# Drop managed hooks from events absent in the new template
# (e.g. switching to autonomous removes sessionStart/stop).
for event, arr in list(hooks.items()):
    if event in want.get("hooks", {}):
        continue
    kept = [h for h in arr if not is_managed(h)]
    if kept:
        hooks[event] = kept
    else:
        del hooks[event]

data["hooks"] = hooks
with open(path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
    f.write("\n")
print(f"Merged hooks into {path}")
PY
}

patch_settings() {
  local settings
  settings="$(detect_settings_path)"
  mkdir -p "$(dirname "$settings")"
  if [[ ! -f "$settings" ]]; then
    printf '%s\n' '{' \
      '  "security.workspace.trust.enabled": true,' \
      '  "task.allowAutomaticTasks": "off"' \
      '}' > "$settings"
    echo "Created ${settings}"
    return
  fi
  backup_file "$settings"
  need_cmd python3
  python3 - "$settings" <<'PY'
import json, sys
path = sys.argv[1]
raw = open(path, "r", encoding="utf-8").read().splitlines()
lines = [ln for ln in raw if not ln.lstrip().startswith("//")]
text = "\n".join(lines)
data = json.loads(text) if text.strip() else {}
data["security.workspace.trust.enabled"] = True
data["task.allowAutomaticTasks"] = "off"
open(path, "w", encoding="utf-8").write(json.dumps(data, indent=4, ensure_ascii=False) + "\n")
print(f"Patched {path}")
PY
}

uninstall_kit() {
  resolve_targets
  if [[ -f "$HOOKS_JSON" ]]; then
    backup_file "$HOOKS_JSON"
    need_cmd python3
    python3 - "$HOOKS_JSON" "$TEMPLATE" <<'PY'
import json, sys
path, template = sys.argv[1], sys.argv[2]
data = json.load(open(path, encoding="utf-8"))
want = json.load(open(template, encoding="utf-8"))
managed = set()
for arr in want.get("hooks", {}).values():
    for h in arr:
        if isinstance(h, dict) and h.get("command"):
            managed.add(h["command"])
            managed.add(h["command"].split("/")[-1])
hooks = data.get("hooks", {})
for event, arr in list(hooks.items()):
    hooks[event] = [
        h for h in arr
        if not (
            isinstance(h, dict)
            and (
                h.get("command") in managed
                or str(h.get("command", "")).split("/")[-1] in managed
                or "before-shell-execution." in str(h.get("command", ""))
                or "ecc-session-" in str(h.get("command", ""))
            )
        )
    ]
    if not hooks[event]:
        del hooks[event]
data["hooks"] = hooks
json.dump(data, open(path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
open(path, "a", encoding="utf-8").write("\n")
print(f"Removed kit hook entries from {path}")
PY
  fi
  echo "Uninstall removed managed hook entries."
  echo "Skills/rules/ecc data were left in place. Delete ${DEST_DIR}/skills or rules manually if desired."
}

copy_readme() {
  if [[ -f "${PACK}/README.md" ]]; then
    if [[ ! -f "${DEST_DIR}/README.md" || "$FORCE" -eq 1 ]]; then
      cp "${PACK}/README.md" "${DEST_DIR}/README.md"
    fi
  fi
}

main() {
  need_cmd python3
  [[ -d "$PACK" ]] || { echo "Missing pack/ directory" >&2; exit 1; }

  if [[ "$DO_TEST" -eq 1 ]]; then
    run_test
    exit 0
  fi

  if [[ "$DO_UNINSTALL" -eq 1 ]]; then
    uninstall_kit
    exit 0
  fi

  resolve_targets
  echo "Install mode: ${MODE}"
  echo "Destination:  ${DEST_DIR}"
  echo "Hooks profile: ${HOOKS_PROFILE} ($(basename "$TEMPLATE"))"
  mkdir -p "$DEST_DIR"
  install_skills_rules_hooks
  install_ecc_data
  write_hooks_json
  copy_readme

  if [[ "$WITH_SETTINGS" -eq 1 ]]; then
    patch_settings
  fi

  run_test

  cat <<EOF

Done.

Installed into: ${DEST_DIR}
  skills: $(find "${DEST_DIR}/skills" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l | tr -d ' ')
  rules:  $(find "${DEST_DIR}/rules" -maxdepth 1 -name '*.mdc' 2>/dev/null | wc -l | tr -d ' ')
  hooks:  ${HOOKS_JSON}

Next:
  1. Reload Cursor (Cmd/Ctrl+Shift+P → Developer: Reload Window)
  2. Check Settings → Hooks / Rules / Skills
  3. Try: 「用 ecc-hub」 or 「安全扫描」
EOF
}

main
