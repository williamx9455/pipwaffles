#!/usr/bin/env python3
"""
Convert a PDF magazine into WebP images for the flipbook website.

Run from the project root:

    python scripts/generate-webp.py magazines/my-magazine.pdf

This script is the canonical converter for the site. It renders lightly lossy
WebP by default:

    pages/{magazine-id}/page-1.webp
    pages/{magazine-id}/page-2.webp
    ...
    covers/{magazine-id}.webp

It also creates data/pages/{magazine-id}.json only when that file does not
already exist, so existing text-to-speech/accessibility copy is preserved.
"""

import argparse
import json
import re
import sys
from pathlib import Path


# ==============================================================
# Rendering settings
# ==============================================================
# 300 DPI plus lightly lossy WebP is visually close to lossless at the reader's
# display size, while keeping the archive much smaller.
DEFAULT_PAGE_DPI = 300
DEFAULT_COVER_DPI = 200
DEFAULT_QUALITY = 82
WEBP_METHOD = 6
# ==============================================================


try:
    import fitz  # PyMuPDF
except ImportError:
    print("\nERROR: PyMuPDF is not installed.\nFix: pip install PyMuPDF\n")
    sys.exit(1)

try:
    from PIL import Image
except ImportError:
    print("\nERROR: Pillow is not installed.\nFix: pip install Pillow\n")
    sys.exit(1)


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def get_magazine_id(pdf_path: Path) -> str:
    return slugify(pdf_path.stem)


def render_page_to_webp(
    page,
    dpi: int,
    output_path: Path,
    *,
    lossless: bool,
    quality: int,
) -> None:
    """Render a single PDF page to a WebP file."""
    matrix = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=matrix, alpha=False)

    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    save_options = {
        "lossless": lossless,
        "method": WEBP_METHOD,
    }
    if not lossless:
        save_options["quality"] = quality

    img.save(str(output_path), "WEBP", **save_options)


def build_page_data_template(num_pages: int) -> list[dict[str, str]]:
    return [
        {
            "title": f"Page {page_num}",
            "text": "",
            "captions": "",
        }
        for page_num in range(1, num_pages + 1)
    ]


def write_page_data_template(path: Path, num_pages: int, overwrite: bool) -> None:
    if path.exists() and not overwrite:
        print(f"Page data already exists, preserving: {path}")
        return

    template = build_page_data_template(num_pages)
    with path.open("w", encoding="utf-8") as f:
        json.dump(template, f, indent=2, ensure_ascii=False)
        f.write("\n")

    action = "Overwrote" if overwrite else "Created"
    print(f"{action} page data template: {path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render a magazine PDF to lossless WebP assets."
    )
    parser.add_argument("pdf", help="Path to a magazine PDF, e.g. magazines/issue.pdf")
    parser.add_argument(
        "--id",
        dest="magazine_id",
        help="Override the generated magazine ID/output folder name.",
    )
    parser.add_argument(
        "--overwrite-page-data",
        action="store_true",
        help="Replace data/pages/{id}.json instead of preserving existing text.",
    )
    parser.add_argument(
        "--page-dpi",
        type=int,
        default=DEFAULT_PAGE_DPI,
        help=f"Render DPI for flipbook pages. Default: {DEFAULT_PAGE_DPI}.",
    )
    parser.add_argument(
        "--cover-dpi",
        type=int,
        default=DEFAULT_COVER_DPI,
        help=f"Render DPI for cover images. Default: {DEFAULT_COVER_DPI}.",
    )
    parser.add_argument(
        "--lossy",
        action="store_true",
        help="Use lossy WebP. This is the default unless --lossless is set.",
    )
    parser.add_argument(
        "--lossless",
        action="store_true",
        help="Use lossless WebP instead of the default lossy WebP.",
    )
    parser.add_argument(
        "--quality",
        type=int,
        default=DEFAULT_QUALITY,
        help=f"Lossy WebP quality. Default: {DEFAULT_QUALITY}.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    pdf_path = Path(args.pdf)

    if not pdf_path.exists():
        print(f"\nERROR: File not found: {pdf_path}\n")
        sys.exit(1)

    if pdf_path.suffix.lower() != ".pdf":
        print(f"\nERROR: Expected a .pdf file, got: {pdf_path}\n")
        sys.exit(1)

    mag_id = args.magazine_id or get_magazine_id(pdf_path)
    pages_dir = Path("pages") / mag_id
    covers_dir = Path("covers")
    data_dir = Path("data") / "pages"

    pages_dir.mkdir(parents=True, exist_ok=True)
    covers_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nPDF: {pdf_path}")
    print(f"ID: {mag_id}")
    use_lossless = args.lossless and not args.lossy

    print(f"Format: {'lossless' if use_lossless else 'lossy'} WebP")
    if not use_lossless:
        print(f"Quality: {args.quality}")
    print(f"Page DPI: {args.page_dpi}")
    print(f"Cover DPI: {args.cover_dpi}\n")

    doc = fitz.open(str(pdf_path))
    num_pages = len(doc)
    print(f"{num_pages} pages found\n")

    print("Converting pages...")
    for i, page in enumerate(doc):
        page_num = i + 1
        out_path = pages_dir / f"page-{page_num}.webp"
        render_page_to_webp(
            page,
            args.page_dpi,
            out_path,
            lossless=use_lossless,
            quality=args.quality,
        )
        print(f"   Page {page_num}/{num_pages}", end="\r")

    print(f"\nSaved {num_pages} WebP pages to {pages_dir}/\n")

    cover_path = covers_dir / f"{mag_id}.webp"
    render_page_to_webp(
        doc[0],
        args.cover_dpi,
        cover_path,
        lossless=use_lossless,
        quality=args.quality,
    )
    print(f"Cover saved to {cover_path}\n")

    doc.close()

    page_data_path = data_dir / f"{mag_id}.json"
    write_page_data_template(page_data_path, num_pages, args.overwrite_page_data)

    snippet = {
        "id": mag_id,
        "title": "Your Title Here",
        "year": "2026",
        "category": "Spring Issue",
        "pageCount": num_pages,
        "pdf": f"magazines/{pdf_path.name}",
        "cover": f"covers/{mag_id}.webp",
        "description": "Short description.",
    }

    print("\n" + "=" * 60)
    print("ADD THIS TO data/magazines.json:\n")
    print(json.dumps(snippet, indent=2))
    print("=" * 60)
    print("\nDone.\n")


if __name__ == "__main__":
    main()
