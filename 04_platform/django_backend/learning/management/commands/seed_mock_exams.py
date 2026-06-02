"""
Management command: seed_mock_exams

Creates MockExam + MockExamQuestion records for 6 years (2019-2024) x all active
subjects x Paper 1 and Paper 2. Also seeds PastPaper link records.

Idempotent: safe to run multiple times (uses get_or_create).
"""
import math

from django.core.management.base import BaseCommand

from dashboard.models import ExamBoard, MockExam, MockExamQuestion, PastPaper
from learning.models import Question, Subject, Topic


YEARS = [2019, 2020, 2021, 2022, 2023, 2024]
PAPER_NUMBERS = [1, 2]
QUESTIONS_PER_PAPER = 25


class Command(BaseCommand):
    help = "Seed MockExam and MockExamQuestion records for AQA subjects (2019-2024)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="Print what would be created without saving to the database.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN mode - nothing will be saved."))

        # 1. Get or create AQA ExamBoard
        board = ExamBoard.objects.filter(code="AQA").first()
        if board is None:
            if not dry_run:
                board = ExamBoard.objects.create(
                    code="AQA",
                    name="Assessment and Qualifications Alliance",
                    is_active=True,
                )
                self.stdout.write(f"Created ExamBoard: {board.code}")
            else:
                self.stdout.write("Would create ExamBoard: AQA")
                board = ExamBoard(code="AQA", name="Assessment and Qualifications Alliance")
                board.id = 0  # fake id for dry-run
        else:
            self.stdout.write(f"Found existing ExamBoard: {board.code}")

        # 2. Get active subjects with at least 5 active questions
        active_subjects = []
        for subject in Subject.objects.filter(is_active=True):
            q_count = Question.objects.filter(
                lesson__topic__subject=subject,
                is_active=True,
            ).count()
            if q_count >= 5:
                active_subjects.append(subject)

        self.stdout.write(
            f"Found {len(active_subjects)} active subjects with >= 5 questions."
        )

        exams_created = 0
        exam_questions_created = 0
        past_papers_created = 0

        for subject in active_subjects:
            # Get topics ordered by topic.order
            topics = list(
                Topic.objects.filter(subject=subject, is_active=True).order_by("order")
            )
            if not topics:
                topics = list(Topic.objects.filter(subject=subject).order_by("order"))

            # All active questions for subject
            all_questions = list(
                Question.objects.filter(
                    lesson__topic__subject=subject,
                    is_active=True,
                ).select_related("lesson__topic")
            )

            for year in YEARS:
                used_question_ids = set()  # track used within this year across papers

                for paper_number in PAPER_NUMBERS:
                    # Build title
                    title = (
                        f"{board.code} {subject.display_name} "
                        f"Paper {paper_number} – {year}"
                    )

                    if not dry_run:
                        mock_exam, created = MockExam.objects.get_or_create(
                            subject=subject,
                            exam_board=board,
                            source_year=year,
                            paper_number=paper_number,
                            tier="higher",
                            defaults={
                                "title": title,
                                "total_marks": 80,
                                "time_allowed_minutes": 90,
                                "calculator_allowed": paper_number == 2,
                                "source_series": "June",
                                "is_active": True,
                            },
                        )
                        if created:
                            exams_created += 1
                    else:
                        mock_exam = None
                        created = True
                        exams_created += 1

                    # Select questions for this paper
                    selected = self._select_questions(
                        all_questions=all_questions,
                        topics=topics,
                        paper_number=paper_number,
                        used_question_ids=used_question_ids,
                        limit=QUESTIONS_PER_PAPER,
                    )

                    # Mark these questions as used for this year
                    used_question_ids.update(q.id for q in selected)

                    # Sort by difficulty ASC
                    selected.sort(key=lambda q: q.difficulty_level)

                    if not dry_run and mock_exam is not None:
                        for idx, question in enumerate(selected):
                            meq, meq_created = MockExamQuestion.objects.get_or_create(
                                mock_exam=mock_exam,
                                question=question,
                                defaults={
                                    "order": idx,
                                    "marks": question.marks_available,
                                },
                            )
                            if meq_created:
                                exam_questions_created += 1
                    else:
                        exam_questions_created += len(selected)

                    if dry_run:
                        self.stdout.write(
                            f"  [DRY RUN] Would create MockExam: {title} "
                            f"({len(selected)} questions)"
                        )

                    # Seed PastPaper link
                    subject_slug = subject.name.lower().replace(" ", "-")
                    source_url = (
                        f"https://www.aqa.org.uk/subjects/{subject_slug}/gcse/"
                        f"past-papers-and-mark-schemes"
                    )
                    pp_title = (
                        f"AQA {subject.display_name} {year} Paper {paper_number}"
                    )
                    if not dry_run:
                        _, pp_created = PastPaper.objects.get_or_create(
                            subject=subject,
                            exam_board=board,
                            year=year,
                            paper_number=paper_number,
                            defaults={
                                "title": pp_title,
                                "source_url": source_url,
                                "is_active": True,
                            },
                        )
                        if pp_created:
                            past_papers_created += 1
                    else:
                        past_papers_created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Created {exams_created} mock exams, "
                f"{exam_questions_created} mock exam questions, "
                f"{past_papers_created} past paper links."
            )
        )

    def _select_questions(self, all_questions, topics, paper_number, used_question_ids, limit):
        """
        Topic-weighted selection: pick ceil(limit / num_topics) questions per topic.
        Paper 1 prefers difficulty_level <= 3; Paper 2 prefers difficulty_level >= 2.
        Excludes questions already used in other papers for the same year.
        """
        if not topics:
            # Fallback: just pick the first N questions not yet used
            available = [q for q in all_questions if q.id not in used_question_ids]
            return available[:limit]

        per_topic = math.ceil(limit / len(topics))
        selected = []
        selected_ids = set()

        for topic in topics:
            if len(selected) >= limit:
                break

            # Questions for this topic not yet used
            topic_qs = [
                q for q in all_questions
                if q.lesson.topic_id == topic.id
                and q.id not in used_question_ids
                and q.id not in selected_ids
            ]

            if paper_number == 1:
                preferred = [q for q in topic_qs if q.difficulty_level <= 3]
                fallback = [q for q in topic_qs if q.difficulty_level > 3]
            else:
                preferred = [q for q in topic_qs if q.difficulty_level >= 2]
                fallback = [q for q in topic_qs if q.difficulty_level < 2]

            pool = preferred + fallback
            take = min(per_topic, limit - len(selected))
            batch = pool[:take]
            selected.extend(batch)
            selected_ids.update(q.id for q in batch)

        return selected
