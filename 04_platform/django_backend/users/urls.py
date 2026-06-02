"""
URLs for users app - Authentication endpoints
"""
from django.urls import path
from . import views
from . import friend_views

app_name = 'users'

urlpatterns = [
    # Authentication API endpoints (mounted at /api/users/ in main urls.py)
    path('auth/register/', views.register, name='register'),
    path('auth/login/', views.login_view, name='login'),
    path('auth/logout/', views.logout_view, name='logout'),
    path('auth/current-user/', views.current_user, name='current_user'),
    path('auth/password-reset/', views.password_reset_request, name='password_reset'),
    path('auth/password-reset/confirm/', views.password_reset_confirm, name='password_reset_confirm'),
    path('onboarding/exam-dates/', views.onboarding_exam_dates_submit, name='onboarding_exam_dates_submit'),
    path('me/settings/', views.my_settings, name='my_settings'),
    path('me/settings/<int:subject_id>/', views.update_my_settings, name='update_my_settings'),
    
    # AI Tutor endpoint
    path('ai-tutor/', views.ai_tutor_chat, name='ai_tutor'),

    # Social friends layer
    path('friends/request/', friend_views.send_friend_request, name='friend-request'),
    path('friends/accept/', friend_views.accept_friend_request, name='friend-accept'),
    path('friends/', friend_views.friends_list, name='friends-list'),
    path('friends/leaderboard/', friend_views.friends_leaderboard, name='friends-leaderboard'),
]
