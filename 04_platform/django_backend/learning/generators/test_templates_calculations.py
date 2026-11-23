"""
Independent checks for the physics equation and chemistry calculation templates.

Each question carries `meta` with the full set of values. These tests restate every physics
relationship and every chemistry rule here (with their own relative atomic masses), check the
values satisfy it, and check the question shows the given values and expects the hidden one.
"""
import random
import re
from decimal import ROUND_HALF_UP, Decimal
from fractions import Fraction as Fr

import pytest

from learning.generators import engine
from learning.generators.templates_science import parse_formula

TEMPLATES = {t.code: t for t in engine.load_all_templates()}
SEEDS = range(200)
G = Fr("9.8")


def draw(code):
    for seed in SEEDS:
        q = TEMPLATES[code].build(random.Random(seed))
        if q:
            yield q


def vals(q):
    return {k: Fr(v) for k, v in q["meta"]["values"].items()}


PHYSICS_RULES = {
    "kinetic_energy": lambda v: v["ke"] == v["m"] * v["v"] ** 2 / 2,
    "gravitational_potential_energy": lambda v: v["gpe"] == v["m"] * G * v["h"],
    "weight": lambda v: v["w"] == v["m"] * G,
    "specific_heat_capacity": lambda v: v["e"] == v["m"] * v["c"] * v["dt"],
    "work_done": lambda v: v["w"] == v["f"] * v["s"],
    "power_energy_time": lambda v: v["p"] * v["t"] == v["e"],
    "ohms_law": lambda v: v["v"] == v["i"] * v["r"],
    "charge_current_time": lambda v: v["q"] == v["i"] * v["t"],
    "electrical_power_iv": lambda v: v["p"] == v["i"] * v["v"],
    "electrical_power_i2r": lambda v: v["p"] == v["i"] ** 2 * v["r"],
    "energy_charge_pd": lambda v: v["e"] == v["q"] * v["v"],
    "energy_power_time_electric": lambda v: v["e"] == v["p"] * v["t"],
    "density": lambda v: v["rho"] * v["v"] == v["m"],
    "specific_latent_heat": lambda v: v["e"] == v["m"] * v["l"],
    "hookes_law": lambda v: v["f"] == v["k"] * v["e"],
    "elastic_potential_energy": lambda v: v["ee"] == v["k"] * v["e"] ** 2 / 2,
    "moment": lambda v: v["m"] == v["f"] * v["d"],
    "pressure_force_area": lambda v: v["p"] * v["a"] == v["f"],
    "speed_distance_time": lambda v: v["s"] == v["v"] * v["t"],
    "newtons_second_law": lambda v: v["f"] == v["m"] * v["a"],
    "momentum": lambda v: v["p"] == v["m"] * v["v"],
    "wave_speed": lambda v: v["v"] == v["f"] * v["lam"],
    "efficiency": lambda v: v["useful"] == v["total"] * v["eff"] and 0 < v["eff"] < 1,
    "pressure_volume": lambda v: v["p1"] * v["v1"] == v["p2"] * v["v2"],
    "principle_of_moments": lambda v: v["f1"] * v["d1"] == v["f2"] * v["d2"],
    "acceleration": lambda v: v["v"] == v["u"] + v["a"] * v["t"],
    "suvat_v2_u2_2as": lambda v: v["v"] ** 2 - v["u"] ** 2 == 2 * v["a"] * v["s"],
    "conservation_of_momentum": lambda v: v["m1"] * v["u1"] == (v["m1"] + v["m2"]) * v["v"],
    "transformer_turns": lambda v: v["vp"] * v["ns"] == v["vs"] * v["np"],
    "half_life": lambda v: v["a"] * 2 ** int(v["n"]) == v["a0"],
}


@pytest.mark.parametrize("code", sorted(PHYSICS_RULES))
def test_physics_values_obey_the_equation_and_the_answer_is_the_hidden_value(code):
    hidden_seen = set()
    for q in draw(code):
        v = vals(q)
        assert PHYSICS_RULES[code](v), (code, v)
        hidden = q["meta"]["hidden"]
        hidden_seen.add(hidden)
        expected = v["eff"] * 100 if hidden == "eff" else v[hidden]
        assert Fr(q["correct_answer"].rstrip("%")) == expected, q
        for key, value in v.items():
            if key not in (hidden, "n", "eff", "useful", "total", "u") and key in q["meta"]["values"]:
                shown = engine.tdec(value)
                if code not in ("half_life",):
                    assert shown in q["question_text"], (code, key, shown, q["question_text"])
    assert len(hidden_seen) >= 1


def test_every_physics_template_is_covered_by_a_rule():
    physics_calc = {c for c, t in TEMPLATES.items() if t.subject == "physics"
                    and "templates_physics_equations" in t.build.__module__}
    assert physics_calc == set(PHYSICS_RULES)


def test_physics_asks_for_different_unknowns():
    for code in ("kinetic_energy", "ohms_law", "specific_heat_capacity", "suvat_v2_u2_2as"):
        assert len({q["meta"]["hidden"] for q in draw(code)}) >= 3, code


# ---------------------------------------------------------------------------
# Chemistry
# ---------------------------------------------------------------------------
AR = {"H": 1, "Li": 7, "C": 12, "N": 14, "O": 16, "Na": 23, "Mg": 24, "Al": 27, "S": 32,
      "Cl": Fr("35.5"), "K": 39, "Ca": 40, "Fe": 56, "Cu": Fr("63.5"), "Zn": 65}


def mr(formula):
    return sum(Fr(AR[el]) * n for el, n in parse_formula(formula).items())


def test_relative_formula_mass():
    for q in draw("relative_formula_mass"):
        formula = q["meta"]["formula"]
        assert Fr(q["correct_answer"]) == mr(formula)
        for el in parse_formula(formula):
            assert f"{el} = " in q["question_text"]


def test_moles_and_mass():
    for q in draw("moles_and_mass"):
        m = q["meta"]
        assert Fr(m["mass"]) == Fr(m["n"]) * mr(m["formula"])
        assert Fr(q["correct_answer"]) == Fr(m[m["hidden"]])


def test_reacting_masses():
    for q in draw("reacting_masses"):
        m = q["meta"]
        species, coeffs = m["left"] + m["right"], m["coeffs"]
        left_atoms, right_atoms = {}, {}
        for idx, s in enumerate(species):
            target = left_atoms if idx < len(m["left"]) else right_atoms
            for el, n in parse_formula(s).items():
                target[el] = target.get(el, 0) + n * coeffs[idx]
        assert left_atoms == right_atoms, species
        i, j = m["i"], m["j"]
        n_i, n_j = Fr(m["mass_i"]) / mr(species[i]), Fr(m["mass_j"]) / mr(species[j])
        assert n_j / n_i == Fr(coeffs[j], coeffs[i])
        assert Fr(q["correct_answer"]) == Fr(m["mass_j"])


def test_conservation_of_mass():
    for q in draw("conservation_of_mass"):
        carbonate, oxide = re.search(r"g of (\w+) is heated.* g of (\w+) and", q["question_text"]).groups()
        m_carb, m_ox = Fr(q["meta"]["m_carb"]), Fr(q["meta"]["m_ox"])
        assert m_carb / mr(carbonate) == m_ox / mr(oxide)  # one mole of oxide per mole of carbonate
        assert Fr(q["correct_answer"]) == m_carb - m_ox == m_carb / mr(carbonate) * mr("CO2")


def test_limiting_reactant():
    for q in draw("limiting_reactant"):
        a, b = q["meta"]["left"]
        ca, cb = q["meta"]["coeffs"][:2]
        n_a, n_b = Fr(q["meta"]["m_a"]) / mr(a), Fr(q["meta"]["m_b"]) / mr(b)
        expected = a if n_a / ca < n_b / cb else b
        assert n_a / ca != n_b / cb
        assert q["correct_answer"] == expected


def test_concentration_gas_and_yield():
    for q in draw("concentration_g_dm3"):
        m = q["meta"]
        assert Fr(m["c"]) * Fr(m["v_cm3"]) / 1000 == Fr(m["mass"])
        assert Fr(q["correct_answer"]) == Fr(m[m["hidden"]])
    for q in draw("gas_volume"):
        m = q["meta"]
        assert Fr(m["vol"]) == Fr(m["n"]) * 24 and Fr(m["mass"]) == Fr(m["n"]) * mr(m["gas"])
        assert Fr(q["correct_answer"]) == Fr(m[m["hidden"]])
    for q in draw("percentage_yield"):
        m = q["meta"]
        assert Fr(m["actual"]) == Fr(m["theoretical"]) * Fr(m["pct"]) / 100
        assert Fr(q["correct_answer"].rstrip("%")) == Fr(m[m["hidden"]])


def test_atom_economy():
    for q in draw("atom_economy"):
        m = q["meta"]
        total = sum(mr(f_) * c for f_, c in m["reactants"])
        value = Decimal(str(float(mr(m["product"]) * m["k"] / total * 100)))
        assert Decimal(q["correct_answer"]) == value.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
        assert 0 < Decimal(q["correct_answer"]) <= 100
