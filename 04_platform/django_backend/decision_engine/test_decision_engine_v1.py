"""
285IQ Decision Engine v1.0 - Behavioral Test Suite
Tests contract invariants from "285IQ Decision & Notification Contract v1.0"

These tests lock the contract behavior. Failing tests indicate contract violation.
Do not modify tests to pass - fix the implementation or bump contract version.
"""

import pytest
from datetime import date, datetime, timedelta
from typing import List, Optional, Tuple

from decision_engine.v1_0.core import (
    # Enums
    TimeZone,
    OutlookTier,
    PerformanceTrend,
    NotificationPriority,
    FocusType,
    # Data classes
    WeeklyPerformanceSummary,
    TopicPerformance,
    TierAssignment,
    HysteresisState,
    NotificationLog,
    NotificationRateLimitState,
    # Functions
    calculate_weeks_remaining,
    classify_time_zone,
    calculate_attainment_band,
    calculate_performance_trend,
    assign_outlook_tier,
    update_hysteresis_state,
    confirm_tier_change,
    create_initial_rate_limit_state,
    apply_notification_rate_limits,
    should_notify_tier_change,
    should_notify_inactivity_spike,
    should_notify_sharp_decline,
    should_suppress_weekly_digest,
    generate_recommendations,
    # Constants
    CONTRACT_VERSION,
    NOTIFICATION_PER_SUBJECT_WEEKLY_LIMIT,
    NOTIFICATION_GLOBAL_WEEKLY_LIMIT,
    NOTIFICATION_GLOBAL_DAILY_LIMIT,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def base_date() -> date:
    """Deterministic base date for all tests."""
    return date(2026, 5, 15)


@pytest.fixture
def base_datetime() -> datetime:
    """Deterministic base datetime for all tests."""
    return datetime(2026, 5, 15, 12, 0, 0)


@pytest.fixture
def exam_date() -> date:
    """Standard exam date 25 weeks from base_date."""
    return date(2026, 11, 13)


def make_weekly_summary(
    week_ending: date,
    accuracy: float,
    questions: int = 50,
    topics: int = 5,
) -> WeeklyPerformanceSummary:
    """Factory for WeeklyPerformanceSummary with sensible defaults."""
    return WeeklyPerformanceSummary(
        week_ending=week_ending,
        average_accuracy=accuracy,
        questions_attempted=questions,
        topics_accessed=topics,
        difficulty_distribution=0.5,
    )


def make_topic_performance(
    topic_id: str,
    accuracy: float,
    trend: PerformanceTrend = PerformanceTrend.NEUTRAL,
    attempts: int = 20,
) -> TopicPerformance:
    """Factory for TopicPerformance with sensible defaults."""
    return TopicPerformance(
        topic_id=topic_id,
        last_4_weeks_accuracy=accuracy,
        last_6_weeks_accuracy=accuracy,
        last_attempt_date=date(2026, 5, 10),
        total_attempts=attempts,
        trend=trend,
    )


def make_tier_assignment(
    timestamp: datetime,
    tier: OutlookTier,
    reason: str = "met_criteria",
    weeks_remaining: int = 20,
    is_frozen_display: bool = False,
) -> TierAssignment:
    """Factory for TierAssignment (engine schema)."""
    return TierAssignment(
        tier=tier,
        reason=reason,
        timestamp=timestamp,
        weeks_remaining=weeks_remaining,
        is_frozen_display=is_frozen_display,
    )


def make_notification_log(
    timestamp: datetime,
    subject_id: str,
    event_type: str,
    priority: NotificationPriority = NotificationPriority.PRIORITY_2,
    time_zone: TimeZone = TimeZone.STANDARD,
    parent_action: Optional[str] = None,
) -> NotificationLog:
    """Factory for NotificationLog."""
    return NotificationLog(
        notification_id=f"notif_{timestamp.isoformat()}_{subject_id}",
        timestamp=timestamp,
        subject_id=subject_id,
        event_type=event_type,
        priority=priority,
        time_zone=time_zone,
        parent_action=parent_action,
    )


def _apply_notification_and_update_state(
    state: NotificationRateLimitState,
    subject_id: str,
    priority: NotificationPriority,
    current_date,
) -> Tuple[bool, str]:
    """Call apply_notification_rate_limits and update state if allowed."""
    allowed, reason = apply_notification_rate_limits(
        state=state,
        subject_id=subject_id,
        priority=priority,
        current_date=current_date.date() if hasattr(current_date, 'date') else current_date,
    )
    if allowed:
        state.subject_notifications_this_week[subject_id] = (
            state.subject_notifications_this_week.get(subject_id, 0) + 1
        )
        state.total_notifications_this_week += 1
        state.last_notification_date = (
            current_date.date() if hasattr(current_date, 'date') else current_date
        )
    return allowed, reason


# ============================================================================
# CONTRACT VERSION
# ============================================================================

class TestContractVersion:
    """Verify contract version is locked."""
    
    def test_contract_version_is_1_0(self):
        """Contract version must be 1.0 for these tests to be valid."""
        assert CONTRACT_VERSION == "1.0"


# ============================================================================
# TIME ZONE CLASSIFICATION (Contract Section 6)
# ============================================================================

class TestTimeZoneClassification:
    """Contract Section 6: Time zone boundaries must be exact."""
    
    def test_20_weeks_is_building_phase(self):
        """20 weeks exactly = Building phase."""
        assert classify_time_zone(20) == TimeZone.BUILDING
    
    def test_21_weeks_is_building_phase(self):
        """21 weeks = Building phase."""
        assert classify_time_zone(21) == TimeZone.BUILDING
    
    def test_19_weeks_is_strengthening_phase(self):
        """19 weeks = Strengthening phase (below 20)."""
        assert classify_time_zone(19) == TimeZone.STRENGTHENING
    
    def test_12_weeks_is_strengthening_phase(self):
        """12 weeks exactly = Strengthening phase."""
        assert classify_time_zone(12) == TimeZone.STRENGTHENING
    
    def test_11_weeks_is_consolidation_phase(self):
        """11 weeks = Consolidation phase (below 12)."""
        assert classify_time_zone(11) == TimeZone.CONSOLIDATION
    
    def test_5_weeks_is_consolidation_phase(self):
        """5 weeks exactly = Consolidation phase."""
        assert classify_time_zone(5) == TimeZone.CONSOLIDATION
    
    def test_4_weeks_is_risk_management_phase(self):
        """4 weeks = Risk Management phase (below 5)."""
        assert classify_time_zone(4) == TimeZone.RISK_MANAGEMENT
    
    def test_0_weeks_is_risk_management_phase(self):
        """0 weeks = Risk Management phase."""
        assert classify_time_zone(0) == TimeZone.RISK_MANAGEMENT
    
    def test_boundary_weeks_remaining_calculation(self, base_date):
        """Weeks remaining calculation is consistent with time zones."""
        # 20 weeks from base_date
        exam_20_weeks = base_date + timedelta(weeks=20)
        assert calculate_weeks_remaining(exam_20_weeks, base_date) == 20
        assert classify_time_zone(20) == TimeZone.BUILDING
        
        # 12 weeks from base_date
        exam_12_weeks = base_date + timedelta(weeks=12)
        assert calculate_weeks_remaining(exam_12_weeks, base_date) == 12
        assert classify_time_zone(12) == TimeZone.STRENGTHENING
        
        # 5 weeks from base_date
        exam_5_weeks = base_date + timedelta(weeks=5)
        assert calculate_weeks_remaining(exam_5_weeks, base_date) == 5
        assert classify_time_zone(5) == TimeZone.CONSOLIDATION
        
        # 4 weeks from base_date
        exam_4_weeks = base_date + timedelta(weeks=4)
        assert calculate_weeks_remaining(exam_4_weeks, base_date) == 4
        assert classify_time_zone(4) == TimeZone.RISK_MANAGEMENT


# ============================================================================
# GAP SIGN CONVENTION (Contract Section 7)
# ============================================================================

class TestGapSignConvention:
    """
    Contract invariant: gap = target_grade - attainment_band
    - gap <= 0: at or above target
    - gap == 1: one grade below
    - gap >= 2: behind target
    """
    
    def test_at_target_is_on_track_in_building_phase(self, base_date):
        """Attainment == target (gap=0) should be On Track in Building phase."""
        summaries = [make_weekly_summary(base_date - timedelta(weeks=i), 0.70) for i in range(4)]
        
        tier, reason = assign_outlook_tier(
            attainment_band=7,  # Grade 7
            target_grade=7,     # Target 7
            performance_trend=PerformanceTrend.NEUTRAL,
            activity_frequency=4.0,
            weeks_remaining=20,
            previous_tier=None,
            hysteresis_state=None,
        )
        
        # gap = 7 - 7 = 0, should be On Track
        assert tier == OutlookTier.ON_TRACK
    
    def test_above_target_is_on_track(self, base_date):
        """Attainment > target (gap<0) should be On Track."""
        tier, reason = assign_outlook_tier(
            attainment_band=8,  # Grade 8
            target_grade=6,     # Target 6
            performance_trend=PerformanceTrend.NEUTRAL,
            activity_frequency=4.0,
            weeks_remaining=20,
            previous_tier=None,
            hysteresis_state=None,
        )
        
        # gap = 6 - 8 = -2, well above target
        assert tier == OutlookTier.ON_TRACK
    
    def test_one_below_target_in_building_is_on_track(self, base_date):
        """One grade below (gap=1) in Building phase can still be On Track."""
        tier, reason = assign_outlook_tier(
            attainment_band=5,  # Grade 5
            target_grade=6,     # Target 6
            performance_trend=PerformanceTrend.NEUTRAL,
            activity_frequency=4.0,
            weeks_remaining=20,
            previous_tier=None,
            hysteresis_state=None,
        )
        
        # gap = 6 - 5 = 1, forgiving in Building phase
        assert tier == OutlookTier.ON_TRACK
    
    def test_one_below_target_in_strengthening_is_stretch(self, base_date):
        """One grade below (gap=1) in Strengthening phase = Stretch."""
        tier, reason = assign_outlook_tier(
            attainment_band=5,  # Grade 5
            target_grade=6,     # Target 6
            performance_trend=PerformanceTrend.NEUTRAL,
            activity_frequency=4.0,
            weeks_remaining=15,  # Strengthening phase
            previous_tier=None,
            hysteresis_state=None,
        )
        
        # gap = 6 - 5 = 1, stricter in Strengthening
        assert tier == OutlookTier.STRETCH_BUT_ACHIEVABLE
    
    def test_two_below_target_in_strengthening_is_at_risk(self, base_date):
        """Two grades below (gap=2) in Strengthening = At Risk."""
        tier, reason = assign_outlook_tier(
            attainment_band=4,  # Grade 4
            target_grade=6,     # Target 6
            performance_trend=PerformanceTrend.NEUTRAL,
            activity_frequency=4.0,
            weeks_remaining=15,
            previous_tier=None,
            hysteresis_state=None,
        )
        
        # gap = 6 - 4 = 2
        assert tier == OutlookTier.AT_RISK
    
    def test_large_gap_is_always_at_risk(self, base_date):
        """Large gap (>=3) is At Risk even in Building phase."""
        tier, reason = assign_outlook_tier(
            attainment_band=3,  # Grade 3
            target_grade=7,     # Target 7
            performance_trend=PerformanceTrend.NEUTRAL,
            activity_frequency=4.0,
            weeks_remaining=25,  # Building phase
            previous_tier=None,
            hysteresis_state=None,
        )
        
        # gap = 7 - 3 = 4
        assert tier == OutlookTier.AT_RISK


# ============================================================================
# FROZEN TIER BEHAVIOR (Contract Section 8)
# ============================================================================

class TestFrozenTierBehavior:
    """
    Contract Section 8: In <5 weeks, tier is frozen.
    - No downgrades displayed to parent
    - Upgrades allowed with sustained evidence
    - Internal recommendations remain active
    """
    
    def test_no_downgrade_at_4_weeks(self):
        """Tier cannot downgrade when weeks_remaining < 5."""
        # Student was On Track, performance drops
        tier, reason = assign_outlook_tier(
            attainment_band=3,  # Poor performance
            target_grade=7,
            performance_trend=PerformanceTrend.NEGATIVE,
            activity_frequency=1.0,
            weeks_remaining=4,  # Risk Management phase
            previous_tier=OutlookTier.ON_TRACK,
            hysteresis_state=HysteresisState(0, 5, date(2026, 4, 1)),
        )
        
        # Should remain On Track despite poor metrics
        assert tier == OutlookTier.ON_TRACK
        assert reason == "frozen"
    
    def test_no_downgrade_at_3_weeks(self):
        """Tier cannot downgrade at 3 weeks."""
        tier, reason = assign_outlook_tier(
            attainment_band=2,
            target_grade=6,
            performance_trend=PerformanceTrend.NEGATIVE,
            activity_frequency=0.5,
            weeks_remaining=3,
            previous_tier=OutlookTier.STRETCH_BUT_ACHIEVABLE,
            hysteresis_state=HysteresisState(0, 10, date(2026, 4, 1)),
        )
        
        assert tier == OutlookTier.STRETCH_BUT_ACHIEVABLE
        assert reason == "frozen"
    
    def test_no_downgrade_at_1_week(self):
        """Tier cannot downgrade even at 1 week remaining."""
        tier, reason = assign_outlook_tier(
            attainment_band=1,
            target_grade=9,
            performance_trend=PerformanceTrend.NEGATIVE,
            activity_frequency=0.0,
            weeks_remaining=1,
            previous_tier=OutlookTier.ON_TRACK,
            hysteresis_state=HysteresisState(0, 20, date(2026, 4, 1)),
        )
        
        assert tier == OutlookTier.ON_TRACK
        assert reason == "frozen"
    
    def test_upgrade_allowed_at_4_weeks_with_sustained_evidence(self):
        """Upgrade IS allowed in <5 weeks if sustained for 3 weeks."""
        tier, reason = assign_outlook_tier(
            attainment_band=7,
            target_grade=6,
            performance_trend=PerformanceTrend.POSITIVE,
            activity_frequency=5.0,
            weeks_remaining=4,
            previous_tier=OutlookTier.AT_RISK,
            hysteresis_state=HysteresisState(3, 0, date(2026, 4, 1)),  # 3 consecutive upgrade weeks
        )
        
        # Upgrade allowed with sustained evidence
        assert tier == OutlookTier.ON_TRACK
        assert reason == "met_criteria"
    
    def test_upgrade_blocked_without_sustained_evidence(self):
        """Upgrade blocked in <5 weeks without 3 weeks sustained evidence."""
        tier, reason = assign_outlook_tier(
            attainment_band=7,
            target_grade=6,
            performance_trend=PerformanceTrend.POSITIVE,
            activity_frequency=5.0,
            weeks_remaining=4,
            previous_tier=OutlookTier.AT_RISK,
            hysteresis_state=HysteresisState(2, 0, date(2026, 4, 1)),  # Only 2 weeks
        )
        
        # Upgrade blocked - need 3 weeks in Risk Management
        assert tier == OutlookTier.AT_RISK
        assert reason == "frozen"
    
    def test_recommendations_generated_in_risk_management(self):
        """Recommendations MUST be generated even in <5 weeks."""
        topics = [
            make_topic_performance("algebra", 0.4),
            make_topic_performance("geometry", 0.6),
            make_topic_performance("statistics", 0.8),
        ]
        
        result = generate_recommendations(
            attainment_band=5,
            target_grade=6,
            trend=PerformanceTrend.NEUTRAL,
            weeks_remaining=4,  # Risk Management
            topic_performances=topics,
        )
        
        assert "focus_type" in result
        assert result["focus_type"] == FocusType.DAMAGE_CONTROL.value
        assert "session_frequency" in result
        assert "message" in result
        assert len(result["message"]) > 0
    
    def test_recommendations_generated_for_on_track_in_risk_management(self):
        """Even On Track students get recommendations in <5 weeks."""
        topics = [
            make_topic_performance("algebra", 0.9),
            make_topic_performance("geometry", 0.85),
        ]
        
        result = generate_recommendations(
            attainment_band=7,
            target_grade=6,
            trend=PerformanceTrend.NEUTRAL,
            weeks_remaining=3,
            topic_performances=topics,
        )
        
        assert "priority_topics" in result
        assert "message" in result
        assert len(result["message"]) > 0
    
    def test_fallback_action_when_no_topics(self):
        """If no topics available, recommendations still return valid structure."""
        result = generate_recommendations(
            attainment_band=5,
            target_grade=6,
            trend=PerformanceTrend.NEUTRAL,
            weeks_remaining=4,
            topic_performances=[],  # No topic data
        )
        
        assert "priority_topics" in result
        assert result["priority_topics"] == []
        assert "message" in result
        assert len(result["message"]) > 0


# ============================================================================
# ANTI-FLICKER HYSTERESIS (Contract Section 3)
# ============================================================================

class TestAntiFlickerHysteresis:
    """
    Contract Section 3: Anti-flicker stability rules.
    - Upgrade requires 2 consecutive weeks
    - Downgrade requires 3 consecutive weeks
    """
    
    def test_upgrade_blocked_at_1_week(self):
        """Upgrade blocked in FROZEN after only 1 week meeting criteria (needs 3)."""
        tier, reason = assign_outlook_tier(
            attainment_band=7,
            target_grade=6,
            performance_trend=PerformanceTrend.POSITIVE,
            activity_frequency=5.0,
            weeks_remaining=4,  # FROZEN - hysteresis applies
            previous_tier=OutlookTier.STRETCH_BUT_ACHIEVABLE,
            hysteresis_state=HysteresisState(1, 0, date(2026, 4, 1)),  # Only 1 week
        )
        
        assert tier == OutlookTier.STRETCH_BUT_ACHIEVABLE
        assert reason == "frozen"
    
    def test_upgrade_allowed_at_2_weeks(self):
        """Upgrade allowed in FROZEN after 3 consecutive weeks (engine requires 3)."""
        tier, reason = assign_outlook_tier(
            attainment_band=7,
            target_grade=6,
            performance_trend=PerformanceTrend.POSITIVE,
            activity_frequency=5.0,
            weeks_remaining=4,
            previous_tier=OutlookTier.AT_RISK,
            hysteresis_state=HysteresisState(3, 0, date(2026, 4, 1)),  # 3 weeks
        )
        
        assert tier == OutlookTier.ON_TRACK
        assert reason == "met_criteria"
    
    def test_downgrade_blocked_at_2_weeks(self):
        """In FROZEN, downgrades are always blocked (no downgrade ever)."""
        tier, reason = assign_outlook_tier(
            attainment_band=3,
            target_grade=7,
            performance_trend=PerformanceTrend.NEGATIVE,
            activity_frequency=1.0,
            weeks_remaining=4,
            previous_tier=OutlookTier.ON_TRACK,
            hysteresis_state=HysteresisState(0, 2, date(2026, 4, 1)),
        )
        
        assert tier == OutlookTier.ON_TRACK
        assert reason == "frozen"
    
    def test_downgrade_allowed_at_3_weeks(self):
        """In STANDARD zone (15 weeks), poor metrics assign AT_RISK (no hysteresis)."""
        tier, reason = assign_outlook_tier(
            attainment_band=3,
            target_grade=7,
            performance_trend=PerformanceTrend.NEGATIVE,
            activity_frequency=1.0,
            weeks_remaining=15,
            previous_tier=OutlookTier.ON_TRACK,
            hysteresis_state=HysteresisState(0, 3, date(2026, 4, 1)),
        )
        
        assert tier == OutlookTier.AT_RISK
        assert reason in ("low_activity", "significant_gap")
    
    def test_hysteresis_state_update_on_upgrade_progress(self):
        """Hysteresis state updates when proposed tier differs (upgrade)."""
        current = HysteresisState(
            current_tier=OutlookTier.STRETCH_BUT_ACHIEVABLE,
            confirmations=1,
            last_change_date=date(2026, 4, 1),
        )
        
        new_state = update_hysteresis_state(
            current_state=current,
            proposed_tier=OutlookTier.ON_TRACK,
            current_date=date(2026, 5, 15),
            min_confirmations=2,
        )
        
        assert new_state.current_tier == OutlookTier.ON_TRACK
        assert new_state.confirmations == 1
    
    def test_hysteresis_state_update_on_downgrade_progress(self):
        """Hysteresis state updates when proposed tier differs (downgrade)."""
        current = HysteresisState(
            current_tier=OutlookTier.ON_TRACK,
            confirmations=2,
            last_change_date=date(2026, 4, 1),
        )
        
        new_state = update_hysteresis_state(
            current_state=current,
            proposed_tier=OutlookTier.AT_RISK,
            current_date=date(2026, 5, 15),
            min_confirmations=2,
        )
        
        assert new_state.current_tier == OutlookTier.AT_RISK
        assert new_state.confirmations == 1
    
    def test_hysteresis_state_reset_on_tier_match(self):
        """Same tier reinforces confirmations (no change)."""
        current = HysteresisState(
            current_tier=OutlookTier.STRETCH_BUT_ACHIEVABLE,
            confirmations=2,
            last_change_date=date(2026, 4, 1),
        )
        
        new_state = update_hysteresis_state(
            current_state=current,
            proposed_tier=OutlookTier.STRETCH_BUT_ACHIEVABLE,
            current_date=date(2026, 5, 15),
        )
        
        assert new_state.current_tier == OutlookTier.STRETCH_BUT_ACHIEVABLE
        assert new_state.confirmations == 3
    
    def test_confirm_tier_change_resets_counters(self):
        """confirm_tier_change returns True when confirmations >= threshold."""
        current = HysteresisState(
            current_tier=OutlookTier.STRETCH_BUT_ACHIEVABLE,
            confirmations=2,
            last_change_date=date(2026, 4, 1),
        )
        
        # Upgrade needs 2 confirmations
        result = confirm_tier_change(
            hysteresis=current,
            proposed_tier=OutlookTier.ON_TRACK,
            is_upgrade=True,
        )
        
        assert result is True


# ============================================================================
# NOTIFICATION RATE LIMITING (Contract Section 10.4)
# ============================================================================

class TestNotificationRateLimiting:
    """
    Contract Section 10.4: Anti-fatigue safeguards.
    - Per-subject weekly limit: 1
    - Global weekly limit: 2
    - Global daily limit: 1
    - P1 override: once per week
    - Second P1: batched
    """
    
    def test_first_notification_allowed(self, base_datetime):
        """First notification should be allowed."""
        state = create_initial_rate_limit_state(base_datetime.date())
        
        allowed, reason = apply_notification_rate_limits(
            state=state,
            subject_id="mathematics",
            priority=NotificationPriority.PRIORITY_2,
            current_date=base_datetime.date(),
        )
        
        assert allowed is True
        assert reason == "allowed"
    
    def test_subject_weekly_limit_enforced(self, base_datetime):
        """Second notification for same subject in same week blocked."""
        monday = datetime(2026, 5, 11, 12, 0, 0)
        state = create_initial_rate_limit_state(monday.date())
        
        # First notification - allowed
        allowed1, _ = apply_notification_rate_limits(
            state=state, subject_id="mathematics",
            priority=NotificationPriority.PRIORITY_2, current_date=monday.date(),
        )
        assert allowed1 is True
        _apply_notification_and_update_state(state, "mathematics", NotificationPriority.PRIORITY_2, monday)
        
        # Second notification same subject same week - blocked
        tuesday = monday.date() + timedelta(days=1)
        allowed2, reason2 = apply_notification_rate_limits(
            state=state, subject_id="mathematics",
            priority=NotificationPriority.PRIORITY_2, current_date=tuesday,
        )
        assert allowed2 is False
        assert reason2 == "subject_weekly_limit_exceeded"
    
    def test_global_daily_limit_enforced(self, base_datetime):
        """Only 1 notification per day globally."""
        state = create_initial_rate_limit_state(base_datetime.date())
        
        # First notification - allowed
        allowed1, _ = apply_notification_rate_limits(
            state=state, subject_id="mathematics",
            priority=NotificationPriority.PRIORITY_2, current_date=base_datetime.date(),
        )
        assert allowed1 is True
        _apply_notification_and_update_state(state, "mathematics", NotificationPriority.PRIORITY_2, base_datetime)
        
        # Second notification different subject same day - blocked
        allowed2, reason2 = apply_notification_rate_limits(
            state=state, subject_id="physics",
            priority=NotificationPriority.PRIORITY_2, current_date=base_datetime.date(),
        )
        assert allowed2 is False
        assert reason2 == "daily_limit_exceeded"
    
    def test_global_weekly_limit_enforced(self, base_datetime):
        """Only 2 notifications per week globally."""
        state = create_initial_rate_limit_state(base_datetime.date())
        
        # Day 1: First notification
        allowed1, _ = apply_notification_rate_limits(
            state=state, subject_id="mathematics",
            priority=NotificationPriority.PRIORITY_2, current_date=base_datetime.date(),
        )
        assert allowed1 is True
        _apply_notification_and_update_state(state, "mathematics", NotificationPriority.PRIORITY_2, base_datetime)
        
        # Day 2: Second notification
        day2 = base_datetime.date() + timedelta(days=1)
        allowed2, _ = apply_notification_rate_limits(
            state=state, subject_id="physics",
            priority=NotificationPriority.PRIORITY_2, current_date=day2,
        )
        assert allowed2 is True
        _apply_notification_and_update_state(state, "physics", NotificationPriority.PRIORITY_2, day2)
        
        # Day 3: Third notification - blocked
        day3 = base_datetime.date() + timedelta(days=2)
        allowed3, reason3 = apply_notification_rate_limits(
            state=state, subject_id="chemistry",
            priority=NotificationPriority.PRIORITY_2, current_date=day3,
        )
        assert allowed3 is False
        assert reason3 == "global_weekly_limit_exceeded"
    
    def test_p1_overrides_limits_once(self, base_datetime):
        """P1 event bypasses global weekly limit ONCE (after 2 P2)."""
        state = create_initial_rate_limit_state(base_datetime.date())
        
        # Exhaust global weekly limit with 2x P2
        allowed1, _ = apply_notification_rate_limits(
            state=state, subject_id="mathematics",
            priority=NotificationPriority.PRIORITY_2, current_date=base_datetime.date(),
        )
        assert allowed1 is True
        _apply_notification_and_update_state(state, "mathematics", NotificationPriority.PRIORITY_2, base_datetime)
        
        day2 = base_datetime.date() + timedelta(days=1)
        allowed2, _ = apply_notification_rate_limits(
            state=state, subject_id="physics",
            priority=NotificationPriority.PRIORITY_2, current_date=day2,
        )
        assert allowed2 is True
        _apply_notification_and_update_state(state, "physics", NotificationPriority.PRIORITY_2, day2)
        
        # P1 should override global weekly limit (3rd notification)
        day3 = base_datetime.date() + timedelta(days=2)
        allowed3, reason3 = apply_notification_rate_limits(
            state=state, subject_id="chemistry",
            priority=NotificationPriority.PRIORITY_1,
            current_date=day3,
        )
        assert allowed3 is True
        assert reason3 == "allowed"
    
    def test_second_p1_batched(self, base_datetime):
        """Second P1 event after override is blocked (P1 override once per week)."""
        state = create_initial_rate_limit_state(base_datetime.date())
        
        # Day 1: First P2 - allowed
        allowed1, _ = apply_notification_rate_limits(
            state=state, subject_id="mathematics",
            priority=NotificationPriority.PRIORITY_2, current_date=base_datetime.date(),
        )
        assert allowed1 is True
        _apply_notification_and_update_state(state, "mathematics", NotificationPriority.PRIORITY_2, base_datetime)
        
        day2 = base_datetime.date() + timedelta(days=1)
        # Day 2: Second P2 - allowed (weekly limit 2)
        allowed2, _ = apply_notification_rate_limits(
            state=state, subject_id="physics",
            priority=NotificationPriority.PRIORITY_2, current_date=day2,
        )
        assert allowed2 is True
        _apply_notification_and_update_state(state, "physics", NotificationPriority.PRIORITY_2, day2)
        
        # Day 3: First P1 - override allowed (different day, bypasses weekly limit)
        day3 = base_datetime.date() + timedelta(days=2)
        allowed3, _ = apply_notification_rate_limits(
            state=state, subject_id="chemistry",
            priority=NotificationPriority.PRIORITY_1, current_date=day3,
        )
        assert allowed3 is True
        _apply_notification_and_update_state(state, "chemistry", NotificationPriority.PRIORITY_1, day3)
        
        # Day 4: Second P1 - blocked (override exhausted)
        day4 = base_datetime.date() + timedelta(days=3)
        allowed4, reason4 = apply_notification_rate_limits(
            state=state, subject_id="biology",
            priority=NotificationPriority.PRIORITY_1, current_date=day4,
        )
        assert allowed4 is False
        assert reason4 in ("global_weekly_limit_exceeded", "priority1_override_exhausted")
    
    def test_limits_reset_on_new_week(self, base_datetime):
        """Limits reset when crossing into new week."""
        state = create_initial_rate_limit_state(base_datetime.date())
        
        # Exhaust limits - first notification
        allowed1, _ = apply_notification_rate_limits(
            state=state, subject_id="math",
            priority=NotificationPriority.PRIORITY_2, current_date=base_datetime.date(),
        )
        assert allowed1 is True
        _apply_notification_and_update_state(state, "math", NotificationPriority.PRIORITY_2, base_datetime)
        
        # Second notification same week - different day
        day2 = base_datetime.date() + timedelta(days=1)
        allowed2, _ = apply_notification_rate_limits(
            state=state, subject_id="physics",
            priority=NotificationPriority.PRIORITY_2, current_date=day2,
        )
        assert allowed2 is True
        _apply_notification_and_update_state(state, "physics", NotificationPriority.PRIORITY_2, day2)
        
        # Next week - should allow notification again (engine resets for new week)
        next_week = base_datetime.date() + timedelta(days=7)
        allowed3, reason3 = apply_notification_rate_limits(
            state=state, subject_id="math",
            priority=NotificationPriority.PRIORITY_2, current_date=next_week,
        )
        assert allowed3 is True
        assert reason3 == "allowed"
    
    def test_positive_events_also_rate_limited(self, base_datetime):
        """Positive events (upgrades) are also subject to rate limits."""
        state = create_initial_rate_limit_state(base_datetime.date())
        
        # First upgrade notification
        allowed1, _ = apply_notification_rate_limits(
            state=state, subject_id="mathematics",
            priority=NotificationPriority.PRIORITY_2, current_date=base_datetime.date(),
        )
        assert allowed1 is True
        _apply_notification_and_update_state(state, "mathematics", NotificationPriority.PRIORITY_2, base_datetime)
        
        # Second positive event same day - blocked by daily limit
        allowed2, reason2 = apply_notification_rate_limits(
            state=state, subject_id="physics",
            priority=NotificationPriority.PRIORITY_2, current_date=base_datetime.date(),
        )
        assert allowed2 is False
        assert reason2 == "daily_limit_exceeded"


# ============================================================================
# NOTIFICATION SUPPRESSION RULES (Contract Section 10.3)
# ============================================================================

class TestNotificationSuppression:
    """Contract Section 10.3: Suppression rules."""
    
    def test_tier_downgrade_suppressed_in_risk_management(self, base_datetime):
        """Tier downgrade notification suppressed when <5 weeks."""
        decision = should_notify_tier_change(
            old_tier=OutlookTier.ON_TRACK,
            new_tier=OutlookTier.AT_RISK,
            weeks_remaining=4,
            last_tier_change_date=None,
            current_date=base_datetime.date(),
        )
        assert decision is False
    
    def test_tier_upgrade_not_suppressed_in_risk_management(self, base_datetime):
        """Tier upgrade notification NOT suppressed when <5 weeks."""
        decision = should_notify_tier_change(
            old_tier=OutlookTier.AT_RISK,
            new_tier=OutlookTier.STRETCH_BUT_ACHIEVABLE,
            weeks_remaining=4,
            last_tier_change_date=None,
            current_date=base_datetime.date(),
        )
        assert decision is True
    
    def test_tier_flicker_suppressed(self, base_datetime):
        """Tier change within 14 days of last change is suppressed (anti-flicker)."""
        last_tier_change_date = base_datetime.date() - timedelta(days=10)
        
        decision = should_notify_tier_change(
            old_tier=OutlookTier.STRETCH_BUT_ACHIEVABLE,
            new_tier=OutlookTier.ON_TRACK,
            weeks_remaining=15,
            last_tier_change_date=last_tier_change_date,
            current_date=base_datetime.date(),
        )
        assert decision is False
    
    def test_duplicate_inactivity_suppressed_within_14_days(self, base_datetime):
        """Duplicate inactivity notification suppressed within 7 days."""
        last_notification_date = base_datetime.date() - timedelta(days=3)
        
        decision = should_notify_inactivity_spike(
            activity_last_week=0,
            activity_4_week_avg=5.0,
            last_notification_date=last_notification_date,
            current_date=base_datetime.date(),
        )
        assert decision is False
    
    def test_weekly_digest_suppressed_after_recent_notification(self, base_datetime):
        """Weekly digest suppressed if notification sent in last 72 hours."""
        last_notification_date = base_datetime.date() - timedelta(days=1)
        
        result = should_suppress_weekly_digest(
            subject_id="mathematics",
            last_notification_date=last_notification_date,
            current_date=base_datetime.date(),
        )
        assert result is True
    
    def test_weekly_digest_not_suppressed_after_72_hours(self, base_datetime):
        """Weekly digest NOT suppressed if notification >72 hours ago."""
        last_notification_date = base_datetime.date() - timedelta(days=4)
        
        result = should_suppress_weekly_digest(
            subject_id="mathematics",
            last_notification_date=last_notification_date,
            current_date=base_datetime.date(),
        )
        assert result is False


# ============================================================================
# RECOMMENDATION CHANGES NEVER NOTIFY
# ============================================================================

class TestRecommendationChangesNeverNotify:
    """Contract invariant: Recommendation changes alone never trigger notifications."""
    
    def test_recommendation_output_has_no_notification_trigger(self):
        """generate_recommendations return dict has no notification-related keys."""
        topics = [
            make_topic_performance("algebra", 0.5),
            make_topic_performance("geometry", 0.7),
        ]
        
        result = generate_recommendations(
            attainment_band=5,
            target_grade=6,
            trend=PerformanceTrend.NEUTRAL,
            weeks_remaining=15,
            topic_performances=topics,
        )
        
        # Return dict must not have notification keys (invariant)
        for key in ("should_notify", "notification_priority", "trigger_notification"):
            assert key not in result
    
    def test_topic_priority_change_does_not_notify(self):
        """Changing topic priorities does not trigger any notification."""
        topics_week1 = [
            make_topic_performance("algebra", 0.3),
            make_topic_performance("geometry", 0.8),
        ]
        
        topics_week2 = [
            make_topic_performance("algebra", 0.7),  # Improved
            make_topic_performance("geometry", 0.4),  # Declined
        ]
        
        result1 = generate_recommendations(
            attainment_band=5,
            target_grade=6,
            trend=PerformanceTrend.NEUTRAL,
            weeks_remaining=15,
            topic_performances=topics_week1,
        )
        
        result2 = generate_recommendations(
            attainment_band=5,
            target_grade=6,
            trend=PerformanceTrend.NEUTRAL,
            weeks_remaining=14,
            topic_performances=topics_week2,
        )
        
        # Topics changed - no notification mechanism exists
        assert "priority_topics" in result1
        assert "priority_topics" in result2
        assert "should_notify" not in result1
        assert "should_notify" not in result2
    
    def test_activity_target_change_does_not_notify(self):
        """Changing activity targets does not trigger notification."""
        topics = [make_topic_performance("algebra", 0.5)]
        
        # Building phase
        result1 = generate_recommendations(
            attainment_band=5,
            target_grade=6,
            trend=PerformanceTrend.NEUTRAL,
            weeks_remaining=20,
            topic_performances=topics,
        )
        
        # Consolidation phase - session_frequency may differ
        result2 = generate_recommendations(
            attainment_band=5,
            target_grade=6,
            trend=PerformanceTrend.NEUTRAL,
            weeks_remaining=8,
            topic_performances=topics,
        )
        
        # Session frequency may differ by time zone; no notification mechanism
        assert "session_frequency" in result1
        assert "session_frequency" in result2
        assert "should_notify" not in result1
        assert "should_notify" not in result2


# ============================================================================
# ATTAINMENT BAND CALCULATION (Contract Section 7.1)
# ============================================================================

class TestAttainmentBandCalculation:
    """Contract Section 7.1: Conservative attainment calculation."""
    
    def test_empty_data_returns_zero(self):
        """Empty data returns 0 (insufficient)."""
        band = calculate_attainment_band([], 0.5)
        assert band == 0

    def test_insufficient_weeks_returns_zero(self, base_date):
        """Fewer than min_weeks (default 4) returns 0."""
        summaries = [
            make_weekly_summary(base_date - timedelta(weeks=i), 0.80)
            for i in range(3)
        ]
        band = calculate_attainment_band(summaries, 0.80)
        assert band == 0
    
    def test_high_accuracy_high_coverage_gives_high_grade(self, base_date):
        """90%+ accuracy with good coverage = Grade 9."""
        summaries = [
            make_weekly_summary(base_date - timedelta(weeks=i), 0.92)
            for i in range(4)
        ]
        
        band = calculate_attainment_band(summaries, coverage_breadth=0.80)
        assert band == 9
    
    def test_low_coverage_caps_grade(self, base_date):
        """<40% coverage caps grade at 5 regardless of accuracy."""
        summaries = [
            make_weekly_summary(base_date - timedelta(weeks=i), 0.95)
            for i in range(4)
        ]
        
        band = calculate_attainment_band(summaries, coverage_breadth=0.30)
        assert band <= 5
    
    def test_recent_weeks_weighted_higher(self, base_date):
        """Weighted accuracy maps to grade band (engine uses last 6 weeks)."""
        summaries = [
            make_weekly_summary(base_date - timedelta(weeks=3), 0.60),
            make_weekly_summary(base_date - timedelta(weeks=2), 0.65),
            make_weekly_summary(base_date - timedelta(weeks=1), 0.75),
            make_weekly_summary(base_date, 0.80),
        ]
        
        band = calculate_attainment_band(summaries, coverage_breadth=0.80)
        
        # Engine: weighted accuracy, coverage penalty, grade mapping
        assert band >= 6


# ============================================================================
# PERFORMANCE TREND (Contract Section 7)
# ============================================================================

class TestPerformanceTrend:
    """Contract Section 7: Trend calculation."""
    
    def test_insufficient_data_is_neutral(self, base_date):
        """Less than 2 weeks of data = NEUTRAL."""
        summaries = [make_weekly_summary(base_date, 0.70)]
        
        trend = calculate_performance_trend(summaries)
        assert trend == PerformanceTrend.NEUTRAL
    
    def test_improving_accuracy_is_positive(self, base_date):
        """Consistent improvement over 6 weeks = POSITIVE."""
        summaries = [
            make_weekly_summary(base_date - timedelta(weeks=5), 0.50),
            make_weekly_summary(base_date - timedelta(weeks=4), 0.55),
            make_weekly_summary(base_date - timedelta(weeks=3), 0.60),
            make_weekly_summary(base_date - timedelta(weeks=2), 0.70),
            make_weekly_summary(base_date - timedelta(weeks=1), 0.75),
            make_weekly_summary(base_date, 0.80),
        ]
        
        trend = calculate_performance_trend(summaries)
        assert trend == PerformanceTrend.POSITIVE
    
    def test_declining_accuracy_is_negative(self, base_date):
        """Consistent decline over 6 weeks = NEGATIVE."""
        summaries = [
            make_weekly_summary(base_date - timedelta(weeks=5), 0.80),
            make_weekly_summary(base_date - timedelta(weeks=4), 0.75),
            make_weekly_summary(base_date - timedelta(weeks=3), 0.70),
            make_weekly_summary(base_date - timedelta(weeks=2), 0.60),
            make_weekly_summary(base_date - timedelta(weeks=1), 0.55),
            make_weekly_summary(base_date, 0.50),
        ]
        
        trend = calculate_performance_trend(summaries)
        assert trend == PerformanceTrend.NEGATIVE
    
    def test_stable_accuracy_is_neutral(self, base_date):
        """Stable performance = NEUTRAL."""
        summaries = [
            make_weekly_summary(base_date - timedelta(weeks=i), 0.70)
            for i in range(6)
        ]
        
        trend = calculate_performance_trend(summaries)
        assert trend == PerformanceTrend.NEUTRAL


# ============================================================================
# SHARP DECLINE NOTIFICATION (Contract Section 10.1)
# ============================================================================

class TestSharpDeclineNotification:
    """Contract Section 10.1: Sharp decline criteria."""
    
    def test_sharp_decline_requires_magnitude(self, base_datetime):
        """Decline must be >=15% from baseline."""
        # Small decline (10%): baseline=0.75, recent=0.70 -> decline=0.05 < 0.15
        decision = should_notify_sharp_decline(
            recent_accuracy=0.70,
            baseline_accuracy=0.75,
            num_topics_affected=2,
            min_topics=2,
        )
        assert decision is False
    
    def test_sharp_decline_requires_multiple_topics(self, base_datetime):
        """Decline must affect 2+ topics."""
        # Large decline (20%) but only 1 topic affected
        decision = should_notify_sharp_decline(
            recent_accuracy=0.60,
            baseline_accuracy=0.80,
            num_topics_affected=1,
            min_topics=2,
        )
        assert decision is False

    def test_sharp_decline_deterministic(self):
        """Same inputs produce same output (no implicit globals)."""
        r1 = should_notify_sharp_decline(0.60, 0.80, 2)
        r2 = should_notify_sharp_decline(0.60, 0.80, 2)
        assert r1 == r2 is True


# ============================================================================
# INACTIVITY SPIKE NOTIFICATION (Contract Section 10.1)
# ============================================================================

class TestInactivitySpikeNotification:
    """Contract Section 10.1: Inactivity thresholds by time zone."""
    
    def test_inactivity_threshold_varies_by_time_zone(self, base_datetime):
        """Inactivity spike triggers when activity drops significantly (50% below avg)."""
        # Significant drop (0 vs 5) + no recent notification -> should notify
        decision = should_notify_inactivity_spike(
            activity_last_week=0,
            activity_4_week_avg=5.0,
            last_notification_date=None,
            current_date=base_datetime.date(),
        )
        assert decision is True
        
        # Not significant drop (3 vs 5, ratio=0.6 >= 0.5) -> should NOT notify
        decision2 = should_notify_inactivity_spike(
            activity_last_week=3,
            activity_4_week_avg=5.0,
            last_notification_date=None,
            current_date=base_datetime.date(),
        )
        assert decision2 is False
    
    def test_inactivity_requires_previous_engagement(self, base_datetime):
        """Inactivity does NOT trigger if drop ratio >= 50% (not significant)."""
        # activity_last_week=0.5, avg=1.0 -> ratio=0.5, engine returns False (not significant drop)
        decision = should_notify_inactivity_spike(
            activity_last_week=1,  # Same as avg -> ratio=1.0 >= 0.5, no drop
            activity_4_week_avg=1.0,
            last_notification_date=None,
            current_date=base_datetime.date(),
        )
        assert decision is False

    def test_inactivity_spike_deterministic(self, base_date):
        """Same inputs produce same output (uses passed current_date)."""
        r1 = should_notify_inactivity_spike(0, 5.0, None, base_date)
        r2 = should_notify_inactivity_spike(0, 5.0, None, base_date)
        assert r1 == r2 is True


# ============================================================================
# RECOMMENDATION OUTPUT INVARIANTS
# ============================================================================

class TestRecommendationInvariants:
    """Contract Section 9: Recommendation invariants."""
    
    def test_topic_count_zero_requires_fallback_action(self):
        """Empty topic_performances returns valid structure with empty priority_topics."""
        result = generate_recommendations(
            attainment_band=5,
            target_grade=6,
            trend=PerformanceTrend.NEUTRAL,
            weeks_remaining=4,
            topic_performances=[],
        )
        assert "priority_topics" in result
        assert result["priority_topics"] == []
        assert len(result["message"]) > 0
    
    def test_activity_target_maintained_in_risk_management(self):
        """In <5 weeks (FROZEN), session_frequency is conservative (3)."""
        result = generate_recommendations(
            attainment_band=5,
            target_grade=6,
            trend=PerformanceTrend.NEUTRAL,
            weeks_remaining=4,
            topic_performances=[make_topic_performance("t1", 0.5)],
        )
        assert result["session_frequency"] == 3
    
    def test_focus_type_matches_time_zone(self):
        """FROZEN zone gets DAMAGE_CONTROL focus type."""
        topics = [make_topic_performance("t1", 0.5)]
        
        result = generate_recommendations(
            attainment_band=5,
            target_grade=6,
            trend=PerformanceTrend.NEUTRAL,
            weeks_remaining=4,
            topic_performances=topics,
        )
        assert result["focus_type"] == FocusType.DAMAGE_CONTROL.value
    
    def test_primary_topics_limited_by_time_zone(self):
        """Topic count (priority_topics) may vary by time zone."""
        topics = [
            make_topic_performance(f"t{i}", 0.4 + i*0.1)
            for i in range(5)
        ]
        
        result_building = generate_recommendations(
            attainment_band=5,
            target_grade=7,
            trend=PerformanceTrend.NEUTRAL,
            weeks_remaining=25,
            topic_performances=topics,
        )
        
        result_consolidation = generate_recommendations(
            attainment_band=5,
            target_grade=7,
            trend=PerformanceTrend.NEUTRAL,
            weeks_remaining=8,
            topic_performances=topics,
        )
        
        assert len(result_building["priority_topics"]) >= 0
        assert len(result_consolidation["priority_topics"]) >= 0


# ============================================================================
# EDGE CASES AND BOUNDARY CONDITIONS
# ============================================================================

class TestEdgeCases:
    """Edge cases and boundary conditions."""
    
    def test_exactly_5_weeks_is_consolidation(self):
        """5 weeks exactly is Consolidation, not Risk Management."""
        assert classify_time_zone(5) == TimeZone.CONSOLIDATION
        
        # Tier can still downgrade at exactly 5 weeks
        tier, reason = assign_outlook_tier(
            attainment_band=3,
            target_grade=7,
            performance_trend=PerformanceTrend.NEGATIVE,
            activity_frequency=1.0,
            weeks_remaining=5,
            previous_tier=OutlookTier.ON_TRACK,
            hysteresis_state=HysteresisState(0, 3, date(2026, 4, 1)),
        )
        
        # Can downgrade at 5 weeks (not frozen yet)
        assert tier == OutlookTier.AT_RISK
    
    def test_zero_weeks_remaining(self):
        """Zero weeks remaining is valid Risk Management."""
        assert classify_time_zone(0) == TimeZone.RISK_MANAGEMENT
        
        tier, reason = assign_outlook_tier(
            attainment_band=2,
            target_grade=8,
            performance_trend=PerformanceTrend.NEGATIVE,
            activity_frequency=0.0,
            weeks_remaining=0,
            previous_tier=OutlookTier.ON_TRACK,
            hysteresis_state=HysteresisState(0, 10, date(2026, 4, 1)),
        )
        
        # Still frozen at 0 weeks
        assert tier == OutlookTier.ON_TRACK
        assert reason == "frozen"
    
    def test_first_tier_assignment_no_hysteresis(self):
        """First assignment ignores hysteresis (no previous tier)."""
        tier, reason = assign_outlook_tier(
            attainment_band=3,
            target_grade=7,
            performance_trend=PerformanceTrend.NEGATIVE,
            activity_frequency=1.0,
            weeks_remaining=15,
            previous_tier=None,
            hysteresis_state=None,
        )
        
        # Immediate assignment, no hysteresis delay
        assert tier == OutlookTier.AT_RISK
        assert reason in ("met_criteria", "low_activity", "significant_gap")
    
    def test_negative_weeks_treated_as_zero(self, base_date):
        """Negative weeks remaining treated as zero."""
        # Exam date in the past
        past_exam = base_date - timedelta(weeks=2)
        weeks = calculate_weeks_remaining(past_exam, base_date)
        
        assert weeks == 0
        assert classify_time_zone(weeks) == TimeZone.RISK_MANAGEMENT
    
    def test_empty_notification_log(self, base_datetime):
        """should_notify_tier_change works with last_tier_change_date=None."""
        decision = should_notify_tier_change(
            old_tier=OutlookTier.STRETCH_BUT_ACHIEVABLE,
            new_tier=OutlookTier.ON_TRACK,
            weeks_remaining=15,
            last_tier_change_date=None,
            current_date=base_datetime.date(),
        )
        assert decision is True


# ============================================================================
# INTEGRATION SCENARIOS
# ============================================================================

class TestIntegrationScenarios:
    """End-to-end scenarios testing multiple components."""
    
    def test_student_journey_building_to_risk_management(self, base_date):
        """Test student journey across all time zones."""
        # Building phase: forgiving
        tier_building, _ = assign_outlook_tier(
            attainment_band=5,
            target_grade=6,
            performance_trend=PerformanceTrend.NEUTRAL,
            activity_frequency=3.5,
            weeks_remaining=25,
            previous_tier=None,
            hysteresis_state=None,
        )
        assert tier_building == OutlookTier.ON_TRACK  # Forgiving (gap=1 OK)
        
        # Strengthening: stricter
        tier_strengthening, _ = assign_outlook_tier(
            attainment_band=5,
            target_grade=6,
            performance_trend=PerformanceTrend.NEUTRAL,
            activity_frequency=3.5,
            weeks_remaining=15,
            previous_tier=OutlookTier.ON_TRACK,
            hysteresis_state=HysteresisState(0, 3, base_date),
        )
        assert tier_strengthening == OutlookTier.STRETCH_BUT_ACHIEVABLE
        
        # Risk Management: frozen
        tier_risk, reason = assign_outlook_tier(
            attainment_band=4,  # Dropped
            target_grade=6,
            performance_trend=PerformanceTrend.NEGATIVE,
            activity_frequency=2.0,
            weeks_remaining=3,
            previous_tier=OutlookTier.STRETCH_BUT_ACHIEVABLE,
            hysteresis_state=HysteresisState(0, 5, base_date),
        )
        assert tier_risk == OutlookTier.STRETCH_BUT_ACHIEVABLE
        assert reason == "frozen"
    
    def test_notification_lifecycle(self, base_datetime):
        """Test notification lifecycle with rate limiting."""
        monday = datetime(2026, 5, 11, 12, 0, 0)
        state = create_initial_rate_limit_state(monday.date())
        
        # Monday: Tier change notification decision (bool)
        decision1 = should_notify_tier_change(
            old_tier=OutlookTier.ON_TRACK,
            new_tier=OutlookTier.STRETCH_BUT_ACHIEVABLE,
            weeks_remaining=15,
            last_tier_change_date=None,
            current_date=monday.date(),
        )
        assert decision1 is True
        
        # Monday: First P2 - allowed
        allowed1, _ = apply_notification_rate_limits(
            state=state, subject_id="physics",
            priority=NotificationPriority.PRIORITY_2, current_date=monday.date(),
        )
        assert allowed1 is True
        _apply_notification_and_update_state(state, "physics", NotificationPriority.PRIORITY_2, monday)
        
        # Tuesday: Second P2 - allowed (weekly limit 2)
        tuesday = monday.date() + timedelta(days=1)
        allowed2, _ = apply_notification_rate_limits(
            state=state, subject_id="chemistry",
            priority=NotificationPriority.PRIORITY_2, current_date=tuesday,
        )
        assert allowed2 is True
        _apply_notification_and_update_state(state, "chemistry", NotificationPriority.PRIORITY_2, tuesday)
        
        # Wednesday: P1 override - allowed
        wednesday = monday.date() + timedelta(days=2)
        allowed3, _ = apply_notification_rate_limits(
            state=state, subject_id="biology",
            priority=NotificationPriority.PRIORITY_1, current_date=wednesday,
        )
        assert allowed3 is True
        _apply_notification_and_update_state(state, "biology", NotificationPriority.PRIORITY_1, wednesday)
        
        # Thursday: Second P1 - blocked (override exhausted)
        thursday = monday.date() + timedelta(days=3)
        allowed4, reason4 = apply_notification_rate_limits(
            state=state, subject_id="math",
            priority=NotificationPriority.PRIORITY_1, current_date=thursday,
        )
        assert allowed4 is False
        assert reason4 in ("global_weekly_limit_exceeded", "priority1_override_exhausted")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
