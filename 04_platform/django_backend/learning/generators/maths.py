"""
Mathematics question generator. Produces question dicts in the schema expected by load_questions.
"""
import random
from typing import List, Dict, Any, Callable, Tuple


def _q(
    question_text: str,
    correct_answer: str,
    question_type: str = "short_answer",
    difficulty_level: int = 2,
    marks_available: int = 1,
    explanation: str = "",
    options: List[Dict[str, Any]] = None,
    template_code: str = None,
    steps: List[Dict[str, Any]] = None,
    skills: List[str] = None,
) -> Dict[str, Any]:
    """Build a question dict."""
    d = {
        "question_text": question_text,
        "correct_answer": correct_answer,
        "question_type": question_type,
        "difficulty_level": difficulty_level,
        "marks_available": marks_available,
        "explanation": explanation,
        "options": options,
        "template_code": template_code,
        "steps": steps if steps is not None else [],
        "skills": skills if skills is not None else [],
    }
    return d


# ---- Linear equations ----
def _linear_1() -> Dict:
    a, b, c = random.randint(2, 9), random.randint(1, 20), random.randint(5, 50)
    x_val = (c - b) / a
    if x_val == int(x_val):
        ans = f"x = {int(x_val)}"
    else:
        ans = f"x = {x_val:.2f}"
    return _q(
        f"Solve: {a}x + {b} = {c}",
        ans,
        difficulty_level=1,
        explanation=f"Subtract {b} from both sides, then divide by {a}.",
        template_code="linear_equation_simple",
        skills=["remove_constant", "divide_coefficient"],
        steps=[
            {
                "step_order": 1,
                "skill": "remove_constant",
                "expected_expression": f"subtract {b} from both sides",
                "hint_level_1": "Move the constant away from x.",
                "hint_level_2": f"Subtract {b} from both sides.",
            },
            {
                "step_order": 2,
                "skill": "divide_coefficient",
                "expected_expression": f"divide both sides by {a}",
                "hint_level_1": "Undo the multiplication on x.",
                "hint_level_2": f"Divide both sides by {a}.",
            },
        ],
    )


def _linear_2() -> Dict:
    a, b, c = random.randint(2, 9), random.randint(1, 15), random.randint(10, 40)
    x_val = (c + b) / a
    if x_val == int(x_val):
        ans = f"x = {int(x_val)}"
    else:
        ans = f"x = {x_val:.2f}"
    return _q(
        f"Solve: {a}x - {b} = {c}",
        ans,
        difficulty_level=1,
        explanation=f"Add {b} to both sides, then divide by {a}.",
    )


def _linear_3() -> Dict:
    a, b, c = random.randint(2, 6), random.randint(1, 10), random.randint(10, 60)
    x_val = c / a - b
    if abs(x_val - round(x_val)) < 0.001:
        ans = f"x = {int(round(x_val))}"
    else:
        ans = f"x = {x_val:.2f}"
    return _q(
        f"Solve: {a}(x + {b}) = {c}",
        ans,
        difficulty_level=2,
        explanation="Expand the bracket, then solve the linear equation.",
    )


# ---- Quadratics ----
def _quad_factorise() -> Dict:
    # x^2 + bx + c, factors (x+p)(x+q), p+q=b, pq=c
    p, q = random.randint(1, 6), random.randint(1, 6)
    b, c = p + q, p * q
    return _q(
        f"Factorise: x² + {b}x + {c}",
        f"(x+{p})(x+{q})",
        difficulty_level=2,
        marks_available=2,
        explanation=f"Find two numbers that multiply to {c} and add to {b}: {p} and {q}.",
    )


def _quad_solve_simple() -> Dict:
    a = random.randint(2, 12)
    return _q(
        f"What is the solution to x² = {a * a}?",
        "x = {} or x = -{}".format(a, a),
        question_type="multiple_choice",
        difficulty_level=1,
        options=[
            {"text": f"x = {a}", "correct": False},
            {"text": f"x = {a} or x = -{a}", "correct": True},
            {"text": f"x = -{a}", "correct": False},
            {"text": f"x = {a * 2}", "correct": False},
        ],
        explanation="Square root of a positive number gives both positive and negative values.",
    )


# ---- Percentages ----
def _percent_of() -> Dict:
    p, n = random.randint(10, 50), random.randint(20, 200)
    ans = round(p * n / 100, 2)
    return _q(
        f"Calculate {p}% of {n}",
        str(ans),
        difficulty_level=1,
        explanation=f"{p}% means {p}/100, so {p}/100 × {n} = {ans}.",
    )


def _percent_increase() -> Dict:
    n, p = random.randint(50, 200), random.randint(5, 30)
    ans = round(n * (1 + p / 100), 2)
    return _q(
        f"Increase {n} by {p}%",
        str(ans),
        difficulty_level=2,
        explanation=f"Multiplier for {p}% increase is 1 + {p}/100 = {1 + p/100}.",
    )


def _percent_decrease() -> Dict:
    n, p = random.randint(50, 200), random.randint(5, 25)
    ans = round(n * (1 - p / 100), 2)
    return _q(
        f"Decrease {n} by {p}%",
        str(ans),
        difficulty_level=2,
        explanation=f"Multiplier for {p}% decrease is 1 - {p}/100.",
    )


# ---- Area/Perimeter ----
def _area_rect() -> Dict:
    l, w = random.randint(5, 20), random.randint(3, 15)
    return _q(
        f"A rectangle has length {l} cm and width {w} cm. Find the area.",
        f"{l * w} cm²",
        difficulty_level=1,
        explanation="Area of rectangle = length × width.",
    )


def _area_triangle() -> Dict:
    b, h = random.randint(4, 15), random.randint(4, 12)
    return _q(
        f"A triangle has base {b} cm and height {h} cm. Find the area.",
        f"{0.5 * b * h} cm²",
        difficulty_level=1,
        explanation="Area of triangle = ½ × base × height.",
    )


def _area_circle() -> Dict:
    r = random.randint(3, 12)
    area = round(3.14 * r * r, 2)
    return _q(
        f"A circle has radius {r} cm. Find the area. (Use π = 3.14)",
        f"{area} cm²",
        difficulty_level=2,
        explanation="Area of circle = πr².",
    )


def _perimeter_rect() -> Dict:
    l, w = random.randint(4, 12), random.randint(3, 10)
    return _q(
        f"A rectangle has length {l} cm and width {w} cm. Find the perimeter.",
        f"{2 * (l + w)} cm",
        difficulty_level=1,
        explanation="Perimeter = 2 × (length + width).",
    )


# ---- Pythagoras ----
def _pythagoras() -> Dict:
    a, b = random.randint(3, 8), random.randint(4, 10)
    c = round((a**2 + b**2) ** 0.5, 2)
    return _q(
        f"In a right-angled triangle, the two shorter sides are {a} cm and {b} cm. Find the length of the hypotenuse.",
        f"{c} cm",
        question_type="calculation",
        difficulty_level=2,
        marks_available=2,
        explanation="Pythagoras: a² + b² = c².",
    )


# ---- Trigonometry ----
def _soh_cah_toa() -> Dict:
    opp, hyp = random.randint(3, 8), random.randint(8, 15)
    angle = round(57.3 * (opp / hyp), 1)  # approximate
    return _q(
        f"In a right-angled triangle, the opposite side is {opp} cm and the hypotenuse is {hyp} cm. Find the angle (to 1 d.p.).",
        f"{angle}°",
        question_type="calculation",
        difficulty_level=3,
        explanation="Use sin(θ) = opposite/hypotenuse, then sin⁻¹.",
    )


# ---- BODMAS / order of operations ----
def _bodmas() -> Dict:
    a, b, c = random.randint(2, 5), random.randint(3, 8), random.randint(1, 5)
    ans = a + b * c
    return _q(
        f"Calculate: {a} + {b} × {c}",
        str(ans),
        difficulty_level=1,
        explanation="Multiplication before addition (BODMAS).",
    )


# ---- Fractions ----
def _fraction_add() -> Dict:
    a, b, c, d = 1, 2, 1, 4
    num = a * d + b * c
    den = b * d
    from math import gcd
    g = gcd(num, den)
    num, den = num // g, den // g
    ans = f"{num}/{den}" if den != 1 else str(num)
    return _q(
        f"Calculate: 1/2 + 1/4. Give your answer as a fraction in its simplest form.",
        ans,
        difficulty_level=2,
        explanation="Find common denominator (4), then add numerators.",
    )


# ---- Ratios ----
def _ratio_simplify() -> Dict:
    a, b = random.randint(2, 6), random.randint(2, 6)
    from math import gcd
    g = gcd(a, b)
    na, nb = a // g, b // g
    return _q(
        f"Simplify the ratio {a}:{b}",
        f"{na}:{nb}",
        difficulty_level=1,
        explanation="Divide both parts by their highest common factor.",
    )


# ---- Probability ----
def _prob_basic() -> Dict:
    n = random.choice([4, 5, 6, 8, 10])
    return _q(
        f"A fair {n}-sided dice is rolled. What is the probability of rolling a 1?",
        f"1/{n}",
        difficulty_level=1,
        explanation="One favourable outcome out of n equally likely outcomes.",
    )


# ---- Generic fallback ----
def _generic_math(topic: str, lesson: str) -> Dict:
    a, b = random.randint(2, 10), random.randint(1, 10)
    c = a + b
    return _q(
        f"Calculate: {a} + {b}",
        str(c),
        difficulty_level=1,
        explanation=f"Basic arithmetic for {lesson}.",
    )


# Lesson title substring -> list of template functions
TEMPLATES: Dict[str, List[Callable[[], Dict]]] = {
    "BODMAS": [_bodmas],
    "Algebraic Equations": [_linear_1, _linear_2, _linear_3],
    "Factorising Quadratic": [_quad_factorise, _quad_solve_simple],
    "Quadratic Formula": [_quad_factorise, _quad_solve_simple],
    "Completing the Square": [_quad_factorise],
    "Percentage": [_percent_of, _percent_increase, _percent_decrease],
    "How to Find a Percentage": [_percent_of, _percent_increase, _percent_decrease],
    "Percentage Increase": [_percent_increase, _percent_decrease],
    "Percentage Change": [_percent_increase, _percent_decrease],
    "Reverse Percentage": [_percent_of, _percent_increase],
    "Area": [_area_rect, _area_triangle, _area_circle],
    "Perimeter": [_perimeter_rect, _area_rect],
    "Pythagoras": [_pythagoras],
    "Trigonometry": [_soh_cah_toa, _pythagoras],
    "SOH CAH TOA": [_soh_cah_toa, _pythagoras],
    "Fractions": [_fraction_add, _percent_of],
    "Adding & Subtracting Fractions": [_fraction_add],
    "Multiplying & Dividing Fractions": [_fraction_add],
    "Ratio": [_ratio_simplify],
    "Ratios": [_ratio_simplify],
    "Probability": [_prob_basic],
}

# Fallback templates for any maths lesson
FALLBACK_TEMPLATES: List[Callable[[], Dict]] = [
    _linear_1,
    _linear_2,
    _percent_of,
    _area_rect,
    _area_triangle,
    _pythagoras,
    _bodmas,
    _ratio_simplify,
    _prob_basic,
    _generic_math,
]


def _pick_templates(lesson_title: str) -> List[Callable[[], Dict]]:
    lt = lesson_title.lower()
    candidates = []
    for key, funcs in TEMPLATES.items():
        if key.lower() in lt:
            candidates.extend(funcs)
    if not candidates:
        return FALLBACK_TEMPLATES
    return list(dict.fromkeys(candidates))  # dedupe preserving order


def generate(topic_name: str, lesson_title: str, count: int) -> List[Dict[str, Any]]:
    """
    Generate up to `count` question dicts for the given topic and lesson.
    Returns list of question dicts (no subject/topic/lesson - those are added by the command).
    """
    templates = _pick_templates(lesson_title)
    out: List[Dict[str, Any]] = []
    seen_texts: set = set()
    attempts = 0
    max_attempts = count * 20
    while len(out) < count and attempts < max_attempts:
        attempts += 1
        try:
            fn = random.choice(templates)
            if fn == _generic_math:
                q = fn(topic_name, lesson_title)
            else:
                q = fn()
            txt = q["question_text"]
            if txt in seen_texts:
                continue
            seen_texts.add(txt)
            out.append(q)
        except Exception:
            continue
    return out
