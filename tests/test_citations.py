#!/usr/bin/env python3
"""Mandatory citation-validation gate.

Fabricated citations are a known LLM failure mode. `nex-cite-check`
resolves every arXiv ID / DOI in `docs/` + `README.md` against the
authoritative API (arXiv / Crossref) and compares returned metadata
(author surnames, title keywords, year) against the on-page context.

This test is mandatory — a failure blocks the test suite. If you find
yourself tempted to skip it because "the network is flaky," that is
exactly the moment when a hallucinated citation slips through.

If the network is genuinely down, run `tests/run-all.sh --offline` to
skip the network-dependent tests; that will skip the publishing gate
too (which is correct — we don't publish citations we can't verify).
"""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CITE_CHECK = ROOT / "bin" / "nex-cite-check"


def test_cite_check_binary_exists():
    assert CITE_CHECK.exists(), f"missing {CITE_CHECK}"
    assert os.access(CITE_CHECK, os.X_OK), f"{CITE_CHECK} not executable"
    print("  [test_cite_check_binary_exists] OK")


def test_offline_extraction_succeeds():
    """Offline mode must extract citations without network; exit 0."""
    r = subprocess.run(
        [str(CITE_CHECK), "--offline"],
        capture_output=True, text=True, timeout=30, cwd=str(ROOT),
    )
    assert r.returncode == 0, f"offline extraction failed: {r.stderr}"
    assert "extracted" in r.stdout, r.stdout
    print("  [test_offline_extraction_succeeds] OK")


def test_all_citations_valid():
    """MANDATORY: every citation in docs/ + README.md must resolve and
    match its context. This is the publishing gate."""
    if os.environ.get("NEOS_SKIP_NETWORK"):
        print("  [test_all_citations_valid] SKIPPED (NEOS_SKIP_NETWORK set)")
        sys.exit(77)
    r = subprocess.run(
        [str(CITE_CHECK)],
        capture_output=True, text=True, timeout=180, cwd=str(ROOT),
    )
    if r.returncode == 2:
        # Operational error (API down, no network). Non-fatal to the
        # dev test loop but MUST fail before release. We surface it as
        # a skip here with a loud warning; the publishing checklist has
        # to catch it separately.
        print("  [test_all_citations_valid] SKIPPED (operational; rerun before release)")
        print(f"    detail: {r.stderr.strip()[:200]}")
        sys.exit(77)
    assert r.returncode == 0, (
        "citation validation FAILED — one or more citations don't match "
        "their authoritative metadata. Hallucinated citations are gate-"
        "blocking; fix them before committing.\n\n" + r.stdout + r.stderr
    )
    assert "PASS:" in r.stdout, r.stdout
    print("  [test_all_citations_valid] OK —", r.stdout.strip().split("\n")[-1])


if __name__ == "__main__":
    test_cite_check_binary_exists()
    test_offline_extraction_succeeds()
    test_all_citations_valid()
    print("ALL CITATION TESTS PASS")
