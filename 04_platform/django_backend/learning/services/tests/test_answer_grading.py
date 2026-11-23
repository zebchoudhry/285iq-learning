import pytest

from learning.services.answer_grading import answers_equivalent


def ok(student, correct):
    return answers_equivalent(student, correct)[0]


@pytest.mark.parametrize("student,correct", [
    ("12", "12"), ("12.0", "12"), ("£12.50", "12.5"), ("12.5", "£12.50"), ("75%", "75%"), ("75", "75%"),
    ("450 g", "450"), ("450g", "450"), ("x = 5", "5"), ("5", "x = 5"), ("1,250", "1250"), ("2,5", "2.5"),
    ("−3", "-3"), ("0.333", "0.333"),
    ("3/4", "3/4"), (" 3 / 4 ", "3/4"), ("1 1/2", "1 1/2"),
    ("3.2 × 10^5", "3.2 × 10^5"), ("3.2x10^5", "3.2 × 10^5"), ("3.2 x 10^5", "3.2 × 10^5"),
    ("3.2*10^5", "3.2 × 10^5"), ("3.2e5", "3.2 × 10^5"), ("4.5 × 10^-3", "4.5 × 10^-3"),
    ("1:2.5", "1:2.5"), ("1 : 2.5", "1:2.5"), ("y=3x", "y = 3x"),
    ("41, 43, 47", "41, 43, 47"), ("41,43,47", "41, 43, 47"),
    ("Sodium Chloride", "sodium chloride"), ("Mg(OH)2", "Mg(OH)2"),
])
def test_accepted(student, correct):
    assert ok(student, correct)


@pytest.mark.parametrize("student,correct", [
    ("12", "1/2"),          # the old bug: '/' was stripped
    ("1/2", "12"),
    ("6/8", "3/4"),         # fractions must be in lowest terms
    ("0.75", "3/4"),        # a fraction answer must be a fraction
    ("3/8", "0.375"),       # and a decimal answer must be a decimal
    ("3/2", "1 1/2"),       # a mixed number must be a mixed number
    ("320000", "3.2 × 10^5"),  # standard form must be standard form
    ("32 × 10^4", "3.2 × 10^5"),  # with 1 <= A < 10
    ("3.2 × 10^5", "320000"),
    ("2", "Mg(OH)2"),       # digits inside a formula are not a number
    ("238", "uranium-238"),
    ("3", "y = 3x"),
    ("12.5", "1:2.5"),
    ("13", "12"), ("", "12"), ("abc", "12"),
    ("41, 43", "41, 43, 47"),
])
def test_rejected(student, correct):
    assert not ok(student, correct)


def test_every_template_answer_matches_itself():
    import random
    from learning.generators.engine import load_all_templates
    for t in load_all_templates():
        for seed in range(30):
            q = t.build(random.Random(seed))
            if q and q["question_type"] == "short_answer":
                assert ok(q["correct_answer"], q["correct_answer"]), q
