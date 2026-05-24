from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = 'Create sample mock exams from existing questions'

    def handle(self, *args, **kwargs):
        from dashboard.models import MockExam, MockExamQuestion
        from learning.models import Subject, Question

        try:
            from dashboard.models import ExamBoard
            exam_board = ExamBoard.objects.first()
        except Exception:
            exam_board = None

        if not exam_board:
            self.stdout.write(
                self.style.ERROR('No ExamBoard found. Create one in Django admin (Dashboard > Exam boards) first.')
            )
            return

        subjects = Subject.objects.filter(is_active=True)

        if not subjects.exists():
            self.stdout.write(self.style.ERROR('No subjects found. Add subjects first.'))
            return

        created_count = 0

        for subject in subjects:
            questions = Question.objects.filter(
                lesson__topic__subject=subject,
                is_active=True
            )[:20]

            if not questions.exists():
                self.stdout.write(f'  Skipping {subject.display_name} - no questions')
                continue

            total_marks = sum(q.marks_available for q in questions)

            mock_exam, created = MockExam.objects.get_or_create(
                title=f'Sample Mock - {subject.display_name}',
                defaults={
                    'subject': subject,
                    'exam_board': exam_board,
                    'time_allowed_minutes': 90,
                    'total_marks': total_marks,
                    'is_active': True,
                }
            )

            if not created:
                self.stdout.write(f'  Already exists: {mock_exam.title}')
                continue

            for order, question in enumerate(questions, start=1):
                MockExamQuestion.objects.create(
                    mock_exam=mock_exam,
                    question=question,
                    order=order,
                    marks=question.marks_available
                )

            created_count += 1
            self.stdout.write(self.style.SUCCESS(
                f'  Created: {mock_exam.title} ({questions.count()} questions, {total_marks} marks)'
            ))

        if created_count == 0:
            self.stdout.write(self.style.WARNING('No new mock exams created.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'\nDone! Created {created_count} mock exam(s).'))
            self.stdout.write('Run: python manage.py runserver')
            self.stdout.write('Then visit: http://127.0.0.1:8000/mock-tests/')

