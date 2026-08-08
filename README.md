# cursor-kit

一键配置 Cursor：**技能 + 规则 + Hooks（安全拦截 / 会话记忆）+ ECC 精简数据面**。

包含当前工作区沉淀的整套配置：

- AI 研究技能（`ai-research-hub` 及子技能）
- 工程技能（`project-development`）
- ECC 精简映射（`ecc-hub` / search-first / instincts / memory / security-scan / context-budget）
- Always-on 规则（研究路由、工程路由、research-first、安全基线）
- Shell 危险命令硬拦截 + sessionStart/stop 记忆钩子

## 一键安装

### 全局（推荐，对所有项目生效）

```bash
git clone git@github.com:JinchaoLove/cursor-kit.git
cd cursor-kit
./install.sh --global --with-settings --force
```

HTTPS：

```bash
git clone https://github.com/JinchaoLove/cursor-kit.git
cd cursor-kit
./install.sh --global --with-settings --force
```

### 仅当前项目

```bash
cd /path/to/your/repo
/path/to/cursor-kit/install.sh --project --force
```

### 自测 / 卸载

```bash
./install.sh --test
./install.sh --uninstall            # 只移除本套件管理的 hooks 条目
./install.sh --project --uninstall
```

装完后：`Cmd/Ctrl+Shift+P` → **Developer: Reload Window**。

## 会装到哪里

| 模式 | 目标 |
|------|------|
| `--global` | `~/.cursor/{skills,rules,hooks,ecc,hooks.json}` |
| `--project` | `./.cursor/...` |

默认 **不覆盖** 你已有的同名文件；加 `--force` 才覆盖托管脚本/技能/规则。  
`ecc/instincts` 与 `memory`：缺失才写入种子；`sessions/` 永不从仓库覆盖。

## 包内技能一览

**研究 / 工程**

- `ai-research-hub`、`ai-literature-review`、`ai-frontier-survey`、`paper-lookup`
- `research-plan`、`hypothesis-generation`、`scientific-brainstorming`、`scientific-critical-thinking`
- `project-development`

**ECC 精简**

- `ecc-hub`、`ecc-search-first`、`ecc-instincts`、`ecc-memory`
- `ecc-security-scan`、`ecc-context-budget`

## Hooks

| 事件 | 作用 |
|------|------|
| `beforeShellExecution` | 拦截 `rm -rf` / `DROP` / `git push --force` 等 |
| `sessionStart` | 注入高置信度本能 + 最近会话摘要 |
| `stop` | 写入会话 stub（供「学习本会话」） |

## 依赖

- `bash`
- `python3`（hooks、合并 `hooks.json`、改 settings、自测）
- 可选：`rsync`（更快拷贝）

脚本技能额外依赖见 `pack/skills/*/requirements.txt`（如 `paper-lookup`）。

**不需要 Node.js。** Hooks 已改为标准库 Python，记忆/本能读写也只依赖本地 Markdown + `python3`。

## 目录结构

```
cursor-kit/
├── install.sh
├── hooks/                 # 自测用安全脚本副本
├── templates/             # hooks.global.json / hooks.project.json
├── pack/                  # 实际安装内容（≈ .cursor）
│   ├── skills/
│   ├── rules/
│   ├── hooks/
│   ├── ecc/
│   ├── hooks.json
│   └── README.md
├── LICENSE
└── README.md
```

## 参考与致谢

- **危险命令硬拦截**：思路来自教程 [别让 Cursor 删库跑路：50 行脚本锁死 AI 的危险权限](https://mdnice.com/writing/84654a4a7ff2409d92bea1ffb50261f3)，并适配当前 Cursor Hooks 的 stdin/stdout JSON 协议（见 [Hooks 文档](https://cursor.com/docs/hooks)）。
- **ECC 精简映射**：技能体系、研究优先、本能/持续学习、记忆与安全扫描等，精简改编自 [affaan-m/ECC](https://github.com/affaan-m/ECC)（Everything Claude Code）。本仓库只保留对 Cursor 最有用的一层，并非 ECC 全量安装。

## License

MIT
