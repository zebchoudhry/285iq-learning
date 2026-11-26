"""
Load the hand-written chemistry question bank (question_bank/chemistry, 504 questions, 8 for
every chemistry lesson) and switch off the old generic chemistry questions that had been
copied into many lessons (for example "What products are formed when an acid reacts with a
base?" in 49 lessons). Copies are switched off, not deleted.

It runs only where the chemistry lessons exist (production). On an empty database, such as
the test database, it does nothing.

Reverse: switches the written chemistry questions off and the switched-off generic chemistry
questions back on.
"""
from io import StringIO

from django.core.management import call_command
from django.db import migrations

SOURCE = "Written for 285IQ (chemistry)"


def load(apps, schema_editor):
    Lesson = apps.get_model("learning", "Lesson")
    if not Lesson.objects.filter(topic__subject__name__iexact="chemistry", is_active=True).exists():
        return
    # Any non-written chemistry wording found in 2 or more lessons is a pasted copy.
    call_command("load_written_questions", "--subject", "chemistry", "--retire-filler", "--min-lessons", "2",
                 stdout=StringIO())


def unload(apps, schema_editor):
    Question = apps.get_model("learning", "Question")
    chemistry = Question.objects.filter(lesson__topic__subject__name__iexact="chemistry")
    chemistry.filter(source=SOURCE).update(is_active=False)
    chemistry.filter(is_active=False).exclude(source=SOURCE).exclude(
        question_text__startswith="[Fallback]").update(is_active=True)


class Migration(migrations.Migration):
    dependencies = [("learning", "0021_readiness_snapshot")]
    operations = [migrations.RunPython(load, unload)]
