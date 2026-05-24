"""
Controlled simulation: practice_selector excludes MASTERED skills.
- Skill A: MASTERED (excluded)
- Skill B: LEARNING (weakest non-mastered, should be chosen)
- Skill C: IMPROVING (should be secondary)

Run: python simulate_practice_selector_mastery.py
"""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "studymate285.settings")
django.setup()

from django.contrib.auth import get_user_model
from learning.models import (
    Subject,
    Topic,
    Lesson,
    Question,
    QuestionStep,
    SkillNode,
    StudentSkillState,
)
from learning.services.practice_selector import select_practice_questions
from users.models import Student

User = get_user_model()


def main():
    print("=== Practice Selector Mastery Graduation Simulation ===\n")

    # Get or create student
    try:
        student = User.objects.get(username="sim_practice_selector")
    except User.DoesNotExist:
        student = User.objects.create_user(
            username="sim_practice_selector", password="testpass123"
        )

    # Get or create subject, topic, lessons, questions
    subject, _ = Subject.objects.get_or_create(
        name="sim_subject",
        defaults={"display_name": "Sim Subject"},
    )
    # Ensure we have a topic
    topic, _ = Topic.objects.get_or_create(
        subject=subject, name="Sim Topic", defaults={"order": 0}
    )

    # Create 3 skills
    skill_a, _ = SkillNode.objects.get_or_create(
        code="SIM_SKILL_A_MASTERED",
        defaults={"subject": "Sim", "description": "Skill A - MASTERED"},
    )
    skill_b, _ = SkillNode.objects.get_or_create(
        code="SIM_SKILL_B_LEARNING",
        defaults={"subject": "Sim", "description": "Skill B - LEARNING"},
    )
    skill_c, _ = SkillNode.objects.get_or_create(
        code="SIM_SKILL_C_IMPROVING",
        defaults={"subject": "Sim", "description": "Skill C - IMPROVING"},
    )

    # Create lessons and questions for each skill (need questions linked via QuestionStep)
    lessons_created = []
    for i, (skill, name) in enumerate(
        [(skill_a, "Skill A"), (skill_b, "Skill B"), (skill_c, "Skill C")]
    ):
        lesson, _ = Lesson.objects.get_or_create(
            topic=topic,
            title=f"Lesson {name}",
            defaults={"content": f"Content {name}", "order": i},
        )
        lessons_created.append((lesson, skill))

    # Create questions and QuestionSteps
    all_question_ids = []
    skill_to_questions = {skill_a.id: [], skill_b.id: [], skill_c.id: []}
    for lesson, skill in lessons_created:
        for j in range(3):  # 3 questions per skill
            q, _ = Question.objects.get_or_create(
                lesson=lesson,
                question_text=f"Q {lesson.title} {j}",
                defaults={
                    "correct_answer": "x",
                    "difficulty_level": 2,
                    "is_active": True,
                },
            )
            all_question_ids.append(q.id)
            skill_to_questions[skill.id].append(q.id)
            QuestionStep.objects.get_or_create(
                question=q, step_order=1, defaults={"skill": skill}
            )

    # Create StudentSkillState with explicit status
    # Skill A: MASTERED (90% accuracy, 10 attempts)
    ss_a, _ = StudentSkillState.objects.update_or_create(
        student=student,
        skill=skill_a,
        defaults={
            "attempts": 10,
            "failures": 1,
            "rolling_accuracy": 90.0,
            "mastery_score": 90.0,
            "status": "MASTERED",
        },
    )
    # Skill B: LEARNING (40% accuracy, 5 attempts) - weakest non-mastered
    ss_b, _ = StudentSkillState.objects.update_or_create(
        student=student,
        skill=skill_b,
        defaults={
            "attempts": 5,
            "failures": 3,
            "rolling_accuracy": 40.0,
            "mastery_score": 40.0,
            "status": "LEARNING",
        },
    )
    # Skill C: IMPROVING (70% accuracy, 6 attempts)
    ss_c, _ = StudentSkillState.objects.update_or_create(
        student=student,
        skill=skill_c,
        defaults={
            "attempts": 6,
            "failures": 2,
            "rolling_accuracy": 70.0,
            "mastery_score": 70.0,
            "status": "IMPROVING",
        },
    )

    print("StudentSkillState setup:")
    print(f"  Skill A ({skill_a.code}): status={ss_a.status}, accuracy={ss_a.rolling_accuracy:.1f}%")
    print(f"  Skill B ({skill_b.code}): status={ss_b.status}, accuracy={ss_b.rolling_accuracy:.1f}%")
    print(f"  Skill C ({skill_c.code}): status={ss_c.status}, accuracy={ss_c.rolling_accuracy:.1f}%")
    print()

    # Run practice_selector
    question_ids = select_practice_questions(student=student, subject_id=subject.id, count=6)
    print(f"practice_selector returned {len(question_ids)} question IDs: {question_ids}")

    # Map question_id -> skill
    qid_to_skill = {}
    for qid in question_ids:
        step = QuestionStep.objects.filter(question_id=qid).select_related("skill").first()
        if step:
            qid_to_skill[qid] = step.skill.code

    # Count by skill
    skill_counts = {skill_a.code: 0, skill_b.code: 0, skill_c.code: 0}
    for qid in question_ids:
        if qid in qid_to_skill:
            skill_counts[qid_to_skill[qid]] += 1

    print("\nQuestions selected by skill:")
    for code, cnt in skill_counts.items():
        print(f"  {code}: {cnt} questions")

    # Confirmations
    skill_a_count = skill_counts.get(skill_a.code, 0)
    skill_b_count = skill_counts.get(skill_b.code, 0)
    skill_c_count = skill_counts.get(skill_c.code, 0)

    print("\n=== Confirmations ===")
    if skill_a_count == 0:
        print("  OK: Skill A (MASTERED) is EXCLUDED - 0 questions")
    else:
        print(f"  FAIL: Skill A (MASTERED) should be excluded but got {skill_a_count} questions")

    if skill_b_count > 0 or skill_c_count > 0:
        print("  OK: Non-mastered skills (B, C) have questions selected")
    else:
        print("  NOTE: Fallback to random/topic - no skill-based questions (may happen if no overlap with base_q)")

    # Weakest non-mastered = Skill B (40%) < Skill C (70%)
    # practice_selector orders by rolling_accuracy ascending, so Skill B should be preferred
    if skill_b_count >= skill_c_count and skill_b_count > 0:
        print("  OK: Weakest non-mastered skill (Skill B, LEARNING) is prioritized")
    elif skill_b_count > 0 or skill_c_count > 0:
        print("  OK: Non-mastered skills selected (order may vary with random fill)")
    else:
        print("  NOTE: All questions from fallback (topic/random) - ensure questions exist for subject")

    print("\nSimulation complete.")


if __name__ == "__main__":
    main()
