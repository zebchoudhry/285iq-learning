#!/usr/bin/env python
"""Repo-root entry so Vercel detects Django when Root Directory is the repository root."""
import os
import sys


def _bootstrap_backend():
    backend = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "04_platform",
        "django_backend",
    )
    os.chdir(backend)
    if backend not in sys.path:
        sys.path.insert(0, backend)
    return backend


_bootstrap_backend()
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "studymate285.settings")

from django.core.management import execute_from_command_line

if __name__ == "__main__":
    execute_from_command_line(sys.argv)
