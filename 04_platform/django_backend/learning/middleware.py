"""Middleware used for deployment diagnostics."""
import os
import traceback

from django.http import HttpResponse


class VercelDiagnosticMiddleware:
    """Return tracebacks as plain text when VERCEL_DIAGNOSTIC=1 (temporary debugging)."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.enabled = os.environ.get("VERCEL_DIAGNOSTIC", "").lower() in (
            "1",
            "true",
            "yes",
        )

    def __call__(self, request):
        if not self.enabled:
            return self.get_response(request)
        try:
            return self.get_response(request)
        except Exception:
            return HttpResponse(
                traceback.format_exc(),
                content_type="text/plain; charset=utf-8",
                status=500,
            )



class PrivatePagesNoIndexMiddleware:
    """
    Tell search engines never to index pages that belong to a signed-in student or to a
    parent's private link. robots.txt only asks crawlers not to visit, and does not stop a
    URL that has been shared from being indexed, so this header is the real protection.
    """

    EXTRA = ("/login/", "/forgot-password/", "/reset-password/", "/register/success")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        from learning.seo_views import PRIVATE_PREFIXES

        path = request.path
        if not path.startswith("/static/") and path.startswith(PRIVATE_PREFIXES + self.EXTRA):
            response["X-Robots-Tag"] = "noindex, nofollow"
        return response
