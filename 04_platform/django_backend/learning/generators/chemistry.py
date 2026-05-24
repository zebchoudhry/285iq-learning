"""
Chemistry question generator. Produces question dicts in the schema expected by load_questions.
Templates: balancing equations, bond types, element/group properties, mole calculations, acid/base recall.
"""
import random
from typing import List, Dict, Any, Callable


def _q(
    question_text: str,
    correct_answer: str,
    question_type: str = "short_answer",
    difficulty_level: int = 2,
    marks_available: int = 1,
    explanation: str = "",
    options: List[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return {
        "question_text": question_text,
        "correct_answer": correct_answer,
        "question_type": question_type,
        "difficulty_level": difficulty_level,
        "marks_available": marks_available,
        "explanation": explanation,
        "options": options,
    }


# ---- Balancing equations (numerical) ----
def _balance_simple() -> Dict:
    # 2H2 + O2 -> 2H2O
    return _q(
        "Balance the equation: H₂ + O₂ → H₂O",
        "2H₂ + O₂ → 2H₂O",
        question_type="short_answer",
        difficulty_level=2,
        marks_available=2,
        explanation="Two hydrogen molecules (4H) and one oxygen molecule (2O) produce two water molecules.",
    )


def _balance_co2() -> Dict:
    return _q(
        "Balance the equation: CH₄ + O₂ → CO₂ + H₂O",
        "CH₄ + 2O₂ → CO₂ + 2H₂O",
        question_type="short_answer",
        difficulty_level=2,
        marks_available=2,
        explanation="Count atoms on each side; balance C, H, then O.",
    )


# ---- Bond type MCQs ----
def _ionic_bond() -> Dict:
    return _q(
        "What type of bond forms between a metal and a non-metal?",
        "Ionic",
        question_type="multiple_choice",
        difficulty_level=1,
        options=[
            {"text": "Covalent", "correct": False},
            {"text": "Ionic", "correct": True},
            {"text": "Metallic", "correct": False},
            {"text": "Hydrogen", "correct": False},
        ],
        explanation="Ionic bonds form when electrons are transferred from metal to non-metal.",
    )


def _covalent_bond() -> Dict:
    return _q(
        "What type of bond is formed when atoms share pairs of electrons?",
        "Covalent",
        question_type="multiple_choice",
        difficulty_level=1,
        options=[
            {"text": "Ionic", "correct": False},
            {"text": "Covalent", "correct": True},
            {"text": "Metallic", "correct": False},
            {"text": "Van der Waals", "correct": False},
        ],
        explanation="Covalent bonds involve shared electron pairs between non-metals.",
    )


# ---- Group 1 (Alkali metals) ----
def _group1_reactivity() -> Dict:
    return _q(
        "What happens to reactivity as you go down Group 1 (alkali metals)?",
        "Reactivity increases",
        question_type="multiple_choice",
        difficulty_level=2,
        options=[
            {"text": "Reactivity increases", "correct": True},
            {"text": "Reactivity decreases", "correct": False},
            {"text": "Reactivity stays the same", "correct": False},
            {"text": "Reactivity increases then decreases", "correct": False},
        ],
        explanation="Outer electron is further from nucleus, so easier to lose.",
    )


# ---- Group 7 (Halogens) ----
def _group7_reactivity() -> Dict:
    return _q(
        "What happens to reactivity as you go down Group 7 (halogens)?",
        "Reactivity decreases",
        question_type="multiple_choice",
        difficulty_level=2,
        options=[
            {"text": "Reactivity increases", "correct": False},
            {"text": "Reactivity decreases", "correct": True},
            {"text": "Reactivity stays the same", "correct": False},
            {"text": "Reactivity varies randomly", "correct": False},
        ],
        explanation="Atomic size increases; harder to gain an electron.",
    )


# ---- Mole calculations ----
def _moles_mass() -> Dict:
    mr = random.choice([18, 44, 32, 16, 28])  # H2O, CO2, O2, CH4, N2
    m = mr * random.randint(1, 5)
    n = round(m / mr, 2)
    return _q(
        f"Calculate the number of moles in {m} g of a substance with Mr = {mr}.",
        str(n),
        question_type="calculation",
        difficulty_level=2,
        marks_available=2,
        explanation="Number of moles = mass / Mr",
    )


def _concentration() -> Dict:
    n, v = random.uniform(0.5, 2.0), random.uniform(0.1, 1.0)
    c = round(n / v, 2)
    return _q(
        f"A solution contains {n} mol of solute in {v} dm³. Calculate the concentration in mol/dm³.",
        str(c),
        question_type="calculation",
        difficulty_level=2,
        explanation="Concentration = moles / volume (mol/dm³)",
    )


# ---- Acids and bases ----
def _acid_base() -> Dict:
    return _q(
        "What is the pH of a neutral solution?",
        "7",
        question_type="multiple_choice",
        difficulty_level=1,
        options=[
            {"text": "0", "correct": False},
            {"text": "7", "correct": True},
            {"text": "14", "correct": False},
            {"text": "1", "correct": False},
        ],
        explanation="pH 7 is neutral; below 7 is acid, above 7 is alkali.",
    )


def _neutralisation() -> Dict:
    return _q(
        "What products are formed when an acid reacts with a base?",
        "Salt and water",
        question_type="multiple_choice",
        difficulty_level=1,
        options=[
            {"text": "Salt and hydrogen", "correct": False},
            {"text": "Salt and water", "correct": True},
            {"text": "Carbon dioxide and water", "correct": False},
            {"text": "Acid and base", "correct": False},
        ],
        explanation="Acid + Base → Salt + Water (neutralisation).",
    )


# ---- Electrolysis ----
def _electrolysis_anode() -> Dict:
    return _q(
        "At which electrode do negatively charged ions (anions) move to?",
        "Anode",
        question_type="multiple_choice",
        difficulty_level=1,
        options=[
            {"text": "Cathode", "correct": False},
            {"text": "Anode", "correct": True},
            {"text": "Both", "correct": False},
            {"text": "Neither", "correct": False},
        ],
        explanation="Anions are negatively charged and attracted to the positive anode.",
    )


# ---- Exothermic / Endothermic ----
def _exothermic() -> Dict:
    return _q(
        "What happens to the temperature in an exothermic reaction?",
        "Temperature increases / heat is released",
        question_type="multiple_choice",
        difficulty_level=1,
        options=[
            {"text": "Temperature decreases", "correct": False},
            {"text": "Temperature increases / heat is released", "correct": True},
            {"text": "Temperature stays the same", "correct": False},
            {"text": "Temperature fluctuates", "correct": False},
        ],
        explanation="Exothermic reactions release energy to surroundings.",
    )


# ---- Organic ----
def _alkane_formula() -> Dict:
    n = random.randint(1, 5)
    return _q(
        f"What is the general formula for alkanes?",
        "CₙH₂ₙ₊₂",
        question_type="multiple_choice",
        difficulty_level=2,
        options=[
            {"text": "CₙH₂ₙ", "correct": False},
            {"text": "CₙH₂ₙ₊₂", "correct": True},
            {"text": "CₙH₂ₙ₋₂", "correct": False},
            {"text": "CₙHₙ", "correct": False},
        ],
        explanation="Alkanes are saturated hydrocarbons with single bonds only.",
    )


# Lesson keyword -> templates
TEMPLATES: Dict[str, List[Callable[[], Dict]]] = {
    "Balancing": [_balance_simple, _balance_co2],
    "Ionic": [_ionic_bond],
    "Covalent": [_covalent_bond],
    "Bonding": [_ionic_bond, _covalent_bond],
    "Group 1": [_group1_reactivity],
    "Group 7": [_group7_reactivity],
    "Alkali": [_group1_reactivity],
    "Halogen": [_group7_reactivity],
    "Moles": [_moles_mass, _concentration],
    "Concentration": [_concentration],
    "Acids": [_acid_base, _neutralisation],
    "Bases": [_acid_base, _neutralisation],
    "Neutralisation": [_neutralisation],
    "Electrolysis": [_electrolysis_anode],
    "Exothermic": [_exothermic],
    "Energy": [_exothermic],
    "Alkane": [_alkane_formula],
    "Organic": [_alkane_formula],
}

FALLBACK = [
    _balance_simple,
    _ionic_bond,
    _covalent_bond,
    _group1_reactivity,
    _moles_mass,
    _acid_base,
    _neutralisation,
    _electrolysis_anode,
    _exothermic,
]


def _pick_templates(lesson_title: str) -> List[Callable[[], Dict]]:
    lt = lesson_title.lower()
    out = []
    for key, funcs in TEMPLATES.items():
        if key.lower() in lt:
            out.extend(funcs)
    return list(dict.fromkeys(out)) if out else FALLBACK


def generate(topic_name: str, lesson_title: str, count: int) -> List[Dict[str, Any]]:
    """Generate up to `count` question dicts for the given chemistry topic and lesson."""
    templates = _pick_templates(lesson_title)
    out: List[Dict[str, Any]] = []
    seen: set = set()
    attempts = 0
    while len(out) < count and attempts < count * 15:
        attempts += 1
        try:
            q = random.choice(templates)()
            txt = q["question_text"]
            if txt in seen:
                continue
            seen.add(txt)
            out.append(q)
        except Exception:
            continue
    return out
