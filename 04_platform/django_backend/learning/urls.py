from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import parent_dashboard_views
from . import parent_export_views
from . import admin_content_views

# Create router for ViewSets
router = DefaultRouter()
router.register(r'subjects', views.SubjectViewSet, basename='subject')
router.register(r'topics', views.TopicViewSet, basename='topic')
router.register(r'lessons', views.LessonViewSet, basename='lesson')
router.register(r'questions', views.QuestionViewSet, basename='question')

urlpatterns = [
    # REST API routes (ViewSets)
    path('', include(router.urls)),
    
    # Custom API endpoints
    path('subject/<int:subject_id>/topics/', views.get_subject_topics, name='subject-topics'),
    path('subject/<int:subject_id>/detail/', views.get_subject_detail, name='subject-detail'),
    path('topic/<int:topic_id>/lessons/', views.get_topic_lessons, name='topic-lessons'),
    path('flashcards/decks/', views.flashcard_decks, name='flashcard-decks'),
    path('flashcards/topic/<int:topic_id>/', views.flashcard_list, name='flashcard-list'),
    path('flashcards/topic/<int:topic_id>/due/', views.flashcards_due, name='flashcard-due'),
    path('flashcards/due-count/', views.flashcards_due_count, name='flashcards-due-count'),
    path('flashcards/review/', views.flashcard_review, name='flashcard-review'),
    path('lesson/<int:lesson_id>/', views.get_lesson_content, name='lesson-content'),
    path('lesson/<int:lesson_id>/complete/', views.lesson_complete, name='lesson-complete'),
    path('lesson/<int:lesson_id>/questions/', views.lesson_questions, name='lesson-questions'),
    path('subject-progress/', views.subject_progress, name='subject-progress'),
    path('weak-areas/', views.weak_areas, name='weak-areas'),
    path('mistake-bank/', views.mistake_bank, name='mistake-bank'),
    path('mistake-bank/<int:item_id>/status/', views.mark_mistake_bank_item, name='mark-mistake-bank-item'),
    path('mistake-bank/<int:item_id>/retry/', views.mistake_bank_retry_question, name='mistake-bank-retry-question'),
    path('mistake-bank/<int:item_id>/retry/submit/', views.submit_mistake_bank_retry, name='submit-mistake-bank-retry'),
    path('struggle-events/', views.struggle_events, name='struggle-events'),
    path('struggle/report-stuck/', views.report_stuck, name='report-stuck'),
    path('mission/', views.mission, name='mission'),
    path('loop-metrics/', views.loop_metrics, name='loop-metrics'),
    path('loop-metrics/summary/', views.loop_metrics_summary, name='loop-metrics-summary'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('revision-summary/', views.revision_summary, name='revision-summary'),
    path('exam-readiness/', views.exam_readiness, name='exam-readiness'),
    path('past-papers/', views.past_papers_list, name='past-papers-list'),
    path('tutor/chat/', views.tutor_chat, name='tutor-chat'),
    path('tutor/explain-wrong/', views.tutor_explain_wrong, name='tutor-explain-wrong'),
    path('tutor/diagnose-stuck/', views.tutor_diagnose_stuck, name='tutor-diagnose-stuck'),
    path('strength/<int:topic_id>/', views.topic_strength, name='topic-strength'),
    path('questions/<int:question_id>/worked-solution/', views.worked_solution, name='worked-solution'),

    # Quiz
    path('quiz/start/', views.quiz_start, name='quiz-start'),
    path('quiz/question/<int:question_id>/', views.quiz_question, name='quiz-question'),
    path('attempts/', views.submit_attempt, name='submit-attempt'),
    
    # Practice (6-question adaptive)
    path('practice/start/', views.practice_start, name='practice-start'),
    
    # Parent Dashboard API (token-based)
    path('parent/dashboard/<uuid:parent_access_token>/', 
         parent_dashboard_views.parent_dashboard, 
         name='parent-dashboard'),
    
    path('parent/subject/<uuid:parent_access_token>/<int:subject_id>/', 
         parent_dashboard_views.subject_outlook, 
         name='subject-outlook'),
    
    path('parent/settings/<uuid:parent_access_token>/<int:subject_id>/',
         parent_dashboard_views.update_exam_settings,
         name='update-exam-settings'),

    path('parent/export/<uuid:parent_access_token>/pdf/',
         parent_export_views.parent_export_pdf,
         name='parent-export-pdf'),

    path('predicted-grade/', views.predicted_grade_view, name='predicted-grade'),
    path('revision-timetable/', views.revision_timetable_view, name='revision-timetable'),

    # Staff-only content management
    path('admin/generate-questions/', admin_content_views.admin_generate_questions, name='admin-generate-questions'),
    path('admin/question-stats/', admin_content_views.admin_question_stats, name='admin-question-stats'),

    # Mock exams (past papers)
    path('mock-exams/', views.mock_exams_list, name='mock-exams-list'),
    path('mock-exams/start/', views.mock_exam_start, name='mock-exam-start'),
    path('mock-exams/attempt/<int:attempt_id>/question/<int:question_id>/', views.mock_exam_question, name='mock-exam-question'),
    path('mock-exams/attempt/<int:attempt_id>/submit/', views.mock_exam_submit, name='mock-exam-submit'),
]
