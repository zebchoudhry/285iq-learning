import random
import string
import logging

from django.conf import settings
from django.db import models

logger = logging.getLogger(__name__)


def _generate_class_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))


class Teacher(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='teacher_profile',
    )
    school_name = models.CharField(max_length=255)
    subject_specialisms = models.TextField(blank=True)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} — {self.school_name}"


class Classroom(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='classrooms')
    name = models.CharField(max_length=255)
    subject = models.ForeignKey('learning.Subject', on_delete=models.SET_NULL, null=True, blank=True)
    students = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='classrooms')
    class_code = models.CharField(max_length=8, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.class_code:
            code = _generate_class_code()
            while Classroom.objects.filter(class_code=code).exists():
                code = _generate_class_code()
            self.class_code = code
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.class_code})"


class Assignment(models.Model):
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name='assignments')
    title = models.CharField(max_length=255)
    topic = models.ForeignKey('learning.Topic', on_delete=models.SET_NULL, null=True, blank=True)
    due_date = models.DateField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.title} — {self.classroom.name}"


class StudentAssignmentProgress(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='progress_records')
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='assignment_progress',
    )
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('assignment', 'student')

    def __str__(self):
        return f"{self.student.username} — {self.assignment.title}"
