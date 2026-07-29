"""
knowledge_updater.py — Skill 223: urban-wildlife-rescue-coordinator
Production-grade crawl pipeline for the knowledge base. Fetches latest papers
and news from ArXiv, Semantic Scholar, and RSS feeds, applies SHA256 dedup and
composite scoring, then appends new entries to SECOND-KNOWLEDGE-BRAIN.md.

Dependencies: pip install requests feedparser python-dateutil
Usage:
    python -m tools.knowledge_updater [--dry-run] [--news-only] [--keywords ...]
"""
import argparse
import hashlib
import logging
import math
import os
import re
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

try:
    import requests as http_requests
except ImportError as exc:
    http_requests: Any = None  # type: ignore[no-redef]

try:
    import feedparser as _feedparser_lib
except ImportError:
    _feedparser_lib: Any = None  # type: ignore[no-redef]

try:
    from dateutil import parser as dateutil_parser
except ImportError:
    dateutil_parser = None


PROJECT_ROOT = Path(__file__).resolve().parent.parent
BRAIN_PATH = PROJECT_ROOT / "SECOND-KNOWLEDGE-BRAIN.md"
LOG_DIR = PROJECT_ROOT / "logs"
STATE_FILE = PROJECT_ROOT / ".knowledge_state.json"

LOG_DIR.mkdir(exist_ok=True)

logger = logging.getLogger("knowledge_updater")
logger.setLevel(logging.INFO)
if not logger.handlers:
    fh = logging.FileHandler(LOG_DIR / "knowledge_update.log", encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(fh)
    sh = logging.StreamHandler(sys.stderr)
    sh.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    logger.addHandler(sh)


KNOWLEDGE_CONFIG = {
    "domain": "Urban Wildlife Rescue & Rehabilitation",
    "keywords": [
        "urban wildlife rescue",
        "wildlife triage rehabilitation",
        "capture handling transport safety",
        "wildlife zoonosis handler",
        "human-wildlife conflict coexistence",
        "wildlife release criteria",
    ],
    "arxiv_categories": ["q-bio.QM", "q-bio.PE", "stat.AP"],
    "arxiv_base": "https://export.arxiv.org/api/query",
    "semantic_scholar_base": "https://api.semanticscholar.org/graph/v1/paper/search",
    "rss_feeds": [],
    "scoring_weights": {
        "recency": 0.4,
        "keyword_relevance": 0.4,
        "citation_count": 0.2,
    },
    "max_results_per_source": 10,
    "max_new_entries_per_run": 20,
    "recency_window_days": 730,
    "citation_log_base": 1000,
    "request_timeout_seconds": 30,
    "max_retries": 3,
    "retry_base_delay_seconds": 2.0,
    "respect_rate_limit_wait_seconds": 1.0,
}


def _check_dependencies() -> List[str]:
    missing: List[str] = []
    if http_requests is None:
        missing.append("requests")
    if _feedparser_lib is None:
        missing.append("feedparser")
    if dateutil_parser is None:
        missing.append("python-dateutil")
    return missing


def load_state() -> Dict[str, Any]:
    if not STATE_FILE.exists():
        return {"last_successful_run": None, "runs": 0, "total_entries_added": 0, "errors": []}
    try:
        return __import__("json").loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"last_successful_run": None, "runs": 0, "total_entries_added": 0, "errors": []}


def save_state(data: Dict[str, Any]) -> None:
    import json

    data["last_updated"] = datetime.now(timezone.utc).isoformat()
    STATE_FILE.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def fetch_with_retry(url: str, params: Optional[Dict] = None, max_retries: int = 3, base_delay: float = 2.0):
    if http_requests is None:
        logger.error("requests library not available — cannot fetch %s", url)
        return None
    cfg = KNOWLEDGE_CONFIG
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                delay = base_delay * (2 ** attempt)
                logger.info("Retry %d/%d (waiting %.1fs)", attempt + 1, max_retries, delay)
                time.sleep(delay)
            resp = http_requests.get(
                url,
                params=params or {},
                timeout=cfg.get("request_timeout_seconds", 30),
                headers={"User-Agent": "urban-wildlife-rescue-coordinator/1.0"},
            )
            if resp.status_code == 429:
                retry_after = resp.headers.get("Retry-After", str(base_delay * (2 ** attempt)))
                logger.warning("Rate limited (429) on attempt %d — retry in %ss", attempt + 1, retry_after)
                if attempt < max_retries - 1:
                    try:
                        time.sleep(float(retry_after))
                    except ValueError:
                        time.sleep(base_delay * (2 ** attempt))
                    continue
                return None
            if resp.status_code >= 500:
                logger.warning("Server error %d on attempt %d", resp.status_code, attempt + 1)
                if attempt < max_retries - 1:
                    continue
                return None
            resp.raise_for_status()
            return resp
        except Exception as ex:
            logger.warning("Request failed attempt %d/%d: %s", attempt + 1, max_retries, ex)
            if attempt < max_retries - 1:
                time.sleep(base_delay)
            else:
                return None
    return None


def compute_hash(identifier: str) -> str:
    return hashlib.sha256(identifier.strip().lower().encode()).hexdigest()


def load_existing_hashes(brain_path: Optional[Path] = None) -> Set[str]:
    p = brain_path or BRAIN_PATH
    if not p.exists():
        logger.warning("Knowledge base not found: %s", p)
        return set()
    hashes: Set[str] = set()
    content = p.read_text(encoding="utf-8")
    for m in re.finditer(r"\*\*DOI/URL:\*\*\s*(\S+)", content):
        hashes.add(compute_hash(m.group(1)))
    logger.debug("Loaded %d existing hashes from knowledge base", len(hashes))
    return hashes


def score_entry(entry: Dict[str, Any], keywords: List[str], now: datetime) -> float:
    pub = entry.get("published_date")
    recency = 0.0
    if pub is not None:
        try:
            delta_days = max(0.0, (now - pub).days)
            recency = max(0.0, 1.0 - delta_days / float(KNOWLEDGE_CONFIG["recency_window_days"]))
        except Exception:
            recency = 0.0

    text_parts = [(entry.get("title") or ""), (entry.get("abstract") or "")]
    for kw_field in entry.get("keywords", []):
        if isinstance(kw_field, str):
            text_parts.append(kw_field)
        elif isinstance(kw_field, list):
            text_parts.extend(k for k in kw_field if isinstance(k, str))
    text = " ".join(text_parts).lower()

    hits = sum(1 for kw in keywords if kw.lower() in text)
    relevance = min(hits / max(len(keywords), 1), 1.0)

    cit = entry.get("citation_count", 0) or 0
    cit_base = float(KNOWLEDGE_CONFIG.get("citation_log_base", 1000))
    cit_score = min(math.log1p(cit) / math.log1p(cit_base), 1.0)

    w = KNOWLEDGE_CONFIG["scoring_weights"]
    composite = round(
        (recency * w["recency"] + relevance * w["keyword_relevance"] + cit_score * w["citation_count"]) * 10.0,
        2,
    )
    return composite


def fetch_arxiv(keywords: List[str]) -> List[Dict[str, Any]]:
    if http_requests is None:
        logger.info("Skipping ArXiv: requests library not available")
        return []
    cats = KNOWLEDGE_CONFIG.get("arxiv_categories", [])
    if not cats:
        logger.info("Skipping ArXiv: no categories configured")
        return []
    cat_query = " OR ".join(f"cat:{c}" for c in cats)
    kw_query = " OR ".join(f'"{k}"' for k in keywords[:5])
    q = f"({cat_query}) AND ({kw_query})"
    resp = fetch_with_retry(
        KNOWLEDGE_CONFIG["arxiv_base"],
        {
            "search_query": q,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
            "max_results": KNOWLEDGE_CONFIG["max_results_per_source"],
        },
    )
    if resp is None:
        return []
    ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
    try:
        root = ET.fromstring(resp.content)
    except ET.ParseError as e:
        logger.error("ArXiv XML parse error: %s", e)
        return []
    out: List[Dict[str, Any]] = []
    for entry in root.findall("atom:entry", ns):
        t = entry.find("atom:title", ns)
        s = entry.find("atom:summary", ns)
        i = entry.find("atom:id", ns)
        p = entry.find("atom:published", ns)
        title = (t.text or "").strip().replace("\n", " ") if t is not None else ""
        url = (i.text or "").strip() if i is not None else ""
        if not title or not url:
            continue
        pub = None
        if p is not None and p.text and dateutil_parser:
            try:
                pub = dateutil_parser.parse(p.text).replace(tzinfo=None)
            except Exception:
                pass
        authors = []
        for a in entry.findall("atom:author", ns):
            nm = a.find("atom:name", ns)
            if nm is not None and nm.text:
                authors.append(nm.text.strip())
        out.append(
            {
                "title": title,
                "authors": authors[:3],
                "year": pub.year if pub else datetime.now().year,
                "venue": "ArXiv",
                "doi_or_url": url,
                "abstract": (s.text or "")[:300] if s is not None else "",
                "published_date": pub,
                "citation_count": 0,
                "source": "arxiv",
            }
        )
    logger.info("ArXiv: fetched %d results", len(out))
    return out


def fetch_semantic_scholar(keywords: List[str]) -> List[Dict[str, Any]]:
    if http_requests is None:
        logger.info("Skipping Semantic Scholar: requests library not available")
        return []
    resp = fetch_with_retry(
        KNOWLEDGE_CONFIG["semantic_scholar_base"],
        {
            "query": " ".join(keywords[:4]),
            "fields": "title,authors,year,venue,externalIds,abstract,citationCount",
            "limit": KNOWLEDGE_CONFIG["max_results_per_source"],
        },
    )
    if resp is None:
        return []
    try:
        data = resp.json()
    except ValueError as e:
        logger.error("Semantic Scholar JSON parse error: %s", e)
        return []
    out: List[Dict[str, Any]] = []
    for p in data.get("data", []):
        title = p.get("title", "")
        if not title:
            continue
        year = p.get("year") or datetime.now().year
        ext = p.get("externalIds", {})
        doi = ext.get("DOI") or (f"https://arxiv.org/abs/{ext['ArXiv']}" if ext.get("ArXiv") else "")
        if not doi:
            doi = f"https://www.semanticscholar.org/paper/{p.get('paperId', '')}"
        out.append(
            {
                "title": title,
                "authors": [a.get("name", "") for a in p.get("authors", [])[:3]],
                "year": year,
                "venue": p.get("venue") or "Unknown",
                "doi_or_url": doi,
                "abstract": (p.get("abstract") or "")[:300],
                "published_date": datetime(year, 1, 1),
                "citation_count": p.get("citationCount", 0),
                "source": "semantic_scholar",
            }
        )
    logger.info("Semantic Scholar: fetched %d results", len(out))
    return out


def fetch_rss() -> List[Dict[str, Any]]:
    if _feedparser_lib is None:
        logger.info("Skipping RSS: feedparser library not available")
        return []
    feeds = KNOWLEDGE_CONFIG.get("rss_feeds", [])
    if not feeds:
        logger.info("Skipping RSS: no feeds configured")
        return []
    out: List[Dict[str, Any]] = []
    for url in feeds:
        try:
            feed = _feedparser_lib.parse(url)
        except Exception as ex:
            logger.warning("RSS parse failed for %s: %s", url, ex)
            continue
        for item in feed.entries[:10]:
            title = item.get("title", "")
            link = item.get("link", "")
            if not title or not link:
                continue
            pp = item.get("published_parsed")
            pub = datetime(*pp[:6]) if pp else datetime.now()
            out.append(
                {
                    "title": title,
                    "authors": ["Editorial"],
                    "year": pub.year,
                    "venue": "RSS",
                    "doi_or_url": link,
                    "abstract": (item.get("summary", ""))[:200],
                    "published_date": pub,
                    "citation_count": 0,
                    "source": "rss",
                }
            )
    logger.info("RSS: fetched %d results from %d feeds", len(out), len(feeds))
    return out


def format_entry(entry: Dict[str, Any], score: float) -> str:
    d = datetime.now().strftime("%Y-%m-%d")
    authors = ", ".join(entry.get("authors", [])) or "Unknown"
    lines = [
        f"\n### {d} — {entry.get('title', 'Untitled')}",
        f"- **Authors:** {authors}",
        f"- **Year:** {entry.get('year', '')}",
        f"- **Venue:** {entry.get('venue', 'Unknown')}",
        f"- **DOI/URL:** {entry.get('doi_or_url', '')}",
        f"- **Relevance Score:** {score}/10",
        f"- **Source:** {entry.get('source', 'unknown')}",
        f"- **Key Finding:** {entry.get('abstract', 'No abstract available.')}",
        "",
    ]
    return "\n".join(lines)


def append_to_brain(entries: List[Dict[str, Any]], dry_run: bool = False) -> int:
    if not BRAIN_PATH.exists():
        logger.error("Knowledge base not found: %s", BRAIN_PATH)
        return 0
    existing = load_existing_hashes()
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    new: List[Dict[str, Any]] = []
    for e in entries:
        doi = e.get("doi_or_url", "")
        if not doi:
            continue
        h = compute_hash(doi)
        if h in existing:
            continue
        existing.add(h)
        new.append(e)
    if not new:
        logger.info("No new entries to add (all %d candidates already present)", len(entries))
        return 0
    for e in new:
        e["_score"] = score_entry(e, KNOWLEDGE_CONFIG["keywords"], now)
    new.sort(key=lambda x: x.get("_score", 0), reverse=True)
    new = new[: KNOWLEDGE_CONFIG["max_new_entries_per_run"]]
    text = "".join(format_entry(e, e.get("_score", 0)) for e in new)
    if dry_run:
        logger.info("[DRY RUN] Would append %d entries (top score: %s)", len(new), new[0].get("_score", "N/A"))
        for e in new:
            logger.info("  [DRY] %s (score=%s)", e.get("title", "?")[:80], e.get("_score", "?"))
        return len(new)
    content = BRAIN_PATH.read_text(encoding="utf-8")
    if "## 7. Knowledge Update Log" in content:
        content = content.rstrip() + "\n" + text
    else:
        content = content.rstrip() + "\n## 7. Knowledge Update Log\n" + text
    BRAIN_PATH.write_text(content, encoding="utf-8")
    logger.info("Appended %d new entries to knowledge base", len(new))
    return len(new)


def main() -> None:
    missing = _check_dependencies()
    if missing:
        logger.warning(
            "Missing Python packages: %s. Install with: pip install %s",
            ", ".join(missing),
            " ".join(missing),
        )
        if "requests" in missing and len(missing) > 1:
            pass
        elif all(m == "feedparser" or m == "dateutil" for m in missing) and "requests" not in missing:
            pass

    ap = argparse.ArgumentParser(
        description="urban-wildlife-rescue-coordinator knowledge crawl pipeline"
    )
    ap.add_argument("--dry-run", action="store_true", help="Preview without modifying knowledge base")
    ap.add_argument("--news-only", action="store_true", help="Only crawl RSS feeds, skip academic sources")
    ap.add_argument(
        "--keywords",
        nargs="+",
        default=None,
        help="Override default keyword list for this run",
    )
    ap.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = ap.parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)
        for h in logger.handlers:
            h.setLevel(logging.DEBUG)

    keywords = args.keywords if args.keywords else KNOWLEDGE_CONFIG["keywords"]

    state = load_state()
    state["runs"] = state.get("runs", 0) + 1
    logger.info(
        "=== Knowledge Crawl Run #%d | dry=%s | news-only=%s | %s ===",
        state["runs"],
        args.dry_run,
        args.news_only,
        datetime.now().isoformat(),
    )

    all_entries: List[Dict[str, Any]] = []
    error_count = 0

    if not args.news_only:
        try:
            all_entries += fetch_arxiv(keywords)
        except Exception as e:
            logger.error("ArXiv fetch failed: %s", e)
            error_count += 1
        time.sleep(KNOWLEDGE_CONFIG.get("respect_rate_limit_wait_seconds", 1.0))
        try:
            all_entries += fetch_semantic_scholar(keywords)
        except Exception as e:
            logger.error("Semantic Scholar fetch failed: %s", e)
            error_count += 1
        time.sleep(KNOWLEDGE_CONFIG.get("respect_rate_limit_wait_seconds", 1.0))

    try:
        all_entries += fetch_rss()
    except Exception as e:
        logger.error("RSS fetch failed: %s", e)
        error_count += 1

    logger.info("Total candidates: %d (errors: %d)", len(all_entries), error_count)

    try:
        n_added = append_to_brain(all_entries, args.dry_run)
    except Exception as e:
        logger.error("Failed to append to knowledge base: %s", e)
        state["errors"].append(str(e))
        save_state(state)
        sys.exit(1)

    state["total_entries_added"] = state.get("total_entries_added", 0) + n_added
    state["last_successful_run"] = datetime.now(timezone.utc).isoformat()
    if error_count:
        state["errors"].append(f"Run #{state['runs']}: {error_count} source errors")
    save_state(state)

    logger.info(
        "=== Complete: added %d entries, total all-time: %d ===",
        n_added,
        state["total_entries_added"],
    )


if __name__ == "__main__":
    main()
