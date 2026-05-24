from datetime import timedelta
from django.utils import timezone

UPGRADE_CONFIRMATIONS_REQUIRED = 2
DOWNGRADE_CONFIRMATIONS_REQUIRED = 3

EXAM_MODES = {"exam_sim"}
BASELINE_MODE = "instruction"

# Mode hierarchy for proper comparison (fixes string comparison bug)
MODE_HIERARCHY = {
    "instruction": 1,
    "guided_practice": 2,
    "drill": 3,
    "mixed_practice": 4,
    "exam_sim": 5,
    "mastery_maintenance": 6,
}


def apply_hysteresis(
    *,
    proposed_mode: str,
    state,
):
    """
    Decide whether to accept a proposed mode change
    based on historical stability.
    """

    # First ever state
    if state is None:
        return proposed_mode, 1

    # Same mode → reinforce
    if proposed_mode == state.current_mode:
        return proposed_mode, state.confirmation_count + 1

    # Exam modes are sticky (hard to downgrade)
    if state.current_mode in EXAM_MODES:
        if state.confirmation_count < DOWNGRADE_CONFIRMATIONS_REQUIRED:
            return state.current_mode, state.confirmation_count + 1

    # Use hierarchy for comparison instead of string comparison
    proposed_level = MODE_HIERARCHY.get(proposed_mode, 0)
    current_level = MODE_HIERARCHY.get(state.current_mode, 0)
    
    # Upgrades require fewer confirmations than downgrades
    confirmations_needed = (
        UPGRADE_CONFIRMATIONS_REQUIRED
        if proposed_level > current_level
        else DOWNGRADE_CONFIRMATIONS_REQUIRED
    )

    if state.confirmation_count + 1 >= confirmations_needed:
        return proposed_mode, 1

    return state.current_mode, state.confirmation_count + 1
