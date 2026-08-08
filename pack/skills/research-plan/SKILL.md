---
name: research-plan
description: Produces focused, executable AI research plans (research-plan.md). Use for 研究方案, 研究计划, experiment plans, proposals, or roadmaps. Selects one coherent route and specifies the minimum detail needed to build and falsify it. For a deep technical report on how a method works, use ai-frontier-survey (technical-analysis.md) instead.
metadata: {"version": "1.2", "skill-author": "lijinchao"}
---

# Research Plan

Answer: **What should we build, why should it work, and how will we know?**

## Inputs

- target capability and non-goals;
- strongest reproducible baseline;
- one core hypothesis;
- data, compute, time, and team constraints.

If these are unknown, state assumptions or narrow the scope.

## Project output

Write `research-plan.md` with:

1. problem definition and key evidence;
2. one primary technical route;
3. architecture and information flow;
4. objectives and training stages;
5. data plan;
6. evaluation and decision thresholds;
7. minimal ablations;
8. compute, risks, milestones, and kill criteria.

This is the *plan*: what to build and how we will know. Deep mechanism-level dissection of the underlying method belongs in `technical-analysis.md` — reference it, do not duplicate it.

## Technical requirements

- Name the backbone/checkpoint and explain why it was selected.
- Mark literature facts, inference, and proposal.
- Specify condition flow, attention/masking, time representation, and frozen/trainable parts.
- Define the complete objective; each loss must address a failure mode.
- Match metrics to their valid domain.
- Reproduce the baseline before adding the new method.
- Change one variable per ablation.

## KISS

- One primary route; alternatives are short rejection/fallback notes.
- One core hypothesis; add more only if independently testable.
- Use the fewest modules and losses that can test the hypothesis.
- Avoid speculative 30–120s systems before short-window evidence.
- Do not repeat the literature review.

Use `assets/plan-template.md` when a scaffold helps. Follow with `scientific-critical-thinking` and `project-development`.
