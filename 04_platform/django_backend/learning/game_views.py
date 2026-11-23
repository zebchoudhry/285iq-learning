"""Learning mini-game pages and endpoints (API mounted under /api/)."""
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import GameSession
from .services import games


def _error(exc):
    return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def games_list(request):
    return Response({
        "games": games.hub_summary(request.user),
        "xp_today": games.game_xp_today(request.user),
        "daily_cap": games.DAILY_GAME_XP_CAP,
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def game_start(request, slug):
    try:
        game = games.get_game(slug)
        session = games.start_session(request.user, slug)
    except games.GameError as exc:
        return _error(exc)
    return Response({
        "session_id": session.id, "slug": game.slug, "title": game.title,
        "time_limit_s": game.time_limit_s, "rounds": games.public_rounds(session),
    })


def _own_session(request, session_id):
    return get_object_or_404(GameSession, id=session_id, student=request.user)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def game_answer(request, session_id):
    session = _own_session(request, session_id)
    try:
        return Response(games.submit_answer(session, request.data.get("round"), request.data.get("answer")))
    except games.GameError as exc:
        return _error(exc)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def game_finish(request, session_id):
    session = _own_session(request, session_id)
    try:
        return Response(games.finish_session(session))
    except games.GameError as exc:
        return _error(exc)


@login_required
@ensure_csrf_cookie
def games_hub_page(request):
    return render(request, "games_hub.html")


@login_required
@ensure_csrf_cookie
def game_play_page(request, slug):
    if slug not in games.BY_SLUG:
        raise Http404
    return render(request, "game_play.html", {"game": games.BY_SLUG[slug]})
