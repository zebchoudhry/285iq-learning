"""Boss battle and gamification endpoints (mounted under /api/)."""
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import BossBattle, Question, Topic
from .serializers import AttemptSerializer, QuestionForQuizSerializer
from .services import boss_battle, gamification
from .services.subscription_limits import check_free_tier_limits


def _question_payload(question_id):
    if question_id is None:
        return None
    question = Question.objects.filter(id=question_id, is_active=True).first()
    return QuestionForQuizSerializer(question).data if question else None


def _battle_response(battle, **extra):
    return Response({
        "battle": boss_battle.battle_state(battle),
        "question": _question_payload(boss_battle.current_question_id(battle)),
        **extra,
    })


def _own_battle(request, battle_id):
    return get_object_or_404(
        BossBattle.objects.select_related("topic"), id=battle_id, student=request.user
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def boss_start(request):
    """Start (or resume) the boss battle for a topic."""
    topic_id = request.data.get("topic_id")
    try:
        topic = Topic.objects.get(id=int(topic_id), is_active=True)
    except (TypeError, ValueError, Topic.DoesNotExist):
        return Response({"error": "Topic not found"}, status=status.HTTP_404_NOT_FOUND)
    try:
        battle = boss_battle.start_battle(request.user, topic)
    except boss_battle.BossError as exc:
        return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    return _battle_response(battle)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def boss_detail(request, battle_id):
    return _battle_response(_own_battle(request, battle_id))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def boss_answer(request, battle_id):
    """Answer the current question in a battle. The attempt is recorded like any other."""
    battle = _own_battle(request, battle_id)
    if battle.status != "active":
        return Response({"error": "This battle is over."}, status=status.HTTP_400_BAD_REQUEST)

    limit_response = check_free_tier_limits(request.user)
    if limit_response is not None:
        return limit_response

    serializer = AttemptSerializer(data=request.data, context={"request": request})
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    question_id = serializer.validated_data["question_id"]
    if boss_battle.current_question_id(battle) != question_id:
        return Response(
            {"error": "That isn't the current question in this battle."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    attempt = serializer.save()
    hit = boss_battle.apply_answer(battle, question_id, attempt.is_correct)

    payload = {
        "is_correct": attempt.is_correct,
        "question_id": question_id,
        "explanation": attempt.question.explanation or "",
        **gamification.reward_payload(getattr(attempt, "reward", None), attempt.is_correct),
        "hit": {k: v for k, v in hit.items() if k != "level"},
    }
    if hit.get("level"):
        payload["win_bonus_level"] = {
            "level": hit["level"]["level"], "rank": hit["level"]["rank"],
            "leveled_up": hit["level"]["leveled_up"],
        }
    if not attempt.is_correct:
        correct_answer = attempt.question.correct_answer or ""
        if not correct_answer:  # multiple choice stores the answer on the options
            correct = attempt.question.options.filter(is_correct=True).first()
            correct_answer = correct.option_text if correct else ""
        payload["correct_answer"] = correct_answer
        feedback = getattr(attempt, "mistake_feedback", None)
        if feedback:
            payload["mistake_feedback"] = feedback
            if feedback.get("explanation"):
                payload["explanation"] = feedback["explanation"]
    return _battle_response(battle, result=payload)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def gamification_me(request):
    """Level, rank, XP, streak and current combo for the signed-in student."""
    return Response(gamification.progress_summary(request.user))


@login_required
@ensure_csrf_cookie
def boss_page(request, topic_id):
    topic = get_object_or_404(Topic, id=topic_id, is_active=True)
    return render(request, "boss.html", {"topic": topic})
