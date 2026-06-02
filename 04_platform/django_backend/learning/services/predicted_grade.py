"""
Predicted grade service for GCSE students.
"""
import logging

logger = logging.getLogger(__name__)


def predict_grade(attainment_band: float, target_grade: int, weeks_remaining: int) -> dict:
    """
    Returns {"predicted_grade": int, "confidence": "low"|"medium"|"high", "message": str}

    attainment_band: 0.0-1.0 (from decision engine)
    target_grade: student's target GCSE grade (1-9)
    weeks_remaining: weeks until exam
    """
    predicted_grade = max(1, min(9, round(attainment_band * 9)))

    if weeks_remaining > 15:
        confidence = "high"
    elif weeks_remaining > 6:
        confidence = "medium"
    else:
        confidence = "low"

    if predicted_grade >= target_grade:
        stretch_grade = min(9, predicted_grade + 1)
        message = (
            f"On track for Grade {predicted_grade}. "
            f"3 more sessions/week could reach Grade {stretch_grade}."
        )
    else:
        gap = target_grade - predicted_grade
        message = (
            f"Currently predicted Grade {predicted_grade}. "
            f"You need to close a {gap}-grade gap to hit your target of Grade {target_grade}. "
            f"Focus on weak topics and increase practice frequency."
        )

    logger.debug(
        "predict_grade: attainment_band=%.3f target=%d weeks=%d → grade=%d confidence=%s",
        attainment_band, target_grade, weeks_remaining, predicted_grade, confidence,
    )
    return {
        "predicted_grade": predicted_grade,
        "confidence": confidence,
        "message": message,
    }
