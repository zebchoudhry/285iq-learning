"""Achievement check and award logic."""
def check_and_award_achievements(user):
    """Check if user qualifies for any achievements and award them."""
    try:
        profile = getattr(user, 'profile', None)
        if profile is None:
            return
        from .models import Achievement, UserAchievement
        from django.db.models import Count
        from learning.models import StudentProgress, QuizAttempt
        for achievement in Achievement.objects.filter(is_active=True):
            if UserAchievement.objects.filter(user_profile=profile, achievement=achievement).exists():
                continue
            slug = achievement.slug or ''
            qualifies = False
            if slug == 'first_lesson':
                qualifies = StudentProgress.objects.filter(student=user, is_completed=True).exists()
            elif slug == 'ten_correct':
                count = QuizAttempt.objects.filter(student=user, is_correct=True).count()
                qualifies = count >= 10
            elif slug == 'seven_day_streak':
                qualifies = profile.daily_streak >= 7
            elif slug == 'fifty_xp':
                qualifies = profile.total_xp >= 50
            elif slug == 'hundred_xp':
                qualifies = profile.total_xp >= 100
            if qualifies:
                UserAchievement.objects.get_or_create(user_profile=profile, achievement=achievement)
    except Exception:
        pass
