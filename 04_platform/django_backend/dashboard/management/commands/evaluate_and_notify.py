"""
Management command to evaluate all students with exam settings and send parent
notifications on tier changes. Run weekly via cron: 0 9 * * 1
"""
from django.core.management.base import BaseCommand
from learning.models import StudentExamSettings
from decision_engine.v1_0.decision_engine_v1 import evaluate_student_subject
from decision_engine.v1_0.core import OutlookTier


class Command(BaseCommand):
    help = 'Evaluate outlook tiers for all students with exam settings; persist tier and notify on change'

    def handle(self, *args, **options):
        settings_qs = StudentExamSettings.objects.select_related('student', 'subject').all()
        count = 0
        notified = 0
        for setting in settings_qs:
            try:
                previous_tier = None
                if setting.last_outlook_tier:
                    try:
                        previous_tier = OutlookTier(setting.last_outlook_tier)
                    except Exception:
                        pass
                evaluation = evaluate_student_subject(
                    student_id=setting.student_id,
                    subject_id=setting.subject_id,
                    exam_date=setting.exam_date,
                    target_grade=setting.target_grade,
                    previous_tier=previous_tier,
                )
                new_tier = evaluation.get('tier')
                new_tier_str = new_tier.value if hasattr(new_tier, 'value') else str(new_tier)
                old_tier_str = setting.last_outlook_tier or ''
                if new_tier_str != old_tier_str:
                    if old_tier_str:
                        try:
                            from dashboard.services.notification_delivery import send_parent_notification
                            msg = f"Outlook changed to {new_tier_str.replace('_', ' ').title()}. {evaluation.get('reason', '')}"
                            if send_parent_notification(
                                student_id=setting.student_id,
                                subject_id=setting.subject_id,
                                event_type='tier_change',
                                priority=2,
                                message=msg,
                                subject_display_name=setting.subject.display_name,
                                student_name=setting.student.display_name,
                            ):
                                notified += 1
                        except Exception as e:
                            self.stderr.write(f"Notify failed {setting.student_id}/{setting.subject_id}: {e}")
                    setting.last_outlook_tier = new_tier_str
                    setting.save(update_fields=['last_outlook_tier'])
                    count += 1
            except Exception as e:
                self.stderr.write(f"Evaluate failed {setting.student_id}/{setting.subject_id}: {e}")
        self.stdout.write(f"Evaluated {settings_qs.count()} settings; {count} tier updates; {notified} notifications sent")
