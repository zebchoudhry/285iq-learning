"""
Decision Engine v2
------------------
Pure decision logic for Gym Mode selection.

Inputs:
- metrics (dict) produced by controller / adapter layer

Outputs:
- mode (str)
- reason (str)
- metrics_snapshot (dict)

This file MUST remain framework-agnostic.
"""

from typing import Dict, Tuple


GYM_MODES = {
    "instruction": "Teach core concepts with guidance",
    "guided_practice": "Worked examples + scaffolded questions",
    "drill": "Targeted repetition on weak skills",
    "mixed_practice": "Interleaved questions across skills",
    "exam_sim": "Timed exam-style questions",
    "mastery_maintenance": "Light practice to prevent decay",
}

MIN_ATTEMPTS_FOR_SIGNAL = 5
RECENT_WINDOW_ATTEMPTS = 5

ACCURACY_WEAK = 0.55
ACCURACY_OK = 0.70
ACCURACY_STRONG = 0.85

RECENT_DROP_DELTA = 0.15

# Long gap since last attempt → light review for strong students
RETENTION_IDLE_DAYS = 12


def decide_gym_mode(metrics: Dict) -> Tuple[str, str, Dict]:
    """
    Decide the correct gym mode based on performance metrics.
    """
    total_attempts = metrics.get("total_attempts", 0)
    accuracy = metrics.get("accuracy_rate", 0.0)
    recent_accuracy = metrics.get("recent_accuracy", 0.0)
    dominant_error = metrics.get("dominant_error_type", "none")
    days_since_last = metrics.get("days_since_last_attempt")

    snapshot = {
        "total_attempts": total_attempts,
        "accuracy_rate": accuracy,
        "recent_accuracy": recent_accuracy,
        "dominant_error_type": dominant_error,
        "days_since_last_attempt": days_since_last,
    }

    # 0. Cold start
    if total_attempts < MIN_ATTEMPTS_FOR_SIGNAL:
        return "instruction", "insufficient_data", snapshot

    # 1. Strong history but idle → retention (before pushing back to exam_sim)
    if (
        days_since_last is not None
        and days_since_last >= RETENTION_IDLE_DAYS
        and accuracy >= ACCURACY_STRONG
    ):
        return "mastery_maintenance", "retention_refresh", snapshot

    # 2. Procedural / guessing pattern in mid-band accuracy → drill
    if (
        dominant_error in ("procedural", "guess")
        and ACCURACY_WEAK <= accuracy < ACCURACY_OK
    ):
        return "drill", "procedural_remediation", snapshot

    # 3. Severe misunderstanding
    if accuracy < ACCURACY_WEAK:
        if dominant_error in ("conceptual", "structural"):
            return "instruction", "foundational_gaps", snapshot
        return "guided_practice", "low_accuracy", snapshot

    # 4. Skill forming stage
    if ACCURACY_WEAK <= accuracy < ACCURACY_OK:
        return "drill", "skill_consolidation", snapshot

    # 5. Regression detection
    if accuracy - recent_accuracy > RECENT_DROP_DELTA:
        return "drill", "performance_regression", snapshot

    # 6. Competent but unstable
    if ACCURACY_OK <= accuracy < ACCURACY_STRONG:
        return "mixed_practice", "stability_building", snapshot

    # 7. Exam readiness
    if accuracy >= ACCURACY_STRONG and recent_accuracy >= ACCURACY_STRONG:
        return "exam_sim", "exam_ready", snapshot

    return "guided_practice", "fallback_safe_mode", snapshot
