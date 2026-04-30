#!/usr/bin/env python3
"""
generate-pages.py
=================
Converts a PDF magazine into page images for the flipbook website.

REQUIREMENTS
------------
Install these once:
    pip install PyMuPDF Pillow

USAGE
-----
Run from the ROOT of the project (not from inside /scripts):

    python scripts/generate-pages.py magazines/my-magazine.pdf

WHAT THIS SCRIPT DOES
---------------------
1. Reads the PDF you point it at.
2. Converts every page to a JPEG image at 150 DPI (adjustable).
3. Saves images to: pages/{magazine-id}/page-1.jpg, page-2.jpg, etc.
4. Saves a higher-resolution cover image to: covers/{magazine-id}.jpg
5. Creates a template file at: data/pages/{magazine-id}.json
   (Open this file and fill in the text/captions for each page.)
6. Prints a JSON snippet to paste into data/magazines.json. Found in terminal.

IMAGE SETTINGS
--------------
- DPI 150 → ~200–400 KB per page (sharp on screen, fast to load)
- DPI 200 → ~400–700 KB per page (higher quality, slower to load)
  Change DPI below if needed.
- JPEG quality 85 is a good balance. Increase to 92 for sharper images.

-------------
Note: PLEASE ONLY UPLOAD PDFS WITH SEPARATED PAGES, NOT SPREADS.
-------------
"""

import sys
import os
import json
import re
from pathlib import Path


# ==============================================================
# ✏️  CONFIGURABLE SETTINGS — adjust these if needed
# ==============================================================
PAGE_DPI      = 250    # Resolution for page images (150 = good, 200 = high quality)
COVER_DPI     = 150    # Resolution for the cover thumbnail (slightly sharper)
JPEG_QUALITY  = 100     # JPEG compression (1–95). 85 = excellent balance.
COVER_QUALITY = 100    # Cover can be slightly higher quality.
# ==============================================================


# ---- Check for required libraries ----
try:
    import fitz  # PyMuPDF — the core PDF engine
except ImportError:
    print()
    print("❌  ERROR: PyMuPDF is not installed.")
    print("   Fix: pip install PyMuPDF")
    print()
    sys.exit(1)

try:
    from PIL import Image  # Pillow — for saving JPEGs with quality control
except ImportError:
    print()
    print("❌  ERROR: Pillow is not installed.")
    print("   Fix: pip install Pillow")
    print()
    sys.exit(1)


def slugify(text: str) -> str:
    """
    Convert a filename or string into a clean URL-safe slug.
    Example: 'Mentor Magic — Spring 2026' → 'mentor-magic-spring-2026'
    """
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)   # Replace non-alphanumeric with dash
    text = text.strip('-')                      # Remove leading/trailing dashes
    return text


def get_magazine_id(pdf_path: Path) -> str:
    """Derive the magazine ID from the PDF filename (without extension)."""
    return slugify(pdf_path.stem)


def render_page_to_jpeg(page, dpi: int, quality: int, output_path: Path):
    """Render a single PDF page to a JPEG file."""
    matrix = fitz.Matrix(dpi / 72, dpi / 72)   # 72 = PDF default DPI
    pix    = page.get_pixmap(matrix=matrix, alpha=False)

    # Use Pillow for better quality JPEG encoding
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    img.save(str(output_path), "JPEG", quality=quality, optimize=True)


def main():
    # ---- Parse arguments ----
    if len(sys.argv) < 2:
        print()
        print("Usage:  python scripts/generate-pages.py magazines/your-magazine.pdf")
        print()
        print("Run this from the root folder of the project (not from inside /scripts).")
        print()
        sys.exit(1)

    pdf_path = Path(sys.argv[1])

    if not pdf_path.exists():
        print(f"\n❌  File not found: {pdf_path}\n")
        sys.exit(1)

    if pdf_path.suffix.lower() != '.pdf':
        print(f"\n❌  Expected a .pdf file, got: {pdf_path}\n")
        sys.exit(1)

    mag_id = get_magazine_id(pdf_path)
    print()
    print(f"📄  PDF:  {pdf_path}")
    print(f"🆔  ID:   {mag_id}")
    print()

    # ---- Create output directories if they don't exist ----
    pages_dir  = Path(f"pages/{mag_id}")
    covers_dir = Path("covers")
    data_dir   = Path("data/pages")

    pages_dir.mkdir(parents=True, exist_ok=True)
    covers_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)

    # ---- Open the PDF ----
    doc = fitz.open(str(pdf_path))
    num_pages = len(doc)
    print(f"📑  {num_pages} pages found in PDF.")
    print()

    # Template data that gets written to data/pages/{id}.json
    page_data_template = []

    # ---- Convert each page to JPEG ----
    print("   Converting pages…")
    for i, page in enumerate(doc):
        page_num  = i + 1
        out_path  = pages_dir / f"page-{page_num}.jpg"

        # Render page to JPEG
        render_page_to_jpeg(page, PAGE_DPI, JPEG_QUALITY, out_path)

        # Print progress
        bar = ('█' * page_num).ljust(num_pages)
        print(f"   [{bar}] {page_num}/{num_pages}", end='\r')

        # Build template entry for this page's text data
        page_data_template.append({
            "title":    f"Page {page_num}",
            "text":     "",      # ← Fill this in for TTS / accessibility
            "captions": ""       # ← Describe images/layout on this page
        })

    print(f"\n   ✅  Saved {num_pages} images to {pages_dir}/")
    print()

    # ---- Save the cover image (first page, slightly higher resolution) ----
    cover_path = covers_dir / f"{mag_id}.jpg"
    render_page_to_jpeg(doc[0], COVER_DPI, COVER_QUALITY, cover_path)
    print(f"🖼️   Cover saved to {cover_path}")
    print()

    doc.close()

    # ---- Write the page data template ----
    page_data_path = data_dir / f"{mag_id}.json"
    with open(str(page_data_path), 'w', encoding='utf-8') as f:
        json.dump(page_data_template, f, indent=2, ensure_ascii=False)

    print(f"📝  Page data template saved to {page_data_path}")
    print(f"    → Open this file and fill in 'text' and 'captions' for each page.")
    print(f"    → This text is used by the text-to-speech feature and for accessibility.")
    print()

    # ---- Print the magazines.json snippet ----
    snippet = {
        "id":          mag_id,
        "title":       "Mentor Magic — Season Year",    # ← Change this
        "year":        "2026",                           # ← Change this
        "category":    "Spring Issue",                   # ← Change this
        "pageCount":   num_pages,
        "pdf":         f"magazines/{pdf_path.name}",
        "cover":       f"covers/{mag_id}.jpg",
        "description": "A short description of this issue."   # ← Change this
    }

    print("=" * 62)
    print("📋  ADD THIS ENTRY TO data/magazines.json")
    print("    (paste it inside the [ ] array, before or after other entries)")
    print("=" * 62)
    print()
    print(json.dumps(snippet, indent=2))
    print()
    print("=" * 62)
    print()
    print("✅  Done! Next steps:")
    print()
    print(f"   1. Edit {page_data_path}")
    print(f"      Fill in 'text' and 'captions' for each page (optional but recommended).")
    print()
    print(f"   2. Add the JSON snippet above to data/magazines.json")
    print(f"      Update 'title', 'year', 'category', and 'description'.")
    print()
    print(f"   3. Commit and push to GitHub.")
    print(f"      The site will update automatically.")
    print()


if __name__ == '__main__':
    main()
