---
description: ""
covers: []
updated: 2026-04-12
---

# Hooks

Claude Code tool hooks (`PreToolUse` and `PostToolUse`). Registered globally in `settings.json` and symlinked to `~/.claude/hooks/`.

Shared utilities live in `_hook_utils.py` and are imported by all Python hooks.

## Available Hooks

| Hook | Trigger | Description |
|---|---|---|
| `prefer-gt.py` | `PreToolUse: Bash` (all) | Self-detects raw git/gh/gt-Bash commit-producing commands and denies them; enforces gt MCP tool usage |
| `pre-commit-docs-check.py` | `PreToolUse: Bash\|mcp__graphite__run_gt_cmd` (commit-producing) | Enforces documentation review before every commit |
| `pre-commit-conventional-commit.py` | `PreToolUse: Bash\|mcp__graphite__run_gt_cmd` (commit-producing) | Validates conventional commit format and requires a ticket reference |
| `post-md-frontmatter.sh` | `PostToolUse: Write\|Edit` (.md files) | Updates or inserts frontmatter `updated` date on markdown writes |

---

## prefer-gt

Registered as a single entry on `PreToolUse: Bash` (no `if` filter). The script reads the bash command and self-detects which commit-producing operation it represents by matching each pattern at a shell-command boundary (start of line, or after `;`, `&&`, `||`, `|`, `(`, `$(`). This avoids false positives from patterns appearing inside string literals or unrelated subcommands (e.g. `git log`, `echo "git commit is a word"`).

| Detected command | Preferred alternative |
|---|---|
| `git commit` | `mcp__graphite__run_gt_cmd` with `["create", "--all", "-m", "…"]` |
| `git push` | `mcp__graphite__run_gt_cmd` with `["submit", "--no-interactive"]` |
| `gh pr create` | `mcp__graphite__run_gt_cmd` with `["submit", "--no-interactive"]` |
| `gh pr merge` | Merge via graphite web UI or merge-when-ready |
| Bash `gt create/modify/submit` | `mcp__graphite__run_gt_cmd` (structured args avoid shell-quoting issues) |

**Bypass:** include `[raw-git]` anywhere in the command for intentional raw-git use (recovery, setup).

### Test

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"git commit -m \"test\""}}' \
  | python3 ~/.claude/hooks/prefer-gt.py
```

---

## pre-commit-docs-check

Fires before any commit-producing call (`git commit`, `gt create`, `gt modify`) via Bash or the graphite MCP tool. Requires either the configured doc file to be staged or the bypass token in the commit message.

Projects opt in by creating `.claude/docs-check.json` at the repo root:

```json
{
  "doc_file": "README.md",
  "bypass_token": "[docs-ok]",
  "safe_pattern": "^(README\\.md|docs/|\\.claude/|\\.gitignore)",
  "custom_instructions": "Update the changelog section before committing."
}
```

- **`doc_file`** — path to the doc that must be reviewed (required)
- **`bypass_token`** — commit message phrase to skip the check (default: `[docs-ok]`)
- **`safe_pattern`** — regex; commits touching only matching files skip the check (optional)
- **`custom_instructions`** — replaces the default "Review doc_file" prompt with custom text (optional)

If `.claude/` exists but no `docs-check.json` is found, the hook scans the repo for candidate doc files and prompts to create the config. Projects without a `.claude/` directory are silently skipped.

### Test

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"git commit -m \"feat: thing [#1]\""}}' \
  | python3 ~/.claude/hooks/pre-commit-docs-check.py

echo '{"tool_name":"mcp__graphite__run_gt_cmd","tool_input":{"args":["create","-m","feat: thing [#1]"]}}' \
  | python3 ~/.claude/hooks/pre-commit-docs-check.py
```

---

## pre-commit-conventional-commit

Fires before any commit-producing call via Bash or the graphite MCP tool. Validates the subject line against the [Conventional Commits](https://www.conventionalcommits.org/) spec and requires a ticket reference.

**Expected format:** `type(optional-scope): description [TICKET-ID]`

**Allowed types:** `build`, `chore`, `ci`, `docs`, `feat`, `fix`, `perf`, `refactor`, `style`, `test`

**Scope-sensitive misuse prevention:** types like `ci`, `docs`, `style`, `test`, `perf`, `build` are standalone — using them as a scope of `feat` or `fix` (e.g. `feat(ci):`) is rejected.

### Test

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"git commit -m \"feat(api): add endpoint [#7]\""}}' \
  | python3 ~/.claude/hooks/pre-commit-conventional-commit.py

echo '{"tool_name":"mcp__graphite__run_gt_cmd","tool_input":{"args":["create","-m","feat(api): add endpoint [#7]"]}}' \
  | python3 ~/.claude/hooks/pre-commit-conventional-commit.py
```
