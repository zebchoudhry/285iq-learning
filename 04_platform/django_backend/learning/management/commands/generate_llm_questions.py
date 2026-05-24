"""
Generate questions using LLM for Biology and Chemistry.
Requires LLM_BACKEND in settings/.env (openai_compatible or huggingface).

Usage:
  python manage.py generate_llm_questions --subject biology --per-topic 8
  python manage.py generate_llm_questions --subject chemistry --per-topic 8
  python manage.py generate_llm_questions --subjects biology,chemistry --per-topic 6
"""
from django.core.management.base import BaseCommand

from learning.models import Topic
from learning.services.llm_question_generator import generate_questions


class Command(BaseCommand):
    help = "Generate GCSE questions using LLM for Biology and/or Chemistry"

    def add_arguments(self, parser):
        parser.add_argument(
            "--subject",
            "-s",
            type=str,
            choices=["biology", "chemistry"],
            help="Single subject to generate for",
        )
        parser.add_argument(
            "--subjects",
            type=str,
            default=None,
            help="Comma-separated subjects (e.g. biology,chemistry). Overrides --subject.",
        )
        parser.add_argument(
            "--per-topic",
            "-n",
            type=int,
            default=8,
            help="Questions to generate per topic (default: 8)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show topics that would be processed without calling LLM",
        )

    def handle(self, *args, **options):
        subjects_arg = options.get("subjects")
        subject_arg = options.get("subject")
        per_topic = max(1, min(20, options.get("per_topic", 8)))
        dry_run = options.get("dry_run", False)

        if subjects_arg:
            subjects = [s.strip().lower() for s in subjects_arg.split(",") if s.strip()]
        elif subject_arg:
            subjects = [subject_arg.lower()]
        else:
            subjects = ["biology", "chemistry"]

        valid = {"biology", "chemistry"}
        subjects = [s for s in subjects if s in valid]
        if not subjects:
            self.stderr.write(self.style.ERROR("No valid subjects. Use biology and/or chemistry."))
            return

        topics = (
            Topic.objects.filter(
                subject__name__in=[s.capitalize() for s in subjects],
                subject__is_active=True,
                is_active=True,
            )
            .select_related("subject")
            .order_by("subject__name", "order")
        )

        topic_list = list(topics)
        if not topic_list:
            self.stderr.write(
                self.style.WARNING(
                    f"No topics found for {', '.join(subjects)}. Run seed_biology_subtopics and seed_chemistry_subtopics first."
                )
            )
            return

        if dry_run:
            self.stdout.write(self.style.SUCCESS(f"[DRY RUN] Would process {len(topic_list)} topics:"))
            for t in topic_list:
                self.stdout.write(f"  - {t.subject.display_name}: {t.name} (id={t.id})")
            return

        try:
            from django.conf import settings

            backend = getattr(settings, "LLM_BACKEND", "disabled") or "disabled"
            if backend.lower() in ("disabled", "none"):
                self.stderr.write(
                    self.style.ERROR(
                        "LLM is disabled. Add to .env — option A (OpenAI):\n"
                        "  LLM_BACKEND=openai_compatible\n"
                        "  LLM_BASE_URL=https://api.openai.com/v1\n"
                        "  LLM_MODEL=gpt-4o-mini\n"
                        "  LLM_API_KEY=sk-your-key\n"
                        "Option B (Hugging Face Inference):\n"
                        "  LLM_BACKEND=huggingface\n"
                        "  HF_TOKEN=hf_...\n"
                        "  HF_MODEL=Qwen/Qwen2.5-7B-Instruct"
                    )
                )
                return
        except Exception:
            pass

        self.stdout.write(
            self.style.SUCCESS(
                f"Generating {per_topic} questions per topic for {len(topic_list)} topics..."
            )
        )
        self.stdout.write("")

        total_created = 0
        errors = 0

        for topic in topic_list:
            label = f"{topic.subject.display_name} / {topic.name}"
            try:
                ids = generate_questions(
                    topic_id=topic.id,
                    mode="practice",
                    difficulty=2,
                    count=per_topic,
                )
                n = len(ids) if ids else 0
                total_created += n
                self.stdout.write(self.style.SUCCESS(f"  + {label}: {n} questions"))
            except RuntimeError as e:
                self.stderr.write(self.style.ERROR(f"  ! {label}: {e}"))
                errors += 1
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"  ! {label}: {e}"))
                errors += 1

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 50))
        self.stdout.write(self.style.SUCCESS(f"Total created: {total_created}"))
        if errors:
            self.stdout.write(self.style.WARNING(f"Errors: {errors}"))
        self.stdout.write("=" * 50)
