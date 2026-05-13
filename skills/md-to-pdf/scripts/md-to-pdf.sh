#!/usr/bin/env bash
# md-to-pdf: Convert a markdown file to a styled PDF with clickable hyperlinks.
# Usage: md-to-pdf.sh <input.md> [output.pdf]
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <input.md> [output.pdf]" >&2
  exit 1
fi

INPUT="$1"
OUTPUT="${2:-${INPUT%.md}.pdf}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CSS="${SCRIPT_DIR}/../assets/github-style.css"

if [[ ! -f "$INPUT" ]]; then
  echo "Input file not found: $INPUT" >&2
  exit 1
fi
if [[ ! -f "$CSS" ]]; then
  echo "Stylesheet not found: $CSS" >&2
  exit 1
fi

command -v pandoc >/dev/null || { echo "pandoc not installed" >&2; exit 1; }

CHROME=""
for candidate in google-chrome chromium chromium-browser google-chrome-stable; do
  if command -v "$candidate" >/dev/null; then
    CHROME="$candidate"
    break
  fi
done
[[ -z "$CHROME" ]] && { echo "No Chrome/Chromium binary found" >&2; exit 1; }

TMP_HTML="$(mktemp --suffix=.html)"
trap 'rm -f "$TMP_HTML"' EXIT

pandoc "$INPUT" -o "$TMP_HTML" --standalone -c "$CSS" --embed-resources

"$CHROME" \
  --headless \
  --disable-gpu \
  --no-sandbox \
  --no-pdf-header-footer \
  --print-to-pdf="$OUTPUT" \
  "file://$TMP_HTML" 2>/dev/null

echo "Wrote $OUTPUT"
