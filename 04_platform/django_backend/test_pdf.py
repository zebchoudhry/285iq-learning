"""
Quick test: Check what's actually in the PDF
"""

import pdfplumber
from pathlib import Path

pdf_path = 'gcse-1-9-textbook.pdf'

if not Path(pdf_path).exists():
    print("PDF not found!")
    exit()

print("\n" + "="*70)
print("PDF CONTENT TEST")
print("="*70)

with pdfplumber.open(pdf_path) as pdf:
    # Test first 3 pages
    for i in range(min(3, len(pdf.pages))):
        print(f"\n--- PAGE {i+1} ---")
        text = pdf.pages[i].extract_text()
        
        if text:
            print(f"Text found: {len(text)} characters")
            print(f"Sample: {text[:300]}...")
        else:
            print("[X] No text found - This page is likely a scanned image!")

print("\n" + "="*70)
