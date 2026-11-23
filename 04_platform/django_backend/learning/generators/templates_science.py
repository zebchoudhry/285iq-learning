"""
Physics and chemistry question templates for lessons that had few or no
questions. See engine.py for how templates work. All wording is original and
every answer is worked out from the numbers the template draws.
"""
import math
from typing import Dict

from learning.generators.engine import make_question, mcq, template

PHYSICS = "physics"
CHEMISTRY = "chemistry"

# ---------------------------------------------------------------------------
# Data (scientific facts, not copyrightable wording)
# ---------------------------------------------------------------------------
# name: (atomic number, isotopes' mass numbers)
ELEMENTS = {
    "hydrogen": (1, [1, 2, 3]), "helium": (2, [3, 4]), "lithium": (3, [6, 7]),
    "beryllium": (4, [9]), "boron": (5, [10, 11]), "carbon": (6, [12, 13, 14]),
    "nitrogen": (7, [14, 15]), "oxygen": (8, [16, 17, 18]), "fluorine": (9, [19]),
    "neon": (10, [20, 21, 22]), "sodium": (11, [23]), "magnesium": (12, [24, 25, 26]),
    "aluminium": (13, [27]), "silicon": (14, [28, 29, 30]), "phosphorus": (15, [31]),
    "sulfur": (16, [32, 33, 34]), "chlorine": (17, [35, 37]), "argon": (18, [36, 38, 40]),
    "potassium": (19, [39, 40, 41]), "calcium": (20, [40, 42, 44]), "copper": (29, [63, 65]),
}

# name: (atomic number, charge)
COMMON_IONS = {
    "lithium": (3, 1), "sodium": (11, 1), "potassium": (19, 1), "magnesium": (12, 2),
    "calcium": (20, 2), "aluminium": (13, 3), "fluorine": (9, -1), "chlorine": (17, -1),
    "oxygen": (8, -2), "sulfur": (16, -2),
}

# Nuclei that decay by the stated mode: (name, atomic number, mass number)
ALPHA_EMITTERS = [
    ("uranium", 92, 238), ("uranium", 92, 235), ("radium", 88, 226), ("radon", 86, 222),
    ("polonium", 84, 218), ("polonium", 84, 210), ("thorium", 90, 230),
    ("plutonium", 94, 239), ("americium", 95, 241),
]
BETA_EMITTERS = [
    ("lead", 82, 214), ("bismuth", 83, 214), ("thorium", 90, 234),
    ("protactinium", 91, 234), ("lead", 82, 210), ("bismuth", 83, 210),
]


def _ion_label(charge: int) -> str:
    return f"{abs(charge)}{'+' if charge > 0 else '-'}"


# ===========================================================================
# PHYSICS: atomic structure
# ===========================================================================
@template(code="neutrons_in_atom", subject=PHYSICS, topic="Atomic Structure", lessons=["4.2"])
def neutrons_in_atom(rng):
    name = rng.choice(list(ELEMENTS))
    z, isotopes = ELEMENTS[name]
    a = rng.choice(isotopes)
    return make_question(
        f"An atom of {name}-{a} has an atomic number of {z}. How many neutrons does it contain?",
        str(a - z), difficulty=2,
        explanation=f"Neutrons = mass number − atomic number = {a} − {z} = {a - z}.",
    )


@template(code="electrons_in_neutral_atom", subject=PHYSICS, topic="Atomic Structure", lessons=["4.2"])
def electrons_in_neutral_atom(rng):
    name = rng.choice(list(ELEMENTS))
    z, isotopes = ELEMENTS[name]
    a = rng.choice(isotopes)
    return make_question(
        f"A neutral atom of {name}-{a} has {z} protons. How many electrons does it have?",
        str(z), difficulty=1,
        explanation="A neutral atom has the same number of electrons as protons.",
    )


@template(code="electrons_in_ion", subject=PHYSICS, topic="Atomic Structure", lessons=["4.2"])
def electrons_in_ion(rng):
    name = rng.choice(list(COMMON_IONS))
    z, charge = COMMON_IONS[name]
    return make_question(
        f"A {name} ion has a charge of {_ion_label(charge)}. A {name} atom has {z} protons. "
        f"How many electrons does the ion have?",
        str(z - charge), difficulty=3,
        explanation=f"The ion has {z} protons. "
                    f"{'Losing' if charge > 0 else 'Gaining'} {abs(charge)} electron"
                    f"{'s' if abs(charge) > 1 else ''} gives {z - charge} electrons.",
    )


@template(code="isotope_neutron_difference", subject=PHYSICS, topic="Atomic Structure", lessons=["4.2"])
def isotope_neutron_difference(rng):
    multi = [n for n, (_, isotopes) in ELEMENTS.items() if len(isotopes) >= 2]
    name = rng.choice(multi)
    a1, a2 = sorted(rng.sample(ELEMENTS[name][1], 2))
    return make_question(
        f"{name.capitalize()}-{a1} and {name}-{a2} are isotopes of {name}. "
        f"How many more neutrons does {name}-{a2} have than {name}-{a1}?",
        str(a2 - a1), difficulty=2,
        explanation="Isotopes have the same number of protons, so the difference in neutrons "
                    "is the difference in mass numbers.",
    )


# ===========================================================================
# PHYSICS: nuclear decay equations
# ===========================================================================
@template(code="alpha_decay_numbers", subject=PHYSICS, topic="Atomic Structure", lessons=["4.4"])
def alpha_decay_numbers(rng):
    name, z, a = rng.choice(ALPHA_EMITTERS)
    ask_mass = rng.random() < 0.5
    return make_question(
        f"A nucleus of {name}-{a} (atomic number {z}) decays by emitting an alpha particle. "
        f"What is the {'mass number' if ask_mass else 'atomic number'} of the nucleus that is formed?",
        str(a - 4 if ask_mass else z - 2), difficulty=3,
        explanation="An alpha particle is 2 protons and 2 neutrons, so the mass number falls by 4 "
                    "and the atomic number falls by 2.",
    )


@template(code="beta_decay_numbers", subject=PHYSICS, topic="Atomic Structure", lessons=["4.4"])
def beta_decay_numbers(rng):
    name, z, a = rng.choice(BETA_EMITTERS)
    ask_mass = rng.random() < 0.5
    return make_question(
        f"A nucleus of {name}-{a} (atomic number {z}) decays by beta-minus emission. "
        f"What is the {'mass number' if ask_mass else 'atomic number'} of the nucleus that is formed?",
        str(a if ask_mass else z + 1), difficulty=3,
        explanation="In beta-minus decay a neutron turns into a proton, so the mass number stays the "
                    "same and the atomic number goes up by 1.",
    )


@template(code="identify_radiation", subject=PHYSICS, topic="Atomic Structure", lessons=["4.4"])
def identify_radiation(rng):
    kind = rng.choice(["alpha", "beta", "gamma"])
    name, z, a = rng.choice(ALPHA_EMITTERS if kind == "alpha" else BETA_EMITTERS)
    if kind == "alpha":
        z2, a2 = z - 2, a - 4
        why = "the mass number fell by 4 and the atomic number fell by 2"
    elif kind == "beta":
        z2, a2 = z + 1, a
        why = "the mass number stayed the same and the atomic number rose by 1"
    else:
        z2, a2 = z, a
        why = "the mass number and atomic number did not change, only energy was lost"
    answers = {"alpha": "Alpha", "beta": "Beta (minus)", "gamma": "Gamma"}
    return mcq(
        rng,
        f"A nucleus with mass number {a} and atomic number {z} decays into a nucleus with mass number "
        f"{a2} and atomic number {z2}. Which type of radiation was emitted?",
        answers[kind], [v for k, v in answers.items() if k != kind] + ["Neutron"], difficulty=3,
        explanation=f"The radiation was {answers[kind].lower()} because {why}.",
    )


# ===========================================================================
# CHEMISTRY: formulae and balancing
# ===========================================================================
ELEMENT_NAMES = {
    "H": "hydrogen", "C": "carbon", "N": "nitrogen", "O": "oxygen", "Na": "sodium",
    "Mg": "magnesium", "Al": "aluminium", "S": "sulfur", "Cl": "chlorine", "K": "potassium",
    "Ca": "calcium", "Mn": "manganese", "Fe": "iron", "Cu": "copper",
}

FORMULAE = [
    "H2O", "CO2", "Ca(OH)2", "Al2(SO4)3", "Mg(NO3)2", "NH4NO3", "H2SO4", "Fe2O3",
    "C6H12O6", "Na2CO3", "Al(OH)3", "(NH4)2SO4", "CaCO3", "C2H5OH", "CH3COOH",
    "Ca(NO3)2", "Cu(OH)2", "KMnO4", "Mg(OH)2", "Fe2(SO4)3",
]


def parse_formula(formula: str) -> Dict[str, int]:
    """Count the atoms of each element in a formula such as 'Al2(SO4)3'."""
    stack = [{}]
    i = 0
    while i < len(formula):
        ch = formula[i]
        if ch == "(":
            stack.append({})
            i += 1
        elif ch == ")":
            i += 1
            j = i
            while j < len(formula) and formula[j].isdigit():
                j += 1
            multiplier = int(formula[i:j] or 1)
            i = j
            group = stack.pop()
            for el, n in group.items():
                stack[-1][el] = stack[-1].get(el, 0) + n * multiplier
        elif ch.isupper():
            j = i + 1
            while j < len(formula) and formula[j].islower():
                j += 1
            el = formula[i:j]
            k = j
            while k < len(formula) and formula[k].isdigit():
                k += 1
            n = int(formula[j:k] or 1)
            stack[-1][el] = stack[-1].get(el, 0) + n
            i = k
        else:
            raise ValueError(f"Unexpected character {ch!r} in {formula!r}")
    return stack[0]


# Balanced reactions: (left species, right species) with the coefficients that balance them.
REACTIONS = [
    (["Mg", "O2"], ["MgO"], [2, 1, 2]),
    (["H2", "O2"], ["H2O"], [2, 1, 2]),
    (["N2", "H2"], ["NH3"], [1, 3, 2]),
    (["Fe", "O2"], ["Fe2O3"], [4, 3, 2]),
    (["Al", "O2"], ["Al2O3"], [4, 3, 2]),
    (["CH4", "O2"], ["CO2", "H2O"], [1, 2, 1, 2]),
    (["C3H8", "O2"], ["CO2", "H2O"], [1, 5, 3, 4]),
    (["C2H6", "O2"], ["CO2", "H2O"], [2, 7, 4, 6]),
    (["Na", "Cl2"], ["NaCl"], [2, 1, 2]),
    (["Ca", "O2"], ["CaO"], [2, 1, 2]),
    (["Al", "Cl2"], ["AlCl3"], [2, 3, 2]),
    (["Mg", "HCl"], ["MgCl2", "H2"], [1, 2, 1, 1]),
    (["Zn", "HCl"], ["ZnCl2", "H2"], [1, 2, 1, 1]),
    (["NaOH", "H2SO4"], ["Na2SO4", "H2O"], [2, 1, 1, 2]),
    (["CaCO3", "HCl"], ["CaCl2", "CO2", "H2O"], [1, 2, 1, 1, 1]),
    (["K", "H2O"], ["KOH", "H2"], [2, 2, 2, 1]),
    (["Li", "H2O"], ["LiOH", "H2"], [2, 2, 2, 1]),
    (["Na", "H2O"], ["NaOH", "H2"], [2, 2, 2, 1]),
]


def _equation_text(left, right, coefficients=None):
    species = left + right
    if coefficients:
        shown = [(f"{c} " if c != 1 else "") + s for c, s in zip(coefficients, species)]
    else:
        shown = [f"__ {s}" for s in species]
    return " + ".join(shown[:len(left)]) + " → " + " + ".join(shown[len(left):])


@template(code="balance_equation", subject=CHEMISTRY, topic="Atomic Structure", lessons=["1.4"])
def balance_equation(rng):
    left, right, coeffs = rng.choice(REACTIONS)
    return make_question(
        f"Balance this equation by writing a number in front of each substance, in order: "
        f"{_equation_text(left, right)}",
        ", ".join(map(str, coeffs)), difficulty=3, marks=2,
        explanation=f"The balanced equation is {_equation_text(left, right, coeffs)}. "
                    f"Count the atoms of each element on both sides to check.",
    )


@template(code="balance_one_coefficient", subject=CHEMISTRY, topic="Atomic Structure", lessons=["1.4"])
def balance_one_coefficient(rng):
    left, right, coeffs = rng.choice(REACTIONS)
    species = left + right
    i = rng.randrange(len(species))
    return make_question(
        f"The unbalanced equation is {_equation_text(left, right)}. When it is balanced, "
        f"what number goes in front of {species[i]}? (Write 1 if no number is needed.)",
        str(coeffs[i]), difficulty=3,
        explanation=f"The balanced equation is {_equation_text(left, right, coeffs)}.",
    )


@template(code="count_atoms_of_element", subject=CHEMISTRY, topic="Atomic Structure", lessons=["1.4"])
def count_atoms_of_element(rng):
    formula = rng.choice(FORMULAE)
    counts = parse_formula(formula)
    symbol = rng.choice(list(counts))
    n = rng.randint(1, 4)
    shown = f"{n}{formula}" if n > 1 else formula
    return make_question(
        f"How many atoms of {ELEMENT_NAMES[symbol]} are shown in {shown}?",
        str(counts[symbol] * n), difficulty=2,
        explanation=f"Each {formula} contains {counts[symbol]} {ELEMENT_NAMES[symbol]} atom"
                    f"{'s' if counts[symbol] > 1 else ''}"
                    + (f", and there are {n} of them, so {counts[symbol]} × {n}." if n > 1 else "."),
    )


@template(code="count_total_atoms", subject=CHEMISTRY, topic="Atomic Structure", lessons=["1.4"])
def count_total_atoms(rng):
    formula = rng.choice(FORMULAE)
    total = sum(parse_formula(formula).values())
    return make_question(
        f"How many atoms are there altogether in one unit of {formula}?", str(total), difficulty=2,
        explanation="Add up the atoms of every element. A number outside a bracket multiplies "
                    "everything inside it.",
    )


# ===========================================================================
# CHEMISTRY: ionic bonding and compounds
# ===========================================================================
# name, symbol, charge, is polyatomic
CATIONS = [
    ("sodium", "Na", 1, False), ("potassium", "K", 1, False), ("lithium", "Li", 1, False),
    ("magnesium", "Mg", 2, False), ("calcium", "Ca", 2, False), ("zinc", "Zn", 2, False),
    ("aluminium", "Al", 3, False), ("ammonium", "NH4", 1, True),
]
ANIONS = [
    ("chloride", "Cl", 1, False), ("bromide", "Br", 1, False), ("fluoride", "F", 1, False),
    ("oxide", "O", 2, False), ("sulfide", "S", 2, False), ("hydroxide", "OH", 1, True),
    ("nitrate", "NO3", 1, True), ("sulfate", "SO4", 2, True), ("carbonate", "CO3", 2, True),
]


def ionic_formula(cation, anion) -> str:
    _, c_sym, c_charge, c_poly = cation
    _, a_sym, a_charge, a_poly = anion
    lcm = math.lcm(c_charge, a_charge)
    n_c, n_a = lcm // c_charge, lcm // a_charge

    def part(sym, n, poly):
        if n == 1:
            return sym
        return f"({sym}){n}" if poly else f"{sym}{n}"

    return part(c_sym, n_c, c_poly) + part(a_sym, n_a, a_poly)


@template(code="ionic_formula_from_name", subject=CHEMISTRY, topic="Bonding", lessons=["2.3"])
def ionic_formula_from_name(rng):
    cation, anion = rng.choice(CATIONS), rng.choice(ANIONS)
    formula = ionic_formula(cation, anion)
    return make_question(
        f"Write the formula of {cation[0]} {anion[0]}.", formula, difficulty=3,
        explanation=f"{cation[0].capitalize()} ions have a charge of {_ion_label(cation[2])} and "
                    f"{anion[0]} ions have a charge of {_ion_label(-anion[2])}. "
                    f"Balance the charges so the compound has no overall charge.",
    )


@template(code="ionic_name_from_formula", subject=CHEMISTRY, topic="Bonding", lessons=["2.3"])
def ionic_name_from_formula(rng):
    cation, anion = rng.choice(CATIONS), rng.choice(ANIONS)
    return make_question(
        f"What is the name of the compound with the formula {ionic_formula(cation, anion)}?",
        f"{cation[0]} {anion[0]}", difficulty=3,
        explanation="Name the metal (or ammonium) first, then the negative ion.",
    )


# name, group
IONIC_ELEMENTS = [
    ("lithium", 1), ("sodium", 1), ("potassium", 1), ("magnesium", 2), ("calcium", 2),
    ("aluminium", 3), ("oxygen", 6), ("sulfur", 6), ("fluorine", 7), ("chlorine", 7), ("bromine", 7),
]


def _group_charge(group: int) -> int:
    return group if group <= 3 else group - 8


@template(code="ion_charge_from_group", subject=CHEMISTRY, topic="Bonding", lessons=["2.2"])
def ion_charge_from_group(rng):
    name, group = rng.choice(IONIC_ELEMENTS)
    charge = _group_charge(group)
    options = [_ion_label(c) for c in (1, 2, 3, -1, -2, -3)]
    return mcq(
        rng, f"{name.capitalize()} is in Group {group}. What is the charge on the ion it forms?",
        _ion_label(charge), [o for o in options if o != _ion_label(charge)], difficulty=2,
        explanation=f"Group {group} atoms "
                    f"{'lose' if charge > 0 else 'gain'} {abs(charge)} electron"
                    f"{'s' if abs(charge) > 1 else ''} to get a full outer shell.",
    )


@template(code="electrons_transferred", subject=CHEMISTRY, topic="Bonding", lessons=["2.2"])
def electrons_transferred(rng):
    name, group = rng.choice(IONIC_ELEMENTS)
    charge = _group_charge(group)
    return make_question(
        f"How many electrons does an atom of {name} (Group {group}) "
        f"{'lose' if charge > 0 else 'gain'} to form an ion?",
        str(abs(charge)), difficulty=2,
        explanation=f"Metals lose their outer electrons and non-metals gain electrons to reach a "
                    f"full outer shell. Group {group} atoms "
                    f"{'lose' if charge > 0 else 'gain'} {abs(charge)}.",
    )


# ===========================================================================
# CHEMISTRY: covalent bonding
# ===========================================================================
COVALENT = [("carbon", 4), ("silicon", 4), ("nitrogen", 5), ("phosphorus", 5), ("oxygen", 6),
            ("sulfur", 6), ("fluorine", 7), ("chlorine", 7), ("bromine", 7)]


@template(code="covalent_bonds_from_group", subject=CHEMISTRY, topic="Bonding", lessons=["2.5"])
def covalent_bonds_from_group(rng):
    name, group = rng.choice(COVALENT)
    return make_question(
        f"{name.capitalize()} is in Group {group}. How many covalent bonds does an atom of "
        f"{name} usually form?",
        str(8 - group), difficulty=2,
        explanation=f"A Group {group} atom has {group} outer electrons and needs {8 - group} more "
                    f"to fill its outer shell, so it shares {8 - group} pair"
                    f"{'s' if 8 - group > 1 else ''} of electrons.",
    )


@template(code="outer_electrons_needed", subject=CHEMISTRY, topic="Bonding", lessons=["2.5"])
def outer_electrons_needed(rng):
    name, group = rng.choice(COVALENT)
    return make_question(
        f"An atom of {name} has {group} electrons in its outer shell. How many more electrons "
        f"does it need to share to have a full outer shell of 8?",
        str(8 - group), difficulty=2,
        explanation=f"8 − {group} = {8 - group}.",
    )


# ===========================================================================
# CHEMISTRY: neutralisation
# ===========================================================================
ACIDS = [("hydrochloric acid", "chloride"), ("sulfuric acid", "sulfate"), ("nitric acid", "nitrate")]
BASES = [
    ("sodium hydroxide", "sodium"), ("potassium hydroxide", "potassium"),
    ("calcium hydroxide", "calcium"), ("magnesium oxide", "magnesium"), ("zinc oxide", "zinc"),
    ("copper(II) oxide", "copper(II)"), ("sodium carbonate", "sodium"),
    ("calcium carbonate", "calcium"), ("magnesium carbonate", "magnesium"),
]


@template(code="name_the_salt", subject=CHEMISTRY, topic="Chemical Changes", lessons=["4.4"])
def name_the_salt(rng):
    acid, anion = rng.choice(ACIDS)
    base, metal = rng.choice(BASES)
    return make_question(
        f"Name the salt formed when {acid} reacts with {base}.", f"{metal} {anion}", difficulty=2,
        explanation=f"The first part of the name comes from the metal in the base ({metal}) and the "
                    f"second part from the acid ({acid} gives {anion}s).",
    )
