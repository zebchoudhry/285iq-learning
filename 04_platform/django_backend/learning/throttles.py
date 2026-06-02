"""
Custom DRF throttle classes for rate-sensitive endpoints.
"""
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle


class PracticeRateThrottle(UserRateThrottle):
    scope = 'practice'


class TutorRateThrottle(UserRateThrottle):
    scope = 'tutor'


class ParentRateThrottle(AnonRateThrottle):
    scope = 'parent'
