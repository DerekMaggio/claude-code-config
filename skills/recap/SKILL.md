---
name: recap
description: "Generate a narrative walkthrough of what changed during a session, using the session log. Use when the user says 'recap', 'walkthrough', 'what did we do', 'session summary', or 'show me what changed'."
allowed-tools: [Bash, Read, Grep, Glob, AskUserQuestion]
updated: 2026-04-07
---

# Session Recap

Generate a narrative walkthrough of changes made during a Claude Code session by reading the session log.

## Steps

### 1. Derive project slug

```bash
remote_url=$(git remote get-url origin 2>/dev/null)
if [ -n "$remote_url" ]; then
  slug=$(echo "$remote_url" | sed 's|\.git$||' | sed 's|.*[:/]\([^/]*/[^/]*\)$|\1|' | sed 's|/|-|g')
else
  slug=$(basename "$(pwd)")
fi
echo "$slug"
```

Use the slug to locate the JSONL file at `~/.claude/session-logs/<slug>.jsonl`.

### 2. Read the session log

- If the file does not exist, tell the user: "No session log found for this project. Session logs are created automatically when commits are made with the session log protocol enabled."
- If the file exists, read it.

### 3. Select the session

- If an argument was provided (e.g., `/recap abc123`), use that as the session ID filter.
- Otherwise, extract the `session` value from the **last line** of the JSONL file and use that as the filter.

### 4. Filter entries

Extract all JSONL lines where `"session"` matches the selected session ID. Parse each line as JSON.

### 5. Enrich with git data (optional)

For each entry:
- If the entry contains a `"sha"` field with an actual commit SHA (not `"pending"`), run `git show --stat <sha>` to get the diff summary.
- If the SHA is `"pending"` or missing, try to correlate with git log by matching the entry's timestamp to nearby commits.

### 6. Render the walkthrough

Output in this format:

```markdown
## Session Recap — <project> (<date range from first to last entry>)

### 1. <First line of narrative as summary heading>
**Files:** file1.py, file2.py
**Narrative:** <full narrative from log entry>

### 2. <First line of narrative as summary heading>
**Files:** file3.py
**Narrative:** <full narrative from log entry>

...

---
*<N> log entries from session `<session_id>`*
```

### 7. Offer visualization

After rendering the walkthrough, ask the user:

> "Would you like me to generate a visual diagram of these changes using `/visualize`?"
