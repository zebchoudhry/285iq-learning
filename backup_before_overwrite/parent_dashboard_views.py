"""
Parent Dashboard API Views - Allow unauthenticated access for parents
"""

from datetime import date
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from django.shortcuts import get_object_or_404

from learning.models import StudentExamSettings, Subject
from users.models import Student
from decision_engine.v1_0.decision_engine_v1 import evaluate_student_subject
from decision_engine.v1_0.core import generate_recommendations, PerformanceTrend


@api_view(['GET'])
@permission_classes([AllowAny])  # Parents may not be users
def parent_dashboard(request, student_id: int):
    """Get comprehensive parent dashboard for a student."""
    
    student = get_object_or_404(Student, id=student_id)
    exam_settings = StudentExamSettings.objects.filter(student=student).select_related('subject')
    
    if not exam_settings.exists():
        return Response({
            "student_id": student_id,
            "student_name": student.username,
            "message": "No exam settings configured",
            "subjects": []
        })
    
    subject_outlooks = []
    
    for setting in exam_settings:
        try:
            evaluation = evaluate_student_subject(
                student_id=student_id,
                subject_id=setting.subject_id,
                exam_date=setting.exam_date,
                target_grade=setting.target_grade,
                previous_tier=setting.last_outlook_tier
            )
            
            recommendations = generate_recommendations(
                attainment_band=evaluation['attainment_band'],
                target_grade=setting.target_grade,
                trend=PerformanceTrend(evaluation['trend']),
                weeks_remaining=evaluation['weeks_remaining'],
                topic_performances=[]
            )
            
            subject_outlooks.append({
                "subject_id": setting.subject_id,
                "subject_name": setting.subject.display_name,
                "exam_date": setting.exam_date.isoformat(),
                "target_grade": setting.target_grade,
                "weeks_remaining": evaluation['weeks_remaining'],
                "outlook": {
                    "tier": evaluation['tier'],
                    "reason": evaluation['reason'],
                    "attainment_band": evaluation['attainment_band'],
                    "trend": evaluation['trend'],
                },
                "activity": {
                    "sessions_per_week": evaluation['activity_per_week'],
                    "coverage_breadth": round(evaluation['coverage_breadth'] * 100, 1),
                },
                "recommendations": recommendations
            })
        except Exception as e:
            subject_outlooks.append({
                "subject_id": setting.subject_id,
                "subject_name": setting.subject.display_name,
                "error": str(e)
            })
    
    return Response({
        "student_id": student_id,
        "student_name": student.username,
        "generated_at": date.today().isoformat(),
        "subjects": subject_outlooks
    })


@api_view(['GET'])
@permission_classes([AllowAny])  # Parents may not be users
def subject_outlook(request, student_id: int, subject_id: int):
    """Get detailed outlook for a single subject."""
    
    student = get_object_or_404(Student, id=student_id)
    subject = get_object_or_404(Subject, id=subject_id)
    
    setting = get_object_or_404(
        StudentExamSettings,
        student=student,
        subject=subject
    )
    
    try:
        evaluation = evaluate_student_subject(
            student_id=student_id,
            subject_id=subject_id,
            exam_date=setting.exam_date,
            target_grade=setting.target_grade,
            previous_tier=setting.last_outlook_tier
        )
        
        return Response({
            "student_id": student_id,
            "subject_id": subject_id,
            "subject_name": subject.display_name,
            "exam_date": setting.exam_date.isoformat(),
            "target_grade": setting.target_grade,
            "evaluation": evaluation,
            "generated_at": date.today().isoformat()
        })
    
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])  # Parents may not be users
def update_exam_settings(request, student_id: int, subject_id: int):
    """Update exam settings for a student-subject pair."""
    
    student = get_object_or_404(Student, id=student_id)
    subject = get_object_or_404(Subject, id=subject_id)
    
    setting, created = StudentExamSettings.objects.get_or_create(
        student=student,
        subject=subject,
        defaults={
            'exam_date': request.data.get('exam_date'),
            'target_grade': request.data.get('target_grade', 5),
            'exam_board': request.data.get('exam_board', 'aqa'),
            'tier': request.data.get('tier', 'higher')
        }
    )
    
    if not created:
        setting.exam_date = request.data.get('exam_date', setting.exam_date)
        setting.target_grade = request.data.get('target_grade', setting.target_grade)
        setting.exam_board = request.data.get('exam_board', setting.exam_board)
        setting.tier = request.data.get('tier', setting.tier)
        setting.save()
    
    return Response({
        "message": "Exam settings updated",
        "student_id": student_id,
        "subject_id": subject_id,
        "settings": {
            "exam_date": setting.exam_date.isoformat(),
            "target_grade": setting.target_grade,
            "exam_board": setting.exam_board,
            "tier": setting.tier
        }
    })