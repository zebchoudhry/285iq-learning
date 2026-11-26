"""Public legal pages: privacy notice and terms of use."""
from django.conf import settings
from django.shortcuts import render

from .seo_views import _base_context

UPDATED = "26 November 2026"


def _page(request, path, template, title, description):
    ctx = _base_context(request, path, title, description, {})
    ctx["jsonld"] = ""  # no structured data on legal pages
    ctx.update(
        updated=UPDATED,
        privacy_email=settings.PRIVACY_EMAIL,
        operator=(settings.OPERATOR_NAME or "").strip(),
        minimum_age=settings.MINIMUM_AGE,
        version=settings.TERMS_VERSION,
    )
    return render(request, template, ctx)


def privacy_page(request):
    return _page(request, "/privacy/", "site/privacy.html", "Privacy notice | 285IQ",
                 "What 285IQ collects, why, who it is shared with, how long it is kept, and how to see, "
                 "download or delete your data.")


def terms_page(request):
    return _page(request, "/terms/", "site/terms.html", "Terms of use | 285IQ",
                 "The rules for using 285IQ, written in plain English for students and parents.")
