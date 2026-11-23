"""
Maths question templates for the Number (1.x) and Ratio, Proportion & Rates
of Change (4.x) topics. See engine.py for how templates work.
All wording is original.
"""
import math
from decimal import Decimal
from fractions import Fraction

from learning.generators.engine import (
    frac_str, is_prime, is_terminating, make_question, mcq, mixed_str, money,
    prime_factors, round_dp, round_sf, sci_str, tdec, template, fmt_dec,
)

SUBJECT = "mathematics"
NUMBER = "Number"
RATIO = "Ratio, Proportion & Rates of Change"


def _coprime_pair(rng, lo, hi):
    a, b = rng.randint(lo, hi), rng.randint(lo, hi)
    return (a, b) if math.gcd(a, b) == 1 else None


def _terminating_places(q: Fraction, max_places: int) -> bool:
    return is_terminating(q) and (q * 10**max_places).denominator == 1


# =========================================================================
# NUMBER
# =========================================================================
@template(code="hcf_two_numbers", subject=SUBJECT, topic=NUMBER, lessons=["1.4"])
def hcf_two_numbers(rng):
    g = rng.choice([2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15])
    pair = _coprime_pair(rng, 2, 12)
    if not pair or pair[0] == pair[1]:
        return None
    x, y = g * pair[0], g * pair[1]
    return make_question(
        f"Find the highest common factor (HCF) of {x} and {y}.", str(g),
        explanation=f"List the factors of {x} and {y} (or use prime factors). "
                    f"The largest number that divides into both is {g}.",
    )


@template(code="hcf_tiles", subject=SUBJECT, topic=NUMBER, lessons=["1.4"])
def hcf_tiles(rng):
    g = rng.choice([5, 6, 8, 10, 12, 15, 20, 25])
    pair = _coprime_pair(rng, 3, 14)
    if not pair or pair[0] == pair[1]:
        return None
    x, y = g * pair[0], g * pair[1]
    return make_question(
        f"A floor is {x} cm long and {y} cm wide. It is covered with identical square tiles "
        f"with no cutting. What is the largest possible side length of a tile, in cm?",
        str(g), difficulty=3,
        explanation=f"The side length must divide exactly into both {x} and {y}, so find their HCF, which is {g}.",
    )


@template(code="which_is_prime", subject=SUBJECT, topic=NUMBER, lessons=["1.5"])
def which_is_prime(rng):
    prime = rng.choice([n for n in range(11, 98) if is_prime(n)])
    composites = rng.sample([n for n in range(21, 100, 2) if not is_prime(n)], 3)
    return mcq(
        rng, "Which one of these numbers is a prime number?", str(prime),
        [str(c) for c in composites], difficulty=2,
        explanation=f"{prime} has exactly two factors, 1 and itself. "
                    f"Each of the other numbers has another factor.",
    )


@template(code="list_primes_between", subject=SUBJECT, topic=NUMBER, lessons=["1.5"])
def list_primes_between(rng):
    a = rng.randint(2, 80)
    b = a + rng.randint(8, 16)
    primes = [n for n in range(a + 1, b) if is_prime(n)]
    if not 1 <= len(primes) <= 4:
        return None
    return make_question(
        f"List all the prime numbers between {a} and {b}.", ", ".join(map(str, primes)),
        difficulty=3,
        explanation="Check each number: a prime has no factors other than 1 and itself.",
    )


@template(code="prime_factor_product", subject=SUBJECT, topic=NUMBER, lessons=["1.6"])
def prime_factor_product(rng):
    n = 1
    for _ in range(rng.randint(2, 4)):
        n *= rng.choice([2, 2, 3, 3, 5, 7, 11])
    if is_prime(n) or n > 500:
        return None
    parts = [f"{p}^{e}" if e > 1 else str(p) for p, e in sorted(prime_factors(n).items())]
    return make_question(
        f"Write {n} as a product of its prime factors. Give your answer in index form.",
        " × ".join(parts), difficulty=3,
        explanation="Keep dividing by the smallest prime that goes in, "
                    "then write the repeated primes using powers.",
    )


@template(code="simplify_fraction", subject=SUBJECT, topic=NUMBER, lessons=["1.7"])
def simplify_fraction(rng):
    b = rng.randint(2, 12)
    a = rng.choice([n for n in range(1, b) if math.gcd(n, b) == 1])
    g = rng.randint(2, 9)
    return make_question(
        f"Simplify the fraction {g * a}/{g * b}.", f"{a}/{b}", difficulty=1,
        explanation=f"Divide the top and bottom by their HCF, {g}.",
    )


@template(code="improper_to_mixed", subject=SUBJECT, topic=NUMBER, lessons=["1.8"])
def improper_to_mixed(rng):
    d = rng.randint(2, 9)
    r = rng.randint(1, d - 1)
    if math.gcd(r, d) != 1:
        return None
    w = rng.randint(1, 9)
    n = w * d + r
    return make_question(
        f"Write {n}/{d} as a mixed number.", f"{w} {r}/{d}", difficulty=2,
        explanation=f"{d} goes into {n} {w} times with remainder {r}.",
    )


@template(code="mixed_to_improper", subject=SUBJECT, topic=NUMBER, lessons=["1.8"])
def mixed_to_improper(rng):
    d = rng.randint(2, 9)
    r = rng.randint(1, d - 1)
    if math.gcd(r, d) != 1:
        return None
    w = rng.randint(1, 9)
    return make_question(
        f"Write {w} {r}/{d} as an improper fraction.", f"{w * d + r}/{d}", difficulty=2,
        explanation=f"{w} × {d} + {r} = {w * d + r}, so the fraction is {w * d + r}/{d}.",
    )


def _small_fraction(rng, lo_den=2, hi_den=9):
    """A proper fraction already in its simplest form, as (value, numerator, denominator)."""
    d = rng.randint(lo_den, hi_den)
    n = rng.choice([k for k in range(1, d) if math.gcd(k, d) == 1])
    return Fraction(n, d), n, d


@template(code="multiply_fractions", subject=SUBJECT, topic=NUMBER, lessons=["1.9"])
def multiply_fractions(rng):
    f1, n1, d1 = _small_fraction(rng)
    f2, n2, d2 = _small_fraction(rng)
    ans = f1 * f2
    if ans.denominator == 1:
        return None
    return make_question(
        f"Work out {n1}/{d1} × {n2}/{d2}. Give your answer as a fraction in its simplest form.",
        frac_str(ans), difficulty=2,
        explanation=f"Multiply the tops ({n1 * n2}) and the bottoms ({d1 * d2}), then simplify.",
    )


@template(code="divide_fractions", subject=SUBJECT, topic=NUMBER, lessons=["1.9"])
def divide_fractions(rng):
    f1, n1, d1 = _small_fraction(rng)
    f2, n2, d2 = _small_fraction(rng)
    ans = f1 / f2
    if ans.denominator == 1 or f1 == f2:
        return None
    return make_question(
        f"Work out {n1}/{d1} ÷ {n2}/{d2}. Give your answer as a fraction in its simplest form.",
        frac_str(ans), difficulty=3,
        explanation=f"Flip the second fraction and multiply: {n1}/{d1} × {d2}/{n2}, then simplify.",
    )


@template(code="multiply_mixed_numbers", subject=SUBJECT, topic=NUMBER, lessons=["1.9"])
def multiply_mixed_numbers(rng):
    w1, w2 = rng.randint(1, 4), rng.randint(1, 4)
    f1, n1, d1 = _small_fraction(rng, 2, 6)
    f2, n2, d2 = _small_fraction(rng, 2, 6)
    a, b = w1 + f1, w2 + f2
    return make_question(
        f"Work out {w1} {n1}/{d1} × {w2} {n2}/{d2}. Give your answer as a mixed number "
        f"or a whole number in its simplest form.",
        mixed_str(a * b), difficulty=4,
        explanation="Change both to improper fractions, multiply, then convert back to a mixed number.",
    )


@template(code="add_fractions", subject=SUBJECT, topic=NUMBER, lessons=["1.10"])
def add_fractions(rng):
    f1, n1, d1 = _small_fraction(rng)
    f2, n2, d2 = _small_fraction(rng)
    if d1 == d2:
        return None
    ans = f1 + f2
    return make_question(
        f"Work out {n1}/{d1} + {n2}/{d2}. Give your answer as a fraction or mixed number in its simplest form.",
        mixed_str(ans), difficulty=2,
        explanation=f"Write both fractions with a common denominator of {math.lcm(d1, d2)}, add the tops, then simplify.",
    )


@template(code="subtract_fractions", subject=SUBJECT, topic=NUMBER, lessons=["1.10"])
def subtract_fractions(rng):
    f1, n1, d1 = _small_fraction(rng)
    f2, n2, d2 = _small_fraction(rng)
    if d1 == d2 or f1 == f2:
        return None
    if f1 < f2:
        f1, n1, d1, f2, n2, d2 = f2, n2, d2, f1, n1, d1
    return make_question(
        f"Work out {n1}/{d1} − {n2}/{d2}. Give your answer in its simplest form.",
        frac_str(f1 - f2), difficulty=2,
        explanation=f"Use a common denominator of {math.lcm(d1, d2)}, subtract the tops, then simplify.",
    )


@template(code="fraction_of_quantity", subject=SUBJECT, topic=NUMBER, lessons=["1.11"])
def fraction_of_quantity(rng):
    f, n, d = _small_fraction(rng, 3, 10)
    total = d * rng.randint(3, 12)
    group = rng.choice([("students in a class", "walk to school"),
                        ("passengers on a bus", "are children"),
                        ("members of a club", "play football"),
                        ("customers in a shop", "pay by card")])
    return make_question(
        f"There are {total} {group[0]}. {n}/{d} of them {group[1]}. How many is this?",
        str(int(f * total)), difficulty=2,
        explanation=f"Divide {total} by {d} to find one part, then multiply by {n}.",
    )


@template(code="fraction_remaining", subject=SUBJECT, topic=NUMBER, lessons=["1.11"])
def fraction_remaining(rng):
    f, n, d = _small_fraction(rng, 3, 10)
    amount = d * rng.choice([2, 3, 4, 5, 6, 8, 10, 12, 15])
    return make_question(
        f"Jo has £{amount}. She spends {n}/{d} of it. How much money does she have left?",
        money(amount * (1 - f)), difficulty=3,
        explanation=f"She spends £{money(amount * f)[1:]}, so she has £{amount} minus that left.",
    )


_ITEMS = [("notebooks", 45), ("pencils", 15), ("folders", 60), ("rulers", 80), ("stickers", 12)]


@template(code="unitary_cost", subject=SUBJECT, topic=NUMBER, lessons=["1.12"])
def unitary_cost(rng):
    name, base = rng.choice(_ITEMS)
    pence = base + 5 * rng.randint(0, 12)
    k, m = rng.randint(2, 9), rng.randint(2, 20)
    if k == m:
        return None
    unit = Fraction(pence, 100)
    return make_question(
        f"{k} {name} cost {money(unit * k)}. How much do {m} {name} cost?",
        money(unit * m), difficulty=2,
        explanation=f"Find the cost of 1 first: {money(unit * k)} ÷ {k} = {money(unit)}. Then multiply by {m}.",
    )


@template(code="fraction_to_decimal", subject=SUBJECT, topic=NUMBER, lessons=["1.13"])
def fraction_to_decimal(rng):
    d = rng.choice([2, 4, 5, 8, 10, 20, 25, 40, 50])
    pair = _coprime_pair(rng, 1, d - 1)
    if not pair or math.gcd(pair[0], d) != 1:
        return None
    n = pair[0]
    return make_question(
        f"Write {n}/{d} as a decimal.", tdec(Fraction(n, d)), difficulty=2,
        explanation=f"Divide the top by the bottom: {n} ÷ {d}.",
    )


@template(code="fraction_to_decimal_3dp", subject=SUBJECT, topic=NUMBER, lessons=["1.14"])
def fraction_to_decimal_3dp(rng):
    d = rng.choice([3, 6, 7, 9, 11, 12, 13])
    n = rng.randint(1, d - 1)
    if math.gcd(n, d) != 1:
        return None
    value = Decimal(n) / Decimal(d)
    return make_question(
        f"Write {n}/{d} as a decimal. Give your answer correct to 3 decimal places.",
        fmt_dec(round_dp(value, 3)), difficulty=3,
        explanation=f"{n} ÷ {d} gives a decimal that never ends, so round it to 3 decimal places.",
    )


@template(code="which_recurring", subject=SUBJECT, topic=NUMBER, lessons=["1.14"])
def which_recurring(rng):
    def pick(dens):
        d = rng.choice(dens)
        return rng.choice([n for n in range(1, d) if math.gcd(n, d) == 1]), d

    rec = pick([3, 6, 7, 9, 11, 12, 15])
    terms = [pick([2, 4, 5, 8, 10, 20, 25]) for _ in range(3)]
    texts = [f"{n}/{d}" for n, d in terms]
    if len(set(texts)) < 3:
        return None
    return mcq(
        rng, "Which one of these fractions is a recurring decimal?", f"{rec[0]}/{rec[1]}", texts,
        difficulty=3,
        explanation="A fraction in its simplest form is a terminating decimal only if its "
                    "denominator has no prime factors other than 2 and 5.",
    )


@template(code="decimal_to_percentage", subject=SUBJECT, topic=NUMBER, lessons=["1.15"])
def decimal_to_percentage(rng):
    k = 5 * rng.randint(1, 250)
    value = Fraction(k, 1000)
    return make_question(
        f"Write {tdec(value)} as a percentage.", f"{tdec(value * 100)}%", difficulty=1,
        explanation="Multiply the decimal by 100.",
    )


@template(code="decimal_to_fraction", subject=SUBJECT, topic=NUMBER, lessons=["1.16"])
def decimal_to_fraction(rng):
    k = rng.randint(1, 99) if rng.random() < 0.6 else rng.randint(1, 999)
    value = Fraction(k, 100 if k < 100 else 1000)
    if value.denominator == 1:
        return None
    return make_question(
        f"Write {tdec(value)} as a fraction in its simplest form.", frac_str(value), difficulty=2,
        explanation="Write the decimal over 10, 100 or 1000 using its decimal places, then simplify.",
    )


@template(code="recurring_to_fraction", subject=SUBJECT, topic=NUMBER, lessons=["1.17"])
def recurring_to_fraction(rng):
    if rng.random() < 0.5:
        d = rng.randint(1, 8)
        digits, den, shown = d, 9, str(d)
    else:
        digits = rng.randint(1, 98)
        den, shown = 99, f"{digits:02d}"
    f = Fraction(digits, den)
    return make_question(
        f"The recurring decimal 0.{shown * 4}... has the digits {shown} repeating forever. "
        f"Write it as a fraction in its simplest form.",
        frac_str(f), difficulty=4,
        explanation=f"Let x = 0.{shown * 3}... Multiply by {10 if den == 9 else 100} and subtract x "
                    f"to remove the repeating part, giving {digits}/{den}, then simplify.",
    )


@template(code="round_decimal_places", subject=SUBJECT, topic=NUMBER, lessons=["1.18"])
def round_decimal_places(rng):
    whole = rng.randint(0, 99)
    frac_digits = "".join(str(rng.randint(0, 9)) for _ in range(rng.randint(4, 5)))
    x = Decimal(f"{whole}.{frac_digits}")
    dp = rng.randint(1, 3)
    return make_question(
        f"Round {x} to {dp} decimal place{'s' if dp > 1 else ''}.", fmt_dec_keep(round_dp(x, dp)),
        difficulty=1,
        explanation=f"Look at the digit after the {dp}{'st' if dp == 1 else 'nd' if dp == 2 else 'rd'} "
                    f"decimal place. If it is 5 or more, round up.",
    )


def fmt_dec_keep(x: Decimal) -> str:
    """Plain decimal string that keeps trailing zeros (3.20 stays 3.20)."""
    return format(x, "f")


@template(code="round_significant_figures", subject=SUBJECT, topic=NUMBER, lessons=["1.19"])
def round_significant_figures(rng):
    digits = "".join(str(rng.randint(1, 9) if i == 0 else rng.randint(0, 9)) for i in range(rng.randint(4, 6)))
    shift = rng.choice([-4, -3, -2, -1, 0, 1, 2, 3])
    x = Decimal(digits).scaleb(shift)
    sf = rng.randint(1, 3)
    if sf >= len(digits) or x == round_sf(x, sf):
        return None
    return make_question(
        f"Round {format(x, 'f')} to {sf} significant figure{'s' if sf > 1 else ''}.",
        fmt_dec_keep(round_sf(x, sf)), difficulty=3,
        explanation=f"Count {sf} significant figure{'s' if sf > 1 else ''} from the first non-zero digit, "
                    f"then round using the next digit. Fill any gap before the decimal point with zeros.",
    )


@template(code="estimate_calculation", subject=SUBJECT, topic=NUMBER, lessons=["1.20"])
def estimate_calculation(rng):
    r1 = rng.choice([20, 30, 40, 50, 60, 70, 80, 90, 200, 300, 400, 500, 600, 700])
    r2 = rng.choice([2, 3, 4, 5, 6, 8])
    r3 = rng.choice([2, 4, 5, 10, 20])
    ans = Fraction(r1 * r2, r3)
    if not _terminating_places(ans, 1):
        return None
    step = 4 if r1 < 100 else 40
    a = r1 + rng.randint(-step, step)
    b = Decimal(r2) + Decimal(rng.randint(-4, 4)) / 10
    if r3 == 20:
        c = Decimal(r3 + rng.randint(-4, 4))
    else:
        c = Decimal(r3) + Decimal(rng.randint(-4, 4)) / 10
    rounds_correctly = (
        round_sf(Decimal(a), 1) == r1 and round_sf(b, 1) == r2 and round_sf(c, 1) == r3
    )
    if not rounds_correctly or (a == r1 and b == r2 and c == r3):
        return None
    return make_question(
        f"Estimate the value of ({a} × {fmt_dec(b)}) ÷ {fmt_dec(c)} by rounding each number to "
        f"1 significant figure.",
        tdec(ans), difficulty=3,
        explanation=f"Round each number to 1 s.f.: {r1}, {r2} and {r3}. Then work out ({r1} × {r2}) ÷ {r3}.",
    )


@template(code="between_which_integers_sqrt", subject=SUBJECT, topic=NUMBER, lessons=["1.21"])
def between_which_integers_sqrt(rng):
    n = rng.randint(10, 150)
    k = math.isqrt(n)
    if k * k == n:
        return None
    opts = [f"{j} and {j + 1}" for j in (k - 1, k, k + 1, k + 2)]
    return mcq(
        rng, f"Between which two consecutive whole numbers does √{n} lie?", f"{k} and {k + 1}",
        [o for o in opts if o != f"{k} and {k + 1}"], difficulty=2,
        explanation=f"{k}² = {k * k} and {k + 1}² = {(k + 1) ** 2}, and {n} is between them.",
    )


@template(code="which_is_standard_form", subject=SUBJECT, topic=NUMBER, lessons=["1.22"])
def which_is_standard_form(rng):
    a = Decimal(rng.randint(10, 99)) / 10
    n = rng.randint(2, 9)
    m = rng.randint(2, 9)
    correct = f"{fmt_dec(a)} × 10^{n}"
    wrong = [
        f"{rng.randint(11, 99)} × 10^{m}",
        f"0.{rng.randint(11, 99)} × 10^{m}",
        f"{fmt_dec(a)} × {rng.choice([3, 5, 7])}^{m}",
    ]
    return mcq(
        rng, "Which one of these numbers is written in standard form?", correct, wrong, difficulty=2,
        explanation="Standard form is A × 10^n where A is at least 1 and less than 10, and n is a whole number.",
    )


def _random_mantissa(rng, max_sf=3):
    sf = rng.randint(1, max_sf)
    digits = [rng.randint(1, 9)] + [rng.randint(0, 9) for _ in range(sf - 1)]
    if sf > 1 and digits[-1] == 0:
        digits[-1] = rng.randint(1, 9)
    return Decimal(f"{digits[0]}.{''.join(map(str, digits[1:]))}" if sf > 1 else str(digits[0]))


@template(code="to_standard_form", subject=SUBJECT, topic=NUMBER, lessons=["1.23"])
def to_standard_form(rng):
    a = _random_mantissa(rng)
    n = rng.choice([-7, -6, -5, -4, -3, 3, 4, 5, 6, 7, 8])
    x = a.scaleb(n)
    return make_question(
        f"Write {format(x, 'f')} in standard form.", sci_str(x), difficulty=3,
        explanation=f"Move the decimal point to make a number between 1 and 10 "
                    f"({fmt_dec(a)}), then count how many places you moved it to get the power of 10.",
    )


@template(code="from_standard_form", subject=SUBJECT, topic=NUMBER, lessons=["1.23"])
def from_standard_form(rng):
    a = _random_mantissa(rng)
    n = rng.choice([-6, -5, -4, -3, -2, 2, 3, 4, 5, 6])
    return make_question(
        f"Write {fmt_dec(a)} × 10^{n} as an ordinary number.", format(a.scaleb(n), "f"), difficulty=2,
        explanation=f"A power of {n} moves the decimal point {abs(n)} places "
                    f"{'right' if n > 0 else 'left'}.",
    )


def _one_dp(rng):
    return Decimal(rng.randint(10, 99)) / 10


@template(code="multiply_standard_form", subject=SUBJECT, topic=NUMBER, lessons=["1.24"])
def multiply_standard_form(rng):
    a, b = _one_dp(rng), _one_dp(rng)
    m, n = rng.randint(2, 8), rng.randint(2, 8)
    product = a.scaleb(m) * b.scaleb(n)
    return make_question(
        f"Work out ({fmt_dec(a)} × 10^{m}) × ({fmt_dec(b)} × 10^{n}). Give your answer in standard form.",
        sci_str(product), difficulty=4,
        explanation=f"Multiply {fmt_dec(a)} × {fmt_dec(b)} and add the powers: {m} + {n}. "
                    f"Then rewrite in standard form if the first number is 10 or more.",
    )


@template(code="divide_standard_form", subject=SUBJECT, topic=NUMBER, lessons=["1.24"])
def divide_standard_form(rng):
    a = _one_dp(rng)
    b = Decimal(rng.choice([2, 4, 5, 8]))
    m, n = rng.randint(6, 12), rng.randint(2, 5)
    quotient = a.scaleb(m) / b.scaleb(n)
    return make_question(
        f"Work out ({fmt_dec(a)} × 10^{m}) ÷ ({fmt_dec(b)} × 10^{n}). Give your answer in standard form.",
        sci_str(quotient), difficulty=4,
        explanation=f"Divide {fmt_dec(a)} by {fmt_dec(b)} and subtract the powers: {m} − {n}. "
                    f"Then rewrite in standard form if needed.",
    )


@template(code="add_standard_form", subject=SUBJECT, topic=NUMBER, lessons=["1.25"])
def add_standard_form(rng):
    a, b = _one_dp(rng), _one_dp(rng)
    m = rng.randint(3, 9)
    n = m - rng.choice([0, 0, 1, 2])
    total = a.scaleb(m) + b.scaleb(n)
    return make_question(
        f"Work out ({fmt_dec(a)} × 10^{m}) + ({fmt_dec(b)} × 10^{n}). Give your answer in standard form.",
        sci_str(total), difficulty=4,
        explanation="Write both numbers as ordinary numbers (or with the same power of 10), add them, "
                    "then convert back to standard form.",
    )


@template(code="subtract_standard_form", subject=SUBJECT, topic=NUMBER, lessons=["1.25"])
def subtract_standard_form(rng):
    a, b = _one_dp(rng), _one_dp(rng)
    m = rng.randint(3, 9)
    n = m - rng.choice([0, 1, 2])
    x, y = a.scaleb(m), b.scaleb(n)
    if x <= y:
        return None
    return make_question(
        f"Work out ({fmt_dec(a)} × 10^{m}) − ({fmt_dec(b)} × 10^{n}). Give your answer in standard form.",
        sci_str(x - y), difficulty=4,
        explanation="Write both numbers with the same power of 10 (or as ordinary numbers), subtract, "
                    "then convert back to standard form.",
    )


# =========================================================================
# RATIO, PROPORTION AND RATES OF CHANGE
# =========================================================================
_PAIRS = [("red beads", "blue beads"), ("boys", "girls"), ("cats", "dogs"),
          ("adults", "children"), ("apples", "pears")]


@template(code="scale_up_ratio", subject=SUBJECT, topic=RATIO, lessons=["4.4"])
def scale_up_ratio(rng):
    pair = _coprime_pair(rng, 1, 9)
    if not pair or pair[0] == pair[1]:
        return None
    a, b = pair
    k = rng.randint(2, 12)
    x, y = rng.choice(_PAIRS)
    return make_question(
        f"The ratio of {x} to {y} is {a}:{b}. There are {k * b} {y}. How many {x} are there?",
        str(k * a), difficulty=2,
        explanation=f"{b} parts is {k * b}, so 1 part is {k}. Multiply {a} by {k}.",
    )


@template(code="ratio_one_to_n", subject=SUBJECT, topic=RATIO, lessons=["4.5"])
def ratio_one_to_n(rng):
    a = rng.choice([2, 4, 5, 8])
    b = rng.randint(a + 1, 40)
    return make_question(
        f"Write the ratio {a}:{b} in the form 1:n.", f"1:{tdec(Fraction(b, a))}", difficulty=3,
        explanation=f"Divide both parts by {a}: {a} ÷ {a} = 1 and {b} ÷ {a} = {tdec(Fraction(b, a))}.",
    )


@template(code="ratio_to_fraction", subject=SUBJECT, topic=RATIO, lessons=["4.5"])
def ratio_to_fraction(rng):
    pair = _coprime_pair(rng, 1, 9)
    if not pair or pair[0] == pair[1]:
        return None
    a, b = pair
    x, y = rng.choice(_PAIRS)
    return make_question(
        f"The ratio of {x} to {y} is {a}:{b}. What fraction of the total are {x}?",
        frac_str(Fraction(a, a + b)), difficulty=3,
        explanation=f"There are {a} + {b} = {a + b} parts altogether, and {a} of them are {x}.",
    )


@template(code="share_in_ratio", subject=SUBJECT, topic=RATIO, lessons=["4.6"])
def share_in_ratio(rng):
    pair = _coprime_pair(rng, 1, 9)
    if not pair or pair[0] == pair[1]:
        return None
    a, b = pair
    part = rng.choice([5, 10, 15, 20, 25, 30, 40, 50])
    total = part * (a + b)
    n1, n2 = rng.sample(["Amy", "Ben", "Cara", "Dev", "Ella", "Femi"], 2)
    return make_question(
        f"{n1} and {n2} share £{total} in the ratio {a}:{b}. How much does {n2} get?",
        money(part * b), difficulty=3,
        explanation=f"{a} + {b} = {a + b} parts, so 1 part is £{total} ÷ {a + b} = £{part}. "
                    f"{n2} gets {b} parts.",
    )


@template(code="share_three_way", subject=SUBJECT, topic=RATIO, lessons=["4.6"])
def share_three_way(rng):
    a, b, c = sorted(rng.sample(range(1, 8), 3))
    if math.gcd(math.gcd(a, b), c) != 1:
        return None
    part = rng.choice([4, 5, 6, 8, 10, 12, 15])
    total = part * (a + b + c)
    return make_question(
        f"£{total} is shared between three people in the ratio {a}:{b}:{c}. "
        f"How much does the person with the largest share get?",
        money(part * c), difficulty=4,
        explanation=f"{a} + {b} + {c} = {a + b + c} parts, so 1 part is £{part}. The largest share is {c} parts.",
    )


@template(code="scale_recipe", subject=SUBJECT, topic=RATIO, lessons=["4.7"])
def scale_recipe(rng):
    per = rng.choice([10, 15, 20, 25, 30, 40, 50])
    p, q = rng.choice([2, 3, 4, 5, 6, 8]), rng.randint(2, 15)
    ingredient = rng.choice([("flour", "grams"), ("sugar", "grams"), ("butter", "grams"), ("milk", "ml")])
    if p == q:
        return None
    return make_question(
        f"A recipe for {p} people uses {per * p} {ingredient[1]} of {ingredient[0]}. "
        f"How many {ingredient[1]} of {ingredient[0]} are needed for {q} people?",
        str(per * q), difficulty=2,
        explanation=f"For 1 person: {per * p} ÷ {p} = {per}. For {q} people: {per} × {q}.",
    )


@template(code="best_buy", subject=SUBJECT, topic=RATIO, lessons=["4.8"])
def best_buy(rng):
    n1, n2 = rng.choice([200, 250, 300, 400, 500]), rng.choice([600, 750, 800, 1000, 1200])
    p1, p2 = Fraction(rng.randint(80, 300), 100), Fraction(rng.randint(200, 600), 100)
    u1, u2 = p1 / n1, p2 / n2
    if abs(u1 - u2) / max(u1, u2) < Fraction(1, 20):
        return None
    pence100 = lambda p, n: round(float(p / n) * 10000, 1)
    better = "Pack A" if u1 < u2 else "Pack B"
    return mcq(
        rng,
        f"Pack A contains {n1} g of pasta and costs {money(p1)}. Pack B contains {n2} g and costs "
        f"{money(p2)}. Which pack is better value for money?",
        better, ["Pack A", "Pack B", "They are the same value", "It cannot be worked out"],
        difficulty=3,
        explanation=f"Pack A costs {pence100(p1, n1)}p per 100 g and Pack B costs {pence100(p2, n2)}p per "
                    f"100 g, so {better} is cheaper per gram.",
    )


@template(code="direct_proportion_value", subject=SUBJECT, topic=RATIO, lessons=["4.9"])
def direct_proportion_value(rng):
    k = Fraction(rng.choice([2, 3, 4, 5, 6, 7, 8, 9, Fraction(3, 2), Fraction(5, 2), Fraction(7, 2), Fraction(1, 2)]))
    a, c = rng.randint(2, 12), rng.randint(2, 20)
    if a == c:
        return None
    return make_question(
        f"y is directly proportional to x. When x = {a}, y = {tdec(k * a)}. Find y when x = {c}.",
        tdec(k * c), difficulty=3,
        explanation=f"y = kx, so k = {tdec(k * a)} ÷ {a} = {tdec(k)}. Then y = {tdec(k)} × {c}.",
    )


@template(code="direct_proportion_formula", subject=SUBJECT, topic=RATIO, lessons=["4.10"])
def direct_proportion_formula(rng):
    k = Fraction(rng.choice([2, 3, 4, 5, 6, 7, 8, Fraction(3, 2), Fraction(5, 2), Fraction(1, 2)]))
    a = rng.randint(2, 12)
    return make_question(
        f"y is directly proportional to x. When x = {a}, y = {tdec(k * a)}. "
        f"Write down a formula for y in terms of x.",
        f"y = {tdec(k)}x", difficulty=3,
        explanation=f"Write y = kx. Substitute to find k = {tdec(k * a)} ÷ {a} = {tdec(k)}.",
    )


@template(code="inverse_proportion_value", subject=SUBJECT, topic=RATIO, lessons=["4.11"])
def inverse_proportion_value(rng):
    a, b = rng.randint(2, 12), rng.randint(2, 12)
    product = a * b
    divisors = [d for d in range(2, product + 1) if product % d == 0 and d != a and d <= 40]
    if not divisors:
        return None
    c = rng.choice(divisors)
    return make_question(
        f"y is inversely proportional to x. When x = {a}, y = {b}. Find y when x = {c}.",
        tdec(Fraction(product, c)), difficulty=4,
        explanation=f"y = k/x, so k = x × y = {a} × {b} = {product}. Then y = {product} ÷ {c}.",
    )


@template(code="inverse_proportion_meaning", subject=SUBJECT, topic=RATIO, lessons=["4.11"])
def inverse_proportion_meaning(rng):
    k = rng.randint(2, 30)
    return mcq(
        rng, "Which one of these equations shows that y is inversely proportional to x?",
        f"y = {k}/x", [f"y = {k}x", f"y = x + {k}", f"y = {k} − x"], difficulty=2,
        explanation="Inverse proportion means y = k ÷ x: when x doubles, y halves.",
    )


@template(code="percentage_of_amount", subject=SUBJECT, topic=RATIO, lessons=["4.12"])
def percentage_of_amount(rng):
    p = rng.choice([5, 10, 15, 20, 25, 30, 35, 40, 45, 60, 75, 80, 12, 8])
    n = rng.choice(range(20, 501, 10))
    result = Fraction(n * p, 100)
    if not _terminating_places(result, 2):
        return None
    return make_question(
        f"Find {p}% of £{n}.", money(result), difficulty=2,
        explanation=f"{p}% = {p}/100, so work out £{n} × {p} ÷ 100.",
    )


@template(code="percentage_multiplier", subject=SUBJECT, topic=RATIO, lessons=["4.13"])
def percentage_multiplier(rng):
    p = rng.choice([3, 4, 5, 6, 7, 8, 12, 15, 18, 20, 25, 35])
    up = rng.random() < 0.5
    mult = Fraction(100 + p if up else 100 - p, 100)
    return make_question(
        f"Write down the single multiplier you would use to {'increase' if up else 'decrease'} "
        f"an amount by {p}%.", tdec(mult), difficulty=3,
        explanation=f"{'100% + ' if up else '100% − '}{p}% = {int(mult * 100)}%, which is {tdec(mult)} as a decimal.",
    )


@template(code="percentage_increase_amount", subject=SUBJECT, topic=RATIO, lessons=["4.13"])
def percentage_increase_amount(rng):
    p = rng.choice([5, 10, 12, 15, 20, 25, 30, 35, 40])
    n = rng.choice(range(40, 801, 20))
    up = rng.random() < 0.5
    result = Fraction(n) * Fraction(100 + p if up else 100 - p, 100)
    if not _terminating_places(result, 2):
        return None
    return make_question(
        f"A price of £{n} is {'increased' if up else 'decreased'} by {p}%. What is the new price?",
        money(result), difficulty=3,
        explanation=f"Multiply by {tdec(Fraction(100 + p if up else 100 - p, 100))}.",
    )


@template(code="express_as_percentage", subject=SUBJECT, topic=RATIO, lessons=["4.14"])
def express_as_percentage(rng):
    b = rng.choice([20, 25, 40, 50, 80, 125, 200])
    a = rng.randint(1, b - 1)
    pct = Fraction(a * 100, b)
    if not _terminating_places(pct, 1):
        return None
    name = rng.choice(["Mia", "Tom", "Asha", "Leo"])
    return make_question(
        f"In a test, {name} scored {a} out of {b}. Write this as a percentage.",
        f"{tdec(pct)}%", difficulty=2,
        explanation=f"Divide {a} by {b} and multiply by 100.",
    )


@template(code="percentage_change", subject=SUBJECT, topic=RATIO, lessons=["4.15"])
def percentage_change(rng):
    p = rng.choice([5, 10, 12, 15, 20, 25, 30, 40, 50, 60, 75])
    old = rng.choice([40, 60, 80, 120, 160, 200, 240, 250, 300, 400, 500, 600, 800])
    up = rng.random() < 0.5
    new = Fraction(old) * Fraction(100 + p if up else 100 - p, 100)
    if new.denominator != 1:
        return None
    return make_question(
        f"The price of a bike changes from £{old} to £{int(new)}. "
        f"Work out the percentage {'increase' if up else 'decrease'}.",
        f"{p}%", difficulty=3,
        explanation=f"Change = £{abs(int(new) - old)}. Percentage change = change ÷ original × 100 "
                    f"= {abs(int(new) - old)} ÷ {old} × 100.",
    )


@template(code="reverse_percentage_sale", subject=SUBJECT, topic=RATIO, lessons=["4.16"])
def reverse_percentage_sale(rng):
    x = rng.choice([10, 15, 20, 25, 30, 40, 50])
    original = rng.choice(range(20, 401, 10))
    sale = Fraction(original) * Fraction(100 - x, 100)
    if not _terminating_places(sale, 2):
        return None
    return make_question(
        f"In a sale, all prices are reduced by {x}%. A coat costs {money(sale)} in the sale. "
        f"What was the original price of the coat?",
        money(original), difficulty=4,
        explanation=f"The sale price is {100 - x}% of the original. Divide {money(sale)} by "
                    f"{tdec(Fraction(100 - x, 100))} to find 100%.",
    )


@template(code="reverse_percentage_vat", subject=SUBJECT, topic=RATIO, lessons=["4.16"])
def reverse_percentage_vat(rng):
    before = rng.choice(range(10, 301, 5))
    total = Fraction(before) * Fraction(6, 5)
    if not _terminating_places(total, 2):
        return None
    return make_question(
        f"A tablet costs {money(total)} including VAT at 20%. What is the price before VAT is added?",
        money(before), difficulty=4,
        explanation=f"The price with VAT is 120% of the price before VAT. Divide {money(total)} by 1.2.",
    )


@template(code="simple_interest_amount", subject=SUBJECT, topic=RATIO, lessons=["4.17"])
def simple_interest_amount(rng):
    principal = rng.choice(range(200, 5001, 100))
    rate = Fraction(rng.choice([1, 2, 3, 4, 5, 6, 8, Fraction(3, 2), Fraction(5, 2), Fraction(7, 2)]))
    years = rng.randint(2, 10)
    interest = Fraction(principal) * rate * years / 100
    if not _terminating_places(interest, 2):
        return None
    return make_question(
        f"Priya invests £{principal} for {years} years at {tdec(rate)}% per year simple interest. "
        f"How much interest does she earn altogether?",
        money(interest), difficulty=3,
        explanation=f"Interest each year = {tdec(rate)}% of £{principal}. Multiply by {years} years.",
    )


@template(code="simple_interest_total", subject=SUBJECT, topic=RATIO, lessons=["4.17"])
def simple_interest_total(rng):
    principal = rng.choice(range(500, 8001, 100))
    rate = Fraction(rng.choice([1, 2, 3, 4, 5, 6, Fraction(5, 2), Fraction(3, 2)]))
    years = rng.randint(2, 8)
    interest = Fraction(principal) * rate * years / 100
    if not _terminating_places(interest, 2):
        return None
    return make_question(
        f"£{principal} is put in an account paying {tdec(rate)}% per year simple interest. "
        f"How much is in the account after {years} years?",
        money(principal + interest), difficulty=3,
        explanation=f"Simple interest is the same each year: £{tdec(interest)} in total. Add it to £{principal}.",
    )
