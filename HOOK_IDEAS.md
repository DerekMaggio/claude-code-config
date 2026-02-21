# Hook Ideas Log

Candidate hooks for enforcing deterministic behavior in Claude Code sessions.
Each entry tracks the idea, its feasibility, enforcement tier, and status.

**Enforcement Tiers:**
- **Tier 1 (Deterministic):** Shell script with exit codes / `permissionDecision: deny`. Tool call is physically blocked. 100% reliable.
- **Tier 2 (Probabilistic):** `prompt` or `agent` hook that asks an LLM to evaluate. ~90% reliable.
- **Tier 3 (Prose):** CLAUDE.md instruction only. ~70-80% reliable.

---

## Pattern: Skill Router

The highest-value hook pattern in this repo. The idea: **block raw tool access and redirect the agent to the structured skill/agent/MCP tool that wraps it.**

### Why This Matters

Skills and agents encode institutional knowledge — validation steps, safety checks, approval gates, field mappings, error recovery. When the main agent bypasses a skill and uses raw tools directly, it skips all of that. A `PreToolUse` hook can make skill usage mandatory rather than optional.

### The Pattern

```
Raw Tool (blocked by hook)
    ↓ deny + reason
"Use /skill-name instead"
    ↓
Skill (structured workflow with gates, validation, error handling)
    ↓
MCP Tool / Script (the actual operation)
```

### Routing Table

This table maps raw operations to the skills that should own them.

| Raw Operation | Blocked Pattern | Redirect To | Tier | Status |
|:--------------|:---------------|:------------|:-----|:-------|
| `gh run *`, `gh workflow *` | `\bgh\s+(run\|workflow)\b` | `/gha-run`, `/gha-analyze` | 1 | Proposed |
| `gh pr create` | `\bgh\s+pr\s+create\b` | `/pr-generator` | 1 | Proposed |
| `git tag`, `git push --tags` | `\bgit\s+tag\b`, `git push.*--tags` | `/named-build-tagging` | 1 | Proposed |
| Direct Jira API via `curl` | `\bcurl.*atlassian.net\b` | `devops-task-creator` / `devops-task-retriever` skills | 1 | Idea |
| Direct Salesforce `sf` commands | `\bsf\s+(data\|org\|sobject)\b` | `/monthly-customer-scheduling` | 1 | Idea |
| Direct `gh api /orgs/.*/copilot` | `\bgh\s+api.*/copilot\b` | `/copilot-usage-report` | 1 | Idea |

### Implementation: Unified Skill Router Hook

Rather than N separate hook scripts, a single router script with a config table:

```bash
#!/bin/bash
# enforce-skill-router.sh (PreToolUse on Bash)
INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

# Routing rules: pattern -> skill name -> reason
declare -A ROUTES
ROUTES["gh (run|workflow)"]="/gha-run or /gha-analyze|GitHub Actions operations must go through the gha-run/gha-analyze skills which use MCP tools for structured data."
ROUTES["gh pr create"]="/pr-generator|PR creation must go through the pr-generator skill which enforces title approval, template filling, and explicit consent."
ROUTES["git tag|git push.*--tags"]="/named-build-tagging|Tag operations must go through the named-build-tagging skill which enforces validation, dry-run, and rollback safety."

for pattern in "${!ROUTES[@]}"; do
  if echo "$COMMAND" | grep -qE "$pattern"; then
    IFS='|' read -r skill reason <<< "${ROUTES[$pattern]}"
    cat <<DENY
{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"Blocked: $reason Use $skill instead."}}
DENY
    exit 0
  fi
done

exit 0
```

### Open Questions

1. **Skill context detection:** Can we detect whether a command is being run *inside* a skill vs. from the main agent? If yes, we could allow the skill itself to use raw tools while blocking the main agent. Currently hooks fire regardless of context — the `matcher` only matches tool name, not caller.

2. **MCP tool routing:** Can we block MCP tools too? E.g., block `mcp__atlassian__create_issue` from the main agent and require it to go through `devops-task-creator`? The matcher supports `mcp__atlassian__.*` patterns, but the same skill-context problem applies — the skill itself needs to call the MCP tool.

3. **Escape hatch:** Should there be a way to bypass the router for power users? E.g., a `--force` flag or environment variable. Risk: defeats the purpose. Alternative: require the user to explicitly approve via the permission prompt (`permissionDecision: "ask"` instead of `"deny"`).

---

## Idea Log

### ID-001: Enforce GHA Skills
- **Block:** `gh run *`, `gh workflow *` in Bash
- **Redirect:** `/gha-run`, `/gha-analyze`
- **Tier:** 1
- **Rationale:** `gha-run` uses MCP tools for structured data, handles polling, and auto-invokes `gha-analyze` on failure. `ansible-test-bed-loop` already mandates "never use gh CLI." This makes it universal.
- **Status:** Proposed

### ID-002: Enforce PR Generator
- **Block:** `gh pr create` in Bash
- **Redirect:** `/pr-generator`
- **Tier:** 1
- **Rationale:** `pr-generator` enforces title approval, template filling, JIRA linking, and explicit consent gate. Raw `gh pr create` skips all of this.
- **Status:** Proposed

### ID-003: Enforce Named Build Tagging Scripts
- **Block:** Raw `git tag`, `git push --tags` in Bash
- **Redirect:** `/named-build-tagging`
- **Tier:** 1
- **Rationale:** The skill already says "HIGHEST PRIORITY DIRECTIVE: ONLY use scripts from scripts/ directory." This makes it enforceable rather than aspirational.
- **Status:** Proposed

### ID-004: Git Commit Format Enforcement
- **Block:** `git commit` where message doesn't match `<type>(<scope>): desc [TICKET-ID]`
- **Redirect:** N/A (just enforce format)
- **Tier:** 1
- **Rationale:** CLAUDE.md §2 defines the format. A regex check on the `-m` argument catches violations before the commit happens.
- **Edge cases:** Heredoc commit messages, `git commit` without `-m` (opens editor — not applicable in Claude Code).
- **Status:** Proposed

### ID-005: Force Push Protection
- **Block:** `git push --force`, `git push -f`
- **Redirect:** N/A (just block)
- **Tier:** 1
- **Rationale:** Destructive operation. Already in Claude Code's system prompt but worth hardening.
- **Status:** Proposed

### ID-006: Post-Edit Syntax Validation
- **Event:** `PostToolUse` on `Edit|Write`
- **Action:** Run `python3 -m py_compile` / `bash -n` / `yq eval` depending on file extension
- **Tier:** 1
- **Rationale:** `sonarqube-fixer` does this manually. Making it automatic catches syntax breaks from any skill or the main agent.
- **Status:** Proposed

### ID-007: Session State Machine (Mode Gates)
- **Block:** All tools before mode selection confirmed; write tools before work approved
- **Mechanism:** State file + `UserPromptSubmit` detector + `PreToolUse` guard
- **Tier:** 1 (mechanical) but fragile (user message parsing is heuristic)
- **Rationale:** CLAUDE.md §0 and §1 define hard gates. Currently pure prose.
- **Risk:** False positives on user message parsing. A user saying "yes" to something unrelated could advance the state machine. Mitigation: require specific phrases or use a `prompt` hook for intent detection (drops to Tier 2).
- **Status:** Needs design

### ID-008: DoD Verification at Stop
- **Event:** `Stop`
- **Action:** `prompt` hook checks whether all acceptance criteria were addressed
- **Tier:** 2
- **Rationale:** Catches premature session endings where work was incomplete.
- **Risk:** LLM evaluation may miss items or hallucinate verification.
- **Status:** Idea

### ID-009: Copilot Report Skill Enforcement
- **Block:** `gh api .*/copilot` in Bash
- **Redirect:** `/copilot-usage-report`
- **Tier:** 1
- **Rationale:** The skill handles path resolution, report building via Python script, and vault saving. Raw API calls skip all of that.
- **Status:** Idea

### ID-010: Salesforce CLI Enforcement
- **Block:** `sf data`, `sf org`, `sf sobject` in Bash (outside of skill helper scripts)
- **Redirect:** `/monthly-customer-scheduling`
- **Tier:** 1
- **Rationale:** Salesforce operations have complex field mappings and timezone calculations. The skill encodes all of this.
- **Caveat:** The skill's own helper script (`fetch_maintenance_data.sh`) uses `sf` directly. Need skill-context detection or whitelist the specific script path.
- **Status:** Idea

### ID-011: Protected File Guard
- **Event:** `PreToolUse` on `Edit|Write`
- **Block:** Writes to `.env`, `devops.json`, `settings.json`, `*.key`, `*.pem`
- **Tier:** 1
- **Rationale:** Prevent accidental credential/config overwrites.
- **Status:** Idea

### ID-012: Jira Direct API Bypass Prevention
- **Block:** `curl` commands targeting `*.atlassian.net` in Bash
- **Redirect:** `devops-task-creator` / `devops-task-retriever` skills
- **Tier:** 1
- **Rationale:** Skills handle ADF formatting, customer field resolution, and error handling. Raw curl skips all of this.
- **Status:** Idea
