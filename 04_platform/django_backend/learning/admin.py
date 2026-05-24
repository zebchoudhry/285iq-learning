from django.contrib import admin
from .models import (
    Subject, Topic, Lesson, Flashcard, Question, MultipleChoiceOption, StudentProgress,
    QuizAttempt, StudentGymState, StudySession, StudentExamSettings, StudentExamDate,
    SkillNode, QuestionStep, StudentSkillState, MistakeBankItem, StruggleEvent, SkillVideo,
)

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'name', 'tier', 'is_active', 'created_at']
    list_filter = ['is_active', 'tier']
    search_fields = ['display_name', 'name']


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ['name', 'subject', 'order', 'is_active']
    list_filter = ['subject', 'is_active']
    search_fields = ['name', 'subject__display_name']
    ordering = ['subject', 'order']


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['title', 'topic', 'lesson_type', 'difficulty_level', 'estimated_duration', 'video_url']
    list_filter = ['topic__subject', 'lesson_type', 'difficulty_level', 'is_active']
    search_fields = ['title', 'topic__name']
    ordering = ['topic', 'order']


@admin.register(Flashcard)
class FlashcardAdmin(admin.ModelAdmin):
    list_display = ['front_short', 'topic', 'order', 'is_active', 'created_at']
    list_filter = ['topic__subject', 'is_active']
    search_fields = ['front', 'back', 'topic__name']
    ordering = ['topic', 'order']

    def front_short(self, obj):
        return obj.front[:60] + "..." if len(obj.front) > 60 else obj.front
    front_short.short_description = "Front"


class MultipleChoiceOptionInline(admin.TabularInline):
    model = MultipleChoiceOption
    extra = 4


class QuestionStepInline(admin.TabularInline):
    model = QuestionStep
    extra = 1
    fields = ['step_order', 'skill', 'expected_expression', 'hint_level_1', 'hint_level_2']
    ordering = ['step_order']


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = [
        'question_text_short',
        'lesson',
        'question_type',
        'difficulty_level',
        'marks_available',
        'exam_board_display',
        'correct_answer_short'
    ]
    list_filter = ['lesson__topic__subject', 'question_type', 'difficulty_level']
    search_fields = ['question_text', 'lesson__title', 'correct_answer', 'explanation']
    inlines = [MultipleChoiceOptionInline, QuestionStepInline]

    def question_text_short(self, obj):
        return obj.question_text[:80] + "..." if len(obj.question_text) > 80 else obj.question_text
    question_text_short.short_description = "Question"

    def correct_answer_short(self, obj):
        return obj.correct_answer[:80] + "..." if obj.correct_answer and len(obj.correct_answer) > 80 else obj.correct_answer
    correct_answer_short.short_description = "Correct Answer"

    def exam_board_display(self, obj):
        if obj.is_shared:
            return "All boards"
        codes = list(obj.specific_exam_boards.values_list('code', flat=True)[:3])
        return ", ".join(codes) if codes else "—"
    exam_board_display.short_description = "Exam board"


@admin.register(StudentProgress)
class StudentProgressAdmin(admin.ModelAdmin):
    list_display = ['student', 'lesson', 'is_completed', 'average_grade', 'completion_date', 'success_rate']
    list_filter = ['is_completed', 'lesson__topic__subject']
    search_fields = ['student__username', 'lesson__title']


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ['student', 'question', 'is_correct', 'error_type', 'attempted_at']
    list_filter = ['is_correct', 'error_type', 'attempted_at']
    search_fields = ['student__username', 'question__question_text']
    ordering = ['-attempted_at']


@admin.register(StudentGymState)
class StudentGymStateAdmin(admin.ModelAdmin):
    list_display = ['student', 'topic', 'current_mode', 'confirmation_count', 'updated_at']
    list_filter = ['current_mode']
    search_fields = ['student__username', 'topic__name']


@admin.register(StudySession)
class StudySessionAdmin(admin.ModelAdmin):
    list_display = ['student', 'subject', 'topic', 'started_at', 'duration_seconds', 'questions_attempted']
    list_filter = ['subject', 'started_at']
    search_fields = ['student__username', 'subject__display_name']
    ordering = ['-started_at']


@admin.register(StudentExamSettings)
class StudentExamSettingsAdmin(admin.ModelAdmin):
    list_display = ['student', 'subject', 'exam_date', 'target_grade', 'exam_board', 'tier']
    list_filter = ['exam_board', 'tier', 'target_grade']
    search_fields = ['student__username', 'subject__display_name']


@admin.register(StudentExamDate)
class StudentExamDateAdmin(admin.ModelAdmin):
    list_display = ['student', 'subject', 'paper_label', 'exam_date', 'created_at']
    list_filter = ['subject', 'exam_date']
    search_fields = ['student__username', 'subject__display_name']


@admin.register(SkillNode)
class SkillNodeAdmin(admin.ModelAdmin):
    list_display = ['code', 'subject', 'difficulty_weight', 'created_at', 'updated_at']
    list_filter = ['subject']
    search_fields = ['code', 'subject', 'description']
    ordering = ['subject', 'code']


@admin.register(QuestionStep)
class QuestionStepAdmin(admin.ModelAdmin):
    list_display = ['question_display', 'step_order', 'skill', 'created_at']
    list_filter = ['skill__subject', 'skill']
    search_fields = ['question__question_text', 'skill__code', 'expected_expression']
    ordering = ['question', 'step_order']

    def question_display(self, obj):
        return f"Q{obj.question_id} ({obj.question.lesson.title})"
    question_display.short_description = "Question"


@admin.register(StudentSkillState)
class StudentSkillStateAdmin(admin.ModelAdmin):
    list_display = ['student', 'skill', 'attempts', 'failures', 'rolling_accuracy_display', 'mastery_score_display', 'last_attempt_at']
    list_filter = ['skill__subject', 'skill']
    search_fields = ['student__username', 'skill__code']
    ordering = ['-mastery_score', '-rolling_accuracy']

    def rolling_accuracy_display(self, obj):
        return f"{obj.rolling_accuracy:.1f}%"
    rolling_accuracy_display.short_description = "Rolling Accuracy"

    def mastery_score_display(self, obj):
        return f"{obj.mastery_score:.2f}"
    mastery_score_display.short_description = "Mastery Score"


@admin.register(MistakeBankItem)
class MistakeBankItemAdmin(admin.ModelAdmin):
    list_display = [
        'student',
        'question',
        'topic',
        'skill',
        'reason',
        'wrong_category',
        'status',
        'attempts_count',
        'correct_retries',
        'last_seen_at',
    ]
    list_filter = ['status', 'reason', 'wrong_category', 'topic__subject']
    search_fields = ['student__username', 'question__question_text', 'skill__code', 'topic__name']
    ordering = ['status', '-last_seen_at']


@admin.register(StruggleEvent)
class StruggleEventAdmin(admin.ModelAdmin):
    list_display = [
        'student',
        'question',
        'topic',
        'skill',
        'trigger',
        'mistake_type',
        'recommended_intervention',
        'created_at',
    ]
    list_filter = ['trigger', 'mistake_type', 'recommended_intervention', 'topic__subject']
    search_fields = ['student__username', 'question__question_text', 'skill__code', 'stuck_point']
    ordering = ['-created_at']


@admin.register(SkillVideo)
class SkillVideoAdmin(admin.ModelAdmin):
    list_display = ['title', 'subject', 'topic', 'skill', 'tier', 'duration_seconds', 'is_active']
    list_filter = ['is_active', 'subject', 'tier', 'exam_board']
    search_fields = ['title', 'topic__name', 'subject__display_name', 'skill__code', 'intervention_goal']
    ordering = ['subject__display_name', 'topic__order', 'title']
