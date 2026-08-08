---
name: ecc-instincts
description: >-
  Continuous learning / instinct system for Cursor (ECC v2 concepts). Extract
  atomic instincts from corrections and repeated workflows into
  .cursor/ecc/instincts/. Use for 本能, 持续学习, learn from session, evolve habits.
metadata:
  origin: ECC-continuous-learning-v2
  version: "2.1-cursor-slim"
---

# Instincts — 持续学习（Cursor 精简版）

完整 ECC v2 依赖 Claude Code 的 PreToolUse 观察器。本精简版把「本能」落成可审查的 Markdown，由 Agent + session hooks 维护。

## Instinct format

Save under `.cursor/ecc/instincts/<id>.md`:

```markdown
---
id: prefer-functional-style
trigger: "when writing new functions"
confidence: 0.7
domain: code-style
scope: project
---

# Prefer Functional Style

## Action
Prefer functional patterns over classes when appropriate.

## Evidence
- User corrected class-based approach on YYYY-MM-DD
```

**Rules:** 一条本能 = 一个 trigger + 一个 action；`confidence` 0.3–0.9；`domain` 如 code-style / testing / git / debugging / workflow / research。

## When to extract

- 用户纠正了你的做法
- 同一 workaround 出现 ≥2 次
- 调试手法被证明有效
- 项目约定被反复强调

**不要**提取：一次性 typo、外部 API 偶发故障、密钥/隐私内容。

## Commands (natural language)

用户说这些时执行对应动作：

| 说法 | 动作 |
|------|------|
| 学习本会话 / learn session | 读近期对话与 `.cursor/ecc/sessions/`，起草 1–5 条本能，**先给用户确认再写入** |
| 列出本能 / instinct status | 列出 instincts，按 confidence 排序 |
| 进化本能 / evolve | 将同 domain、高置信度本能聚类，提议新的 Cursor skill 草稿（不自动覆盖现有 skill） |
| 导入/导出 | 读写 instincts 目录；导出时去掉证据里的敏感路径 |

## Session hooks

- `sessionStart`：注入 confidence≥0.7 的本能摘要
- `stop`：写入会话 stub 到 `.cursor/ecc/sessions/`（不自动改本能）

## Promotion

`scope: project` 默认。若同一本能在多个项目被验证，再升为 `global` 并复制到 `~/.cursor/ecc/instincts/`（需用户明确同意）。
