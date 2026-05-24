from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import uuid

class Student(AbstractUser):
    grade_level = models.CharField(max_length=10, blank=True)
    subjects = models.TextField(blank=True)
    
    # NEW: School Leaderboard Fields
    school_name = models.CharField(max_length=200, blank=True, help_text="Name of your school")
    city = models.CharField(max_length=100, blank=True, help_text="City where you live")
    
    # Parent access token
    parent_access_token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        help_text="Secure token for parent dashboard access"
    )

    subscription_status = models.CharField(max_length=20, default='free')
    stripe_customer_id = models.CharField(max_length=100, blank=True, null=True)
    stripe_subscription_id = models.CharField(max_length=100, blank=True, null=True)
    subscription_expires_at = models.DateTimeField(null=True, blank=True)
    parent_email = models.EmailField(blank=True, null=True)
    
    # Fix reverse accessor conflicts
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name="student_set",
        related_query_name="student",
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name="student_set",
        related_query_name="student",
    )
    
    @property
    def display_name(self):
        name = f"{self.first_name or ''} {self.last_name or ''}".strip()
        return name if name else self.username

    @property
    def is_pro(self):
        if self.subscription_status in ('pro_monthly', 'pro_annual'):
            if self.subscription_expires_at is None:
                return True
            return self.subscription_expires_at > timezone.now()
        return False

    @property
    def name(self):
        return self.display_name

    def __str__(self):
        return self.username


class UserProfile(models.Model):
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='profile')
    total_xp = models.PositiveIntegerField(default=0)
    current_level = models.PositiveIntegerField(default=1)
    daily_streak = models.PositiveIntegerField(default=0)
    last_activity_date = models.DateField(null=True, blank=True)
    school_rank = models.PositiveIntegerField(default=0)
    
    def update_streak(self):
        """Update daily_streak and last_activity_date based on today's activity."""
        from datetime import date
        today = date.today()
        last = self.last_activity_date
        if last is None:
            self.daily_streak = 1
        elif today == last:
            pass
        elif (today - last).days == 1:
            self.daily_streak = self.daily_streak + 1
        else:
            self.daily_streak = 1
        self.last_activity_date = today
        self.save(update_fields=['daily_streak', 'last_activity_date'])
    
    def __str__(self):
        return f"{self.student.username} - Level {self.current_level} ({self.total_xp} XP)"


class Achievement(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=50, unique=True, blank=True, null=True)
    description = models.TextField()
    icon = models.CharField(max_length=50)
    xp_requirement = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name


class UserAchievement(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    earned_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user_profile', 'achievement']


class StudentTopicPerformance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    topic = models.ForeignKey('learning.Topic', on_delete=models.CASCADE)
    questions_attempted = models.PositiveIntegerField(default=0)
    questions_correct = models.PositiveIntegerField(default=0)
    time_spent_seconds = models.PositiveIntegerField(default=0)
    last_interaction = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['student', 'topic']
    
    @property
    def success_rate(self):
        if self.questions_attempted == 0:
            return 0
        return (self.questions_correct / self.questions_attempted) * 100
    
    def __str__(self):
        return f"{self.student.username} - {self.topic.name} ({self.success_rate:.1f}%)"


# NEW: School Leaderboard Models
class School(models.Model):
    """Track schools and their aggregate performance"""
    name = models.CharField(max_length=200, unique=True)
    city = models.CharField(max_length=100)
    postcode = models.CharField(max_length=10, blank=True)
    total_students = models.PositiveIntegerField(default=0)
    total_xp = models.PositiveIntegerField(default=0)
    average_score = models.FloatField(default=0.0)
    rank_national = models.PositiveIntegerField(default=0)
    rank_city = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-total_xp']
    
    def __str__(self):
        return f"{self.name} - {self.city}"
    
    def update_stats(self):
        """Recalculate school statistics"""
        students = Student.objects.filter(school_name=self.name, city=self.city)
        self.total_students = students.count()
        
        # Calculate total XP from all students
        total_xp = 0
        for student in students:
            if hasattr(student, 'profile'):
                total_xp += student.profile.total_xp
        
        self.total_xp = total_xp
        
        # Calculate average
        if self.total_students > 0:
            self.average_score = total_xp / self.total_students
        else:
            self.average_score = 0
        
        self.save()


class GCSEResult(models.Model):
    """Store and verify GCSE results"""
    GRADE_CHOICES = [
        (9, 'Grade 9'),
        (8, 'Grade 8'),
        (7, 'Grade 7'),
        (6, 'Grade 6'),
        (5, 'Grade 5'),
        (4, 'Grade 4'),
        (3, 'Grade 3'),
        (2, 'Grade 2'),
        (1, 'Grade 1'),
        (0, 'U (Ungraded)'),
    ]
    
    SUBJECT_CHOICES = [
        ('mathematics', 'Mathematics'),
        ('biology', 'Biology'),
        ('chemistry', 'Chemistry'),
        ('physics', 'Physics'),
        ('english_language', 'English Language'),
        ('english_literature', 'English Literature'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='gcse_results')
    subject = models.CharField(max_length=50, choices=SUBJECT_CHOICES)
    grade = models.IntegerField(choices=GRADE_CHOICES)
    exam_board = models.CharField(max_length=20, choices=[
        ('aqa', 'AQA'),
        ('edexcel', 'Edexcel'),
        ('ocr', 'OCR'),
        ('wjec', 'WJEC'),
    ])
    exam_year = models.PositiveIntegerField()
    
    # Verification
    certificate_upload = models.FileField(upload_to='gcse_certificates/', null=True, blank=True)
    verified = models.BooleanField(default=False)
    verified_date = models.DateTimeField(null=True, blank=True)
    
    # Prize eligibility
    eligible_for_prize = models.BooleanField(default=False)
    prize_awarded = models.BooleanField(default=False)
    prize_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['student', 'subject', 'exam_year']
        ordering = ['-grade', '-created_at']
    
    def __str__(self):
        return f"{self.student.username} - {self.get_subject_display()} - Grade {self.grade}"


class PrizePool(models.Model):
    """Manage prize competitions"""
    COMPETITION_TYPES = [
        ('top_grades', 'Top GCSE Grades'),
        ('most_improved', 'Most Improved'),
        ('subject_champion', 'Subject Champion'),
        ('school_champion', 'School Champion'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    competition_type = models.CharField(max_length=50, choices=COMPETITION_TYPES)
    subject = models.CharField(max_length=50, blank=True)
    
    total_prize_pool = models.DecimalField(max_digits=10, decimal_places=2)
    number_of_winners = models.PositiveIntegerField(default=10)
    
    start_date = models.DateField()
    end_date = models.DateField()
    results_announced = models.BooleanField(default=False)
    
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} - £{self.total_prize_pool}"


class PrizeWinner(models.Model):
    """Track prize winners"""
    prize_pool = models.ForeignKey(PrizePool, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    rank = models.PositiveIntegerField()
    prize_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Payment details
    payment_method = models.CharField(max_length=50, choices=[
        ('bank_transfer', 'Bank Transfer'),
        ('paypal', 'PayPal'),
        ('gift_card', 'Gift Card'),
    ])
    payment_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
    ], default='pending')
    
    awarded_date = models.DateTimeField(auto_now_add=True)
    paid_date = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.student.username} - {self.prize_pool.name} - £{self.prize_amount}"