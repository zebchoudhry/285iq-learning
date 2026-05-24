"""
Management command to send daily study digest to parents.
Aggregates that day's study activity per student and sends one email per student.
Run daily via cron: 0 20 * * * (e.g. 8pm)
"""
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone

from learning.models import StudentProgress, QuizAttempt, StudentExamSettings
from learning.services.activity_feed import get_recent_activity


class Command(BaseCommand):
    help = "Send daily study digest to parents for students with activity today"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Show what would be sent without sending")

    def handle(self, *args, **options):
        dry_run = options.get("dry_run", False)
        today = date.today()

        # Students with activity today: lesson completions or quiz attempts
        lesson_student_ids = set(
            StudentProgress.objects.filter(
                is_completed=True,
                completion_date__date=today,
            ).values_list("student_id", flat=True)
        )
        quiz_student_ids = set(
            QuizAttempt.objects.filter(attempted_at__date=today).values_list("student_id", flat=True)
        )
        active_student_ids = lesson_student_ids | quiz_student_ids

        if not active_student_ids:
            self.stdout.write("No study activity today. Nothing to send.")
            return

        notified = 0
        for student_id in active_student_ids:
            acts = get_recent_activity(student_id, limit=20)
            today_acts = [a for a in acts if a.get("date") == today.isoformat()]
            if not today_acts:
                continue

            # Build digest message
            lines = [f"Study activity for {today.isoformat()}:"]
            for a in today_acts:
                lines.append(f"  - {a.get('subject', '')}: {a.get('details', a.get('title', ''))}")

            msg = "\n".join(lines)

            setting = StudentExamSettings.objects.filter(student_id=student_id).first()
            subject_id = setting.subject_id if setting else None
            if subject_id is None:
                from learning.models import Subject
                first_subject = Subject.objects.filter(is_active=True).first()
                subject_id = first_subject.id if first_subject else 1

            if dry_run:
                self.stdout.write(f"[DRY-RUN] Would send to parent of student {student_id}: {msg[:80]}...")
                notified += 1
                continue

            try:
                from users.models import Student
                from dashboard.services.notification_delivery import send_parent_notification

                student = Student.objects.filter(id=student_id).first()
                if not student:
                    continue
                subject = setting.subject if setting else None
                subject_display = subject.display_name if subject else "Study"

                if send_parent_notification(
                    student_id=student_id,
                    subject_id=subject_id,
                    event_type="daily_digest",
                    priority=2,
                    message=msg,
                    subject_display_name=subject_display,
                    student_name=getattr(student, "display_name", student.username),
                ):
                    notified += 1
            except Exception as e:
                self.stderr.write(f"Digest failed for student {student_id}: {e}")

        self.stdout.write(f"Daily digest: {len(active_student_ids)} students with activity; {notified} notifications sent")
