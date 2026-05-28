"""Replay QuizAttempt history to seed skill_rating and difficulty_rating.

Usage:
    python manage.py backfill_skill_ratings --dry-run    # report only
    python manage.py backfill_skill_ratings              # apply
    python manage.py backfill_skill_ratings --reset      # zero ratings first
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from learning.models import QuizAttempt, Question, StudentTopicSkill
from learning.services.calibration import update_ratings, outcome_from_attempt


class Command(BaseCommand):
    help = "Backfill Elo skill and question difficulty ratings from QuizAttempt history."

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--reset', action='store_true',
                            help='Reset all ratings to 1500 before replaying.')

    def handle(self, *args, **opts):
        dry = opts['dry_run']
        reset = opts['reset']

        if reset and not dry:
            self.stdout.write("Resetting all ratings to 1500…")
            Question.objects.update(difficulty_rating=1500.0, rating_attempts=0)
            StudentTopicSkill.objects.all().delete()

        attempts = (
            QuizAttempt.objects
            .select_related('question__lesson__topic')
            .order_by('attempted_at', 'id')
        )
        total = attempts.count()
        self.stdout.write(f"Replaying {total} attempts…")

        seen_first = set()  # (student_id, question_id)
        processed = 0
        skipped = 0

        with transaction.atomic():
            for a in attempts.iterator(chunk_size=1000):
                q = a.question
                if not q or not q.lesson_id or not q.lesson.topic_id:
                    skipped += 1
                    continue

                key = (a.student_id, a.question_id)
                update_question = key not in seen_first
                seen_first.add(key)

                skill, _ = StudentTopicSkill.objects.get_or_create(
                    student_id=a.student_id, topic_id=q.lesson.topic_id,
                )

                outcome = outcome_from_attempt(
                    is_correct=a.is_correct,
                    marks_achieved=getattr(a, 'marks_achieved', 0) or 0,
                    marks_available=q.marks_available or 1,
                )

                new_s, new_q = update_ratings(
                    student_rating=skill.skill_rating,
                    question_rating=q.difficulty_rating,
                    outcome=outcome,
                    student_attempts=skill.attempt_count,
                    question_attempts=q.rating_attempts,
                    update_question=update_question,
                )

                if not dry:
                    skill.skill_rating = new_s
                    skill.attempt_count += 1
                    skill.save(update_fields=['skill_rating', 'attempt_count'])
                    if update_question:
                        q.difficulty_rating = new_q
                        q.rating_attempts += 1
                        q.save(update_fields=['difficulty_rating', 'rating_attempts'])

                processed += 1

            if dry:
                transaction.set_rollback(True)

        self.stdout.write(self.style.SUCCESS(
            f"Done. processed={processed} skipped={skipped} dry_run={dry}"
        ))

        # Report top/bottom 10 questions
        if not dry:
            self.stdout.write("\nTop 10 hardest questions:")
            for q in Question.objects.order_by('-difficulty_rating')[:10]:
                self.stdout.write(f"  {q.id} (lvl {q.difficulty_level}): {q.difficulty_rating:.0f} ({q.rating_attempts} attempts)")
            self.stdout.write("\nTop 10 easiest questions:")
            for q in Question.objects.filter(rating_attempts__gt=5).order_by('difficulty_rating')[:10]:
                self.stdout.write(f"  {q.id} (lvl {q.difficulty_level}): {q.difficulty_rating:.0f} ({q.rating_attempts} attempts)")
