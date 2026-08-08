---
name: deep-research
description: Opt-in Gemini-based autonomous web research; requires GEMINI_API_KEY. Use ONLY when the user explicitly asks to run the Gemini Deep Research script. For general deep research, 深度调研, exhaustive survey, or a cited web report, use paper-lookup with ai-frontier-survey or ai-literature-review instead.
license: Apache-2.0
metadata: {"version": "1.0", "skill-author": "lijinchao", "upstream": "sanjay3290/ai-skills", "openclaw": {"primaryEnv": "GEMINI_API_KEY", "requires": {"env": ["GEMINI_API_KEY"]}, "envVars": [{"name": "GEMINI_API_KEY", "required": true, "description": "Google Gemini API key for the Deep Research Agent."}]}}
required_environment_variables: [{"name": "GEMINI_API_KEY", "prompt": "Google Gemini API key (aistudio.google.com).", "required_for": "full functionality"}]
---

# Gemini Deep Research

Run autonomous research tasks that plan, search, read, and synthesize the web into comprehensive, cited reports. The agent iterates through many search/read cycles — slower than a chat answer, but far more thorough.

Adapted from the upstream `sanjay3290/ai-skills` deep-research skill (`scripts/research.py` kept intact).

## Requirements

- Python 3.8+, `pip install -r requirements.txt` (`httpx`, `python-dotenv`).
- `GEMINI_API_KEY` from [Google AI Studio](https://aistudio.google.com/) — set in env or a local `.env` (see `.env.example`).

## Usage

`scripts/`, `requirements.txt`, and `.env` are siblings of this `SKILL.md`. Paths below are **relative to this SKILL.md's directory**, NOT the current project's working directory. Set `SKILL_DIR` to the absolute path of the folder containing this SKILL.md, then reuse it in every command:

```bash
# Absolute path of the directory that contains THIS SKILL.md
SKILL_DIR="/Users/lijinchao/Projects/.cursor/skills/deep-research"
pip install -r "$SKILL_DIR/requirements.txt"
```

```bash
# Start and wait for the report
python3 "$SKILL_DIR/scripts/research.py" --query "Survey SOTA in audio-video joint generation (2025): methods, benchmarks, numbers"

# Impose an output structure
python3 "$SKILL_DIR/scripts/research.py" --query "Compare open video world-model approaches" \
  --format "1. Landscape table\n2. Method dissection\n3. Benchmarks & numbers\n4. Gaps"

# Stream progress live
python3 "$SKILL_DIR/scripts/research.py" --query "Foley / video-to-audio SOTA" --stream

# Fire-and-forget, then poll
python3 "$SKILL_DIR/scripts/research.py" --query "..." --no-wait
python3 "$SKILL_DIR/scripts/research.py" --status <interaction_id>
python3 "$SKILL_DIR/scripts/research.py" --wait   <interaction_id>

# Follow-up on a prior report (keeps context)
python3 "$SKILL_DIR/scripts/research.py" --query "Expand section 3 with latency numbers" --continue <interaction_id>

# History
python3 "$SKILL_DIR/scripts/research.py" --list
```

Output: default markdown; `--json` structured; `--raw` unprocessed API response.

## Workflow

1. Confirm scope.
2. Write a sharp query. For AV-gen / agents / world models, ask explicitly for **benchmarks, metrics, and numbers**, not just prose — and specify the current year to force recency.
3. Run with `--stream` (or `--no-wait` + poll for long tasks).
4. **Verify** — deep-research can hallucinate citations. Spot-check key sources with `paper-lookup` before trusting numbers.
5. Fold results into an `ai-frontier-survey` / `ai-literature-review` artifact, or `--continue` for follow-ups.

## When to use vs. siblings

- **deep-research** — broad, autonomous, cited web report; good first pass on an unfamiliar landscape.
- **ai-frontier-survey** — you (the agent) hand-dissect primary sources for reproducible technical depth.
- **ai-literature-review** — systematic, criteria-driven synthesis of a paper set.

## Safety & limits

- Read-only research; no file modifications by the script.
- No secrets in queries. Verify citations — the model can fabricate sources.
- Web-only (no private/authenticated sources); no custom tools/MCP; 60-min hard cap.

## Exit codes

`0` success · `1` error (API/config/timeout) · `130` cancelled (Ctrl+C).
