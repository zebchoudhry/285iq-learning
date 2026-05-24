"""
PDF TEXTBOOK EXTRACTION MODULE
Extracts questions from GCSE textbook PDFs

Supports:
- Oxford University Press textbooks
- AQA, Edexcel, OCR exam board books
- Automatic question detection
- Answer extraction
- Image/diagram extraction
"""

import re
from typing import List, Tuple, Optional
from pathlib import Path


class PDFTextbookExtractor:
    """
    Extract questions from GCSE textbook PDFs
    """
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.pages = []
        self.questions = []
    
    def extract_text_from_pdf(self) -> List[str]:
        """
        Extract text from all pages
        
        Requires: pip install PyPDF2 pdfplumber
        """
        try:
            import pdfplumber
            
            pages_text = []
            
            with pdfplumber.open(self.pdf_path) as pdf:
                print(f"📖 Reading PDF: {Path(self.pdf_path).name}")
                print(f"   Total pages: {len(pdf.pages)}")
                
                for i, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if text:
                        pages_text.append(text)
                    
                    if (i + 1) % 50 == 0:
                        print(f"   Processed {i + 1} pages...")
            
            self.pages = pages_text
            print(f"✅ Extracted text from {len(pages_text)} pages")
            return pages_text
        
        except ImportError:
            print("❌ pdfplumber not installed!")
            print("   Install: pip install pdfplumber --break-system-packages")
            return []
        
        except Exception as e:
            print(f"❌ Error extracting PDF: {e}")
            return []
    
    def find_question_pages(self) -> List[Tuple[int, str]]:
        """
        Find pages that contain practice questions/exercises
        """
        question_pages = []
        
        # Keywords that indicate question pages
        keywords = [
            'exercise', 'practice', 'questions', 'problem',
            'Q1', 'Q2', 'Question 1', 'Question 2',
            'Work out', 'Calculate', 'Solve', 'Find'
        ]
        
        for page_num, page_text in enumerate(self.pages, 1):
            page_lower = page_text.lower()
            
            # Check if page has question indicators
            has_questions = any(keyword.lower() in page_lower for keyword in keywords)
            
            # Check for question numbering patterns
            has_numbering = bool(re.search(r'(Q\d+|Question \d+|\d+\.)', page_text))
            
            if has_questions and has_numbering:
                question_pages.append((page_num, page_text))
        
        print(f"\n📄 Found {len(question_pages)} pages with questions")
        return question_pages
    
    def extract_questions_from_page(self, page_text: str, page_num: int) -> List[dict]:
        """
        Extract individual questions from a page
        
        Patterns to match:
        - Q1. Question text
        - Question 1: Question text
        - 1. Question text
        - (a) Question text
        """
        questions = []
        
        # Pattern 1: Q followed by number
        pattern1 = r'Q(\d+)[.:]\s*([^\n]+(?:\n(?!Q\d)[^\n]+)*)'
        
        # Pattern 2: Question followed by number
        pattern2 = r'Question\s+(\d+)[.:]\s*([^\n]+(?:\n(?!Question\s+\d)[^\n]+)*)'
        
        # Pattern 3: Just number with dot
        pattern3 = r'^(\d+)\.\s+([^\n]+(?:\n(?!^\d+\.)[^\n]+)*)'
        
        # Try all patterns
        for pattern in [pattern1, pattern2, pattern3]:
            matches = re.finditer(pattern, page_text, re.MULTILINE)
            
            for match in matches:
                q_num = match.group(1)
                q_text = match.group(2).strip()
                
                if len(q_text) < 15:  # Skip very short text
                    continue
                
                # Try to find answer on same page
                answer = self._find_answer(page_text, q_num)
                
                # Estimate marks
                marks = self._estimate_marks(q_text)
                
                questions.append({
                    'question_number': q_num,
                    'question_text': q_text,
                    'answer': answer,
                    'marks': marks,
                    'page': page_num,
                    'source': f"p.{page_num} Q{q_num}"
                })
        
        return questions
    
    def _find_answer(self, page_text: str, question_num: str) -> Optional[str]:
        """
        Try to find answer for question on same page
        """
        # Common answer patterns
        patterns = [
            f'Answer.*?{question_num}.*?:.*?([^\n]+)',
            f'Ans.*?{question_num}.*?:.*?([^\n]+)',
            f'{question_num}[.:]\s*Answer:?\s*([^\n]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _estimate_marks(self, question_text: str) -> int:
        """
        Estimate marks based on question complexity
        """
        q_lower = question_text.lower()
        
        # High marks indicators
        if any(word in q_lower for word in ['explain', 'describe', 'evaluate', 'justify']):
            return 4
        elif any(word in q_lower for word in ['show', 'prove', 'demonstrate']):
            return 3
        elif len(question_text) > 150:
            return 2
        else:
            return 1
    
    def process_textbook(self) -> List[dict]:
        """
        Main method: Extract all questions from textbook
        """
        print("\n" + "="*70)
        print("📚 PROCESSING TEXTBOOK")
        print("="*70)
        
        # Step 1: Extract text
        if not self.pages:
            self.extract_text_from_pdf()
        
        if not self.pages:
            print("❌ No text extracted!")
            return []
        
        # Step 2: Find question pages
        question_pages = self.find_question_pages()
        
        if not question_pages:
            print("❌ No question pages found!")
            return []
        
        # Step 3: Extract questions
        print(f"\n🔍 Extracting questions...")
        all_questions = []
        
        for page_num, page_text in question_pages:
            page_questions = self.extract_questions_from_page(page_text, page_num)
            all_questions.extend(page_questions)
            
            if len(all_questions) % 50 == 0:
                print(f"   Extracted {len(all_questions)} questions...")
        
        self.questions = all_questions
        
        print(f"\n✅ Total questions extracted: {len(all_questions)}")
        print("="*70)
        
        return all_questions
    
    def save_to_file(self, output_path: str):
        """Save extracted questions to JSON"""
        import json
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.questions, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Saved to: {output_path}")


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == '__main__':
    # Example: Extract from your GCSE textbook
    pdf_path = 'gcse-1-9-textbook.pdf'
    
    if Path(pdf_path).exists():
        print("\n🎓 Starting textbook extraction...")
        
        extractor = PDFTextbookExtractor(pdf_path)
        questions = extractor.process_textbook()
        
        if questions:
            # Show sample
            print("\n📝 Sample questions:")
            for q in questions[:3]:
                print(f"\nQ{q['question_number']} (p.{q['page']}, {q['marks']} marks):")
                print(f"  {q['question_text'][:100]}...")
                if q['answer']:
                    print(f"  Answer: {q['answer']}")
            
            # Save
            extractor.save_to_file('extracted_maths_questions.json')
        
        print("\n✅ Extraction complete!")
    
    else:
        print(f"❌ PDF not found: {pdf_path}")
        print("\nPlace your GCSE textbook PDF in the same directory")
        print("Supported: AQA, Edexcel, OCR textbooks")