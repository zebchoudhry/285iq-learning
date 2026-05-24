"""
Seed UK GCSE Exam Boards (AQA, Edexcel, OCR, WJEC).
"""
from django.core.management.base import BaseCommand

from dashboard.models import ExamBoard

# Standard GCSE grade boundaries (percentage for each grade 9-1)
DEFAULT_BOUNDARIES = {
    "mathematics_higher": {
        "9": 85, "8": 75, "7": 65, "6": 55, "5": 45,
        "4": 35, "3": 25, "2": 15, "1": 5,
    },
    "physics_higher": {
        "9": 84, "8": 73, "7": 62, "6": 51, "5": 40,
        "4": 30, "3": 20, "2": 10, "1": 5,
    },
    "biology_higher": {
        "9": 85, "8": 74, "7": 63, "6": 52, "5": 41,
        "4": 31, "3": 21, "2": 11, "1": 5,
    },
    "chemistry_higher": {
        "9": 84, "8": 73, "7": 62, "6": 51, "5": 40,
        "4": 30, "3": 20, "2": 10, "1": 5,
    },
}

EXAM_BOARDS = [
    {
        "code": "AQA",
        "name": "Assessment and Qualifications Alliance",
        "popularity_percentage": 52,
        "website": "https://www.aqa.org.uk",
    },
    {
        "code": "EDEXCEL",
        "name": "Pearson Edexcel",
        "popularity_percentage": 28,
        "website": "https://qualifications.pearson.com",
    },
    {
        "code": "OCR",
        "name": "Oxford Cambridge and RSA Examinations",
        "popularity_percentage": 15,
        "website": "https://www.ocr.org.uk",
    },
    {
        "code": "WJEC",
        "name": "Welsh Joint Education Committee",
        "popularity_percentage": 5,
        "website": "https://www.wjec.co.uk",
    },
]


class Command(BaseCommand):
    help = "Create UK GCSE exam boards (AQA, Edexcel, OCR, WJEC)"

    def handle(self, *args, **options):
        created = 0
        for data in EXAM_BOARDS:
            _, was_created = ExamBoard.objects.get_or_create(
                code=data["code"],
                defaults={
                    "name": data["name"],
                    "popularity_percentage": data["popularity_percentage"],
                    "website": data.get("website", ""),
                    "grade_boundaries": DEFAULT_BOUNDARIES,
                    "paper_structure": {},
                    "is_active": True,
                },
            )
            if was_created:
                created += 1
                self.stdout.write(self.style.SUCCESS(f"[OK] Created: {data['code']}"))
            else:
                self.stdout.write(f"[OK] Already exists: {data['code']}")
        self.stdout.write(self.style.SUCCESS(f"\nDone. Created {created} exam board(s)."))
