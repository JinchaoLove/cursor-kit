# Gemini Deep Research (skill)

Autonomous multi-step web research via Google's Gemini Deep Research Agent. Plans → searches → reads → synthesizes into a cited report.

`scripts/research.py` is adapted from the upstream [`sanjay3290/ai-skills`](https://github.com/sanjay3290/ai-skills/tree/main/skills/deep-research) skill (Apache-2.0).

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # then add your GEMINI_API_KEY
```

## Quick start

```bash
python3 scripts/research.py --query "Your research question" --stream
python3 scripts/research.py --help
```

See `SKILL.md` for the full command reference, workflow, and how this relates to the `ai-frontier-survey` and `ai-literature-review` skills.

## Config (env vars)

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_API_KEY` | (required) | Google Gemini API key |
| `DEEP_RESEARCH_TIMEOUT` | `600` | Max wait time (s) |
| `DEEP_RESEARCH_POLL_INTERVAL` | `10` | Poll interval (s) |
| `DEEP_RESEARCH_CACHE_DIR` | `~/.cache/deep-research` | Local history cache |

## Caveats

- Verify citations before trusting them (cross-check with the `paper-lookup` skill).
- Web-only; no private sources; 60-minute hard cap; no MCP/function calling.
