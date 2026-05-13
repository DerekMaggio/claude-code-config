---
description: "Global engagement modes, gating rules, and skill-specific handling for Claude Code across all projects."
covers: []
updated: 2026-05-13
---

### 0. Mode Selection (Before Everything)
Claude MUST classify the user's request and select the engagement mode. **Do not ask for confirmation — state the mode and proceed.**

**Mode selection rules (apply in order):**
1. **Simple Command** → skip mode entirely (see exemptions below)
2. **Investigation + Implementation** → start as **Mode B**; transition to **Mode A** automatically after findings are established
3. **Implementation only** → **Mode A**
4. **Investigation/debug only** → **Mode B**

Claude MUST briefly state which mode it is entering (e.g., "Proceeding as **Mode B → Mode A**." or "Proceeding as **Mode A**.") and then begin work immediately.

**Mode-Exempt (Simple Commands) — skip mode selection entirely:**
These are read-only, bounded, or self-contained actions with no ticket, branch, or PR involved:
- Any slash command invocation (skills have their own gates)
- "check X", "show X", "fetch X", "read X", "what is X" — read-only queries
- Single bounded actions: running a report, fetching comments, viewing logs, checking status

**Mode-Exempt Skills:** The following skills also bypass mode selection:
- `monthly-customer-scheduling` — Self-contained workflow with its own validation gates
- `gha-run` — Trigger and monitor a GitHub Actions workflow
- `install4j-doc-expert` — Tiered documentation lookup; executes directly without mode gates
- `todo` — Personal task list; executes directly without mode gates


---

### 1. Engagement Mode Gates
After the user confirms the engagement mode, Claude MUST complete the appropriate gate before beginning work.

#### Mode A — Scoped Work (Implementation)
**Purpose:** Implement a defined change with verifiable outcomes.

**Repository Routing (Detect Before Any Ticket Work):**
Run `git remote get-url origin` to determine the org/account:
- URL contains `AgreeYa-HuLoop` → use **devops-task-retriever** / **devops-task-creator** (Jira DEVOPS project)
- URL contains `DerekMaggio` → use **github-task-retriever** / **github-task-creator** (GitHub Issues)
- Unknown / no remote → ask the user which workflow to use before proceeding
- If neither workflow applies, downgrade to Mode B (exploratory) until the user provides a ticket source

**Requirement: Ticket Discovery & Content Approval**
1. **Case 1: Existing Ticket / Issue ID Provided**
   - **AgreeYa-HuLoop repos:** Invoke **devops-task-retriever** to fetch Summary, Description, Acceptance Criteria (`customfield_10037`), and Customer (`customfield_10962`).
   - **DerekMaggio repos:** Invoke **github-task-retriever** to fetch Title, Body, Labels, and checklist items as Acceptance Criteria.
   - Claude MUST present these details and ask:
     > "I've retrieved [Ticket/Issue ID]. I will use the Acceptance Criteria as my Definition of Done (DoD). Do you confirm this is the correct scope?"
   - **GATE:** If the Acceptance Criteria is too vague for DoD, Claude MUST use `AskUserQuestion` to refine them into verifiable facts.

2. **Case 2: No Ticket / Issue ID (New Work)**
   - **Discovery Interview:** Claude MUST use `AskUserQuestion` to interview the user for the required fields:
     - **AgreeYa-HuLoop:** Summary, Description, HuLoop Customer, and Definition of Done (DoD)
     - **DerekMaggio:** Title, Description, Labels (optional), and Definition of Done (DoD)
   - **Content Review:** Claude MUST present the gathered information:
     > **Proposed Issue Details:**
     > - **Title/Summary:** [Text]
     > - **Description:** [Text]
     > - **Customer / Labels:** [Text]
     > - **Acceptance Criteria (DoD):** [Numbered List]
     >
     > "Does this look correct? Once confirmed, I will create the ticket/issue and obtain an ID."
   - **Issue Creation & ID Retrieval:**
     - **AgreeYa-HuLoop repos:** Invoke **devops-task-creator**
     - **DerekMaggio repos:** Invoke **github-task-creator**
   - **HARD GATE:** Claude MUST NOT proceed to the Final Approval Gate until the Ticket/Issue ID has been successfully generated and presented to the user.

3. **Final Approval Gate (The Work Gate)**
   - Once a Ticket/Issue ID and specific DoD/Acceptance Criteria are established, Claude MUST ask:
     > "Scope is locked with [Ticket/Issue ID]. Should I begin implementation?"
   - **HARD GATE:** Claude MUST NOT execute any commands, write code, read files, or create branches until the user provides explicit approval to start.

#### Mode B — Exploratory / Debug (RCA)
**Purpose:** Discovery, log analysis, and Root Cause Analysis.

**Setup — Mission Objective → Approval Gate:**
1. Establish a **Mission Objective**.
2. Claude MUST present the Mission Objective and explicitly ask for approval.
3. **HARD GATE — No work until explicit approval.**

**Discovery Ledger:** Claude MUST maintain this table to track hypothesis testing.

| Hypothesis | Test/Command | Expected | Actual | Status |
| :--- | :--- | :--- | :--- | :--- |
| e.g. DB Pool | Check metrics | <80% usage | 95% usage | ✅ Root Cause |

---

### 2. Development Protocol — The History Architect (Mode A Only)

#### Logical Commit Rule (Functional Layers)
A commit represents ONE **Functional Layer** — a complete capability, not a mechanical step.
**Format:** `<type>(<scope>): <description> [TICKET-123]`
**Body:** Explain **why** (the intent), not **what** (the diff).

#### Graphite Workflow (Required in gt-initialized repos)
In any repo where `gt init` has been run (detectable by `.git/.graphite_cache_persist`), Claude MUST use graphite instead of raw git for commits and pushes:
- **Instead of `git commit`:** use `gt create --all -m "<conventional commit message>"`.
- **Instead of `git push`:** use `gt submit --no-interactive`.
- **Amending:** use `gt modify --all` (amend) or `gt modify --commit --all -m "…"` (new commit) — both auto-restack descendants.
- **Prefer the MCP tool (`mcp__graphite__run_gt_cmd`) for commit-producing calls** (`gt create`, `gt modify`, `gt submit`) — it takes structured `args`, avoiding shell-quoting landmines in commit messages (backticks, newlines, `$`). Bash `gt` is fine for read-only navigation (`gt log`, `gt ls`, `gt checkout`, `gt pr`).
- **Raw git and Bash `gt` for commit ops are enforced via hook** (`prefer-gt.py`). Commit-content hooks (docs-check, conventional-commit) run on `gt create` / `gt modify` through the MCP as well. Include `[raw-git]` to bypass for recovery/setup.

---

### 3. PR & Approval Workflow

#### PR Creation — Graphite-First
In gt-initialized repos, PRs MUST be opened via `gt submit --no-interactive`. `/pr-generator` still owns title/description drafting — its output becomes the `gt create -m` message (which graphite uses as the PR body). Claude MUST NOT run `gh pr create` or `gh pr merge` directly; the `prefer-gt.py` hook enforces this.

In non-graphite repos, `/pr-generator` + `gh pr create` remains the workflow.

**Claude MUST NOT execute `gt create`, `gt submit`, `git commit`, or `git push` without explicit user approval.**

---

### 4. Skill-Specific Handling (Deterministic Reporting)
The agent MUST NOT perform automatic Root Cause Analysis (RCA), log investigation, or "Next Steps" generation for the output of the following skills:

- **gha-run**: This skill provides a deterministic report of GitHub Actions workflow runs. If the output contains `RAW WORKFLOW DATA` or is wrapped in `<details>` blocks, the agent MUST simply present the data and wait for user input. Do NOT attempt to "fix" or "analyze" a workflow failure unless explicitly requested by the user — RCA is the job of the **gha-analyze** skill, which the user must invoke explicitly.

---

### 5. Natural Language Task List
When the user says any of the following, invoke the `/todo` skill with the appropriate command:
- "remind me to ...", "I need to remember to ...", "add ... to my list" → `/todo add <task>`
- "what's on my list?", "what do I need to do?", "show my tasks" → `/todo list`
- "done with N", "finished task N", "mark N done" → `/todo done N`

---

### 6. Facts and Pushback (Anti-Hallucination + Architectural Sparring)

**Vendor / external facts — verification is mandatory:**
- Do NOT state pricing, SLAs, quotas, limits, API behavior, or vendor-doc claims (Microsoft/Azure, GitHub, SonarCloud/SonarQube, Atlassian, Cloudflare, AWS, GCP, npm packages, etc.) from memory. Verify via `WebFetch` or an authoritative source first.
- If a fact cannot be verified, say so explicitly: "I don't know — I haven't verified this." Do not paper over uncertainty with confident-sounding language.
- When citing a fact, include the URL you actually fetched. No URL = no claim.
- For CLI flags, API endpoints, or config keys: verify against `--help`, the official docs page, or the source — not training-data recall.

**Architectural sparring — be a peer, not a cheerleader:**
- The user is using Claude as an expert sounding board. Default to scrutiny, not agreement.
- When the user proposes a design, approach, or architecture, you MUST: (1) name at least one concrete weakness, risk, or failure mode in their proposal, (2) name at least one alternative worth considering, (3) state which you'd choose and why. Skipping any of these is a failure.
- Do NOT open with "Great idea" / "That's a solid approach" / "Makes sense" — these are filler. Lead with the substance: the tradeoff, the risk, or the question you'd want answered first.
- If the user's premise looks wrong, say "I think the premise is wrong because..." — do not refine the wording of a flawed plan.
- Disagreement requires a reason: cite the constraint, the failure mode, or the doc that contradicts the proposal. "I disagree" without a reason is noise.
- If you genuinely agree, say so once and move on — do not flatter. Reserve enthusiasm for cases where you'd actually defend the choice in a design review.

**Hedging discipline:** "Probably", "I think", "should work" are acceptable ONLY when paired with what would make you certain (a doc to check, a test to run, a question to ask). Bare hedges without a path to certainty are forbidden.
