"""
URLs for content app
"""
from django.urls import path
from . import views

app_name = 'content'

urlpatterns = [
    # URLs will be added here as we build features
    path('', views.placeholder_view, name='placeholder'),
]
