# Hook Ideas Log

Candidate hooks for enforcing deterministic behavior in Claude Code sessions.
Each entry tracks the idea, its feasibility, enforcement tier, and status.

**Enforcement Tiers:**
- **Tier 1 (Deterministic):** Shell script with exit codes / `permissionDecision: deny`. Tool call is physically blocked. 100% reliable.
- **Tier 2 (Probabilistic):** `prompt` or `agent` hook that asks an LLM to evaluate. ~90% reliable.
- **Tier 3 (Prose):** CLAUDE.md instruction only. ~70-80% reliable.

---

## Hook Events Reference

All available hook events and their primary use cases. Implementation should target the events that match the enforcement goal.

| Event | When It Fires | Can Block? | Best For |
|:------|:-------------|:-----------|:---------|
| `SessionStart` | Session begins or resumes | No | Context injection, env setup, memory loading |
| `UserPromptSubmit` | Before Claude processes a user prompt | Yes (modify/block) | Prompt validation, auto-context injection, state machine advancement |
| `PreToolUse` | Before any tool executes | Yes (deny) | Security gates, skill routing, permission overrides |
| `PostToolUse` | After tool succeeds | No | Formatting, logging, syntax validation, side effects |
| `PostToolUseFailure` | After tool fails | No | Error handling, retry logic, alerts |
| `Stop` | Claude finishes responding | Yes (continue) | Quality gates, multi-criteria validation, DoD checks |
| `Notification` | Claude needs attention | No | Desktop alerts, Slack/webhook pings |
| `SubagentStart` | Subagent spawns | No | Context injection for subagents |
| `SubagentStop` | Subagent finishes | No | Quality gates, result validation |
| `PreCompact` | Before context compaction | No | Re-inject critical rules before context cleanup |
| `SessionEnd` | Session terminates | No | Cleanup, analytics, state preservation |

**Matchers** (filter when a hook fires):
- `tool_name`: Regex matching tool name — `Bash`, `Edit|Write`, `mcp__github__.*`
- Notification type: `permission_prompt`, `idle_prompt`

---

## Hook Handler Types

Three execution models, each with different tradeoffs:

| Type | How It Works | Latency | Best For |
|:-----|:-------------|:--------|:---------|
| `command` | Runs a shell script. Reads JSON from stdin, writes JSON to stdout. Exit codes control behavior. | ~5ms | Deterministic rules, regex matching, known patterns |
| `prompt` | Single LLM call with structured JSON response. No tool access. | ~1-2s | Judgment-based decisions, ambiguous cases, intent detection |
| `agent` | Full subagent with Read, Grep, Glob, Bash tools. Multi-turn (up to 50 turns). | ~5-30s | Complex verification requiring file inspection, multi-criteria checks |

**Async execution:** Any hook can set `"async": true` to run in the background without blocking Claude. Useful for test suites, notifications, logging.

**Input format** (received via stdin for command hooks, or as context for prompt/agent hooks):
```json
{
  "session_id": "abc123",
  "cwd": "/project/root",
  "hook_event_name": "PreToolUse",
  "tool_name": "Bash",
  "tool_input": {"command": "gh pr create --title 'foo'"},
  "permission_mode": "default"
}
```

**Output format** (for PreToolUse command hooks):
```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Use /pr-generator skill instead."
  }
}
```

**Decision values:** `"allow"`, `"deny"`, or `"ask"` (falls through to user permission prompt).

---

## Configuration Scopes

Hooks can be defined at multiple levels. Implementation should go in the appropriate scope:

| Scope | File | Use Case |
|:------|:-----|:---------|
| Global (all projects) | `~/.claude/settings.json` | Universal safety hooks (force push protection, destructive command blocking) |
| Project (shared, committed) | `.claude/settings.json` | Project-specific skill routing, workflow enforcement |
| Project local (gitignored) | `.claude/settings.local.json` | Personal overrides, dev-only hooks |

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

## Pattern: MCP Shadowing (Preference Layer)

A complementary approach to the Skill Router. Instead of blocking raw tools, **register an MCP tool whose name and description make the agent prefer it** over the equivalent raw CLI command.

### How It Works

Claude picks tools based on name + description relevance. If your MCP server exposes:

```json
{
  "name": "create_pull_request",
  "description": "Create a GitHub PR with JIRA linking, template validation, and team review assignment. Use this for ALL pull request creation."
}
```

...the agent will naturally prefer this over shelling out to `gh pr create` because it's more specific, more descriptive, and purpose-built for the task.

### Limitations

This is **Tier 2 (probabilistic)**. Under pressure (retries, complex prompts, or if the MCP tool errors out), the agent can fall back to raw CLI. That's why it should be combined with a hook enforcement layer.

### Layered Approach: Preference + Enforcement

| Layer | Mechanism | Reliability | Latency |
|:------|:----------|:------------|:--------|
| 1. Preference | MCP tool with strong description | ~90% (agent prefers it) | None (built into tool selection) |
| 2. Enforcement | `PreToolUse` command hook blocks raw CLI | ~100% (catches the rest) | ~5ms |

Layer 1 handles the happy path silently. Layer 2 is the safety net.

### MCP Gateway Approach

An MCP server that wraps the underlying tool and becomes the *only* way to perform the operation. The skill calls the MCP tool directly, never touching the CLI, so the hook never fires. This cleanly solves the skill-context detection problem (Open Question #1 above).

```
Skill → MCP Gateway Tool → underlying CLI/API
Main Agent → Raw CLI → BLOCKED by PreToolUse hook
```

---

## Pattern: Prompt Hook as Skill Router (LLM-Gated Bash)

Instead of a deterministic command hook with hardcoded patterns, gate **every Bash call** with a prompt hook that checks whether a skill or MCP tool should be used instead.

### Implementation

```jsonc
// .claude/settings.json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": { "tool_name": "Bash" },
        "type": "prompt",
        "prompt": "The agent is about to run a Bash command. Check if this command maps to a known skill or MCP tool that should be used instead.\n\nKnown skills/tools:\n- `gh pr create` → use the PR workflow in CLAUDE.md\n- `jira` CLI / `curl *.atlassian.net` → use devops-task-retriever skill\n- `gh workflow run` / `gh run` → use github-workflow-monitor skill\n- `gh api .*/copilot` → use copilot-usage-report skill\n- `git tag` / `git push --tags` → use named-build-tagging skill\n- `sf data` / `sf org` → use monthly-customer-scheduling skill\n\nIf the command matches, return {\"decision\": \"block\", \"reason\": \"Use the [skill-name] skill instead of raw CLI.\"}.\nOtherwise return {\"decision\": \"allow\"}."
      }
    ]
  }
}
```

### Tradeoffs

| Pro | Con |
|:----|:----|
| Catches novel bypass patterns a regex would miss | Every Bash call pays ~1-2s LLM latency |
| Self-documenting — the skill list is in the prompt | Tier 2 reliability (~90%), not Tier 1 |
| Easy to update — just edit the prompt text | Cost per invocation (LLM call) |

### Recommendation: Hybrid (Deterministic + Prompt Fallback)

Layer them so the fast deterministic hook handles known patterns and the slower prompt hook catches ambiguous cases:

| Layer | Hook Type | What It Catches | Latency |
|:------|:----------|:----------------|:--------|
| **1st** | `command` | Known violations (regex matches) | ~5ms |
| **2nd** | `prompt` | Ambiguous cases the command hook doesn't cover | ~1-2s |

The command hook runs first. If it allows, the prompt hook gets a turn. If the command hook blocks, the prompt hook never fires.

---

## Pattern: CLAUDE.md Drift Enforcement

Use hooks to **catch specific cases where the agent ignores CLAUDE.md instructions.** Every CLAUDE.md rule that the agent sometimes ignores becomes a candidate for a deterministic hook. This turns soft prose instructions into hard gates.

### Known Drift Patterns

These are behaviors observed where the agent doesn't follow CLAUDE.md rules:

| CLAUDE.md Rule | Agent Behavior (Drift) | Hook Fix | Event | Tier |
|:---------------|:----------------------|:---------|:------|:-----|
| §0 Mode Selection | Skips mode selection, immediately starts reading files | Block `Read`/`Glob`/`Grep` early in session if no mode confirmed | `PreToolUse` | 1 (but needs state tracking) |
| §1 Work Gate | Starts editing/writing code before explicit approval | Block `Edit`/`Write` if no ticket ID established | `PreToolUse` | 1 (but needs state tracking) |
| §2 Commit Format | Commits with wrong format | Regex-validate `-m` argument against `<type>(<scope>): desc [TICKET-ID]` | `PreToolUse` on Bash | 1 |
| §3 Consent Gate | Creates PR without pre-flight check and approval | Block `gh pr create` in Bash | `PreToolUse` on Bash | 1 |
| §3 Push Gate | Pushes without explicit approval | Block `git push` in Bash | `PreToolUse` on Bash | 1 |
| §4 Workflow Monitor | Auto-analyzes workflow-monitor output instead of presenting raw data | Check if last skill was workflow-monitor and block RCA | `Stop` | 2 |

### Implementation: State Machine for Session Gates (ID-007 Design)

The mode selection (§0) and work gate (§1) enforcement requires **session state tracking** — the hook needs to know what phase the session is in.

**Mechanism:**
1. `SessionStart` hook creates a state file: `~/.claude/session_state.json` with `{"phase": "mode_selection"}`
2. `UserPromptSubmit` hook (prompt type) detects mode confirmation → advances state to `"mode_confirmed"`
3. `UserPromptSubmit` hook detects work approval → advances state to `"work_approved"`
4. `PreToolUse` hooks on `Read|Glob|Grep|Edit|Write` check the state file and block if phase is too early

**Risk:** False positives on user message parsing. A user saying "yes" to something unrelated could advance the state machine.

**Mitigation options:**
- Use a `prompt` hook for intent detection (drops enforcement to Tier 2 but more accurate)
- Require specific phrases like "confirmed" or "approved"
- Use `AskUserQuestion` tool output as the state advancement trigger (if detectable)

---

## Broader Hook Use Cases (Beyond Skill Routing)

Categories of hooks worth implementing beyond the skill router pattern. These inform the overall hook strategy for this repo.

### Security & Guardrails
- **Destructive command blocking:** `rm -rf`, `DROP TABLE`, `--force` flags → Tier 1 command hook
- **Protected file guard:** Block writes to `.env`, `*.pem`, `*.key`, lock files → Tier 1 on `Edit|Write`
- **Dangerous pattern detection:** SQL injection, path traversal in generated code → Tier 2 prompt hook on `Edit|Write`
- **Environment-aware restrictions:** Stricter rules when `$ENV` is `production` → Tier 1 command hook

### Notifications & Awareness
- **Desktop notifications:** `osascript` (macOS) / `notify-send` (Linux) when Claude needs input → `Notification` event
- **Slack/webhook pings:** POST to webhook when long-running tasks finish → `PostToolUse` async hook
- **Idle detection alerts:** Notify when Claude has been waiting 5+ minutes → `Notification` event with `idle_prompt` matcher

### Logging & Auditing
- **Command audit log:** Append every Bash command with timestamp to immutable log file → `PostToolUse` async on Bash
- **Tool usage tracking:** Count tool invocations per session for analytics → `PostToolUse` async
- **Token/cost metrics:** Log session cost on `SessionEnd` for budget tracking → `SessionEnd` hook
- **Compliance trails:** Immutable audit log for regulated environments → `PostToolUse` + `SessionEnd`

### Context & Memory Management
- **SessionStart context loading:** Load recent git log, current sprint info, team conventions → `SessionStart` hook
- **PreCompact re-injection:** Re-inject critical project rules before context compression so they survive → `PreCompact` hook
- **SubagentStart context injection:** Inject project-specific context into subagents that wouldn't otherwise have it → `SubagentStart` hook

### Workflow Enforcement
- **Multi-criteria Stop gates:** Block completion until tests pass AND docs updated AND changelog entry exists → `Stop` agent hook
- **Commit message format validation:** Regex check on `git commit -m` argument → `PreToolUse` command hook on Bash (ID-004)
- **PR checklist enforcement:** Verify pre-flight check before `gh pr create` → `PreToolUse` on Bash (ID-002)

### Code Transformation
- **Auto-format on edit:** Run Prettier/Black/gofmt after every `Edit`/`Write` → `PostToolUse` command hook
- **Auto-organize imports:** Run isort or similar after Python file changes → `PostToolUse` command hook
- **Post-edit syntax validation:** `python3 -m py_compile` / `bash -n` / `yq eval` based on file extension → `PostToolUse` (ID-006)

### Cost & Resource Control
- **Rate limiting:** Block tool use after N Bash calls per session → `PreToolUse` command hook with counter
- **Temp file cleanup:** Delete temp/scratch files on `SessionEnd` → `SessionEnd` hook
- **Background test execution:** Run test suites async without blocking Claude → `PostToolUse` async hook

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
- **Design notes:** See "Pattern: CLAUDE.md Drift Enforcement" section above for the state machine design.
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

### ID-013: Git Push Consent Gate
- **Event:** `PreToolUse` on Bash
- **Block:** `git push` (all forms)
- **Redirect:** N/A (block with message "Git push requires explicit user approval per CLAUDE.md §3")
- **Tier:** 1
- **Rationale:** CLAUDE.md §3 states "Claude MUST NOT execute `git push` without explicit user approval." Currently pure prose. This makes it a hard gate.
- **Status:** Proposed

### ID-014: Git Commit Consent Gate
- **Event:** `PreToolUse` on Bash
- **Block:** `git commit` (all forms)
- **Redirect:** N/A (block with message "Git commit requires explicit user approval per CLAUDE.md §3")
- **Tier:** 1
- **Rationale:** CLAUDE.md §3 states "Claude MUST NOT execute `git commit` without explicit user approval." Separate from format enforcement (ID-004) — this is about *permission*, not *format*.
- **Note:** Could be combined with ID-004 into a single hook that checks both permission state and format. But they serve different purposes: ID-004 is about correctness, this is about consent.
- **Status:** Proposed

### ID-015: Prompt Hook Skill Router (LLM-Gated Catch-All)
- **Event:** `PreToolUse` on Bash
- **Type:** `prompt` hook
- **Action:** LLM checks if the Bash command maps to any known skill/MCP tool
- **Tier:** 2
- **Rationale:** Catches novel bypass patterns that deterministic regex would miss. Acts as second layer behind the command hook skill router.
- **Tradeoff:** ~1-2s latency on every Bash call. Only valuable as a fallback behind the deterministic router, not as the primary gate.
- **Status:** Idea

### ID-016: Workflow Monitor RCA Prevention
- **Event:** `Stop`
- **Action:** Check if the last skill invoked was `github-workflow-monitor`. If so, verify the agent is presenting raw data and not auto-analyzing.
- **Tier:** 2 (prompt hook needed to evaluate response content)
- **Rationale:** CLAUDE.md §4 says the agent "MUST simply present the data and wait for user input" for workflow-monitor output. The agent frequently ignores this and auto-generates RCA.
- **Status:** Idea

### ID-017: Desktop Notifications on Idle
- **Event:** `Notification` with matcher `idle_prompt`
- **Action:** Fire OS-level notification (Linux `notify-send` / macOS `osascript`)
- **Tier:** 1
- **Rationale:** Long-running sessions where Claude is waiting for input. User may have switched windows.
- **Status:** Idea

### ID-018: Session Audit Log
- **Event:** `PostToolUse` on all tools (async)
- **Action:** Append tool name, timestamp, truncated input/output to `~/.claude/audit.log`
- **Tier:** 1
- **Rationale:** Provides forensic trail for debugging unexpected agent behavior. Low-overhead when async.
- **Status:** Idea

### ID-019: PreCompact Context Re-injection
- **Event:** `PreCompact`
- **Action:** Re-inject critical context that must survive compaction: current ticket ID, DoD items, project conventions, active mode
- **Tier:** 1
- **Rationale:** Context compaction can cause the agent to "forget" important rules mid-session. Re-injection ensures continuity.
- **Status:** Idea

---

## Implementation Priority

Suggested order for implementation based on value and complexity:

### Phase 1: Deterministic Safety (Low complexity, high value)
These are simple regex-based command hooks. Can be implemented as a single unified router script.

1. **ID-005:** Force push protection
2. **ID-013:** Git push consent gate
3. **ID-014:** Git commit consent gate
4. **ID-011:** Protected file guard
5. **ID-004:** Git commit format enforcement

### Phase 2: Skill Router (Medium complexity, highest value)
The unified skill router script with the routing table.

6. **ID-001:** Enforce GHA skills
7. **ID-002:** Enforce PR generator
8. **ID-003:** Enforce named build tagging
9. **ID-009:** Copilot report enforcement
10. **ID-012:** Jira bypass prevention

### Phase 3: Post-Action Validation (Medium complexity, medium value)
PostToolUse hooks that validate after actions complete.

11. **ID-006:** Post-edit syntax validation
12. **ID-018:** Session audit log
13. **ID-017:** Desktop notifications

### Phase 4: Smart Gates (High complexity, high value)
These require prompt/agent hooks or state tracking.

14. **ID-007:** Session state machine
15. **ID-008:** DoD verification at Stop
16. **ID-015:** Prompt hook skill router (LLM catch-all)
17. **ID-016:** Workflow monitor RCA prevention
18. **ID-019:** PreCompact context re-injection

---

## Repo Context for Implementation

This repo (`claude-code-config`) contains the Claude Code configuration: skills, agents, MCP servers, and CLAUDE.md.

### Available Skills (in `skills/` directory)
Skills that hooks should route to:

| Skill | Directory | What It Wraps |
|:------|:----------|:-------------|
| `gha-run` | `skills/gha-run/` | `gh workflow run`, `gh run watch` |
| `gha-analyze` | `skills/gha-analyze/` | `gh run view`, workflow failure analysis |
| `pr-generator` | `skills/pr-generator/` | `gh pr create` |
| `named-build-tagging` | `skills/named-build-tagging/` | `git tag`, `git push --tags` |
| `devops-task-creator` | `skills/devops-task-creator/` | Jira issue creation via API |
| `devops-task-retriever` | `skills/devops-task-retriever/` | Jira issue retrieval via API |
| `copilot-usage-report` | `skills/copilot-usage-report/` | `gh api .*/copilot` |
| `monthly-customer-scheduling` | `skills/monthly-customer-scheduling/` | Salesforce `sf` CLI |
| `sonarqube-fixer` | `skills/sonarqube-fixer/` | SonarQube analysis + code fixes |
| `ansible-test-bed-loop` | `skills/ansible-test-bed-loop/` | GHA + Ansible test workflows |
| `request-triage` | `skills/request-triage/` | Incoming request classification |
| `task-definition` | `skills/task-definition/` | Task breakdown and planning |

### CLAUDE.md Rules That Need Hook Enforcement
Key rules from `CLAUDE.md` that are currently pure prose (Tier 3) and should be upgraded to hook enforcement:

- **§0:** Mode selection must happen before any work
- **§1:** Engagement mode gates (ticket ID, DoD, explicit approval)
- **§2:** Commit format: `<type>(<scope>): desc [TICKET-ID]`
- **§3:** PR consent gate: verify DoD, pre-flight check, explicit approval before `gh pr create`, `git commit`, `git push`
- **§4:** Workflow monitor output must be presented raw, no auto-RCA

### Hook File Location
Hook scripts should be created in `hooks/` directory within this repo. The settings.json will reference them by path.
