"""
Bootstrap complete GCSE platform with subjects, topics, lessons, and questions.
Usage: python manage.py bootstrap_gcse

This command is idempotent and safe to run multiple times.
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
from learning.models import Subject, Topic, Lesson, Question
from learning.generators.base import resolve_lesson, create_question_from_dict
from pathlib import Path
import json


class Command(BaseCommand):
    help = "Bootstrap complete GCSE platform with subjects, topics, lessons, questions"
    
    SUBJECTS = {
        'mathematics': 'Mathematics',
        'biology': 'Biology',
        'chemistry': 'Chemistry',
        'physics': 'Physics',
    }
    
    TOPICS = {
        'mathematics': [
            'Number',
            'Algebra',
            'Ratio & Proportion',
            'Geometry & Measures',
            'Probability',
            'Statistics'
        ],
        'biology': [
            'Cell Biology',
            'Organisation',
            'Infection & Response',
            'Bioenergetics',
            'Homeostasis',
            'Inheritance & Evolution',
            'Ecology'
        ],
        'chemistry': [
            'Atomic Structure',
            'Bonding',
            'Quantitative Chemistry',
            'Chemical Changes',
            'Energy Changes',
            'Rates & Equilibrium',
            'Organic Chemistry'
        ],
        'physics': [
            'Energy',
            'Electricity',
            'Particle Model',
            'Atomic Structure',
            'Forces',
            'Waves',
            'Magnetism & Electromagnetism'
        ],
    }
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting GCSE Bootstrap..."))
        self.stdout.write("")
        
        subjects_created = self._create_subjects()
        topics_created = self._create_topics()
        lessons_created = self._create_lessons()
        questions_loaded = self._load_questions()
        
        self._print_summary(subjects_created, topics_created, lessons_created, questions_loaded)
    
    def _create_subjects(self):
        """Create all 4 GCSE subjects."""
        created = 0
        self.stdout.write("Creating subjects...")
        
        for subject_key, subject_name in self.SUBJECTS.items():
            subject, was_created = Subject.objects.get_or_create(
                name=subject_key,
                defaults={
                    'display_name': subject_name,
                    'is_active': True,
                }
            )
            if was_created:
                created += 1
                self.stdout.write(f"  + Created: {subject_name}")
            else:
                self.stdout.write(f"  - Exists: {subject_name}")
        
        self.stdout.write("")
        return created
    
    def _create_topics(self):
        """Create topics for each subject."""
        created = 0
        self.stdout.write("Creating topics...")
        
        for subject_key, topic_names in self.TOPICS.items():
            try:
                subject = Subject.objects.get(name=subject_key)
            except Subject.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"  ! Subject not found: {subject_key}"))
                continue
            
            for idx, topic_name in enumerate(topic_names):
                topic, was_created = Topic.objects.get_or_create(
                    subject=subject,
                    name=topic_name,
                    defaults={
                        'order': idx,
                        'is_active': True,
                    }
                )
                if was_created:
                    created += 1
                    self.stdout.write(f"  + Created: {subject.display_name} -> {topic_name}")
        
        self.stdout.write("")
        return created
    
    def _create_lessons(self):
        """Create 3 lessons for each topic."""
        created = 0
        self.stdout.write("Creating lessons...")
        
        topics = Topic.objects.filter(is_active=True).select_related('subject')
        
        for topic in topics:
            for i in range(1, 4):
                lesson_title = f"{topic.name} - Lesson {i}"
                lesson, was_created = Lesson.objects.get_or_create(
                    topic=topic,
                    title=lesson_title,
                    defaults={
                        'content': f'Learning materials for {topic.name}, Lesson {i}.',
                        'estimated_duration': 45,
                        'lesson_type': 'theory',
                        'difficulty_level': i,
                        'order': i - 1,
                        'is_active': True,
                    }
                )
                if was_created:
                    created += 1
        
        self.stdout.write(f"  + Created {created} new lessons")
        self.stdout.write("")
        return created
    
    def _load_questions(self):
        """Load questions from JSON files or create fallbacks."""
        total_loaded = 0
        self.stdout.write("Loading questions...")
        
        for subject_key, subject_name in self.SUBJECTS.items():
            # Count existing questions for this subject
            existing_count = Question.objects.filter(
                lesson__topic__subject__name=subject_key,
                is_active=True
            ).count()
            
            self.stdout.write(f"  {subject_name}: {existing_count} existing questions")
            
            if existing_count >= 300:
                self.stdout.write(f"    -> Sufficient questions, skipping")
                total_loaded += existing_count
                continue
            
            # Try to load from JSON file
            json_file = Path(__file__).parent.parent.parent.parent.parent / f"data/questions_{subject_key}.json"
            
            if json_file.exists():
                self.stdout.write(f"    -> Loading from {json_file.name}")
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    loaded = self._load_questions_from_data(data, subject_key)
                    self.stdout.write(f"    + Loaded {loaded} questions from JSON")
                    total_loaded += loaded
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"    ! Error loading JSON: {e}"))
            else:
                self.stdout.write(f"    -> JSON file not found: {json_file.name}")
            
            # Check if we still need more questions
            current_count = Question.objects.filter(
                lesson__topic__subject__name=subject_key,
                is_active=True
            ).count()
            
            if current_count < 300:
                self.stdout.write(f"    -> Creating fallback questions")
                try:
                    call_command('seed_fallback_question_bank', min_per_topic=10, verbosity=0)
                    fallback_count = Question.objects.filter(
                        lesson__topic__subject__name=subject_key,
                        is_active=True
                    ).count()
                    added = fallback_count - current_count
                    self.stdout.write(f"    + Added {added} fallback questions")
                    total_loaded += added
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"    ! Error creating fallbacks: {e}"))
        
        self.stdout.write("")
        return total_loaded
    
    def _load_questions_from_data(self, data, subject_key):
        """Load questions from parsed JSON data."""
        loaded = 0
        
        # Normalize data structure
        if isinstance(data, dict):
            if "questions" in data:
                blocks = [data]
            else:
                blocks = []
        elif isinstance(data, list):
            blocks = data
        else:
            return 0
        
        for block in blocks:
            if not isinstance(block, dict) or "questions" not in block:
                continue
            
            subject_name = str(block.get("subject") or block.get("Subject") or "").strip()
            topic_name = str(block.get("topic") or block.get("Topic") or "").strip()
            lesson_title = str(block.get("lesson") or block.get("Lesson") or "").strip()
            questions = block.get("questions", [])
            
            if not (subject_name and topic_name and lesson_title and questions):
                continue
            
            # Resolve lesson
            subject_obj, topic_obj, lesson_obj = resolve_lesson(subject_name, topic_name, lesson_title)
            
            if not lesson_obj:
                continue
            
            # Load questions
            for q_data in questions:
                if not isinstance(q_data, dict):
                    continue
                
                q_obj, was_created = create_question_from_dict(lesson_obj, q_data, skip_duplicates=True)
                if was_created:
                    loaded += 1
        
        return loaded
    
    def _print_summary(self, subjects_created, topics_created, lessons_created, questions_total):
        """Print final summary."""
        subject_count = Subject.objects.count()
        topic_count = Topic.objects.filter(is_active=True).count()
        lesson_count = Lesson.objects.filter(is_active=True).count()
        question_count = Question.objects.filter(is_active=True).count()
        
        # Check if system is ready
        system_ready = (
            subject_count >= 4 and
            topic_count >= 20 and
            lesson_count >= 60 and
            question_count >= 100
        )
        
        self.stdout.write("=" * 40)
        self.stdout.write(self.style.SUCCESS("GCSE Bootstrap Complete"))
        self.stdout.write("=" * 40)
        self.stdout.write(f"Subjects: {subject_count} ({subjects_created} new)")
        self.stdout.write(f"Topics: {topic_count} ({topics_created} new)")
        self.stdout.write(f"Lessons: {lesson_count} ({lessons_created} new)")
        self.stdout.write(f"Questions: {question_count}")
        self.stdout.write(f"System Ready: {'YES' if system_ready else 'NO'}")
        self.stdout.write("=" * 40)
        self.stdout.write("")
        self.stdout.write(self.style.WARNING("PARENT DASHBOARD ACCESS"))
        self.stdout.write("")
        self.stdout.write("Share parent dashboard links with parents:")
        self.stdout.write("Format: /parent/<parent_access_token>/")
        self.stdout.write("")
        self.stdout.write("Example links for existing students:")
        from users.models import Student
        for student in Student.objects.all()[:3]:
            token = student.parent_access_token
            self.stdout.write(f"  {student.username}: /parent/{token}/")
        self.stdout.write("")
        self.stdout.write("View all tokens in Django admin (Student model)")
        self.stdout.write("=" * 40)
