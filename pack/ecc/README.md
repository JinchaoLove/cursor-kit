# ECC → Cursor 精简映射包

从 [affaan-m/ECC](https://github.com/affaan-m/ECC) 抽取并适配到 Cursor 的最小有用子集。

本地 ECC 源码克隆（可选参考）：`/Users/lijinchao/Projects/ECC`  
完整上游：<https://github.com/affaan-m/ECC>

## 已安装内容

| 能力 | Cursor 落点 |
|------|-------------|
| 技能路由 | `.cursor/skills/ecc-hub` |
| 研究优先开发 | `ecc-search-first` + rule `ecc-research-first.mdc` |
| 本能 / 持续学习 | `ecc-instincts` + `sessionStart`/`stop` hooks |
| 记忆优化 | `ecc-memory` + `.cursor/ecc/memory/` |
| 安全扫描 | `ecc-security-scan`（AgentShield）+ `ecc-security-baseline.mdc` |
| 上下文预算 | `ecc-context-budget` |
| 危险 Shell 硬拦截 | 已有 `before-shell-execution.js`（与本包并存） |

## 启用

1. `Cmd+Shift+P` → **Developer: Reload Window**
2. **Cursor Settings → Hooks** 确认：`beforeShellExecution` / `sessionStart` / `stop`
3. 对话里可说：`用 ecc-hub`、`学习本会话`、`安全扫描`、`上下文预算`

## 可选增强

```bash
# 完整跨 harness 记忆库
npm install -g ecc-universal

# 配置安全扫描
npx ecc-agentshield scan
```

## 刻意未全量安装

- 数百个框架专属 skills（Django/Laravel/…）
- Claude `/plugin` 市场与 multi-* / ccg-workflow
- ECC 完整 homunculus 观察守护进程

需要时再从 `Projects/ECC/skills/` 按需拷贝单个 skill，并改成 Cursor `SKILL.md` frontmatter。

## 数据目录

```
.cursor/ecc/
  instincts/      # 确认后写入的本能
  memory/project/ # 项目记忆
  sessions/       # stop hook 自动摘要（建议 gitignore）
```
