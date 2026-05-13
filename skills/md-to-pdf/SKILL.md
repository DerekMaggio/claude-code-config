---
name: md-to-pdf
description: Convert a markdown file to a styled PDF with working clickable hyperlinks. Use whenever the user asks to "export this to PDF", "save as PDF", "make a PDF of this markdown", "convert .md to .pdf", or wants a sharable PDF version of a markdown document (summaries, reports, notes). The output uses a GitHub-style stylesheet (sans-serif body, blue underlined links, gray-bordered blockquotes, bordered headings) and preserves all hyperlinks as live, clickable PDF link annotations.
allowed-tools: [Bash]
updated: 2026-05-13
---

# md-to-pdf

Convert a markdown file to a styled PDF where hyperlinks remain blue, underlined, and clickable.

## Pipeline

```
markdown → pandoc → HTML (CSS embedded) → Chrome headless --print-to-pdf → PDF
```

Chrome's print-to-PDF preserves `<a href>` as native PDF link annotations. Pandoc's `--embed-resources` inlines the CSS so the intermediate HTML is self-contained.

## How to invoke

Run the bundled script:

```bash
~/.claude/skills/md-to-pdf/scripts/md-to-pdf.sh <input.md> [output.pdf]
```

If `output.pdf` is omitted, it defaults to the input path with the extension swapped (`foo.md` → `foo.pdf`) in the same directory.

## Dependencies (Linux)

- `pandoc` (`sudo apt install pandoc`)
- `google-chrome` or `chromium` / `chromium-browser` on PATH
- The bundled stylesheet at `assets/github-style.css`

The script auto-detects whichever Chrome binary is installed and errors clearly if pandoc or Chrome is missing.

## What the script does

1. Resolves the output path (defaulting alongside the input).
2. Renders markdown → standalone HTML via pandoc, embedding `assets/github-style.css` inline.
3. Calls Chrome headless: `--headless --disable-gpu --no-sandbox --no-pdf-header-footer --print-to-pdf=<output>`.
4. Cleans up the temp HTML.

## Stylesheet

`assets/github-style.css` is GitHub-flavored: sans-serif body at 11pt, blue (`#0969da`) underlined links, gray-bordered blockquotes with `#f6f8fa` background, h1/h2 with bottom border, monospace inline code with `#f6f8fa` background, 0.75in page margins, bordered tables.

If the user wants a different style (different font, narrower margins, dark theme, etc.), edit `assets/github-style.css` — the script always uses that file.

## Why these choices

- **Chrome headless over wkhtmltopdf / weasyprint**: Chrome is already installed on most dev machines, has the most reliable CSS support, and produces clickable PDF links by default. wkhtmltopdf is unmaintained; weasyprint requires extra Python deps.
- **`--embed-resources` on pandoc**: makes the HTML self-contained so Chrome doesn't need a working directory context to find the CSS.
- **`--no-pdf-header-footer`**: removes Chrome's default URL/timestamp header and page-number footer that nobody wants in a finished doc.

## After generating

Tell the user the absolute output path. Don't open the PDF (the user is on Linux without a guaranteed default PDF viewer in this context).
