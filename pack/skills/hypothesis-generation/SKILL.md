---
name: hypothesis-generation
description: Structured hypothesis formulation from observations. Use when experimental results, ablations, or failures need testable hypotheses, mechanism proposals, and experiment designs. Turns "X happened / X didn't work" into falsifiable claims with predicted outcomes and the minimal experiment to test them. For open-ended ideation use scientific-brainstorming.
metadata: {"version": "1.0", "skill-author": "lijinchao, cursor"}
---

# Hypothesis Generation

Convert observations (results, ablations, failures, surprises) into falsifiable hypotheses, each with a proposed mechanism, a predicted outcome, and the cheapest experiment that would confirm or refute it.

## When to use

- "为什么 X 会这样 / 为什么这个 ablation 没提升?"
- A training run failed, plateaued, or behaved surprisingly.
- You have results and need to explain them before the next iteration.
- Before `research-plan`: to sharpen the bet you're planning around.

## Method

1. **State the observation precisely** — what was measured, under what conditions, vs what baseline. Separate fact from interpretation.
2. **Enumerate candidate mechanisms** — brainstorm ≥3 distinct explanations (data, optimization, architecture, eval artifact, distribution shift, capacity, alignment). Include the boring ones (bug, metric artifact, seed variance).
3. **Turn each into a hypothesis** — "If <mechanism>, then <specific, measurable prediction>." It must be falsifiable: state what result would kill it.
4. **Rank** — by (a) prior plausibility, (b) cost to test, (c) information gain. Prefer cheap, discriminating tests first.
5. **Design the test** — for the top hypotheses, the minimal experiment: the one variable to change, what to hold fixed, the metric, and the expected result under each competing hypothesis (so the test discriminates).
6. **Note confounders** — what could make the test misleading, and how to control it.

## Output format

For each hypothesis:
- **H:** <claim>
- **Mechanism:** <why this would cause the observation>
- **Prediction:** <measurable outcome if true>
- **Falsifier:** <result that would refute it>
- **Test:** <minimal experiment; variable, control, metric>
- **Cost / info-gain:** <low/med/high>

Then: a ranked shortlist of which experiments to run next and in what order.

## Quality bar

- Every hypothesis is falsifiable and tied to a measurement. "The model learns better features" is not a hypothesis; "removing the cross-modal loss lowers AV-Sync by ≥X on <dataset>" is.
- Always include the mundane explanations (bug, metric/protocol artifact, variance across seeds) — they're often right and cheap to rule out.
- Tests should *discriminate* between competing hypotheses, not just confirm a favorite.

## Domain notes (AV-gen / agents / world models)

- Common culprits: eval protocol mismatch, sync-vs-quality trade-off, codec/latent bottleneck, exposure bias in AR rollout, CFG scale, data leakage/contamination, insufficient temporal context, reward hacking (agents).
- For generative quality claims, first rule out metric artifacts (e.g. FVD sensitivity to preprocessing) before proposing deep mechanisms.
