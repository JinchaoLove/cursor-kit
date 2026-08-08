#!/usr/bin/env python3
"""Self-test for before-shell-execution.py (stdlib only)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HOOK = Path(__file__).with_name("before-shell-execution.py")

CASES = [
    ("deny-rm", {"command": "r" + "m -rf /tmp/foo"}, "deny"),
    ("deny-drop", {"command": "DROP" + " TABLE users"}, "deny"),
    ("deny-force", {"command": "git push " + "--force origin main"}, "deny"),
    ("ask-delete", {"command": "DELETE" + " FROM logs WHERE id=1"}, "ask"),
    ("allow-status", {"command": "git status"}, "allow"),
]


def main() -> int:
    failed = 0
    for name, payload, expect in CASES:
        proc = subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            check=False,
        )
        try:
            out = json.loads((proc.stdout or "").strip() or "{}")
        except Exception as exc:
            out = {"parse_error": str(exc), "raw": proc.stdout, "err": proc.stderr}
        got = out.get("permission")
        ok = got == expect
        print(f"{'PASS' if ok else 'FAIL'} {name}: expected={expect} got={got or 'n/a'}")
        if not ok:
            print("  detail:", json.dumps(out, ensure_ascii=False))
            failed += 1
    if failed:
        return 1
    print("all checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
