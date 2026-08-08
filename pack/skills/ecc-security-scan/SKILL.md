---
name: ecc-security-scan
description: >-
  Security scan for Cursor/Claude agent configs using AgentShield, plus checks
  for .cursor hooks, MCP, and rules. Use after changing hooks/MCP/settings, or
  for 安全扫描 / AgentShield / config audit.
metadata:
  origin: ECC-security-scan
---

# Security Scan

基于 ECC `security-scan` + [AgentShield](https://www.npmjs.com/package/ecc-agentshield)，并覆盖 Cursor 配置面。

## When

- 新建或克隆带 Agent 配置的仓库后
- 修改了 `.cursor/hooks*`、MCP、rules、skills
- 提交配置变更前
- 定期卫生检查

## Run

```bash
# 快速扫描（推荐）
npx ecc-agentshield scan

# 指定路径（Claude 配置）
npx ecc-agentshield scan --path ~/.claude

# 同时关注 Cursor 工作区
npx ecc-agentshield scan --path .
```

可选：

```bash
npx ecc-agentshield scan --fix
npx ecc-agentshield scan --format markdown
```

## Cursor-specific checklist（Agent 应手动核对）

- [ ] `.cursor/hooks.json` 安全钩子设置了 `failClosed: true`
- [ ] 无把生产密钥写进 rules/skills/memory
- [ ] MCP 数量可控（活动工具不宜过多）
- [ ] `cursor-security-kit` / `before-shell-execution` 仍在拦截高危命令
- [ ] Workspace Trust 已启用（若团队要求）

## Response protocol

发现严重问题时：停止扩大改动 → 汇报等级与路径 → 先修 CRITICAL → 轮换可能泄露的密钥。
