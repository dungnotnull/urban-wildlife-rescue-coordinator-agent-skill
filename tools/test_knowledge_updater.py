"""
test_knowledge_updater.py — Skill 223: urban-wildlife-rescue-coordinator
Validation: hash dedup, composite scoring, entry formatting, state management.
"""
import datetime
import json
import sys
import tempfile
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS_DIR.parent))

from tools import knowledge_updater as ku


def test_hash():
    a = ku.compute_hash("https://x.com/1")
    b = ku.compute_hash("https://x.com/1")
    c = ku.compute_hash("https://x.com/2")
    assert a == b, "same URL should produce same hash"
    assert a != c, "different URLs should produce different hashes"
    assert ku.compute_hash("  HTTPS://X.COM/1  ") == a, "hash should be case/whitespace insensitive"
    print("[OK] dedup hash — consistent and case-insensitive")


def test_score_max():
    e = {
        "title": ku.KNOWLEDGE_CONFIG["domain"],
        "abstract": " ".join(ku.KNOWLEDGE_CONFIG["keywords"]),
        "published_date": datetime.datetime.now(),
        "citation_count": 10000,
    }
    s = ku.score_entry(e, ku.KNOWLEDGE_CONFIG["keywords"], datetime.datetime.now())
    assert 7.0 <= s <= 10.0, f"matching entry should score high, got {s}"
    print(f"[OK] max-relevance score={s}")


def test_score_min():
    e = {
        "title": "Unrelated Topic",
        "abstract": "nothing to do with wildlife",
        "published_date": datetime.datetime(2020, 1, 1),
        "citation_count": 0,
    }
    s = ku.score_entry(e, ku.KNOWLEDGE_CONFIG["keywords"], datetime.datetime.now())
    assert 0.0 <= s <= 3.0, f"unrelated entry should score low, got {s}"
    print(f"[OK] min-relevance score={s}")


def test_score_old_paper():
    e = {
        "title": ku.KNOWLEDGE_CONFIG["keywords"][0],
        "abstract": " ".join(ku.KNOWLEDGE_CONFIG["keywords"]),
        "published_date": datetime.datetime(2019, 1, 1),
        "citation_count": 500,
    }
    s = ku.score_entry(e, ku.KNOWLEDGE_CONFIG["keywords"], datetime.datetime.now())
    assert 4.0 <= s <= 9.0, f"old but high-citation matching paper should score mid-high, got {s}"
    print(f"[OK] old-paper with-citations score={s}")


def test_format():
    e = {
        "title": "Test Title",
        "authors": ["Author One", "Author Two"],
        "year": 2026,
        "venue": "Test Journal",
        "doi_or_url": "https://example.com/paper",
        "abstract": "Test abstract content here.",
        "source": "semantic_scholar",
    }
    txt = ku.format_entry(e, 8.5)
    assert "DOI/URL:" in txt, "missing DOI/URL field"
    assert "Relevance Score:" in txt, "missing Relevance Score"
    assert "8.5/10" in txt, "wrong score format"
    assert "Test Title" in txt, "missing title"
    assert "Source:" in txt, "missing source field"
    print("[OK] entry formatting — all fields present")


def test_load_existing_hashes():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as tf:
        tf.write("Some text **DOI/URL:** https://doi.org/10.1234/test1 more text\n")
        tf.write("**DOI/URL:** https://doi.org/10.1234/test2\n")
        tf.write("Not a match\n")
        tf.flush()
        tmp_path = Path(tf.name)
    try:
        hashes = ku.load_existing_hashes(tmp_path)
        assert len(hashes) == 2, f"should find 2 DOIs, found {len(hashes)}"
        assert ku.compute_hash("https://doi.org/10.1234/test1") in hashes
        assert ku.compute_hash("https://doi.org/10.1234/test2") in hashes
        print("[OK] load_existing_hashes — 2 DOIs detected")
    finally:
        tmp_path.unlink(missing_ok=True)


def test_state_persistence():
    tmp_path = Path(tempfile.gettempdir()) / "_test_knowledge_state.json"
    orig = ku.STATE_FILE
    ku.STATE_FILE = tmp_path
    try:
        if tmp_path.exists():
            tmp_path.unlink()
        state = ku.load_state()
        assert state["runs"] == 0, f"initial state should have runs=0, got {state}"
        state["runs"] = 5
        state["total_entries_added"] = 42
        ku.save_state(state)
        state2 = ku.load_state()
        assert state2["runs"] == 5, f"persisted state should have runs=5, got {state2}"
        assert state2["total_entries_added"] == 42
        print("[OK] state persistence — load/save works")
    finally:
        ku.STATE_FILE = orig
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)


if __name__ == "__main__":
    test_hash()
    test_score_max()
    test_score_min()
    test_score_old_paper()
    test_format()
    test_load_existing_hashes()
    test_state_persistence()
    print("all knowledge_updater tests passed")
