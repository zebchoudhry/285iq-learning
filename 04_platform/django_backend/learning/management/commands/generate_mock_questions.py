"""
Management command: generate_mock_questions

Uses the LLM service to generate original past-paper-style GCSE questions for each
topic, then seeds them as real Question records (source="llm_mock_gen") and adds them
to mock exams.

Usage:
    python manage.py generate_mock_questions --subject-name "Mathematics"
    python manage.py generate_mock_questions --subject-name "Physics" --questions-per-topic 5
    python manage.py generate_mock_questions --subject-name "Biology" --dry-run
"""
import json

from django.core.management.base import BaseCommand, CommandError

from dashboard.models import MockExam, MockExamQuestion
from learning.models import Lesson, Question, Subject, Topic


class Command(BaseCommand):
    help = "Generate LLM past-paper-style GCSE questions per topic and seed them."

    def add_arguments(self, parser):
        parser.add_argument(
            "--subject-name",
            type=str,
            required=True,
            help='Subject display_name, e.g. "Mathematics"',
        )
        parser.add_argument(
            "--questions-per-topic",
            type=int,
            default=8,
            help="Number of questions to generate per topic (default: 8)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="Print what would be created without saving to the database.",
        )

    def handle(self, *args, **options):
        subject_name = options["subject_name"]
        questions_per_topic = options["questions_per_topic"]
        dry_run = options["dry_run"]

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN mode - nothing will be saved."))

        # 1. Get subject by display_name
        subject = Subject.objects.filter(display_name__icontains=subject_name, is_active=True).first()
        if subject is None:
            raise CommandError(f"Subject with display_name containing '{subject_name}' not found.")

        self.stdout.write(f"Subject: {subject.display_name}")

        topics = list(
            Topic.objects.filter(subject=subject, is_active=True).order_by("order")
        )
        self.stdout.write(f"Found {len(topics)} active topics.")

        questions_created = 0
        mock_links_created = 0

        for topic in topics:
            self.stdout.write(f"  Topic: {topic.name}")

            # Check if LLM is available
            try:
                from django.conf import settings
                backend = (getattr(settings, "LLM_BACKEND", "disabled") or "disabled").lower()
                if backend in ("disabled", "none"):
                    self.stdout.write(
                        self.style.WARNING(
                            f"    Skipping '{topic.name}' - LLM backend is disabled."
                        )
                    )
                    continue
            except Exception:
                self.stdout.write(
                    self.style.WARNING(f"    Skipping '{topic.name}' - cannot check LLM backend.")
                )
                continue

            # Build prompt
            prompt = (
                f"You are an AQA GCSE {subject.display_name} examiner. "
                f"Generate {questions_per_topic} original exam-style questions for the topic "
                f'"{topic.name}".\n\n'
                "Requirements:\n"
                "- Mix of question types: short_answer (1-2 marks), calculation (2-4 marks), extended (3-6 marks)\n"
                "- Match AQA GCSE style and difficulty\n"
                "- Each question must have a clear model answer / mark scheme\n"
                "- Cover different aspects of the topic\n\n"
                "Return ONLY a JSON array. Each element:\n"
                '{"question_text": "...", "correct_answer": "...", '
                '"question_type": "short_answer|calculation|extended", '
                '"marks_available": int, "difficulty_level": int (1-5)}\n\n'
                'Example element: {"question_text": "Calculate the speed of a wave with frequency '
                '50 Hz and wavelength 2 m.", "correct_answer": "speed = frequency × wavelength '
                '= 50 × 2 = 100 m/s", "question_type": "calculation", "marks_available": 2, '
                '"difficulty_level": 2}'
            )

            # Call LLM
            try:
                from learning.services.llm_service import generate as llm_generate
                response = llm_generate(prompt, max_tokens=1500, temperature=0.6)
            except RuntimeError as e:
                self.stdout.write(
                    self.style.WARNING(f"    Skipping '{topic.name}' - LLM error: {e}")
                )
                continue
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"    Error calling LLM for '{topic.name}': {e}")
                )
                continue

            # Parse JSON from response
            parsed_questions = self._parse_json_array(response)
            if parsed_questions is None:
                self.stdout.write(
                    self.style.WARNING(
                        f"    Could not parse JSON from LLM response for '{topic.name}'. Skipping."
                    )
                )
                continue

            self.stdout.write(f"    Parsed {len(parsed_questions)} questions from LLM.")

            for q_data in parsed_questions:
                question_text = q_data.get("question_text", "").strip()
                correct_answer = q_data.get("correct_answer", "").strip()
                question_type = q_data.get("question_type", "short_answer")
                marks_available = int(q_data.get("marks_available", 1))
                difficulty_level = int(q_data.get("difficulty_level", 2))

                if not question_text or not correct_answer:
                    continue

                # Validate question_type
                valid_types = {"short_answer", "multiple_choice", "calculation", "extended"}
                if question_type not in valid_types:
                    question_type = "short_answer"

                # Get or create a Lesson for the topic
                lesson = self._get_or_create_lesson(topic, dry_run)
                if lesson is None:
                    continue

                if dry_run:
                    self.stdout.write(
                        f"    [DRY RUN] Would create Question: {question_text[:60]}..."
                    )
                    questions_created += 1
                    continue

                # Check if question already exists for this lesson
                if Question.objects.filter(
                    lesson=lesson,
                    question_text=question_text,
                ).exists():
                    self.stdout.write(f"    Skipping duplicate question: {question_text[:60]}...")
                    continue

                question = Question.objects.create(
                    lesson=lesson,
                    question_text=question_text,
                    correct_answer=correct_answer,
                    question_type=question_type,
                    marks_available=marks_available,
                    difficulty_level=difficulty_level,
                    explanation=correct_answer,
                    source="llm_mock_gen",
                    is_active=True,
                )
                questions_created += 1

                # Add to mock exams for this subject (up to 5 that need more questions)
                mock_exams = MockExam.objects.filter(
                    subject=subject,
                    is_active=True,
                ).order_by("source_year", "paper_number")[:5]

                for mock_exam in mock_exams:
                    if MockExamQuestion.objects.filter(
                        mock_exam=mock_exam,
                        question=question,
                    ).exists():
                        continue

                    order = MockExamQuestion.objects.filter(mock_exam=mock_exam).count()
                    MockExamQuestion.objects.create(
                        mock_exam=mock_exam,
                        question=question,
                        order=order,
                        marks=question.marks_available,
                    )
                    mock_links_created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Generated {questions_created} questions, "
                f"added {mock_links_created} mock exam question links."
            )
        )

    def _get_or_create_lesson(self, topic, dry_run):
        """Return the first existing lesson for the topic, or create a placeholder."""
        lesson = Lesson.objects.filter(topic=topic, is_active=True).first()
        if lesson:
            return lesson

        if dry_run:
            return Lesson(
                topic=topic,
                title=f"LLM Generated - {topic.name}",
                content="Auto-generated lesson for LLM questions.",
            )

        lesson = Lesson.objects.create(
            topic=topic,
            title=f"LLM Generated - {topic.name}",
            content="Auto-generated lesson for LLM questions.",
            lesson_type="practice",
            is_active=True,
        )
        return lesson

    def _parse_json_array(self, text):
        """Strip code fences and extract JSON array from LLM response."""
        # Strip markdown code fences
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            # Remove first and last fence lines
            text = "\n".join(lines[1:])
            if text.rstrip().endswith("```"):
                text = "\n".join(text.rstrip().split("\n")[:-1])

        # Find the first [ and last ]
        start = text.find("[")
        end = text.rfind("]")
        if start == -1 or end == -1:
            return None

        json_str = text[start : end + 1]
        try:
            data = json.loads(json_str)
            if isinstance(data, list):
                return data
        except json.JSONDecodeError:
            pass

        return None
