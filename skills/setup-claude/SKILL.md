---
name: setup-claude
description: Run the claude-code-config setup script and display a summary of available skills, agents, and hooks. Use when setting up a new machine, refreshing the Claude Code environment after pulling changes, or any time a change is made to this repo (new skill, agent, hook, or config update).
allowed-tools: Bash, Read, Glob
updated: 2026-03-21
---

# Setup Claude

Runs the setup script, then presents a complete summary of what's available in this Claude Code config.

## Step 1 — Run Setup

Locate the repo and run the setup script:

```bash
REPO_ROOT=$(find ~ -maxdepth 2 -type d -name "claude-code-config" 2>/dev/null | head -1)
bash "$REPO_ROOT/setup.sh" --skip-optional
```

## Step 2 — Present Summary

After setup completes, read the source files, extract the data, and **construct the tables yourself** with proper column alignment. Do not copy-paste raw README content.

**Skills** — read `/home/derek-maggio/claude-code-config/skills/README.md` and extract each skill name and description.

**Agents** — resolve the repo root and read the agents README:
```bash
REPO_ROOT=$(find ~ -maxdepth 2 -type d -name "claude-code-config" 2>/dev/null | head -1)
cat "$REPO_ROOT/agents/README.md"
```
Extract each agent name, description, and group (Project Management, Python, Testing, Utility, Private).

**Hooks** — read `~/.claude/hooks/README.md` and extract each hook name, trigger, and description.

Using the extracted data, build and render clean, well-aligned markdown tables. Use this structure:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 Claude Code Config — What's Available
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SKILLS  (invoke with /skill-name)
[well-aligned two-column table: Skill | Description]

AGENTS  (available automatically in all sessions)
[grouped sections, each with a well-aligned two-column table: Agent | Description]

HOOKS   (run automatically by the harness)
[well-aligned three-column table: Hook | Trigger | Description]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Step 3 — Restart Reminder

Always end with this message, formatted prominently:

```
IMPORTANT: Close and reopen your Claude Code session to activate any
newly registered MCP servers, updated symlinks, or hook changes.
```
