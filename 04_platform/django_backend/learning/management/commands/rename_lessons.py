import json
import time
import anthropic
from django.core.management.base import BaseCommand
from learning.models import Lesson


class Command(BaseCommand):
    help = 'Rename all lessons with proper descriptive titles using Claude API'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Print titles without saving')
        parser.add_argument('--subject', type=str, help='Filter by subject name e.g. mathematics')

    def handle(self, *args, **options):
        client = anthropic.Anthropic()

        lessons = Lesson.objects.select_related('topic__subject').filter(is_active=True)
        if options['subject']:
            lessons = lessons.filter(topic__subject__name__icontains=options['subject'])

        lessons = lessons.order_by('topic__subject__name', 'topic__order', 'order')
        total = lessons.count()
        self.stdout.write(f'Renaming {total} lessons...\n')

        # Group by topic to send in batches — saves API calls
        from itertools import groupby
        from django.db.models import Prefetch

        topics_seen = {}
        for lesson in lessons:
            topic_key = lesson.topic.id
            if topic_key not in topics_seen:
                topics_seen[topic_key] = {
                    'topic_name': lesson.topic.name,
                    'subject': lesson.topic.subject.name,
                    'lessons': []
                }
            topics_seen[topic_key]['lessons'].append(lesson)

        renamed = 0
        errors = 0

        for topic_id, topic_data in topics_seen.items():
            topic_name = topic_data['topic_name']
            subject = topic_data['subject']
            lesson_list = topic_data['lessons']
            count = len(lesson_list)

            self.stdout.write(f'  Topic: {subject} > {topic_name} ({count} lessons)...')

            prompt = f"""You are a GCSE {subject} curriculum expert.

For the topic "{topic_name}" in GCSE {subject}, generate exactly {count} short, descriptive lesson titles.
These should be specific, exam-relevant subtopics that a student would study within "{topic_name}".
Each title should be 2-6 words. Do not number them. Do not include the topic name in the title.

Respond ONLY with a JSON array of exactly {count} strings. No other text.
Example format: ["Place Value", "Rounding Numbers", "Powers of Ten"]"""

            try:
                message = client.messages.create(
                    model="claude-opus-4-6",
                    max_tokens=500,
                    messages=[{"role": "user", "content": prompt}]
                )
                raw = message.content[0].text.strip()
                # Strip markdown code fences if present
                if raw.startswith('```'):
                    raw = raw.split('```')[1]
                    if raw.startswith('json'):
                        raw = raw[4:]
                titles = json.loads(raw.strip())

                if len(titles) != count:
                    self.stdout.write(self.style.WARNING(f'    Got {len(titles)} titles, expected {count}. Skipping.'))
                    errors += 1
                    continue

                for lesson, new_title in zip(lesson_list, titles):
                    old_title = lesson.title
                    if options['dry_run']:
                        self.stdout.write(f'    [{old_title}] → [{new_title}]')
                    else:
                        lesson.title = new_title.strip()
                        lesson.save(update_fields=['title'])
                        renamed += 1

                # Rate limit — be polite to the API
                time.sleep(0.5)

            except json.JSONDecodeError as e:
                self.stdout.write(self.style.ERROR(f'    JSON parse error: {e}'))
                errors += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'    Error: {e}'))
                errors += 1

        self.stdout.write('\n')
        if options['dry_run']:
            self.stdout.write(self.style.SUCCESS(f'Dry run complete. {total} lessons would be renamed.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Done. {renamed} lessons renamed, {errors} errors.'))
