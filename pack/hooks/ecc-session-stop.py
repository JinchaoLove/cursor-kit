#!/usr/bin/env python3
"""Cursor stop — write a lightweight session stub (fail-open)."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def main() -> None:
    try:
        data = json.loads(sys.stdin.read() or "{}")
    except Exception:
        data = {}

    workspace_root = Path.cwd()
    roots = data.get("workspace_roots") or []
    if isinstance(roots, list) and roots:
        workspace_root = Path(str(roots[0]))

    try:
        session_dir = workspace_root / ".cursor" / "ecc" / "sessions"
        session_dir.mkdir(parents=True, exist_ok=True)

        ts = datetime.now(timezone.utc)
        stamp = ts.isoformat().replace(":", "-").replace(".", "-")
        path = session_dir / f"{stamp}.md"
        status = data.get("status") or data.get("reason") or "unknown"
        body = "\n".join(
            [
                "---",
                "kind: session-stub",
                f"status: {json.dumps(str(status))}",
                f"created: {ts.isoformat()}",
                "trust: unreviewed",
                "---",
                "",
                "# Session stub",
                "",
                "Auto-saved by `ecc-session-stop` hook.",
                "Say「学习本会话」to extract instincts via `ecc-instincts` (confirm before write).",
                "",
                "## Hook payload (redacted keys only)",
                "",
                f"- status: {status}",
                f"- conversation_id: {data.get('conversation_id') or 'n/a'}",
                "",
            ]
        )
        path.write_text(body, encoding="utf-8")
    except Exception as err:
        sys.stderr.write(f"[ecc-session-stop] {err}\n")

    sys.stdout.write("{}\n")


if __name__ == "__main__":
    main()
