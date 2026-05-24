"""
Tests for build_weekly_summaries (decision engine adapter).
"""
import pytest

pytestmark = pytest.mark.django_db


def test_build_weekly_summaries_returns_list():
    """build_weekly_summaries returns a list (empty if no data)."""
    from decision_engine.v1_0.decision_engine_v1 import build_weekly_summaries

    result = build_weekly_summaries(7, 1, weeks=8)
    assert isinstance(result, list)
