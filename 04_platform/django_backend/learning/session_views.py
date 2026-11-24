"""API and page for the "Start your 10 minutes" daily session."""
from django.shortcuts import redirect, render
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from learning.services.daily_session import build_daily_session
from learning.services.exam_progress import build_exam_progress


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def daily_session(request):
    """Today's short session: due mistakes, due flashcards, then the weakest topic."""
    try:
        size = int(request.query_params.get("size", 8))
    except (TypeError, ValueError):
        size = 8
    return Response(build_daily_session(request.user, size=size))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def exam_progress(request):
    """Readiness bar per subject, days to exam, and whether the student is on pace."""
    return Response(build_exam_progress(request.user))


@ensure_csrf_cookie
def today_page(request):
    if not request.user.is_authenticated:
        return redirect("/login/")
    return render(request, "today.html")
