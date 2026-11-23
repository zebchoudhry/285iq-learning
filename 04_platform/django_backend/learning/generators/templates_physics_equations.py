"""
Physics equation templates: every AQA GCSE calculation.

Each template picks a consistent set of values (the inputs are chosen, the dependent value
is worked out forwards), then hides one of them and asks for it. So the answer is always a
value the template chose or computed exactly, and no rearranging can go wrong. Each question
carries `meta` with every value, which the tests use to re-check the physics independently.
"""
from fractions import Fraction as Fr
from typing import Dict, List, Optional, Tuple

from learning.generators.engine import make_question, tdec, template

PHYSICS = "physics"
G = Fr(98, 10)  # AQA uses g = 9.8 N/kg


def f(x) -> Fr:
    return Fr(str(x))


def _ok(x: Fr, max_dp: int = 3) -> bool:
    """Shown values must be positive and need no more than max_dp decimal places."""
    return x > 0 and (x * 10**max_dp).denominator == 1


def fmt(x: Fr) -> str:
    return tdec(x)


def _join(parts: List[str]) -> str:
    return parts[0] if len(parts) == 1 else ", ".join(parts[:-1]) + " and " + parts[-1]


def ask(
    rng,
    *,
    values: Dict[str, Fr],
    labels: Dict[str, Tuple[str, str]],
    hide_from: List[str],
    subject: str,
    equation: str,
    difficulty: int = 3,
    note: str = "",
) -> Optional[dict]:
    """
    "For <subject>, the <label> is <value> <unit> and ... Calculate the <hidden label>, in <unit>."
    labels: key -> (label, unit). Returns None if a value would be awkward to show.
    """
    if not all(_ok(v) for v in values.values()):
        return None
    hidden = rng.choice(hide_from)
    givens = [f"the {labels[k][0]} is {fmt(v)} {labels[k][1]}".rstrip() for k, v in values.items() if k != hidden]
    label, unit = labels[hidden]
    text = (f"For {subject}, {_join(givens)}.{(' ' + note) if note else ''} "
            f"Calculate the {label}" + (f", in {unit}" if unit else "") + ".")
    q = make_question(
        text, fmt(values[hidden]), difficulty=difficulty, marks=2 if hidden == hide_from[0] else 3,
        explanation=f"Use {equation}. Put in the values you know and rearrange for the {label}: "
                    f"{fmt(values[hidden])}{(' ' + unit) if unit else ''}.",
    )
    q["meta"] = {"values": {k: str(v) for k, v in values.items()}, "hidden": hidden}
    return q


def custom(text, answer: Fr, explanation, meta, difficulty=3, marks=3, unit=""):
    q = make_question(text, fmt(answer), difficulty=difficulty, marks=marks,
                      explanation=explanation + f" Answer: {fmt(answer)}{(' ' + unit) if unit else ''}.")
    q["meta"] = meta
    return q


# Realistic pairings: (object, masses in kg, speeds in m/s)
MOVERS = [
    ("a car", [800, 1000, 1200, 1500], list(range(5, 31))),
    ("a cyclist", [60, 70, 80, 90], list(range(3, 13))),
    ("a runner", [50, 60, 70, 80], [2, 3, 4, 5, 6, 7, 8, 9]),
    ("a tennis ball", [0.05, 0.06], list(range(10, 41))),
    ("a football", [0.4, 0.45], list(range(5, 31))),
    ("a trolley", [0.5, 1, 2, 4], [0.5, 1, 1.5, 2, 3, 4, 5]),
    ("a skateboarder", [40, 50, 60], [2, 3, 4, 5, 6, 8]),
]


def mover(rng):
    name, masses, speeds = rng.choice(MOVERS)
    return name, f(rng.choice(masses)), f(rng.choice(speeds))


# ===========================================================================
# ENERGY
# ===========================================================================
@template(code="kinetic_energy", subject=PHYSICS, topic="Energy", lessons=["1.3", "1.5"])
def kinetic_energy(rng):
    obj, m, v = mover(rng)
    return ask(rng, values={"m": m, "v": v, "ke": m * v * v / 2},
               labels={"ke": ("kinetic energy", "J"), "m": ("mass", "kg"), "v": ("speed", "m/s")},
               hide_from=["ke", "m", "v"], subject=obj, equation="kinetic energy = ½ × mass × speed²")


@template(code="gravitational_potential_energy", subject=PHYSICS, topic="Energy", lessons=["1.4", "1.5"])
def gravitational_potential_energy(rng):
    m = f(rng.choice([0.2, 0.5, 1, 2, 5, 10, 20, 50, 60, 70]))
    h = f(rng.choice([2, 5, 10, 12, 15, 20, 25, 40, 50]))
    return ask(rng, values={"m": m, "h": h, "gpe": m * G * h},
               labels={"gpe": ("gain in gravitational potential energy", "J"), "m": ("mass", "kg"),
                       "h": ("height gained", "m")},
               hide_from=["gpe", "m", "h"], subject="an object lifted straight up",
               equation="GPE = mass × g × height", note="Take g = 9.8 N/kg.")


@template(code="weight", subject=PHYSICS, topic="Energy", lessons=["1.4"])
def weight(rng):
    m = f(rng.choice([0.1, 0.2, 0.5, 1, 2, 5, 10, 25, 50, 60, 70, 80]))
    return ask(rng, values={"m": m, "w": m * G},
               labels={"w": ("weight", "N"), "m": ("mass", "kg")},
               hide_from=["w", "m"], subject="an object on Earth", equation="weight = mass × g",
               difficulty=2, note="Take g = 9.8 N/kg.")


MATERIALS = [("water", 4200), ("aluminium", 900), ("copper", 385), ("iron", 450), ("concrete", 880)]


@template(code="specific_heat_capacity", subject=PHYSICS, topic="Energy", lessons=["1.6"])
def specific_heat_capacity(rng):
    name, c = rng.choice(MATERIALS)
    m = f(rng.choice([0.1, 0.2, 0.25, 0.5, 1, 1.5, 2, 2.5, 4, 5]))
    dt = f(rng.randint(2, 60))
    return ask(rng, values={"m": m, "c": f(c), "dt": dt, "e": m * c * dt},
               labels={"e": ("change in thermal energy", "J"), "m": ("mass", "kg"),
                       "c": ("specific heat capacity", "J/kg°C"), "dt": ("temperature rise", "°C")},
               hide_from=["e", "m", "dt", "c"], subject=f"a block of {name}" if name != "water" else "some water being heated",
               equation="change in thermal energy = mass × specific heat capacity × temperature change", difficulty=4)


@template(code="work_done", subject=PHYSICS, topic="Energy", lessons=["1.10"])
def work_done(rng):
    force = f(5 * rng.randint(1, 100))
    s = f(rng.choice([0.5, 1, 2, 3, 4, 5, 8, 10, 12, 20, 25, 50]))
    return ask(rng, values={"f": force, "s": s, "w": force * s},
               labels={"w": ("work done", "J"), "f": ("force", "N"), "s": ("distance moved", "m")},
               hide_from=["w", "f", "s"], subject="a box pushed along the floor",
               equation="work done = force × distance (along the line of the force)", difficulty=2)


@template(code="power_energy_time", subject=PHYSICS, topic="Energy", lessons=["1.10"])
def power_energy_time(rng):
    p = f(rng.choice([5, 10, 20, 40, 60, 100, 500, 1000, 1200, 2000, 2500, 3000]))
    t = f(rng.choice([2, 5, 10, 20, 30, 60, 120, 300]))
    return ask(rng, values={"p": p, "t": t, "e": p * t},
               labels={"e": ("energy transferred", "J"), "p": ("power", "W"), "t": ("time", "s")},
               hide_from=["p", "e", "t"], subject="a motor",
               equation="power = energy transferred ÷ time", difficulty=2)


@template(code="efficiency", subject=PHYSICS, topic="Energy", lessons=["1.11"])
def efficiency(rng):
    total = f(rng.choice([100, 200, 400, 500, 800, 1000, 2000, 2500]))
    eff = f(rng.choice([0.2, 0.25, 0.3, 0.4, 0.45, 0.5, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9]))
    useful = total * eff
    hidden = rng.choice(["eff", "useful", "total"])
    machine = rng.choice(["A motor", "A kettle", "A light bulb", "A pump", "A loudspeaker"])
    meta = {"values": {"total": str(total), "eff": str(eff), "useful": str(useful)}, "hidden": hidden}
    if hidden == "eff":
        q = custom(f"{machine} is supplied with {fmt(total)} J of energy and transfers {fmt(useful)} J usefully. "
                   f"Calculate its efficiency as a percentage.", eff * 100,
                   "efficiency = useful energy output ÷ total energy input, then × 100 for a percentage.", meta, marks=2)
        q["correct_answer"] += "%"
        return q
    if hidden == "useful":
        return custom(f"{machine} has an efficiency of {fmt(eff * 100)}%. It is supplied with {fmt(total)} J. "
                      f"How much energy does it transfer usefully, in J?", useful,
                      f"useful output = efficiency × total input = {fmt(eff)} × {fmt(total)}.", meta, unit="J")
    return custom(f"{machine} has an efficiency of {fmt(eff * 100)}% and transfers {fmt(useful)} J usefully. "
                  f"How much energy was supplied to it, in J?", total,
                  f"total input = useful output ÷ efficiency = {fmt(useful)} ÷ {fmt(eff)}.", meta, difficulty=4, unit="J")


# ===========================================================================
# ELECTRICITY
# ===========================================================================
CURRENTS = [0.1, 0.2, 0.25, 0.5, 1, 1.5, 2, 2.5, 3, 4, 5]


@template(code="ohms_law", subject=PHYSICS, topic="Electricity", lessons=["2.2"])
def ohms_law(rng):
    i, r = f(rng.choice(CURRENTS)), f(rng.choice([2, 4, 5, 6, 8, 10, 12, 20, 24, 30, 50, 100]))
    return ask(rng, values={"i": i, "r": r, "v": i * r},
               labels={"v": ("potential difference", "V"), "i": ("current", "A"), "r": ("resistance", "Ω")},
               hide_from=["v", "i", "r"], subject="a resistor in a circuit",
               equation="potential difference = current × resistance (V = IR)", difficulty=2)


@template(code="charge_current_time", subject=PHYSICS, topic="Electricity", lessons=["2.3"])
def charge_current_time(rng):
    i, t = f(rng.choice(CURRENTS)), f(rng.choice([5, 10, 20, 30, 60, 120, 300]))
    return ask(rng, values={"i": i, "t": t, "q": i * t},
               labels={"q": ("charge flow", "C"), "i": ("current", "A"), "t": ("time", "s")},
               hide_from=["q", "i", "t"], subject="a circuit",
               equation="charge flow = current × time (Q = It)", difficulty=2)


@template(code="electrical_power_iv", subject=PHYSICS, topic="Electricity", lessons=["2.7"])
def electrical_power_iv(rng):
    i, v = f(rng.choice(CURRENTS)), f(rng.choice([1.5, 3, 6, 9, 12, 24, 230]))
    return ask(rng, values={"i": i, "v": v, "p": i * v},
               labels={"p": ("power", "W"), "i": ("current", "A"), "v": ("potential difference", "V")},
               hide_from=["p", "i", "v"], subject="an appliance",
               equation="power = potential difference × current (P = IV)", difficulty=2)


@template(code="electrical_power_i2r", subject=PHYSICS, topic="Electricity", lessons=["2.7"])
def electrical_power_i2r(rng):
    i, r = f(rng.choice([0.5, 1, 2, 3, 4, 5])), f(rng.choice([2, 4, 5, 6, 8, 10, 12, 20, 50]))
    return ask(rng, values={"i": i, "r": r, "p": i * i * r},
               labels={"p": ("power", "W"), "i": ("current", "A"), "r": ("resistance", "Ω")},
               hide_from=["p", "r", "i"], subject="a heating element",
               equation="power = current² × resistance (P = I²R)", difficulty=4)


@template(code="energy_charge_pd", subject=PHYSICS, topic="Electricity", lessons=["2.7"])
def energy_charge_pd(rng):
    q, v = f(rng.choice([2, 5, 10, 20, 50, 100, 500])), f(rng.choice([1.5, 3, 6, 9, 12, 24, 230]))
    return ask(rng, values={"q": q, "v": v, "e": q * v},
               labels={"e": ("energy transferred", "J"), "q": ("charge flow", "C"), "v": ("potential difference", "V")},
               hide_from=["e", "q", "v"], subject="a component",
               equation="energy transferred = charge flow × potential difference (E = QV)", difficulty=3)


@template(code="energy_power_time_electric", subject=PHYSICS, topic="Electricity", lessons=["2.7"])
def energy_power_time_electric(rng):
    p, t = f(rng.choice([60, 100, 500, 800, 1000, 1500, 2000, 3000])), f(rng.choice([10, 30, 60, 120, 300, 600]))
    return ask(rng, values={"p": p, "t": t, "e": p * t},
               labels={"e": ("energy transferred", "J"), "p": ("power", "W"), "t": ("time switched on", "s")},
               hide_from=["e", "p", "t"], subject=rng.choice(["a kettle", "a hairdryer", "a heater", "a toaster"]),
               equation="energy transferred = power × time (E = Pt)", difficulty=2)


# ===========================================================================
# PARTICLE MODEL
# ===========================================================================
@template(code="density", subject=PHYSICS, topic="Particle Model", lessons=["3.2"])
def density(rng):
    v = f(rng.choice([2, 4, 5, 8, 10, 20, 25, 40, 50, 100]))
    rho = f(rng.choice([0.8, 1, 1.2, 2.5, 2.7, 7.8, 8.9, 11.3, 19.3]))
    return ask(rng, values={"m": rho * v, "v": v, "rho": rho},
               labels={"rho": ("density", "g/cm³"), "m": ("mass", "g"), "v": ("volume", "cm³")},
               hide_from=["rho", "m", "v"], subject="a small block",
               equation="density = mass ÷ volume", difficulty=2)


@template(code="specific_latent_heat", subject=PHYSICS, topic="Particle Model", lessons=["3.3"])
def specific_latent_heat(rng):
    kind, latent = rng.choice([("melts", 334000), ("boils", 2260000)])
    m = f(rng.choice([0.1, 0.2, 0.25, 0.5, 1, 1.5, 2, 3]))
    return ask(rng, values={"m": m, "l": f(latent), "e": m * latent},
               labels={"e": ("energy needed", "J"), "m": ("mass", "kg"), "l": ("specific latent heat", "J/kg")},
               hide_from=["e", "m", "l"], subject=f"some water that {kind} completely",
               equation="energy = mass × specific latent heat (E = mL)", difficulty=3)


@template(code="pressure_volume", subject=PHYSICS, topic="Particle Model", lessons=["3.5"])
def pressure_volume(rng):
    p1 = f(rng.choice([100, 120, 150, 200, 250, 300]))
    v1 = f(rng.choice([10, 20, 30, 40, 50, 60, 80]))
    k = f(rng.choice([2, 4, 5, 0.5, 0.25, 1.5, 2.5]))
    v2, p2 = v1 * k, p1 / k
    meta = {"values": {"p1": str(p1), "v1": str(v1), "p2": str(p2), "v2": str(v2)}}
    if not all(_ok(x) for x in (p2, v2)):
        return None
    if rng.random() < 0.5:
        meta["hidden"] = "p2"
        return custom(f"A gas at constant temperature has a pressure of {fmt(p1)} kPa and a volume of {fmt(v1)} cm³. "
                      f"Its volume changes to {fmt(v2)} cm³. Calculate its new pressure, in kPa.", p2,
                      "At constant temperature, pressure × volume stays the same: p₁V₁ = p₂V₂.", meta, unit="kPa")
    meta["hidden"] = "v2"
    return custom(f"A gas at constant temperature has a pressure of {fmt(p1)} kPa and a volume of {fmt(v1)} cm³. "
                  f"Its pressure changes to {fmt(p2)} kPa. Calculate its new volume, in cm³.", v2,
                  "At constant temperature, pressure × volume stays the same: p₁V₁ = p₂V₂.", meta, unit="cm³")


# ===========================================================================
# FORCES
# ===========================================================================
@template(code="hookes_law", subject=PHYSICS, topic="Forces", lessons=["5.5"])
def hookes_law(rng):
    k = f(rng.choice([10, 20, 25, 40, 50, 80, 100, 200, 250, 500]))
    e = f(rng.choice([0.02, 0.04, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3]))
    return ask(rng, values={"k": k, "e": e, "f": k * e},
               labels={"f": ("force", "N"), "k": ("spring constant", "N/m"), "e": ("extension", "m")},
               hide_from=["f", "k", "e"], subject="a spring",
               equation="force = spring constant × extension (F = ke)", difficulty=2)


@template(code="elastic_potential_energy", subject=PHYSICS, topic="Forces", lessons=["5.6"])
def elastic_potential_energy(rng):
    k = f(rng.choice([10, 20, 25, 40, 50, 80, 100, 200, 250, 400, 500]))
    e = f(rng.choice([0.02, 0.04, 0.05, 0.1, 0.2, 0.25, 0.3, 0.4, 0.5]))
    return ask(rng, values={"k": k, "e": e, "ee": k * e * e / 2},
               labels={"ee": ("elastic potential energy", "J"), "k": ("spring constant", "N/m"), "e": ("extension", "m")},
               hide_from=["ee", "k", "e"], subject="a stretched spring",
               equation="elastic potential energy = ½ × spring constant × extension²", difficulty=4)


@template(code="moment", subject=PHYSICS, topic="Forces", lessons=["5.7"])
def moment(rng):
    force = f(5 * rng.randint(1, 40))
    d = f(rng.choice([0.1, 0.2, 0.25, 0.3, 0.4, 0.5, 0.75, 1, 1.5, 2]))
    return ask(rng, values={"f": force, "d": d, "m": force * d},
               labels={"m": ("moment", "Nm"), "f": ("force", "N"), "d": ("perpendicular distance to the pivot", "m")},
               hide_from=["m", "f", "d"], subject=rng.choice(["a spanner turning a nut", "a door being pushed open"]),
               equation="moment = force × perpendicular distance from the pivot (M = Fd)", difficulty=2)


@template(code="principle_of_moments", subject=PHYSICS, topic="Forces", lessons=["5.8"])
def principle_of_moments(rng):
    f1, d1 = f(10 * rng.randint(20, 70)), f(rng.choice([0.5, 1, 1.2, 1.5, 2, 2.5]))
    d2 = f(rng.choice([0.5, 0.8, 1, 1.2, 1.5, 2, 2.5, 3]))
    f2 = f1 * d1 / d2
    if d1 == d2 or not _ok(f2, 2):
        return None
    meta = {"values": {"f1": str(f1), "d1": str(d1), "f2": str(f2), "d2": str(d2)}}
    if rng.random() < 0.5:
        meta["hidden"] = "f2"
        return custom(f"A seesaw is balanced. A child of weight {fmt(f1)} N sits {fmt(d1)} m from the pivot. "
                      f"A second child sits {fmt(d2)} m from the pivot on the other side. "
                      f"Calculate the weight of the second child, in N.", f2,
                      "When balanced, clockwise moment = anticlockwise moment: F₁d₁ = F₂d₂.", meta, difficulty=4, unit="N")
    meta["hidden"] = "d2"
    return custom(f"A seesaw is balanced. A child of weight {fmt(f1)} N sits {fmt(d1)} m from the pivot. "
                  f"A second child of weight {fmt(f2)} N sits on the other side. "
                  f"How far from the pivot is the second child, in m?", d2,
                  "When balanced, clockwise moment = anticlockwise moment: F₁d₁ = F₂d₂.", meta, difficulty=4, unit="m")


@template(code="pressure_force_area", subject=PHYSICS, topic="Forces", lessons=["5.9"])
def pressure_force_area(rng):
    force = f(10 * rng.randint(1, 100))
    area = f(rng.choice([0.01, 0.02, 0.05, 0.1, 0.2, 0.25, 0.5, 1, 2]))
    return ask(rng, values={"f": force, "a": area, "p": force / area},
               labels={"p": ("pressure", "Pa"), "f": ("force", "N"), "a": ("area", "m²")},
               hide_from=["p", "f", "a"], subject="a force acting on a surface",
               equation="pressure = force ÷ area", difficulty=2)


@template(code="speed_distance_time", subject=PHYSICS, topic="Forces", lessons=["5.12"])
def speed_distance_time(rng):
    obj, _, v = mover(rng)
    t = f(rng.choice([5, 10, 20, 30, 40, 60, 90, 120]))
    return ask(rng, values={"v": v, "t": t, "s": v * t},
               labels={"s": ("distance travelled", "m"), "v": ("speed", "m/s"), "t": ("time", "s")},
               hide_from=["s", "v", "t"], subject=obj,
               equation="distance travelled = speed × time", difficulty=1)


@template(code="acceleration", subject=PHYSICS, topic="Forces", lessons=["5.13"])
def acceleration(rng):
    u = f(rng.choice([0, 0, 2, 4, 5, 10]))
    t = f(rng.choice([2, 4, 5, 8, 10, 20, 25]))
    a = f(rng.choice([0.5, 1, 1.5, 2, 2.5, 3, 4, 5]))
    v = u + a * t
    meta = {"values": {"u": str(u), "v": str(v), "t": str(t), "a": str(a)}}
    start = "from rest" if u == 0 else f"from {fmt(u)} m/s"
    if rng.random() < 0.6:
        meta["hidden"] = "a"
        return custom(f"A car speeds up {start} to {fmt(v)} m/s in {fmt(t)} s. Calculate its acceleration, in m/s².",
                      a, "acceleration = change in velocity ÷ time taken.", meta, difficulty=2, marks=2, unit="m/s²")
    meta["hidden"] = "t"
    return custom(f"A car accelerates at {fmt(a)} m/s² {start} to {fmt(v)} m/s. How long does this take, in s?",
                  t, "time = change in velocity ÷ acceleration.", meta, difficulty=3, unit="s")


@template(code="suvat_v2_u2_2as", subject=PHYSICS, topic="Forces", lessons=["5.13", "5.15"])
def suvat_v2_u2_2as(rng):
    u = rng.choice([0, 0, 2, 3, 4, 5, 6, 8, 10])
    v = u + rng.randint(2, 20)
    a = f(rng.choice([0.5, 1, 1.5, 2, 2.5, 4, 5, 10]))
    s = f(v * v - u * u) / (2 * a)
    if not _ok(s, 2):
        return None
    meta = {"values": {"u": str(u), "v": str(v), "a": str(a), "s": str(s)}}
    start = "from rest" if u == 0 else f"from {u} m/s"
    hidden = rng.choice(["s", "a", "v"])
    meta["hidden"] = hidden
    eq = "final velocity² − initial velocity² = 2 × acceleration × distance (v² − u² = 2as)."
    if hidden == "s":
        return custom(f"A cart accelerates uniformly at {fmt(a)} m/s² {start} to {v} m/s. "
                      f"Calculate the distance it travels, in m.", s, eq, meta, difficulty=4, unit="m")
    if hidden == "a":
        return custom(f"A cart accelerates uniformly {start} to {v} m/s over a distance of {fmt(s)} m. "
                      f"Calculate its acceleration, in m/s².", a, eq, meta, difficulty=4, unit="m/s²")
    return custom(f"A cart accelerates uniformly at {fmt(a)} m/s² {start} over a distance of {fmt(s)} m. "
                  f"Calculate its final velocity, in m/s.", f(v), eq, meta, difficulty=5, unit="m/s")


@template(code="newtons_second_law", subject=PHYSICS, topic="Forces", lessons=["5.17"])
def newtons_second_law(rng):
    obj, masses = rng.choice([("a car", [800, 1000, 1200, 1500]), ("a trolley", [0.5, 1, 2, 4]),
                              ("a sledge", [5, 10, 20, 40]), ("a boat", [200, 500, 1000]),
                              ("a cyclist", [70, 80, 90])])
    m = f(rng.choice(masses))
    a = f(rng.choice([0.5, 1, 1.5, 2, 2.5, 3, 4, 5]))
    return ask(rng, values={"m": m, "a": a, "f": m * a},
               labels={"f": ("resultant force", "N"), "m": ("mass", "kg"), "a": ("acceleration", "m/s²")},
               hide_from=["f", "m", "a"], subject=obj,
               equation="resultant force = mass × acceleration (F = ma)", difficulty=2)


@template(code="momentum", subject=PHYSICS, topic="Forces", lessons=["5.20"])
def momentum(rng):
    obj, m, v = mover(rng)
    return ask(rng, values={"m": m, "v": v, "p": m * v},
               labels={"p": ("momentum", "kg m/s"), "m": ("mass", "kg"), "v": ("velocity", "m/s")},
               hide_from=["p", "m", "v"], subject=obj,
               equation="momentum = mass × velocity (p = mv)", difficulty=2)


@template(code="conservation_of_momentum", subject=PHYSICS, topic="Forces", lessons=["5.21"])
def conservation_of_momentum(rng):
    m1, m2 = f(rng.choice([1, 2, 3, 4, 5, 1000, 1200])), f(rng.choice([1, 2, 3, 4, 5, 800, 1000]))
    u1 = f(rng.choice([2, 3, 4, 5, 6, 8, 10, 12, 15, 20]))
    v = m1 * u1 / (m1 + m2)
    if not _ok(v, 2) or (m1 > 100) != (m2 > 100):
        return None
    things = "cars" if m1 > 100 else "trolleys"
    meta = {"values": {"m1": str(m1), "m2": str(m2), "u1": str(u1), "v": str(v)}, "hidden": "v"}
    return custom(f"Two {things} collide and stick together. One has a mass of {fmt(m1)} kg and moves at {fmt(u1)} m/s; "
                  f"the other has a mass of {fmt(m2)} kg and is not moving. Calculate their speed just after the collision, "
                  f"in m/s.", v, "Momentum is conserved: m₁u₁ = (m₁ + m₂)v.", meta, difficulty=4, unit="m/s")


# ===========================================================================
# WAVES, MAGNETISM, RADIOACTIVITY
# ===========================================================================
@template(code="wave_speed", subject=PHYSICS, topic="Waves", lessons=["6.1", "6.13"])
def wave_speed(rng):
    freq = f(rng.choice([2, 5, 10, 20, 50, 100, 200, 250, 500, 1000]))
    lam = f(rng.choice([0.01, 0.02, 0.05, 0.1, 0.2, 0.25, 0.5, 1, 1.5, 2, 4, 10]))
    return ask(rng, values={"f": freq, "lam": lam, "v": freq * lam},
               labels={"v": ("wave speed", "m/s"), "f": ("frequency", "Hz"), "lam": ("wavelength", "m")},
               hide_from=["v", "f", "lam"], subject="a wave",
               equation="wave speed = frequency × wavelength (v = fλ)", difficulty=2)


@template(code="transformer_turns", subject=PHYSICS, topic="Magnetism & Electromagnetism", lessons=["7.10"])
def transformer_turns(rng):
    np_ = f(rng.choice([100, 200, 250, 400, 500, 1000, 2000]))
    ns = f(rng.choice([10, 20, 25, 40, 50, 100, 200, 500, 1000, 4000]))
    vp = f(rng.choice([12, 24, 120, 230, 400, 1000]))
    vs = vp * ns / np_
    if np_ == ns or not _ok(vs, 2):
        return None
    hidden = rng.choice(["vs", "ns"])
    meta = {"values": {"np": str(np_), "ns": str(ns), "vp": str(vp), "vs": str(vs)}, "hidden": hidden}
    kind = "step-up" if ns > np_ else "step-down"
    if hidden == "vs":
        return custom(f"A {kind} transformer has {fmt(np_)} turns on its primary coil and {fmt(ns)} turns on its secondary coil. "
                      f"The primary voltage is {fmt(vp)} V. Calculate the secondary voltage, in V.", vs,
                      "Vp ÷ Vs = np ÷ ns.", meta, difficulty=4, unit="V")
    return custom(f"A transformer has {fmt(np_)} turns on its primary coil. The primary voltage is {fmt(vp)} V and the "
                  f"secondary voltage is {fmt(vs)} V. How many turns are on the secondary coil?", ns,
                  "Vp ÷ Vs = np ÷ ns.", meta, difficulty=4)


@template(code="half_life", subject=PHYSICS, topic="Atomic Structure", lessons=["4.5"])
def half_life(rng):
    a0 = f(rng.choice([80, 160, 200, 400, 640, 800, 1000, 1600, 3200]))
    h = rng.choice([2, 3, 5, 6, 8, 10, 12, 15, 20, 30])
    unit = rng.choice(["minutes", "hours", "days"])
    n = rng.randint(1, 4)
    a = a0 / 2**n
    meta = {"values": {"a0": str(a0), "h": str(h), "n": str(n), "a": str(a)}}
    if rng.random() < 0.6:
        meta["hidden"] = "a"
        return custom(f"A radioactive sample has an activity of {fmt(a0)} Bq. Its half-life is {h} {unit}. "
                      f"What is its activity after {h * n} {unit}, in Bq?", a,
                      f"{h * n} {unit} is {n} half-li{'fe' if n == 1 else 'ves'}, so halve the activity {n} time"
                      f"{'' if n == 1 else 's'}.", meta, difficulty=3, unit="Bq")
    meta["hidden"] = "h"
    return custom(f"The activity of a radioactive sample falls from {fmt(a0)} Bq to {fmt(a)} Bq in {h * n} {unit}. "
                  f"What is its half-life, in {unit}?", f(h),
                  f"{fmt(a0)} halves {n} time{'' if n == 1 else 's'} to reach {fmt(a)}, so {h * n} ÷ {n}.", meta,
                  difficulty=4)
