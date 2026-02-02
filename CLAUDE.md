## CLAUDE.md — Workflow & Invariants

### 0. Mode Selection (Before Everything)
Claude MUST classify the user's request and confirm the engagement mode before doing anything else.

1. Claude MUST propose a mode based on the user's request:
   > "This sounds like **[Mode A: Scoped Work]** / **[Mode B: Exploratory/Debug]**. Should I proceed with that framing?"
2. **HARD GATE — No work of any kind until mode is confirmed.** Claude MUST NOT read files, run commands, search code, analyze structure, or begin any investigation until the user explicitly confirms the engagement mode. Inferring agreement from context or continuation is not permitted.
3. If the request is ambiguous, Claude MUST ask a clarifying question rather than assume a mode.
4. Once the mode is confirmed, proceed to the corresponding section below.

---

### 1. Engagement Mode Gates
After the user confirms the engagement mode, Claude MUST complete the appropriate gate before beginning work.

#### Mode A — Scoped Work (Implementation)
**Purpose:** Implement a defined change with verifiable outcomes.

**Requirements:**
- **Ticket ID:** Mandatory. If missing, invoke `ticket-creator` skill.
- **DoD Interview → Approval Gate:**
  1. Claude MUST interview to produce a Definition of Done (DoD) as **verifiable facts**:
     - ✅ "API returns 200 status code for GET /health"
     - ✅ "CLI command `aws s3 ls` succeeds without errors"
     - ❌ "The feature works" (too vague)
  2. Claude MUST present the DoD as a numbered checklist and explicitly ask:
     > "Here is the proposed Definition of Done. Do you approve this DoD? I will not begin any work until you confirm."
  3. **HARD GATE — No work until explicit approval.** Claude MUST NOT execute any commands, write any code, read any files, create any branches, or begin any investigation until the user responds with explicit approval of the DoD. Silence, continuation of conversation, or lack of objection do NOT constitute approval.
  4. If the user modifies or questions any DoD item, Claude MUST re-present the **full updated DoD** and repeat the approval ask. Partial acknowledgments do not satisfy this gate.

#### Mode B — Exploratory / Debug (RCA)
**Purpose:** Discovery, log analysis, and Root Cause Analysis.

**Setup — Mission Objective → Approval Gate:**
1. Establish a **Mission Objective** (e.g., "Identify why API latency is spiking above 500ms").
2. Claude MUST present the Mission Objective and explicitly ask:
   > "Here is the proposed Mission Objective. Do you approve? I will not begin any investigation until you confirm."
3. **HARD GATE — No work until explicit approval.** Same rules as Mode A: no commands, no file reads, no investigation until the user explicitly approves.

**Discovery Ledger:** Claude MUST maintain this table to track hypothesis testing.
**Limit:** If 5 hypotheses are disproven without reaching the Mission Objective, Claude MUST stop and propose a "Mission Reset" (Zoom out, Pivot, or Clean Slate).

| Hypothesis | Test/Command | Expected | Actual | Status |
| :--- | :--- | :--- | :--- | :--- |
| e.g. DB Pool | Check metrics | <80% usage | 95% usage | ✅ Root Cause |

**Rules:**
- Focus on observation and hypothesis testing only.
- No commits, patches, or implementation work.
- Update the ledger after each test.

**Exit Condition:** When root cause is identified, Claude MUST ask:
> "Root cause identified: [summary]. Switch to Mode A (Scoped Work) to implement the fix?"

---

### 2. Development Protocol — The History Architect (Mode A Only)

#### Logical Commit Rule (Functional Layers)
A commit represents ONE **Functional Layer** — a complete capability, not a mechanical step.

**The Revert Test:** If reverting a commit would:
- Leave the system **stable** → ✅ Valid Functional Layer
- Cause **syntax errors or orphaned code** → ❌ Too granular, must be combined

**Format:** `<type>(<scope>): <description> [TICKET-123]`
**Body:** Explain **why** (the intent), not **what** (the diff).

#### Side-Fix Protocol (Out-of-Scope Cleanups)
When Claude discovers unrelated issues (typos, formatting, docs):

**Claude MUST ask:**
> "I found [unrelated issue]. This is outside the current Functional Layer. Should we:
> A) Create a separate branch for this cleanup
> B) Skip it for now (track in comment for later)
> C) Bundle it as an exception (adds scope to current work)"

**If approved for bundling:** Use a separate commit with `[SIDE-FIX]` marker.

#### Circuit Breakers
- **Hard Limit:** 5 logical commits per branch. At the 6th, Claude MUST recommend a PR.
- **Predictive Breaker:** At commit 4/5, if significant DoD items remain incomplete, Claude MUST pause and ask to consolidate or pivot to a PR to maintain history hygiene.
- **CI/CD Exception:** Use `--amend` for CI/CD refinements to stay under the limit.

---

### 3. PR & Approval Workflow

#### The Consent Gate (Before PR Creation)
Claude MUST complete these steps before proposing a PR:

1. **Verification:** Re-verify EVERY DoD item against actual system state.
2. **Side-Fix Resolution:** If `[SIDE-FIX]` commits exist, ask to Keep, Extract, or Discard.
3. **Pre-Flight Check:** Generate PR description showing commits mapped to DoD items and verification results.
4. **Explicit Approval:** Get approval before running `gh pr create`.

**Claude MUST NOT execute `git commit`, `git push`, or `gh pr create` without explicit user approval.**