#!/usr/bin/env node
/**
 * Cursor beforeShellExecution security gate
 * Based on: 别让 Cursor 删库跑路：50 行脚本锁死 AI 的“危险权限”
 * https://mdnice.com/writing/84654a4a7ff2409d92bea1ffb50261f3
 *
 * Protocol: JSON in via stdin, JSON out via stdout
 * (adapted from the article's export-default example to current Cursor hooks API)
 */

const fs = require("fs");

const dangerousPatterns = [
  { pattern: /rm\s+-[rRf]/, reason: "递归强制删除，危险操作" },
  { pattern: /DROP\s+TABLE/i, reason: "删除数据表，高危" },
  { pattern: /DROP\s+DATABASE/i, reason: "删除数据库，高危" },
  { pattern: /TRUNCATE/i, reason: "清空表数据，不可逆" },
  { pattern: /DELETE\s+FROM\s+\w+\s+WHERE\s*1\s*=\s*1/i, reason: "无条件删除全表" },
  { pattern: /DELETE\s+FROM\s+\w+\s*;?\s*$/i, reason: "无 WHERE 的 DELETE，高危" },
  { pattern: /git\s+push\s+.*--force/i, reason: "强制推送，可能覆盖远程" },
  { pattern: /git\s+push\s+-f\b/i, reason: "强制推送，可能覆盖远程" },
  { pattern: /chmod\s+777/i, reason: "权限全开，安全风险" },
  { pattern: /format\s+\w+:/i, reason: "格式化操作，危险" },
  { pattern: /\bdd\s+if=/i, reason: "磁盘写入操作，危险" },
  { pattern: /\bmkfs\b/i, reason: "格式化文件系统，危险" },
];

const askPatterns = [
  { pattern: /DELETE\s+FROM/i, reason: "删除操作，请确认" },
  { pattern: /UPDATE\s+\w+\s+SET/i, reason: "更新操作，请确认" },
  { pattern: /git\s+reset\s+--hard/i, reason: "硬重置，会丢失更改" },
];

function respond(payload) {
  process.stdout.write(JSON.stringify(payload) + "\n");
}

function main() {
  let input;
  try {
    input = JSON.parse(fs.readFileSync(0, "utf8") || "{}");
  } catch (err) {
    // Fail closed for security gates
    respond({
      permission: "deny",
      user_message: "安全 hook 无法解析输入，已拒绝执行",
      agent_message:
        "beforeShellExecution hook failed to parse input; command denied",
    });
    process.exit(0);
  }

  const command = String(input.command || "");

  for (const { pattern, reason } of dangerousPatterns) {
    if (pattern.test(command)) {
      respond({
        permission: "deny",
        user_message: `🚫 危险命令被拦截：${reason}\n命令：${command}`,
        agent_message: `操作被安全策略拦截：${reason}。请改用更安全的方式完成任务。`,
      });
      return;
    }
  }

  for (const { pattern, reason } of askPatterns) {
    if (pattern.test(command)) {
      respond({
        permission: "ask",
        user_message: `⚠️ 需要确认：${reason}\n命令：${command}\n允许执行吗？`,
        agent_message: `操作需要用户确认：${reason}`,
      });
      return;
    }
  }

  respond({ permission: "allow" });
}

main();
