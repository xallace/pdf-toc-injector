"""
demo.py: Self-contained demonstration of pdf-toc-injector.
Synthesizes a sample multi-page PDF with printed Table of Contents,
detects the offset, and injects interactive PDF bookmarks.
"""

import sys
from pathlib import Path
import pymupdf

# Ensure clean UTF-8 printing on Windows terminals
sys.stdout.reconfigure(encoding="utf-8")

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from pdf_toc_injector import inject_toc

def create_sample_pdf(output_path: Path):
    """Creates a sample PDF with a printed TOC and a +2 page offset."""
    doc = pymupdf.open()
    
    # Page 1: Cover
    p1 = doc.new_page()
    p1.insert_text((72, 100), "Principles of Modern Engineering", fontsize=24)
    p1.insert_text((72, 140), "A Sample Technical Monograph for Demonstration", fontsize=14)
    p1.insert_text((72, 200), "Author: Walter Lehn & Antigravity (2026)", fontsize=11)
    
    # Page 2: Printed Table of Contents
    p2 = doc.new_page()
    p2.insert_text((72, 100), "Table of Contents", fontsize=18)
    toc_lines = [
        "1 Introduction to Applied Mechanics ............................................ 1",
        "1.1 Scope of the Investigation ................................................. 2",
        "1.2 Terminology and Foundations ................................................ 3",
        "2 Kinematic Chains and Degrees of Freedom ...................................... 4",
        "2.1 Four-Bar Linkages and Inversion ............................................ 5",
        "3 Concluding Synthesis ......................................................... 6",
    ]
    y = 140
    for line in toc_lines:
        p2.insert_text((72, y), line, fontsize=10)
        y += 24
        
    # Page 3: (Printed Page 1) -> Offset is +2 (PDF page 3 = Printed page 1)
    p3 = doc.new_page()
    p3.insert_text((72, 80), "1 Introduction to Applied Mechanics", fontsize=16)
    p3.insert_text((72, 120), "This is chapter 1 on printed page 1 (PDF page 3).", fontsize=11)
    
    # Page 4: (Printed Page 2)
    p4 = doc.new_page()
    p4.insert_text((72, 80), "1.1 Scope of the Investigation", fontsize=14)
    p4.insert_text((72, 120), "Detailed breakdown of the mechanical scope.", fontsize=11)
    
    # Page 5: (Printed Page 3)
    p5 = doc.new_page()
    p5.insert_text((72, 80), "1.2 Terminology and Foundations", fontsize=14)
    p5.insert_text((72, 120), "Core definitions and mathematical notation.", fontsize=11)

    # Page 6: (Printed Page 4)
    p6 = doc.new_page()
    p6.insert_text((72, 80), "2 Kinematic Chains and Degrees of Freedom", fontsize=16)
    p6.insert_text((72, 120), "Chapter 2 begins here on printed page 4.", fontsize=11)
    
    # Page 7: (Printed Page 5)
    p7 = doc.new_page()
    p7.insert_text((72, 80), "2.1 Four-Bar Linkages and Inversion", fontsize=14)
    p7.insert_text((72, 120), "Mechanisms and mobility equations.", fontsize=11)
    
    # Page 8: (Printed Page 6)
    p8 = doc.new_page()
    p8.insert_text((72, 80), "3 Concluding Synthesis", fontsize=16)
    p8.insert_text((72, 120), "Final conclusions and bibliography.", fontsize=11)
    
    doc.save(str(output_path))
    doc.close()
    print(f"[Demo] Created synthetic test PDF with 8 pages: {output_path.name}")

def main():
    test_pdf = Path(__file__).parent / "sample_synthetic_book.pdf"
    
    print("=" * 70)
    print(">>> PDF-TOC-INJECTOR LIVE REPOSITORY DEMO <<<")
    print("=" * 70)
    
    # Step 1: Create a test document with 0 bookmarks
    create_sample_pdf(test_pdf)
    
    doc_before = pymupdf.open(str(test_pdf))
    print(f"Bookmarks before injection: {len(doc_before.get_toc())} (DIGITAL_NO_TOC)")
    doc_before.close()
    
    # Step 2: Run automated detection & injection
    print("\nRunning automated TOC detection and offset calibration...")
    res = inject_toc(test_pdf)
    
    print(f"\nResult Status:        {res['status'].upper()}")
    print(f"Bookmarks Injected:   {res['toc_count']}")
    print(f"Detected Offset:      +{res['offset']} pages (Printed 1 = PDF 3)")
    print(f"Elapsed Execution:    {res['elapsed_seconds']}s")
    
    # Step 3: Verify the injected bookmark hierarchy
    doc_after = pymupdf.open(str(test_pdf))
    print("\nVerified PDF Bookmark Tree:")
    for lvl, title, pno in doc_after.get_toc():
        indent = "  " * lvl
        print(f"{indent}├── {title} (Target: PDF Page {pno})")
    doc_after.close()
    
    print("\n" + "=" * 70)
    print(">>> SUCCESS: Open 'sample_synthetic_book.pdf' in any PDF reader! <<<")
    print("=" * 70)

if __name__ == "__main__":
    main()
