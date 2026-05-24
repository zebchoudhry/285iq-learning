import time

import anthropic
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from learning.models import Lesson

CONTENT_PROMPT = """You are an expert GCSE teacher. Generate lesson content for a GCSE {subject} lesson titled "{title}".

Format your response EXACTLY like this with these exact section headers:

Key Concept
[2-3 sentences explaining the core concept clearly]

Formula/Key Info
[Key formulas, rules, or facts students need to know. Use plain text, no markdown]

Worked Example
[A step by step worked example showing how to apply the concept]

Common Mistake
[The most common mistake students make on this topic and how to avoid it]

Quick Check
[One question students can use to test their understanding]

Rules:
- Plain text only, no markdown, no bullet points with symbols
- GCSE level appropriate
- Concise and clear
- Each section must have content
"""


class Command(BaseCommand):
    help = 'Generate lesson content using Claude API for placeholder lessons'

    def add_arguments(self, parser):
        parser.add_argument('--subject', type=str, help='Filter by subject name (e.g. mathematics)')
        parser.add_argument('--limit', type=int, default=0, help='Max lessons to process (0 = all)')
        parser.add_argument('--dry-run', action='store_true', help='Show what would be generated without saving')

    def handle(self, *args, **options):
        api_key = getattr(settings, 'ANTHROPIC_API_KEY', '') or ''
        if not api_key:
            raise CommandError('ANTHROPIC_API_KEY not set in settings/env')

        client = anthropic.Anthropic(api_key=api_key)

        from django.db.models import Q
        lessons = Lesson.objects.filter(
            Q(content__startswith='Lesson content for') |
            Q(content__startswith='Learning materials for')
        )

        if options['subject']:
            lessons = lessons.filter(topic__subject__name=options['subject'])

        if options['limit']:
            lessons = lessons[:options['limit']]

        total = lessons.count()
        self.stdout.write(f'Found {total} lessons to generate content for')

        updated = 0
        errors = 0

        for i, lesson in enumerate(lessons):
            subject_name = lesson.topic.subject.name
            self.stdout.write(f'[{i+1}/{total}] Generating: {lesson.title}')

            if options['dry_run']:
                self.stdout.write(f'  DRY RUN - would generate for: {lesson.title}')
                continue

            try:
                message = client.messages.create(
                    model='claude-sonnet-4-20250514',
                    max_tokens=1000,
                    messages=[
                        {
                            'role': 'user',
                            'content': CONTENT_PROMPT.format(
                                subject=subject_name,
                                title=lesson.title
                            )
                        }
                    ]
                )
                content = message.content[0].text.strip()
                lesson.content = content
                lesson.save(update_fields=['content'])
                updated += 1
                self.stdout.write(f'  OK')
                time.sleep(0.5)

            except Exception as e:
                self.stdout.write(f'  ERROR: {e}')
                errors += 1
                time.sleep(1)

        self.stdout.write(f'Done. Updated: {updated}, Errors: {errors}')
