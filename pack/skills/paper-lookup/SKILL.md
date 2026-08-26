---
name: paper-lookup
description: Search academic literature APIs for papers, preprints, citations, and open-access full text with reproducible provenance. Covers arXiv, Semantic Scholar, OpenAlex, and Crossref out of the box (no key required). Use when searching for papers, citations, DOI/arXiv lookups, abstracts, open-access PDFs, preprints, citation graphs, author publications, or any scholarly query. Triggers on "find papers on X", "look up this DOI/arXiv", "who cites this", "get me the PDF".
metadata: {"version": "1.1", "skill-author": "lijinchao, cursor", "openclaw": {"envVars": [{"name": "SEMANTIC_SCHOLAR_API_KEY", "required": false, "description": "Raises Semantic Scholar rate limits."}, {"name": "OPENALEX_MAILTO", "required": false, "description": "Email for the OpenAlex polite pool (faster, more reliable)."}]}}
required_environment_variables: [{"name": "SEMANTIC_SCHOLAR_API_KEY", "prompt": "Semantic Scholar API key (raises rate limits).", "required_for": "optional features"}, {"name": "OPENALEX_MAILTO", "prompt": "Email for OpenAlex polite pool.", "required_for": "optional features"}]
---

# Paper Lookup

Retrieve scholarly literature with reproducible provenance. Supporting skill for `ai-frontier-survey`, `ai-literature-review`, and `research-plan`.

## Requirements

- Python 3.8+, `pip install -r requirements.txt` (only `httpx`).
- No API key required for arXiv, OpenAlex, Crossref. Optional: `SEMANTIC_SCHOLAR_API_KEY` (higher rate limits), `OPENALEX_MAILTO` (polite pool).

## Usage

`scripts/` and `requirements.txt` are siblings of this `SKILL.md`. Paths below are **relative to this SKILL.md's directory**, NOT the current project's working directory. Set `SKILL_DIR` to the absolute path of the folder containing this SKILL.md, then reuse it in every command:

```bash
# Absolute path of the directory that contains THIS SKILL.md
SKILL_DIR="/Users/lijinchao/Projects/.cursor/skills/paper-lookup"
pip install -r "$SKILL_DIR/requirements.txt"
```

### Where retrieval output is saved

Generated files go into a subdirectory **of the project you are working in**, NOT into `SKILL_DIR`. Set `OUT_DIR` to a subfolder of the current project and pass it via `--out-dir` (or the `PAPER_LOOKUP_OUT_DIR` env var):

```bash
# Project you are currently working in (usually the CWD)
OUT_DIR="${PWD}/sources"    # per-project provenance directory
export PAPER_LOOKUP_OUT_DIR="$OUT_DIR"    # so every call below auto-saves there
```

When `--out-dir` (or `PAPER_LOOKUP_OUT_DIR`) is set, each search writes a timestamped pair of files into that directory — `YYYYMMDD-HHMMSS_<query-slug>.json` (machine-readable) and `.md` (human-readable). If neither is set, nothing is written to disk (print-only, original behavior).

Saved JSON/Markdown files are provenance artifacts, not project synthesis documents. Synthesize their findings into the project's `literature-review.md`.

Every saved JSON result has a stable `title`, `url`, and `abstract` field in addition to source metadata, authors, year, venue, identifier, PDF URL, and citation count when available. Markdown uses the canonical paper URL in each title and prints the complete abstract under an **Abstract** section. A missing upstream abstract is represented as `null` in JSON and explicitly marked unavailable in Markdown. For duplicate records, complementary metadata from later sources is merged instead of discarded.

```bash
# Search across all default sources
python3 "$SKILL_DIR/scripts/search_papers.py" "audio video joint generation diffusion" --limit 10

# One source only
python3 "$SKILL_DIR/scripts/search_papers.py" "world model video game" --source arxiv --limit 15

# Lookup by identifier
python3 "$SKILL_DIR/scripts/search_papers.py" --id arXiv:2312.02696
python3 "$SKILL_DIR/scripts/search_papers.py" --id 10.1109/CVPR.2023.00001   # DOI

# Who cites / references (Semantic Scholar)
python3 "$SKILL_DIR/scripts/search_papers.py" --citations <arxivID-or-DOI>
python3 "$SKILL_DIR/scripts/search_papers.py" --references <arxivID-or-DOI>

# JSON output for programmatic use / piping into a review
python3 "$SKILL_DIR/scripts/search_papers.py" "talking head generation" --json

# Save results into the current project's subdirectory
python3 "$SKILL_DIR/scripts/search_papers.py" "world model" --out-dir "${PWD}/sources"
```

Each result reports the source API and identifier so results are traceable. Links prefer the publisher or repository landing page; DOI and arXiv identifiers are converted to canonical URLs when an API omits one.

## Source selection

| Need | Source |
| --- | --- |
| Preprints, latest cs.CV/cs.SD/cs.LG | `arxiv` |
| Citation graph, TL;DR, influential-citation counts | `semanticscholar` |
| Broad coverage, open metadata, concepts, OA status | `openalex` |
| Authoritative DOI metadata, publisher records | `crossref` |

Default `--source all` queries arXiv + Semantic Scholar + OpenAlex and merges/dedupes by title & DOI.

## Workflow

1. Start broad with `--source all`, then narrow.
2. For each promising hit, record: title, authors, year, venue, arXiv/DOI, and the source API.
3. Follow the citation graph with `--citations` / `--references` for snowballing.
4. Fetch OA PDFs via the `openAccessPdf` / OpenAlex `best_oa_location` fields when present.
5. Hand results to `ai-literature-review` (synthesis) or `ai-frontier-survey` (dissection). Keep the query log for reproducibility.

## Notes

- Respect rate limits: without a Semantic Scholar key, keep requests modest. The script backs off on HTTP 429.
- Never fabricate a citation. If a lookup returns nothing, say so and try another source/identifier form (arXiv id vs DOI).
- For paywalled papers, report metadata + OA link if any; do not attempt to bypass paywalls.
- More endpoints (PubMed, bioRxiv, CORE, Unpaywall, Semantic Scholar batch) can be added in `references/apis.md`; keep this AI/ML-focused set as the fast path.
