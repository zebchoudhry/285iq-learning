"""
Undo the 25 November 2026 duplicate-question cleanup for Maths and Physics.

What happened: the same question wording had been copied into many topics (one physics
question 68 times). In Maths and Physics every copy but one was switched off
(is_active=False), keeping the copy whose topic best matched the question. Lessons that
would otherwise have had no questions kept up to five of their own. Nothing was deleted,
and no student had ever answered any of the hidden copies.

The hidden set is exactly: Maths and Physics questions that are inactive and are not the
old "[Fallback] ..." placeholders (those were switched off earlier by migration 0020).
At the time of the cleanup that was 2,896 questions, ids 274 to 9263, id sum 15,089,011.

This command switches them back on. It refuses to run if the set no longer matches the
recorded checksum (for example if other questions were switched off since), unless --force.

    python manage.py restore_question_dedupe            # report only
    python manage.py restore_question_dedupe --apply    # switch them back on
"""
from django.core.management.base import BaseCommand
from django.db.models import Sum

from learning.models import Question

EXPECTED_COUNT = 2896
EXPECTED_SUM = 15_089_011


def hidden_copies():
    return Question.objects.filter(
        is_active=False, lesson__topic__subject__name__in=("mathematics", "physics"),
    ).exclude(question_text__startswith="[Fallback]")


class Command(BaseCommand):
    help = "Switch back on the Maths/Physics duplicate copies hidden on 2026-11-25."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true", help="Actually switch them back on.")
        parser.add_argument("--force", action="store_true", help="Run even if the checksum does not match.")

    def handle(self, *args, apply=False, force=False, **opts):
        qs = hidden_copies()
        count = qs.count()
        total = qs.aggregate(s=Sum("id"))["s"] or 0
        matches = count == EXPECTED_COUNT and total == EXPECTED_SUM
        self.stdout.write(f"Inactive Maths/Physics non-placeholder questions: {count} (id sum {total}).")
        self.stdout.write("Matches the recorded cleanup." if matches else
                          f"Does NOT match the recorded cleanup ({EXPECTED_COUNT}, sum {EXPECTED_SUM}).")
        if not apply:
            self.stdout.write("Report only. Re-run with --apply to switch them back on.")
            return
        if not matches and not force:
            self.stderr.write("Refusing: the set has changed since the cleanup. Use --force only if you are sure.")
            return
        updated = qs.update(is_active=True)
        self.stdout.write(self.style.SUCCESS(f"Switched {updated} questions back on."))
