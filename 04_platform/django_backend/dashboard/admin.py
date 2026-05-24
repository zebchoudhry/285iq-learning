from django.contrib import admin
from .models import MockExam, MockExamAttempt, MockExamQuestion, MockExamAttemptAnswer, PastPaper


class MockExamQuestionInline(admin.TabularInline):
    model = MockExamQuestion
    extra = 0
    raw_id_fields = ('question',)
    ordering = ('order',)


@admin.register(PastPaper)
class PastPaperAdmin(admin.ModelAdmin):
    list_display = ['title', 'subject', 'exam_board', 'year', 'paper_number', 'is_active']
    list_filter = ['subject', 'exam_board', 'is_active']
    search_fields = ['title']


@admin.register(MockExam)
class MockExamAdmin(admin.ModelAdmin):
    list_display = ['title', 'subject', 'exam_board', 'time_allowed_minutes', 'total_marks', 'is_active']
    list_filter = ['is_active', 'subject']
    inlines = [MockExamQuestionInline]


@admin.register(MockExamAttempt)
class MockExamAttemptAdmin(admin.ModelAdmin):
    list_display = ['student', 'mock_exam', 'status', 'marks_achieved', 'total_marks_available', 'started_at']
    list_filter = ['status']


@admin.register(MockExamQuestion)
class MockExamQuestionAdmin(admin.ModelAdmin):
    list_display = ['mock_exam', 'question', 'order', 'marks']
    list_filter = ['mock_exam']
    raw_id_fields = ('question',)


@admin.register(MockExamAttemptAnswer)
class MockExamAttemptAnswerAdmin(admin.ModelAdmin):
    list_display = ['attempt', 'question', 'marks_achieved', 'correct']
    list_filter = ['correct']
