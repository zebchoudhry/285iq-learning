"""
Short-answer comparison with tolerant normalisation (STEM-friendly).

Numbers are compared by value only when the whole answer is a number written in the
same form as the correct answer:
  - plain numbers, ignoring a currency sign, a unit, '%' or a leading "x =":  "£12.50" = "12.5"
  - fractions must be fractions, in lowest terms:  "3/4" accepted, "6/8" and "0.75" not
  - mixed numbers must be mixed numbers:  "1 1/2" accepted, "3/2" not
  - standard form must be standard form, with 1 <= A < 10:  "3.2 x 10^5" accepted, "320000" not

Before, every non-digit was stripped before comparing, so "12" matched "1/2" and "2"
matched "Mg(OH)2".
"""
from __future__ import annotations

import math
import re
import unicodedata
from fractions import Fraction
from typing import Optional, Tuple


def _normalise_text(s: str) -> str:
    s = unicodedata.normalize("NFKC", s or "")
    s = s.replace("−", "-")
    s = s.lower().strip()
    s = re.sub(r"\s+", " ", s)
    return s


def _strip_wrapping_punctuation(s: str) -> str:
    return s.strip(" \t\n\r.,;:!?\"'()[]{}|")


# ---------------------------------------------------------------------------
# Reading a number
# ---------------------------------------------------------------------------
_UNITS = (
    "%", "°c", "°", "kg/m3", "kg/m³", "g/cm3", "g/cm³", "g/dm3", "g/dm³", "mol/dm3", "mol/dm³",
    "m/s2", "m/s²", "m/s", "km/h", "mph", "cm3", "cm³", "dm3", "dm³", "m3", "m³", "cm2", "cm²",
    "m2", "m²", "mm", "cm", "km", "kg", "mg", "kj", "kw", "kpa", "pa", "hz", "mol", "ml",
    "ohms", "ohm", "ω", "ms", "min", "hours", "hrs", "h", "j", "w", "v", "n", "g", "m", "s", "k", "l", "a",
    "degrees", "people", "years",
)
_UNIT_RE = re.compile(r"(?:\s*(?:" + "|".join(re.escape(u) for u in _UNITS) + r"))$")
_PLAIN_RE = re.compile(r"[-+]?(?:\d+(?:\.\d+)?|\.\d+)")
_FRACTION_RE = re.compile(r"([-+]?\d+)/(\d+)")
_MIXED_RE = re.compile(r"([-+]?\d+) (\d+)/(\d+)")
_SCI_RE = re.compile(r"([-+]?\d+(?:\.\d+)?)\s*(?:×|x|\*)\s*10\s*\^?\s*\(?([-+]?\d+)\)?")
_E_RE = re.compile(r"([-+]?\d+(?:\.\d+)?)e([-+]?\d+)")


def _clean_number_text(s: str) -> str:
    t = s.strip()
    t = re.sub(r"^[a-z]\s*=\s*", "", t)          # "x = 5" -> "5"
    t = re.sub(r"^[£$€]\s*", "", t)               # currency
    t = _UNIT_RE.sub("", t).strip()               # one trailing unit
    if re.fullmatch(r"[-+]?\d{1,3}(?:,\d{3})+(?:\.\d+)?", t):
        t = t.replace(",", "")                    # 1,250 -> 1250
    elif re.fullmatch(r"[-+]?\d+,\d+", t):
        t = t.replace(",", ".")                   # 2,5 -> 2.5
    return t


def _read_number(s: str) -> Optional[tuple]:
    """
    (kind, value, well_formed) for a whole-string number, else None.
    kind: 'plain', 'fraction', 'mixed' or 'sci'. well_formed means lowest terms for
    fractions and 1 <= |A| < 10 for standard form.
    """
    t = _clean_number_text(s)
    if not t:
        return None
    if m := _MIXED_RE.fullmatch(t):
        whole, num, den = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if den == 0:
            return None
        frac = Fraction(num, den)
        value = whole + (frac if whole >= 0 else -frac)
        return "mixed", value, math.gcd(num, den) == 1 and num < den
    if m := _FRACTION_RE.fullmatch(t.replace(" ", "")):
        num, den = int(m.group(1)), int(m.group(2))
        if den == 0:
            return None
        return "fraction", Fraction(num, den), math.gcd(abs(num), den) == 1
    compact = t.replace(" ", "")
    if (m := _SCI_RE.fullmatch(compact)) or (m := _E_RE.fullmatch(compact)):
        mantissa = float(m.group(1))
        return "sci", mantissa * 10 ** int(m.group(2)), 1 <= abs(mantissa) < 10
    if _PLAIN_RE.fullmatch(compact):
        return "plain", float(compact), True
    return None


def _close(a: float, b: float, rel_tol: float = 1e-4, abs_tol: float = 1e-6) -> bool:
    if a == b:
        return True
    diff = abs(a - b)
    return diff <= abs_tol or diff / max(abs(a), abs(b), 1e-12) <= rel_tol


def _numbers_equal(student: str, correct: str) -> bool:
    s, c = _read_number(student), _read_number(correct)
    if not s or not c or s[0] != c[0]:
        return False
    kind = c[0]
    if kind in ("fraction", "mixed"):
        return s[2] and s[1] == c[1]
    if kind == "sci":
        return s[2] and _close(s[1], c[1])
    return _close(s[1], c[1])


# Kept for callers that only need a float.
def _try_float(s: str) -> Optional[float]:
    n = _read_number(s)
    return float(n[1]) if n else None


def _numeric_close(a: str, b: str) -> bool:
    return _numbers_equal(a, b)


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

    sa_cmp = re.sub(r"\s*([=+\-*/:])\s*", r"\1", sa.replace(" ", ""))
    ca_cmp = re.sub(r"\s*([=+\-*/:])\s*", r"\1", ca.replace(" ", ""))
    if sa_cmp == ca_cmp or sa == ca:
        return True, "exact"

    if _numbers_equal(sa, ca):
        return True, "numeric"

    stoks = sorted(_split_answer_tokens(sa))
    ctoks = sorted(_split_answer_tokens(ca))
    if len(stoks) > 1 and len(stoks) == len(ctoks):
        if all(a == b or _numbers_equal(a, b) for a, b in zip(stoks, ctoks)):
            return True, "token_set"
        sn, cn = [_try_float(t) for t in stoks], [_try_float(t) for t in ctoks]
        if None not in sn and None not in cn and all(_close(a, b) for a, b in zip(sorted(sn), sorted(cn))):
            return True, "token_set"

    return False, "none"
