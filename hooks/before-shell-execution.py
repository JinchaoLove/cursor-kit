#!/usr/bin/env python3
"""Cursor beforeShellExecution security gate (stdlib only).

Based on: https://mdnice.com/writing/84654a4a7ff2409d92bea1ffb50261f3
Protocol: JSON on stdin → JSON on stdout
"""

from __future__ import annotations

import json
import re
import sys

DANGEROUS = [
    (re.compile(r"rm\s+-[rRf]"), "递归强制删除，危险操作"),
    (re.compile(r"DROP\s+TABLE", re.I), "删除数据表，高危"),
    (re.compile(r"DROP\s+DATABASE", re.I), "删除数据库，高危"),
    (re.compile(r"TRUNCATE", re.I), "清空表数据，不可逆"),
    (re.compile(r"DELETE\s+FROM\s+\w+\s+WHERE\s*1\s*=\s*1", re.I), "无条件删除全表"),
    (re.compile(r"DELETE\s+FROM\s+\w+\s*;?\s*$", re.I), "无 WHERE 的 DELETE，高危"),
    (re.compile(r"git\s+push\s+.*--force", re.I), "强制推送，可能覆盖远程"),
    (re.compile(r"git\s+push\s+-f\b", re.I), "强制推送，可能覆盖远程"),
    (re.compile(r"chmod\s+777", re.I), "权限全开，安全风险"),
    (re.compile(r"format\s+\w+:", re.I), "格式化操作，危险"),
    (re.compile(r"\bdd\s+if=", re.I), "磁盘写入操作，危险"),
    (re.compile(r"\bmkfs\b", re.I), "格式化文件系统，危险"),
]

ASK = [
    (re.compile(r"DELETE\s+FROM", re.I), "删除操作，请确认"),
    (re.compile(r"UPDATE\s+\w+\s+SET", re.I), "更新操作，请确认"),
    (re.compile(r"git\s+reset\s+--hard", re.I), "硬重置，会丢失更改"),
]


def respond(payload: dict) -> None:
    sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")


def main() -> None:
    try:
        raw = sys.stdin.read() or "{}"
        data = json.loads(raw)
    except Exception:
        respond(
            {
                "permission": "deny",
                "user_message": "安全 hook 无法解析输入，已拒绝执行",
                "agent_message": "beforeShellExecution hook failed to parse input; command denied",
            }
        )
        return

    command = str(data.get("command") or "")

    for pattern, reason in DANGEROUS:
        if pattern.search(command):
            respond(
                {
                    "permission": "deny",
                    "user_message": f"🚫 危险命令被拦截：{reason}\n命令：{command}",
                    "agent_message": f"操作被安全策略拦截：{reason}。请改用更安全的方式完成任务。",
                }
            )
            return

    for pattern, reason in ASK:
        if pattern.search(command):
            respond(
                {
                    "permission": "ask",
                    "user_message": f"⚠️ 需要确认：{reason}\n命令：{command}\n允许执行吗？",
                    "agent_message": f"操作需要用户确认：{reason}",
                }
            )
            return

    respond({"permission": "allow"})


if __name__ == "__main__":
    main()
