"""
Physics question generator for load_questions.
"""
import random
from typing import List, Dict, Any, Callable


def _q(question_text, correct_answer, question_type="short_answer", difficulty_level=2,
       marks_available=1, explanation="", options=None):
    return {
        "question_text": question_text,
        "correct_answer": correct_answer,
        "question_type": question_type,
        "difficulty_level": difficulty_level,
        "marks_available": marks_available,
        "explanation": explanation,
        "options": options,
    }


def _ke_formula():
    m, v = random.randint(2, 10), random.randint(5, 20)
    ke = round(0.5 * m * v * v, 1)
    return _q("A car of mass %d kg moves at %d m/s. Calculate its kinetic energy in joules." % (m, v),
              str(ke), question_type="calculation", difficulty_level=2, marks_available=2,
              explanation="KE = 0.5mv^2")


def _gpe_formula():
    m, h = random.randint(5, 20), random.randint(2, 15)
    gpe = round(m * 9.8 * h, 1)
    return _q("An object of mass %d kg is raised %d m. Calculate its gravitational potential energy. (g = 9.8 N/kg)" % (m, h),
              str(gpe), question_type="calculation", difficulty_level=2, explanation="GPE = mgh")


def _v_ir():
    i, r = round(random.uniform(0.5, 3.0), 1), random.randint(2, 12)
    v = round(i * r, 2)
    return _q("A circuit has current %s A and resistance %d ohm. Calculate the voltage." % (i, r),
              "%s V" % v, question_type="calculation", difficulty_level=1, explanation="V = IR")


def _power_iv():
    i, v = round(random.uniform(1, 5), 1), random.randint(6, 24)
    p = round(i * v, 1)
    return _q("A device has current %s A and voltage %d V. Calculate the power in watts." % (i, v),
              str(p), question_type="calculation", difficulty_level=2, explanation="P = IV")


def _wave_speed():
    f, lam = round(random.uniform(0.5, 5.0), 1), random.randint(2, 20)
    v = round(f * lam, 2)
    return _q("A wave has frequency %s Hz and wavelength %d m. Calculate the wave speed in m/s." % (f, lam),
              str(v), question_type="calculation", difficulty_level=2, explanation="v = f*lambda")


def _efficiency():
    useful, total = random.randint(40, 80), random.randint(100, 200)
    eff = round(100 * useful / total, 1)
    return _q("A device transfers %d J useful from %d J input. Calculate efficiency (%%)." % (useful, total),
              "%s%%" % eff, question_type="calculation", difficulty_level=2,
              explanation="Efficiency = (useful/total) * 100%%")


def _definition_ke():
    return _q("What is kinetic energy?", "The energy an object has due to its motion",
              question_type="multiple_choice", difficulty_level=1,
              options=[{"text": "Energy stored in a spring", "correct": False},
                       {"text": "The energy an object has due to its motion", "correct": True},
                       {"text": "Energy in chemical bonds", "correct": False},
                       {"text": "Energy of position in gravity", "correct": False}],
              explanation="KE = 0.5mv^2")


def _definition_gpe():
    return _q("What is gravitational potential energy?",
              "Energy stored due to position in a gravitational field",
              question_type="multiple_choice", difficulty_level=1,
              options=[{"text": "Energy stored due to position in a gravitational field", "correct": True},
                       {"text": "Energy of motion", "correct": False},
                       {"text": "Energy in chemical bonds", "correct": False},
                       {"text": "Energy transferred by heating", "correct": False}],
              explanation="GPE = mgh")


def _unit_current():
    return _q("What is the unit of electric current?", "Ampere (A)",
              question_type="multiple_choice", difficulty_level=1,
              options=[{"text": "Volt (V)", "correct": False}, {"text": "Ampere (A)", "correct": True},
                       {"text": "Ohm", "correct": False}, {"text": "Watt (W)", "correct": False}],
              explanation="Current is measured in amperes")


def _unit_resistance():
    return _q("What is the unit of resistance?", "Ohm",
              question_type="multiple_choice", difficulty_level=1,
              options=[{"text": "Volt (V)", "correct": False}, {"text": "Ampere (A)", "correct": False},
                       {"text": "Ohm", "correct": True}, {"text": "Joule (J)", "correct": False}],
              explanation="Resistance is measured in ohms")


def _density():
    m, v = random.randint(20, 100), random.randint(5, 25)
    d = round(m / v, 2)
    return _q("An object has mass %d g and volume %d cm3. Calculate density in g/cm3." % (m, v),
              str(d), question_type="calculation", difficulty_level=1, explanation="Density = mass/volume")


def _speed():
    d, t = random.randint(50, 200), random.randint(5, 20)
    s = round(d / t, 1)
    return _q("A car travels %d m in %d s. Calculate its speed in m/s." % (d, t),
              str(s), question_type="calculation", difficulty_level=1, explanation="Speed = distance/time")


def _alpha_beta_gamma():
    return _q("Which nuclear radiation has highest ionising power?", "Alpha",
              question_type="multiple_choice", difficulty_level=2,
              options=[{"text": "Alpha", "correct": True}, {"text": "Beta", "correct": False},
                       {"text": "Gamma", "correct": False}, {"text": "All equal", "correct": False}],
              explanation="Alpha particles are most ionising")


def _energy_store_elastic():
    return _q("What energy store increases when you stretch a spring?",
              "Elastic potential energy",
              question_type="multiple_choice", difficulty_level=1,
              options=[
                  {"text": "Kinetic energy", "correct": False},
                  {"text": "Elastic potential energy", "correct": True},
                  {"text": "Chemical energy", "correct": False},
                  {"text": "Thermal energy", "correct": False},
              ],
              explanation="Stretching or compressing stores energy in the spring as elastic potential energy.")


def _energy_transferred_not_used():
    return _q("When energy is transferred from one store to another, is it used up or destroyed?",
              "No - energy is transferred, not destroyed",
              question_type="multiple_choice", difficulty_level=1,
              options=[
                  {"text": "Yes, energy is used up", "correct": False},
                  {"text": "No - energy is transferred, not destroyed", "correct": True},
                  {"text": "Energy is created", "correct": False},
                  {"text": "Energy disappears", "correct": False},
              ],
              explanation="Energy is conserved - it transfers between stores but is never created or destroyed.")


def _energy_stores_list():
    return _q("Which of these is a type of energy store?",
              "Kinetic",
              question_type="multiple_choice", difficulty_level=1,
              options=[
                  {"text": "Kinetic", "correct": True},
                  {"text": "Transfer", "correct": False},
                  {"text": "Heating", "correct": False},
                  {"text": "Radiation", "correct": False},
              ],
              explanation="Kinetic, thermal, chemical, gravitational potential, elastic, and nuclear are energy stores.")


# ---- Recall (Low Difficulty) - ChatGPT Energy Stores Bank ----
def _name_three_energy_stores():
    return _q("Name three energy stores.",
              "Kinetic, thermal, chemical",
              question_type="multiple_choice", difficulty_level=1,
              options=[
                  {"text": "Kinetic, thermal, chemical", "correct": True},
                  {"text": "Heating, radiation, conduction", "correct": False},
                  {"text": "Voltage, current, resistance", "correct": False},
                  {"text": "Mass, speed, force", "correct": False},
              ],
              explanation="Common energy stores include kinetic, thermal, chemical, gravitational potential, elastic, and nuclear.")


def _moving_car_energy_store():
    return _q("What energy store does a moving car have?",
              "Kinetic energy",
              question_type="multiple_choice", difficulty_level=1,
              options=[
                  {"text": "Kinetic energy", "correct": True},
                  {"text": "Chemical energy", "correct": False},
                  {"text": "Gravitational potential energy", "correct": False},
                  {"text": "Elastic potential energy", "correct": False},
              ],
              explanation="A moving object has kinetic energy - the energy due to motion.")


def _lifted_object_energy_store():
    return _q("What energy store increases when an object is lifted?",
              "Gravitational potential energy",
              question_type="multiple_choice", difficulty_level=1,
              options=[
                  {"text": "Gravitational potential energy", "correct": True},
                  {"text": "Kinetic energy", "correct": False},
                  {"text": "Chemical energy", "correct": False},
                  {"text": "Thermal energy", "correct": False},
              ],
              explanation="Lifting increases height, so gravitational potential energy (GPE) increases.")


def _energy_used_up_true_false():
    return _q("True or false: Energy is used up when transferred.",
              "False",
              question_type="multiple_choice", difficulty_level=1,
              options=[
                  {"text": "True", "correct": False},
                  {"text": "False", "correct": True},
              ],
              explanation="Energy is conserved - it transfers between stores but is never created or destroyed.")


def _food_energy_store():
    return _q("Which energy store is associated with food?",
              "Chemical energy",
              question_type="multiple_choice", difficulty_level=1,
              options=[
                  {"text": "Chemical energy", "correct": True},
                  {"text": "Kinetic energy", "correct": False},
                  {"text": "Elastic potential energy", "correct": False},
                  {"text": "Nuclear energy", "correct": False},
              ],
              explanation="Food stores energy in chemical bonds - released when digested or burned.")


# ---- Understanding (Medium Difficulty) ----
def _spring_released_transfer():
    return _q("A stretched spring is released. Describe the energy transfer.",
              "Elastic potential to kinetic energy",
              question_type="multiple_choice", difficulty_level=2,
              options=[
                  {"text": "Elastic potential to kinetic energy", "correct": True},
                  {"text": "Kinetic to chemical energy", "correct": False},
                  {"text": "Thermal to gravitational potential", "correct": False},
                  {"text": "Chemical to electrical energy", "correct": False},
              ],
              explanation="When released, the spring's elastic potential energy transfers to kinetic energy of the moving parts.")


def _torch_battery_transfer():
    return _q("A torch uses a battery. Describe the energy transfer.",
              "Chemical to electrical to light and thermal",
              question_type="multiple_choice", difficulty_level=2,
              options=[
                  {"text": "Chemical to electrical to light and thermal", "correct": True},
                  {"text": "Kinetic to gravitational potential", "correct": False},
                  {"text": "Thermal to elastic", "correct": False},
                  {"text": "Nuclear to chemical", "correct": False},
              ],
              explanation="Battery: chemical -> electrical. Bulb: electrical -> light + thermal (some wasted as heat).")


def _falling_book_stores():
    return _q("A falling book speeds up. Which energy stores change?",
              "Gravitational potential decreases, kinetic increases",
              question_type="multiple_choice", difficulty_level=2,
              options=[
                  {"text": "Gravitational potential decreases, kinetic increases", "correct": True},
                  {"text": "Chemical decreases, thermal increases", "correct": False},
                  {"text": "Kinetic decreases, elastic increases", "correct": False},
                  {"text": "No stores change", "correct": False},
              ],
              explanation="As the book falls, GPE transfers to kinetic energy. Speed increases so KE increases.")


def _ball_stops_bouncing():
    return _q("Why does a ball eventually stop bouncing?",
              "Energy transfers to the thermal store of the surroundings",
              question_type="multiple_choice", difficulty_level=2,
              options=[
                  {"text": "Energy transfers to the thermal store of the surroundings", "correct": True},
                  {"text": "Energy is destroyed", "correct": False},
                  {"text": "Gravitational potential runs out", "correct": False},
                  {"text": "The ball loses mass", "correct": False},
              ],
              explanation="Friction and air resistance transfer energy to thermal store of the ball, ground, and air.")


def _kettle_system():
    return _q("Identify the system when a kettle boils water.",
              "Kettle and water",
              question_type="multiple_choice", difficulty_level=2,
              options=[
                  {"text": "Kettle and water", "correct": True},
                  {"text": "Just the water", "correct": False},
                  {"text": "The plug socket", "correct": False},
                  {"text": "The whole room", "correct": False},
              ],
              explanation="The system is the object(s) being studied - here, the kettle and the water inside it.")


# ---- Application (Higher Difficulty) ----
def _book_falls_energy_changes():
    return _q("A 2 kg book falls from a shelf. Explain the energy changes.",
              "GPE decreases, kinetic increases, then thermal and sound on impact",
              question_type="multiple_choice", difficulty_level=3,
              options=[
                  {"text": "GPE decreases, kinetic increases, then thermal and sound on impact", "correct": True},
                  {"text": "Chemical energy is released", "correct": False},
                  {"text": "Energy is destroyed when it lands", "correct": False},
                  {"text": "Elastic energy increases throughout", "correct": False},
              ],
              explanation="Falling: GPE -> KE. On impact: KE -> thermal (heating) + sound.")


def _phone_warm_charging():
    return _q("Why does a phone feel warm after charging?",
              "Electrical energy transfers to the thermal store",
              question_type="multiple_choice", difficulty_level=3,
              options=[
                  {"text": "Electrical energy transfers to the thermal store", "correct": True},
                  {"text": "Chemical energy is released", "correct": False},
                  {"text": "Nuclear radiation heats it", "correct": False},
                  {"text": "Kinetic energy from electrons", "correct": False},
              ],
              explanation="Not all electrical energy goes to the battery - some is wasted as heat (thermal store).")


def _define_system():
    return _q("Define a system in physics.",
              "An object or group of objects being studied",
              question_type="multiple_choice", difficulty_level=3,
              options=[
                  {"text": "An object or group of objects being studied", "correct": True},
                  {"text": "A type of energy store", "correct": False},
                  {"text": "A way to transfer energy", "correct": False},
                  {"text": "A unit of measurement", "correct": False},
              ],
              explanation="A system is the object or group of objects we focus on when analysing energy transfers.")


def _rollercoaster_lowest_point():
    return _q("A rollercoaster reaches the lowest point. Which store is greatest?",
              "Kinetic energy",
              question_type="multiple_choice", difficulty_level=3,
              options=[
                  {"text": "Kinetic energy", "correct": True},
                  {"text": "Gravitational potential energy", "correct": False},
                  {"text": "Elastic potential energy", "correct": False},
                  {"text": "Chemical energy", "correct": False},
              ],
              explanation="At the lowest point, GPE is minimum and speed is maximum, so kinetic energy is greatest.")


def _explain_energy_conserved():
    return _q("Explain why energy is conserved.",
              "Total energy remains constant; it changes store or transfers",
              question_type="multiple_choice", difficulty_level=3,
              options=[
                  {"text": "Total energy remains constant; it changes store or transfers", "correct": True},
                  {"text": "Energy is created when needed", "correct": False},
                  {"text": "Energy disappears into nothing", "correct": False},
                  {"text": "Only some types of energy are conserved", "correct": False},
              ],
              explanation="Energy cannot be created or destroyed - it only moves between stores or transfers to surroundings.")


# ---- Exam-Style 4-6 Mark ----
def _cyclist_uphill_downhill():
    return _q("Describe the energy transfers when a cyclist pedals uphill then coasts downhill.",
              "Uphill: chemical to kinetic to GPE. Downhill: GPE to kinetic, some to thermal via friction.",
              question_type="short_answer", difficulty_level=3, marks_available=4,
              explanation="Uphill: muscles (chemical) -> kinetic -> GPE. Downhill: GPE -> kinetic. Friction causes some energy to thermal store.")


def _pendulum_stops():
    return _q("Explain why a pendulum eventually stops swinging.",
              "Energy transfers from kinetic and GPE to thermal store of air and pivot due to friction",
              question_type="short_answer", difficulty_level=3, marks_available=4,
              explanation="Friction at the pivot and air resistance transfer energy to the thermal store of the surroundings.")


# Energy-only templates for Energy Stores, Energy Transfer, etc.
ENERGY_ONLY = [
    _ke_formula,
    _gpe_formula,
    _definition_ke,
    _definition_gpe,
    _efficiency,
    _energy_store_elastic,
    _energy_transferred_not_used,
    _energy_stores_list,
    # Recall
    _name_three_energy_stores,
    _moving_car_energy_store,
    _lifted_object_energy_store,
    _energy_used_up_true_false,
    _food_energy_store,
    # Understanding
    _spring_released_transfer,
    _torch_battery_transfer,
    _falling_book_stores,
    _ball_stops_bouncing,
    _kettle_system,
    # Application
    _book_falls_energy_changes,
    _phone_warm_charging,
    _define_system,
    _rollercoaster_lowest_point,
    _explain_energy_conserved,
    # Exam-style
    _cyclist_uphill_downhill,
    _pendulum_stops,
]

TEMPLATES = {
    "Energy Stores": ENERGY_ONLY,
    "Energy Transfer": ENERGY_ONLY,
    "Energy & Systems": ENERGY_ONLY,
    "Conservation of Energy": ENERGY_ONLY,
    "Kinetic Energy": [_ke_formula, _definition_ke],
    "Gravitational Potential": [_gpe_formula, _definition_gpe],
    "V = IR": [_v_ir, _unit_current, _unit_resistance],
    "Circuits": [_v_ir, _power_iv, _unit_current],
    "Energy & Power": [_power_iv, _ke_formula, _efficiency],
    "Efficiency": [_efficiency],
    "Waves": [_wave_speed],
    "Density": [_density],
    "Particle Model": [_density],
    "Speed": [_speed],
    "Velocity": [_speed],
    "Atomic": [_alpha_beta_gamma],
    "Nuclear": [_alpha_beta_gamma],
}

FALLBACK = [_ke_formula, _gpe_formula, _v_ir, _wave_speed, _efficiency,
            _density, _speed, _definition_ke, _unit_current]


def _pick_templates(lesson_title):
    lt = lesson_title.lower()
    out = []
    for key, funcs in TEMPLATES.items():
        if key.lower() in lt:
            out.extend(funcs)
    return list(dict.fromkeys(out)) if out else FALLBACK


def generate(topic_name: str, lesson_title: str, count: int) -> List[Dict[str, Any]]:
    """Generate up to count question dicts for the given physics topic and lesson."""
    templates = _pick_templates(lesson_title)
    out = []
    seen = set()
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
