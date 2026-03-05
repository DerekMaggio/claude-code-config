# Hooks

Claude Code `PreToolUse` hooks. Registered globally in `settings.json` and symlinked to `~/.claude/hooks/`.

## Available Hooks

| Hook | Trigger | Description |
|---|---|---|
| `pre-commit-docs-check.sh` | `PreToolUse: Bash` (git commit) | Enforces documentation review before every commit |

## pre-commit-docs-check

Fires before any `git commit` command. Requires either the configured doc file to be staged or `[docs-ok]` in the commit message.

Projects opt in by creating `.claude/docs-check.json` at the repo root:

```json
{
  "doc_file": "README.md",
  "bypass_token": "[docs-ok]",
  "safe_pattern": "^(README\\.md|docs/|\\.claude/|\\.gitignore)"
}
```

- **`doc_file`** — path to the doc that must be reviewed (required)
- **`bypass_token`** — commit message phrase to skip the check (default: `[docs-ok]`)
- **`safe_pattern`** — regex; commits touching only matching files skip the check (optional)

If `.claude/` exists but no `docs-check.json` is found, the hook scans the repo for candidate doc files and prompts to create the config. Projects without a `.claude/` directory are silently skipped.

### Test

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"git commit -m test"}}' \
  | bash ~/.claude/hooks/pre-commit-docs-check.sh
```
