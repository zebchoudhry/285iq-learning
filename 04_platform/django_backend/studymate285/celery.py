"""
Celery application for 285IQ async task processing.
"""
import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "studymate285.settings")

app = Celery("studymate285")

# Read config from Django settings, CELERY_ namespace
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks in all INSTALLED_APPS
app.autodiscover_tasks()
