# Magazine Archive Project Context

This file is a handoff/context note for future work in this repo. It summarizes the current project structure, data flow, asset expectations, and known issues observed on April 30, 2026.

## Project Purpose

This is a static magazine archive and flipbook reader for Sharpur Edge magazines.

The app has two main screens:

- `index.html`: archive/library page with magazine cards, search, filters, and sorting.
- `reader.html`: flipbook reader for one magazine, selected by URL query string such as `reader.html?id=arts-issue-fall-2025`.

The project is intentionally data-driven. Most content updates should happen through JSON data files and generated assets rather than editing the main HTML files.

## Main Runtime Flow

### Archive Page

`index.html`:

- Fetches `data/magazines.json`.
- Expects it to be a JSON array.
- Builds filter buttons from unique `year` and `category` values.
- Supports search across `title`, `year`, `category`, and `description`.
- Sorts by newest, oldest, or title.
- Renders each magazine as a card linking to `reader.html?id={magazine.id}`.
- Uses each magazine object's `cover` path for card artwork.

### Reader Page

`reader.html`:

- Reads `id` from the URL query string.
- Fetches `data/magazines.json`.
- Finds the magazine entry with the matching `id`.
- Sets the page title, header title, PDF download link, and open-PDF link.
- Attempts to fetch optional page text from `data/pages/{magazine.id}.json`.
- Builds page image paths using:

```text
pages/{magazine.id}/page-1.webp
pages/{magazine.id}/page-2.webp
...
```

- Uses StPageFlip from CDN:

```text
https://cdn.jsdelivr.net/npm/page-flip/dist/js/page-flip.browser.min.js
```

- Falls back to unpkg if jsDelivr fails.
- Supports previous/next page navigation, direct page input, zoom, fit-to-screen, keyboard shortcuts, PDF download/open links, and browser text-to-speech.

## Core Files

- `index.html`: archive page UI, filtering, searching, sorting, and card rendering.
- `reader.html`: flipbook reader, StPageFlip integration, PDF links, page text panel, text-to-speech, keyboard controls.
- `assets/style.css`: shared design tokens and base components.
- `data/magazines.json`: source of truth for visible magazine issues.
- `data/pages/{id}.json`: per-page text and captions for accessibility/TTS.
- `scripts/generate-webp.py`: current WebP PDF-to-image conversion script.
- `scripts/generate-jpg.py`: older/alternate JPG conversion script.
- `README.md`: project instructions, but currently stale in places.

## Data Model

Each magazine entry in `data/magazines.json` looks like:

```json
{
  "id": "arts-issue-fall-2025",
  "title": "The Arts Issue, Fall 2025",
  "year": "2025",
  "category": "Fall Issue",
  "pageCount": 14,
  "pdf": "magazines/arts-issue-fall-2025.pdf",
  "cover": "covers/arts-issue-fall-2025.webp",
  "description": "Explore the wonders of art or something"
}
```

Important fields:

- `id`: must match the PDF-derived slug, page data filename, and page image folder.
- `pageCount`: drives how many page image URLs the reader tries to load.
- `pdf`: relative path to the source PDF.
- `cover`: relative path to the cover image shown on the archive page.

Page data files are arrays:

```json
[
  {
    "title": "Page 1",
    "text": "",
    "captions": ""
  }
]
```

The reader uses `title`, `text`, and `captions` for the side panel and text-to-speech.

## Current Magazine Inventory

Current entries in `data/magazines.json`:

| ID | Page Count | PDF Present | Cover Present | WebP Pages Present |
| --- | ---: | --- | --- | ---: |
| `take-charge-fall-2023` | 16 | yes | no | 0 |
| `dream-big-spring-2024` | 16 | yes | no | 0 |
| `find-your-edge-fall-2024` | 16 | yes | no | 0 |
| `arts-issue-fall-2025` | 14 | yes | yes | 14 |
| `mentor-magic-spring-2025` | 16 | yes | no | 0 |

PDF page counts were checked with PyMuPDF and match `pageCount`.

## Current Asset Format State

The repo has been migrated from JPG runtime assets to WebP runtime assets.

Current runtime code expects WebP:

- `data/magazines.json` points covers to `covers/{id}.webp`.
- `reader.html` builds page image paths as `pages/{id}/page-N.webp`.

All active `data/magazines.json` entries should have matching WebP covers and page images. The current preferred output is lightly lossy WebP at 300 DPI / quality 82 because it looks nearly identical at the reader's display size and is much smaller than 450 DPI lossless output.

## Scripts

### `scripts/generate-webp.py`

Current intended converter.

Behavior:

- Takes a PDF path.
- Slugifies the PDF filename into a magazine ID.
- Renders all pages to:

```text
pages/{id}/page-N.webp
```

- Renders cover to:

```text
covers/{id}.webp
```

- Writes a page text template to:

```text
data/pages/{id}.json
```

- Prints a JSON snippet for `data/magazines.json`.

Settings:

- Default page render DPI is 300.
- Default cover render DPI is 200.
- Default WebP output is lossy quality 82.
- `--lossless` is available for artifact-free output when needed.
- `--page-dpi` and `--cover-dpi` can override defaults.
- `COVER_QUALITY = 90`

Dependencies:

- PyMuPDF (`fitz`)
- Pillow

### `scripts/generate-jpg.py`

Older/alternate converter.

Behavior is similar, but outputs:

```text
pages/{id}/page-N.jpg
covers/{id}.jpg
```

Current runtime code no longer points at JPG files.

## README Status

`README.md` still documents the older JPG workflow:

- It references `scripts/generate-pages.py`.
- It says generated page images are `.jpg`.
- It says covers are `.jpg`.
- It says reader images live at `page-N.jpg`.

But the current working tree:

- Deletes `scripts/generate-pages.py`.
- Adds `scripts/generate-webp.py`.
- Adds `scripts/generate-jpg.py`.
- Changes runtime references to WebP.

The README should be updated once the desired final asset strategy is confirmed.

## Validation Already Performed

The following checks were run:

- All JSON files under `data/` parse successfully.
- `scripts/generate-webp.py` and `scripts/generate-jpg.py` compile successfully with Python.
- PDF page counts match `data/magazines.json`.
- Current asset presence was compared against `data/magazines.json`.

The Python compile check briefly created `scripts/__pycache__`, which was removed.

## Notable Working Tree State

The git working tree is dirty.

Notable changes include:

- Deleted old JPG covers.
- Deleted old JPG page images.
- Modified `data/magazines.json` to reference WebP covers.
- Modified `reader.html` to reference WebP page images.
- Modified several `data/pages/*.json` files, mostly clearing placeholder text.
- Modified `magazines/arts-issue-fall-2025.pdf`.
- Deleted `scripts/generate-pages.py`.
- Added `scripts/generate-webp.py`.
- Added `scripts/generate-jpg.py`.
- Added WebP assets for `arts-issue-fall-2025`.

Do not blindly revert these changes. Treat them as user work unless explicitly told otherwise.

## Odd/Probably Accidental Directories

There is an unusual directory path:

```text
{assets,data/pages,scripts,magazines,covers,pages}
```

It appears to be accidental and empty/nested strangely. Confirm before deleting.

There is also an `assets/SVG` directory that appears empty.

## Design Assets

Text/code-readable assets:

- `assets/sharpur-edge-logo.svg`: Sharpur Edge logo.
- `assets/pips/over-the-hedge-pip.svg`: large mascot illustration used as the search icon.

Binary assets:

- `assets/pips/over-the-hedge-pip.png`
- many `.otf` font files under `assets/fonts/`
- magazine PDFs under `magazines/`
- generated WebP cover/page images

The current CSS does not define `@font-face`; it uses system sans-serif and Georgia-style serif defaults despite the font files being present.

## Things To Watch When Making Changes

- This site needs to be served from a web server because it uses `fetch()`. Opening `index.html` directly as a file will not work reliably.
- `reader.html` depends on external CDNs for StPageFlip. Offline usage may fail unless the library is vendored.
- Page image format must stay consistent across:
  - `reader.html`
  - `data/magazines.json`
  - actual files in `covers/` and `pages/`
  - README instructions
  - conversion scripts
- If adding a new magazine:
  - Add PDF to `magazines/`.
  - Run the correct converter.
  - Add/update the `data/magazines.json` entry.
  - Ensure `pageCount` matches actual generated pages.
  - Fill in `data/pages/{id}.json` if accessibility/TTS text is desired.

## Likely Next Cleanup Tasks

1. Test reader performance on GitHub Pages/mobile connections.
2. Confirm whether 300 DPI / q82 remains the preferred quality-size tradeoff.
3. Consider removing temporary lossy-test entries after comparison is complete.
4. Remove or ignore accidental empty directories after confirmation.
5. Consider removing `scripts/generate-jpg.py` if JPG is no longer supported.
6. Consider vendoring StPageFlip if offline/no-CDN reliability matters.
