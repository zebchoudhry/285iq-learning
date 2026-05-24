from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import parent_dashboard_views

# import at top if not present:
from . import views
# ...
# add route (order doesn't matter much)
path('leaderboard/', views.leaderboard, name='leaderboard'),

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
    path('topic/<int:topic_id>/lessons/', views.get_topic_lessons, name='topic-lessons'),
    path('lesson/<int:lesson_id>/', views.get_lesson_content, name='lesson-content'),
    
    # Parent Dashboard API
    path('parent/dashboard/<int:student_id>/', 
         parent_dashboard_views.parent_dashboard, 
         name='parent-dashboard'),
    
    path('parent/subject/<int:student_id>/<int:subject_id>/', 
         parent_dashboard_views.subject_outlook, 
         name='subject-outlook'),
    
    path('parent/settings/<int:student_id>/<int:subject_id>/', 
         parent_dashboard_views.update_exam_settings, 
         name='update-exam-settings'),
]
