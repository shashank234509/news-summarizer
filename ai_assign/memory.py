"""
Memory module for the Newsletter Agent.

Maintains a persistent archive of previously covered articles in
`memory/news_archive.json` so the agent can detect and skip duplicates
across runs — making the agent truly stateful and agentic.

Archive schema (JSON):
[
    {
        "title": "...",
        "url": "...",
        "summary": "...",
        "covered_date": "2025-05-14"
    },
    ...
]
"""

import json, os, datetime
from typing import List, Dict, Set
from difflib import SequenceMatcher

import config

# ── Helpers ────────────────────────────────────────────────────────────

def _archive_path() -> str:
    """Return the full path to the news archive JSON file."""
    return os.path.join(config.MEMORY_DIR, "news_archive.json")


def _normalise(text: str) -> str:
    """Lower-case and strip whitespace for fuzzy matching."""
    return " ".join(text.lower().split())


def _title_similarity(a: str, b: str) -> float:
    """Return 0-1 similarity score between two titles."""
    return SequenceMatcher(None, _normalise(a), _normalise(b)).ratio()


# ── Public API ─────────────────────────────────────────────────────────

def load_archive() -> List[Dict]:
    """Load the news archive from disk. Returns [] if none exists."""
    path = _archive_path()
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def save_archive(archive: List[Dict]) -> None:
    """Persist the news archive to disk."""
    os.makedirs(config.MEMORY_DIR, exist_ok=True)
    path = _archive_path()
    with open(path, "w") as f:
        json.dump(archive, f, indent=2, ensure_ascii=False)


def get_covered_urls(archive: List[Dict]) -> Set[str]:
    """Return a set of all URLs that have been covered before."""
    return {entry.get("url", "") for entry in archive}


def get_covered_titles(archive: List[Dict]) -> List[str]:
    """Return a list of all previously covered titles."""
    return [entry.get("title", "") for entry in archive]


def is_duplicate(article: Dict, archive: List[Dict],
                 url_key: str = "href",
                 title_key: str = "title",
                 similarity_threshold: float = 0.80) -> bool:
    """
    Check whether an article has already been covered.

    Matching strategy (any one triggers a duplicate):
      1. Exact URL match
      2. Fuzzy title match (>= similarity_threshold)
    """
    url = article.get(url_key, "")
    title = article.get(title_key, "")

    covered_urls = get_covered_urls(archive)
    if url and url in covered_urls:
        return True

    for prev_title in get_covered_titles(archive):
        if title and _title_similarity(title, prev_title) >= similarity_threshold:
            return True

    return False


def deduplicate_articles(articles: List[Dict],
                         url_key: str = "href",
                         title_key: str = "title") -> List[Dict]:
    """
    Filter out articles that were already covered in past newsletters.
    Prints which articles were skipped and why.
    Returns the list of NEW (unseen) articles only.
    """
    archive = load_archive()
    if not archive:
        print("  📂  No previous archive found — all articles are new")
        return articles

    print(f"  📂  Loaded archive with {len(archive)} previously covered articles")

    new_articles = []
    for article in articles:
        if is_duplicate(article, archive, url_key, title_key):
            print(f"  🔁  SKIPPED (duplicate): {article.get(title_key, '?')[:60]}")
        else:
            new_articles.append(article)

    skipped = len(articles) - len(new_articles)
    print(f"  ✅  {len(new_articles)} new articles | {skipped} duplicates filtered out")
    return new_articles


def archive_articles(articles: List[Dict]) -> None:
    """
    Add the current newsletter's articles to the persistent archive.
    Called after the newsletter is successfully generated.
    """
    archive = load_archive()
    today = datetime.datetime.now().strftime("%Y-%m-%d")

    for a in articles:
        archive.append({
            "title": a.get("title", ""),
            "url": a.get("url", a.get("href", "")),
            "summary": a.get("summary", a.get("body", "")),
            "covered_date": today,
        })

    save_archive(archive)
    print(f"  💾  Archived {len(articles)} articles → {_archive_path()}")
