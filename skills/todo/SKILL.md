---
name: todo
description: >-
  Manage a personal task list stored as a pinned GitHub Issue in DerekMaggio/tasks.
  Add, complete, remove, and list tasks with High/Normal priority and optional due dates.
allowed-tools: [mcp__github__get_issue, mcp__github__update_issue]
updated: 2026-04-01
---

# Todo — Personal Task List

## 1. Purpose
A simple, cross-platform task list backed by a pinned GitHub Issue (`DerekMaggio/tasks#1`).
Tasks are markdown checkboxes grouped by priority (High / Normal) with optional due dates.

## 2. Trigger

### Slash Commands
- `/todo` or `/todo list` — display the current task list
- `/todo add <task>` — add a Normal priority task
- `/todo add! <task>` — add a High priority task
- `/todo done <number>` — mark task #N as complete
- `/todo remove <number>` — remove task #N

### Due Dates
Append a date/time naturally — the skill parses it into `[due: YYYY-MM-DD]` or `[due: YYYY-MM-DD HH:MM]`:
- `/todo add Fix deploy script by Friday` → `- [ ] Fix deploy script [due: 2026-04-03]`
- `/todo add! Call Alex tomorrow at 2pm` → `- [ ] Call Alex [due: 2026-04-02 14:00]`

Always convert relative dates to absolute dates using today's date from context.

### Natural Language (auto-detected)
- "remind me to ...", "I need to ...", "add to my list ..." → add task
- "what's on my list?", "what do I need to do?" → list tasks
- "done with N", "finished N" → complete task

## 3. Constants
- **Owner:** `DerekMaggio`
- **Repo:** `tasks`
- **Issue Number:** `1`

## 4. Issue Body Format

```markdown
# Task List

## High Priority
- [ ] Task description [due: 2026-04-05]
- [ ] Task with no date

## Normal
- [ ] Another task [due: 2026-04-10 09:00]
- [x] Completed task
```

Rules:
- High Priority tasks under `## High Priority`, normal under `## Normal`
- `- [x]` = done, `- [ ]` = open
- `[due: ...]` suffix is optional
- Empty sections keep their headers

## 5. Workflow

### Fetch
Call `mcp__github__get_issue` with owner `DerekMaggio`, repo `tasks`, issue_number `1`. Parse the `body`.

### Parse
Each task line: `^- \[([ x])\] (.+?)(?:\s*\[due: (.+?)\])?$`
- Group 1: status
- Group 2: description
- Group 3: due date (optional)

Number tasks sequentially: High Priority first, then Normal.

### Commands

**list**: Display tasks grouped by priority with numbers. Flag overdue tasks with `⚠️ OVERDUE`. If empty: "Your task list is empty."

**add / add!**: Parse due date from natural language if present. Append `- [ ] <task>` (with `[due: ...]` if applicable) to the correct section. Update issue and confirm.

**done N**: Change `- [ ]` to `- [x]` at position N. Update issue and confirm. Out of range → "Task #N not found."

**remove N**: Delete the line at position N. Update issue and confirm. Out of range → "Task #N not found."

### Update
Call `mcp__github__update_issue` with the reconstructed body. Always fetch latest state before writing.

## 6. Constraints
- Never close the issue.
- Never auto-remove completed tasks.
- List is read-only (no writes).
- Fetch before every write to avoid overwrites.

## 7. Errors
- **404:** "Task list issue not found. Would you like me to recreate it?"
- **API error:** Show the error, don't retry.
- **Malformed body:** Show raw body, ask user how to proceed.
