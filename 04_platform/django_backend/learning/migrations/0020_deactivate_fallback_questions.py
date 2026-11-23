"""
Switch off the placeholder questions ("[Fallback] Topic: practice question N" with the
answer "Sample answer"). They were created when generated content was missing and teach
nothing. They are deactivated, not deleted, so past attempts that point at them survive.
"""
from django.db import migrations


def deactivate(apps, schema_editor):
    Question = apps.get_model("learning", "Question")
    Question.objects.filter(question_text__startswith="[Fallback]", correct_answer="Sample answer").update(is_active=False)


def reactivate(apps, schema_editor):
    Question = apps.get_model("learning", "Question")
    Question.objects.filter(question_text__startswith="[Fallback]", correct_answer="Sample answer").update(is_active=True)


class Migration(migrations.Migration):
    dependencies = [("learning", "0019_gamesession")]
    operations = [migrations.RunPython(deactivate, reactivate)]
