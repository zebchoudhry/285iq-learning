from datetime import timedelta

from django.db.models import Count, Q
from django.conf import settings
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action, permission_classes, api_view
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import (
    Subject,
    Topic,
    Lesson,
    Flashcard,
    Question,
    QuizAttempt,
    StudentProgress,
    StudentExamDate,
    StudentExamSettings,
    StudentFlashcardProgress,
    MistakeBankItem,
    StruggleEvent,
)
from .serializers import (
    SubjectSerializer,
    TopicSerializer,
    LessonSerializer,
    FlashcardSerializer,
    QuestionSerializer,
    QuestionForQuizSerializer,
    AttemptSerializer,
    MistakeBankItemSerializer,
    StruggleEventSerializer,
    SkillVideoSerializer,
)
from .services.gym_controller import decide_gym_mode
from .services.subscription_limits import check_free_tier_limits
from .services.learning_mission import build_learning_mission
from .ai_tutor import generate_tutor_response, generate_wrong_answer_explanation

# new imports for attempts endpoint
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated as DRFIsAuthenticated

# leaderboard view
from django.contrib.auth import get_user_model

User = get_user_model()


def calculate_predicted_grade(percentage: float, subject, exam_board) -> int:
    """
    Map percentage score to GCSE grade 1-9.
    Uses exam board grade boundaries if available; falls back to standard boundaries.
    """
    boundaries = {}
    if exam_board and getattr(exam_board, 'grade_boundaries', None):
        subject_key = f"{getattr(subject, 'name', 'mathematics')}_{getattr(subject, 'tier', 'higher')}"
        boundaries = exam_board.grade_boundaries.get(
            subject_key,
            exam_board.grade_boundaries.get('mathematics_higher', {}),
        )
    if not boundaries:
        boundaries = {
            '9': 85, '8': 75, '7': 65, '6': 55,
            '5': 45, '4': 35, '3': 25, '2': 15, '1': 5,
        }
    sorted_grades = sorted(
        boundaries.items(),
        key=lambda x: int(x[1]),
        reverse=True,
    )
    for grade, threshold in sorted_grades:
        if percentage >= float(threshold):
            return int(grade)
    return 1


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mission(request):
    """Return today's next-best-task mission for the logged-in student."""
    subject_id = request.query_params.get("subject_id")
    try:
        subject_id = int(subject_id) if subject_id else None
    except (TypeError, ValueError):
        subject_id = None
    return Response(build_learning_mission(request.user, subject_id=subject_id))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def loop_metrics(request):
    """Basic signature-loop health metrics for product iteration."""
    now = timezone.now()
    week_ago = now - timedelta(days=7)
    two_weeks_ago = now - timedelta(days=14)

    attempts = request.user.quiz_attempts.all()
    attempts_7d = attempts.filter(attempted_at__gte=week_ago)
    attempts_14d = attempts.filter(attempted_at__gte=two_weeks_ago)

    mission_completion_rate = 0.0
    if attempts_14d.count() > 0:
        mission_completion_rate = round(
            100.0 * attempts_7d.count() / max(1, attempts_14d.count()), 1
        )

    from learning.models import StudentSkillState

    skill_states = StudentSkillState.objects.filter(student=request.user, attempts__gte=3)
    diagnostic_completion_rate = round(
        100.0 * skill_states.filter(attempts__gte=5).count() / max(1, skill_states.count()), 1
    ) if skill_states.exists() else 0.0

    weak_skill_improvement_count = skill_states.filter(
        status__in=["IMPROVING", "MASTERED", "MAINTENANCE"], rolling_accuracy__gte=70
    ).count()

    # Parent open tracking is not event-based yet; use a conservative proxy signal.
    parent_open_signal = 1 if getattr(request.user, "parent_email", None) else 0

    return Response(
        {
            "diagnostic_completion_rate": diagnostic_completion_rate,
            "mission_completion_rate": mission_completion_rate,
            "weak_skill_improvement_after_3_sessions": weak_skill_improvement_count,
            "estimated_parent_open_signal": parent_open_signal,
            "attempts_last_7_days": attempts_7d.count(),
        }
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def loop_metrics_summary(request):
    """
    Weekly KPI rollup for phase-gate decisions.
    Staff only to avoid leaking aggregate user metrics.
    """
    if not getattr(request.user, "is_staff", False):
        return Response({"error": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    from learning.models import StudentSkillState
    from users.models import Student

    now = timezone.now()
    week_ago = now - timedelta(days=7)

    students = Student.objects.all()
    active_student_ids = set(
        QuizAttempt.objects.filter(attempted_at__gte=week_ago)
        .values_list("student_id", flat=True)
        .distinct()
    )
    active_students = students.filter(id__in=active_student_ids)

    # KPI 1: diagnostic completion proxy
    skill_states = StudentSkillState.objects.filter(student_id__in=active_student_ids, attempts__gte=3)
    diagnostic_completion_rate = 0.0
    if skill_states.exists():
        diagnostic_completion_rate = round(
            100.0 * skill_states.filter(attempts__gte=5).count() / max(1, skill_states.count()),
            1,
        )

    # KPI 2: mission completion proxy = avg attempts per active student this week
    attempts_7d = QuizAttempt.objects.filter(student_id__in=active_student_ids, attempted_at__gte=week_ago)
    mission_completion_rate = 0.0
    if active_students.exists():
        mission_completion_rate = round(100.0 * attempts_7d.count() / max(1, active_students.count() * 6), 1)

    # KPI 3: weak-skill improvement proxy
    weak_skill_improvement = skill_states.filter(
        status__in=["IMPROVING", "MASTERED", "MAINTENANCE"],
        rolling_accuracy__gte=70,
    ).count()

    # KPI 4: parent engagement proxy
    parent_engagement_rate = round(
        100.0 * students.exclude(parent_email__isnull=True).exclude(parent_email="").count() / max(1, students.count()),
        1,
    )

    gate_pass = (
        diagnostic_completion_rate >= 55.0
        and mission_completion_rate >= 40.0
        and weak_skill_improvement >= 10
        and parent_engagement_rate >= 25.0
    )

    return Response(
        {
            "window_days": 7,
            "active_students": active_students.count(),
            "diagnostic_completion_rate": diagnostic_completion_rate,
            "mission_completion_rate": mission_completion_rate,
            "weak_skill_improvement_after_3_sessions": weak_skill_improvement,
            "parent_engagement_rate": parent_engagement_rate,
            "phase_gate": {
                "ready_for_next_phase": gate_pass,
                "reason": (
                    "All KPI thresholds met for phase expansion."
                    if gate_pass
                    else "Hold rollout and continue loop tuning until KPI thresholds are met."
                ),
                "thresholds": {
                    "diagnostic_completion_rate": 55.0,
                    "mission_completion_rate": 40.0,
                    "weak_skill_improvement_after_3_sessions": 10,
                    "parent_engagement_rate": 25.0,
                },
            },
        }
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def leaderboard(request):
    try:
        limit = int(request.query_params.get('limit', 10))
    except (TypeError, ValueError):
        limit = 10

    # Users with profile, ordered by total_xp (handle missing profile)
    from users.models import UserProfile
    user_ids = UserProfile.objects.all().order_by('-total_xp').values_list('student_id', flat=True)[:limit * 2]
    qs = User.objects.filter(id__in=user_ids).order_by('-id')[:limit]
    # Re-sort by XP manually since we filtered
    with_profile = []
    for u in User.objects.filter(id__in=user_ids).select_related('profile')[:limit * 2]:
        try:
            xp = u.profile.total_xp
        except Exception:
            xp = 0
        with_profile.append((u, xp))
    with_profile.sort(key=lambda x: -x[1])
    with_profile = with_profile[:limit]

    results = []
    for u, xp in with_profile:
        results.append({
            'id': u.id,
            'username': u.username,
            'first_name': u.first_name or '',
            'last_name': u.last_name or '',
            'grade_level': getattr(u, 'grade_level', None) or '',
            'profile': {
                'total_xp': xp,
                'current_level': getattr(u.profile, 'current_level', 1) if hasattr(u, 'profile') and u.profile else 1
            }
        })

    return Response(results)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def weak_areas(request):
    """Return topics where student has low success rate (below 60%) for Focus Areas card."""
    from users.models import StudentTopicPerformance

    perfs = StudentTopicPerformance.objects.filter(
        student=request.user,
        questions_attempted__gte=3,
    ).select_related('topic', 'topic__subject')
    results = []
    for stp in perfs:
        rate = stp.questions_correct / stp.questions_attempted if stp.questions_attempted else 0
        if rate < 0.6:
            gap = 1.0 - rate
            suggested_minutes = min(30, max(10, int(round(gap * 35))))
            results.append({
                'topic_id': stp.topic_id,
                'topic_name': stp.topic.name,
                'subject_name': stp.topic.subject.display_name,
                'subject_id': stp.topic.subject_id,
                'success_rate': rate * 100,
                'questions_attempted': stp.questions_attempted,
                'questions_correct': stp.questions_correct,
                'suggested_session_minutes': suggested_minutes,
                'revision_tip': (
                    f"Do ~{suggested_minutes} min of mixed retrieval on {stp.topic.name}, "
                    "then re-check with a short quiz."
                ),
            })
    results.sort(key=lambda x: x['success_rate'])
    for i, row in enumerate(results):
        row['priority_rank'] = i + 1
    return Response(results)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mistake_bank(request):
    """Return the current student's active review queue of mistakes and slow/guessed answers."""
    status_filter = request.query_params.get('status', 'active')
    qs = (
        MistakeBankItem.objects.filter(student=request.user)
        .select_related('question', 'topic', 'topic__subject', 'skill')
        .order_by('status', 'next_review_at', '-last_seen_at')
    )
    if status_filter != 'all':
        qs = qs.filter(status=status_filter)

    try:
        limit = int(request.query_params.get('limit', 25))
    except (TypeError, ValueError):
        limit = 25
    limit = max(1, min(limit, 100))

    return Response(MistakeBankItemSerializer(qs[:limit], many=True).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def struggle_events(request):
    """Recent diagnostic signals for where the student is getting stuck."""
    qs = (
        StruggleEvent.objects.filter(student=request.user)
        .select_related('question', 'topic', 'topic__subject', 'skill')
        .order_by('-created_at')
    )
    try:
        limit = int(request.query_params.get('limit', 20))
    except (TypeError, ValueError):
        limit = 20
    limit = max(1, min(limit, 100))
    return Response(StruggleEventSerializer(qs[:limit], many=True).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def report_stuck(request):
    """Record an in-session stuck signal and return the smallest useful intervention."""
    question_id = request.data.get('question_id')
    student_answer = request.data.get('student_answer', '')
    confidence_level = request.data.get('confidence_level', 'unsure')
    time_to_first_action_ms = request.data.get('time_to_first_action_ms')
    time_spent_ms = request.data.get('time_spent_ms')

    try:
        question = Question.objects.select_related('lesson__topic__subject').get(id=question_id, is_active=True)
    except (Question.DoesNotExist, TypeError, ValueError):
        return Response({'error': 'Question not found'}, status=status.HTTP_404_NOT_FOUND)

    from learning.services.llm_diagnostic import diagnose_stuck_step
    from learning.models import QuestionStep

    diagnostic = diagnose_stuck_step(
        question_id=question.id,
        student_answers=[{'step_order': 1, 'student_answer': student_answer}],
        student_said_stuck=True,
    )
    skill = None
    skill_code = diagnostic.get('skill_code') or ''
    if skill_code:
        step = QuestionStep.objects.filter(question=question, skill__code=skill_code).select_related('skill').first()
        if step:
            skill = step.skill
    if skill is None:
        step = QuestionStep.objects.filter(question=question).select_related('skill').order_by('step_order').first()
        skill = step.skill if step else None

    event = StruggleEvent.objects.create(
        student=request.user,
        question=question,
        topic=question.lesson.topic,
        skill=skill,
        trigger='stuck_button',
        stuck_point=skill_code or str(diagnostic.get('stuck_at_step', 1)),
        mistake_type='stuck',
        confidence_level=confidence_level if confidence_level in ('guessed', 'unsure', 'confident') else 'unsure',
        time_to_first_action_ms=time_to_first_action_ms or None,
        time_spent_ms=time_spent_ms or None,
        student_answer=student_answer or '',
        diagnostic_message=diagnostic.get('recommendation') or diagnostic.get('reason') or '',
        recommended_intervention='hint',
    )

    hint = ''
    if skill:
        step = QuestionStep.objects.filter(question=question, skill=skill).order_by('step_order').first()
        if step:
            hint = step.hint_level_1 or step.hint_level_2 or ''
    if not hint:
        hint = diagnostic.get('recommendation') or 'Write down what the question gives you, what it asks for, and the first operation you can safely do.'

    from learning.services.video_recommendations import recommend_skill_video
    video = recommend_skill_video(
        question=question,
        skill=skill,
        tier=getattr(question.lesson.topic.subject, 'tier', None),
    )

    return Response({
        'event': StruggleEventSerializer(event).data,
        'diagnostic': diagnostic,
        'hint': hint,
        'recommendation': diagnostic.get('recommendation') or hint,
        'video': SkillVideoSerializer(video).data if video else None,
        'next_action': 'try_hint_then_submit',
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_mistake_bank_item(request, item_id):
    """Update a mistake-bank item status after a retry or manual dismiss."""
    try:
        item = MistakeBankItem.objects.get(id=item_id, student=request.user)
    except MistakeBankItem.DoesNotExist:
        return Response({'error': 'Mistake bank item not found'}, status=status.HTTP_404_NOT_FOUND)

    new_status = request.data.get('status')
    valid_statuses = {choice[0] for choice in MistakeBankItem.STATUS_CHOICES}
    if new_status not in valid_statuses:
        return Response({'error': f'status must be one of {sorted(valid_statuses)}'}, status=status.HTTP_400_BAD_REQUEST)
    item.status = new_status
    item.save(update_fields=['status', 'last_seen_at'])
    return Response(MistakeBankItemSerializer(item).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mistake_bank_retry_question(request, item_id):
    """Return the exact question attached to a mistake-bank item."""
    try:
        item = (
            MistakeBankItem.objects
            .select_related('question', 'topic', 'topic__subject', 'skill')
            .get(id=item_id, student=request.user)
        )
    except MistakeBankItem.DoesNotExist:
        return Response({'error': 'Mistake bank item not found'}, status=status.HTTP_404_NOT_FOUND)

    if item.status == 'active':
        item.status = 'retrying'
        item.save(update_fields=['status', 'last_seen_at'])

    return Response({
        'mistake': MistakeBankItemSerializer(item).data,
        'question': QuestionForQuizSerializer(item.question).data,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_mistake_bank_retry(request, item_id):
    """Submit an exact retry and update the mistake-bank mastery state."""
    try:
        item = (
            MistakeBankItem.objects
            .select_related('question', 'topic', 'skill')
            .get(id=item_id, student=request.user)
        )
    except MistakeBankItem.DoesNotExist:
        return Response({'error': 'Mistake bank item not found'}, status=status.HTTP_404_NOT_FOUND)

    question = item.question
    selected_option_id = request.data.get('selected_option_id')
    raw_answer = request.data.get('answer') or ''
    is_correct = False
    if selected_option_id:
        try:
            option = MultipleChoiceOption.objects.get(id=selected_option_id, question=question)
            is_correct = option.is_correct
        except MultipleChoiceOption.DoesNotExist:
            is_correct = False
    else:
        from learning.services.answer_grading import answers_equivalent
        is_correct, _ = answers_equivalent(raw_answer, question.correct_answer or '')

    item.attempts_count += 1
    item.last_student_answer = raw_answer or item.last_student_answer
    if is_correct:
        item.correct_retries += 1
        item.status = 'mastered' if item.correct_retries >= 2 else 'retrying'
    else:
        item.correct_retries = 0
        item.status = 'active'
    item.save()

    return Response({
        'is_correct': is_correct,
        'correct_retries': item.correct_retries,
        'status': item.status,
        'explanation': question.explanation or '',
        'correct_answer': '' if is_correct else (question.correct_answer or ''),
        'mistake': MistakeBankItemSerializer(item).data,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def subject_progress(request):
    """Return per-subject progress (lessons completed / total) for current user."""
    subjects = Subject.objects.filter(is_active=True)
    progress_list = []
    for subject in subjects:
        total_lessons = Lesson.objects.filter(topic__subject=subject, is_active=True).count()
        completed = StudentProgress.objects.filter(
            student=request.user,
            lesson__topic__subject=subject,
            is_completed=True
        ).count()
        # Also count as "done" if they have any progress record (attempted)
        attempted_lessons = StudentProgress.objects.filter(
            student=request.user,
            lesson__topic__subject=subject
        ).values_list('lesson_id', flat=True).distinct().count()
        pct = round(100.0 * completed / total_lessons, 0) if total_lessons else 0
        progress_list.append({
            'subject_id': subject.id,
            'subject_name': subject.name,
            'display_name': subject.display_name,
            'total_lessons': total_lessons,
            'completed_lessons': completed,
            'attempted_lessons': attempted_lessons,
            'progress_percent': int(pct)
        })
    return Response(progress_list)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def revision_summary(request):
    """Return exam dates with time left, study mode, and exams within 48h for current user."""
    from datetime import date, timedelta
    from decision_engine.v1_0.study_mode import calculate_study_mode

    today = date.today()
    in_48h_end = today + timedelta(days=2)
    exam_dates_qs = (
        StudentExamDate.objects
        .filter(student=request.user, exam_date__gte=today)
        .select_related('subject')
        .order_by('exam_date')
    )
    exam_dates_list = []
    exams_within_48h = []
    for ed in exam_dates_qs:
        days_remaining = (ed.exam_date - today).days
        weeks_remaining = max(0, days_remaining // 7)
        try:
            study_mode = calculate_study_mode(ed.exam_date, today)
            mode_str = study_mode['mode'].value if hasattr(study_mode['mode'], 'value') else str(study_mode['mode'])
            description = study_mode.get('description', '')
        except Exception:
            mode_str = 'standard'
            description = ''
        exam_dates_list.append({
            'subject_id': ed.subject_id,
            'subject_name': ed.subject.display_name,
            'paper_label': ed.paper_label,
            'exam_date': ed.exam_date.isoformat(),
            'days_remaining': days_remaining,
            'weeks_remaining': weeks_remaining,
            'study_mode': mode_str,
            'description': description,
        })
        if ed.exam_date <= in_48h_end:
            exams_within_48h.append({
                'subject_id': ed.subject_id,
                'subject_name': ed.subject.display_name,
                'paper_label': ed.paper_label,
                'exam_date': ed.exam_date.isoformat(),
                'days_remaining': days_remaining,
            })
    next_exam_days = None
    if exam_dates_list:
        next_exam_days = exam_dates_list[0]['days_remaining']

    subject_readiness = []
    try:
        from decision_engine.v1_0.decision_engine_v1 import evaluate_student_subject
        from decision_engine.v1_0.core import OutlookTier
        settings_qs = StudentExamSettings.objects.filter(student=request.user).select_related('subject')
        for setting in settings_qs:
            try:
                prev_tier = None
                if setting.last_outlook_tier:
                    try:
                        prev_tier = OutlookTier(setting.last_outlook_tier)
                    except Exception:
                        pass
                ev = evaluate_student_subject(
                    student_id=request.user.id,
                    subject_id=setting.subject_id,
                    exam_date=setting.exam_date,
                    target_grade=setting.target_grade,
                    previous_tier=prev_tier,
                )
                attainment = ev.get('attainment_band', 0)
                tg = setting.target_grade
                exam_ready = attainment >= tg
                almost = attainment >= tg - 1 and attainment < tg
                status_label = 'yes' if exam_ready else ('almost' if almost else 'not_yet')
                subject_readiness.append({
                    'subject_id': setting.subject_id,
                    'subject_name': setting.subject.display_name,
                    'target_grade': tg,
                    'attainment_band': attainment,
                    'exam_ready': exam_ready,
                    'status': status_label,
                    'outlook_tier': ev.get('tier', ''),
                })
            except Exception:
                pass
    except Exception:
        pass

    return Response({
        'exam_dates': exam_dates_list,
        'exams_within_48h': exams_within_48h,
        'next_exam_days': next_exam_days,
        'subject_readiness': subject_readiness,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def exam_readiness(request):
    """Return exam-readiness scores and unlock guidance per subject."""
    from learning.services.exam_readiness import build_exam_readiness
    return Response({"subjects": build_exam_readiness(request.user)})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def tutor_chat(request):
    """LLM-backed tutor chat with fallback to rule-based tutor."""
    message = (request.data.get('message') or '').strip()
    topic_id = request.data.get('topic_id')
    question_id = request.data.get('question_id')
    student_answers = request.data.get('student_answers', [])
    if not message:
        return Response({'error': 'message is required'}, status=status.HTTP_400_BAD_REQUEST)
    reply = generate_tutor_response(
        student_id=request.user.id,
        message=message,
        topic_id=topic_id,
        question_id=question_id,
        student_answers=student_answers,
    )
    return Response({'message': reply})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def tutor_explain_wrong(request):
    """
    Generate a structured explanation for a wrong answer (user-initiated only).
    Call with: question_id, student_answer, correct_answer, skill_code.
    Falls back to Question.explanation if LLM fails.
    """
    question_id = request.data.get('question_id')
    student_answer = request.data.get('student_answer', '')
    correct_answer = request.data.get('correct_answer', '')
    skill_code = request.data.get('skill_code', '')
    if question_id is None:
        return Response({'error': 'question_id is required'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        question_id = int(question_id)
    except (TypeError, ValueError):
        return Response({'error': 'question_id must be an integer'}, status=status.HTTP_400_BAD_REQUEST)
    if not isinstance(student_answer, str):
        student_answer = str(student_answer) if student_answer is not None else ''
    if not isinstance(correct_answer, str):
        correct_answer = str(correct_answer) if correct_answer is not None else ''
    if not isinstance(skill_code, str):
        skill_code = str(skill_code) if skill_code is not None else ''

    explanation = generate_wrong_answer_explanation(
        question_id=question_id,
        student_answer=student_answer,
        correct_answer=correct_answer,
        skill_code=skill_code,
    )
    return Response({'explanation': explanation})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def tutor_diagnose_stuck(request):
    """
    LLM step-level diagnostic: identify where the student got stuck.

    Request body:
        question_id: int (required)
        student_answers: list of {"step_order": N, "student_answer": str}
        student_said_stuck: bool (optional, default False)

    Returns:
        stuck_at_step, reason, skill_code, recommendation
    """
    question_id = request.data.get('question_id')
    if question_id is None:
        return Response({'error': 'question_id is required'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        question_id = int(question_id)
    except (TypeError, ValueError):
        return Response({'error': 'question_id must be an integer'}, status=status.HTTP_400_BAD_REQUEST)

    student_answers = request.data.get('student_answers', [])
    student_said_stuck = bool(request.data.get('student_said_stuck', False))

    from learning.services.llm_diagnostic import diagnose_stuck_step

    result = diagnose_stuck_step(
        question_id=question_id,
        student_answers=student_answers,
        student_said_stuck=student_said_stuck,
    )
    return Response(result)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def worked_solution(request, question_id):
    """
    Return step-by-step worked solution for a question.
    GET /api/questions/<question_id>/worked-solution/
    """
    from learning.services.worked_solutions import get_worked_solution
    steps = get_worked_solution(question_id)
    return Response({'question_id': question_id, 'steps': steps})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def topic_strength(request, topic_id):
    """Return latest strength trend for current student/topic."""
    from .models import TopicStrengthSnapshot

    snapshots = list(
        TopicStrengthSnapshot.objects.filter(
            student=request.user,
            topic_id=topic_id,
        ).order_by('-date')[:8]
    )
    if not snapshots:
        return Response({'topic_id': topic_id, 'trend': [], 'status': 'insufficient_data'})

    trend = [
        {
            'date': s.date.isoformat(),
            'accuracy_rate': s.accuracy_rate,
            'recent_accuracy': s.recent_accuracy,
            'questions_attempted': s.questions_attempted,
        }
        for s in reversed(snapshots)
    ]
    latest = snapshots[0]
    status_label = 'improving' if latest.recent_accuracy >= latest.accuracy_rate else 'needs_practice'
    return Response({
        'topic_id': topic_id,
        'status': status_label,
        'trend': trend,
    })


@login_required
def frontend_view(request, subject_id=None, topic_id=None):
    """
    Main frontend view that serves different templates based on URL.
    Used for dashboard and practice pages.
    """
    if not StudentExamSettings.objects.filter(student=request.user).exists():
        return redirect('/onboarding/exam-dates/')
    
    # Check if this is a practice route
    if 'practice' in request.path:
        return render(request, 'practice.html', {
            'subject_id': subject_id,
            'topic_id': topic_id
        })
    
    # Default to dashboard
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
    """Return topics with nested lessons (for collapsible subject view)."""
    try:
        subject = Subject.objects.get(id=subject_id)
        topics = Topic.objects.filter(subject=subject, is_active=True).order_by('order')
        topic_ids = [t.id for t in topics]

        # Fetch all lessons for these topics
        lessons_qs = Lesson.objects.filter(
            topic_id__in=topic_ids, is_active=True
        ).order_by('topic_id', 'order').select_related('topic')
        lesson_ids = [l.id for l in lessons_qs]

        # Completion status per lesson
        completed_ids = set()
        if lesson_ids:
            completed_ids = set(
                StudentProgress.objects.filter(
                    student=request.user,
                    lesson_id__in=lesson_ids,
                    is_completed=True,
                ).values_list('lesson_id', flat=True)
            )

        # Group lessons by topic
        lessons_by_topic = {}
        for l in lessons_qs:
            tid = l.topic_id
            if tid not in lessons_by_topic:
                lessons_by_topic[tid] = []
            lessons_by_topic[tid].append({
                'id': l.id,
                'title': l.title,
                'duration': l.estimated_duration,
                'lesson_type': l.get_lesson_type_display(),
                'order': l.order,
                'is_completed': l.id in completed_ids,
            })

        topics_data = []
        for t in topics:
            lessons = lessons_by_topic.get(t.id, [])
            completed = sum(1 for le in lessons if le['is_completed'])
            total = len(lessons)
            topics_data.append({
                'id': t.id,
                'name': t.name,
                'description': t.description,
                'order': t.order,
                'lesson_count': total,
                'completed_lessons': completed,
                'total_lessons': total,
                'lessons': lessons,
            })

        data = {
            'subject_id': subject.id,
            'subject_name': subject.display_name,
            'topics': topics_data,
        }
        return Response(data)
    except Subject.DoesNotExist:
        return Response({'error': 'Subject not found'}, status=404)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_subject_detail(request, subject_id):
    """Return subject detail with topic cards, performance summary, exam settings."""
    from users.models import UserProfile
    from decision_engine.v1_0.decision_engine_v1 import evaluate_student_subject
    from decision_engine.v1_0.core import OutlookTier
    
    subject = get_object_or_404(Subject, id=subject_id, is_active=True)
    topics = Topic.objects.filter(subject=subject, is_active=True).order_by('order')
    
    # Get exam settings for exam board
    exam_settings = StudentExamSettings.objects.filter(
        student=request.user,
        subject=subject
    ).first()
    
    # Overall progress
    total_lessons = Lesson.objects.filter(
        topic__subject=subject, is_active=True
    ).count()
    completed_lessons = StudentProgress.objects.filter(
        student=request.user,
        lesson__topic__subject=subject,
        is_completed=True
    ).count()
    completion_pct = (completed_lessons / total_lessons * 100) if total_lessons else 0
    
    # Streak from profile
    profile = getattr(request.user, 'profile', None)
    streak = profile.daily_streak if profile else 0
    
    # Exam readiness tier
    outlook_tier = None
    if exam_settings:
        try:
            prev_tier = OutlookTier(exam_settings.last_outlook_tier) if exam_settings.last_outlook_tier else None
            evaluation = evaluate_student_subject(
                student_id=request.user.id,
                subject_id=subject_id,
                exam_date=exam_settings.exam_date,
                target_grade=exam_settings.target_grade,
                previous_tier=prev_tier
            )
            outlook_tier = evaluation.get('tier')
        except Exception:
            pass
    
    # Topic cards with accuracy
    topic_cards = []
    for topic in topics:
        lessons_count = Lesson.objects.filter(topic=topic, is_active=True).count()
        completed_count = StudentProgress.objects.filter(
            student=request.user,
            lesson__topic=topic,
            is_completed=True
        ).count()
        topic_completion = (completed_count / lessons_count * 100) if lessons_count else 0
        
        # Calculate accuracy from QuizAttempt
        attempts = QuizAttempt.objects.filter(
            student=request.user,
            question__lesson__topic=topic
        )
        total_attempts = attempts.count()
        correct_attempts = attempts.filter(is_correct=True).count()
        accuracy = (correct_attempts / total_attempts * 100) if total_attempts else 0
        
        # Status label
        if accuracy >= 70:
            status = "Strong"
            status_color = "green"
        elif accuracy >= 50:
            status = "Strengthening"
            status_color = "amber"
        else:
            status = "At Risk"
            status_color = "red"
        
        topic_cards.append({
            'id': topic.id,
            'name': topic.name,
            'lessons_count': lessons_count,
            'completion_pct': round(topic_completion, 1),
            'accuracy_pct': round(accuracy, 1),
            'total_attempts': total_attempts,
            'status': status,
            'status_color': status_color,
        })
    
    # Mastery % (average accuracy across all topics)
    all_attempts = QuizAttempt.objects.filter(
        student=request.user,
        question__lesson__topic__subject=subject
    )
    total_all = all_attempts.count()
    correct_all = all_attempts.filter(is_correct=True).count()
    mastery_pct = (correct_all / total_all * 100) if total_all else 0
    
    return Response({
        'subject_id': subject.id,
        'subject_name': subject.display_name,
        'exam_board': exam_settings.exam_board if exam_settings else 'aqa',
        'completion_pct': round(completion_pct, 1),
        'mastery_pct': round(mastery_pct, 1),
        'streak': streak,
        'outlook_tier': outlook_tier,
        'topics': topic_cards,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_topic_lessons(request, topic_id):
    try:
        topic = Topic.objects.get(id=topic_id)
        lessons = Lesson.objects.filter(topic=topic, is_active=True).order_by('order')
        lesson_ids = [l.id for l in lessons]
        completed_ids = set(
            StudentProgress.objects.filter(
                student=request.user,
                lesson_id__in=lesson_ids,
                is_completed=True
            ).values_list('lesson_id', flat=True)
        )
        data = {
            'topic_id': topic.id,
            'topic_name': topic.name,
            'subject_name': topic.subject.display_name,
            'lessons': [{
                'id': l.id,
                'title': l.title,
                'duration': l.estimated_duration,
                'lesson_type': l.get_lesson_type_display(),
                'order': l.order,
                'is_completed': l.id in completed_ids,
            } for l in lessons]
        }
        return Response(data)
    except Topic.DoesNotExist:
        return Response({'error': 'Topic not found'}, status=404)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def flashcard_decks(request):
    """List topics that have flashcards, with counts."""
    topics = Topic.objects.filter(
        flashcards__is_active=True
    ).annotate(
        card_count=Count('flashcards', filter=Q(flashcards__is_active=True))
    ).filter(card_count__gt=0).order_by('subject', 'order').select_related('subject')
    data = [
        {
            'id': t.id,
            'name': t.name,
            'subject_name': t.subject.display_name,
            'card_count': t.card_count,
        }
        for t in topics
    ]
    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def flashcard_list(request, topic_id):
    """List flashcards for a topic."""
    try:
        topic = Topic.objects.get(id=topic_id)
    except Topic.DoesNotExist:
        return Response({'error': 'Topic not found'}, status=404)
    cards = Flashcard.objects.filter(topic=topic, is_active=True).order_by('order')
    serializer = FlashcardSerializer(cards, many=True)
    return Response({
        'topic_id': topic.id,
        'topic_name': topic.name,
        'subject_name': topic.subject.display_name,
        'flashcards': serializer.data,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def flashcards_due(request, topic_id):
    """Flashcards due today or earlier for spaced repetition (per user)."""
    from django.utils import timezone

    try:
        topic = Topic.objects.get(id=topic_id)
    except Topic.DoesNotExist:
        return Response({'error': 'Topic not found'}, status=404)

    today = timezone.now().date()
    cards = Flashcard.objects.filter(topic=topic, is_active=True).order_by('order')
    due_payload = []
    for c in cards:
        prog, _ = StudentFlashcardProgress.objects.get_or_create(
            student=request.user,
            flashcard=c,
            defaults={
                'ease_factor': 2.5,
                'interval_days': 1,
                'repetition_count': 0,
                'due_date': today,
            },
        )
        if prog.due_date <= today:
            row = FlashcardSerializer(c).data
            row['due_date'] = prog.due_date.isoformat()
            row['interval_days'] = prog.interval_days
            row['ease_factor'] = prog.ease_factor
            due_payload.append(row)

    return Response({
        'topic_id': topic.id,
        'topic_name': topic.name,
        'subject_name': topic.subject.display_name,
        'due_count': len(due_payload),
        'flashcards': due_payload,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def flashcards_due_count(request):
    """Return total flashcard due count across all topics for the user."""
    from django.utils import timezone
    today = timezone.now().date()
    try:
        due_count = StudentFlashcardProgress.objects.filter(
            student=request.user,
            due_date__lte=today,
            flashcard__is_active=True,
        ).count()
        return Response({'due_count': due_count})
    except Exception as e:
        return Response({'due_count': 0})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def flashcard_review(request):
    """Record a review (again/hard/good/easy) and reschedule the card (SM-2)."""
    from django.utils import timezone

    from learning.services.flashcard_srs import RATING_TO_QUALITY, sm2_step, next_due_date

    fid = request.data.get('flashcard_id')
    rating = (request.data.get('rating') or '').strip().lower()
    if not fid:
        return Response({'error': 'flashcard_id required'}, status=400)
    if rating not in RATING_TO_QUALITY:
        return Response(
            {'error': 'rating must be one of: again, hard, good, easy'},
            status=400,
        )
    try:
        card = Flashcard.objects.get(id=int(fid), is_active=True)
    except (Flashcard.DoesNotExist, ValueError, TypeError):
        return Response({'error': 'Flashcard not found'}, status=404)

    today = timezone.now().date()
    prog, _ = StudentFlashcardProgress.objects.get_or_create(
        student=request.user,
        flashcard=card,
        defaults={
            'ease_factor': 2.5,
            'interval_days': 1,
            'repetition_count': 0,
            'due_date': today,
        },
    )
    q = RATING_TO_QUALITY[rating]
    new_ef, new_iv, new_reps = sm2_step(
        q, prog.ease_factor, prog.interval_days, prog.repetition_count
    )
    prog.ease_factor = new_ef
    prog.interval_days = new_iv
    prog.repetition_count = new_reps
    prog.due_date = next_due_date(new_iv, from_day=today)
    prog.last_reviewed_at = timezone.now()
    prog.save()

    return Response({
        'flashcard_id': card.id,
        'next_due_date': prog.due_date.isoformat(),
        'interval_days': prog.interval_days,
        'ease_factor': prog.ease_factor,
        'repetition_count': prog.repetition_count,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_lesson_content(request, lesson_id):
    try:
        lesson = Lesson.objects.get(id=lesson_id)
        
        # Use relative paths for static files so they work regardless of host (localhost vs 127.0.0.1)
        infographic_url = lesson.infographic_url or ''
        video_url = lesson.video_url or ''
        if infographic_url and '/static/' in infographic_url:
            infographic_url = '/static/' + infographic_url.split('/static/', 1)[1]
        if video_url and '/static/' in video_url:
            video_url = '/static/' + video_url.split('/static/', 1)[1]

        data = {
            'id': lesson.id,
            'title': lesson.title,
            'content': lesson.content,
            'duration': lesson.estimated_duration,
            'lesson_type': getattr(lesson, 'get_lesson_type_display', lambda: lesson.lesson_type)(),
            'difficulty_level': lesson.difficulty_level,
            'key_skills': lesson.key_skills,
            'topic_id': lesson.topic_id,
            'topic_name': lesson.topic.name,
            'subject_name': lesson.topic.subject.display_name,
            'video_url': video_url,
            'infographic_url': infographic_url,
        }
        return Response(data)
    except Lesson.DoesNotExist:
        return Response({'error': 'Lesson not found'}, status=404)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def lesson_complete(request, lesson_id):
    """Mark a lesson as complete for the current user."""
    from django.utils import timezone
    try:
        lesson = Lesson.objects.get(id=lesson_id, is_active=True)
    except Lesson.DoesNotExist:
        return Response({'error': 'Lesson not found'}, status=status.HTTP_404_NOT_FOUND)
    time_spent = request.data.get('time_spent')
    progress, created = StudentProgress.objects.get_or_create(
        student=request.user,
        lesson=lesson,
        defaults={'is_completed': True, 'completion_date': timezone.now()}
    )
    if not created and not progress.is_completed:
        progress.is_completed = True
        progress.completion_date = timezone.now()
        if time_spent is not None:
            progress.time_spent = int(time_spent)
        progress.save()
    try:
        profile = getattr(request.user, 'profile', None)
        if profile is not None:
            profile.update_streak()
            from users.achievements import check_and_award_achievements
            check_and_award_achievements(request.user)
    except Exception:
        pass
    try:
        from .services.study_activity import record_study_activity
        record_study_activity(
            student=request.user,
            subject=lesson.topic.subject,
            topic=lesson.topic,
            duration_seconds=int(time_spent or 0),
        )
    except Exception:
        pass
    return Response({
        'lesson_id': lesson_id,
        'completed': True,
        'message': 'Lesson marked complete',
    }, status=status.HTTP_200_OK)


@login_required
def lessons_page(request):
    subject_id = request.GET.get('subject')
    topic_id = request.GET.get('topic')
    lesson_id = request.GET.get('lesson')
    if subject_id and not topic_id and not lesson_id:
        try:
            return redirect(f'/subject/{int(subject_id)}/')
        except (TypeError, ValueError):
            pass
    return render(request, 'lessons.html')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def lesson_questions(request, lesson_id):
    """
    Get practice questions for a lesson with hints.
    Returns questions for micro-learning on the lesson page.
    """
    try:
        lesson = Lesson.objects.get(id=lesson_id, is_active=True)
    except Lesson.DoesNotExist:
        return Response({'error': 'Lesson not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Serve questions needing review first
    review_question_ids = list(
        QuizAttempt.objects.filter(
            student=request.user,
            question__lesson=lesson,
            needs_review=True,
        ).values_list('question_id', flat=True).distinct()
    )
    review_questions = list(
        Question.objects.filter(
            id__in=review_question_ids,
            lesson=lesson,
            is_active=True,
        )
    )
    # Fill remaining slots with random questions
    remaining = max(0, 10 - len(review_questions))
    random_questions = list(
        Question.objects.filter(
            lesson=lesson,
            is_active=True,
        ).exclude(
            id__in=review_question_ids,
        ).order_by('?')[:remaining]
    )
    questions = review_questions + random_questions
    
    questions_data = []
    for q in questions:
        # Get first QuestionStep for hints (if available)
        first_step = q.steps.first()
        hint_level_1 = first_step.hint_level_1 if first_step else q.explanation
        hint_level_2 = first_step.hint_level_2 if first_step else ''
        
        # Build question payload
        q_data = {
            'id': q.id,
            'question_text': q.question_text,
            'question_type': q.question_type,
            'difficulty_level': q.difficulty_level,
            'marks_available': q.marks_available,
            'hint_level_1': hint_level_1 or 'Try breaking the problem down step by step.',
            'hint_level_2': hint_level_2 or '',
            'options': []
        }
        
        # Add MCQ options if applicable
        if q.question_type == 'multiple_choice':
            q_data['options'] = list(
                q.options.order_by('order').values('id', 'option_text')
            )
        
        questions_data.append(q_data)
    
    return Response({
        'lesson_id': lesson_id,
        'lesson_title': lesson.title,
        'questions': questions_data
    })


# ---------------------------------------------------------------------
# Practice: 6-question adaptive practice session
# ---------------------------------------------------------------------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def practice_start(request):
    """Start adaptive mission-driven practice session."""
    from learning.services.practice_selector import select_practice_questions
    
    subject_id = request.data.get('subject_id')
    topic_id = request.data.get('topic_id')
    try:
        subject_id = int(subject_id) if subject_id is not None else None
    except (TypeError, ValueError):
        subject_id = None
    try:
        topic_id = int(topic_id) if topic_id is not None else None
    except (TypeError, ValueError):
        topic_id = None
    
    if not subject_id and not topic_id:
        return Response(
            {'error': 'subject_id or topic_id required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    mission_data = build_learning_mission(request.user, subject_id=subject_id)
    intent = mission_data.get("task_type")
    question_count = 8 if intent == "diagnostic" else 6
    
    question_ids = select_practice_questions(
        student=request.user,
        subject_id=subject_id,
        topic_id=topic_id,
        count=question_count,
        intent=intent,
    )
    
    if not question_ids:
        return Response(
            {'error': 'No questions available for practice'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Return first question
    first_question = Question.objects.filter(id=question_ids[0]).first()
    
    # Get subject/topic name for top bar display
    subject_name = None
    topic_name = None
    if subject_id:
        try:
            subj = Subject.objects.get(id=subject_id)
            subject_name = subj.display_name
        except Subject.DoesNotExist:
            pass
    elif topic_id:
        try:
            top = Topic.objects.get(id=topic_id)
            topic_name = top.name
            subject_name = top.subject.display_name
        except Topic.DoesNotExist:
            pass
    
    return Response({
        'mode': 'adaptive_practice' if intent != "diagnostic" else 'diagnostic',
        'question_ids': question_ids,
        'total_questions': len(question_ids),
        'question': QuestionForQuizSerializer(first_question).data if first_question else None,
        'subject_name': subject_name,
        'topic_name': topic_name,
        'mission': mission_data,
    })


# ---------------------------------------------------------------------
# Quiz: start session (gym mode + first question)
# ---------------------------------------------------------------------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def quiz_start(request):
    """Start a quiz session for a topic or quick-fire mode."""
    topic_id = request.data.get('topic_id')
    mode = request.data.get('mode')

    # Quick-fire: 5-10 random questions across all subjects
    if mode == 'quick_fire':
        questions = list(
            Question.objects.filter(is_active=True)
            .order_by('?')
            .values_list('id', flat=True)[:10]
        )
        response_data = {
            'mode': 'quick_fire',
            'reason': 'Quick practice',
            'content_type': 'questions',
            'question_ids': questions,
            'question': None,
        }
        if questions:
            first = Question.objects.filter(id=questions[0], is_active=True).first()
            if first:
                response_data['question'] = QuestionForQuizSerializer(first).data
        return Response(response_data)

    if topic_id is None:
        return Response({'error': 'topic_id or mode=quick_fire required'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        topic = Topic.objects.get(id=topic_id, is_active=True)
    except Topic.DoesNotExist:
        return Response({'error': 'Topic not found'}, status=status.HTTP_404_NOT_FOUND)

    use_llm_query = request.query_params.get('use_llm')
    use_llm = (
        str(use_llm_query).lower() in ('1', 'true', 'yes')
        if use_llm_query is not None
        else bool(getattr(settings, 'LLM_USE_FOR_QUIZ', False))
    )
    result = decide_gym_mode(request.user.id, int(topic_id), use_llm=use_llm)
    content = result.get('content') or {}
    items = content.get('items') or []
    content_type = content.get('content_type') or 'none'

    response_data = {
        'mode': result.get('mode'),
        'reason': result.get('reason'),
        'content_type': content_type,
        'question_ids': [],
        'question': None,
    }

    if content_type == 'questions' or content_type == 'exam_questions' or content_type == 'light_review':
        question_ids = [q['id'] for q in items if 'id' in q]
        response_data['question_ids'] = question_ids
        if question_ids:
            first = Question.objects.filter(id=question_ids[0], is_active=True).first()
            if first:
                response_data['question'] = QuestionForQuizSerializer(first).data
    elif content_type == 'lessons':
        response_data['lesson_ids'] = [l['id'] for l in items if 'id' in l]

    return Response(response_data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def quiz_question(request, question_id):
    """Get a single question for quiz (no correct answer)."""
    try:
        q = Question.objects.get(id=question_id, is_active=True)
    except Question.DoesNotExist:
        return Response({'error': 'Question not found'}, status=status.HTTP_404_NOT_FOUND)
    return Response(QuestionForQuizSerializer(q).data)


@login_required
def quiz_page(request):
    """Render quiz UI (topic from query param)."""
    return render(request, 'quiz.html')


def revision_planner_page(request):
    """Render revision planner (time left, upcoming exams)."""
    if not request.user.is_authenticated:
        return redirect('/login/')
    return render(request, 'revision_planner.html')


def subjects_page(request):
    """Render My Subjects page with subject cards and progress."""
    if not request.user.is_authenticated:
        return redirect('/login/')
    return render(request, 'subjects.html')


def mock_tests_page(request):
    """Render mock tests (past papers) - list and timed exam UI."""
    if not request.user.is_authenticated:
        return redirect('/login/')
    return render(request, 'mock_tests.html')


def exam_readiness_page(request):
    """Render exam-readiness monitor."""
    if not request.user.is_authenticated:
        return redirect('/login/')
    return render(request, 'exam_readiness.html')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def past_papers_list(request):
    """List link-based past papers filtered by subject/exam board."""
    from dashboard.models import PastPaper

    try:
        subject_id = int(request.query_params.get('subject_id')) if request.query_params.get('subject_id') else None
    except (TypeError, ValueError):
        subject_id = None

    try:
        exam_board_id = int(request.query_params.get('exam_board_id')) if request.query_params.get('exam_board_id') else None
    except (TypeError, ValueError):
        exam_board_id = None

    papers = PastPaper.objects.filter(
        is_active=True,
        subject__is_active=True,
        exam_board__is_active=True,
    ).select_related('subject', 'exam_board')

    if subject_id:
        papers = papers.filter(subject_id=subject_id)
    if exam_board_id:
        papers = papers.filter(exam_board_id=exam_board_id)

    return Response([
        {
            'id': p.id,
            'title': p.title,
            'subject_id': p.subject_id,
            'subject_name': p.subject.display_name,
            'exam_board_id': p.exam_board_id,
            'exam_board_code': p.exam_board.code,
            'year': p.year,
            'paper_number': p.paper_number,
            'source_url': p.source_url,
        }
        for p in papers.order_by('-year', 'paper_number')
    ])


def flashcards_page(request):
    """Render flashcards - deck list and flip-card UI."""
    if not request.user.is_authenticated:
        return redirect('/login/')
    return render(request, 'flashcards.html')


def mistakes_page(request):
    """Render mistake bank review queue."""
    if not request.user.is_authenticated:
        return redirect('/login/')
    return render(request, 'mistakes.html')


def mistake_retry_page(request, item_id):
    """Render exact retry page for a mistake-bank item."""
    if not request.user.is_authenticated:
        return redirect('/login/')
    return render(request, 'mistake_retry.html', {'item_id': item_id})


def parent_dashboard_page(request, parent_access_token):
    """Render parent dashboard (no login required for parents). Token is in URL for client-side API calls."""
    return render(request, 'parent_dashboard.html')


# ---------------------------------------------------------------------
# Mock exams (past papers + generated from question bank) - timed interface
# ---------------------------------------------------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mock_exams_list(request):
    """List available mock exams: curated past papers + generated options per subject (Option A)."""
    from dashboard.models import MockExam, MockExamQuestion, ExamBoard
    from django.db.models import Count
    from learning.services.exam_readiness import build_exam_readiness

    readiness_by_subject = {
        item["subject_id"]: item
        for item in build_exam_readiness(request.user)
    }

    def readiness_payload(subject_id):
        readiness = readiness_by_subject.get(subject_id)
        if not readiness:
            return {
                "exam_arena_unlocked": False,
                "score": 0,
                "status": "not_ready",
                "unlock_requirements": ["Build readiness before attempting timed mocks."],
            }
        return {
            "exam_arena_unlocked": readiness["exam_arena_unlocked"],
            "score": readiness["score"],
            "status": readiness["status"],
            "unlock_requirements": readiness["unlock_requirements"],
        }

    try:
        subject_id = int(request.query_params.get('subject_id')) if request.query_params.get('subject_id') else None
    except (TypeError, ValueError):
        subject_id = None
    qs = MockExam.objects.filter(is_active=True).select_related('subject')
    if subject_id:
        qs = qs.filter(subject_id=subject_id)
    mocks_with_questions = set(
        MockExamQuestion.objects.values_list('mock_exam_id', flat=True).distinct()
    )
    out = []
    for m in qs:
        if m.id not in mocks_with_questions:
            continue
        out.append({
            'id': m.id,
            'title': m.title,
            'subject_id': m.subject_id,
            'subject_name': m.subject.display_name if m.subject_id else '',
            'time_allowed_minutes': m.time_allowed_minutes,
            'total_marks': m.total_marks,
            'is_generated': False,
            'readiness': readiness_payload(m.subject_id),
        })
    # Option A: Add generated mock templates per subject (from question bank)
    subjects_with_questions = (
        Question.objects.filter(
            lesson__topic__subject__is_active=True,
            lesson__topic__is_active=True,
            lesson__is_active=True,
            is_active=True
        )
        .values('lesson__topic__subject_id', 'lesson__topic__subject__display_name')
        .annotate(qcount=Count('id'))
        .filter(qcount__gte=5)
    )
    for row in subjects_with_questions:
        sid = row['lesson__topic__subject_id']
        if subject_id and sid != subject_id:
            continue
        subj_name = row['lesson__topic__subject__display_name'] or 'Subject'
        out.append({
            'id': f'gen-{sid}',
            'title': f'Practice mock – {subj_name} (generated)',
            'subject_id': sid,
            'subject_name': subj_name,
            'time_allowed_minutes': 90,
            'total_marks': 80,
            'is_generated': True,
            'readiness': readiness_payload(sid),
        })
    return Response(out)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mock_exam_start(request):
    """Start a mock exam: curated past paper or generated from question bank (Option A)."""
    from django.utils import timezone
    from dashboard.models import MockExam, MockExamAttempt, MockExamQuestion, ExamBoard
    mock_exam_id = request.data.get('mock_exam_id')
    _sid = request.data.get('subject_id')
    subject_id = int(_sid) if _sid is not None else None
    is_generated = request.data.get('is_generated', False)
    if not mock_exam_id and not subject_id:
        return Response({'error': 'mock_exam_id or subject_id required'}, status=status.HTTP_400_BAD_REQUEST)
    if isinstance(mock_exam_id, str) and mock_exam_id.startswith('gen-'):
        try:
            subject_id = int(mock_exam_id.split('-')[1])
            is_generated = True
        except (ValueError, IndexError):
            pass
        mock_exam_id = None
    gate_subject_id = subject_id
    if gate_subject_id is None and mock_exam_id:
        try:
            mock_for_gate = MockExam.objects.get(id=mock_exam_id, is_active=True)
            gate_subject_id = mock_for_gate.subject_id
        except (MockExam.DoesNotExist, TypeError, ValueError):
            pass
    if gate_subject_id:
        from learning.services.exam_readiness import build_subject_exam_readiness
        try:
            gate_subject = Subject.objects.get(id=gate_subject_id, is_active=True)
        except Subject.DoesNotExist:
            return Response({'error': 'Subject not found'}, status=status.HTTP_404_NOT_FOUND)
        readiness = build_subject_exam_readiness(request.user, gate_subject)
        if not readiness.get('exam_arena_unlocked'):
            return Response(
                {
                    'error': 'Exam Arena is locked for this subject.',
                    'readiness': readiness,
                },
                status=status.HTTP_403_FORBIDDEN,
            )
    question_ids = []
    mock = None
    time_allowed_minutes = 90
    total_marks = 80
    if is_generated or subject_id:
        if not subject_id:
            return Response({'error': 'subject_id required for generated mock'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            subject = Subject.objects.get(id=subject_id, is_active=True)
        except Subject.DoesNotExist:
            return Response({'error': 'Subject not found'}, status=status.HTTP_404_NOT_FOUND)
        qs = Question.objects.filter(
            lesson__topic__subject=subject,
            lesson__topic__is_active=True,
            lesson__is_active=True,
            is_active=True
        ).order_by('?')[:30]
        question_ids = list(qs.values_list('id', flat=True))
        if len(question_ids) < 5:
            return Response({'error': 'Not enough questions in question bank for this subject'}, status=status.HTTP_400_BAD_REQUEST)
        exam_board = ExamBoard.objects.filter(is_active=True).first()
        if not exam_board:
            return Response({'error': 'No exam board configured'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        total_marks = min(80, sum(Question.objects.filter(id__in=question_ids).values_list('marks_available', flat=True)) or 80)
        mock = MockExam.objects.create(
            subject=subject,
            exam_board=exam_board,
            title=f'Practice mock – {subject.display_name} (generated)',
            total_marks=total_marks,
            time_allowed_minutes=90,
            tier=getattr(subject, 'tier', 'higher'),
        )
        for i, qid in enumerate(question_ids):
            q = Question.objects.get(id=qid)
            MockExamQuestion.objects.create(mock_exam=mock, question_id=qid, order=i, marks=q.marks_available)
    else:
        try:
            mock = MockExam.objects.get(id=mock_exam_id, is_active=True)
        except (MockExam.DoesNotExist, TypeError):
            return Response({'error': 'Mock exam not found'}, status=status.HTTP_404_NOT_FOUND)
        question_ids = list(
            MockExamQuestion.objects.filter(mock_exam=mock).order_by('order').values_list('question_id', flat=True)
        )
        if not question_ids:
            return Response({'error': 'This mock exam has no questions'}, status=status.HTTP_400_BAD_REQUEST)
        total_marks = sum(
            MockExamQuestion.objects.filter(mock_exam=mock).order_by('order').values_list('marks', flat=True)
        ) or mock.total_marks
        time_allowed_minutes = mock.time_allowed_minutes
    started_at = timezone.now()
    attempt = MockExamAttempt.objects.create(
        student=request.user,
        mock_exam=mock,
        started_at=started_at,
        total_marks_available=total_marks,
        exam_conditions=True,
    )
    first_q = Question.objects.filter(id=question_ids[0], is_active=True).first()
    return Response({
        'attempt_id': attempt.id,
        'question_ids': question_ids,
        'time_allowed_seconds': time_allowed_minutes * 60,
        'question': QuestionForQuizSerializer(first_q).data if first_q else None,
        'current_index': 0,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mock_exam_question(request, attempt_id, question_id):
    """Get a question for an in-progress mock attempt (no correct answer)."""
    from dashboard.models import MockExamAttempt, MockExamQuestion
    try:
        attempt = MockExamAttempt.objects.get(id=attempt_id, student=request.user, status='in_progress')
    except MockExamAttempt.DoesNotExist:
        return Response({'error': 'Attempt not found'}, status=status.HTTP_404_NOT_FOUND)
    qids = list(MockExamQuestion.objects.filter(mock_exam=attempt.mock_exam).order_by('order').values_list('question_id', flat=True))
    if int(question_id) not in qids:
        return Response({'error': 'Question not in this mock'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        q = Question.objects.get(id=question_id, is_active=True)
    except Question.DoesNotExist:
        return Response({'error': 'Question not found'}, status=status.HTTP_404_NOT_FOUND)
    return Response(QuestionForQuizSerializer(q).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mock_exam_submit(request, attempt_id):
    """Submit one answer; return result and next question or finished."""
    from django.utils import timezone
    from dashboard.models import MockExamAttempt, MockExamQuestion, MockExamAttemptAnswer
    from .models import MultipleChoiceOption
    try:
        attempt = MockExamAttempt.objects.get(id=attempt_id, student=request.user, status='in_progress')
    except MockExamAttempt.DoesNotExist:
        return Response({'error': 'Attempt not found'}, status=status.HTTP_404_NOT_FOUND)
    question_id = request.data.get('question_id')
    if not question_id:
        return Response({'error': 'question_id required'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        question = Question.objects.get(id=question_id, is_active=True)
    except Question.DoesNotExist:
        return Response({'error': 'Question not found'}, status=status.HTTP_404_NOT_FOUND)
    mq = MockExamQuestion.objects.filter(mock_exam=attempt.mock_exam, question=question).first()
    marks_for_question = mq.marks if mq else question.marks_available
    selected_option_id = request.data.get('selected_option_id')
    is_correct = False
    if selected_option_id:
        try:
            opt = MultipleChoiceOption.objects.get(id=selected_option_id, question=question)
            is_correct = opt.is_correct
        except MultipleChoiceOption.DoesNotExist:
            pass
    else:
        from learning.services.answer_grading import answers_equivalent

        raw = request.data.get("answer") or ""
        is_correct, _ = answers_equivalent(raw, question.correct_answer or "")
    marks_achieved = marks_for_question if is_correct else 0
    MockExamAttemptAnswer.objects.update_or_create(
        attempt=attempt, question=question,
        defaults={'marks_achieved': marks_achieved, 'correct': is_correct},
    )
    qids = list(MockExamQuestion.objects.filter(mock_exam=attempt.mock_exam).order_by('order').values_list('question_id', flat=True))
    current_idx = qids.index(int(question_id)) if int(question_id) in qids else -1
    next_idx = current_idx + 1
    next_question = None
    finished = False
    if next_idx < len(qids):
        next_q = Question.objects.filter(id=qids[next_idx], is_active=True).first()
        if next_q:
            next_question = QuestionForQuizSerializer(next_q).data
    else:
        finished = True
        total_achieved = sum(
            MockExamAttemptAnswer.objects.filter(attempt=attempt).values_list('marks_achieved', flat=True)
        )
        attempt.marks_achieved = total_achieved
        attempt.completed_at = timezone.now()
        attempt.time_taken_seconds = int((attempt.completed_at - attempt.started_at).total_seconds())
        attempt.percentage_score = round(100.0 * total_achieved / attempt.total_marks_available, 1) if attempt.total_marks_available else 0
        attempt.predicted_grade = calculate_predicted_grade(
            percentage=attempt.percentage_score,
            subject=attempt.mock_exam.subject,
            exam_board=attempt.mock_exam.exam_board,
        )
        attempt.status = 'completed'
        attempt.save()
    payload = {
        'correct': is_correct,
        'marks_achieved': marks_achieved,
        'explanation': question.explanation or '',
        'next_question': next_question,
        'finished': finished,
        'next_index': next_idx if not finished else None,
    }
    if finished:
        payload['total_marks_achieved'] = attempt.marks_achieved
        payload['total_marks_available'] = attempt.total_marks_available
        payload['percentage_score'] = attempt.percentage_score
        payload['predicted_grade'] = attempt.predicted_grade
        try:
            from learning.services.mock_debrief import build_mock_debrief
            payload['debrief'] = build_mock_debrief(attempt)
        except Exception:
            payload['debrief'] = None
    return Response(payload)


# ---------------------------------------------------------------------
# submit_attempt endpoint
# ---------------------------------------------------------------------
@api_view(['POST'])
@permission_classes([DRFIsAuthenticated])
def submit_attempt(request):
    limit_response = check_free_tier_limits(request.user)
    if limit_response is not None:
        return limit_response

    serializer = AttemptSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        attempt = serializer.save()
        
        # Get skill codes for this question (for practice summary)
        skill_codes = list(
            attempt.question.steps.values_list('skill__code', flat=True).distinct()
        )
        xp_earned = 10 if attempt.is_correct else 2
        
        confidence_level = (request.data.get("confidence_level") or "unsure").strip().lower()
        if confidence_level not in ("guessed", "unsure", "confident"):
            confidence_level = "unsure"

        mission_data = build_learning_mission(
            request.user, subject_id=attempt.question.lesson.topic.subject_id
        )
        next_action = mission_data.get("cta_url", "/subjects/")

        payload = {
            'id': attempt.id,
            'is_correct': attempt.is_correct,
            'question_id': attempt.question.id,
            'explanation': attempt.question.explanation or "",
            'skill_codes': skill_codes,
            'xp_earned': xp_earned,
            'marks_awarded': getattr(attempt, "partial_marks", 0),
            'marks_available': getattr(attempt, "marks_available", attempt.question.marks_available or 1),
            'confidence_level': confidence_level,
            'skill_impact': 'improved' if attempt.is_correct else 'needs_work',
            'next_action': next_action,
            'next_action_reason': mission_data.get("reason", ""),
            'wrong_category': getattr(attempt, "wrong_category", "none"),
            'failed_skill': getattr(attempt, "failed_skill", None),
            'remediation_tip': getattr(attempt, "remediation_tip", ""),
            'session_summary': {
                'strongest_skill': skill_codes[0] if attempt.is_correct and skill_codes else None,
                'weakest_skill': skill_codes[0] if (not attempt.is_correct) and skill_codes else None,
                'next_action': next_action,
                'marks_awarded': getattr(attempt, "partial_marks", 0),
                'marks_available': getattr(attempt, "marks_available", attempt.question.marks_available or 1),
            },
        }
        if not attempt.is_correct:
            payload['correct_answer'] = attempt.question.correct_answer or ""
        return Response(payload)
    return Response(serializer.errors, status=400)


# ---------------------------------------------------------------------
# Subject detail page (template view)
# ---------------------------------------------------------------------
@login_required
def subject_detail_page(request, subject_id):
    """Render subject detail page with topic cards."""
    return render(request, 'subject_detail.html', {'subject_id': subject_id})


# ---------------------------------------------------------------------
# Predicted Grade endpoint
# ---------------------------------------------------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def predicted_grade_view(request):
    """GET /api/predicted-grade/ — predicted grades per subject with exam settings."""
    from datetime import date as _date
    from decision_engine.v1_0.decision_engine_v1 import evaluate_student_subject
    from .services.predicted_grade import predict_grade

    settings_qs = (
        StudentExamSettings.objects
        .filter(student=request.user)
        .select_related('subject')
    )

    results = []
    for setting in settings_qs:
        if setting.exam_date < _date.today():
            continue
        try:
            engine_result = evaluate_student_subject(
                student_id=request.user.pk,
                subject_id=setting.subject_id,
                exam_date=setting.exam_date,
                target_grade=setting.target_grade,
            )
            grade_data = predict_grade(
                attainment_band=engine_result['attainment_band'],
                target_grade=setting.target_grade,
                weeks_remaining=engine_result['weeks_remaining'],
            )
        except Exception as exc:
            logger.warning("predicted_grade_view error for subject %s: %s", setting.subject_id, exc)
            continue

        results.append({
            'subject_id': setting.subject_id,
            'subject_name': setting.subject.display_name,
            'predicted_grade': grade_data['predicted_grade'],
            'confidence': grade_data['confidence'],
            'message': grade_data['message'],
            'target_grade': setting.target_grade,
            'weeks_remaining': engine_result['weeks_remaining'],
        })

    return Response(results)


# ---------------------------------------------------------------------
# Revision Timetable endpoint
# ---------------------------------------------------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def revision_timetable_view(request):
    """GET /api/revision-timetable/?days=42 — personalised revision calendar."""
    from django.utils.timezone import now as _now
    from .services.revision_timetable import build_revision_timetable

    try:
        days = int(request.query_params.get('days', 42))
        days = max(1, min(days, 365))
    except (TypeError, ValueError):
        days = 42

    timetable = build_revision_timetable(request.user, days_ahead=days)
    return Response({'timetable': timetable, 'generated_at': _now().isoformat()})
