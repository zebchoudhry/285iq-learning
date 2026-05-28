"""Single point of dispatch between v1.0 (frozen) and v1.1.

All live callers import from here. The version is selected via the
DECISION_ENGINE_VERSION env/settings flag. Default is '1.0'.
"""
from django.conf import settings

_version = getattr(settings, 'DECISION_ENGINE_VERSION', '1.0')

if _version == '1.1':
    from decision_engine.v1_1.decision_engine_v1 import (  # noqa: F401
        evaluate_student_subject,
    )
    from decision_engine.v1_1.core import (  # noqa: F401
        OutlookTier,
        PerformanceTrend,
        FocusType,
        NotificationPriority,
        NotificationRateLimitState,
        apply_notification_rate_limits,
        generate_recommendations,
    )
else:
    from decision_engine.v1_0.decision_engine_v1 import (  # noqa: F401
        evaluate_student_subject,
    )
    from decision_engine.v1_0.core import (  # noqa: F401
        OutlookTier,
        PerformanceTrend,
        FocusType,
        NotificationPriority,
        NotificationRateLimitState,
        apply_notification_rate_limits,
        generate_recommendations,
    )
