---
name: ai-research-hub
description: Routes AI/ML research tasks to literature review, frontier analysis, hypothesis, planning, critique, or implementation skills. Use for 调研, 综述, SOTA, 研究方案, 假设, 批判性分析, deep research, or technical due diligence.
metadata: {"version": "1.2", "skill-author": "lijinchao, cursor", "domain": "multimodal-generation, av-joint-gen, agents, world-models"}
---

# AI Research Hub

## Routing

- Broad literature landscape or taxonomy → `ai-literature-review`
- Recent SOTA, method dissection, or deep technical report (`technical-analysis.md`) → `ai-frontier-survey`
- Paper/DOI/citation retrieval → `paper-lookup`
- Testable research claims → `hypothesis-generation`
- Executable technical proposal or plan (`research-plan.md`) → `research-plan`
- Claim, metric, or plan review → `scientific-critical-thinking`
- Implementation → `project-development`

For a full project, use:

1. literature review;
2. frontier analysis for a few important anchors;
3. hypothesis and research plan;
4. critique;
5. implementation.

## Project files

Use these top-level Markdown files:

- `README.md` — short index and conclusions;
- `literature-review.md` — breadth: scope, taxonomy, academic/product landscape, evidence limits, references;
- `technical-analysis.md` — depth **report**: how the chosen technology/method actually works — mechanism-level dissection, architecture and information flow, objectives, key technical tradeoffs, and the evidence behind them;
- `research-plan.md` — *(only when a plan is needed)* the executable proposal: what to build, hypothesis, experiments, decision thresholds, roadmap, milestones, and kill criteria.

Keep retrieval logs under `sources/`.

## Breadth vs depth vs plan

- Literature review answers **what exists**. Cover all important families, but keep each system compact.
- Technical analysis answers **how the technology works and why it holds up**. It is a technical report, not a plan: select one coherent object of study and explain its mechanics deeply. No roadmaps, milestones, or kill criteria.
- Research plan answers **what to build and how we will know**. Keep planning, staging, and go/no-go decisions here, grounded in the technical analysis rather than repeating it.

Do not:

- turn the review into dozens of paper mini-essays;
- repeat the full landscape in technical analysis;
- put project planning, milestones, or roadmaps in technical analysis;
- combine every promising module into one architecture;
- add process sections that do not change a technical decision.

## Quality bar

- Primary sources first: arXiv IDs, DOIs, proceedings, official repos/reports.
- Distinguish peer-reviewed, preprint, author-reported, and product claims.
- No unsupported numbers or cross-protocol rankings.
- State uncertainty instead of inventing detail.
- Prefer the smallest document that preserves the important reasoning.
