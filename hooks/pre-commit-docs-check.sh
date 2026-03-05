#!/usr/bin/env bash
# PreToolUse hook — Documentation freshness check
#
# Fires before every git commit. Reads project-level config from
# .claude/docs-check.json in the project root.
#
# If .claude/ exists but no docs-check.json is found, scans the repo for
# candidate doc files and prompts Claude to create the config.
# If no .claude/ directory exists, silently skips.
#
# Project config (.claude/docs-check.json):
# {
#   "doc_file":      "MAINTENANCE_NOTES.md",
#   "bypass_token":  "[docs-ok]",
#   "safe_pattern":  "^(MAINTENANCE_NOTES\\.md|CLAUDE\\.md|\\.claude/)"
# }
#
# Test:
#   echo '{"tool_name":"Bash","tool_input":{"command":"git commit -m test"}}' | bash hooks/pre-commit-docs-check.sh

# ── Input parsing ─────────────────────────────────────────────────────────────

extract_command() {
    local input="$1"
    if command -v jq &>/dev/null; then
        echo "$input" | jq -r '.tool_input.command // ""'
    else
        echo "$input" | python3 -c \
            "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('command',''))" \
            2>/dev/null || echo ""
    fi
}

# ── Guards ────────────────────────────────────────────────────────────────────

is_git_commit() {
    echo "$1" | grep -qE 'git\s+commit'
}

block_combined_add_commit() {
    local cmd_stripped
    cmd_stripped=$(echo "$1" | sed 's/-m.*//')
    if echo "$cmd_stripped" | grep -qE 'git\s+add.*&&.*git\s+commit'; then
        echo "HOOK ERROR: Do not combine 'git add' and 'git commit' in one command." >&2
        echo "Run 'git add' first, then 'git commit' separately so this hook can" >&2
        echo "inspect the correct staged file list." >&2
        return 2
    fi
}

# ── Config ────────────────────────────────────────────────────────────────────

read_config() {
    local config_file="$1"
    if command -v jq &>/dev/null; then
        DOC_FILE=$(jq -r '.doc_file // ""' "$config_file")
        BYPASS_TOKEN=$(jq -r '.bypass_token // "[docs-ok]"' "$config_file")
        SAFE_PATTERN=$(jq -r '.safe_pattern // ""' "$config_file")
    else
        DOC_FILE=$(python3 -c "import json; d=json.load(open('$config_file')); print(d.get('doc_file',''))" 2>/dev/null || echo "")
        BYPASS_TOKEN=$(python3 -c "import json; d=json.load(open('$config_file')); print(d.get('bypass_token','[docs-ok]'))" 2>/dev/null || echo "[docs-ok]")
        SAFE_PATTERN=$(python3 -c "import json; d=json.load(open('$config_file')); print(d.get('safe_pattern',''))" 2>/dev/null || echo "")
    fi
}

# ── Candidate doc finder ──────────────────────────────────────────────────────

find_doc_candidates() {
    local root="$1"

    find "$root" \
        -not \( -path "*/.git/*" -o -path "*/node_modules/*" -o -path "*/__pycache__/*" \
                -o -path "*/.venv/*" -o -path "*/dist/*" -o -path "*/build/*" \) \
        -type f -name "*.md" 2>/dev/null \
        | sed "s|$root/||" | sort

    local name
    for name in README CHANGELOG CONTRIBUTING CHANGES HISTORY NOTES MAINTAINERS AUTHORS NOTICE; do
        local f
        for f in "$root/$name" "$root/$name.txt" "$root/$name.markdown" "$root/$name.mkd"; do
            [ -f "$f" ] && echo "${f#$root/}"
        done
    done
}

prompt_create_config() {
    local root="$1"
    local candidates
    candidates=$(find_doc_candidates "$root")

    echo "DOCS CHECK — no .claude/docs-check.json found" >&2
    echo "" >&2
    echo "This project has a .claude/ directory but no docs-check config." >&2
    echo "Please create .claude/docs-check.json:" >&2
    echo "" >&2
    echo '  {' >&2
    echo '    "doc_file":     "<path relative to repo root>",  // required' >&2
    echo '    "bypass_token": "[docs-ok]",                     // optional' >&2
    echo '    "safe_pattern": "^(\\.claude/|CLAUDE\\.md)"      // optional regex' >&2
    echo '  }' >&2
    echo "" >&2
    echo "Candidate doc files found in this repo:" >&2
    if [ -n "$candidates" ]; then
        echo "$candidates" | sed 's/^/  /' >&2
    else
        echo "  (none found)" >&2
    fi
    echo "" >&2
    echo "Once created, retry the commit." >&2
}

# ── Freshness check ───────────────────────────────────────────────────────────

run_docs_check() {
    local doc_file="$1" bypass_token="$2" safe_pattern="$3" command="$4"

    local staged
    staged=$(git diff --cached --name-only 2>/dev/null || echo "")

    [ -z "$staged" ] && return 0

    local non_safe
    if [ -n "$safe_pattern" ]; then
        non_safe=$(echo "$staged" | grep -vE "$safe_pattern")
    else
        non_safe="$staged"
    fi

    [ -z "$non_safe" ] && return 0
    echo "$staged" | grep -qF "$doc_file" && return 0
    echo "$command" | grep -qF "$bypass_token" && return 0

    echo "DOCS CHECK" >&2
    echo "" >&2
    echo "Staged files:" >&2
    echo "$staged" | sed 's/^/  /' >&2
    echo "" >&2
    echo "Review $doc_file before committing." >&2
    echo "Option A: Update the doc, stage it, then retry." >&2
    echo "Option B: If no update is needed, add $bypass_token to your commit message." >&2
    return 2
}

# ── Main ──────────────────────────────────────────────────────────────────────

main() {
    local input command
    input=$(cat)
    command=$(extract_command "$input")

    is_git_commit "$command" || exit 0
    block_combined_add_commit "$command" || exit 2

    local claude_dir="${CLAUDE_PROJECT_DIR}/.claude"
    local config_file="$claude_dir/docs-check.json"

    [ -d "$claude_dir" ] || exit 0

    if [ ! -f "$config_file" ]; then
        prompt_create_config "$CLAUDE_PROJECT_DIR"
        exit 2
    fi

    local DOC_FILE BYPASS_TOKEN SAFE_PATTERN
    read_config "$config_file"
    [ -z "$DOC_FILE" ] && exit 0

    run_docs_check "$DOC_FILE" "$BYPASS_TOKEN" "$SAFE_PATTERN" "$command"
    exit $?
}

main
