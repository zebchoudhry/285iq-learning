"""
Friend / social layer views for the 285IQ platform.
"""
import logging

from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Friendship, UserProfile

logger = logging.getLogger(__name__)

User = get_user_model()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _profile_summary(student):
    """Return a small dict of stats for a student."""
    try:
        profile = student.profile
        return {
            'id': student.id,
            'username': student.username,
            'first_name': student.first_name,
            'total_xp': profile.total_xp,
            'daily_streak': profile.daily_streak,
            'last_activity_date': profile.last_activity_date,
            'current_level': profile.current_level,
        }
    except UserProfile.DoesNotExist:
        return {
            'id': student.id,
            'username': student.username,
            'first_name': student.first_name,
            'total_xp': 0,
            'daily_streak': 0,
            'last_activity_date': None,
            'current_level': 1,
        }


# ── Endpoints ─────────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_friend_request(request):
    """
    POST /api/users/friends/request/
    Body: { "username": "<target username>" }
    Creates a Friendship with status='pending'.
    """
    username = (request.data.get('username') or '').strip()
    if not username:
        return Response({'error': 'username is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        target = User.objects.get(username=username)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    if target == request.user:
        return Response({'error': 'Cannot befriend yourself'}, status=status.HTTP_400_BAD_REQUEST)

    friendship, created = Friendship.objects.get_or_create(
        student=request.user,
        friend=target,
        defaults={'status': Friendship.STATUS_PENDING},
    )
    if not created:
        return Response(
            {'error': 'Friend request already exists', 'status': friendship.status},
            status=status.HTTP_409_CONFLICT,
        )

    logger.info('Friend request sent: %s -> %s', request.user.username, target.username)
    return Response(
        {'id': friendship.id, 'status': friendship.status, 'to': target.username},
        status=status.HTTP_201_CREATED,
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def accept_friend_request(request):
    """
    POST /api/users/friends/accept/
    Body: { "friendship_id": <int> }
    Sets status='accepted' on the incoming request and creates the reverse link.
    """
    friendship_id = request.data.get('friendship_id')
    if not friendship_id:
        return Response({'error': 'friendship_id is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        friendship = Friendship.objects.get(id=friendship_id, friend=request.user)
    except Friendship.DoesNotExist:
        return Response({'error': 'Friendship request not found'}, status=status.HTTP_404_NOT_FOUND)

    if friendship.status != Friendship.STATUS_PENDING:
        return Response(
            {'error': f'Request is already {friendship.status}'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    with transaction.atomic():
        friendship.status = Friendship.STATUS_ACCEPTED
        friendship.save(update_fields=['status'])

        # Create the reverse link so both sides appear in each other's friend list
        Friendship.objects.get_or_create(
            student=request.user,
            friend=friendship.student,
            defaults={'status': Friendship.STATUS_ACCEPTED},
        )

    logger.info(
        'Friend request accepted: %s accepted request from %s',
        request.user.username,
        friendship.student.username,
    )
    return Response({'id': friendship.id, 'status': friendship.status})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def friends_list(request):
    """
    GET /api/users/friends/
    Returns accepted friends with XP, streak, last_activity_date.
    """
    friend_ids = Friendship.objects.filter(
        student=request.user,
        status=Friendship.STATUS_ACCEPTED,
    ).values_list('friend_id', flat=True)

    friends = User.objects.filter(id__in=friend_ids).select_related('profile')
    data = [_profile_summary(f) for f in friends]
    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def friends_leaderboard(request):
    """
    GET /api/users/friends/leaderboard/
    Returns accepted friends sorted by total_xp desc, with rank position.
    Also includes the requesting user so they can see their own standing.
    """
    friend_ids = list(
        Friendship.objects.filter(
            student=request.user,
            status=Friendship.STATUS_ACCEPTED,
        ).values_list('friend_id', flat=True)
    )
    # Include self in leaderboard
    all_ids = friend_ids + [request.user.id]

    users = User.objects.filter(id__in=all_ids).select_related('profile')
    entries = sorted(
        [_profile_summary(u) for u in users],
        key=lambda e: e['total_xp'],
        reverse=True,
    )

    for rank, entry in enumerate(entries, start=1):
        entry['rank'] = rank
        entry['is_self'] = (entry['id'] == request.user.id)

    return Response(entries)
