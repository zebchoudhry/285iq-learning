"""
"Download my data": everything the app stores about one user, as plain JSON.

It walks every table that points at the user, so new features are included automatically.
The password hash and the parent progress-link token are left out on purpose (secrets).
"""
from django.db import models

ACCOUNT_FIELDS_LEFT_OUT = {"password", "parent_access_token", "is_superuser", "is_staff", "groups", "user_permissions"}
MAX_ROWS_PER_TABLE = 20000


def _plain(value):
    return value if value is None or isinstance(value, (str, int, float, bool)) else str(value)


def _row(obj, fields):
    return {f.name: _plain(getattr(obj, f.attname, None)) for f in fields}


def build_export(user) -> dict:
    account_fields = [
        f for f in user._meta.concrete_fields if f.name not in ACCOUNT_FIELDS_LEFT_OUT
    ]
    data = {
        "about": "Everything 285IQ stores about your account. The password (kept scrambled) and your private "
                 "parent progress link are left out for your security.",
        "account": _row(user, account_fields),
    }
    for rel in user._meta.related_objects:
        if not (rel.one_to_many or rel.one_to_one) or rel.related_model is None:
            continue
        model = rel.related_model
        if model._meta.auto_created:  # through tables
            continue
        accessor = rel.get_accessor_name()
        try:
            manager = getattr(user, accessor)
        except Exception:
            continue
        fields = [f for f in model._meta.concrete_fields]
        if rel.one_to_one:
            related = manager if isinstance(manager, models.Model) else None
            rows = [_row(related, fields)] if related else []
        else:
            rows = [_row(o, fields) for o in manager.all()[:MAX_ROWS_PER_TABLE]]
        if rows:
            data[model._meta.model_name] = rows
    return data
