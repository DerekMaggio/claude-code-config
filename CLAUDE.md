### 0. Mode Selection (Before Everything)
Claude MUST classify the user's request and confirm the engagement mode before doing anything else.

1. Claude MUST propose a mode based on the user's request:
   > "This sounds like **[Mode A: Scoped Work]** / **[Mode B: Exploratory/Debug]**. Should I proceed with that framing?"
2. **HARD GATE — No work of any kind until mode is confirmed.** Claude MUST NOT read files, run commands, search code, analyze structure, or begin any investigation until the user explicitly confirms the engagement mode.
3. If the request is ambiguous, Claude MUST ask a clarifying question rather than assume a mode.
4. Once the mode is confirmed, proceed to the corresponding section below.

**Mode-Exempt Skills:** The following skills bypass mode selection entirely. When invoked, execute them directly:
- `monthly-customer-scheduling` — Self-contained workflow with its own validation gates
- `github-workflow-monitor` — Trigger and monitor a GitHub Actions workflow
- `install4j-doc-expert` — Tiered documentation lookup; executes directly without mode gates


---

### 4. Skill-Specific Handling (Deterministic Reporting)
The agent MUST NOT perform automatic Root Cause Analysis (RCA), log investigation, or "Next Steps" generation for the output of the following skills:

- **github-workflow-monitor**: This skill provides a deterministic report. If the output contains `RAW WORKFLOW DATA` or is wrapped in `<details>` blocks, the agent MUST simply present the data and wait for user input. Do NOT attempt to "fix" or "analyze" a workflow failure unless explicitly requested by the user.

---

### 1. Engagement Mode Gates
After the user confirms the engagement mode, Claude MUST complete the appropriate gate before beginning work.

#### Mode A — Scoped Work (Implementation)
**Purpose:** Implement a defined change with verifiable outcomes.

**Requirement: Ticket Discovery & Content Approval**
1. **Case 1: Existing Ticket ID Provided**
   - Claude MUST invoke the **devops-task-retriever** skill to fetch Summary, Description, Acceptance Criteria (`customfield_10037`), and Customer (`customfield_10962`).
   - Claude MUST present these details and ask: 
     > "I've retrieved Ticket [ID]. I will use the Acceptance Criteria as my Definition of Done (DoD). Do you confirm this is the correct scope?"
   - **GATE:** If the Acceptance Criteria is too vague for DoD, Claude MUST use `AskUser` to refine them into verifiable facts.

2. **Case 2: No Ticket ID (New Work)**
   - **Discovery Interview:** Claude MUST use the `AskUser` task to interview the user for: **Summary, Description, HuLoop Customer,** and **Definition of Done (DoD)** as verifiable facts.
   - **Content Review:** Claude MUST present the gathered information:
     > **Proposed Ticket Details:**
     > - **Summary:** [Text]
     > - **Description:** [Text]
     > - **Customer:** [Text]
     > - **Acceptance Criteria (DoD):** [Numbered List]
     > 
     > "Does this look correct? Once confirmed, I will create the ticket and obtain an ID."
   - **Ticket Creation & ID Retrieval:** After confirmation, Claude MUST invoke the **devops-task-creator** skill.
   - **HARD GATE:** Claude MUST NOT proceed to the Final Approval Gate until the Ticket ID has been successfully generated and presented to the user.

3. **Final Approval Gate (The Work Gate)**
   - Once a Ticket ID and specific DoD/Acceptance Criteria are established, Claude MUST ask:
     > "Scope is locked with Ticket [ID]. Should I begin implementation?"
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

---

### 3. PR & Approval Workflow

#### The Consent Gate (Before PR Creation)
Claude MUST complete these steps before proposing a PR:
1. **Verification:** Re-verify EVERY DoD item against actual system state.
2. **Pre-Flight Check:** Generate PR description mapping commits to Acceptance Criteria and verification results.
3. **Explicit Approval:** Get approval before running `gh pr create`.

**Claude MUST NOT execute `git commit`, `git push`, or `gh pr create` without explicit user approval.**