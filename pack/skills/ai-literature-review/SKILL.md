---
name: ai-literature-review
description: Produces broad, structured AI/ML literature reviews and taxonomies. Use for 综述, literature review, related work, landscape, coverage analysis, or literature-review.md. Prioritizes defensible coverage and synthesis over per-paper technical depth.
metadata: {"version": "1.2", "skill-author": "lijinchao"}
---

# AI Literature Review

Answer: **What exists, how is it organized, and where is the evidence weak?**

## Workflow

1. Define the research questions, time window, and inclusion/exclusion rules.
2. Search multiple query families with `paper-lookup`; save raw results under `sources/`.
3. Follow references/citations for representative works.
4. Deduplicate and screen candidates.
5. Build orthogonal taxonomy axes such as task, topology, domain, temporal scale, and openness.
6. Cover every important family with compact entries.
7. Synthesize trends, benchmark gaps, disagreements, and open problems.

## Project output

Write `literature-review.md` with:

1. scope and evidence rules;
2. taxonomy;
3. breadth-first academic landscape;
4. product/API landscape;
5. datasets and evaluation;
6. cross-cutting conclusions and gaps;
7. deduplicated primary-source references.

Use one comparison table plus short synthesis sections. Mechanism-level detail — tensor flow, losses, architecture, information flow — belongs in the `technical-analysis.md` report; training stages, roadmaps, and proposals belong in `research-plan.md`.

## Coverage checks

- Include seminal work, recent work, open systems, closed products, and adjacent evidence.
- Separate direct evidence from neighboring tasks.
- Distinguish author-reported results from independent reproduction.
- State important missing families or incomplete screening.
- Do not silently compare incompatible FVD/FAD/Sync/WER protocols.

## KISS

- One compact paragraph or table row per system is usually enough.
- Deep-dive only the few works needed to distinguish method families.
- Do not add workflow bureaucracy, repeated metadata, or a paper-by-paper catalog unless the user explicitly asks for a systematic review.
