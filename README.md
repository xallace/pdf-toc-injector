<div align="center">

# 📑 pdf-toc-injector

**Automated Table of Contents Detection & Hierarchical Bookmark Injection for Digitized PDFs**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Engine: PyMuPDF](https://img.shields.io/badge/Engine-PyMuPDF-green.svg)](https://pymupdf.readthedocs.io/)
[![Zero-Config](https://img.shields.io/badge/Config-Zero-orange.svg)]()

*Stop squinting at digitized books with zero bookmarks. Automatically detect printed tables of contents, calculate page offsets, and inject interactive PDF outlines in milliseconds.*

</div>

---

## ⚡ The Problem

Millions of scanned technical books, academic monographs, and public-domain documents have readable text, but **zero PDF bookmarks** (`DIGITAL_NO_TOC`). 

Navigating a 500-page book requires manual page guessing because:
1. Printed page numbers almost **never match** PDF page numbers due to front matter (covers, prefaces, roman numerals).
2. Manually creating 100+ nested bookmarks in Acrobat or Skim takes hours.

## 🚀 The Solution: `pdf-toc-injector`

`pdf-toc-injector` is an intelligent, zero-config engine that:
* 🔍 **Discovers TOC Pages:** Scans front matter using multilingual heuristic keywords (`Table of Contents`, `Inhaltsverzeichnis`, `Содержание`, `Índice`, etc.) and dotted-leader pattern recognition.
* 📐 **Probes Mathematical Page Offset:** Cross-references chapter titles against body pages to calculate the exact offset ($\text{PDF Page} = \text{Printed Page} + \text{Offset}$).
* 🌲 **Builds Multi-Tier Hierarchies:** Automatically detects sections, sub-sections, and detail levels (`1.1`, `1.2.3`), with built-in hierarchy clamping to guarantee valid PDF outlines.
* ⚡ **High Throughput:** Processes a typical book in **0.2 to 1.5 seconds**.

---

## 🏗️ Architecture

```
┌─────────────────┐     ┌──────────────────────┐     ┌────────────────────────┐
│  Input PDF      │ ──> │ 1. Heuristic Scan    │ ──> │ 2. Offset Calibration  │
│  (0 Bookmarks)  │     │    (Keyword + Dots)  │     │    (Multi-point Probe) │
└─────────────────┘     └──────────────────────┘     └────────────────────────┘
                                                                 │
                                                                 ▼
┌─────────────────┐     ┌──────────────────────┐     ┌────────────────────────┐
│  Output PDF     │ <── │ 4. Atomic In-Place   │ <── │ 3. Hierarchical Clamped│
│  (Interactive)  │     │    Safe Swap (SSD)   │     │    Outline Tree (MuPDF)│
└─────────────────┘     └──────────────────────┘     └────────────────────────┘
```

---

## 🏁 Quickstart & Demo

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/xallace/pdf-toc-injector.git
cd pdf-toc-injector

# Install dependencies
pip install -r requirements.txt
```

### 2. Run the Built-In Demo (Instant Test)

The repository includes a self-contained demonstration script that synthesizes an 8-page sample technical book and injects bookmarks into it in 0.15 seconds:

```bash
python demo.py
```

**Output:**
```text
======================================================================
>>> PDF-TOC-INJECTOR LIVE REPOSITORY DEMO <<<
======================================================================
[Demo] Created synthetic test PDF with 8 pages: sample_synthetic_book.pdf
Bookmarks before injection: 0 (DIGITAL_NO_TOC)

Running automated TOC detection and offset calibration...

Result Status:        SUCCESS
Bookmarks Injected:   7
Detected Offset:      +2 pages (Printed 1 = PDF 3)
Elapsed Execution:    0.14s

Verified PDF Bookmark Tree:
  ├── Table of Contents (Target: PDF Page 2)
  ├── 1 Introduction to Applied Mechanics (Target: PDF Page 3)
    ├── 1.1 Scope of the Investigation (Target: PDF Page 4)
    ├── 1.2 Terminology and Foundations (Target: PDF Page 5)
  ├── 2 Kinematic Chains and Degrees of Freedom (Target: PDF Page 6)
    ├── 2.1 Four-Bar Linkages and Inversion (Target: PDF Page 7)
  ├── 3 Concluding Synthesis (Target: PDF Page 8)
```

---

## 💻 CLI Usage

```bash
# Process a single book in-place
python -m pdf_toc_injector.cli "my_book.pdf"

# Dry run (inspect detected bookmarks & offset without modifying file)
python -m pdf_toc_injector.cli "my_book.pdf" --dry-run

# Save to a new output file
python -m pdf_toc_injector.cli "input.pdf" -o "output_bookmarked.pdf"
```

---

## 🐍 Python API

```python
from pathlib import Path
from pdf_toc_injector import inject_toc

# Inject bookmarks directly
result = inject_toc(Path("handbook.pdf"))

print(f"Status:   {result['status']}")
print(f"Injected: {result['toc_count']} bookmarks")
print(f"Offset:   +{result['offset']} pages")
```

---

## 📤 Publishing this to GitHub

To push this demo to your own GitHub profile:

```bash
cd "G:\My Drive\agy\demos\pdf-toc-injector"

# Initialize Git
git init -b main
git add .
git commit -m "Initial release of pdf-toc-injector v0.1.0"

# Connect to your GitHub repository
git remote add origin https://github.com/xallace/pdf-toc-injector.git
git push -u origin main
```

---

## 📄 License

MIT License © 2026 Walter Lehn & Antigravity.
