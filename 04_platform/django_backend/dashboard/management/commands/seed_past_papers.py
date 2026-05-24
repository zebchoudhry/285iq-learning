"""
Seed link-based past papers for active exam boards and subjects.
Usage: python manage.py seed_past_papers
"""
from django.core.management.base import BaseCommand

from dashboard.models import ExamBoard, PastPaper
from learning.models import Subject


class Command(BaseCommand):
    help = "Seed starter past paper links (AQA/Edexcel) for active subjects"

    def handle(self, *args, **options):
        subjects = Subject.objects.filter(is_active=True)
        if not subjects.exists():
            self.stdout.write(self.style.WARNING("No active subjects found."))
            return

        board_codes = ["AQA", "EDEXCEL"]
        boards = list(ExamBoard.objects.filter(code__in=board_codes, is_active=True))
        if not boards:
            self.stdout.write(self.style.WARNING("No active exam boards found (expected AQA/EDEXCEL)."))
            return

        created = 0
        for subject in subjects:
            for board in boards:
                for year in (2024, 2023):
                    title = f"{board.code} {subject.display_name} Paper 1 - {year}"
                    url = self._build_source_url(board.code, subject.name, year)
                    _, was_created = PastPaper.objects.get_or_create(
                        subject=subject,
                        exam_board=board,
                        year=year,
                        paper_number=1,
                        defaults={
                            "title": title,
                            "source_url": url,
                            "is_active": True,
                        },
                    )
                    if was_created:
                        created += 1
        self.stdout.write(self.style.SUCCESS(f"Done. Created {created} past paper link(s)."))

    def _build_source_url(self, board_code, subject_name, year):
        slug = (subject_name or "subject").lower().replace(" ", "-")
        if board_code == "AQA":
            return f"https://www.aqa.org.uk/subjects/{slug}/gcse/past-papers-and-mark-schemes"
        if board_code == "EDEXCEL":
            return f"https://qualifications.pearson.com/en/qualifications/edexcel-gcses/{slug}-2015.coursematerials.html"
        return "https://www.gov.uk"
