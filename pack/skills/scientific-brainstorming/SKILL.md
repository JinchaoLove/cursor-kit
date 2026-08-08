---
name: scientific-brainstorming
description: Creative research ideation and exploration. Use for open-ended brainstorming, interdisciplinary analogies, challenging assumptions, or identifying research gaps. Best early-stage before a concrete plan. For testable hypotheses from observations use hypothesis-generation; for a structured plan use research-plan.
metadata: {"version": "1.0", "skill-author": "lijinchao"}
---

# Scientific Brainstorming

Generate a wide, diverse space of research ideas and directions, then triage. This is divergent thinking on purpose — quantity and variety first, judgment second. Use early, before committing to a hypothesis or plan.

## When to use

- "有没有什么新的方向 / idea?" / "我们还能怎么做 X?"
- Stuck, or the obvious approaches are exhausted.
- Looking for a novel angle, an analogy from another field, or an assumption to break.

Follow with `hypothesis-generation` (make the best ideas testable) and `research-plan` (turn one into a project). Use `ai-frontier-survey` first if you need to know what already exists.

## Method

Run several divergent lenses, then converge.

**Diverge (generate ≥10 ideas across lenses):**
- **Assumption-breaking** — list the field's load-bearing assumptions; negate each. ("What if we don't need paired A/V data?" "What if the world model is trained purely from action-free video?")
- **Analogy transfer** — borrow mechanisms from adjacent fields (NLP → vision, RL → generation, control theory → rollout, physics → simulation priors).
- **Scaling & regime shifts** — what changes at 10×/100× data, params, context, or horizon? What breaks?
- **Constraint injection** — force real-time, on-device, zero-shot, or single-example settings; new constraints spawn new methods.
- **Compose existing pieces** — cross two SOTA ideas that haven't been combined.
- **Invert the objective** — optimize for the opposite (controllability over fidelity, latency over quality) and see what emerges.

**Converge (triage):**
- Cluster ideas; kill duplicates.
- Score each on **novelty × feasibility × impact** (and "does it fit the user's AV-gen/agents/world-models focus?").
- Pick the top 3–5; for each, note the crux (the one thing that must be true) and the cheapest way to probe it.

## Output format

- **Idea list** — grouped by lens, one line each.
- **Shortlist** — top 3–5 with: crux, why it's novel, feasibility flag, and the first probe.
- **Wild cards** — 1–2 high-risk/high-reward ideas worth remembering.

## Guardrails

- Separate divergence from judgment — don't critique during generation.
- Novelty claims are tentative until checked against prior art (`ai-frontier-survey` / `paper-lookup`).
- Prefer ideas with a cheap first experiment; a brilliant idea that takes 6 months to test loses to a good one testable in a day.
