#!/usr/bin/env bash
# PreToolUse hook — Session log enforcer
#
# Fires before every git commit. Ensures a narrative JSONL entry
# exists for the current session since the last commit.
#
# The JSONL file lives at ~/.claude/session-logs/<project-slug>.jsonl
# and is written by Claude per the CLAUDE.md session log protocol.
#
# Test:
#   echo '{"session_id":"test","tool_name":"Bash","tool_input":{"command":"git commit -m \"test [#1]\""}}' \
#     | bash hooks/pre-commit-session-log.sh

# ── Input parsing ─────────────────────────────────────────────────────────────

extract_fields() {
    local input="$1"
    if command -v jq &>/dev/null; then
        COMMAND=$(echo "$input" | jq -r '.tool_input.command // ""')
        SESSION_ID=$(echo "$input" | jq -r '.session_id // ""')
    else
        COMMAND=$(echo "$input" | python3 -c \
            "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('command',''))" \
            2>/dev/null || echo "")
        SESSION_ID=$(echo "$input" | python3 -c \
            "import sys,json; d=json.load(sys.stdin); print(d.get('session_id',''))" \
            2>/dev/null || echo "")
    fi
}

# ── Guards ────────────────────────────────────────────────────────────────────

is_git_commit() {
    echo "$1" | grep -qE 'git\s+commit'
}

has_bypass_token() {
    echo "$1" | grep -qF '[skip-log]'
}

# ── Project slug ──────────────────────────────────────────────────────────────

derive_project_slug() {
    local remote_url
    remote_url=$(git remote get-url origin 2>/dev/null)
    if [ -n "$remote_url" ]; then
        # Strip trailing .git, extract org/repo, replace / with -
        echo "$remote_url" \
            | sed 's|\.git$||' \
            | sed 's|.*[:/]\([^/]*/[^/]*\)$|\1|' \
            | sed 's|/|-|g'
    else
        basename "$(pwd)"
    fi
}

# ── Deny helper ───────────────────────────────────────────────────────────────

deny() {
    local reason="$1"
    if command -v jq &>/dev/null; then
        jq -Rn --arg reason "$reason" \
            '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":$reason}}'
    else
        python3 -c "import json,sys; print(json.dumps({'hookSpecificOutput':{'hookEventName':'PreToolUse','permissionDecision':'deny','permissionDecisionReason':sys.argv[1]}}))" "$reason" 2>/dev/null \
            || printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"%s"}}\n' \
                "$(echo "$reason" | sed 's/"/\\"/g')"
    fi
    exit 2
}

# ── Timestamp helpers ─────────────────────────────────────────────────────────

to_epoch() {
    local ts="$1"
    date -d "$ts" +%s 2>/dev/null || echo "0"
}

# ── Main ──────────────────────────────────────────────────────────────────────

main() {
    local input
    input=$(cat)

    local COMMAND SESSION_ID
    extract_fields "$input"

    # Only act on git commit commands
    is_git_commit "$COMMAND" || exit 0

    # Bypass token
    has_bypass_token "$COMMAND" && exit 0

    # Need a session ID to enforce
    if [ -z "$SESSION_ID" ]; then
        exit 0
    fi

    # Derive project slug and JSONL path
    local slug jsonl_path
    slug=$(derive_project_slug)
    jsonl_path="$HOME/.claude/session-logs/${slug}.jsonl"

    # If no JSONL file exists, deny
    if [ ! -f "$jsonl_path" ]; then
        deny "No session log found. Before committing, append a narrative JSONL entry to ${jsonl_path}. See the Session Log Entry protocol in CLAUDE.md."
    fi

    # Find the last entry for this session
    local last_entry last_entry_ts
    last_entry=$(tac "$jsonl_path" | grep -m1 "\"session\":\"${SESSION_ID}\"")

    if [ -z "$last_entry" ]; then
        deny "No session log entry found for this session. Before committing, append a narrative JSONL entry to ${jsonl_path}. See the Session Log Entry protocol in CLAUDE.md."
    fi

    # Extract timestamp from the entry
    if command -v jq &>/dev/null; then
        last_entry_ts=$(echo "$last_entry" | jq -r '.ts // ""')
    else
        last_entry_ts=$(echo "$last_entry" | python3 -c \
            "import sys,json; print(json.load(sys.stdin).get('ts',''))" 2>/dev/null || echo "")
    fi

    if [ -z "$last_entry_ts" ]; then
        deny "Session log entry is missing a timestamp. Ensure the JSONL entry has a 'ts' field in ISO-8601 format."
    fi

    # Get last commit timestamp
    local last_commit_ts
    last_commit_ts=$(git log -1 --format=%cI 2>/dev/null)

    # If no commits exist (new repo), the entry's existence is enough
    if [ -z "$last_commit_ts" ]; then
        exit 0
    fi

    # Compare: entry must be newer than or equal to the last commit
    local entry_epoch commit_epoch
    entry_epoch=$(to_epoch "$last_entry_ts")
    commit_epoch=$(to_epoch "$last_commit_ts")

    if [ "$entry_epoch" -ge "$commit_epoch" ]; then
        exit 0
    else
        deny "Session log entry is older than the last commit. Write a new narrative entry to ${jsonl_path} before committing. See the Session Log Entry protocol in CLAUDE.md."
    fi
}

main
