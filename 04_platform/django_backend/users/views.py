"""
Views for users app - Authentication and User Management
"""
import logging

logger = logging.getLogger(__name__)

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator

from .serializers import (
    UserRegistrationSerializer,
    UserSerializer,
    LoginSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    OnboardingExamDatesSerializer,
)
from .models import UserProfile

User = get_user_model()


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """User registration endpoint"""
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        student = serializer.save()
        # Save parent_email if provided
        data = request.data
        if data.get('parent_email'):
            student.parent_email = data['parent_email']
            student.save(update_fields=['parent_email'])
        # Send welcome email to parent if parent_email is present
        if student.parent_email:
            try:
                dashboard_url = f"https://285iq.com/parent/{student.parent_access_token}/"
                send_mail(
                    subject=f"285IQ: Track {student.display_name}'s GCSE revision",
                    message=(
                        f"Hi,\n\n"
                        f"{student.display_name} has started using 285IQ for GCSE revision.\n\n"
                        f"You can track their progress, see their predicted grades, and get weekly updates here:\n"
                        f"{dashboard_url}\n\n"
                        f"No account needed — just bookmark the link above.\n\n"
                        f"The 285IQ Team"
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[student.parent_email],
                    fail_silently=True,
                )
            except Exception as e:
                logger.warning("Failed to send parent welcome email for user %s: %s", student.username, e)
        # Auto-login after registration
        login(request, student)
        user_serializer = UserSerializer(student)
        return Response({
            'message': 'Registration successful',
            'user': user_serializer.data
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """User login endpoint"""
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            user_serializer = UserSerializer(user)
            return Response({
                'message': 'Login successful',
                'user': user_serializer.data
            })
        else:
            return Response({
                'error': 'Invalid username or password'
            }, status=status.HTTP_401_UNAUTHORIZED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """User logout endpoint"""
    logout(request)
    return Response({'message': 'Logout successful'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user(request):
    """Get current authenticated user"""
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_request(request):
    """Request a password reset email. Does not reveal whether email exists."""
    serializer = PasswordResetRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    email = serializer.validated_data['email']
    user = User.objects.filter(email__iexact=email).first()
    if user:
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        reset_link = f"{request.scheme}://{request.get_host()}/reset-password/?uid={uid}&token={token}"
        try:
            send_mail(
                subject='285IQ Password Reset',
                message=f'Use this link to reset your password: {reset_link}\n\nLink expires in 24 hours.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=True,
            )
        except Exception:
            pass  # In dev without email backend, fail silently
    # Always return same message for anonymity
    return Response({'message': 'If an account exists with this email, you will receive reset instructions.'})


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_confirm(request):
    """Confirm password reset with uid and token."""
    serializer = PasswordResetConfirmSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    try:
        uid = force_str(urlsafe_base64_decode(serializer.validated_data['uid']))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return Response({'error': 'Invalid or expired reset link'}, status=status.HTTP_400_BAD_REQUEST)
    if not default_token_generator.check_token(user, serializer.validated_data['token']):
        return Response({'error': 'Invalid or expired reset link'}, status=status.HTTP_400_BAD_REQUEST)
    user.set_password(serializer.validated_data['new_password'])
    user.save()
    return Response({'message': 'Password has been reset. You can now log in.'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def placeholder_view(request):
    """Placeholder view - will be replaced with real functionality"""
    return Response({
        'message': f'Users app is ready!',
        'status': 'placeholder'
    })


# Template views for login/register pages
from django.shortcuts import render, redirect

def login_page(request):
    """Render login page"""
    if request.user.is_authenticated:
        return redirect('/')
    return render(request, 'login.html')


def register_page(request):
    """Render register page"""
    if request.user.is_authenticated:
        return redirect('/')
    return render(request, 'register.html')


def reset_password_page(request):
    """Render reset password page (from email link with uid and token)"""
    if request.user.is_authenticated:
        return redirect('/')
    return render(request, 'reset_password.html')


def forgot_password_page(request):
    """Render forgot password page (request reset email)"""
    if request.user.is_authenticated:
        return redirect('/')
    return render(request, 'forgot_password.html')


def settings_page(request):
    """Render settings page (exam settings, logout)."""
    if not request.user.is_authenticated:
        return redirect(settings.LOGIN_URL)
    return render(request, 'settings.html')


def onboarding_exam_dates_page(request):
    """Render exam dates onboarding (Paper 1/2 per subject). Redirect to / if onboarding complete."""
    if not request.user.is_authenticated:
        return redirect(settings.LOGIN_URL)
    from learning.models import StudentExamSettings
    if StudentExamSettings.objects.filter(student=request.user).exists():
        return redirect('/')
    return render(request, 'onboarding_exam_dates.html')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def onboarding_exam_dates_submit(request):
    """Create/update StudentExamSettings and StudentExamDate from onboarding form."""
    serializer = OnboardingExamDatesSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    from learning.models import Subject, StudentExamSettings, StudentExamDate
    student = request.user
    for subj_data in serializer.validated_data['subjects']:
        subject_id = subj_data['subject_id']
        try:
            subject = Subject.objects.get(id=subject_id, is_active=True)
        except Subject.DoesNotExist:
            return Response({'error': f'Subject id {subject_id} not found'}, status=status.HTTP_400_BAD_REQUEST)
        target_grade = subj_data['target_grade']
        exam_dates_list = subj_data['exam_dates']
        if not exam_dates_list:
            continue
        earliest = min(ed['exam_date'] for ed in exam_dates_list)
        settings_obj, _ = StudentExamSettings.objects.update_or_create(
            student=student,
            subject=subject,
            defaults={
                'exam_date': earliest,
                'target_grade': target_grade,
                'exam_board': 'aqa',
                'tier': 'higher',
            },
        )
        StudentExamDate.objects.filter(student=student, subject=subject).delete()
        for ed in exam_dates_list:
            StudentExamDate.objects.create(
                student=student,
                subject=subject,
                exam_date=ed['exam_date'],
                paper_label=ed.get('paper_label') or 'Paper 1',
            )
    return Response({'message': 'Exam dates saved.', 'redirect': '/'}, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_settings(request):
    """Return current user's exam settings per subject."""
    from learning.models import StudentExamSettings, StudentExamDate
    settings_qs = StudentExamSettings.objects.filter(student=request.user).select_related('subject')
    out = []
    for s in settings_qs:
        dates = list(
            StudentExamDate.objects.filter(student=request.user, subject=s.subject)
            .order_by('exam_date')
            .values('exam_date', 'paper_label')
        )
        exam_dates = [{'exam_date': d['exam_date'].isoformat(), 'paper_label': d['paper_label']} for d in dates]
        if not exam_dates and s.exam_date:
            exam_dates = [{'exam_date': s.exam_date.isoformat(), 'paper_label': 'Paper 1'}]
        out.append({
            'subject_id': s.subject_id,
            'subject_name': s.subject.display_name,
            'exam_date': s.exam_date.isoformat() if s.exam_date else None,
            'target_grade': s.target_grade,
            'exam_board': s.exam_board,
            'tier': s.tier,
            'exam_dates': exam_dates,
        })
    return Response({'settings': out})


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_my_settings(request, subject_id: int):
    """Update exam settings for current user and subject."""
    from learning.models import StudentExamSettings, StudentExamDate, Subject
    try:
        subject = Subject.objects.get(id=subject_id, is_active=True)
    except Subject.DoesNotExist:
        return Response({'error': 'Subject not found'}, status=status.HTTP_404_NOT_FOUND)
    from datetime import date
    ed = request.data.get('exam_date')
    ed_val = date.fromisoformat(str(ed)) if ed else date.today()
    setting, _ = StudentExamSettings.objects.get_or_create(
        student=request.user,
        subject=subject,
        defaults={'exam_date': ed_val, 'target_grade': int(request.data.get('target_grade', 5)), 'exam_board': 'aqa', 'tier': 'higher'}
    )
    if 'exam_date' in request.data:
        ed = request.data['exam_date']
        setting.exam_date = date.fromisoformat(str(ed)) if ed else setting.exam_date
    if 'target_grade' in request.data:
        setting.target_grade = int(request.data['target_grade'])
    if 'exam_board' in request.data:
        setting.exam_board = request.data['exam_board']
    if 'tier' in request.data:
        setting.tier = request.data['tier']
    setting.save()
    exam_dates = request.data.get('exam_dates', [])
    if exam_dates:
        StudentExamDate.objects.filter(student=request.user, subject=subject).delete()
        for ed_item in exam_dates:
            d = ed_item.get('exam_date') or setting.exam_date
            d = date.fromisoformat(str(d)) if d else setting.exam_date
            StudentExamDate.objects.create(
                student=request.user,
                subject=subject,
                exam_date=d,
                paper_label=ed_item.get('paper_label', 'Paper 1'),
            )
        dates_only = [ed_item.get('exam_date') for ed_item in exam_dates if ed_item.get('exam_date')]
        if dates_only:
            setting.exam_date = min(d if isinstance(d, date) else date.fromisoformat(str(d)) for d in dates_only)
            setting.save()
    return Response({
        'message': 'Settings updated',
        'settings': {
            'subject_id': subject_id,
            'exam_date': setting.exam_date.isoformat(),
            'target_grade': setting.target_grade,
        },
    })


# AI Tutor view (placeholder - will be implemented later)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ai_tutor_chat(request):
    """AI tutor chat endpoint - requires authentication"""
    # TODO: Implement AI tutor functionality
    return Response({
        'response': 'AI Tutor feature coming soon!',
        'recommended_lesson': None,
        'weak_areas': []
    })