#!/usr/bin/env bash
# PostToolUse hook — Keep frontmatter current on .md file writes/edits.
#
# If the modified file has frontmatter, updates the `updated` field to today.
# If the modified file has no frontmatter, inserts a blank template and
# instructs Claude to fill in the semantic fields before continuing.
#
# Fires on Write and Edit tool calls only.

extract_file_path() {
    local input="$1"
    if command -v jq &>/dev/null; then
        echo "$input" | jq -r '.tool_input.file_path // ""'
    else
        echo "$input" | python3 -c \
            "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('file_path',''))" \
            2>/dev/null || echo ""
    fi
}

main() {
    local input file_path today
    input=$(cat)
    file_path=$(extract_file_path "$input")

    # Only process .md files that exist
    [[ "$file_path" == *.md ]] || exit 0
    [ -f "$file_path" ] || exit 0

    # Skip auto-generated files
    head -3 "$file_path" | grep -q "Do not edit by hand" && exit 0

    today=$(date +%Y-%m-%d)

    if head -1 "$file_path" | grep -q "^---$"; then
        # Has frontmatter — update the `updated` field silently
        sed -i "s/^updated: .*/updated: $today/" "$file_path"
    else
        # No frontmatter — prepend a blank template
        local tmp
        tmp=$(mktemp)
        cat > "$tmp" <<EOF
---
description: ""
covers: []
updated: $today
---

EOF
        cat "$file_path" >> "$tmp"
        mv "$tmp" "$file_path"

        # Instruct Claude to fill in the semantic fields
        echo "FRONTMATTER ADDED to $file_path"
        echo ""
        echo "Fill in the frontmatter fields before continuing:"
        echo ""
        echo "  description: A single sentence summarising what this document covers."
        echo "               Write it for someone scanning the doc index deciding whether to open the file."
        echo ""
        echo "  covers:      List the file or directory paths (relative to repo root) that this"
        echo "               document describes. Used by the commit hook to identify which docs"
        echo "               need updating when those files change. Use a directory path (e.g."
        echo "               pr_index/search/) when the doc covers a whole package, or specific"
        echo "               file paths when it covers individual files. Leave empty ([]) for"
        echo "               conceptual or reference docs with no direct code counterpart."
    fi
}

main
