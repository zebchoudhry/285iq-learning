"""Elo-style rating calibration for questions and students.

References:
- Standard Elo update with shrinking K-factor (Glicko-lite).
- Outcome is in [0.0, 1.0]; partial credit allowed via marks_achieved / marks_available.

Design notes:
- High K for new questions/students so ratings move quickly toward truth.
- K shrinks once enough attempts accumulate, locking in calibrated values.
- First-attempt-only for question difficulty updates (prevents a student
  from "training" a question by repeated attempts).
"""

from typing import Tuple


def expected_score(student_rating: float, question_rating: float) -> float:
    """Standard Elo expected-score formula."""
    return 1.0 / (1.0 + 10 ** ((question_rating - student_rating) / 400.0))


def k_factor_question(rating_attempts: int) -> float:
    if rating_attempts < 30:
        return 64.0
    if rating_attempts < 100:
        return 32.0
    if rating_attempts < 300:
        return 16.0
    return 8.0


def k_factor_student(attempt_count: int) -> float:
    if attempt_count < 50:
        return 32.0
    if attempt_count < 200:
        return 16.0
    return 8.0


def update_ratings(
    *,
    student_rating: float,
    question_rating: float,
    outcome: float,         # 0.0 .. 1.0
    student_attempts: int,
    question_attempts: int,
    update_question: bool,  # False on repeat attempts of same question
) -> Tuple[float, float]:
    """Return (new_student_rating, new_question_rating)."""
    if not (0.0 <= outcome <= 1.0):
        raise ValueError("outcome must be in [0.0, 1.0]")

    expected = expected_score(student_rating, question_rating)
    k_s = k_factor_student(student_attempts)
    new_student = student_rating + k_s * (outcome - expected)

    if update_question:
        k_q = k_factor_question(question_attempts)
        new_question = question_rating + k_q * (expected - outcome)
    else:
        new_question = question_rating

    return new_student, new_question


def outcome_from_attempt(*, is_correct: bool, marks_achieved: int, marks_available: int) -> float:
    """Map an attempt to an Elo outcome in [0.0, 1.0].

    - For MCQ/binary: is_correct → 1.0 / 0.0.
    - For multi-mark: marks_achieved / marks_available (capped to [0, 1]).
    """
    if marks_available and marks_available > 1:
        return max(0.0, min(1.0, marks_achieved / marks_available))
    return 1.0 if is_correct else 0.0
