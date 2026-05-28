import pytest

from learning.services.calibration import (
    expected_score,
    k_factor_question,
    k_factor_student,
    outcome_from_attempt,
    update_ratings,
)


def test_expected_score_symmetric():
    assert expected_score(1500, 1500) == 0.5


def test_expected_score_strong_vs_weak():
    assert expected_score(1700, 1500) > 0.7


def test_update_correct_increases_student_decreases_question():
    new_student, new_question = update_ratings(
        student_rating=1500.0,
        question_rating=1500.0,
        outcome=1.0,
        student_attempts=0,
        question_attempts=0,
        update_question=True,
    )
    assert new_student > 1500.0
    assert new_question < 1500.0


def test_update_wrong_decreases_student_increases_question():
    new_student, new_question = update_ratings(
        student_rating=1500.0,
        question_rating=1500.0,
        outcome=0.0,
        student_attempts=0,
        question_attempts=0,
        update_question=True,
    )
    assert new_student < 1500.0
    assert new_question > 1500.0


def test_k_factor_shrinks():
    assert k_factor_question(0) > k_factor_question(500)
    assert k_factor_student(0) > k_factor_student(500)


def test_outcome_partial_credit():
    assert outcome_from_attempt(is_correct=False, marks_achieved=3, marks_available=5) == 0.6
    assert outcome_from_attempt(is_correct=True, marks_achieved=1, marks_available=1) == 1.0
    assert outcome_from_attempt(is_correct=False, marks_achieved=0, marks_available=1) == 0.0


def test_update_question_false_leaves_question_alone():
    _, new_question = update_ratings(
        student_rating=1500.0,
        question_rating=1500.0,
        outcome=1.0,
        student_attempts=0,
        question_attempts=0,
        update_question=False,
    )
    assert new_question == 1500.0


def test_convergence():
    """A true 1700-skill student converges to ~1700 against 1500 questions."""
    TRUE_SKILL = 1700.0
    POOL_SIZE = 100
    ITERATIONS = 500

    questions = [{"rating": 1500.0, "attempts": 0} for _ in range(POOL_SIZE)]
    student = {"rating": 1500.0, "attempts": 0}

    for i in range(ITERATIONS):
        q = questions[i % POOL_SIZE]
        outcome = expected_score(TRUE_SKILL, q["rating"])
        new_s, new_q = update_ratings(
            student_rating=student["rating"],
            question_rating=q["rating"],
            outcome=outcome,
            student_attempts=student["attempts"],
            question_attempts=q["attempts"],
            update_question=True,
        )
        student["rating"] = new_s
        student["attempts"] += 1
        q["rating"] = new_q
        q["attempts"] += 1

    assert abs(student["rating"] - TRUE_SKILL) <= 50, \
        f"Expected ~1700, got {student['rating']:.2f}"


def test_outcome_bounds():
    with pytest.raises(ValueError):
        update_ratings(
            student_rating=1500.0,
            question_rating=1500.0,
            outcome=1.5,
            student_attempts=0,
            question_attempts=0,
            update_question=True,
        )
