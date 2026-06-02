import logging
from datetime import date, timedelta

from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status

from .models import Classroom, Assignment, StudentAssignmentProgress
from .serializers import ClassroomSerializer, AssignmentSerializer

logger = logging.getLogger(__name__)


def _get_teacher_or_403(request):
    if not hasattr(request.user, 'teacher_profile'):
        return None, Response({'detail': 'Teacher account required.'}, status=status.HTTP_403_FORBIDDEN)
    return request.user.teacher_profile, None


def _week_completion_pct(classroom):
    week_ago = date.today() - timedelta(days=7)
    assignments = classroom.assignments.filter(is_active=True, due_date__gte=week_ago)
    if not assignments.exists():
        return 0
    student_ids = list(classroom.students.values_list('id', flat=True))
    if not student_ids:
        return 0
    total = assignments.count() * len(student_ids)
    completed = StudentAssignmentProgress.objects.filter(
        assignment__in=assignments,
        student_id__in=student_ids,
        completed=True,
    ).count()
    return round((completed / total) * 100, 1) if total else 0


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard(request):
    teacher, err = _get_teacher_or_403(request)
    if err:
        return err

    classrooms = teacher.classrooms.prefetch_related('students').select_related('subject')
    data = []
    for cr in classrooms:
        data.append({
            'id': cr.id,
            'name': cr.name,
            'subject': cr.subject.name if cr.subject else None,
            'class_code': cr.class_code,
            'student_count': cr.students.count(),
            'week_completion_pct': _week_completion_pct(cr),
        })
    return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_classroom(request):
    teacher, err = _get_teacher_or_403(request)
    if err:
        return err

    serializer = ClassroomSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    classroom = serializer.save(teacher=teacher)
    logger.info("Classroom %s created by teacher %s", classroom.id, teacher.id)
    return Response(ClassroomSerializer(classroom).data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def classroom_students(request, classroom_id):
    teacher, err = _get_teacher_or_403(request)
    if err:
        return err

    classroom = get_object_or_404(Classroom, id=classroom_id, teacher=teacher)
    from learning.models import Topic, StudentExamSettings
    from users.models import StudentTopicPerformance

    subject = classroom.subject
    topic_count = Topic.objects.filter(subject=subject).count() if subject else 0

    students = classroom.students.prefetch_related('profile').all()
    data = []
    for student in students:
        xp = getattr(getattr(student, 'profile', None), 'total_xp', 0)
        streak = getattr(getattr(student, 'profile', None), 'daily_streak', 0)

        if topic_count > 0:
            covered = StudentTopicPerformance.objects.filter(
                student=student,
                topic__subject=subject,
                questions_attempted__gt=0,
            ).count()
            coverage_pct = round((covered / topic_count) * 100, 1)
        else:
            coverage_pct = 0

        data.append({
            'id': student.id,
            'username': student.username,
            'email': student.email,
            'xp': xp,
            'streak': streak,
            'topic_coverage_pct': coverage_pct,
        })
    return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_assignment(request, classroom_id):
    teacher, err = _get_teacher_or_403(request)
    if err:
        return err

    classroom = get_object_or_404(Classroom, id=classroom_id, teacher=teacher)
    serializer = AssignmentSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    assignment = serializer.save(classroom=classroom)
    logger.info("Assignment %s created for classroom %s", assignment.id, classroom.id)
    return Response(AssignmentSerializer(assignment).data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def at_risk_students(request, classroom_id):
    teacher, err = _get_teacher_or_403(request)
    if err:
        return err

    classroom = get_object_or_404(Classroom, id=classroom_id, teacher=teacher)
    from learning.models import StudentExamSettings

    student_ids = list(classroom.students.values_list('id', flat=True))
    at_risk_ids = StudentExamSettings.objects.filter(
        student_id__in=student_ids,
        last_outlook_tier='AT_RISK',
    ).values_list('student_id', flat=True).distinct()

    from django.contrib.auth import get_user_model
    User = get_user_model()
    students = User.objects.filter(id__in=at_risk_ids)
    data = [{'id': s.id, 'username': s.username, 'email': s.email} for s in students]
    return Response(data)


@api_view(['POST'])
@permission_classes([AllowAny])
def join_classroom(request, classroom_id):
    class_code = request.data.get('class_code', '').strip().upper()
    if not class_code:
        return Response({'detail': 'class_code is required.'}, status=status.HTTP_400_BAD_REQUEST)

    classroom = get_object_or_404(Classroom, id=classroom_id, class_code=class_code)

    if not request.user.is_authenticated:
        return Response({'detail': 'Authentication required to join.'}, status=status.HTTP_401_UNAUTHORIZED)

    classroom.students.add(request.user)
    logger.info("Student %s joined classroom %s", request.user.id, classroom.id)
    return Response({'detail': 'Joined classroom successfully.'})
