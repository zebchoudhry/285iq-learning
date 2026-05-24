"""WSGI entry for Vercel when building from the repository root."""
import os
import sys

_backend = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "04_platform",
    "django_backend",
)
os.chdir(_backend)
if _backend not in sys.path:
    sys.path.insert(0, _backend)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "studymate285.settings")

from studymate285.wsgi import application
