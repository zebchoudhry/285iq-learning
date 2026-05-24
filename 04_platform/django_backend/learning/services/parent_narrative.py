from typing import Any, Dict, List


def _status_label(risk_level: str) -> str:
    if risk_level == "at_risk":
        return "At risk"
    if risk_level == "watch":
        return "Watch"
    return "On track"


def build_parent_narrative(
    *,
    subject_name: str,
    target_grade: int,
    predicted_grade: int,
    risk_level: str,
    sessions_per_week: float,
    coverage_breadth: float,
    weak_skills: List[str],
) -> Dict[str, Any]:
    gap = max(0, int(target_grade) - int(predicted_grade))
    status = _status_label(risk_level)
    weak_label = ", ".join(weak_skills[:3]) if weak_skills else "core retrieval and timed fluency"
    sessions_goal = 3 if gap >= 2 else 2

    if risk_level == "at_risk":
        summary = (
            f"{status}: target Grade {target_grade}, current estimate Grade {predicted_grade}. "
            f"Biggest blockers are {weak_label}."
        )
    elif risk_level == "watch":
        summary = (
            f"{status}: target Grade {target_grade}, current estimate Grade {predicted_grade}. "
            f"Performance is close but still inconsistent in {weak_label}."
        )
    else:
        summary = (
            f"{status}: target Grade {target_grade}, current estimate Grade {predicted_grade}. "
            f"Maintain momentum with mixed and timed practice."
        )

    evidence = [
        f"Sessions per week: {sessions_per_week}",
        f"Coverage breadth: {round(coverage_breadth, 1)}%",
        f"Grade gap: {gap}",
    ]
    actions = [
        f"Complete {sessions_goal} focused sessions this week in {subject_name}.",
        f"Prioritize: {weak_label}.",
        "Finish one timed exam-style block and review mistakes the same day.",
    ]
    return {
        "status": status.lower().replace(" ", "_"),
        "summary": summary,
        "evidence": evidence,
        "actions": actions,
    }
