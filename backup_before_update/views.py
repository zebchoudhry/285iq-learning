
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action, permission_classes, api_view
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import Subject, Topic, Lesson, Question, StudentProgress
from .serializers import SubjectSerializer, TopicSerializer, LessonSerializer, QuestionSerializer

# add near other imports at top of file
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.contrib.auth import get_user_model

# new leaderboard view
@api_view(['GET'])
@permission_classes([AllowAny])
def leaderboard(request):
    """
    Return top students ordered by profile.total_xp (descending).
    Optional query param: ?limit=10
    """
    User = get_user_model()
    try:
        limit = int(request.query_params.get('limit', 10))
    except (TypeError, ValueError):
        limit = 10

    # select_related for profile to avoid extra queries
    qs = User.objects.all().select_related('profile').order_by('-profile__total_xp')[:limit]

    results = []
    for u in qs:
        prof = getattr(u, 'profile', None)
        results.append({
            'id': u.id,
            'username': u.username,
            'first_name': u.first_name,
            'last_name': u.last_name,
            'grade_level': getattr(u, 'grade_level', None),
            'profile': {
                'total_xp': prof.total_xp if prof else 0,
                'current_level': prof.current_level if prof else None
            }
        })

    return Response(results)


@login_required
def frontend_view(request):
    """Dashboard view - requires authentication"""
    return render(request, 'index.html')

class SubjectViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Subject.objects.filter(is_active=True)
    serializer_class = SubjectSerializer

class TopicViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Topic.objects.filter(is_active=True)
    serializer_class = TopicSerializer
    
    @action(detail=False, methods=['get'])
    def by_subject(self, request):
        subject_id = request.query_params.get('subject_id')
        if subject_id:
            topics = Topic.objects.filter(subject_id=subject_id, is_active=True).order_by('order')
            serializer = self.get_serializer(topics, many=True)
            return Response(serializer.data)
        return Response({'error': 'subject_id parameter required'}, status=400)

class LessonViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Lesson.objects.filter(is_active=True)
    serializer_class = LessonSerializer
    
    @action(detail=False, methods=['get'])
    def by_topic(self, request):
        topic_id = request.query_params.get('topic_id')
        if topic_id:
            lessons = Lesson.objects.filter(topic_id=topic_id, is_active=True).order_by('order')
            serializer = self.get_serializer(lessons, many=True)
            return Response(serializer.data)
        return Response({'error': 'topic_id parameter required'}, status=400)

class QuestionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Question.objects.filter(is_active=True)
    serializer_class = QuestionSerializer
    
    @action(detail=False, methods=['get'])
    def by_lesson(self, request):
        lesson_id = request.query_params.get('lesson_id')
        if lesson_id:
            questions = Question.objects.filter(lesson_id=lesson_id, is_active=True)
            serializer = self.get_serializer(questions, many=True)
            return Response(serializer.data)
        return Response({'error': 'lesson_id parameter required'}, status=400)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_subject_topics(request, subject_id):
    """API: Get all topics for a subject"""
    try:
        subject = Subject.objects.get(id=subject_id)
        topics = Topic.objects.filter(subject=subject, is_active=True).order_by('order')
        
        data = {
            'subject_id': subject.id,
            'subject_name': subject.display_name,
            'topics': [{
                'id': t.id,
                'name': t.name,
                'description': t.description,
                'order': t.order,
                'lesson_count': Lesson.objects.filter(topic=t, is_active=True).count()
            } for t in topics]
        }
        return Response(data)
    except Subject.DoesNotExist:
        return Response({'error': 'Subject not found'}, status=404)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_topic_lessons(request, topic_id):
    """API: Get all lessons for a topic"""
    try:
        topic = Topic.objects.get(id=topic_id)
        lessons = Lesson.objects.filter(topic=topic, is_active=True).order_by('order')
        
        data = {
            'topic_id': topic.id,
            'topic_name': topic.name,
            'subject_name': topic.subject.display_name,
            'lessons': [{
                'id': l.id,
                'title': l.title,
                'duration': l.estimated_duration,
                'lesson_type': l.get_lesson_type_display(),
                'order': l.order
            } for l in lessons]
        }
        return Response(data)
    except Topic.DoesNotExist:
        return Response({'error': 'Topic not found'}, status=404)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_lesson_content(request, lesson_id):
    """API: Get full lesson content"""
    try:
        lesson = Lesson.objects.get(id=lesson_id)
        
        data = {
            'id': lesson.id,
            'title': lesson.title,
            'content': lesson.content,
            'duration': lesson.estimated_duration,
            'lesson_type': lesson.get_lesson_type_display(),
            'difficulty_level': lesson.get_difficulty_level_display(),
            'key_skills': lesson.key_skills,
            'topic_name': lesson.topic.name,
            'subject_name': lesson.topic.subject.display_name
        }
        return Response(data)
    except Lesson.DoesNotExist:
        return Response({'error': 'Lesson not found'}, status=404)


@login_required
def lessons_page(request):
    """Render the lessons navigation page"""
    return render(request, 'lessons.html')