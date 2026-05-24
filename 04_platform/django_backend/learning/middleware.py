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
