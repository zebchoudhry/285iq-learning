"""
Django signals for the users app.
Auto-creates default StudentExamSettings when a student registers.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import date, timedelta
from .models import Student


@receiver(post_save, sender=Student)
def create_default_exam_settings(sender, instance, created, **kwargs):
    """
    When a new Student is created, automatically create StudentExamSettings
    for all 4 GCSE subjects with default exam date (6 months from now).
    """
    if created:
        from learning.models import Subject, StudentExamSettings
        
        # Get all 4 core GCSE subjects
        subjects = Subject.objects.filter(name__in=['mathematics', 'biology', 'chemistry', 'physics'])
        default_exam_date = date.today() + timedelta(days=180)  # 6 months ahead
        
        for subject in subjects:
            StudentExamSettings.objects.get_or_create(
                student=instance,
                subject=subject,
                defaults={
                    'exam_date': default_exam_date,
                    'target_grade': 6,
                    'tier': 'higher',
                    'exam_board': 'aqa',
                }
            )
