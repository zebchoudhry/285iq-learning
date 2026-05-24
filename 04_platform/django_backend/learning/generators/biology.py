"""
Biology question generator. Produces question dicts in the schema expected by load_questions.
Templates: definitions (osmosis, photosynthesis), process ordering, recall MCQs.
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


def _osmosis() -> Dict:
    return _q(
        "What is osmosis?",
        "The net movement of water from a dilute to a more concentrated solution through a partially permeable membrane",
        question_type="multiple_choice",
        difficulty_level=2,
        options=[
            {"text": "The movement of particles from high to low concentration", "correct": False},
            {"text": "The net movement of water from a dilute to a more concentrated solution through a partially permeable membrane", "correct": True},
            {"text": "The movement of ions against a concentration gradient", "correct": False},
            {"text": "The diffusion of oxygen into cells", "correct": False},
        ],
        explanation="Osmosis is the passive movement of water only, through a partially permeable membrane.",
    )


def _photosynthesis() -> Dict:
    return _q(
        "What is the word equation for photosynthesis?",
        "Carbon dioxide + Water -> Glucose + Oxygen (in the presence of light and chlorophyll)",
        question_type="multiple_choice",
        difficulty_level=1,
        options=[
            {"text": "Glucose + Oxygen -> Carbon dioxide + Water", "correct": False},
            {"text": "Carbon dioxide + Water -> Glucose + Oxygen (in the presence of light and chlorophyll)", "correct": True},
            {"text": "Carbon dioxide + Oxygen -> Glucose + Water", "correct": False},
            {"text": "Water + Light -> Glucose", "correct": False},
        ],
        explanation="Photosynthesis converts CO2 and H2O into glucose and O2 using light energy.",
    )


def _respiration() -> Dict:
    return _q(
        "What is the word equation for aerobic respiration?",
        "Glucose + Oxygen -> Carbon dioxide + Water",
        question_type="multiple_choice",
        difficulty_level=1,
        options=[
            {"text": "Glucose + Oxygen -> Carbon dioxide + Water", "correct": True},
            {"text": "Carbon dioxide + Water -> Glucose + Oxygen", "correct": False},
            {"text": "Glucose -> Lactic acid", "correct": False},
            {"text": "Oxygen -> Carbon dioxide", "correct": False},
        ],
        explanation="Aerobic respiration releases energy from glucose using oxygen.",
    )


def _diffusion() -> Dict:
    return _q(
        "What is diffusion?",
        "The net movement of particles from an area of higher concentration to an area of lower concentration",
        question_type="multiple_choice",
        difficulty_level=1,
        options=[
            {"text": "The net movement of particles from an area of higher concentration to an area of lower concentration", "correct": True},
            {"text": "The movement of water through a membrane", "correct": False},
            {"text": "The active transport of ions", "correct": False},
            {"text": "The breakdown of glucose", "correct": False},
        ],
        explanation="Diffusion is passive movement down a concentration gradient.",
    )


def _enzyme() -> Dict:
    return _q(
        "What is an enzyme?",
        "A biological catalyst that speeds up reactions without being used up",
        question_type="multiple_choice",
        difficulty_level=1,
        options=[
            {"text": "A type of carbohydrate", "correct": False},
            {"text": "A biological catalyst that speeds up reactions without being used up", "correct": True},
            {"text": "A type of cell", "correct": False},
            {"text": "A hormone", "correct": False},
        ],
        explanation="Enzymes are proteins that act as biological catalysts.",
    )


def _mitosis() -> Dict:
    return _q(
        "What is mitosis?",
        "Cell division that produces two genetically identical daughter cells",
        question_type="multiple_choice",
        difficulty_level=2,
        options=[
            {"text": "Cell division that produces gametes", "correct": False},
            {"text": "Cell division that produces two genetically identical daughter cells", "correct": True},
            {"text": "The process of protein synthesis", "correct": False},
            {"text": "The breakdown of glucose", "correct": False},
        ],
        explanation="Mitosis produces two identical cells for growth and repair.",
    )


def _heart_chamber() -> Dict:
    return _q(
        "How many chambers does the human heart have?",
        "4",
        question_type="multiple_choice",
        difficulty_level=1,
        options=[
            {"text": "2", "correct": False},
            {"text": "3", "correct": False},
            {"text": "4", "correct": True},
            {"text": "5", "correct": False},
        ],
        explanation="The heart has 4 chambers: 2 atria and 2 ventricles.",
    )


def _gas_exchange() -> Dict:
    return _q(
        "Where does gas exchange occur in the lungs?",
        "Alveoli",
        question_type="multiple_choice",
        difficulty_level=1,
        options=[
            {"text": "Bronchi", "correct": False},
            {"text": "Trachea", "correct": False},
            {"text": "Alveoli", "correct": True},
            {"text": "Diaphragm", "correct": False},
        ],
        explanation="Alveoli have a large surface area for gas exchange.",
    )


def _homeostasis() -> Dict:
    return _q(
        "What is homeostasis?",
        "The maintenance of a constant internal environment",
        question_type="multiple_choice",
        difficulty_level=2,
        options=[
            {"text": "The maintenance of a constant internal environment", "correct": True},
            {"text": "The breakdown of nutrients", "correct": False},
            {"text": "Cell division", "correct": False},
            {"text": "The production of hormones", "correct": False},
        ],
        explanation="Homeostasis keeps conditions like temperature and blood glucose stable.",
    )


def _define_osmosis_short() -> Dict:
    return _q(
        "Define osmosis.",
        "The net movement of water molecules from a region of higher water concentration to a region of lower water concentration through a partially permeable membrane",
        question_type="short_answer",
        difficulty_level=2,
        marks_available=2,
        explanation="Osmosis involves water only and a partially permeable membrane.",
    )


TEMPLATES: Dict[str, List[Callable[[], Dict]]] = {
    "Osmosis": [_osmosis, _define_osmosis_short],
    "Diffusion": [_diffusion],
    "Active Transport": [_diffusion, _osmosis],
    "Photosynthesis": [_photosynthesis],
    "Respiration": [_respiration],
    "Enzymes": [_enzyme],
    "Enzyme": [_enzyme],
    "Mitosis": [_mitosis],
    "Heart": [_heart_chamber],
    "Circulatory": [_heart_chamber, _gas_exchange],
    "Lungs": [_gas_exchange],
    "Gas Exchange": [_gas_exchange],
    "Homeostasis": [_homeostasis],
    "Cell": [_diffusion, _osmosis, _mitosis],
}

FALLBACK = [
    _osmosis, _photosynthesis, _respiration, _diffusion,
    _enzyme, _mitosis, _heart_chamber, _gas_exchange, _homeostasis,
]


def _pick_templates(lesson_title: str) -> List[Callable[[], Dict]]:
    lt = lesson_title.lower()
    out = []
    for key, funcs in TEMPLATES.items():
        if key.lower() in lt:
            out.extend(funcs)
    return list(dict.fromkeys(out)) if out else FALLBACK


def generate(topic_name: str, lesson_title: str, count: int) -> List[Dict[str, Any]]:
    """Generate up to count question dicts for the given biology topic and lesson."""
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
