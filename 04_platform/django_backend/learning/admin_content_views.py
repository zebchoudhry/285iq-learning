"""
Staff-only content management endpoints.

POST /api/admin/generate-questions/
  Body: { "topic_id": 3, "count": 10, "difficulty": 2 }
  Requires: is_staff=True

GET /api/admin/question-stats/
  Returns question counts per topic.
"""
import logging

from django.contrib.auth.decorators import user_passes_test
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status

from learning.models import Topic, Question
from learning.services.llm_question_generator import generate_questions

logger = logging.getLogger(__name__)


@api_view(["POST"])
@permission_classes([IsAdminUser])
def admin_generate_questions(request):
    """
    Generate LLM questions for a topic and persist them.
    Staff only.
    """
    topic_id = request.data.get("topic_id")
    count = min(int(request.data.get("count", 10)), 50)  # cap at 50 per request
    difficulty = int(request.data.get("difficulty", 2))

    if not topic_id:
        return Response({"error": "topic_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        topic = Topic.objects.select_related("subject").get(id=topic_id, is_active=True)
    except Topic.DoesNotExist:
        return Response({"error": "Topic not found"}, status=status.HTTP_404_NOT_FOUND)

    try:
        created = generate_questions(topic_id=topic_id, mode="practice", difficulty=difficulty, count=count)
        if created is None:
            created = []
        logger.info(
            "Admin %s generated %d questions for topic %s (%s)",
            request.user.username, len(created), topic_id, topic.name,
        )
        return Response({
            "topic_id": topic_id,
            "topic_name": topic.name,
            "subject": topic.subject.display_name,
            "questions_created": len(created),
            "question_ids": [q.id for q in created],
        })
    except RuntimeError as exc:
        return Response({"error": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as exc:
        logger.error("Question generation failed for topic %s: %s", topic_id, exc, exc_info=True)
        return Response({"error": "Generation failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAdminUser])
def admin_question_stats(request):
    """
    Return question counts per subject/topic.
    Staff only.
    """
    from django.db.models import Count
    stats = (
        Question.objects
        .filter(is_active=True)
        .values(
            "lesson__topic__id",
            "lesson__topic__name",
            "lesson__topic__subject__display_name",
        )
        .annotate(count=Count("id"))
        .order_by("lesson__topic__subject__display_name", "lesson__topic__name")
    )
    return Response(list(stats))
