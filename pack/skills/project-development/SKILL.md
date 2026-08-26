---
name: project-development
description: General software/ML engineering workflow for implementation work. Use for 开发 / 编码 / 重构 / 调试 / 测试 / 部署, building or changing code, setting up a repo, writing training/eval scripts, fixing bugs, or turning a research plan into runnable, reproducible code. Language- and framework-agnostic, with an ML-research reproducibility bias.
metadata: {"version": "1.0", "skill-author": "lijinchao, cursor"}
---

# Project Development

The engineering workflow and quality bar for turning ideas/plans into working, reproducible code. Pairs with `research-plan` (what to build) — this skill is about building it well.

## Core loop

1. **Understand before changing** — read the relevant code and existing conventions first. Match the repo's style, structure, and tooling before introducing new ones. Reuse existing utilities.
2. **Plan the change** — smallest reversible step that moves toward the goal. For multi-step work, keep a short task list.
3. **Implement** — follow existing patterns; keep functions focused; avoid narrating-the-obvious comments (comment intent/trade-offs only).
4. **Verify** — run it. Build, run the script, execute tests. Never claim done without evidence it works.
5. **Check lints** — fix linter/type errors you introduced.
6. **Iterate** — small commits/changes; re-run after each.

## Quality bar

- **Small, reversible changes.** Prefer several verifiable steps over one big diff.
- **Verify before claiming done** — actually run/build/test; show the evidence.
- **Match conventions** — formatting, naming, error handling, logging, dependency management as the repo already does it.
- **No secrets in code** — read keys from env/`.env`; never commit credentials.
- **Dependencies** — pin versions; add via the package manager (don't invent versions); update the manifest (requirements.txt / pyproject / package.json).
- **Errors** — fail loud and early with actionable messages; don't swallow exceptions.

## ML / research-code reproducibility (apply for training/eval work)

- **Config-driven** — no magic constants; hyperparameters in a config (yaml/argparse/hydra), logged with each run.
- **Seeded** — set and log seeds (python/numpy/torch, and `torch.use_deterministic_algorithms` where feasible); note sources of nondeterminism.
- **Logged** — metrics, config, git commit, and environment captured per run (e.g. wandb/tensorboard + a run dir). A result you can't trace to a config is not a result.
- **Deterministic data** — fixed splits, recorded dataset version/hash, documented preprocessing.
- **Checkpointing** — save/resume; store the config alongside the checkpoint.
- **Eval harness first** — implement and validate the metric on a known baseline before trusting it on your method (mirrors `research-plan` Phase 0).
- **Reproduce the baseline** before building the new thing; a green baseline is the foundation for every later claim.

## Debugging

- Reproduce reliably (minimal case, fixed seed) before fixing.
- Form a hypothesis about the cause (see `hypothesis-generation` for structure), add targeted logging/asserts, isolate one variable at a time.
- Fix root cause, not symptoms; add a regression test where practical.
- For ML: check the boring things first (data pipeline, shapes/dtypes, normalization, label alignment, learning rate, loss scaling) before suspecting the model.

## Deployment / handoff

- Reproducible env (pinned deps, documented Python/CUDA versions, containerize if it matters).
- A README that states: how to install, how to run training/eval, expected outputs, and required env vars.
- Sanity-check the runnable path end-to-end before declaring it shippable.

## Guardrails

- Don't commit unless asked. When asked, follow the repo's commit conventions.
- Don't refactor unrelated code opportunistically inside a focused change.
- Prefer editing existing files over creating new ones; don't create docs unless asked.
