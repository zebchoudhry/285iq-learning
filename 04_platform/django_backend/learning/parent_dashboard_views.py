import logging
from datetime import date

from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from learning.throttles import ParentRateThrottle

logger = logging.getLogger(__name__)

from django.shortcuts import get_object_or_404

from learning.models import StudentExamSettings, Subject
from users.models import Student
from decision_engine.v1_0.decision_engine_v1 import evaluate_student_subject
from decision_engine.v1_0.core import generate_recommendations, PerformanceTrend, OutlookTier
from learning.services.activity_feed import get_recent_activity
from learning.services.learning_mission import build_learning_mission
from learning.services.parent_narrative import build_parent_narrative
from learning.services.dashboard_cache import get_snapshot, set_snapshot


ParentDashboardThrottle = ParentRateThrottle


def _weekly_evidence(recent_activity):
    """Build simple this-week vs last-week activity evidence."""
    from datetime import timedelta

    today = date.today()
    this_week_start = today - timedelta(days=6)
    last_week_start = today - timedelta(days=13)
    last_week_end = today - timedelta(days=7)

    this_week = 0
    last_week = 0
    for row in recent_activity:
        d = None
        raw = (row or {}).get("date")
        try:
            d = date.fromisoformat(raw) if raw else None
        except Exception:
            d = None
        if not d:
            continue
        if this_week_start <= d <= today:
            this_week += 1
        elif last_week_start <= d <= last_week_end:
            last_week += 1

    delta = this_week - last_week
    direction = "up" if delta > 0 else "down" if delta < 0 else "flat"
    return {
        "this_week_activity": this_week,
        "last_week_activity": last_week,
        "delta_activity": delta,
        "direction": direction,
    }


@api_view(['GET'])
@permission_classes([AllowAny])  # Parents may not be users
@throttle_classes([ParentDashboardThrottle])
def parent_dashboard(request, parent_access_token: str):
    try:
        student = Student.objects.get(parent_access_token=parent_access_token)
    except Student.DoesNotExist:
        return Response(
            {"error": "Invalid access token"},
            status=status.HTTP_404_NOT_FOUND
        )
    
    student_id = student.id

    # Serve cached snapshot if fresh
    cached = get_snapshot(student_id)
    if cached:
        logger.debug("Serving cached parent dashboard for student %s", student_id)
        return Response(cached)

    exam_settings = StudentExamSettings.objects.filter(student=student).select_related('subject')

    if not exam_settings.exists():
        return Response({
            "student_id": student_id,
            "student_name": student.username,
            "message": "No exam settings configured",
            "subjects": [],
            "recent_activity": get_recent_activity(student_id, limit=10),
        })
    
    subject_outlooks = []
    
    for setting in exam_settings:
        try:
            # convert stored string to OutlookTier enum safely
            previous_tier = None
            if setting.last_outlook_tier:
                try:
                    previous_tier = OutlookTier(setting.last_outlook_tier)
                except Exception:
                    previous_tier = None

            evaluation = evaluate_student_subject(
                student_id=student_id,
                subject_id=setting.subject_id,
                exam_date=setting.exam_date,
                target_grade=setting.target_grade,
                previous_tier=previous_tier
            )
            new_tier = evaluation.get('tier')
            new_tier_str = new_tier.value if hasattr(new_tier, 'value') else str(new_tier)
            old_tier_str = setting.last_outlook_tier or ''
            if new_tier_str != old_tier_str:
                if old_tier_str:
                    try:
                        from dashboard.services.notification_delivery import send_parent_notification
                        msg = f"Outlook changed to {new_tier_str.replace('_', ' ').title()}. {evaluation.get('reason', '')}"
                        send_parent_notification(
                            student_id=student_id,
                            subject_id=setting.subject_id,
                            event_type='tier_change',
                            priority=2,
                            message=msg,
                            subject_display_name=setting.subject.display_name,
                            student_name=student.display_name,
                            parent_email=student.parent_email or '',
                        )
                    except Exception:
                        pass
                setting.last_outlook_tier = new_tier_str
                setting.save(update_fields=['last_outlook_tier'])
            
            rec_dict = generate_recommendations(
                attainment_band=evaluation['attainment_band'],
                target_grade=setting.target_grade,
                trend=PerformanceTrend(evaluation['trend']),
                weeks_remaining=evaluation['weeks_remaining'],
                topic_performances=[]
            )
            rec_list = [rec_dict.get("message", ""), f"Target: {rec_dict.get('session_frequency', 0)} sessions per week"]
            if rec_dict.get("priority_topics"):
                rec_list.append("Focus topics: " + ", ".join(str(t) for t in rec_dict["priority_topics"]))
            recommendations = [r for r in rec_list if r]
            mission = build_learning_mission(student, subject_id=setting.subject_id)
            parent_narrative = build_parent_narrative(
                subject_name=setting.subject.display_name,
                target_grade=setting.target_grade,
                predicted_grade=mission.get("predicted_grade", setting.target_grade),
                risk_level=mission.get("risk_level", "watch"),
                sessions_per_week=evaluation.get("activity_per_week", 0),
                coverage_breadth=round(evaluation.get("coverage_breadth", 0.0) * 100, 1),
                weak_skills=mission.get("skill_codes", []),
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
                "recommendations": recommendations,
                "parent_narrative": parent_narrative,
            })
        except Exception as e:
            subject_outlooks.append({
                "subject_id": setting.subject_id,
                "subject_name": setting.subject.display_name,
                "error": str(e)
            })
    
    recent_activity = get_recent_activity(student_id, limit=10)

    weekly_evidence = _weekly_evidence(recent_activity)

    response_data = {
        "student_id": student_id,
        "student_name": student.username,
        "generated_at": date.today().isoformat(),
        "subjects": subject_outlooks,
        "recent_activity": recent_activity,
        "weekly_evidence": weekly_evidence,
    }
    set_snapshot(student_id, response_data)
    return Response(response_data)


@api_view(['GET'])
@permission_classes([AllowAny])  # Parents may not be users
@throttle_classes([ParentDashboardThrottle])
def subject_outlook(request, parent_access_token: str, subject_id: int):
    try:
        student = Student.objects.get(parent_access_token=parent_access_token)
    except Student.DoesNotExist:
        return Response(
            {"error": "Invalid access token"},
            status=status.HTTP_404_NOT_FOUND
        )
    
    student_id = student.id
    subject = get_object_or_404(Subject, id=subject_id)
    
    setting = get_object_or_404(
        StudentExamSettings,
        student=student,
        subject=subject
    )
    
    try:
        previous_tier = None
        if setting.last_outlook_tier:
            try:
                previous_tier = OutlookTier(setting.last_outlook_tier)
            except Exception:
                previous_tier = None

        evaluation = evaluate_student_subject(
            student_id=student_id,
            subject_id=subject_id,
            exam_date=setting.exam_date,
            target_grade=setting.target_grade,
            previous_tier=previous_tier
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
@throttle_classes([ParentDashboardThrottle])
def update_exam_settings(request, parent_access_token: str, subject_id: int):
    try:
        student = Student.objects.get(parent_access_token=parent_access_token)
    except Student.DoesNotExist:
        return Response(
            {"error": "Invalid access token"},
            status=status.HTTP_404_NOT_FOUND
        )
    
    student_id = student.id
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
