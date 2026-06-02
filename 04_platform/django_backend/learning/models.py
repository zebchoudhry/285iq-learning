from django.conf import settings
from django.db import models


class Subject(models.Model):
    """
    Subject tied to exam board
    """
    # Link to exam board
    exam_board = models.ForeignKey('dashboard.ExamBoard', on_delete=models.CASCADE, null=True, blank=True)
    
    name = models.CharField(max_length=50)
    # "mathematics", "physics", "biology", "chemistry"
    
    tier = models.CharField(
        max_length=20,
        choices=[
            ('higher', 'Higher Tier'),
            ('foundation', 'Foundation Tier'),
        ],
        default='higher'
    )
    
    display_name = models.CharField(max_length=100)
    # "GCSE Mathematics (Higher Tier)"
    
    description = models.TextField(blank=True)
    
    specification_code = models.CharField(max_length=20, blank=True)
    # AQA: "8300", Edexcel: "1MA1", OCR: "J560"
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('exam_board', 'name', 'tier')
        ordering = ['display_name']
    
    def __str__(self):
        board_name = self.exam_board.code if self.exam_board else "No Board"
        return f"{board_name} - {self.display_name}"


class Topic(models.Model):
    """
    Topic within a subject (e.g., Algebra, Geometry)
    """
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='topics')
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['subject', 'order']
        unique_together = ('subject', 'name')
    
    def __str__(self):
        return f"{self.subject.display_name} - {self.name}"


class Lesson(models.Model):
    """
    Lesson within a topic
    """
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='lessons')
    
    title = models.CharField(max_length=200)
    content = models.TextField()
    
    estimated_duration = models.IntegerField(default=30)
    # Duration in minutes
    
    LESSON_TYPE_CHOICES = [
        ('theory', 'Theory'),
        ('worked_examples', 'Worked Examples'),
        ('practice', 'Practice'),
        ('revision', 'Revision'),
    ]
    lesson_type = models.CharField(max_length=20, choices=LESSON_TYPE_CHOICES, default='theory')
    
    difficulty_level = models.IntegerField(default=2)
    # 1 (easy) to 5 (very hard)
    
    key_skills = models.JSONField(default=list, blank=True)
    # ["solving equations", "rearranging formulas"]
    
    video_url = models.URLField(max_length=500, blank=True)
    # Optional YouTube/Vimeo URL - embedded in lesson view

    infographic_url = models.URLField(max_length=500, blank=True)
    # URL to infographic image (Wikimedia Commons, OpenStax etc.)

    focus_areas = models.JSONField(default=list, blank=True)
    # ["Key formula: F=ma", "Units must be SI", "Show working"]

    common_mistakes = models.JSONField(default=list, blank=True)
    # ["Forgetting to convert units", "Mixing up mass and weight"]

    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['topic', 'order']
    
    def __str__(self):
        return f"{self.topic.name} - {self.title}"


class Flashcard(models.Model):
    """Flashcard for a topic - front/back for revision."""
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='flashcards')
    front = models.TextField()
    back = models.TextField()
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['topic', 'order']

    def __str__(self):
        return f"{self.topic.name} - {self.front[:50]}..."


class StudentFlashcardProgress(models.Model):
    """Per-student spaced-repetition state for a flashcard (SM-2 style)."""
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='flashcard_progress',
    )
    flashcard = models.ForeignKey(
        Flashcard,
        on_delete=models.CASCADE,
        related_name='student_progress',
    )
    ease_factor = models.FloatField(default=2.5)
    interval_days = models.PositiveIntegerField(default=1)
    repetition_count = models.PositiveIntegerField(default=0)
    due_date = models.DateField()
    last_reviewed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'flashcard')
        ordering = ['due_date', 'flashcard_id']

    def __str__(self):
        return f"{self.student_id} - FC{self.flashcard_id} due {self.due_date}"


class Question(models.Model):
    """
    Question within a lesson
    NOW WITH EXAM BOARD SUPPORT
    """
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='questions')
    
    question_text = models.TextField()
    correct_answer = models.TextField()
    
    # EXAM BOARD SPECIFICITY
    is_shared = models.BooleanField(default=True)
    # True = works for all exam boards (95% of questions)
    # False = specific to certain boards (5% of questions)
    
    specific_exam_boards = models.ManyToManyField('dashboard.ExamBoard', blank=True)
    # Only populated if is_shared = False
    # E.g., "This question style only appears in AQA papers"
    
    QUESTION_TYPE_CHOICES = [
        ('short_answer', 'Short Answer'),
        ('multiple_choice', 'Multiple Choice'),
        ('calculation', 'Calculation with Working'),
        ('extended', 'Extended Response'),
    ]
    question_type = models.CharField(max_length=30, choices=QUESTION_TYPE_CHOICES, default='short_answer')
    
    difficulty_level = models.IntegerField(default=2)
    # 1 (easy) to 5 (very hard)
    
    marks_available = models.IntegerField(default=1)
    
    explanation = models.TextField(blank=True)
    # Explanation of the answer
    
    marking_scheme = models.TextField(blank=True)
    # How to award marks (M1, A1, etc.)
    
    # Provenance
    source = models.CharField(max_length=100, blank=True)
    # "AQA June 2024 Paper 1 Q7", "Edexcel Nov 2023 Paper 3 Q12"
    
    # Cached LLM explanation — populated on first wrong-answer request, reused thereafter
    llm_explanation_cache = models.TextField(blank=True, default='')
    llm_explanation_cached_at = models.DateTimeField(null=True, blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['lesson', 'difficulty_level']

    def __str__(self):
        return f"{self.lesson.title} - Q{self.id} ({self.marks_available}m)"
    
    def is_available_for_exam_board(self, exam_board):
        """
        Check if this question is available for a specific exam board
        """
        if self.is_shared:
            return True
        return self.specific_exam_boards.filter(id=exam_board.id).exists()


class MultipleChoiceOption(models.Model):
    """MCQ option for a question."""
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    option_text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.question_id} - option {self.order}"


class StudentProgress(models.Model):
    """Tracks a student's progress on a lesson."""
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='learning_progress',
    )
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False)
    completion_date = models.DateTimeField(blank=True, null=True)
    time_spent = models.PositiveIntegerField(default=0)
    questions_attempted = models.PositiveIntegerField(default=0)
    questions_correct = models.PositiveIntegerField(default=0)
    average_grade = models.FloatField(blank=True, null=True)

    class Meta:
        unique_together = ('student', 'lesson')

    def __str__(self):
        return f"{self.student_id} - {self.lesson_id}"

    @property
    def success_rate(self):
        if self.questions_attempted == 0:
            return None
        return round(100.0 * self.questions_correct / self.questions_attempted, 1)


class QuizAttempt(models.Model):
    """A single quiz question attempt by a student."""
    ERROR_TYPE_CHOICES = [
        ('none', 'No Error'),
        ('conceptual', 'Conceptual Error'),
        ('procedural', 'Procedural Error'),
        ('structural', 'Structural / Logic Error'),
        ('guess', 'Guessing'),
    ]
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='quiz_attempts',
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='attempts',
    )
    is_correct = models.BooleanField(default=False)
    error_type = models.CharField(
        max_length=20,
        choices=ERROR_TYPE_CHOICES,
        default='none',
    )
    time_to_first_action_ms = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text='Time before first interaction (ms)',
    )
    time_spent_ms = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text='Total time on question (ms)',
    )
    attempted_at = models.DateTimeField(auto_now_add=True)
    needs_review = models.BooleanField(
        default=False,
        help_text='Flagged for review after repeated wrong answers',
    )

    class Meta:
        ordering = ['-attempted_at']

    def __str__(self):
        return f"{self.student_id} - Q{self.question_id} ({'correct' if self.is_correct else 'wrong'})"


class StudentGymState(models.Model):
    """Hysteresis state for gym mode per student/topic."""
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='gym_states',
    )
    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name='gym_states',
    )
    current_mode = models.CharField(max_length=32)
    stable_since = models.DateTimeField(auto_now_add=True)
    confirmation_count = models.PositiveIntegerField(default=1)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'topic')

    def __str__(self):
        return f"{self.student_id} - {self.topic_id} - {self.current_mode}"


class TopicStrengthSnapshot(models.Model):
    """Daily snapshot of topic strength for trend display."""
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='topic_strength_snapshots',
    )
    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name='strength_snapshots',
    )
    date = models.DateField()
    accuracy_rate = models.FloatField(default=0.0)
    recent_accuracy = models.FloatField(default=0.0)
    questions_attempted = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-date']
        unique_together = ('student', 'topic', 'date')

    def __str__(self):
        return f"{self.student_id} - {self.topic_id} @ {self.date}"


class StudySession(models.Model):
    """Study session for activity tracking (decision engine)."""
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='study_sessions',
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='study_sessions',
    )
    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name='study_sessions',
        blank=True,
        null=True,
    )
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(blank=True, null=True)
    duration_seconds = models.PositiveIntegerField(default=0)
    questions_attempted = models.PositiveIntegerField(default=0)
    questions_correct = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.student_id} - {self.subject_id} @ {self.started_at}"


class StudentExamSettings(models.Model):
    """Exam date and target grade per student/subject (parent dashboard)."""
    GRADE_CHOICES = [(i, f'Grade {i}') for i in range(1, 10)]
    EXAM_BOARD_CHOICES = [
        ('aqa', 'AQA'),
        ('edexcel', 'Edexcel'),
        ('ocr', 'OCR'),
        ('wjec', 'WJEC'),
    ]
    TIER_CHOICES = [
        ('foundation', 'Foundation'),
        ('higher', 'Higher'),
    ]
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='learning_exam_settings',
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='learning_exam_settings',
    )
    exam_date = models.DateField(help_text='Expected exam date')
    target_grade = models.IntegerField(
        choices=GRADE_CHOICES,
        default=5,
        help_text='Target GCSE grade (1-9)',
    )
    exam_board = models.CharField(
        max_length=20,
        choices=EXAM_BOARD_CHOICES,
        default='aqa',
    )
    tier = models.CharField(
        max_length=20,
        choices=TIER_CHOICES,
        default='higher',
    )
    last_outlook_tier = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text='Last assigned outlook tier for hysteresis',
    )
    last_tier_change_date = models.DateField(
        blank=True,
        null=True,
        help_text='Date of last tier change',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'subject')

    def __str__(self):
        return f"{self.student_id} - {self.subject_id} (Grade {self.target_grade})"


class StudentExamDate(models.Model):
    """Individual exam date per student/subject (e.g. Paper 1, Paper 2)."""
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='exam_dates',
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='student_exam_dates',
    )
    exam_date = models.DateField(help_text='Date of this exam paper')
    paper_label = models.CharField(
        max_length=50,
        default='Paper 1',
        help_text='e.g. Paper 1, Paper 2',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['exam_date']
        unique_together = ('student', 'subject', 'paper_label')

    def __str__(self):
        return f"{self.student_id} - {self.subject.display_name} {self.paper_label} ({self.exam_date})"


class SkillNode(models.Model):
    """Micro-skill for step-level diagnostics."""
    code = models.CharField(max_length=50, unique=True)
    subject = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    difficulty_weight = models.FloatField(default=1.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.code} ({self.subject})"


class QuestionStep(models.Model):
    """Structured step within a question, mapped to a skill."""
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='steps',
    )
    step_order = models.PositiveIntegerField()
    skill = models.ForeignKey(
        SkillNode,
        on_delete=models.PROTECT,
        related_name='question_steps',
    )
    expected_expression = models.TextField(blank=True)
    hint_level_1 = models.TextField(blank=True)
    hint_level_2 = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['step_order']
        constraints = [
            models.UniqueConstraint(
                fields=['question', 'step_order'],
                name='unique_question_step_order'
            )
        ]

    def __str__(self):
        return f"Q{self.question_id} - Step {self.step_order} ({self.skill.code})"


class StudentSkillState(models.Model):
    """Per-student skill mastery tracking."""

    # Mastery thresholds (for future status transitions)
    MASTERY_MIN_ATTEMPTS = 8
    MASTERY_MIN_ACCURACY = 85
    MASTERY_MIN_STREAK = 3

    STATUS_CHOICES = [
        ('NEW', 'NEW'),
        ('LEARNING', 'LEARNING'),
        ('IMPROVING', 'IMPROVING'),
        ('MASTERED', 'MASTERED'),
        ('MAINTENANCE', 'MAINTENANCE'),
        ('AT_RISK', 'AT_RISK'),
    ]

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='skill_states',
    )
    skill = models.ForeignKey(
        SkillNode,
        on_delete=models.CASCADE,
        related_name='student_states',
    )
    attempts = models.IntegerField(default=0)
    failures = models.IntegerField(default=0)
    rolling_accuracy = models.FloatField(default=0.0)
    average_time_ms = models.FloatField(default=0.0)
    mastery_score = models.FloatField(default=0.0)
    last_attempt_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='NEW',
    )

    class Meta:
        unique_together = ('student', 'skill')

    def __str__(self):
        return f"{self.student_id} - {self.skill.code} (Mastery: {self.mastery_score:.1f})"


class MistakeBankItem(models.Model):
    """Persistent retry queue for questions where the student struggled."""

    REASON_CHOICES = [
        ('wrong', 'Wrong answer'),
        ('guess', 'Guessed'),
        ('slow', 'Too slow'),
        ('hint_used', 'Needed hint'),
        ('repeated_wrong', 'Repeated wrong answer'),
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('retrying', 'Retrying'),
        ('mastered', 'Mastered'),
        ('dismissed', 'Dismissed'),
    ]

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='mistake_bank_items',
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='mistake_bank_items',
    )
    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name='mistake_bank_items',
    )
    skill = models.ForeignKey(
        SkillNode,
        on_delete=models.SET_NULL,
        related_name='mistake_bank_items',
        null=True,
        blank=True,
    )
    reason = models.CharField(max_length=30, choices=REASON_CHOICES, default='wrong')
    wrong_category = models.CharField(max_length=50, blank=True)
    last_student_answer = models.TextField(blank=True)
    remediation_tip = models.TextField(blank=True)
    attempts_count = models.PositiveIntegerField(default=1)
    correct_retries = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    first_seen_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(auto_now=True)
    next_review_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('student', 'question')
        ordering = ['status', '-last_seen_at']

    def __str__(self):
        return f"{self.student_id} - Q{self.question_id} ({self.status})"


class StruggleEvent(models.Model):
    """One moment where the app detected hesitation, wrong work, or help need."""

    TRIGGER_CHOICES = [
        ('wrong_answer', 'Wrong answer'),
        ('slow_start', 'Slow start'),
        ('slow_submit', 'Slow submit'),
        ('hint_request', 'Hint request'),
        ('stuck_button', 'Stuck button'),
        ('repeated_wrong', 'Repeated wrong'),
    ]
    INTERVENTION_CHOICES = [
        ('none', 'None'),
        ('hint', 'Hint'),
        ('worked_example', 'Worked example'),
        ('video', 'Video'),
        ('retry_easier', 'Retry easier question'),
        ('retry_similar', 'Retry similar question'),
    ]

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='struggle_events',
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='struggle_events',
    )
    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name='struggle_events',
    )
    skill = models.ForeignKey(
        SkillNode,
        on_delete=models.SET_NULL,
        related_name='struggle_events',
        null=True,
        blank=True,
    )
    quiz_attempt = models.ForeignKey(
        QuizAttempt,
        on_delete=models.SET_NULL,
        related_name='struggle_events',
        null=True,
        blank=True,
    )
    trigger = models.CharField(max_length=30, choices=TRIGGER_CHOICES)
    stuck_point = models.CharField(max_length=200, blank=True)
    mistake_type = models.CharField(max_length=50, blank=True)
    confidence_level = models.CharField(max_length=20, blank=True)
    time_to_first_action_ms = models.PositiveIntegerField(null=True, blank=True)
    time_spent_ms = models.PositiveIntegerField(null=True, blank=True)
    student_answer = models.TextField(blank=True)
    diagnostic_message = models.TextField(blank=True)
    recommended_intervention = models.CharField(
        max_length=30,
        choices=INTERVENTION_CHOICES,
        default='none',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student_id} - Q{self.question_id} - {self.trigger}"


class SkillVideo(models.Model):
    """Short intervention video mapped to a subject/topic/skill."""

    title = models.CharField(max_length=200)
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='skill_videos',
        null=True,
        blank=True,
    )
    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name='skill_videos',
        null=True,
        blank=True,
    )
    skill = models.ForeignKey(
        SkillNode,
        on_delete=models.SET_NULL,
        related_name='skill_videos',
        null=True,
        blank=True,
    )
    exam_board = models.CharField(max_length=30, blank=True)
    tier = models.CharField(
        max_length=20,
        choices=[('foundation', 'Foundation'), ('higher', 'Higher'), ('both', 'Both')],
        default='both',
    )
    duration_seconds = models.PositiveIntegerField(default=90)
    video_url = models.URLField(max_length=500)
    thumbnail_url = models.URLField(max_length=500, blank=True)
    intervention_goal = models.CharField(
        max_length=200,
        blank=True,
        help_text='The exact stuck point this video fixes.',
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['subject__display_name', 'topic__order', 'title']

    def __str__(self):
        return self.title


class ParentDashboardSnapshot(models.Model):
    """Cached parent dashboard evaluation payload (keyed by student)."""
    student = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='parent_dashboard_snapshot',
    )
    payload = models.TextField()
    generated_at = models.DateTimeField()

    class Meta:
        verbose_name = 'Parent dashboard snapshot'

    def __str__(self):
        return f"Snapshot for student {self.student_id} at {self.generated_at}"
