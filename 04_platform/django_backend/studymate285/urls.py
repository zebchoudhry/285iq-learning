from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from learning.views import frontend_view, lessons_page, quiz_page, parent_dashboard_page, revision_planner_page, mock_tests_page, subjects_page, flashcards_page, mistakes_page, mistake_retry_page, exam_readiness_page, subject_detail_page
from learning.billing_views import (
    create_checkout_session,
    stripe_webhook,
    billing_status,
    billing_success_page,
    billing_cancel_page,
)
from users import views as user_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/', include('users.urls')),  # User authentication API endpoints
    path('api/billing/create-checkout-session/', create_checkout_session, name='billing-create-checkout'),
    path('api/billing/webhook/', stripe_webhook, name='billing-webhook'),
    path('api/billing/status/', billing_status, name='billing-status'),
    path('billing/success/', billing_success_page, name='billing-success'),
    path('billing/cancel/', billing_cancel_page, name='billing-cancel'),
    path('api/', include('learning.urls')),  # Learning API endpoints
    path('login/', user_views.login_page, name='login_page'),  # Login page
    path('register/', user_views.register_page, name='register_page'),  # Register page
    path('forgot-password/', user_views.forgot_password_page, name='forgot_password_page'),
    path('reset-password/', user_views.reset_password_page, name='reset_password_page'),
    path('settings/', user_views.settings_page, name='settings_page'),
    path('onboarding/exam-dates/', user_views.onboarding_exam_dates_page, name='onboarding_exam_dates_page'),
    path('lessons/', lessons_page, name='lessons_page'),
    path('quiz/', quiz_page, name='quiz_page'),
    path('subjects/', subjects_page, name='subjects_page'),
    path('subject/<int:subject_id>/', subject_detail_page, name='subject_detail_page'),
    path('practice/<int:subject_id>/', frontend_view, name='practice_subject_page'),
    path('practice/topic/<int:topic_id>/', frontend_view, name='practice_topic_page'),
    path('revision/', revision_planner_page, name='revision_planner_page'),
    path('exam-readiness/', exam_readiness_page, name='exam_readiness_page'),
    path('mock-tests/', mock_tests_page, name='mock_tests_page'),
    path('flashcards/', flashcards_page, name='flashcards_page'),
    path('mistakes/', mistakes_page, name='mistakes_page'),
    path('mistakes/retry/<int:item_id>/', mistake_retry_page, name='mistake_retry_page'),
    path('parent/<uuid:parent_access_token>/', parent_dashboard_page, name='parent_dashboard_page'),
    path('', frontend_view, name='frontend'),  # This serves your homepage
]

# Serve static files for the local packaged app. A production reverse proxy/CDN
# should serve these paths in a deployed environment.
for static_dir in getattr(settings, 'STATICFILES_DIRS', []):
    urlpatterns.append(
        re_path(r'^static/(?P<path>.*)$', serve, {'document_root': static_dir})
    )
urlpatterns.append(
    re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT})
)
