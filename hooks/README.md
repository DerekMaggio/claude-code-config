---
description: ""
covers: []
updated: 2026-05-23
---

# Hooks

Claude Code tool hooks (`PreToolUse` and `PostToolUse`). Registered globally in `settings.json` and symlinked to `~/.claude/hooks/`.

Shared utilities live in `_hook_utils.py` and are imported by all Python hooks.

## Available Hooks

| Hook | Trigger | Description |
|---|---|---|
| `pre-commit-docs-check.py` | `PreToolUse: Bash` (commit-producing) | Enforces documentation review before every commit |
| `pre-commit-conventional-commit.py` | `PreToolUse: Bash` (commit-producing) | Validates conventional commit format and requires a ticket reference |
| `post-md-frontmatter.sh` | `PostToolUse: Write\|Edit` (.md files) | Updates or inserts frontmatter `updated` date on markdown writes |

---

## pre-commit-docs-check

Fires before any commit-producing call (`git commit`) via Bash. Requires either the configured doc file to be staged or the bypass token in the commit message.

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
```

---

## pre-commit-conventional-commit

Fires before any commit-producing call via Bash. Validates the subject line against the [Conventional Commits](https://www.conventionalcommits.org/) spec and requires a ticket reference.

**Expected format:** `type(optional-scope): description [TICKET-ID]`

**Allowed types:** `build`, `chore`, `ci`, `docs`, `feat`, `fix`, `perf`, `refactor`, `style`, `test`

**Scope-sensitive misuse prevention:** types like `ci`, `docs`, `style`, `test`, `perf`, `build` are standalone — using them as a scope of `feat` or `fix` (e.g. `feat(ci):`) is rejected.

### Test

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"git commit -m \"feat(api): add endpoint [#7]\""}}' \
  | python3 ~/.claude/hooks/pre-commit-conventional-commit.py
```
