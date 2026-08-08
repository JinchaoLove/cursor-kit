---
name: ecc-context-budget
description: >-
  Audit Cursor context overhead from skills, rules, MCP, and hooks. Identify
  bloat and recommend cuts. Use when sessions feel slow, after adding many
  skills/MCP, or for 上下文 / token budget / context-budget.
metadata:
  origin: ECC-context-budget
---

# Context Budget — 记忆与上下文优化

改编自 ECC `context-budget` + `strategic-compact`，面向 Cursor。

## Inventory（扫描这些路径）

- `.cursor/skills/*/SKILL.md`
- `.cursor/rules/*.mdc`
- MCP 配置（Cursor 设置 / `mcp.json`）
- `.cursor/hooks.json` 与 hooks 脚本
- 用户规则 / AGENTS.md（若存在）

粗估：英文约 words×1.3 tokens；MCP 每个 tool schema 约 ~500 tokens。

## Classify

| Bucket | Action |
|--------|--------|
| Always needed | 保留（安全 hook、ecc-hub、当前栈规则） |
| Sometimes | 改为按描述触发，勿 alwaysApply |
| Rarely / duplicate | 删除或移出工作区 |

## Red flags

- alwaysApply 规则过多或单文件过长
- 技能 description 含糊导致误触发
- MCP >10 或大量 CLI 包装型 MCP（`gh`/`git`/`npm` 可直接 Shell）
- 与 `ai-research-hub` / `ecc-hub` 重复的路由技能

## Strategic compact（长会话）

在这些边界建议用户开新会话或主动总结压缩：

- 调研结束 → 实现开始
- 一个里程碑完成 → 下一里程碑
- 任务主题切换

压缩前：把要点写入 `.cursor/ecc/memory/project/` 或 instincts，避免只靠对话记忆。

## Report template

```
Context Budget Report
- Skills: N (flag >400 lines)
- Rules alwaysApply: N
- MCP servers/tools: N / M
- Top cuts: ...
- Keep: security hook, ecc-hub, ...
```
