"""
IMPORT EXTRACTED QUESTIONS TO DATABASE
Imports questions from JSON file into your 285IQ database
"""

import os
import sys
import django
import json
from pathlib import Path

# Setup Django
sys.path.insert(0, 'C:/Users/zeb/Desktop/285iq_learning/04_platform/django_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'studymate285.settings')
django.setup()

from learning.models import Subject, Topic, Lesson, Question

# JSON file from extraction
JSON_FILE = 'extracted_maths_questions.json'

print("\n" + "="*70)
print("📥 IMPORTING QUESTIONS TO DATABASE")
print("="*70)

# Check if file exists
if not Path(JSON_FILE).exists():
    print(f"\n❌ File not found: {JSON_FILE}")
    print("\nRun the extraction script first:")
    print("  python run_extraction.py")
    sys.exit(1)

# Load questions
print(f"\n📖 Loading questions from: {JSON_FILE}")
with open(JSON_FILE, 'r', encoding='utf-8') as f:
    questions_data = json.load(f)

print(f"✅ Loaded {len(questions_data)} questions")

# Get or create Mathematics subject
print(f"\n🔍 Setting up database structure...")
maths, created = Subject.objects.get_or_create(
    name='mathematics',
    defaults={'display_name': 'GCSE Maths'}
)

if created:
    print(f"   Created Mathematics subject")
else:
    print(f"   Using existing Mathematics subject")

# Group questions by page (use as topics/lessons)
questions_by_page = {}
for q in questions_data:
    page = q.get('page', 1)
    if page not in questions_by_page:
        questions_by_page[page] = []
    questions_by_page[page].append(q)

print(f"\n📚 Questions span {len(questions_by_page)} pages")

# Import questions
print(f"\n📥 Importing to database...")
imported_count = 0
skipped_count = 0

for page_num, page_questions in sorted(questions_by_page.items()):
    # Create topic for every 10 pages (chapter equivalent)
    chapter = (page_num - 1) // 10 + 1
    
    topic, _ = Topic.objects.get_or_create(
        subject=maths,
        name=f"Chapter {chapter}",
        defaults={'order': chapter, 'is_active': True}
    )
    
    # Create lesson for this page
    lesson, _ = Lesson.objects.get_or_create(
        topic=topic,
        title=f"Practice Questions - Page {page_num}",
        defaults={
            'content': f"Questions from textbook page {page_num}",
            'estimated_duration': len(page_questions) * 2,  # 2 min per question
            'order': page_num
        }
    )
    
    # Import each question
    for q_data in page_questions:
        try:
            # Check if question already exists (avoid duplicates)
            existing = Question.objects.filter(
                lesson=lesson,
                question_text=q_data['question_text']
            ).exists()
            
            if existing:
                skipped_count += 1
                continue
            
            # Create question
            Question.objects.create(
                lesson=lesson,
                question_text=q_data['question_text'],
                correct_answer=q_data.get('answer', 'See mark scheme'),
                question_type='short_answer',
                difficulty_level=2,  # Default medium
                marks_available=q_data.get('marks', 2),
                explanation=f"From textbook {q_data.get('source', 'page ' + str(page_num))}",
                marking_scheme='Standard GCSE marking criteria',
                exam_board='aqa'
            )
            
            imported_count += 1
            
            if imported_count % 50 == 0:
                print(f"   Imported {imported_count} questions...")
        
        except Exception as e:
            print(f"   ❌ Error importing question: {e}")
            continue

# Summary
print("\n" + "="*70)
print("📊 IMPORT SUMMARY")
print("="*70)
print(f"✅ Successfully imported: {imported_count} questions")
print(f"⏭️  Skipped (duplicates): {skipped_count} questions")
print(f"📚 Total in database: {Question.objects.count()} questions")

# Show breakdown
maths_topics = Topic.objects.filter(subject=maths).count()
maths_lessons = Lesson.objects.filter(topic__subject=maths).count()
maths_questions = Question.objects.filter(lesson__topic__subject=maths).count()

print(f"\n📊 Mathematics content:")
print(f"   Topics: {maths_topics}")
print(f"   Lessons: {maths_lessons}")
print(f"   Questions: {maths_questions}")

print("\n" + "="*70)
print("✅ IMPORT COMPLETE!")
print("="*70)
print("\n🎯 Next steps:")
print("1. Check questions in Django admin: http://127.0.0.1:8000/admin/")
print("2. Test Decision Engine with real content")
print("3. Extract more textbooks (Physics, Biology, Chemistry)")

print()