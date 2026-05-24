"""
SIMPLE TEXTBOOK EXTRACTOR
Run this to extract questions from your GCSE Maths textbook
"""

import sys
from pathlib import Path

# Add pdf_textbook_extractor to path
sys.path.insert(0, str(Path(__file__).parent))

from pdf_textbook_extractor import PDFTextbookExtractor

# Path to your textbook
# Change this if your PDF is in a different location
PDF_PATH = 'gcse-1-9-textbook.pdf'

print("\n" + "="*70)
print("📚 GCSE MATHEMATICS TEXTBOOK QUESTION EXTRACTOR")
print("="*70)

# Check if PDF exists
if not Path(PDF_PATH).exists():
    print(f"\n❌ PDF not found: {PDF_PATH}")
    print("\nPlease either:")
    print("1. Copy gcse-1-9-textbook.pdf to this directory")
    print("2. Update PDF_PATH in this script to the correct location")
    sys.exit(1)

print(f"\n📖 Processing: {PDF_PATH}")
print("This may take a few minutes for a 447-page textbook...")

# Create extractor
extractor = PDFTextbookExtractor(PDF_PATH)

# Extract all questions
questions = extractor.process_textbook()

if questions:
    # Save to JSON
    output_file = 'extracted_maths_questions.json'
    extractor.save_to_file(output_file)
    
    # Show statistics
    print("\n" + "="*70)
    print("📊 EXTRACTION STATISTICS")
    print("="*70)
    print(f"✅ Total questions extracted: {len(questions)}")
    
    # Count by marks
    marks_count = {}
    for q in questions:
        marks = q.get('marks', 1)
        marks_count[marks] = marks_count.get(marks, 0) + 1
    
    print(f"\nQuestions by marks:")
    for marks in sorted(marks_count.keys()):
        print(f"  {marks} marks: {marks_count[marks]} questions")
    
    # Show sample questions
    print("\n" + "="*70)
    print("📝 SAMPLE QUESTIONS (First 5)")
    print("="*70)
    
    for i, q in enumerate(questions[:5], 1):
        print(f"\n{i}. [Page {q['page']}, Q{q['question_number']}, {q['marks']} marks]")
        print(f"   {q['question_text'][:150]}...")
        if q['answer']:
            print(f"   Answer: {q['answer']}")
    
    print("\n" + "="*70)
    print(f"✅ SUCCESS! Saved {len(questions)} questions to {output_file}")
    print("="*70)
    
    print("\n📥 Next step: Import to database")
    print("   Run: python import_to_database.py")
    
else:
    print("\n❌ No questions extracted!")
    print("The PDF might:")
    print("  - Be scanned images (not searchable text)")
    print("  - Have unusual formatting")
    print("  - Not contain practice questions")

print()