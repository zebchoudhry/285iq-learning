"""
Chemistry calculation templates for Quantitative Chemistry (3.1 to 3.9).

Like the physics templates, each one chooses a consistent set of amounts (moles first,
then masses, volumes and percentages worked out from them), hides one and asks for it.
Every question carries `meta` so the tests can re-check the chemistry independently.
"""
import math
from decimal import ROUND_HALF_UP, Decimal
from fractions import Fraction as Fr

from learning.generators.engine import make_question, mcq, tdec, template
from learning.generators.templates_science import parse_formula

CHEMISTRY = "chemistry"
TOPIC = "Quantitative Chemistry"

# Relative atomic masses as given on the AQA periodic table.
AR = {
    "H": Fr(1), "Li": Fr(7), "C": Fr(12), "N": Fr(14), "O": Fr(16), "Na": Fr(23), "Mg": Fr(24),
    "Al": Fr(27), "S": Fr(32), "Cl": Fr(71, 2), "K": Fr(39), "Ca": Fr(40), "Fe": Fr(56),
    "Cu": Fr(127, 2), "Zn": Fr(65),
}

COMPOUNDS = [
    "H2O", "CO2", "NaCl", "MgO", "CaCO3", "H2SO4", "NaOH", "Ca(OH)2", "Mg(OH)2", "Al2O3", "Fe2O3",
    "CuSO4", "KCl", "NH3", "CH4", "C2H6", "HCl", "ZnCl2", "Na2CO3", "Al2(SO4)3", "Mg(NO3)2",
    "(NH4)2SO4", "C6H12O6", "CuO", "MgCl2", "CaCl2", "K2O", "LiOH",
]


def mr(formula: str) -> Fr:
    return sum(AR[el] * n for el, n in parse_formula(formula).items())


def ar_note(*formulas: str) -> str:
    elements = []
    for f_ in formulas:
        for el in parse_formula(f_):
            if el not in elements:
                elements.append(el)
    return "(Relative atomic masses: " + ", ".join(f"{el} = {tdec(AR[el])}" for el in elements) + ")"


def _ok(x: Fr, dp: int = 2) -> bool:
    return x > 0 and (x * 10**dp).denominator == 1


def _q(text, answer, explanation, meta, difficulty=3, marks=2, suffix=""):
    q = make_question(text, tdec(answer) + suffix, difficulty=difficulty, marks=marks, explanation=explanation)
    q["meta"] = meta
    return q


# ---------------------------------------------------------------------------
@template(code="relative_formula_mass", subject=CHEMISTRY, topic=TOPIC, lessons=["3.1"])
def relative_formula_mass(rng):
    formula = rng.choice(COMPOUNDS)
    return _q(f"Calculate the relative formula mass (Mr) of {formula}. {ar_note(formula)}", mr(formula),
              "Add up the relative atomic masses of every atom in the formula. A number after a bracket "
              "multiplies everything inside it.", {"formula": formula}, difficulty=2)


MOLES = [0.1, 0.2, 0.25, 0.5, 1, 1.5, 2, 2.5, 3, 4, 5]


@template(code="moles_and_mass", subject=CHEMISTRY, topic=TOPIC, lessons=["3.2"])
def moles_and_mass(rng):
    formula = rng.choice(COMPOUNDS)
    n, m_r = Fr(str(rng.choice(MOLES))), mr(formula)
    mass = n * m_r
    if not _ok(mass):
        return None
    meta = {"formula": formula, "n": str(n), "mass": str(mass), "mr": str(m_r)}
    if rng.random() < 0.5:
        meta["hidden"] = "n"
        return _q(f"How many moles are there in {tdec(mass)} g of {formula}? The Mr of {formula} is {tdec(m_r)}.", n,
                  "moles = mass ÷ Mr.", meta, difficulty=2)
    meta["hidden"] = "mass"
    return _q(f"Calculate the mass of {tdec(n)} mol of {formula}, in g. The Mr of {formula} is {tdec(m_r)}.", mass,
              "mass = moles × Mr.", meta, difficulty=2)


def _balanced(left, right, coeffs):
    def side(species, cs):
        return " + ".join((f"{c}" if c != 1 else "") + s for s, c in zip(species, cs))
    return side(left, coeffs[:len(left)]) + " → " + side(right, coeffs[len(left):])


# Reactions whose species all have relative atomic masses above.
MASS_REACTIONS = [
    (["Mg", "O2"], ["MgO"], [2, 1, 2]),
    (["H2", "O2"], ["H2O"], [2, 1, 2]),
    (["N2", "H2"], ["NH3"], [1, 3, 2]),
    (["Fe2O3", "CO"], ["Fe", "CO2"], [1, 3, 2, 3]),
    (["Al", "O2"], ["Al2O3"], [4, 3, 2]),
    (["CH4", "O2"], ["CO2", "H2O"], [1, 2, 1, 2]),
    (["Mg", "HCl"], ["MgCl2", "H2"], [1, 2, 1, 1]),
    (["Zn", "HCl"], ["ZnCl2", "H2"], [1, 2, 1, 1]),
    (["NaOH", "H2SO4"], ["Na2SO4", "H2O"], [2, 1, 1, 2]),
    (["CaCO3"], ["CaO", "CO2"], [1, 1, 1]),
    (["CaCO3", "HCl"], ["CaCl2", "CO2", "H2O"], [1, 2, 1, 1, 1]),
    (["Na", "Cl2"], ["NaCl"], [2, 1, 2]),
]


@template(code="reacting_masses", subject=CHEMISTRY, topic=TOPIC, lessons=["3.3"])
def reacting_masses(rng):
    left, right, coeffs = rng.choice(MASS_REACTIONS)
    species = left + right
    i, j = rng.sample(range(len(species)), 2)
    n_i = Fr(str(rng.choice([0.1, 0.2, 0.25, 0.5, 1, 2])))
    mass_i = n_i * mr(species[i])
    n_j = n_i * Fr(coeffs[j], coeffs[i])
    mass_j = n_j * mr(species[j])
    if not (_ok(mass_i) and _ok(mass_j) and _ok(n_j, 4)):
        return None
    verb = "is made" if j >= len(left) else "is needed"
    return _q(f"{_balanced(left, right, coeffs)}. What mass of {species[j]} {verb} when {tdec(mass_i)} g of "
              f"{species[i]} reacts? Give your answer in g. {ar_note(species[i], species[j])}", mass_j,
              f"moles of {species[i]} = {tdec(mass_i)} ÷ {tdec(mr(species[i]))} = {tdec(n_i)}. The equation gives a "
              f"ratio of {coeffs[i]}:{coeffs[j]}, so moles of {species[j]} = {tdec(n_j)}. "
              f"mass = {tdec(n_j)} × {tdec(mr(species[j]))}.",
              {"left": left, "right": right, "coeffs": coeffs, "i": i, "j": j,
               "mass_i": str(mass_i), "mass_j": str(mass_j)}, difficulty=4, marks=3)


CARBONATES = [("CaCO3", "CaO"), ("MgCO3", "MgO"), ("CuCO3", "CuO"), ("ZnCO3", "ZnO")]


@template(code="conservation_of_mass", subject=CHEMISTRY, topic=TOPIC, lessons=["3.4"])
def conservation_of_mass(rng):
    carbonate, oxide = rng.choice(CARBONATES)
    n = Fr(str(rng.choice([0.05, 0.1, 0.2, 0.25, 0.5, 1])))
    m_carb, m_ox = n * mr(carbonate), n * mr(oxide)
    m_co2 = m_carb - m_ox
    if not all(_ok(x) for x in (m_carb, m_ox, m_co2)):
        return None
    return _q(f"When {tdec(m_carb)} g of {carbonate} is heated, it breaks down into {tdec(m_ox)} g of {oxide} and "
              f"carbon dioxide gas, which escapes. What mass of carbon dioxide is given off, in g?", m_co2,
              "Mass is conserved: mass of carbonate = mass of oxide + mass of carbon dioxide.",
              {"m_carb": str(m_carb), "m_ox": str(m_ox), "m_co2": str(m_co2)}, difficulty=2)


@template(code="limiting_reactant", subject=CHEMISTRY, topic=TOPIC, lessons=["3.5"])
def limiting_reactant(rng):
    left, right, coeffs = rng.choice([r for r in MASS_REACTIONS if len(r[0]) == 2])
    a, b = left
    n_a = Fr(str(rng.choice([0.1, 0.2, 0.25, 0.5, 1, 2])))
    n_b = Fr(str(rng.choice([0.1, 0.2, 0.25, 0.5, 1, 2])))
    need_b = n_a * Fr(coeffs[1], coeffs[0])  # moles of b that would react with all of a
    if need_b == n_b:
        return None
    m_a, m_b = n_a * mr(a), n_b * mr(b)
    if not (_ok(m_a) and _ok(m_b)):
        return None
    limiting = a if need_b < n_b else b
    q = mcq(rng, f"{_balanced(left, right, coeffs)}. {tdec(m_a)} g of {a} is mixed with {tdec(m_b)} g of {b}. "
                 f"Which reactant is the limiting reactant? {ar_note(a, b)}",
            limiting, [a, b, "Neither: they react exactly", "It can't be worked out without the products"],
            difficulty=4,
            explanation=f"Moles: {a} = {tdec(n_a)}, {b} = {tdec(n_b)}. The equation needs {coeffs[0]} {a} for every "
                        f"{coeffs[1]} {b}, so {tdec(n_a)} mol of {a} needs {tdec(need_b)} mol of {b}. "
                        f"{limiting} runs out first.")
    if q:
        q["meta"] = {"left": left, "coeffs": coeffs, "m_a": str(m_a), "m_b": str(m_b)}
    return q


@template(code="concentration_g_dm3", subject=CHEMISTRY, topic=TOPIC, lessons=["3.6"])
def concentration_g_dm3(rng):
    v_cm3 = Fr(rng.choice([25, 50, 100, 200, 250, 500, 1000]))
    c = Fr(rng.choice([2, 4, 5, 8, 10, 20, 25, 40, 50, 80, 100]))
    mass = c * v_cm3 / 1000
    solute = rng.choice(["sodium chloride", "copper sulfate", "potassium nitrate", "glucose"])
    meta = {"c": str(c), "v_cm3": str(v_cm3), "mass": str(mass)}
    if not _ok(mass):
        return None
    if rng.random() < 0.5:
        meta["hidden"] = "c"
        return _q(f"{tdec(mass)} g of {solute} is dissolved in water to make {tdec(v_cm3)} cm³ of solution. "
                  f"Calculate the concentration in g/dm³.", c,
                  f"Convert the volume to dm³ ({tdec(v_cm3)} ÷ 1000), then concentration = mass ÷ volume.", meta)
    meta["hidden"] = "mass"
    return _q(f"What mass of {solute} is dissolved in {tdec(v_cm3)} cm³ of a solution of concentration "
              f"{tdec(c)} g/dm³? Give your answer in g.", mass,
              f"Convert the volume to dm³ ({tdec(v_cm3)} ÷ 1000), then mass = concentration × volume.", meta, difficulty=4)


GASES = ["O2", "CO2", "N2", "H2", "CH4", "Cl2", "NH3"]


@template(code="gas_volume", subject=CHEMISTRY, topic=TOPIC, lessons=["3.7"])
def gas_volume(rng):
    gas = rng.choice(GASES)
    n = Fr(str(rng.choice([0.1, 0.2, 0.25, 0.5, 1, 1.5, 2, 2.5, 3, 4, 5])))
    vol, mass = n * 24, n * mr(gas)
    meta = {"gas": gas, "n": str(n), "vol": str(vol), "mass": str(mass)}
    if not _ok(mass):
        return None
    note = "One mole of any gas occupies 24 dm³ at room temperature and pressure."
    if rng.random() < 0.5:
        meta["hidden"] = "vol"
        return _q(f"What volume does {tdec(mass)} g of {gas} occupy at room temperature and pressure, in dm³? "
                  f"{note} {ar_note(gas)}", vol, "moles = mass ÷ Mr, then volume = moles × 24.", meta, difficulty=4, marks=3)
    meta["hidden"] = "n"
    return _q(f"How many moles of {gas} are in {tdec(vol)} dm³ of the gas at room temperature and pressure? {note}",
              n, "moles = volume ÷ 24.", meta, difficulty=2)


# reaction text, reactants [(formula, coeff)], desired (formula, coeff)
ATOM_ECONOMY = [
    ("CaCO3 → CaO + CO2", [("CaCO3", 1)], ("CaO", 1)),
    ("Mg + 2HCl → MgCl2 + H2", [("Mg", 1), ("HCl", 2)], ("MgCl2", 1)),
    ("Zn + 2HCl → ZnCl2 + H2", [("Zn", 1), ("HCl", 2)], ("H2", 1)),
    ("2NaOH + H2SO4 → Na2SO4 + 2H2O", [("NaOH", 2), ("H2SO4", 1)], ("Na2SO4", 1)),
    ("CaCO3 + 2HCl → CaCl2 + CO2 + H2O", [("CaCO3", 1), ("HCl", 2)], ("CaCl2", 1)),
    ("C6H12O6 → 2C2H5OH + 2CO2", [("C6H12O6", 1)], ("C2H5OH", 2)),
    ("Fe2O3 + 3CO → 2Fe + 3CO2", [("Fe2O3", 1), ("CO", 3)], ("Fe", 2)),
    ("2K + 2H2O → 2KOH + H2", [("K", 2), ("H2O", 2)], ("KOH", 2)),
]


@template(code="atom_economy", subject=CHEMISTRY, topic=TOPIC, lessons=["3.8"])
def atom_economy(rng):
    text, reactants, (product, k) = rng.choice(ATOM_ECONOMY)
    total = sum(mr(f_) * c for f_, c in reactants)
    useful = mr(product) * k
    value = Decimal(useful.numerator * 100) / Decimal(useful.denominator) / (Decimal(total.numerator) / Decimal(total.denominator))
    answer = value.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    q = make_question(
        f"{text}. Calculate the atom economy for making {product}. Give your answer to 1 decimal place. "
        f"{ar_note(*[f_ for f_, _ in reactants], product)}",
        format(answer, "f"), difficulty=4, marks=3,
        explanation=f"atom economy = (Mr of desired product × its number in the equation) ÷ (total Mr of reactants) "
                    f"× 100 = {tdec(useful)} ÷ {tdec(total)} × 100.",
    )
    q["meta"] = {"reactants": reactants, "product": product, "k": k}
    return q


@template(code="percentage_yield", subject=CHEMISTRY, topic=TOPIC, lessons=["3.9"])
def percentage_yield(rng):
    theoretical = Fr(str(rng.choice([2, 4, 5, 8, 10, 12, 16, 20, 25, 40, 50])))
    pct = Fr(rng.choice([40, 50, 60, 65, 70, 75, 80, 85, 90, 95]))
    actual = theoretical * pct / 100
    product = rng.choice(["magnesium oxide", "copper sulfate crystals", "aspirin", "zinc chloride", "ethyl ethanoate"])
    meta = {"theoretical": str(theoretical), "pct": str(pct), "actual": str(actual)}
    if not _ok(actual):
        return None
    if rng.random() < 0.6:
        meta["hidden"] = "pct"
        return _q(f"A student expected to make {tdec(theoretical)} g of {product} but made {tdec(actual)} g. "
                  f"Calculate the percentage yield.", pct,
                  "percentage yield = actual mass ÷ theoretical mass × 100.", meta, suffix="%")
    meta["hidden"] = "actual"
    return _q(f"The theoretical yield of {product} in a reaction is {tdec(theoretical)} g. The percentage yield is "
              f"{tdec(pct)}%. What mass of {product} was actually made, in g?", actual,
              "actual mass = percentage yield ÷ 100 × theoretical mass.", meta, difficulty=3)
