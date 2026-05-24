from django.db import models
from django.utils import timezone
from users.models import Student
from learning.models import Subject


class ExamBoard(models.Model):
    """
    UK GCSE Exam Boards (AQA, Edexcel, OCR, WJEC)
    """
    code = models.CharField(max_length=10, unique=True)
    # 'AQA', 'EDEXCEL', 'OCR', 'WJEC'
    
    name = models.CharField(max_length=100)
    # 'Assessment and Qualifications Alliance'
    
    # Grade boundaries (slightly different per board)
    grade_boundaries = models.JSONField(default=dict)
    # {
    #   "mathematics_higher": {
    #     "9": 86, "8": 76, "7": 66, "6": 56, "5": 46,
    #     "4": 36, "3": 26, "2": 16, "1": 6
    #   }
    # }
    
    # Paper structure
    paper_structure = models.JSONField(default=dict)
    # {
    #   "mathematics_higher": {
    #     "num_papers": 3,
    #     "papers": [
    #       {"number": 1, "name": "Non-Calculator", "marks": 80, "time_minutes": 90},
    #       {"number": 2, "name": "Calculator", "marks": 80, "time_minutes": 90},
    #       {"number": 3, "name": "Calculator", "marks": 80, "time_minutes": 90}
    #     ]
    #   }
    # }
    
    formula_sheet_url = models.URLField(blank=True)
    website = models.URLField(blank=True)
    
    popularity_percentage = models.IntegerField(default=0)
    # AQA: 52%, Edexcel: 28%, OCR: 15%, WJEC: 5%
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.code
    
    def get_grade_boundaries(self, subject_key):
        """Get grade boundaries for a specific subject"""
        return self.grade_boundaries.get(subject_key, {})
    
    def convert_percentage_to_grade(self, percentage, subject_key='mathematics_higher'):
        """
        Convert percentage to GCSE grade (1-9) based on boundaries
        """
        boundaries = self.get_grade_boundaries(subject_key)
        
        if not boundaries:
            # Fallback to standard boundaries
            boundaries = {
                "9": 85, "8": 75, "7": 65, "6": 55, "5": 45,
                "4": 35, "3": 25, "2": 15, "1": 5
            }
        
        # Sort by threshold descending
        sorted_boundaries = sorted(
            boundaries.items(),
            key=lambda x: int(x[1]),
            reverse=True
        )
        
        for grade, threshold in sorted_boundaries:
            if percentage >= threshold:
                return int(grade)
        
        return 1  # Below all thresholds


class MockExam(models.Model):
    """
    Template for a mock exam (e.g., "AQA Maths Paper 1 - June 2024")
    """
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    exam_board = models.ForeignKey(ExamBoard, on_delete=models.CASCADE)
    
    # Exam metadata
    title = models.CharField(max_length=200)
    # "AQA GCSE Mathematics Paper 1 (Non-Calculator) - June 2024"
    
    paper_number = models.IntegerField(default=1)
    # 1, 2, or 3
    
    tier = models.CharField(max_length=20, default='higher')
    # foundation or higher
    
    # Exam specs
    total_marks = models.IntegerField(default=80)
    time_allowed_minutes = models.IntegerField(default=90)
    calculator_allowed = models.BooleanField(default=True)
    
    # Source
    source_year = models.IntegerField(null=True, blank=True)
    # 2024, 2023, etc.
    
    source_series = models.CharField(max_length=20, blank=True)
    # "June", "November"
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-source_year', '-source_series', 'paper_number']
    
    def __str__(self):
        return f"{self.exam_board.code} - {self.title}"


class PastPaper(models.Model):
    """Link to official past paper PDFs/pages by exam board."""
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    exam_board = models.ForeignKey(ExamBoard, on_delete=models.CASCADE)
    year = models.IntegerField()
    paper_number = models.IntegerField(default=1)
    title = models.CharField(max_length=200)
    source_url = models.URLField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-year', 'paper_number']
        unique_together = ('subject', 'exam_board', 'year', 'paper_number')

    def __str__(self):
        return self.title


class MockExamAttempt(models.Model):
    """
    Student's attempt at a mock exam
    """
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='mock_attempts')
    mock_exam = models.ForeignKey(MockExam, on_delete=models.CASCADE)
    
    # Timing
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)
    time_taken_seconds = models.IntegerField(null=True, blank=True)
    
    # Status
    STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('abandoned', 'Abandoned'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')
    
    # Scoring
    total_marks_available = models.IntegerField()
    marks_achieved = models.IntegerField(null=True, blank=True)
    percentage_score = models.FloatField(null=True, blank=True)
    predicted_grade = models.IntegerField(null=True, blank=True)
    # GCSE grade 1-9 based on this mock
    
    # Conditions
    exam_conditions = models.BooleanField(default=False)
    # Did they take it under timed exam conditions?
    
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.student.username} - {self.mock_exam.title} - {self.status}"


class MockExamQuestion(models.Model):
    """Link a mock exam (past paper) to a fixed set of questions in order."""
    mock_exam = models.ForeignKey(MockExam, on_delete=models.CASCADE, related_name='questions')
    question = models.ForeignKey('learning.Question', on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)
    marks = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['order']
        unique_together = ('mock_exam', 'question')


class MockExamAttemptAnswer(models.Model):
    """Per-question result for a mock exam attempt."""
    attempt = models.ForeignKey(MockExamAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey('learning.Question', on_delete=models.CASCADE)
    marks_achieved = models.PositiveIntegerField(default=0)
    correct = models.BooleanField(default=False)

    class Meta:
        unique_together = ('attempt', 'question')


class NotificationLog(models.Model):
    """
    Audit + anti-fatigue tracking for parent notifications
    """
    EVENT_CHOICES = [
        ("tier_change", "Tier Change"),
        ("inactivity", "Inactivity Spike"),
        ("decline", "Sharp Decline"),
        ("positive", "Positive Trend"),
        ("timezone", "Time Zone Transition"),
        ("exam_soon", "Exam Approaching"),
        ("mock_complete", "Mock Exam Completed"),
        ("daily_digest", "Daily Study Digest"),
    ]
    
    PRIORITY_CHOICES = [
        (1, "Critical"),
        (2, "Normal"),
        (3, "Low"),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, null=True, blank=True)
    
    event_type = models.CharField(max_length=30, choices=EVENT_CHOICES)
    priority = models.IntegerField(choices=PRIORITY_CHOICES, default=2)
    
    message = models.TextField()
    sent_at = models.DateTimeField(default=timezone.now)
    
    parent_opened = models.BooleanField(default=False)
    
    class Meta:
        ordering = ["-sent_at"]
    
    def __str__(self):
        return f"{self.student.display_name} - {self.event_type} - {self.sent_at.date()}"