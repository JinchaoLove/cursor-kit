---
name: scientific-critical-thinking
description: Evaluate scientific and AI research claims for evidence quality. Use when assessing experimental design, baselines, metrics validity, bias/confounders, overclaimed SOTA, or critiquing papers and research plans. Also triggers on 批判性分析, 挑刺, review claims, or eval protocol critique.
metadata: {"version": "1.0", "skill-author": "lijinchao, cursor"}
---

# Scientific Critical Thinking

Stress-test a claim, a paper, or your own plan/results before believing (or publishing) them. Adversarial by design: assume the claim is wrong and see if it survives.

## When to use

- Reviewing a paper, a blog benchmark, or a competitor's claims.
- "批判性分析一下这个方法 / 结果 / 方案" / "帮我挑刺".
- Before claiming your own result is real (pre-publication self-review).
- Vetting a `research-plan` (pre-mortem) or a research report (citation/number check).

## Checklist

**1. Claim clarity**
- What exactly is claimed? Is it falsifiable? Is the scope creep? ("SOTA" on what, measured how?)

**2. Baselines**
- Are baselines strong, current, and fairly tuned? Or strawmen / stale / under-tuned?
- Is the comparison apples-to-apples (same data, compute, eval protocol)?

**3. Metrics & evaluation**
- Does the metric measure what's claimed? Known artifacts (e.g. FVD preprocessing sensitivity, FAD backbone choice, sync metrics gameable)?
- Right dataset & split? Any train/test contamination or leakage?
- Cherry-picked demos vs benchmarked numbers? Is human eval needed and present (N, protocol, significance)?

**4. Statistics & rigor**
- Multiple seeds / error bars / significance? Or a single run?
- Ablations isolating the claimed contribution, or confounded changes?
- Selective reporting (missing metrics, missing datasets where it loses)?

**5. Confounders & alternative explanations**
- Could the gain come from more data/compute/params/tuning rather than the idea?
- What's the most likely boring explanation?

**6. Reproducibility**
- Code, configs, seeds, checkpoints released? Enough detail to reproduce? Author-reported vs independently verified?

**7. Generalization & limits**
- Does it hold beyond the reported setting? What are the failure modes and honestly-stated limitations?

## Output format

- **Verdict** — how much to believe the claim (with confidence).
- **Strongest evidence for** / **strongest concerns against**.
- **Critical issues** — ranked; each with why it matters and what would resolve it.
- **What would change my mind** — the specific experiment/data that would confirm or refute.

## Stance

- Be specific and fair: cite the exact table/figure/section; propose the concrete fix or test, not vague doubt.
- Apply the same rigor to the user's own work as to others'. Flattering a weak result helps no one.
- Distinguish "not shown" from "shown to be false." Absence of evidence ≠ evidence of absence.
