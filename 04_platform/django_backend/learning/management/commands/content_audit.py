from collections import defaultdict

from django.core.management.base import BaseCommand
from django.db.models import Count, Q

from dashboard.models import MockExam, PastPaper
from learning.models import Flashcard, Lesson, Question, SkillVideo, Subject, Topic


class Command(BaseCommand):
    help = "Report GCSE content coverage by subject and topic."

    def add_arguments(self, parser):
        parser.add_argument(
            "--min-questions",
            type=int,
            default=20,
            help="Minimum active questions expected per lesson before a lesson is flagged.",
        )
        parser.add_argument(
            "--min-flashcards",
            type=int,
            default=5,
            help="Minimum active flashcards expected per topic before a topic is flagged.",
        )
        parser.add_argument(
            "--min-videos",
            type=int,
            default=1,
            help="Minimum active skill videos expected per topic before a topic is flagged.",
        )

    def handle(self, *args, **options):
        min_questions = options["min_questions"]
        min_flashcards = options["min_flashcards"]
        min_videos = options["min_videos"]

        subjects = Subject.objects.filter(is_active=True).order_by("display_name")
        if not subjects.exists():
            self.stdout.write(self.style.WARNING("No active subjects found."))
            return

        totals = {
            "subjects": subjects.count(),
            "topics": Topic.objects.filter(subject__in=subjects, is_active=True).count(),
            "lessons": Lesson.objects.filter(topic__subject__in=subjects, is_active=True).count(),
            "questions": Question.objects.filter(
                lesson__topic__subject__in=subjects,
                is_active=True,
            ).count(),
            "flashcards": Flashcard.objects.filter(
                topic__subject__in=subjects,
                is_active=True,
            ).count(),
            "videos": SkillVideo.objects.filter(
                Q(subject__in=subjects) | Q(topic__subject__in=subjects),
                is_active=True,
            ).distinct().count(),
            "mock_exams": MockExam.objects.filter(subject__in=subjects, is_active=True).count(),
            "past_papers": PastPaper.objects.filter(subject__in=subjects, is_active=True).count(),
        }

        self.stdout.write(self.style.SUCCESS("Content audit"))
        self.stdout.write(
            "Totals: "
            f"{totals['subjects']} subjects, {totals['topics']} topics, "
            f"{totals['lessons']} lessons, {totals['questions']} questions, "
            f"{totals['flashcards']} flashcards, {totals['videos']} videos, "
            f"{totals['mock_exams']} mock exams, {totals['past_papers']} past paper links"
        )
        self.stdout.write("")

        blockers = defaultdict(list)
        for subject in subjects:
            lessons = Lesson.objects.filter(topic__subject=subject, is_active=True)
            questions = Question.objects.filter(lesson__topic__subject=subject, is_active=True)
            flashcards = Flashcard.objects.filter(topic__subject=subject, is_active=True)
            videos = SkillVideo.objects.filter(
                Q(subject=subject) | Q(topic__subject=subject),
                is_active=True,
            ).distinct()
            mock_exams = MockExam.objects.filter(subject=subject, is_active=True)
            past_papers = PastPaper.objects.filter(subject=subject, is_active=True)

            self.stdout.write(self.style.MIGRATE_HEADING(subject.display_name))
            self.stdout.write(
                f"  Topics: {subject.topics.filter(is_active=True).count()} | "
                f"Lessons: {lessons.count()} | Questions: {questions.count()} | "
                f"Flashcards: {flashcards.count()} | Videos: {videos.count()} | "
                f"Mock exams: {mock_exams.count()} | Past papers: {past_papers.count()}"
            )

            if not mock_exams.exists():
                blockers[subject.display_name].append("no timed mock exam")
            if not past_papers.exists():
                blockers[subject.display_name].append("no past paper links")

            topic_rows = (
                Topic.objects.filter(subject=subject, is_active=True)
                .annotate(
                    lesson_count=Count("lessons", filter=Q(lessons__is_active=True), distinct=True),
                    question_count=Count(
                        "lessons__questions",
                        filter=Q(lessons__questions__is_active=True),
                        distinct=True,
                    ),
                    flashcard_count=Count(
                        "flashcards",
                        filter=Q(flashcards__is_active=True),
                        distinct=True,
                    ),
                    video_count=Count(
                        "skill_videos",
                        filter=Q(skill_videos__is_active=True),
                        distinct=True,
                    ),
                )
                .order_by("order", "name")
            )

            for topic in topic_rows:
                topic_flags = []
                if topic.lesson_count == 0:
                    topic_flags.append("no lessons")
                if topic.flashcard_count < min_flashcards:
                    topic_flags.append(f"flashcards {topic.flashcard_count}/{min_flashcards}")
                if topic.video_count < min_videos:
                    topic_flags.append(f"videos {topic.video_count}/{min_videos}")
                if topic.lesson_count and topic.question_count < topic.lesson_count * min_questions:
                    topic_flags.append(
                        f"questions {topic.question_count}/{topic.lesson_count * min_questions}"
                    )
                if topic_flags:
                    blockers[subject.display_name].append(f"{topic.name}: {', '.join(topic_flags)}")
                    self.stdout.write(
                        self.style.WARNING(
                            f"  - {topic.name}: {topic.lesson_count} lessons, "
                            f"{topic.question_count} questions, {topic.flashcard_count} flashcards, "
                            f"{topic.video_count} videos"
                        )
                    )
            self.stdout.write("")

        if not blockers:
            self.stdout.write(self.style.SUCCESS("No content coverage blockers found."))
            return

        self.stdout.write(self.style.WARNING("Priority content gaps"))
        for subject_name, items in blockers.items():
            self.stdout.write(f"{subject_name}:")
            for item in items[:12]:
                self.stdout.write(f"  - {item}")
            if len(items) > 12:
                self.stdout.write(f"  - ...and {len(items) - 12} more")
