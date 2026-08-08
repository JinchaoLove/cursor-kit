---
name: ecc-search-first
description: >-
  Research-before-coding workflow from ECC. Search existing tools, libraries,
  patterns, and skills before writing custom code. Use when adding features,
  dependencies, utilities, or when tempted to build from scratch.
metadata:
  origin: ECC
---

# Search First — 研究优先再动手

改编自 ECC `search-first`，适配 Cursor。

## Trigger

- 新功能很可能已有成熟方案
- 要加依赖 / 集成
- 用户说「加个 X」而你正准备直接写
- 新建 utility / helper / abstraction 之前

## Workflow

1. **Need** — 明确要什么能力、语言/框架约束。
2. **Search in parallel**
   - 仓库：`Grep` / `Glob` / `Task(explore)`
   - 包：npm / PyPI / 项目 package manager
   - 文档：`WebSearch` / `WebFetch` / MCP
   - 本机技能：`.cursor/skills/`（含 `ai-research-hub`、`ecc-*`）
   - GitHub：已登录则用 `gh`；否则公开网页搜索
3. **Evaluate** — 功能匹配、维护、社区、文档、许可证、依赖重量。
4. **Decide**
   - **Adopt** — 直接用
   - **Extend** — 薄封装
   - **Compose** — 组合 2–3 个小件
   - **Build** — 自写，但必须基于调研结论
5. **Implement** — 最小改动；先引用再造轮子。

## AI/ML research tasks

若任务是调研 / 综述 / SOTA / 方案，不要用本 skill 硬套成「找 npm 包」——改走 `ai-research-hub`。

## Output before coding

简短给出：候选方案表（Adopt/Extend/Build）+ 推荐理由 + 将要改的文件范围。用户未反对再动手。
