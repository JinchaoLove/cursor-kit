---
name: keep-it-simple
description: Cut a change or a codebase down to what the requirements actually pay for. Use for KISS, 精简, 极简, 最小实现, 最小 diff, over-engineering, "this feels too complex", removing flags/abstractions/state, or auditing code and docs for redundancy. Pairs with project-development.
metadata: {"version": "1.0", "skill-author": "lijinchao, cursor"}
---

# Keep It Simple

Simplicity is not a style preference. It is what remains after you delete everything no requirement pays for. This skill is the audit that finds those things.

## Trigger

- User says the code or docs feel bloated, complex, or "not KISS"
- The diff is growing larger than the feature that motivated it
- Reviewing an implementation you wrote earlier in the session
- About to add a flag, a config option, an abstraction layer, or a state file
- Before committing

## The one test

Write the requirement as a single sentence. Then, for every construct, ask:

> **Which requirement does this serve, and what breaks if I delete it?**

Delete it if the answer is "nothing breaks" or "it handles a case nobody asked about". *It might be useful later* is not an answer. Neither is *it's only a few lines*: the cost of a line is not its length, it is that every future reader must understand it, and every future change must not break it.

## Audit procedure

1. **State the core requirement in one sentence.** Needing two sentences means you have two features; audit them separately.
2. **Derive what is necessary from it.** Usually three to six things. Everything else is under suspicion until it earns its place.
3. **Measure where the lines are.** Count lines per section or file. Load-bearing logic is often an order of magnitude smaller than the scaffolding around it, and that ratio tells you where to cut.
4. **Cut by category, not line by line.** See the table below.
5. **Re-verify.** Simplification must keep the tests green. If nothing tests the core requirement, write that test before cutting.

## What to cut

| Category | Looks like | Why it goes |
|---|---|---|
| Invented problems | Defenses against adversarial or hypothetical scenarios nobody requested | You added the problem *and* the solution |
| Speculative generality | Flags, config knobs, extension points, abstractions with one implementation | Add it when the second caller appears |
| Redundant state | Cache files, persisted progress, memoized derivable values | Statelessness deletes a whole class of bugs; recompute instead |
| Defensive noise | Guards for impossible conditions, broad `except` that hides real failures | Fail loud beats fail obscure |
| Author convenience | Reload-on-edit, debug subcommands, dev-only shortcuts | Not a user requirement |
| Structural excess | Extra processes, threads, services, files, indirection | Question the architecture, not only the parameters |

**Parameter trimming plateaus; structural cuts do not.** If constants and branches are already lean and it still feels heavy, the shape is wrong. Collapse a layer.

## Prefer the failure mode that points the safe way

When two designs are close, pick the one that fails safe.

Persisted state that can go stale is worse than no state: stale data makes you *skip* work you needed to do, while missing data makes you *redo* work already done. Redoing is cheap. Skipping is the bug.

## Cutting capability is allowed

Removing a real but low-value capability is a legitimate simplification. Make the trade visible when you do it — name what was dropped, what it cost, and what it covered — so it is a decision rather than an omission.

## Check the environment before recommending an idiom

Do not copy a pattern because it is standard elsewhere. Verify it exists here: the scheduler, the init system, the package manager, the writable path, the shell builtin. A recommendation that cannot run is worse than none, because it looks like coverage.

## Docs and comments

Documentation is for someone who wants to use the thing, not for the person who built it.

**Keep:** what it does, how to install and run it, configuration, observable behavior, real limitations.

**Cut:**

- Why you did *not* choose the alternatives — nobody asked
- Environment archaeology and debugging war stories
- Anything phrased as an answer to a question the reader never asked
- Rationale that only makes sense if you watched the development happen

**Comments** state constraints the code cannot express: an ordering requirement, a reference that must stay alive, a non-obvious API footgun. Never restate what the line does, never argue the change to a reviewer, never record who requested it.

## Guardrails

- Simplify only what you are already changing. Do not opportunistically refactor neighboring code.
- Never use bulk undo (`git checkout .`, `reset --hard`, `stash`, `clean`) to "clean up" — it destroys unrelated uncommitted work. Revert your own lines precisely.
- Do not simplify away a requirement. If a cut weakens something the user stated, surface it and ask.
- Verify after cutting, before claiming done.
