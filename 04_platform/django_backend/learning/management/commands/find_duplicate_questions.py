"""
Find semantically similar Question pairs (near-duplicates) using sentence embeddings.

Requires HF_EMBEDDINGS_ENABLED=true and sentence-transformers installed.

Usage:
  python manage.py find_duplicate_questions --dry-run
  python manage.py find_duplicate_questions --subject mathematics --threshold 0.92
  python manage.py find_duplicate_questions --topic-id 42 --limit 500
"""
from django.core.management.base import BaseCommand, CommandError

from learning.models import Question
from learning.services.question_similarity import (
    EmbeddingsNotAvailable,
    embeddings_available,
    find_near_duplicate_pairs,
)


class Command(BaseCommand):
    help = "Report near-duplicate questions using Hugging Face sentence embeddings"

    def add_arguments(self, parser):
        parser.add_argument(
            "--subject",
            "-s",
            type=str,
            help="Filter by subject name (e.g. mathematics, biology)",
        )
        parser.add_argument(
            "--topic-id",
            type=int,
            help="Filter by topic ID",
        )
        parser.add_argument(
            "--threshold",
            type=float,
            default=0.92,
            help="Cosine similarity threshold (default: 0.92)",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=2000,
            help="Max questions to scan (default: 2000)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Only show how many questions would be scanned",
        )

    def handle(self, *args, **options):
        dry_run = options.get("dry_run", False)
        if not dry_run and not embeddings_available():
            raise CommandError(
                "Embeddings not available. Set HF_EMBEDDINGS_ENABLED=true in .env and run:\n"
                "  pip install sentence-transformers"
            )

        qs = Question.objects.filter(is_active=True).select_related(
            "lesson__topic__subject"
        )
        if options.get("subject"):
            qs = qs.filter(lesson__topic__subject__name__iexact=options["subject"])
        if options.get("topic_id"):
            qs = qs.filter(lesson__topic_id=options["topic_id"])

        limit = max(2, options.get("limit") or 2000)
        questions = list(qs.order_by("id")[:limit])

        if dry_run:
            emb_note = "embeddings ready" if embeddings_available() else "enable HF_EMBEDDINGS_ENABLED + sentence-transformers"
            self.stdout.write(
                self.style.SUCCESS(
                    f"[DRY RUN] Would scan {len(questions)} questions "
                    f"(threshold={options['threshold']}, {emb_note})"
                )
            )
            return

        if len(questions) < 2:
            self.stdout.write(self.style.WARNING("Fewer than 2 questions to compare."))
            return

        self.stdout.write(f"Embedding {len(questions)} questions...")

        try:
            pairs = find_near_duplicate_pairs(
                ((q.id, q.question_text) for q in questions),
                threshold=options["threshold"],
            )
        except EmbeddingsNotAvailable as exc:
            raise CommandError(str(exc)) from exc

        if not pairs:
            self.stdout.write(self.style.SUCCESS("No near-duplicates found at this threshold."))
            return

        by_id = {q.id: q for q in questions}
        self.stdout.write(
            self.style.WARNING(f"Found {len(pairs)} similar pair(s):\n")
        )
        for id_a, id_b, score in pairs[:100]:
            qa = by_id.get(id_a)
            qb = by_id.get(id_b)
            subj = ""
            if qa and qa.lesson and qa.lesson.topic:
                subj = qa.lesson.topic.subject.display_name
            self.stdout.write(f"  score={score}  ids={id_a},{id_b}  ({subj})")
            self.stdout.write(f"    A: {(qa.question_text if qa else '')[:120]}")
            self.stdout.write(f"    B: {(qb.question_text if qb else '')[:120]}")
            self.stdout.write("")

        if len(pairs) > 100:
            self.stdout.write(f"  ... and {len(pairs) - 100} more pairs")
