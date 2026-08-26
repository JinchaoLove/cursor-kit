---
name: ai-frontier-survey
description: Dissects recent AI/ML frontier methods with architecture, data, training, evaluation, and reproducibility detail. Use for 前沿调研, SOTA 细节, 技术拆解, method comparison, or technical due diligence.
metadata: {"version": "1.2", "skill-author": "lijinchao, cursor"}
---

# AI Frontier Survey

Use this skill for depth on a small number of important systems, not exhaustive coverage.

## Method

1. Select 3–8 anchor systems relevant to the user's decision.
2. Read primary sources: Methods, Experiments, appendix, official code/model card.
3. Extract:
   - problem and I/O;
   - backbone, representation, conditioning, temporal mechanism;
   - objective and training recipe;
   - data and compute;
   - metric, dataset, protocol, and reported number;
   - code/weights/data availability;
   - limitations and failure modes.
4. Compare protocols before comparing numbers.
5. State what changed at the frontier and what it implies.

## Output

In a project, this skill owns `technical-analysis.md`: a deep technical **report** on how the chosen method(s) work — mechanism, architecture, information flow, objectives, and technical tradeoffs, with evidence. Keep it to depth of understanding; do not add project planning, milestones, or roadmaps (those go in `research-plan.md`). Keep the broad corpus and references in `literature-review.md`.

## Guardrails

- Mark author-reported vs reproduced.
- No “SOTA” without benchmark and protocol.
- Do not infer closed-product architecture.
- Do not copy modules into a proposal without checking interface compatibility.
- Prefer 3–8 well-understood anchors over 20 shallow summaries.
