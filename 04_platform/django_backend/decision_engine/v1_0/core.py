"""
285IQ Decision Engine v1.0 - Core Implementation
Frozen on: 2026-01-14

This implementation is governed by:
- 285IQ Decision & Notification Contract v1.0
- test_decision_engine_v1.py (behavioural lock)

⚠️ IMMUTABLE MODULE — DO NOT MODIFY
Any change to logic, thresholds, or behaviour
REQUIRES a version bump (v1.1 or v2.0).
"""

from datetime import date, datetime, timedelta
from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass
from enum import Enum


# ============================================================================
# CONTRACT VERSION
# ============================================================================

CONTRACT_VERSION = "1.0"


# ============================================================================
# ENUMS
# ============================================================================

class TimeZone(Enum):
    """Time-based strictness zones."""
    FORGIVING = "forgiving"      # 20+ weeks
    STANDARD = "standard"        # 12-20 weeks
    STRICT = "strict"            # 5-12 weeks
    FROZEN = "frozen"            # <5 weeks
    # Aliases for test contract compatibility
    BUILDING = "forgiving"       # 20+ weeks
    STRENGTHENING = "standard"   # 12-20 weeks
    CONSOLIDATION = "strict"     # 5-12 weeks
    RISK_MANAGEMENT = "frozen"   # <5 weeks


class OutlookTier(Enum):
    """Parent-facing outlook tiers."""
    ON_TRACK = "on_track"
    STRETCH_ACHIEVABLE = "stretch_but_achievable"
    STRETCH_BUT_ACHIEVABLE = "stretch_but_achievable"  # Alias for test compatibility
    AT_RISK = "at_risk"


class PerformanceTrend(Enum):
    """Performance direction over time."""
    IMPROVING = "improving"
    NEUTRAL = "neutral"
    DECLINING = "declining"
    POSITIVE = "improving"   # Alias for test compatibility
    NEGATIVE = "declining"   # Alias for test compatibility


class NotificationPriority(Enum):
    """Priority levels for notifications."""
    PRIORITY_1_URGENT = 1     # Inactivity, sharp decline
    PRIORITY_2_INFORMATIONAL = 2  # Tier change, milestone
    PRIORITY_1 = 1   # Alias for PRIORITY_1_URGENT (test compatibility)
    PRIORITY_2 = 2   # Alias for PRIORITY_2_INFORMATIONAL (test compatibility)


class FocusType(Enum):
    """Recommendation focus areas."""
    TOPIC_PRIORITIZATION = "topic_prioritization"
    CONSISTENCY_ADJUSTMENT = "consistency_adjustment"
    CONFIDENCE_REINFORCEMENT = "confidence_reinforcement"
    DAMAGE_CONTROL = "damage_control"


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class WeeklyPerformanceSummary:
    """Weekly aggregate performance data."""
    week_ending: date
    average_accuracy: float  # 0.0 to 1.0
    questions_attempted: int
    topics_accessed: int
    difficulty_distribution: float  # Average difficulty level


@dataclass
class TopicPerformance:
    """Per-topic performance metrics."""
    topic_id: str
    last_4_weeks_accuracy: float
    last_6_weeks_accuracy: float
    last_attempt_date: date
    total_attempts: int
    trend: PerformanceTrend


@dataclass
class TierAssignment:
    """Tier assignment with reasoning."""
    tier: OutlookTier
    reason: str
    timestamp: datetime
    weeks_remaining: int
    is_frozen_display: bool


@dataclass
class HysteresisState:
    """State for anti-flicker stability. Supports two schemas:
    - (current_tier, confirmations, last_change_date) for general use
    - (consecutive_upgrade_weeks, consecutive_downgrade_weeks, last_change_date) for frozen-period checks
    """
    current_tier: Optional[OutlookTier] = None
    confirmations: int = 0
    last_change_date: Optional[date] = None
    consecutive_upgrade_weeks: int = 0
    consecutive_downgrade_weeks: int = 0

    def __post_init__(self):
        if isinstance(self.current_tier, int) and self.last_change_date is not None:
            self.consecutive_upgrade_weeks = int(self.current_tier)
            self.consecutive_downgrade_weeks = self.confirmations
            self.current_tier = None
            self.confirmations = 0


@dataclass
class NotificationLog:
    """Log entry for notification tracking."""
    notification_id: str
    timestamp: datetime
    subject_id: str
    event_type: str
    priority: NotificationPriority
    time_zone: TimeZone
    parent_action: Optional[str]


@dataclass
class NotificationRateLimitState:
    """Rate limiting state."""
    subject_notifications_this_week: Dict[str, int]
    total_notifications_this_week: int
    last_notification_date: Optional[date]
    week_start: date


# ============================================================================
# NOTIFICATION RATE LIMITS (from contract)
# ============================================================================

NOTIFICATION_PER_SUBJECT_WEEKLY_LIMIT = 1
NOTIFICATION_GLOBAL_WEEKLY_LIMIT = 2
NOTIFICATION_GLOBAL_DAILY_LIMIT = 1


# ============================================================================
# CORE FUNCTIONS
# ============================================================================

def calculate_weeks_remaining(exam_date: date, current_date: date) -> int:
    """
    Calculate weeks remaining to exam.
    
    Args:
        exam_date: Date of the exam
        current_date: Current date
        
    Returns:
        Number of complete weeks remaining
    """
    delta = exam_date - current_date
    return max(0, delta.days // 7)


def classify_time_zone(weeks_remaining: int) -> TimeZone:
    """
    Classify time zone based on weeks remaining.
    
    Time zones from contract:
    - 20+ weeks: Forgiving
    - 12-20 weeks: Standard
    - 5-12 weeks: Strict
    - <5 weeks: Frozen
    
    Args:
        weeks_remaining: Weeks until exam
        
    Returns:
        TimeZone enum
    """
    if weeks_remaining >= 20:
        return TimeZone.BUILDING   # same as FORGIVING
    elif weeks_remaining >= 12:
        return TimeZone.STRENGTHENING  # same as STANDARD
    elif weeks_remaining >= 5:
        return TimeZone.CONSOLIDATION  # same as STRICT
    else:
        return TimeZone.RISK_MANAGEMENT  # same as FROZEN


def calculate_attainment_band(
    weekly_summaries: List[WeeklyPerformanceSummary],
    coverage_breadth: float,
    min_weeks: int = 4
) -> int:
    """
    Calculate conservative attainment band (GCSE grade 1-9).
    
    Conservative bias: lowest grade band consistently supported.
    Based on recent 6-week window.
    
    Args:
        weekly_summaries: Recent weekly performance data
        coverage_breadth: Fraction of syllabus covered (0.0-1.0)
        min_weeks: Minimum weeks of data required
        
    Returns:
        Grade band (1-9), or 0 if insufficient data
    """
    if len(weekly_summaries) < min_weeks:
        return 0  # Insufficient data
    
    # Take last 6 weeks
    recent = weekly_summaries[-6:]
    
    # Calculate weighted accuracy
    total_questions = sum(w.questions_attempted for w in recent)
    if total_questions == 0:
        return 0
    
    weighted_accuracy = sum(
        w.average_accuracy * w.questions_attempted for w in recent
    ) / total_questions
    
    # Apply coverage penalty (can't achieve high grades without breadth)
    effective_accuracy = weighted_accuracy * min(1.0, coverage_breadth + 0.3)
    
    # Conservative grade mapping
    if effective_accuracy >= 0.90:
        return 9
    elif effective_accuracy >= 0.85:
        return 8
    elif effective_accuracy >= 0.78:
        return 7
    elif effective_accuracy >= 0.70:
        return 6
    elif effective_accuracy >= 0.60:
        return 5
    elif effective_accuracy >= 0.50:
        return 4
    elif effective_accuracy >= 0.40:
        return 3
    elif effective_accuracy >= 0.30:
        return 2
    else:
        return 1


def calculate_performance_trend(
    weekly_summaries: List[WeeklyPerformanceSummary],
    window_weeks: int = 6
) -> PerformanceTrend:
    """
    Calculate performance trend over recent weeks.
    
    Args:
        weekly_summaries: Weekly performance data
        window_weeks: Size of analysis window
        
    Returns:
        PerformanceTrend enum
    """
    if len(weekly_summaries) < 3:
        return PerformanceTrend.NEUTRAL
    
    # Take last N weeks
    recent = weekly_summaries[-window_weeks:]
    
    if len(recent) < 3:
        return PerformanceTrend.NEUTRAL
    
    # Split into first half and second half
    mid = len(recent) // 2
    first_half = recent[:mid]
    second_half = recent[mid:]
    
    # Calculate average accuracy for each half
    first_avg = sum(w.average_accuracy for w in first_half) / len(first_half)
    second_avg = sum(w.average_accuracy for w in second_half) / len(second_half)
    
    # Thresholds for trend detection
    IMPROVEMENT_THRESHOLD = 0.08
    DECLINE_THRESHOLD = 0.08
    
    delta = second_avg - first_avg
    
    if delta >= IMPROVEMENT_THRESHOLD:
        return PerformanceTrend.IMPROVING
    elif delta <= -DECLINE_THRESHOLD:
        return PerformanceTrend.DECLINING
    else:
        return PerformanceTrend.NEUTRAL


def assign_outlook_tier(
    *,
    attainment_band: int,
    target_grade: int,
    weeks_remaining: int,
    previous_tier: Optional[OutlookTier],
    trend: Optional[PerformanceTrend] = None,
    activity_per_week: Optional[float] = None,
    performance_trend: Optional[PerformanceTrend] = None,
    activity_frequency: Optional[float] = None,
    hysteresis: Optional[HysteresisState] = None,
    hysteresis_state: Optional[HysteresisState] = None,
) -> Tuple[OutlookTier, str]:
    """
    Assign outlook tier based on performance and time remaining.
    
    Contract rules:
    - ON_TRACK: Performance aligns with time remaining
    - STRETCH_ACHIEVABLE: Improvement realistic with focus
    - AT_RISK: Trajectory misaligned with time
    
    Args:
        attainment_band: Current grade band (1-9)
        target_grade: Target grade (typically 5)
        trend: Performance trend
        activity_per_week: Recent activity sessions
        weeks_remaining: Weeks until exam
        previous_tier: Previous tier assignment
        hysteresis: Anti-flicker state
        
    Returns:
        Tuple of (OutlookTier, reason_string)
    """
    # Support both naming conventions (trend/activity_per_week vs performance_trend/activity_frequency)
    trend = trend or performance_trend
    activity_per_week_val = activity_per_week if activity_per_week is not None else activity_frequency
    if activity_per_week_val is None:
        activity_per_week_val = 0
    hysteresis_val = hysteresis or hysteresis_state

    time_zone = classify_time_zone(weeks_remaining)
    
    # Grade gap analysis
    grade_gap = target_grade - attainment_band
    
    # Insufficient data
    if attainment_band == 0:
        return OutlookTier.AT_RISK, "insufficient_activity"

    # Inactivity check (skip in Risk Management when preserving previous tier - no downgrade)
    in_risk_mgmt = time_zone in (TimeZone.FROZEN, TimeZone.RISK_MANAGEMENT)
    if activity_per_week_val < 2 and not (in_risk_mgmt and previous_tier):
        return OutlookTier.AT_RISK, "low_activity"

    # === TIME ZONE LOGIC ===
    
    if time_zone == TimeZone.FORGIVING:
        # 20+ weeks (Building): Build habits, tolerate gaps. Large gap (>=3) = At Risk.
        if trend == PerformanceTrend.IMPROVING:
            return OutlookTier.ON_TRACK, "improving_trend_early"
        elif grade_gap <= 0:
            return OutlookTier.ON_TRACK, "at_or_above_target"
        elif grade_gap <= 2:
            return OutlookTier.ON_TRACK, "close_to_target_early"
        elif grade_gap == 3:
            return OutlookTier.STRETCH_ACHIEVABLE, "moderate_gap_early"
        else:
            return OutlookTier.AT_RISK, "large_gap_early"
    
    elif time_zone == TimeZone.STANDARD:
        # 12-20 weeks (Strengthening): gap=1 -> Stretch, gap>=2 -> At Risk
        if grade_gap <= 0:
            return OutlookTier.ON_TRACK, "at_or_above_target"
        elif grade_gap == 1:
            return OutlookTier.STRETCH_ACHIEVABLE, "one_below_strengthening"
        elif grade_gap >= 2:
            return OutlookTier.AT_RISK, "significant_gap"
    
    elif time_zone == TimeZone.STRICT:
        # 5-12 weeks: Must be close or improving rapidly
        if grade_gap <= 0:
            return OutlookTier.ON_TRACK, "target_achieved"
        elif grade_gap <= 1:
            return OutlookTier.ON_TRACK, "near_target_late"
        elif grade_gap <= 2 and trend == PerformanceTrend.IMPROVING:
            return OutlookTier.STRETCH_ACHIEVABLE, "improving_late_stage"
        else:
            return OutlookTier.AT_RISK, "insufficient_progress"
    
    else:  # FROZEN / RISK_MANAGEMENT
        # <5 weeks: No downgrades; upgrades allowed with sustained evidence
        if previous_tier:
            # Compute proposed tier from metrics (activity already passed or skipped)
            if grade_gap <= 0 and activity_per_week_val >= 2:
                proposed = OutlookTier.ON_TRACK
            elif grade_gap <= 1 and activity_per_week_val >= 2:
                proposed = OutlookTier.ON_TRACK
            elif grade_gap >= 2 or activity_per_week_val < 2:
                proposed = OutlookTier.AT_RISK
            else:
                proposed = OutlookTier.STRETCH_ACHIEVABLE
            tier_order = {OutlookTier.ON_TRACK: 3, OutlookTier.STRETCH_ACHIEVABLE: 2, OutlookTier.STRETCH_BUT_ACHIEVABLE: 2, OutlookTier.AT_RISK: 1}
            prev_order = tier_order.get(previous_tier, 1)
            prop_order = tier_order.get(proposed, 1)
            if prop_order < prev_order:
                return previous_tier, "frozen"  # No downgrade
            if prop_order > prev_order:
                upgrade_weeks = getattr(hysteresis_val, 'consecutive_upgrade_weeks', 0) if hysteresis_val else 0
                if upgrade_weeks == 0 and hysteresis_val:
                    upgrade_weeks = hysteresis_val.confirmations
                if upgrade_weeks >= 3:
                    return proposed, "met_criteria"
                return previous_tier, "frozen"  # Upgrade blocked without sustained evidence
            return previous_tier, "frozen"
        # Fallback if no previous tier
        if grade_gap <= 1:
            return OutlookTier.ON_TRACK, "final_stage"
        else:
            return OutlookTier.STRETCH_ACHIEVABLE, "final_push"


def update_hysteresis_state(
    current_state: Optional[HysteresisState],
    proposed_tier: OutlookTier,
    current_date: date,
    min_confirmations: int = 2
) -> HysteresisState:
    """
    Update hysteresis state for anti-flicker stability.
    
    Contract: Judgements must be harder to downgrade than upgrade.
    
    Args:
        current_state: Current hysteresis state
        proposed_tier: Newly calculated tier
        current_date: Current date
        min_confirmations: Confirmations needed for change
        
    Returns:
        Updated HysteresisState
    """
    # First time or state from (upgrade_weeks, downgrade_weeks, date) schema
    if current_state is None or current_state.current_tier is None:
        return HysteresisState(
            current_tier=proposed_tier,
            confirmations=1,
            last_change_date=current_date
        )

    # Same tier - reinforce
    if proposed_tier == current_state.current_tier:
        return HysteresisState(
            current_tier=current_state.current_tier,
            confirmations=current_state.confirmations + 1,
            last_change_date=current_state.last_change_date
        )
    
    # Different tier - increment confirmation counter
    new_confirmations = current_state.confirmations + 1
    
    # Check if enough confirmations to change
    if new_confirmations >= min_confirmations:
        return HysteresisState(
            current_tier=proposed_tier,
            confirmations=1,
            last_change_date=current_date
        )
    
    # Not enough confirmations - keep current tier
    return HysteresisState(
        current_tier=current_state.current_tier,
        confirmations=new_confirmations,
        last_change_date=current_state.last_change_date
    )


def confirm_tier_change(
    hysteresis: HysteresisState,
    proposed_tier: OutlookTier,
    is_upgrade: bool
) -> bool:
    """
    Determine if tier change should be confirmed.
    
    Upgrades require fewer confirmations than downgrades.
    
    Args:
        hysteresis: Current hysteresis state
        proposed_tier: Proposed new tier
        is_upgrade: Whether this is an upgrade
        
    Returns:
        True if change should be applied
    """
    UPGRADE_CONFIRMATIONS = 2
    DOWNGRADE_CONFIRMATIONS = 3
    
    needed = UPGRADE_CONFIRMATIONS if is_upgrade else DOWNGRADE_CONFIRMATIONS
    
    return hysteresis.confirmations >= needed


def create_initial_rate_limit_state(week_start: date) -> NotificationRateLimitState:
    """
    Create initial notification rate limit state.
    
    Args:
        week_start: Start of current week
        
    Returns:
        NotificationRateLimitState
    """
    return NotificationRateLimitState(
        subject_notifications_this_week={},
        total_notifications_this_week=0,
        last_notification_date=None,
        week_start=week_start
    )


def apply_notification_rate_limits(
    state: NotificationRateLimitState,
    subject_id: str,
    priority: NotificationPriority,
    current_date: date
) -> Tuple[bool, str]:
    """
    Check if notification should be sent based on rate limits.
    
    Hard limits from contract:
    - Max 1 per subject per week
    - Max 2 total per week
    - Max 1 per day
    - Priority 1 can override weekly limit once
    
    Args:
        state: Current rate limit state
        subject_id: Subject identifier
        priority: Notification priority
        current_date: Current date
        
    Returns:
        Tuple of (should_send: bool, reason: str)
    """
    # Check if new week
    days_since_week_start = (current_date - state.week_start).days
    if days_since_week_start >= 7:
        # Reset for new week
        state = create_initial_rate_limit_state(current_date)
    
    # Daily limit check
    if state.last_notification_date == current_date:
        return False, "daily_limit_exceeded"
    
    # Per-subject weekly limit
    subject_count = state.subject_notifications_this_week.get(subject_id, 0)
    if subject_count >= NOTIFICATION_PER_SUBJECT_WEEKLY_LIMIT:
        if priority == NotificationPriority.PRIORITY_1_URGENT:
            # Priority 1 can override once
            if subject_count >= NOTIFICATION_PER_SUBJECT_WEEKLY_LIMIT + 1:
                return False, "priority1_override_exhausted"
        else:
            return False, "subject_weekly_limit_exceeded"
    
    # Global weekly limit
    if state.total_notifications_this_week >= NOTIFICATION_GLOBAL_WEEKLY_LIMIT:
        if priority == NotificationPriority.PRIORITY_1_URGENT:
            # Priority 1 can override once
            if state.total_notifications_this_week >= NOTIFICATION_GLOBAL_WEEKLY_LIMIT + 1:
                return False, "global_weekly_limit_exceeded"
        else:
            return False, "global_weekly_limit_exceeded"
    
    return True, "allowed"


def should_notify_tier_change(
    old_tier: OutlookTier,
    new_tier: OutlookTier,
    weeks_remaining: int,
    last_tier_change_date: Optional[date],
    current_date: date
) -> bool:
    """
    Determine if tier change should trigger notification.
    
    Suppression rules:
    - Tier downgrade in frozen window (<5 weeks)
    - Tier flicker within 14 days
    
    Args:
        old_tier: Previous tier
        new_tier: New tier
        weeks_remaining: Weeks until exam
        last_tier_change_date: Date of last tier change
        current_date: Current date
        
    Returns:
        True if should notify
    """
    # No change
    if old_tier == new_tier:
        return False
    
    # Frozen window suppression
    if weeks_remaining < 5:
        # Suppress downgrades in frozen window
        tier_order = {
            OutlookTier.ON_TRACK: 3,
            OutlookTier.STRETCH_ACHIEVABLE: 2,
            OutlookTier.AT_RISK: 1
        }
        if tier_order[new_tier] < tier_order[old_tier]:
            return False
    
    # Anti-flicker: suppress if changed recently
    if last_tier_change_date:
        days_since = (current_date - last_tier_change_date).days
        if days_since < 14:
            return False
    
    return True


def should_notify_inactivity_spike(
    activity_last_week: int,
    activity_4_week_avg: float,
    last_notification_date: Optional[date],
    current_date: date
) -> bool:
    """
    Determine if inactivity spike should trigger notification.
    
    Args:
        activity_last_week: Sessions last week
        activity_4_week_avg: Average sessions over 4 weeks
        last_notification_date: Date of last notification
        current_date: Current date
        
    Returns:
        True if should notify
    """
    # Threshold: 50% drop below average
    if activity_4_week_avg > 0:
        drop_ratio = activity_last_week / activity_4_week_avg
        if drop_ratio >= 0.5:
            return False  # Not a significant drop
    
    # Don't spam - at most once per week
    if last_notification_date:
        days_since = (current_date - last_notification_date).days
        if days_since < 7:
            return False
    
    return True


def should_notify_sharp_decline(
    recent_accuracy: float,
    baseline_accuracy: float,
    num_topics_affected: int,
    min_topics: int = 2
) -> bool:
    """
    Determine if sharp performance decline should trigger notification.
    
    Must be sustained across multiple topics.
    
    Args:
        recent_accuracy: Recent accuracy (last 2 weeks)
        baseline_accuracy: Baseline accuracy (prior 6 weeks)
        num_topics_affected: Number of topics with decline
        min_topics: Minimum topics needed for alert
        
    Returns:
        True if should notify
    """
    DECLINE_THRESHOLD = 0.15
    
    decline = baseline_accuracy - recent_accuracy
    
    if decline < DECLINE_THRESHOLD:
        return False
    
    if num_topics_affected < min_topics:
        return False
    
    return True


def should_suppress_weekly_digest(
    subject_id: str,
    last_notification_date: Optional[date],
    current_date: date
) -> bool:
    """
    Determine if weekly digest should be suppressed.
    
    Suppressed if notification sent in last 72 hours.
    
    Args:
        subject_id: Subject identifier
        last_notification_date: Date of last notification
        current_date: Current date
        
    Returns:
        True if should suppress
    """
    if last_notification_date is None:
        return False
    
    days_since = (current_date - last_notification_date).days
    
    return days_since < 3  # 72 hours


def generate_recommendations(
    attainment_band: int,
    target_grade: int,
    trend: PerformanceTrend,
    weeks_remaining: int,
    topic_performances: List[TopicPerformance]
) -> Dict[str, Any]:
    """
    Generate actionable recommendations.
    
    Recommendations adjust aggressiveness based on time zone.
    Never contradict displayed outlook tier.
    
    Args:
        attainment_band: Current grade band
        target_grade: Target grade
        trend: Performance trend
        weeks_remaining: Weeks until exam
        topic_performances: Per-topic performance data
        
    Returns:
        Dictionary with recommendation details
    """
    time_zone = classify_time_zone(weeks_remaining)
    
    # Find weak topics
    weak_topics = [
        t for t in topic_performances
        if t.last_4_weeks_accuracy < 0.65
    ]
    
    # Sort by priority (worst accuracy + recency)
    weak_topics.sort(key=lambda t: (t.last_4_weeks_accuracy, -t.total_attempts))
    
    recommendations = {
        "time_zone": time_zone.value,
        "focus_type": None,
        "priority_topics": [],
        "session_frequency": 0,
        "message": ""
    }
    
    grade_gap = target_grade - attainment_band
    
    # === FORGIVING ZONE ===
    if time_zone == TimeZone.FORGIVING:
        recommendations["focus_type"] = FocusType.CONSISTENCY_ADJUSTMENT.value
        recommendations["session_frequency"] = 3  # 3x per week
        recommendations["priority_topics"] = [t.topic_id for t in weak_topics[:2]]
        recommendations["message"] = "Focus on building consistent habits and addressing weak areas."
    
    # === STANDARD ZONE ===
    elif time_zone == TimeZone.STANDARD:
        if grade_gap > 2:
            recommendations["focus_type"] = FocusType.TOPIC_PRIORITIZATION.value
            recommendations["session_frequency"] = 4  # 4x per week
            recommendations["priority_topics"] = [t.topic_id for t in weak_topics[:3]]
            recommendations["message"] = "Prioritize weak topics and increase session frequency."
        else:
            recommendations["focus_type"] = FocusType.CONFIDENCE_REINFORCEMENT.value
            recommendations["session_frequency"] = 3
            recommendations["priority_topics"] = [t.topic_id for t in weak_topics[:2]]
            recommendations["message"] = "Continue steady progress and reinforce understanding."
    
    # === STRICT ZONE ===
    elif time_zone == TimeZone.STRICT:
        if grade_gap > 1:
            recommendations["focus_type"] = FocusType.TOPIC_PRIORITIZATION.value
            recommendations["session_frequency"] = 5  # Daily
            recommendations["priority_topics"] = [t.topic_id for t in weak_topics[:4]]
            recommendations["message"] = "Intensive focus needed. Daily practice on weak areas."
        else:
            recommendations["focus_type"] = FocusType.CONFIDENCE_REINFORCEMENT.value
            recommendations["session_frequency"] = 4
            recommendations["priority_topics"] = [t.topic_id for t in weak_topics[:2]]
            recommendations["message"] = "Maintain momentum and polish exam technique."
    
    # === FROZEN ZONE ===
    else:  # FROZEN
        recommendations["focus_type"] = FocusType.DAMAGE_CONTROL.value
        recommendations["session_frequency"] = 3  # Don't overwhelm
        recommendations["priority_topics"] = [t.topic_id for t in weak_topics[:2]]
        recommendations["message"] = "Focus on consolidation and maintaining confidence."
    
    return recommendations


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_week_start(current_date: date) -> date:
    """Get the start of the current week (Monday)."""
    days_since_monday = current_date.weekday()
    return current_date - timedelta(days=days_since_monday)
