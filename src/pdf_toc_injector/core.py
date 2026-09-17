"""
core.py: Core algorithms for heuristic TOC discovery, offset probing, and outline injection.
"""

import os
import re
import sys
import time
import shutil
import tempfile
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
import pymupdf

pymupdf.TOOLS.mupdf_display_errors(False)

TOC_KEYWORDS = [
    "inhaltsverzeichnis", "inhaltsübersicht", "inhaltsuebersicht", "inhaltsiibersicht",
    "inhalt", "table of contents", "contents", "table des matières",
    "содержание", "оглавление", "índice", "indice", "índice general"
]

def clean_section_title(text: str) -> str:
    """Normalizes OCR spaces in numbers and dots, and cleans dotted leader artifacts."""
    cleaned = re.sub(r'(\d+)\s*\.\s*', r'\1.', text)
    cleaned = re.sub(r'[\.·\-_]{2,}.*$', '', cleaned).strip()
    cleaned = re.sub(r'[\.·\-_]+$', '', cleaned).strip()
    return cleaned

def find_toc_pages(doc: pymupdf.Document, max_search_pages: int = 35) -> List[int]:
    """Finds pages in the front matter that contain the Table of Contents."""
    total = min(len(doc), max_search_pages)
    toc_pages = []
    in_toc = False
    
    for pno in range(total):
        text = doc[pno].get_text()
        text_lower = text.lower()
        first_lines = [l.strip().lower() for l in text_lower.splitlines() if l.strip()][:5]
        has_keyword = any(any(kw in line for kw in TOC_KEYWORDS) for line in first_lines)
        dot_leaders = len(re.findall(r'[\.·\-_]{2,}\s*[0-9]{1,4}', text))
        
        if has_keyword or (in_toc and dot_leaders >= 3):
            toc_pages.append(pno)
            in_toc = True
        elif in_toc:
            if dot_leaders == 0 and len(text.strip()) > 100:
                break
                
    return toc_pages

def parse_toc_entries(doc: pymupdf.Document, toc_page_indices: List[int]) -> List[Tuple[str, int]]:
    """Parses TOC pages into raw tuples of (title, printed_page_number)."""
    raw_lines = []
    for pno in toc_page_indices:
        text = doc[pno].get_text()
        raw_lines.extend(text.splitlines())
        
    entries = []
    buffer = ""
    
    for line in raw_lines:
        s = line.strip()
        if not s:
            continue
            
        s_lower = s.lower()
        if any(s_lower == kw for kw in TOC_KEYWORDS) or re.match(r'^[ivxlcdm]+\b', s_lower):
            continue
            
        # 1. Two-line format: title was accumulated in buffer, current line is pure page number
        if re.match(r'^[0-9]{1,4}$', s) and buffer and re.search(r'[a-zA-ZäöüÄÖÜßа-яА-Я]', buffer):
            full_title = clean_section_title(buffer)
            pnum = int(s)
            buffer = ""
            if full_title and 0 < pnum < len(doc) + 500:
                entries.append((full_title, pnum))
            continue

        # 2. Check if line is just a section number (e.g. '3.1' or '7.1.1')
        clean_num = clean_section_title(s)
        if re.match(r'^\d+(\.\d+)+\.?$', clean_num):
            buffer = clean_num
            continue

        # 3. Match dotted leaders or tab/spaced trailing page numbers
        m = re.search(r'[\.·\-_]{2,}\s*([0-9\s]{1,6})$', s)
        if not m:
            m = re.search(r'\s{3,}([0-9\s]{1,6})$', s)
            
        if m:
            pnum_str = m.group(1).replace(' ', '').replace('l', '1').replace('O', '0')
            title_part = s[:m.start()].strip()
            full_title = (buffer + " " + title_part).strip() if buffer else title_part
            buffer = ""
            full_title = clean_section_title(full_title)
            
            try:
                pnum = int(pnum_str)
                if full_title and 0 < pnum < len(doc) + 500:
                    entries.append((full_title, pnum))
            except ValueError:
                pass
        else:
            if buffer.isdigit():
                buffer = s
            else:
                buffer = (buffer + " " + s).strip()
            
    return entries

def detect_page_offset(doc: pymupdf.Document, entries: List[Tuple[str, int]], toc_pages: List[int]) -> Optional[int]:
    """
    Detects offset between printed page numbers and PDF 1-indexed page numbers.
    Formula: pdf_page = printed_page + offset.
    """
    if not entries:
        return None
        
    probe_candidates = []
    for title, printed_p in entries:
        m = re.match(r'^(?:Chapter\s+|Kapitel\s+|Часть\s+|Глава\s+)?([0-9]+)\s+([A-Za-zÄÖÜäöüßА-Яа-я]{3,})', title, re.IGNORECASE)
        if m and int(m.group(1)) in [1, 2, 3]:
            probe_candidates.append((title, printed_p, m.group(2).lower()))
            
    if not probe_candidates:
        for title, printed_p in entries[:5]:
            clean_word = re.sub(r'[^a-zA-ZäöüÄÖÜßа-яА-Я]', '', title)
            if len(clean_word) >= 4:
                probe_candidates.append((title, printed_p, clean_word[:6].lower()))

    offset_votes = {}
    last_toc_page = max(toc_pages) if toc_pages else 0
    page_text_cache = {}
    
    for title, printed_p, probe_kw in probe_candidates:
        min_pdf_p = max(last_toc_page + 1, printed_p - 5)
        max_pdf_p = min(len(doc), printed_p + 35)
        
        for p_test in range(min_pdf_p, max_pdf_p + 1):
            if p_test not in page_text_cache:
                page_text_cache[p_test] = doc[p_test - 1].get_text().lower()
            page_text = page_text_cache[p_test]
            if probe_kw in page_text:
                calc_offset = p_test - printed_p
                if calc_offset >= 0:
                    offset_votes[calc_offset] = offset_votes.get(calc_offset, 0) + 1

    if not offset_votes:
        return last_toc_page + 1

    return max(offset_votes.items(), key=lambda x: x[1])[0]

def compute_hierarchy_level(title: str) -> int:
    """Calculates outline depth level (1, 2, 3...)."""
    m = re.match(r'^(\d+(?:\.\d+)*)', title)
    if m:
        parts = m.group(1).split('.')
        return min(len(parts), 4)
    return 1

def build_pdf_toc(doc: pymupdf.Document, entries: List[Tuple[str, int]], offset: int, toc_pages: List[int]) -> List[List[Any]]:
    """Builds the PyMuPDF TOC list: [[level, title, pdf_page], ...], with hierarchy clamping."""
    raw_toc = []
    
    if toc_pages:
        first_toc = min(toc_pages) + 1
        raw_toc.append([1, "Table of Contents", first_toc])
        
    seen = set()
    for title, printed_p in entries:
        pdf_p = printed_p + offset
        if 1 <= pdf_p <= len(doc):
            level = compute_hierarchy_level(title)
            key = (title.lower(), pdf_p)
            if key not in seen:
                seen.add(key)
                raw_toc.append([level, title, pdf_p])
                
    # Hierarchy clamp: ensure level <= prev_level + 1
    clamped_toc = []
    prev_level = 0
    for level, title, page in raw_toc:
        if level > prev_level + 1:
            level = prev_level + 1
        clamped_toc.append([level, title, page])
        prev_level = level
        
    return clamped_toc

def inject_toc(pdf_path: Path, output_path: Optional[Path] = None, dry_run: bool = False) -> Dict[str, Any]:
    """Extracts printed TOC and injects it as interactive bookmarks into the PDF."""
    t0 = time.time()
    pdf_path = Path(pdf_path)
    
    try:
        doc = pymupdf.open(str(pdf_path))
    except Exception as e:
        return {"status": "open_failed", "error": str(e), "toc_count": 0}
        
    total_pages = len(doc)
    existing_toc = doc.get_toc()
    
    if len(existing_toc) > 0:
        doc.close()
        return {
            "status": "already_has_toc",
            "toc_count": len(existing_toc),
            "message": f"Document already has {len(existing_toc)} bookmarks."
        }
        
    toc_pages = find_toc_pages(doc)
    if not toc_pages:
        doc.close()
        return {
            "status": "no_toc_found",
            "toc_count": 0,
            "message": "No printed Table of Contents detected in front matter."
        }
        
    entries = parse_toc_entries(doc, toc_pages)
    if not entries:
        doc.close()
        return {
            "status": "parse_failed",
            "toc_count": 0,
            "message": f"TOC pages detected at {[p+1 for p in toc_pages]}, but could not parse entries."
        }
        
    offset = detect_page_offset(doc, entries, toc_pages)
    if offset is None:
        offset = 0
        
    new_toc = build_pdf_toc(doc, entries, offset, toc_pages)
    
    if dry_run:
        doc.close()
        return {
            "status": "dry_run",
            "toc_pages": [p + 1 for p in toc_pages],
            "offset": offset,
            "toc_count": len(new_toc),
            "sample": new_toc[:10]
        }
        
    doc.set_toc(new_toc)
    
    # Save to temp file on local scratch directory
    temp_dir = Path(tempfile.gettempdir()) / "pdf_toc_injector"
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_out = temp_dir / f"tmp_{os.getpid()}_{int(time.time()*1000)}.pdf"
    
    try:
        doc.save(str(temp_out), deflate=True)
        doc.close()
    except Exception as e:
        doc.close()
        if temp_out.exists():
            temp_out.unlink()
        return {"status": "save_failed", "error": str(e), "toc_count": 0}
        
    # Verification
    try:
        verify_doc = pymupdf.open(str(temp_out))
        verify_len = len(verify_doc)
        verify_toc = len(verify_doc.get_toc())
        verify_doc.close()
    except Exception as e:
        if temp_out.exists():
            temp_out.unlink()
        return {"status": "verify_failed", "error": str(e), "toc_count": 0}
        
    if verify_len != total_pages or verify_toc == 0:
        if temp_out.exists():
            temp_out.unlink()
        return {
            "status": "verify_mismatch",
            "error": f"Verification mismatch: pages={verify_len}/{total_pages}, toc={verify_toc}",
            "toc_count": 0
        }
        
    target_dest = Path(output_path) if output_path else pdf_path
    swapped = False
    for attempt in range(5):
        try:
            shutil.copy2(str(temp_out), str(target_dest))
            swapped = True
            break
        except PermissionError:
            time.sleep(0.5)
            
    if temp_out.exists():
        try:
            temp_out.unlink()
        except Exception:
            pass
            
    if not swapped:
        return {"status": "file_locked", "error": f"Target file locked: {target_dest}", "toc_count": 0}
        
    elapsed = round(time.time() - t0, 2)
    return {
        "status": "success",
        "path": str(target_dest),
        "filename": target_dest.name,
        "toc_count": len(new_toc),
        "offset": offset,
        "elapsed_seconds": elapsed,
        "sample": new_toc[:10]
    }
