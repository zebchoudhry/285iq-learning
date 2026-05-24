"""
Unified command to seed practice questions for all subjects.
Usage: python manage.py seed_all_questions [--per-lesson 10] [--subjects physics,chemistry,biology,mathematics] [--dry-run]
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = "Generate and load practice questions for all subjects (or specified subjects)"
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--per-lesson',
            '-n',
            type=int,
            default=10,
            help='Number of questions to generate per lesson (default: 10)'
        )
        parser.add_argument(
            '--subjects',
            '-s',
            type=str,
            default='physics,chemistry,biology,mathematics',
            help='Comma-separated list of subjects (default: all)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Report what would be generated without creating records'
        )
    
    def handle(self, *args, **options):
        per_lesson = options['per_lesson']
        subjects_str = options['subjects']
        dry_run = options['dry_run']
        
        subjects = [s.strip().lower() for s in subjects_str.split(',') if s.strip()]
        valid_subjects = ['physics', 'chemistry', 'biology', 'mathematics']
        subjects = [s for s in subjects if s in valid_subjects]
        
        if not subjects:
            self.stderr.write(self.style.ERROR('No valid subjects specified'))
            return
        
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('SEEDING PRACTICE QUESTIONS'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write('')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('[DRY RUN MODE]'))
            self.stdout.write('')
        
        total_created = 0
        total_skipped = 0
        
        for subject in subjects:
            self.stdout.write(self.style.SUCCESS(f'Processing: {subject.title()}'))
            self.stdout.write('-' * 60)
            
            try:
                # Call generate_questions for each subject
                call_command(
                    'generate_questions',
                    subject=subject,
                    per_lesson=per_lesson,
                    dry_run=dry_run,
                    stdout=self.stdout,
                    stderr=self.stderr
                )
                self.stdout.write('')
            except Exception as e:
                self.stderr.write(self.style.ERROR(f'Error processing {subject}: {e}'))
                self.stdout.write('')
        
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('ALL SUBJECTS PROCESSED'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write('')
        
        if not dry_run:
            self.stdout.write('Run the server and check practice questions for each lesson.')
        else:
            self.stdout.write('[DRY RUN] No records were created.')
