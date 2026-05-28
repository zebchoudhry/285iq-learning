"""Post-save hook: every QuizAttempt updates Elo ratings."""
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from learning.models import QuizAttempt, Question, StudentTopicSkill
from learning.services.calibration import update_ratings, outcome_from_attempt


@receiver(post_save, sender=QuizAttempt)
def update_elo_on_attempt(sender, instance: QuizAttempt, created: bool, **kwargs):
    if not created:
        return
    if not instance.student_id or not instance.question_id:
        return

    with transaction.atomic():
        question = Question.objects.select_for_update().get(pk=instance.question_id)
        topic_id = question.lesson.topic_id

        skill, _ = StudentTopicSkill.objects.select_for_update().get_or_create(
            student_id=instance.student_id,
            topic_id=topic_id,
        )

        # First-attempt-only for question difficulty:
        prior_attempts = QuizAttempt.objects.filter(
            student_id=instance.student_id,
            question_id=instance.question_id,
        ).exclude(pk=instance.pk).exists()
        update_question = not prior_attempts

        outcome = outcome_from_attempt(
            is_correct=instance.is_correct,
            marks_achieved=getattr(instance, 'marks_achieved', 0) or 0,
            marks_available=getattr(question, 'marks_available', 1) or 1,
        )

        new_student, new_question = update_ratings(
            student_rating=skill.skill_rating,
            question_rating=question.difficulty_rating,
            outcome=outcome,
            student_attempts=skill.attempt_count,
            question_attempts=question.rating_attempts,
            update_question=update_question,
        )

        skill.skill_rating = new_student
        skill.attempt_count += 1
        skill.save(update_fields=['skill_rating', 'attempt_count', 'updated_at'])

        if update_question:
            question.difficulty_rating = new_question
            question.rating_attempts += 1
            question.save(update_fields=['difficulty_rating', 'rating_attempts'])
