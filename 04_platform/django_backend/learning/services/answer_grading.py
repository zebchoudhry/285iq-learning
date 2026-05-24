"""
Short-answer comparison with tolerant normalisation (STEM-friendly).
"""
from __future__ import annotations

import re
import unicodedata
from typing import Optional, Tuple


def _normalise_text(s: str) -> str:
    s = unicodedata.normalize("NFKC", s or "")
    s = s.lower().strip()
    s = re.sub(r"\s+", " ", s)
    return s


def _strip_wrapping_punctuation(s: str) -> str:
    return s.strip(" \t\n\r.,;:!?\"'()[]{}|")


def _try_float(s: str) -> Optional[float]:
    t = s.replace(",", ".")
    t = re.sub(r"[^\d.\-+eE]", "", t)
    if not t or t in (".", "-", "+"):
        return None
    try:
        return float(t)
    except ValueError:
        return None


def _numeric_close(a: str, b: str, rel_tol: float = 1e-4, abs_tol: float = 1e-6) -> bool:
    fa, fb = _try_float(a), _try_float(b)
    if fa is None or fb is None:
        return False
    if fa == fb:
        return True
    diff = abs(fa - fb)
    if diff <= abs_tol:
        return True
    scale = max(abs(fa), abs(fb), 1e-12)
    return diff / scale <= rel_tol


def _split_answer_tokens(s: str) -> list[str]:
    parts = re.split(r"\s+or\s+|;\s*|,\s*", s, flags=re.IGNORECASE)
    return [_strip_wrapping_punctuation(p) for p in parts if _strip_wrapping_punctuation(p)]


def answers_equivalent(student_answer: str, correct_answer: str) -> Tuple[bool, str]:
    """
    Return (is_equivalent, method) where method is 'exact', 'numeric', 'token_set', or 'none'.
    """
    sa = _normalise_text(student_answer or "")
    ca = _normalise_text(correct_answer or "")
    if not sa or not ca:
        return False, "none"

    sa_cmp = re.sub(r"\s*([=+\-*/])\s*", r"\1", sa.replace(" ", ""))
    ca_cmp = re.sub(r"\s*([=+\-*/])\s*", r"\1", ca.replace(" ", ""))
    if sa_cmp == ca_cmp:
        return True, "exact"

    if sa == ca:
        return True, "exact"

    if _numeric_close(sa, ca):
        return True, "numeric"

    stoks = sorted(_split_answer_tokens(sa))
    ctoks = sorted(_split_answer_tokens(ca))
    if stoks and ctoks and len(stoks) == len(ctoks):
        if all(
            a == b or _numeric_close(a, b)
            for a, b in zip(stoks, ctoks)
        ):
            return True, "token_set"

    if stoks and ctoks and all(_try_float(t) is not None for t in stoks + ctoks):
        if sorted(float(_try_float(t)) for t in stoks) == sorted(float(_try_float(t)) for t in ctoks):
            return True, "token_set"

    return False, "none"
