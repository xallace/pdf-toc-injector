"""
cli.py: Command line interface for pdf-toc-injector.
"""

import sys
import argparse
from pathlib import Path
from .core import inject_toc

# Ensure clean UTF-8 printing
sys.stdout.reconfigure(encoding="utf-8")

def main():
    parser = argparse.ArgumentParser(
        description="pdf-toc-injector: Heuristic Table of Contents detection & bookmark injection for PDFs."
    )
    parser.add_argument("file", type=str, help="Path to PDF file to process")
    parser.add_argument("-o", "--output", type=str, default=None, help="Output path (default: in-place modification)")
    parser.add_argument("--dry-run", action="store_true", help="Simulate extraction without writing changes")
    args = parser.parse_args()
    
    pdf_path = Path(args.file)
    if not pdf_path.exists():
        print(f"[Error] File not found: {pdf_path}", file=sys.stderr)
        sys.exit(1)
        
    print("=" * 70)
    print(">>> PDF TOC INJECTOR <<<")
    print(f"File: {pdf_path.name}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'IN-PLACE INJECTION'}")
    print("=" * 70)
    
    res = inject_toc(pdf_path, output_path=args.output, dry_run=args.dry_run)
    status = res.get("status")
    
    if status in ("success", "dry_run"):
        print(f"Status:             {status.upper()}")
        print(f"Bookmarks Found:    {res.get('toc_count')}")
        print(f"Page Offset:        +{res.get('offset', 0)} pages")
        if not args.dry_run:
            print(f"Elapsed Time:       {res.get('elapsed_seconds')}s")
            
        print("\nSample Hierarchy (First 10):")
        for lvl, title, pno in res.get("sample", []):
            indent = "  " * lvl
            print(f"{indent}- {title} (p. {pno})")
        print("\n[Done] Process completed successfully.")
    else:
        print(f"Status:             {status.upper()}")
        print(f"Detail:             {res.get('message') or res.get('error')}")
        sys.exit(1)

if __name__ == "__main__":
    main()
