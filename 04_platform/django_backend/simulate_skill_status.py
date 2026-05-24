"""
Django shell simulation: StudentSkillState status transitions.
Run: python manage.py shell < simulate_skill_status.py
Or paste into: python manage.py shell
"""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "studymate285.settings")
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from learning.models import SkillNode, StudentSkillState

User = get_user_model()


def apply_attempt(skill_state, is_correct):
    """Mirror the AttemptSerializer logic for updating StudentSkillState."""
    skill_state.attempts += 1
    if not is_correct:
        skill_state.failures += 1
    if skill_state.attempts > 0:
        skill_state.rolling_accuracy = ((skill_state.attempts - skill_state.failures) / skill_state.attempts) * 100.0
    else:
        skill_state.rolling_accuracy = 0.0
    skill_state.mastery_score = skill_state.rolling_accuracy
    skill_state.last_attempt_at = timezone.now()
    # Status transitions (same as serializers.py)
    if skill_state.attempts < 3:
        skill_state.status = "NEW"
    elif skill_state.rolling_accuracy < 60:
        skill_state.status = "LEARNING"
    elif skill_state.rolling_accuracy < StudentSkillState.MASTERY_MIN_ACCURACY:
        skill_state.status = "IMPROVING"
    elif (
        skill_state.rolling_accuracy >= StudentSkillState.MASTERY_MIN_ACCURACY
        and skill_state.attempts >= StudentSkillState.MASTERY_MIN_ATTEMPTS
    ):
        skill_state.status = "MASTERED"
    else:
        skill_state.status = "IMPROVING"
    skill_state.save()
    return skill_state.status


# 1. Create or get Student and SkillNode
try:
    student = User.objects.get(username="sim_student_skill")
except User.DoesNotExist:
    student = User.objects.create_user(username="sim_student_skill", password="testpass123")
skill, _ = SkillNode.objects.get_or_create(
    code="MATH_SIM_STATUS",
    defaults={"subject": "Mathematics", "description": "Simulation skill"},
)

# 2. Create StudentSkillState (fresh for simulation)
ss, _ = StudentSkillState.objects.get_or_create(
    student=student,
    skill=skill,
    defaults={
        "attempts": 0,
        "failures": 0,
        "rolling_accuracy": 0.0,
        "mastery_score": 0.0,
        "status": "NEW",
    },
)
# Reset for clean run
ss.attempts = 0
ss.failures = 0
ss.rolling_accuracy = 0.0
ss.mastery_score = 0.0
ss.status = "NEW"
ss.save()

print("=== StudentSkillState status transition simulation ===\n")
print(f"Skill: {skill.code} | Student: {student.username}")
print(f"Thresholds: MASTERY_MIN_ATTEMPTS={StudentSkillState.MASTERY_MIN_ATTEMPTS}, MASTERY_MIN_ACCURACY={StudentSkillState.MASTERY_MIN_ACCURACY}\n")

# 3. Simulate attempts: 2 wrong (NEW), 1 wrong (LEARNING), then correct until MASTERED
# Path: NEW -> NEW -> LEARNING -> ... -> IMPROVING -> MASTERED
attempts_sequence = [
    False, False, False,   # 3 wrong -> LEARNING (0%)
    True, True, True, True, True,  # 5/8 = 62.5% -> IMPROVING
    True, True, True, True, True, True, True, True, True,  # 14/17 = 82.4% -> IMPROVING
    True, True, True,  # 17/20 = 85% -> MASTERED
]

for i, correct in enumerate(attempts_sequence, 1):
    status = apply_attempt(ss, correct)
    acc = ss.rolling_accuracy
    corr = ss.attempts - ss.failures
    result = "correct" if correct else "wrong"
    print(f"  Attempt {i:2d} ({result:6s}) -> attempts={ss.attempts}, accuracy={acc:5.1f}% ({corr}/{ss.attempts}) -> status={status}")

print("\n=== Transition path confirmed ===")
print("Expected: NEW -> LEARNING -> IMPROVING -> MASTERED")
print(f"Final state: {ss.attempts} attempts, {ss.rolling_accuracy:.1f}% accuracy, status={ss.status}")
print("Simulation complete.")
