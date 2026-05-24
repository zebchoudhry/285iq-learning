from dataclasses import dataclass


@dataclass
class DecisionSummary:
    logic_locked: bool
    trend: str
    stability_score: float
    verification_rate: float


def get_decision_summary(student_id: int, topic_id: int) -> DecisionSummary:
    """
    TEMPORARY STUB.
    This will be replaced by the real decision engine later.
    """

    return DecisionSummary(
        logic_locked=False,
        trend="stable",
        stability_score=0.0,
        verification_rate=0.0,
    )
