#!/usr/bin/env python3
"""Tests for the HLE text-only filter.

Scope: verify that `lib.hle.filter_text_only` correctly identifies
text-only rows from an HLE-shaped iterable. Fixture has 10 synthetic
rows matching the HLE dataset schema — 7 text-only (empty/whitespace
`image` field) and 3 multimodal (non-empty `image`).

Why this matters: the kernel's HLE gate (`filter: text-only` in
`config/reasoning-benchmarks.example.yaml`) relies on this filter to
exclude multimodal questions before scoring. A bug here silently scores
an agent's multimodal capability as part of its text-reasoning grade —
wrong axis, wrong threshold, admits weak text agents.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from lib.hle import filter_text_only, is_text_only, parse_score_line, pass_rate


FIXTURE = ROOT / "tests" / "fixtures" / "hle-format-sample.jsonl"


def load_fixture():
    return [json.loads(line) for line in FIXTURE.read_text().splitlines() if line.strip()]


def test_fixture_loads():
    rows = load_fixture()
    assert len(rows) == 10, f"expected 10 rows, got {len(rows)}"
    assert all("id" in r and "image" in r for r in rows), "every row must have id and image fields"
    print("  [test_fixture_loads] OK (10 rows)")


def test_filter_keeps_only_text_rows():
    rows = load_fixture()
    text_only = filter_text_only(rows)
    # Expected text-only rows: t001, t002, t004, t006, t007 (whitespace-only image), t008, t010
    expected_ids = {"t001", "t002", "t004", "t006", "t007", "t008", "t010"}
    got_ids = {r["id"] for r in text_only}
    assert got_ids == expected_ids, f"expected {expected_ids}, got {got_ids}"
    print(f"  [test_filter_keeps_only_text_rows] OK ({len(text_only)} text-only kept)")


def test_filter_drops_multimodal_rows():
    rows = load_fixture()
    text_only_ids = {r["id"] for r in filter_text_only(rows)}
    # Multimodal rows must NOT appear
    multimodal_ids = {"t003", "t005", "t009"}
    assert text_only_ids.isdisjoint(multimodal_ids), \
        f"multimodal rows leaked into text-only: {text_only_ids & multimodal_ids}"
    print("  [test_filter_drops_multimodal_rows] OK")


def test_is_text_only_edge_cases():
    # Empty string → text-only
    assert is_text_only({"image": ""}) is True
    # None → text-only
    assert is_text_only({"image": None}) is True
    # Missing key → text-only
    assert is_text_only({"id": "x"}) is True
    # Whitespace-only → text-only (common HLE encoding artifact)
    assert is_text_only({"image": "   "}) is True
    # Non-empty url → multimodal
    assert is_text_only({"image": "http://x/y.png"}) is False
    # Non-empty filename → multimodal
    assert is_text_only({"image": "fig_1.jpg"}) is False
    print("  [test_is_text_only_edge_cases] OK")


def test_filter_is_idempotent():
    rows = load_fixture()
    once = filter_text_only(rows)
    twice = filter_text_only(once)
    assert once == twice, "filtering a text-only set must be a no-op"
    print("  [test_filter_is_idempotent] OK")


def test_filter_preserves_row_integrity():
    rows = load_fixture()
    text_only = filter_text_only(rows)
    # Each surviving row must be the same dict-shape it came in with
    for r in text_only:
        assert "question" in r and "answer" in r and "id" in r
        assert "canary" in r, "canary field must be preserved (leak-detection)"
    print("  [test_filter_preserves_row_integrity] OK")


def test_parse_score_line():
    # Well-formed correct
    ok = parse_score_line("t001\tcorrect\t0.95")
    assert ok == ("t001", True, 0.95), ok
    # Well-formed incorrect
    bad = parse_score_line("t002\tincorrect\t0.80")
    assert bad == ("t002", False, 0.80), bad
    # No confidence field → default 1.0
    plain = parse_score_line("t003\tcorrect")
    assert plain == ("t003", True, 1.0), plain
    # Malformed → None
    assert parse_score_line("garbage") is None
    # Unknown judgment → None
    assert parse_score_line("t001\tmaybe\t0.5") is None
    print("  [test_parse_score_line] OK")


def test_pass_rate():
    results = [
        ("t001", True, 1.0),
        ("t002", False, 1.0),
        ("t003", True, 1.0),
        ("t004", True, 1.0),
    ]
    # 3/4 = 75%
    rate = pass_rate(results)
    assert abs(rate - 75.0) < 0.001, rate
    # Empty → 0%
    assert pass_rate([]) == 0.0
    print("  [test_pass_rate] OK")


if __name__ == "__main__":
    test_fixture_loads()
    test_filter_keeps_only_text_rows()
    test_filter_drops_multimodal_rows()
    test_is_text_only_edge_cases()
    test_filter_is_idempotent()
    test_filter_preserves_row_integrity()
    test_parse_score_line()
    test_pass_rate()
    print("ALL HLE FILTER TESTS PASS")
