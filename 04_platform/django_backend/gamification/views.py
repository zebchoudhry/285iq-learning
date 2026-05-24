"""
Views for gamification app
"""
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['GET'])
def placeholder_view(request):
    """Placeholder view - will be replaced with real functionality"""
    return Response({
        'message': f'Gamification app is ready!',
        'status': 'placeholder'
    })
