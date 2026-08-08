#!/usr/bin/env python3
"""Search academic literature across arXiv, Semantic Scholar, OpenAlex, and Crossref.

No API key required for arXiv/OpenAlex/Crossref. Optional env vars:
  SEMANTIC_SCHOLAR_API_KEY  - higher Semantic Scholar rate limits
  OPENALEX_MAILTO           - email for the OpenAlex polite pool

Examples:
  python3 search_papers.py "audio video joint generation" --limit 10
  python3 search_papers.py "world model" --source arxiv
  python3 search_papers.py --id arXiv:2312.02696
  python3 search_papers.py --citations 10.1109/CVPR.2023.00001
"""
import argparse
import datetime
import html
import json
import os
import re
import sys
import time
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional

try:
    import httpx
except ImportError:
    print("Error: httpx not installed. Run: pip install -r requirements.txt", file=sys.stderr)
    sys.exit(1)

TIMEOUT = 30.0
USER_AGENT = "paper-lookup-skill/1.0 (research use)"


def _get(url: str, params: Dict[str, Any] = None, headers: Dict[str, str] = None) -> Optional[httpx.Response]:
    """GET with simple retry/backoff on 429."""
    headers = {"User-Agent": USER_AGENT, **(headers or {})}
    for attempt in range(3):
        try:
            r = httpx.get(url, params=params, headers=headers, timeout=TIMEOUT, follow_redirects=True)
            if r.status_code == 429:
                time.sleep(2 * (attempt + 1))
                continue
            return r
        except httpx.HTTPError as e:
            if attempt == 2:
                print(f"  [warn] request failed: {e}", file=sys.stderr)
            time.sleep(1)
    return None


def _norm_title(t: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (t or "").lower())


def _clean_text(text: Optional[str]) -> Optional[str]:
    """Collapse whitespace and remove markup commonly returned by Crossref."""
    if not text:
        return None
    text = re.sub(r"<[^>]+>", " ", html.unescape(text))
    return re.sub(r"\s+", " ", text).strip() or None


def _openalex_abstract(inverted_index: Optional[Dict[str, List[int]]]) -> Optional[str]:
    """Reconstruct OpenAlex's abstract text from its inverted index."""
    if not inverted_index:
        return None
    words = sorted(
        ((position, word) for word, positions in inverted_index.items() for position in positions),
        key=lambda item: item[0],
    )
    return _clean_text(" ".join(word for _, word in words))


def _identifier_url(ident: Optional[str]) -> Optional[str]:
    if not ident:
        return None
    if ident.lower().startswith("arxiv:"):
        return f"https://arxiv.org/abs/{ident.split(':', 1)[1]}"
    if ident.lower().startswith("10."):
        return f"https://doi.org/{ident}"
    if ident.startswith(("http://", "https://")):
        return ident
    return None


def normalize_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """Return a stable result shape with title, URL, and abstract fields."""
    normalized = dict(row)
    normalized["title"] = _clean_text(normalized.get("title")) or "Untitled"
    normalized["url"] = normalized.get("url") or _identifier_url(normalized.get("id"))
    normalized["abstract"] = _clean_text(normalized.get("abstract"))
    return normalized


# ---------------------------------------------------------------- arXiv
def search_arxiv(query: str, limit: int) -> List[Dict[str, Any]]:
    r = _get(
        "http://export.arxiv.org/api/query",
        params={"search_query": f"all:{query}", "start": 0, "max_results": limit,
                "sortBy": "relevance", "sortOrder": "descending"},
    )
    if not r or r.status_code != 200:
        return []
    ns = {"a": "http://www.w3.org/2005/Atom"}
    out = []
    for e in ET.fromstring(r.text).findall("a:entry", ns):
        aid = (e.findtext("a:id", "", ns) or "").split("/abs/")[-1]
        out.append({
            "source": "arxiv",
            "title": (e.findtext("a:title", "", ns) or "").strip().replace("\n", " "),
            "authors": [a.findtext("a:name", "", ns) for a in e.findall("a:author", ns)],
            "year": (e.findtext("a:published", "", ns) or "")[:4],
            "venue": "arXiv",
            "id": f"arXiv:{aid}",
            "url": e.findtext("a:id", "", ns),
            "pdf": next((l.get("href") for l in e.findall("a:link", ns) if l.get("title") == "pdf"), None),
            "abstract": (e.findtext("a:summary", "", ns) or "").strip().replace("\n", " "),
        })
    return out


# ------------------------------------------------------- Semantic Scholar
def search_semanticscholar(query: str, limit: int) -> List[Dict[str, Any]]:
    headers = {}
    key = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
    if key:
        headers["x-api-key"] = key
    fields = "title,authors,year,venue,url,externalIds,openAccessPdf,abstract,tldr,citationCount"
    r = _get("https://api.semanticscholar.org/graph/v1/paper/search",
             params={"query": query, "limit": limit, "fields": fields}, headers=headers)
    if not r or r.status_code != 200:
        return []
    out = []
    for p in r.json().get("data", []):
        ext = p.get("externalIds") or {}
        ident = (f"arXiv:{ext['ArXiv']}" if ext.get("ArXiv")
                 else ext.get("DOI") or p.get("paperId"))
        tldr = (p.get("tldr") or {}).get("text")
        out.append({
            "source": "semanticscholar",
            "title": p.get("title"),
            "authors": [a.get("name") for a in (p.get("authors") or [])],
            "year": p.get("year"),
            "venue": p.get("venue"),
            "id": ident,
            "url": p.get("url") or _identifier_url(ident),
            "citationCount": p.get("citationCount"),
            "pdf": (p.get("openAccessPdf") or {}).get("url"),
            "abstract": p.get("abstract") or tldr,
        })
    return out


# ------------------------------------------------------------- OpenAlex
def search_openalex(query: str, limit: int) -> List[Dict[str, Any]]:
    params = {"search": query, "per-page": limit}
    mailto = os.getenv("OPENALEX_MAILTO")
    if mailto:
        params["mailto"] = mailto
    r = _get("https://api.openalex.org/works", params=params)
    if not r or r.status_code != 200:
        return []
    out = []
    for w in r.json().get("results", []):
        oa = w.get("best_oa_location") or {}
        primary = w.get("primary_location") or {}
        ident = w.get("doi") or w.get("id")
        out.append({
            "source": "openalex",
            "title": w.get("title"),
            "authors": [a["author"]["display_name"] for a in (w.get("authorships") or [])[:12]],
            "year": w.get("publication_year"),
            "venue": (primary.get("source") or {}).get("display_name"),
            "id": ident,
            "url": primary.get("landing_page_url") or _identifier_url(ident) or w.get("id"),
            "citationCount": w.get("cited_by_count"),
            "pdf": oa.get("pdf_url"),
            "abstract": _openalex_abstract(w.get("abstract_inverted_index")),
        })
    return out


# ------------------------------------------------------------- Crossref
def search_crossref(query: str, limit: int) -> List[Dict[str, Any]]:
    r = _get("https://api.crossref.org/works", params={"query": query, "rows": limit})
    if not r or r.status_code != 200:
        return []
    out = []
    for it in r.json().get("message", {}).get("items", []):
        ident = it.get("DOI")
        out.append({
            "source": "crossref",
            "title": (it.get("title") or [""])[0],
            "authors": [f"{a.get('given','')} {a.get('family','')}".strip()
                        for a in (it.get("author") or [])],
            "year": ((it.get("issued") or {}).get("date-parts") or [[None]])[0][0],
            "venue": (it.get("container-title") or [""])[0],
            "id": ident,
            "url": it.get("URL") or _identifier_url(ident),
            "citationCount": it.get("is-referenced-by-count"),
            "pdf": None,
            "abstract": _clean_text(it.get("abstract")),
        })
    return out


SOURCES = {
    "arxiv": search_arxiv,
    "semanticscholar": search_semanticscholar,
    "openalex": search_openalex,
    "crossref": search_crossref,
}
DEFAULT_SOURCES = ["arxiv", "semanticscholar", "openalex"]


def dedupe(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen: Dict[str, Dict[str, Any]] = {}
    out = []
    for raw_row in rows:
        r = normalize_row(raw_row)
        key = _norm_title(raw_row.get("title")) or (r.get("id") or "")
        if key and key in seen:
            existing = seen[key]
            for field, value in r.items():
                if existing.get(field) in (None, "", []) and value not in (None, "", []):
                    existing[field] = value
            continue
        seen[key] = r
        out.append(r)
    return out


# --------------------------------------------------- identifier lookups
def lookup_id(ident: str) -> List[Dict[str, Any]]:
    """Resolve an arXiv id or DOI via Semantic Scholar."""
    pid = _s2_id(ident)
    headers = {}
    key = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
    if key:
        headers["x-api-key"] = key
    fields = "title,authors,year,venue,url,externalIds,openAccessPdf,abstract,citationCount,tldr"
    r = _get(f"https://api.semanticscholar.org/graph/v1/paper/{pid}",
             params={"fields": fields}, headers=headers)
    if not r or r.status_code != 200:
        print(f"  [warn] lookup failed for {ident} (HTTP {getattr(r,'status_code','?')})", file=sys.stderr)
        return []
    p = r.json()
    ext = p.get("externalIds") or {}
    return [{
        "source": "semanticscholar",
        "title": p.get("title"),
        "authors": [a.get("name") for a in (p.get("authors") or [])],
        "year": p.get("year"),
        "venue": p.get("venue"),
        "id": (f"arXiv:{ext['ArXiv']}" if ext.get("ArXiv") else ext.get("DOI") or p.get("paperId")),
        "url": p.get("url"),
        "citationCount": p.get("citationCount"),
        "pdf": (p.get("openAccessPdf") or {}).get("url"),
        "abstract": p.get("abstract") or (p.get("tldr") or {}).get("text"),
    }]


def _s2_id(ident: str) -> str:
    ident = ident.strip()
    if ident.lower().startswith("arxiv:"):
        return f"arXiv:{ident.split(':',1)[1]}"
    if re.match(r"^\d{4}\.\d{4,5}(v\d+)?$", ident):
        return f"arXiv:{ident}"
    if ident.lower().startswith("10."):
        return f"DOI:{ident}"
    return ident


def graph(ident: str, kind: str, limit: int) -> List[Dict[str, Any]]:
    """kind = 'citations' or 'references'."""
    pid = _s2_id(ident)
    headers = {}
    key = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
    if key:
        headers["x-api-key"] = key
    fields = "title,authors,year,venue,url,externalIds,openAccessPdf,abstract,tldr,citationCount"
    r = _get(f"https://api.semanticscholar.org/graph/v1/paper/{pid}/{kind}",
             params={"fields": fields, "limit": limit}, headers=headers)
    if not r or r.status_code != 200:
        return []
    out = []
    for item in r.json().get("data", []):
        p = item.get("citingPaper") or item.get("citedPaper") or {}
        ext = p.get("externalIds") or {}
        out.append({
            "source": f"semanticscholar/{kind}",
            "title": p.get("title"),
            "authors": [a.get("name") for a in (p.get("authors") or [])],
            "year": p.get("year"),
            "venue": p.get("venue"),
            "id": (f"arXiv:{ext['ArXiv']}" if ext.get("ArXiv") else ext.get("DOI") or p.get("paperId")),
            "url": p.get("url"),
            "citationCount": p.get("citationCount"),
            "pdf": (p.get("openAccessPdf") or {}).get("url"),
            "abstract": p.get("abstract") or (p.get("tldr") or {}).get("text"),
        })
    return out


def print_human(rows: List[Dict[str, Any]]):
    if not rows:
        print("No results.")
        return
    for i, r in enumerate(rows, 1):
        authors = ", ".join((r.get("authors") or [])[:4])
        if r.get("authors") and len(r["authors"]) > 4:
            authors += " et al."
        cc = f" | cited {r['citationCount']}" if r.get("citationCount") is not None else ""
        print(f"[{i}] {r.get('title')}")
        print(f"    {authors} ({r.get('year')}) — {r.get('venue')} [{r.get('source')}]{cc}")
        print(f"    id: {r.get('id')}")
        if r.get("pdf"):
            print(f"    pdf: {r['pdf']}")
        if r.get("abstract"):
            ab = r["abstract"]
            print(f"    {ab[:280]}{'...' if len(ab) > 280 else ''}")
        print()


def _slug(text: str, maxlen: int = 60) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return (s[:maxlen].rstrip("-")) or "results"


def render_markdown(rows: List[Dict[str, Any]], label: str) -> str:
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [f"# Paper lookup: {label}", "", f"_Generated: {ts} — {len(rows)} result(s)_", ""]
    for i, raw_row in enumerate(rows, 1):
        r = normalize_row(raw_row)
        authors = ", ".join((r.get("authors") or [])[:4])
        if r.get("authors") and len(r["authors"]) > 4:
            authors += " et al."
        cc = f" | cited {r['citationCount']}" if r.get("citationCount") is not None else ""
        title = r["title"].replace("[", r"\[").replace("]", r"\]")
        if r.get("url"):
            lines.append(f"## {i}. [{title}]({r['url']})")
        else:
            lines.append(f"## {i}. {title}")
        lines.append(f"- {authors} ({r.get('year')}) — {r.get('venue')} [{r.get('source')}]{cc}")
        lines.append(f"- id: `{r.get('id')}`")
        if r.get("url"):
            lines.append(f"- link: <{r['url']}>")
        if r.get("pdf"):
            lines.append(f"- pdf: <{r['pdf']}>")
        lines.extend(["", "**Abstract**", "", r.get("abstract") or "_Abstract unavailable from this source._"])
        lines.append("")
    return "\n".join(lines)


def save_results(rows: List[Dict[str, Any]], out_dir: str, label: str) -> List[str]:
    """Write timestamped JSON + Markdown into out_dir (created if missing)."""
    os.makedirs(out_dir, exist_ok=True)
    normalized_rows = [normalize_row(row) for row in rows]
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    base = f"{stamp}_{_slug(label)}"
    json_path = os.path.join(out_dir, base + ".json")
    md_path = os.path.join(out_dir, base + ".md")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(normalized_rows, f, indent=2, ensure_ascii=False)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(render_markdown(normalized_rows, label))
    return [json_path, md_path]


def main():
    ap = argparse.ArgumentParser(description="Multi-source academic paper search.")
    ap.add_argument("query", nargs="?", help="Search query")
    ap.add_argument("--source", default="all",
                    choices=["all"] + list(SOURCES.keys()), help="Source API (default: all)")
    ap.add_argument("--limit", type=int, default=10, help="Max results per source")
    ap.add_argument("--id", dest="ident", help="Look up a single arXiv id or DOI")
    ap.add_argument("--citations", metavar="ID", help="Papers that cite this arXiv id / DOI")
    ap.add_argument("--references", metavar="ID", help="Papers referenced by this arXiv id / DOI")
    ap.add_argument("--json", default=True, action="store_true", help="Output JSON")
    ap.add_argument("--out-dir", dest="out_dir", default=os.getenv("PAPER_LOOKUP_OUT_DIR"),
                    help="Save timestamped JSON+Markdown into this directory "
                         "(default: $PAPER_LOOKUP_OUT_DIR if set). "
                         "Point it at a subdirectory of the current project.")
    args = ap.parse_args()

    if args.ident:
        rows = lookup_id(args.ident)
        label = args.ident
    elif args.citations:
        rows = graph(args.citations, "citations", args.limit)
        label = f"citations of {args.citations}"
    elif args.references:
        rows = graph(args.references, "references", args.limit)
        label = f"references of {args.references}"
    elif args.query:
        srcs = DEFAULT_SOURCES if args.source == "all" else [args.source]
        rows = []
        for s in srcs:
            print(f"  [info] querying {s}...", file=sys.stderr)
            rows.extend(SOURCES[s](args.query, args.limit))
        rows = dedupe(rows)
        label = args.query
    else:
        ap.error("provide a query, --id, --citations, or --references")

    rows = [normalize_row(row) for row in rows]

    if args.out_dir and rows:
        for path in save_results(rows, args.out_dir, label):
            print(f"  [info] saved {path}", file=sys.stderr)

    if args.json:
        print(json.dumps(rows, indent=2, ensure_ascii=False))
    else:
        print_human(rows)
    return 0 if rows else 1


if __name__ == "__main__":
    sys.exit(main())
