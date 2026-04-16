"""HLE (Humanity's Last Exam) utilities.

Text-only filter, scoring helpers. Shared between `bin/nex-reasoning-bench`
and `tests/test_hle_filter.py` so both exercise the same code path.

HLE row schema (from huggingface.co/datasets/cais/hle):
  - id: str
  - question: str
  - answer: str
  - answer_type: "exactMatch" | "multipleChoice"
  - category: str (e.g. "Math", "Humanities/Social Science")
  - image: str                # empty string or a url/path when multimodal
  - image_preview: str | None
  - raw_subject: str
  - author_name: str
  - canary: str               # leak-detection canary

A row is "text-only" iff its `image` field is empty (the HLE authors
encode the absence of a visual element as an empty string, not as
absent/None).
"""
from typing import Iterable, List, Mapping


def is_text_only(row: Mapping) -> bool:
    """True iff the HLE row has no image component.

    Accepts any mapping-like (dict, HF dataset row). Treats `image` field
    that is empty-string, None, or missing as text-only. A non-empty
    `image` (url, filepath, or base64) marks the row multimodal.
    """
    img = row.get("image")
    if img is None or img == "":
        return True
    if isinstance(img, str) and img.strip() == "":
        return True
    return False


def filter_text_only(rows: Iterable[Mapping]) -> List[Mapping]:
    """Keep only text-only rows from an HLE-shaped iterable."""
    return [r for r in rows if is_text_only(r)]


def parse_score_line(line: str):
    """Parse an LLM-as-judge scoring line of the form:
        <row_id>\t<judgment>\t<confidence>
    where judgment is one of "correct" / "incorrect" / "unclear".
    Returns (row_id, is_correct: bool, confidence: float) or None on parse
    failure.
    """
    parts = line.strip().split("\t")
    if len(parts) < 2:
        return None
    row_id = parts[0]
    judgment = parts[1].strip().lower()
    if judgment not in ("correct", "incorrect", "unclear"):
        return None
    try:
        conf = float(parts[2]) if len(parts) >= 3 else 1.0
    except ValueError:
        conf = 1.0
    return (row_id, judgment == "correct", conf)


def pass_rate(results) -> float:
    """Given an iterable of (row_id, is_correct, confidence) triples, return
    the unweighted pass rate in [0, 100]."""
    results = list(results)
    if not results:
        return 0.0
    correct = sum(1 for _, ok, _ in results if ok)
    return 100.0 * correct / len(results)
