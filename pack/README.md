# Cursor config: AI research & development skills

Skills + rules for deep AI research and engineering, tuned for **multimodal interaction & generation** (audio-video joint generation, agents, world models). Follows the [Agent Skills](https://agentskills.io/specification) convention (used by Cursor, Claude Code, Codex, etc.) and is modeled on `sanjay3290/ai-skills` and `K-Dense-AI/scientific-agent-skills`.

## Layout

```
.cursor/
├── rules/
│   ├── ai-research.mdc             # routes research tasks → ai-research-hub
│   ├── engineering.mdc             # routes dev tasks → project-development
│   ├── ecc-research-first.mdc      # ECC: search before coding
│   └── ecc-security-baseline.mdc   # ECC: secrets / scan / hooks
├── hooks/                          # security gate + ECC session memory
├── ecc/                            # instincts / memory / sessions (ECC slim)
└── skills/
    ├── ai-research-hub/            # router + shared playbook (start here)
    ├── ai-frontier-survey/         # 前沿技术细节调研 (SOTA dissection)
    ├── ai-literature-review/       # 综述 / systematic synthesis
    ├── paper-lookup/               # multi-API paper/citation search (+ script)
    ├── research-plan/              # 详细研究方案 (+ template)
    ├── hypothesis-generation/      # observations → testable hypotheses
    ├── scientific-brainstorming/   # divergent ideation
    ├── scientific-critical-thinking/  # 批判性分析 / claim vetting
    ├── project-development/        # 开发 / reproducible ML engineering
    ├── keep-it-simple/             # KISS 审计：砍冗余代码与文档
    ├── agent-wake-poll/            # 长任务 one-shot wake 轮询，防 hang
    ├── ecc-hub/                    # ECC Cursor slim router
    ├── ecc-search-first/           # research-before-coding
    ├── ecc-instincts/              # continuous learning / instincts
    ├── ecc-memory/                 # local memory vault
    ├── ecc-security-scan/          # AgentShield + Cursor checklist
    └── ecc-context-budget/         # context / token budget audit
```

See `.cursor/ecc/README.md` for the ECC slim mapping notes.

## Typical flow

brainstorm → frontier survey → literature review → hypothesis → research plan → build → critique. `ai-research-hub/SKILL.md` has the routing table.

## Setup for script-backed skills

```bash
# paper-lookup (no key needed for arXiv/OpenAlex/Crossref)
pip install -r skills/paper-lookup/requirements.txt
```

Optional keys raise limits / unlock features: `SEMANTIC_SCHOLAR_API_KEY`, `OPENALEX_MAILTO` (paper-lookup).
