"""
Template engine for numeric and formula-based questions.

Each template is a small function that draws fresh numbers from a seeded
random generator, builds the question text, and works the answer out by
calculation, so every question is right by construction and a template can
produce thousands of distinct questions. The wording of every template is
written by us; nothing is copied from exam papers or other sites.

A template is registered with @template and returns a question dict (built
with make_question or mcq) or None when the numbers it drew do not give a
clean question, in which case the engine simply draws again.

    @template(code="hcf_two_numbers", subject="mathematics",
              topic="Number", lessons=["1.4"])
    def hcf_two_numbers(rng):
        ...
"""
import random
import re
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from fractions import Fraction
from typing import Callable, Dict, Iterable, List, Optional

SOURCE_PREFIX = "285IQ template: "


@dataclass(frozen=True)
class Template:
    code: str
    subject: str
    topic: str
    lessons: tuple
    build: Callable[[random.Random], Optional[Dict]]


REGISTRY: List[Template] = []


def template(*, code: str, subject: str, topic: str, lessons: Iterable[str]):
    """Register a question template for lessons identified by number, e.g. "1.4"."""

    def decorator(fn):
        if any(t.code == code for t in REGISTRY):
            raise ValueError(f"Duplicate template code: {code}")
        REGISTRY.append(Template(code, subject.lower(), topic_key(topic), tuple(lessons), fn))
        return fn

    return decorator


def topic_key(name: str) -> str:
    """
    Topic names compared loosely, because the curriculum has near-duplicate spellings
    ('Number' and 'Numbers', 'Rates of Change' and 'Rates of Changes').
    """
    return re.sub(r"[^a-z]", "", (name or "").lower()).rstrip("s")


def load_all_templates() -> List[Template]:
    """Import every template module so that REGISTRY is populated."""
    from learning.generators import (  # noqa: F401
        templates_chemistry_calculations, templates_maths, templates_physics_equations, templates_science,
    )

    return REGISTRY


def lesson_number(title: str) -> Optional[str]:
    """'1.10 - Adding & Subtracting Fractions' -> '1.10'."""
    m = re.match(r"\s*(\d+\.\d+)\b", title or "")
    return m.group(1) if m else None


def templates_for(subject: str, topic: str, lesson_title: str) -> List[Template]:
    number = lesson_number(lesson_title)
    if not number:
        return []
    subject, topic = (subject or "").strip().lower(), topic_key(topic)
    return [
        t for t in load_all_templates()
        if t.subject == subject and t.topic == topic and number in t.lessons
    ]


# ---------------------------------------------------------------------------
# Building question dicts
# ---------------------------------------------------------------------------
def make_question(
    text: str,
    answer: str,
    *,
    difficulty: int = 2,
    marks: int = 1,
    explanation: str = "",
    question_type: str = "short_answer",
    options: Optional[List[Dict]] = None,
) -> Dict:
    return {
        "question_text": text.strip(),
        "correct_answer": str(answer).strip(),
        "question_type": question_type,
        "difficulty_level": difficulty,
        "marks_available": marks,
        "explanation": explanation.strip(),
        "options": options,
    }


def mcq(
    rng: random.Random,
    text: str,
    correct: str,
    wrong: List[str],
    *,
    difficulty: int = 2,
    explanation: str = "",
) -> Optional[Dict]:
    """Multiple choice with the correct answer shuffled among the wrong ones."""
    wrong = list(dict.fromkeys(w for w in wrong if w != correct))
    if len(wrong) < 3:
        return None
    options = [{"text": correct, "correct": True}] + [
        {"text": w, "correct": False} for w in wrong[:3]
    ]
    rng.shuffle(options)
    return make_question(
        text, correct, difficulty=difficulty, explanation=explanation,
        question_type="multiple_choice", options=options,
    )


# ---------------------------------------------------------------------------
# Number formatting and maths helpers shared by the template modules
# ---------------------------------------------------------------------------
def is_terminating(q: Fraction) -> bool:
    d = q.denominator
    for p in (2, 5):
        while d % p == 0:
            d //= p
    return d == 1


def fmt_dec(d: Decimal) -> str:
    s = format(d.normalize(), "f")
    return s


def tdec(q) -> str:
    """Terminating fraction or number as a plain decimal string ('0.375', '12')."""
    q = Fraction(q)
    if not is_terminating(q):
        raise ValueError(f"{q} does not terminate")
    return fmt_dec(Decimal(q.numerator) / Decimal(q.denominator))


def money(q) -> str:
    q = Fraction(q)
    s = tdec(q)
    if "." in s and len(s.split(".")[1]) == 1:
        s += "0"
    return f"£{s}"


def frac_str(q: Fraction) -> str:
    return str(q.numerator) if q.denominator == 1 else f"{q.numerator}/{q.denominator}"


def mixed_str(q: Fraction) -> str:
    whole, rem = divmod(q.numerator, q.denominator)
    if rem == 0:
        return str(whole)
    if whole == 0:
        return f"{rem}/{q.denominator}"
    return f"{whole} {rem}/{q.denominator}"


def round_dp(x: Decimal, places: int) -> Decimal:
    return x.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)


def round_sf(x: Decimal, figures: int) -> Decimal:
    exp = x.adjusted() - figures + 1
    return x.quantize(Decimal(1).scaleb(exp), rounding=ROUND_HALF_UP)


def sci_str(x: Decimal) -> str:
    """Standard form: '3.2 × 10^5'."""
    exp = x.adjusted()
    mantissa = fmt_dec(x.scaleb(-exp))
    return f"{mantissa} × 10^{exp}"


def is_prime(n: int) -> bool:
    if n < 2:
        return False
    i = 2
    while i * i <= n:
        if n % i == 0:
            return False
        i += 1
    return True


def prime_factors(n: int) -> Dict[int, int]:
    out: Dict[int, int] = {}
    p = 2
    while p * p <= n:
        while n % p == 0:
            out[p] = out.get(p, 0) + 1
            n //= p
        p += 1
    if n > 1:
        out[n] = out.get(n, 0) + 1
    return out


# ---------------------------------------------------------------------------
# Generating questions for a lesson
# ---------------------------------------------------------------------------
def question_key(text: str, answer: str) -> tuple:
    """Two questions count as the same when the wording and the answer match."""
    return (text.strip(), str(answer).strip())


def generate_for_lesson(
    subject: str,
    topic: str,
    lesson_title: str,
    count: int,
    rng: random.Random,
    existing_keys: Iterable[tuple] = (),
) -> List[Dict]:
    """
    Up to `count` new, distinct question dicts for a lesson, spread across
    its templates. Returns fewer when the templates run out of variety.
    `existing_keys` are question_key() values already in the lesson.
    """
    templates = templates_for(subject, topic, lesson_title)
    if not templates:
        return []
    seen = set(existing_keys)
    out: List[Dict] = []
    attempts, max_attempts = 0, max(count, 1) * 40
    while len(out) < count and attempts < max_attempts:
        t = templates[len(out) % len(templates)] if attempts % 3 == 0 else rng.choice(templates)
        attempts += 1
        try:
            q = t.build(rng)
        except (ArithmeticError, ValueError, AssertionError):
            continue
        if not q:
            continue
        key = question_key(q["question_text"], q["correct_answer"])
        if key in seen:
            continue
        seen.add(key)
        q["source"] = SOURCE_PREFIX + t.code
        out.append(q)
    return out
