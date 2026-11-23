"""
Tests for the question template engine. The important ones recompute each
answer independently from the numbers in the question text, so a template
cannot quietly ship a wrong answer.
"""
import math
import random
import re
from decimal import ROUND_HALF_UP, Decimal
from fractions import Fraction

import pytest
from django.core.management import call_command

from learning.generators import engine
from learning.generators.templates_science import (
    ANIONS, CATIONS, REACTIONS, ionic_formula, parse_formula,
)
from learning.models import Lesson, MultipleChoiceOption, Question, Subject, Topic
from learning.services.answer_grading import answers_equivalent

TEMPLATES = engine.load_all_templates()
BY_CODE = {t.code: t for t in TEMPLATES}
SEEDS = range(150)


def draw(code, seeds=SEEDS):
    """Yield every valid question a template produces over many seeds."""
    for seed in seeds:
        q = BY_CODE[code].build(random.Random(seed))
        if q:
            yield q


def numbers(text):
    return [Decimal(n) for n in re.findall(r"\d+(?:\.\d+)?", text)]


def sci_value(s):
    m = re.fullmatch(r"([\d.]+) × 10\^(-?\d+)", s.strip())
    assert m, f"not standard form: {s!r}"
    mantissa = Decimal(m.group(1))
    assert 1 <= mantissa < 10, f"mantissa out of range: {s!r}"
    return mantissa.scaleb(int(m.group(2)))


# ---------------------------------------------------------------------------
# Every template
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("template", TEMPLATES, ids=lambda t: t.code)
def test_template_produces_well_formed_questions(template):
    produced = 0
    for seed in SEEDS:
        q = template.build(random.Random(seed))
        if q is None:
            continue
        produced += 1
        assert q["question_text"] and q["correct_answer"]
        for field in ("question_text", "correct_answer", "explanation"):
            assert not re.search(r"None|nan|Decimal\(|Fraction\(", q[field]), (field, q[field])
        assert 1 <= q["difficulty_level"] <= 5
        if q["question_type"] == "multiple_choice":
            opts = q["options"]
            assert len(opts) == 4 and len({o["text"] for o in opts}) == 4
            correct = [o["text"] for o in opts if o["correct"]]
            assert correct == [q["correct_answer"]]
    assert produced >= 20, f"{template.code} rarely produces a question"


@pytest.mark.parametrize("template", TEMPLATES, ids=lambda t: t.code)
def test_answer_matches_itself_in_the_grader(template):
    for q in draw(template.code, range(40)):
        if q["question_type"] == "short_answer":
            ok, _ = answers_equivalent(q["correct_answer"], q["correct_answer"])
            assert ok, q


def test_template_codes_are_unique():
    assert len({t.code for t in TEMPLATES}) == len(TEMPLATES)


# ---------------------------------------------------------------------------
# Lesson matching
# ---------------------------------------------------------------------------
def test_lesson_number_and_matching_do_not_confuse_1_1_with_1_10():
    assert engine.lesson_number("1.10 - Adding & Subtracting Fractions") == "1.10"
    assert engine.lesson_number("4.4 - Scaling Up Ratios") == "4.4"
    assert engine.lesson_number("Revision") is None
    adding = engine.templates_for("Mathematics", "number", "1.10 - Adding & Subtracting Fractions")
    assert {t.code for t in adding} == {"add_fractions", "subtract_fractions"}
    assert engine.templates_for("mathematics", "Number", "1.1 - Something else") == []


def test_near_duplicate_topic_names_both_match():
    for topic in ("Number", "Numbers"):
        assert engine.templates_for("mathematics", topic, "1.4 - Highest Common Factor (HCF)")
    for topic in ("Ratio, Proportion & Rates of Change", "Ratio, Proportion & Rates of Changes"):
        assert engine.templates_for("mathematics", topic, "4.6 - Proportional Division")


def test_chemistry_and_physics_atomic_structure_do_not_share_templates():
    chem = {t.code for t in engine.templates_for("chemistry", "Atomic Structure", "1.4 - Balancing")}
    phys = {t.code for t in engine.templates_for("physics", "Atomic Structure", "4.2 - Atoms")}
    assert chem and phys and not chem & phys


# ---------------------------------------------------------------------------
# Independent answer checks: maths, Number
# ---------------------------------------------------------------------------
def test_hcf_templates():
    for code in ("hcf_two_numbers", "hcf_tiles"):
        for q in draw(code):
            x, y = [int(n) for n in numbers(q["question_text"])[:2]]
            assert int(q["correct_answer"]) == math.gcd(x, y)


def test_prime_templates():
    for q in draw("which_is_prime"):
        flags = {o["text"]: engine.is_prime(int(o["text"])) for o in q["options"]}
        assert [t for t, p in flags.items() if p] == [q["correct_answer"]]
    for q in draw("list_primes_between"):
        a, b = [int(n) for n in numbers(q["question_text"])[:2]]
        assert q["correct_answer"] == ", ".join(str(n) for n in range(a + 1, b) if engine.is_prime(n))


def test_prime_factor_product_multiplies_back():
    for q in draw("prime_factor_product"):
        n = int(numbers(q["question_text"])[0])
        total = 1
        for term in q["correct_answer"].split(" × "):
            base, _, power = term.partition("^")
            assert engine.is_prime(int(base))
            total *= int(base) ** int(power or 1)
        assert total == n


def test_fraction_templates():
    for q in draw("simplify_fraction"):
        a, b = [int(n) for n in re.search(r"(\d+)/(\d+)", q["question_text"]).groups()]
        assert Fraction(q["correct_answer"]) == Fraction(a, b)
        n, d = [int(n) for n in q["correct_answer"].split("/")]
        assert math.gcd(n, d) == 1

    for q in draw("improper_to_mixed"):
        n, d = [int(x) for x in re.search(r"(\d+)/(\d+)", q["question_text"]).groups()]
        w, r, d2 = [int(x) for x in re.fullmatch(r"(\d+) (\d+)/(\d+)", q["correct_answer"]).groups()]
        assert d2 == d and w + Fraction(r, d) == Fraction(n, d)

    for q in draw("mixed_to_improper"):
        w, r, d = [int(x) for x in re.search(r"(\d+) (\d+)/(\d+)", q["question_text"]).groups()]
        assert Fraction(q["correct_answer"]) == w + Fraction(r, d)

    ops = {"multiply_fractions": lambda a, b: a * b, "divide_fractions": lambda a, b: a / b,
           "add_fractions": lambda a, b: a + b, "subtract_fractions": lambda a, b: a - b}
    for code, op in ops.items():
        for q in draw(code):
            m = re.search(r"(\d+)/(\d+) [×÷+−] (\d+)/(\d+)", q["question_text"])
            a, b, c, d = [int(x) for x in m.groups()]
            expected = op(Fraction(a, b), Fraction(c, d))
            assert expected > 0
            ans = q["correct_answer"]
            parsed = (Fraction(int(ans.split()[0])) + Fraction(ans.split()[1])
                      if " " in ans else Fraction(ans))
            assert parsed == expected, q


def test_multiply_mixed_numbers():
    for q in draw("multiply_mixed_numbers"):
        w1, n1, d1, w2, n2, d2 = [int(x) for x in re.search(
            r"(\d+) (\d+)/(\d+) × (\d+) (\d+)/(\d+)", q["question_text"]).groups()]
        expected = (w1 + Fraction(n1, d1)) * (w2 + Fraction(n2, d2))
        ans = q["correct_answer"]
        parsed = (Fraction(int(ans.split()[0])) + Fraction(ans.split()[1])
                  if " " in ans else Fraction(ans))
        assert parsed == expected


def test_real_life_fraction_and_unitary_templates():
    for q in draw("fraction_of_quantity"):
        total, n, d = [int(x) for x in re.search(r"There are (\d+) .*?(\d+)/(\d+) of", q["question_text"]).groups()]
        assert Fraction(q["correct_answer"]) == Fraction(total * n, d)
    for q in draw("unitary_cost"):
        k, cost, m = re.search(r"^(\d+) \w+ cost £([\d.]+)\. How much do (\d+)", q["question_text"]).groups()
        assert Decimal(q["correct_answer"][1:]) == Decimal(cost) / int(k) * int(m)


def test_decimal_conversion_templates():
    for q in draw("fraction_to_decimal"):
        n, d = [int(x) for x in re.search(r"(\d+)/(\d+)", q["question_text"]).groups()]
        assert Decimal(q["correct_answer"]) == Decimal(n) / Decimal(d)
    for q in draw("fraction_to_decimal_3dp"):
        n, d = [int(x) for x in re.search(r"(\d+)/(\d+)", q["question_text"]).groups()]
        expected = (Decimal(n) / Decimal(d)).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
        assert Decimal(q["correct_answer"]) == expected
    for q in draw("which_recurring"):
        flags = {}
        for o in q["options"]:
            n, d = [int(x) for x in o["text"].split("/")]
            reduced = Fraction(n, d).denominator
            while reduced % 2 == 0:
                reduced //= 2
            while reduced % 5 == 0:
                reduced //= 5
            flags[o["text"]] = reduced != 1
        assert [t for t, rec in flags.items() if rec] == [q["correct_answer"]]
    for q in draw("decimal_to_percentage"):
        assert Decimal(q["correct_answer"][:-1]) == Decimal(numbers(q["question_text"])[0]) * 100
    for q in draw("decimal_to_fraction"):
        d = Decimal(re.search(r"Write ([\d.]+) as", q["question_text"]).group(1))
        assert Fraction(q["correct_answer"]) == Fraction(d)
    for q in draw("recurring_to_fraction"):
        shown = re.search(r"digits (\d+) repeating", q["question_text"]).group(1)
        expected = Fraction(int(shown), 10 ** len(shown) - 1)
        assert Fraction(q["correct_answer"]) == expected


def test_rounding_templates():
    for q in draw("round_decimal_places"):
        x, dp = re.search(r"Round ([\d.]+) to (\d) decimal", q["question_text"]).groups()
        expected = Decimal(x).quantize(Decimal(1).scaleb(-int(dp)), rounding=ROUND_HALF_UP)
        assert q["correct_answer"] == format(expected, "f")
    for q in draw("round_significant_figures"):
        x, sf = re.search(r"Round ([\d.]+) to (\d) significant", q["question_text"]).groups()
        value = Decimal(x)
        exp = value.adjusted() - int(sf) + 1
        expected = value.quantize(Decimal(1).scaleb(exp), rounding=ROUND_HALF_UP)
        assert Decimal(q["correct_answer"]) == expected


def test_estimate_templates():
    for q in draw("estimate_calculation"):
        a, b, c = [Decimal(x) for x in re.search(
            r"\(([\d.]+) × ([\d.]+)\) ÷ ([\d.]+)", q["question_text"]).groups()]
        r = [engine.round_sf(v, 1) for v in (a, b, c)]
        assert Decimal(q["correct_answer"]) == r[0] * r[1] / r[2]
    for q in draw("between_which_integers_sqrt"):
        n = int(re.search(r"√(\d+)", q["question_text"]).group(1))
        k = math.isqrt(n)
        assert q["correct_answer"] == f"{k} and {k + 1}" and k * k != n


def test_standard_form_templates():
    for q in draw("which_is_standard_form"):
        good = []
        for o in q["options"]:
            m = re.fullmatch(r"([\d.]+) × 10\^(\d+)", o["text"])
            if m and 1 <= Decimal(m.group(1)) < 10:
                good.append(o["text"])
        assert good == [q["correct_answer"]]
    for q in draw("to_standard_form"):
        assert sci_value(q["correct_answer"]) == Decimal(re.search(r"Write ([\d.]+) in", q["question_text"]).group(1))
    for q in draw("from_standard_form"):
        a, n = re.search(r"Write ([\d.]+) × 10\^(-?\d+)", q["question_text"]).groups()
        assert Decimal(q["correct_answer"]) == Decimal(a).scaleb(int(n))

    pattern = r"\(([\d.]+) × 10\^(-?\d+)\) ([×÷+−]) \(([\d.]+) × 10\^(-?\d+)\)"
    ops = {"×": lambda x, y: x * y, "÷": lambda x, y: x / y,
           "+": lambda x, y: x + y, "−": lambda x, y: x - y}
    for code in ("multiply_standard_form", "divide_standard_form",
                 "add_standard_form", "subtract_standard_form"):
        for q in draw(code):
            a, m, op, b, n = re.search(pattern, q["question_text"]).groups()
            expected = ops[op](Decimal(a).scaleb(int(m)), Decimal(b).scaleb(int(n)))
            assert expected > 0
            assert sci_value(q["correct_answer"]) == expected, q


# ---------------------------------------------------------------------------
# Independent answer checks: maths, Ratio
# ---------------------------------------------------------------------------
def test_ratio_templates():
    for q in draw("scale_up_ratio"):
        a, b, count = [int(x) for x in re.search(r"is (\d+):(\d+)\. There are (\d+)", q["question_text"]).groups()]
        assert Fraction(int(q["correct_answer"]), count) == Fraction(a, b)
    for q in draw("ratio_one_to_n"):
        a, b = [int(x) for x in re.search(r"ratio (\d+):(\d+) in", q["question_text"]).groups()]
        assert Decimal(q["correct_answer"].split(":")[1]) == Decimal(b) / Decimal(a)
    for q in draw("ratio_to_fraction"):
        a, b = [int(x) for x in re.search(r"is (\d+):(\d+)\.", q["question_text"]).groups()]
        assert Fraction(q["correct_answer"]) == Fraction(a, a + b)
    for q in draw("share_in_ratio"):
        total, a, b = [int(x) for x in re.search(r"share £(\d+) in the ratio (\d+):(\d+)", q["question_text"]).groups()]
        assert Decimal(q["correct_answer"][1:]) == Decimal(total * b) / (a + b)
    for q in draw("share_three_way"):
        total, a, b, c = [int(x) for x in re.search(r"£(\d+) is shared .* (\d+):(\d+):(\d+)", q["question_text"]).groups()]
        assert Decimal(q["correct_answer"][1:]) == Decimal(total * c) / (a + b + c)
    for q in draw("scale_recipe"):
        p, amount, q_people = [int(x) for x in re.search(r"for (\d+) people uses (\d+) .* for (\d+) people", q["question_text"]).groups()]
        assert Fraction(int(q["correct_answer"]), q_people) == Fraction(amount, p)


def test_best_buy_picks_the_cheaper_pack():
    for q in draw("best_buy"):
        n1, p1, n2, p2 = [Decimal(x) for x in re.search(
            r"contains (\d+) g .* costs £(\d+(?:\.\d+)?)\. Pack B contains (\d+) g and costs £(\d+(?:\.\d+)?)",
            q["question_text"]).groups()]
        assert q["correct_answer"] == ("Pack A" if p1 / n1 < p2 / n2 else "Pack B")


def test_proportion_templates():
    for q in draw("direct_proportion_value"):
        a, b, c = [Decimal(x) for x in re.search(r"x = ([\d.]+), y = ([\d.]+)\. Find y when x = ([\d.]+)", q["question_text"]).groups()]
        assert Decimal(q["correct_answer"]) == b / a * c
    for q in draw("direct_proportion_formula"):
        a, b = [Decimal(x) for x in re.search(r"x = (\d+(?:\.\d+)?), y = (\d+(?:\.\d+)?)", q["question_text"]).groups()]
        assert Decimal(re.fullmatch(r"y = ([\d.]+)x", q["correct_answer"]).group(1)) == b / a
    for q in draw("inverse_proportion_value"):
        a, b, c = [Decimal(x) for x in re.search(r"x = ([\d.]+), y = ([\d.]+)\. Find y when x = ([\d.]+)", q["question_text"]).groups()]
        assert Decimal(q["correct_answer"]) == a * b / c
    for q in draw("inverse_proportion_meaning"):
        assert re.fullmatch(r"y = \d+/x", q["correct_answer"])


def test_percentage_templates():
    for q in draw("percentage_of_amount"):
        p, n = [Decimal(x) for x in re.search(r"Find ([\d.]+)% of £(\d+)", q["question_text"]).groups()]
        assert Decimal(q["correct_answer"][1:]) == p * n / 100
    for q in draw("percentage_multiplier"):
        p = Decimal(re.search(r"by (\d+)%", q["question_text"]).group(1))
        up = "increase" in q["question_text"]
        assert Decimal(q["correct_answer"]) == (100 + p if up else 100 - p) / 100
    for q in draw("percentage_increase_amount"):
        n, verb, p = re.search(r"£(\d+) is (increased|decreased) by (\d+)%", q["question_text"]).groups()
        factor = 100 + int(p) if verb == "increased" else 100 - int(p)
        assert Decimal(q["correct_answer"][1:]) == Decimal(n) * factor / 100
    for q in draw("express_as_percentage"):
        a, b = [Decimal(x) for x in re.search(r"scored (\d+) out of (\d+)", q["question_text"]).groups()]
        assert Decimal(q["correct_answer"][:-1]) == a / b * 100
    for q in draw("percentage_change"):
        old, new = [Decimal(x) for x in re.search(r"from £(\d+) to £(\d+)", q["question_text"]).groups()]
        assert Decimal(q["correct_answer"][:-1]) == abs(new - old) / old * 100
        assert ("increase" in q["question_text"]) == (new > old)


def test_reverse_percentage_templates():
    for q in draw("reverse_percentage_sale"):
        x, sale = re.search(r"reduced by (\d+)%\. A coat costs £([\d.]+)", q["question_text"]).groups()
        assert Decimal(q["correct_answer"][1:]) * (100 - int(x)) / 100 == Decimal(sale)
    for q in draw("reverse_percentage_vat"):
        total = Decimal(re.search(r"costs £([\d.]+) including", q["question_text"]).group(1))
        assert Decimal(q["correct_answer"][1:]) * Decimal("1.2") == total


def test_simple_interest_templates():
    for q in draw("simple_interest_amount"):
        p, years, rate = re.search(r"invests £(\d+) for (\d+) years at ([\d.]+)%", q["question_text"]).groups()
        assert Decimal(q["correct_answer"][1:]) == Decimal(p) * Decimal(rate) * int(years) / 100
    for q in draw("simple_interest_total"):
        p, rate, years = re.search(r"£(\d+) is put .* paying ([\d.]+)% .* after (\d+) years", q["question_text"]).groups()
        assert Decimal(q["correct_answer"][1:]) == Decimal(p) * (1 + Decimal(rate) * int(years) / 100)


# ---------------------------------------------------------------------------
# Science
# ---------------------------------------------------------------------------
def test_formula_parser():
    assert parse_formula("H2O") == {"H": 2, "O": 1}
    assert parse_formula("Ca(OH)2") == {"Ca": 1, "O": 2, "H": 2}
    assert parse_formula("Al2(SO4)3") == {"Al": 2, "S": 3, "O": 12}
    assert parse_formula("(NH4)2SO4") == {"N": 2, "H": 8, "S": 1, "O": 4}
    assert parse_formula("C6H12O6") == {"C": 6, "H": 12, "O": 6}


@pytest.mark.parametrize("left,right,coeffs", REACTIONS, ids=lambda v: str(v))
def test_every_reaction_is_really_balanced(left, right, coeffs):
    def totals(species, cs):
        out = {}
        for s, c in zip(species, cs):
            for el, n in parse_formula(s).items():
                out[el] = out.get(el, 0) + n * c
        return out

    assert totals(left, coeffs[:len(left)]) == totals(right, coeffs[len(left):])
    assert math.gcd(*coeffs) == 1, "coefficients should be in lowest terms"


def test_atom_counting_templates():
    for q in draw("count_total_atoms"):
        formula = re.search(r"one unit of (\S+)\?", q["question_text"]).group(1)
        assert int(q["correct_answer"]) == sum(parse_formula(formula).values())


def test_ionic_formulae():
    cat = {c[0]: c for c in CATIONS}
    an = {a[0]: a for a in ANIONS}
    known = {
        ("magnesium", "hydroxide"): "Mg(OH)2", ("aluminium", "sulfate"): "Al2(SO4)3",
        ("ammonium", "sulfate"): "(NH4)2SO4", ("calcium", "oxide"): "CaO",
        ("sodium", "carbonate"): "Na2CO3", ("aluminium", "oxide"): "Al2O3",
        ("calcium", "nitrate"): "Ca(NO3)2", ("sodium", "chloride"): "NaCl",
        ("zinc", "sulfide"): "ZnS", ("aluminium", "chloride"): "AlCl3",
    }
    for (c, a), formula in known.items():
        assert ionic_formula(cat[c], an[a]) == formula
    for c in CATIONS:
        for a in ANIONS:
            f = ionic_formula(c, a)
            parse_formula(f)  # well-formed
            assert "1" not in f, f"{f}: a count of 1 should not be written"
            assert not re.search(r"\)(?!\d)", f), f"{f}: brackets only appear with a count"


def test_atomic_structure_templates():
    for q in draw("neutrons_in_atom"):
        name, a, z = re.search(r"atom of (\w+)-(\d+) has an atomic number of (\d+)", q["question_text"]).groups()
        assert int(q["correct_answer"]) == int(a) - int(z)
    for q in draw("electrons_in_ion"):
        sign = "+" if "+" in q["question_text"] else "-"
        charge, z = re.search(r"charge of (\d)[+-]\. .* has (\d+) protons", q["question_text"]).groups()
        assert int(q["correct_answer"]) == int(z) - (int(charge) if sign == "+" else -int(charge))
    for q in draw("alpha_decay_numbers"):
        a, z = re.search(r"-(\d+) \(atomic number (\d+)\)", q["question_text"]).groups()
        want = int(a) - 4 if "mass number of" in q["question_text"] else int(z) - 2
        assert int(q["correct_answer"]) == want
    for q in draw("beta_decay_numbers"):
        a, z = re.search(r"-(\d+) \(atomic number (\d+)\)", q["question_text"]).groups()
        want = int(a) if "mass number of" in q["question_text"] else int(z) + 1
        assert int(q["correct_answer"]) == want


def test_identify_radiation_matches_the_numbers():
    for q in draw("identify_radiation"):
        a, z, a2, z2 = [int(x) for x in re.search(
            r"mass number (\d+) and atomic number (\d+) decays into a nucleus with mass number (\d+) and atomic number (\d+)",
            q["question_text"]).groups()]
        if (a2, z2) == (a - 4, z - 2):
            assert q["correct_answer"] == "Alpha"
        elif (a2, z2) == (a, z + 1):
            assert q["correct_answer"] == "Beta (minus)"
        else:
            assert (a2, z2) == (a, z) and q["correct_answer"] == "Gamma"


# ---------------------------------------------------------------------------
# Generating into the database
# ---------------------------------------------------------------------------
@pytest.fixture
def maths_lessons(db):
    subject = Subject.objects.create(name="mathematics", display_name="GCSE Maths")
    number = Topic.objects.create(subject=subject, name="Number", order=1)
    ratio = Topic.objects.create(subject=subject, name="Ratio, Proportion & Rates of Change", order=4)
    return {
        "prime": Lesson.objects.create(topic=number, title="1.5 - Prime & Composite Numbers", content="x", order=5),
        "add": Lesson.objects.create(topic=number, title="1.10 - Adding & Subtracting Fractions", content="x", order=10),
        "other": Lesson.objects.create(topic=number, title="1.1 - Place Value", content="x", order=1),
        "ratio": Lesson.objects.create(topic=ratio, title="4.6 - Proportional Division", content="x", order=6),
    }


def test_command_adds_questions_only_to_lessons_with_templates(maths_lessons):
    call_command("generate_templated_questions", "--subject", "mathematics", "--per-lesson", "6", "--seed", "1")
    assert Question.objects.filter(lesson=maths_lessons["other"]).count() == 0
    for key in ("prime", "add", "ratio"):
        qs = Question.objects.filter(lesson=maths_lessons[key])
        assert 1 <= qs.count() <= 6
        assert all(q.source.startswith(engine.SOURCE_PREFIX) and q.explanation for q in qs)


def test_command_saves_multiple_choice_options(maths_lessons):
    call_command("generate_templated_questions", "--per-lesson", "10", "--seed", "3")
    mcqs = Question.objects.filter(lesson=maths_lessons["prime"], question_type="multiple_choice")
    assert mcqs.exists()
    for q in mcqs:
        opts = list(MultipleChoiceOption.objects.filter(question=q))
        assert len(opts) == 4 and sum(o.is_correct for o in opts) == 1


def test_running_again_adds_new_questions_not_copies(maths_lessons):
    call_command("generate_templated_questions", "--per-lesson", "8", "--seed", "1")
    call_command("generate_templated_questions", "--per-lesson", "8", "--seed", "2")
    pairs = list(Question.objects.filter(lesson=maths_lessons["ratio"]).values_list("question_text", "correct_answer"))
    assert len(pairs) == len(set(pairs)) > 8


def test_dry_run_and_fill_below(maths_lessons):
    call_command("generate_templated_questions", "--dry-run", "--per-lesson", "5")
    assert Question.objects.count() == 0
    for i in range(3):
        Question.objects.create(lesson=maths_lessons["prime"], question_text=f"q{i}", correct_answer="1")
    call_command("generate_templated_questions", "--fill-below", "3", "--per-lesson", "4", "--seed", "1")
    assert Question.objects.filter(lesson=maths_lessons["prime"]).count() == 3
    assert Question.objects.filter(lesson=maths_lessons["add"]).count() > 0
