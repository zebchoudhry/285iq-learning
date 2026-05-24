"""
WSGI entry for Vercel (repository root).
Bootstraps the Django project in 04_platform/django_backend.
"""
import os
import sys
import traceback

_BACKEND = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "04_platform",
    "django_backend",
)


def _bootstrap():
    os.chdir(_BACKEND)
    if _BACKEND not in sys.path:
        sys.path.insert(0, _BACKEND)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "studymate285.settings")


def _error_application(exc: BaseException):
    """If Django fails to import, return the traceback as the HTTP body."""
    body = traceback.format_exc().encode("utf-8")

    def application(environ, start_response):
        start_response(
            "500 Internal Server Error",
            [("Content-Type", "text/plain; charset=utf-8")],
        )
        return [body]

    return application


try:
    _bootstrap()
    from django.core.wsgi import get_wsgi_application

    application = get_wsgi_application()
    app = application  # Vercel / ASGI tooling alias
except Exception as exc:
    application = _error_application(exc)
    app = application
