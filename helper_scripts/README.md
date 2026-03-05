# Helper Scripts

Utility scripts for maintaining the claude-code-config repo and Claude Code setup.

## Scripts

| Script | Description |
|---|---|
| `update_symlinks.sh` | Symlinks all config, skills, agents, hooks, and MCP servers from this repo to `~/.claude/` |
| `inject_devops_config.sh` | Injected on every `UserPromptSubmit` — loads `devops.json` into the session context |
| `analyze_claude_history.py` | Parses Claude Code session history for analysis |
| `generate_markdown_report.py` | Generates markdown reports from session/history data |

## update_symlinks.sh

The primary setup script. Run after cloning or adding new skills/agents/hooks:

```bash
bash helper_scripts/update_symlinks.sh
```

Creates symlinks in `~/.claude/` for:
- `settings.json`, `CLAUDE.md`, `statusline-command.sh`, `.mcp.json`
- `agents/` subdirectories
- `skills/` subdirectories
- `hooks/` directory
- `inject_devops_config.sh`
- `config/devops.json` (if present)

Also registers user-scoped MCP servers (`gemini-bridge`, `pr-index`) via `claude mcp add`.

## inject_devops_config.sh

Hooked into every session via `UserPromptSubmit`. Reads `~/.claude/devops.json` and injects its contents as context so Claude always has access to org-specific config (Jira IDs, Salesforce org, vault paths, etc.) without it being hardcoded in prompts.
