# check_fix_kia_profile.py
import os, django, random
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "studymate285.settings")
django.setup()

from django.contrib.auth import get_user_model
from users.models import UserProfile
User = get_user_model()

try:
    u = User.objects.get(username='kia')
except User.DoesNotExist:
    print("User 'kia' not found")
    raise SystemExit(1)

profile = getattr(u, "profile", None)
if not profile:
    profile = UserProfile.objects.create(student=u, total_xp=0, current_level=1, daily_streak=0, school_rank=0)
    print("Created profile for kia:", profile)
else:
    print("Kia profile:", {"total_xp": profile.total_xp, "current_level": profile.current_level, "daily_streak": profile.daily_streak, "school_rank": profile.school_rank})

# Optional: set a non-zero XP for testing
if profile.total_xp == 0:
    profile.total_xp = 750
    profile.current_level = 2
    profile.save()
    print("Updated Kia profile with sample XP for UI testing.")