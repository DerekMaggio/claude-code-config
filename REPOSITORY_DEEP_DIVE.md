# Claude Code Configuration Manager — Complete Repository Deep Dive

## Document Purpose

This document provides a comprehensive, self-contained reference for the `claude-code-config` repository owned by Derek Maggio. It is designed for use as a source in Google NotebookLM, enabling conversational Q&A about the repository's structure, purpose, components, workflows, and design philosophy.

---

## 1. Repository Overview

### What Is This Repository?

The `claude-code-config` repository is a centralized, version-controlled configuration system for Claude Code — Anthropic's CLI-based AI coding assistant. It manages the global instructions, specialized sub-agents, reusable workflow skills, and maintenance scripts that define how Claude Code behaves across all of Derek Maggio's projects.

The repository lives at `https://github.com/DerekMaggio/claude-code-config.git` and is designed to be cloned and symlinked into the `~/.claude/` directory, making the configuration portable and shareable.

### Core Design Goals

1. **Reproducibility**: Any machine can be set up with the same Claude Code environment by cloning the repo and running the symlink script.
2. **Shareability**: Public agents and skills are separated from private ones (managed via Git submodule), allowing selective sharing.
3. **Reliability**: Safety gates, approval workflows, and validation checks are baked into every agent and skill.
4. **Modularity**: Each agent is a single-purpose assistant; each skill is a self-contained workflow package. They compose together but operate independently.

### How It Works

1. Clone the repository (with submodules for private agents).
2. Run `./helper_scripts/update_symlinks.sh` to create symlinks from `~/.claude/` to this repo.
3. Claude Code automatically picks up the custom agents, skills, and global instructions.

---

## 2. Repository Structure

```
claude-code-config/
├── CLAUDE.md                          # Global instructions & engagement mode policies
├── README.md                          # Setup guide & overview
├── .claudeignore                      # Patterns excluded from Claude's context window
├── .gitmodules                        # Git submodule config for private agents
│
├── agents/                            # Specialized AI sub-assistants
│   ├── public/                        # Shareable, non-sensitive agents
│   │   ├── utility/                   # General-purpose utility agents
│   │   │   ├── gemini-bridge.md       # Delegate tasks to Google Gemini CLI
│   │   │   ├── subagent-architect.md  # Meta-agent for creating new agents
│   │   │   ├── install4j-doc-expert.md# install4j documentation lookup
│   │   │   ├── voice-transcription-cleaner.md # Fix speech-to-text errors
│   │   │   └── brain-dump-refiner.md  # Structure messy requirements
│   │   ├── python/                    # Python-specific development agents
│   │   │   ├── python-test-architect.md    # Comprehensive pytest testing
│   │   │   ├── python-class-architect.md   # OOP class design
│   │   │   └── python-refactoring-specialist.md # Code refactoring
│   │   ├── testing/                   # Infrastructure testing agents
│   │   │   └── goss-test-architect.md # Goss infrastructure validation
│   │   └── project_management/        # Project management agents
│   │       ├── triage-sheriff.md      # Transform requests into Parent MVRs
│   │       └── task-architect.md      # Decompose MVRs into Child MVTs
│   └── private/                       # Private agents (Git submodule)
│
├── skills/                            # Reusable workflow capability packages
│   ├── monthly-customer-scheduling/   # Salesforce-to-Jira maintenance scheduling
│   ├── named-build-tagging/           # Multi-repo git tag automation
│   ├── sonarqube-fixer/               # Automated SonarQube issue remediation
│   ├── devops-task-creator/           # Create Jira DEVOPS tickets
│   ├── devops-task-retriever/         # Fetch & parse Jira tickets
│   ├── huloop-task-definition/        # Decompose MVR into MVTs via Gemini
│   ├── jira-monthly-scheduling/       # CSV customer mapping to Jira
│   ├── gha-analyze/                   # GitHub Actions failure RCA
│   ├── gha-run/                       # Trigger & monitor GHA workflows
│   ├── pr-generator/                  # Generate PR descriptions from diffs
│   ├── ansible-test-bed-loop/         # Iterative Ansible test-fix loop
│   └── huloop-request-triage/         # Transform chaotic requests into MVRs
│
└── helper_scripts/                    # Repository maintenance utilities
    ├── update_symlinks.sh             # Symlink ~/.claude to this repo
    ├── generate_markdown_report.py    # Generate usage pattern reports
    └── analyze_claude_history.py      # Analyze Claude interaction history
```

---

## 3. Global Instructions (CLAUDE.md)

The `CLAUDE.md` file is the most important file in the repository. It defines the operational policies that govern how Claude Code behaves in every session. Claude Code reads this file automatically from `~/.claude/CLAUDE.md` (symlinked from the repo).

### Mode Selection System

Before doing ANY work, Claude must classify the user's request into one of two engagement modes and get explicit confirmation:

**Mode A — Scoped Work (Implementation)**: For defined changes with verifiable outcomes. Requires a Jira ticket (existing or newly created), acceptance criteria as a Definition of Done, and explicit approval before any code is written.

**Mode B — Exploratory / Debug (RCA)**: For discovery, log analysis, and root cause analysis. Requires a stated Mission Objective and explicit approval. Claude maintains a Discovery Ledger table tracking hypotheses, tests, expected vs. actual results, and status.

**Mode-Exempt Skills**: Two skills bypass mode selection entirely because they have their own validation gates:
- `monthly-customer-scheduling`
- `github-workflow-monitor`

### Hard Gates

The CLAUDE.md enforces multiple "hard gates" — points where Claude must stop and wait for explicit user approval before proceeding:

1. **Mode confirmation gate**: No work until the user confirms Mode A or Mode B.
2. **Ticket discovery gate**: In Mode A, no work until a ticket ID exists with confirmed acceptance criteria.
3. **Work gate**: No implementation until the user says "begin."
4. **PR consent gate**: No `git commit`, `git push`, or `gh pr create` without explicit approval.

### Development Protocol (Mode A Only)

Commits follow the "History Architect" protocol:
- Each commit represents one **Functional Layer** — a complete capability, not a mechanical step.
- Format: `<type>(<scope>): <description> [TICKET-123]`
- The commit body explains **why** (intent), not **what** (the diff).

### PR Workflow

Before creating a PR, Claude must:
1. Re-verify every Definition of Done item against actual system state.
2. Generate a pre-flight check mapping commits to acceptance criteria.
3. Get explicit user approval before running `gh pr create`.

### Skill-Specific Handling

The `github-workflow-monitor` skill produces deterministic reports. Claude must present the raw data without attempting automatic RCA or "next steps" generation unless explicitly asked.

---

## 4. Agents — Specialized Sub-Assistants

Agents are markdown files that define specialized AI assistants with separate context windows. Each agent has a focused purpose, specific tool access, and behavioral guidelines. They are invoked by Claude Code when a task matches their description.

### 4.1 Utility Agents

#### gemini-bridge

**Purpose**: A single-action execution pipe that delegates high-context tasks to the Google Gemini CLI. It constructs and runs one `gemini` command, then terminates immediately.

**Key Behavior**:
- Executes exactly ONE action: running the `gemini` command.
- Never analyzes, summarizes, or interprets Gemini's output.
- Always suppresses stderr (`2> /dev/null`) unless debug mode is requested.
- Never tells Gemini how to structure its JSON response.

**Model Fallback Chain**:
1. Primary: `gemini-3-pro-preview` (for reasoning tasks)
2. Secondary: `gemini-2.5-pro` (if quota exhausted)
3. Tertiary: `gemini-2.5-flash` (speed tasks or last resort)

**Use for**: Analysis of many files, large-scale comparisons, deep code audits — tasks where token context is a concern for Claude.

**Tools**: Bash only.

#### subagent-architect

**Purpose**: A meta-agent that guides users through designing and creating new Claude Code subagents. It follows a four-phase process.

**Phases**:
1. **Understanding the Need**: Analyzes the request, validates scope, checks for existing agents.
2. **Requirement Gathering**: Presents 14 questions covering core purpose, technical requirements, behavior/style, examples/edge cases, and organization.
3. **Subagent Generation**: Creates the complete agent markdown file with proper frontmatter, system prompt, and validation checklist.
4. **Delivery & Installation**: Provides file path, invocation patterns, and a sample test request.

**Agent Color Coding Convention**:
- Blue: Code/technical agents
- Green: Testing/validation agents
- Yellow: Analysis/review agents
- Purple: Meta/utility agents
- Red: Security/critical agents
- Orange: Build/deployment agents

**Tools**: All tools (no restrictions). Uses Sonnet model.

#### install4j-doc-expert

**Purpose**: A three-tier documentation lookup specialist for the install4j installer toolkit.

**Lookup Tiers**:
1. **Tier 1 — Quick Reference**: Scans indices for keywords, provides brief descriptions. Always asks: "Would you like a detailed summary, or is this enough?"
2. **Tier 2 — Detailed Reference**: Provides key topics and common use cases. Asks: "Does this answer your question, or do you need the full source documentation?"
3. **Tier 3 — Source Docs**: Full documentation with code snippets and configuration flags.

**Guardrails**: Never skips tiers. Never hallucinates. Provides code blocks verbatim from source.

**Tools**: Read, Grep, Glob only (read-only access).

#### voice-transcription-cleaner

**Purpose**: Fixes speech-to-text errors in technical content, with a learnable correction database.

**Core Correction Patterns** (applied automatically):
- "cash" → "cache" (near system/memory/data/browser context)
- "dock her" → "Docker"
- "get hub" → "GitHub"
- "terra form" → "Terraform"
- "pie thon" → "Python"
- "jason" → "JSON" (data/config contexts)
- "engine X" → "nginx"
- "mango" → "MongoDB" (database context)
- "golden bills" → "golden builds" (CI/CD context)
- And many more domain-specific corrections.

**Pattern Learning Protocol**: New patterns require 2+ occurrences, explicit user confirmation, and are never auto-learned. The agent presents evidence and asks for approval.

**Output Sections**: Cleaned Transcription, Auto-Corrections Applied, New Pattern Detected (confirmation needed), Manual Review Needed.

**Tools**: All tools. Uses Sonnet model.

#### brain-dump-refiner

**Purpose**: Transforms messy, unstructured technical thoughts into clear, actionable specifications while actively preventing over-engineering.

**Analysis Framework**:
1. Extract Core Problems
2. Map Solution Approaches
3. Spot Missing Requirements
4. Flag Gold-Plating Risks
5. Ask Targeted Questions

**Anti-Gold-Plating Triggers**: Challenges phrases like "It would be nice if...", "We might need...", "Should be extensible...", "Make it configurable...", "Future-proof."

**Output Format**: Core Problem Identified, Solution Approaches, Key Assumptions, Missing Information checklist, Gold-Plating Risk Assessment (High/Medium/Low), Targeted Refinement Questions.

**Tools**: All tools. Uses Sonnet model.

### 4.2 Python Agents

#### python-test-architect

**Purpose**: Creates comprehensive pytest test suites with a strong emphasis on dependency injection over mocking.

**Key Principles**:
- Uses dependency injection (constructor injection, factory patterns, protocol-based testing) instead of mocks.
- Evaluates code testability and suggests refactoring when testing is difficult.
- Focuses on edge cases: boundary values, invalid inputs, type edge cases, concurrent access, resource exhaustion.
- Follows pytest conventions: descriptive test names, fixtures, parametrized tests, arrange-act-assert.

**Philosophy**: "If testing feels difficult or requires extensive mocking, that's often a sign the code itself needs refactoring."

**Tools**: All tools. Uses Sonnet model.

#### python-class-architect

**Purpose**: Designs OOP-compliant Python classes following SOLID principles and modern Python best practices.

**Standards**:
- SOLID principles (Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion).
- Composition over inheritance when appropriate.
- PEP 8 naming conventions.
- Consistent type hints, proper docstrings (Google or NumPy style).
- Dataclasses or attrs for simple data containers.
- Python 3.6+ features: f-strings, dataclasses, enhanced type hints, context managers, decorators, ABCs.

**Tools**: All tools. Uses Sonnet model.

#### python-refactoring-specialist

**Purpose**: Refactors Python code for clarity, maintainability, and testability.

**Core Principles**:
- Clarity over cleverness
- Simplicity over complexity
- Consistency over optimization
- Descriptive naming
- Testability first

**For every refactoring**: Explains reasoning, lists pros/cons vs. original, highlights testability improvements, provides working code, suggests test cases.

**Tools**: All tools. Uses Sonnet model.

### 4.3 Testing Agents

#### goss-test-architect

**Purpose**: Creates evidence-based infrastructure validation tests using Goss (Go Server Spec).

**Critical Constraints**:
- NEVER makes assumptions without evidence from IaC source materials.
- NEVER adds more than 5 test objects at a time.
- NEVER attempts to run tests directly on remote servers.
- ALWAYS requires evidence (playbooks, configs, docs) before creating tests.

**Workflow**: Evidence Gathering → Test Design → Goss Command Generation → Documentation → Incremental Review (5 tests at a time).

**Best Practices**: Modular files by function, descriptive naming, master suite with imports, negative tests, templates for similar servers, variables for environment-specific values.

**Tools**: All tools. Uses Sonnet model.

### 4.4 Project Management Agents

#### triage-sheriff

**Purpose**: Transforms ambiguous DevOps requests into formally defined Parent MVRs (Minimum Viable Requests).

**The Three Immutable Laws**:
1. **Rule of Facts**: Must identify exactly WHAT is changing and WHERE (environment). No guessing.
2. **Rule of Trade-offs**: If marked "Urgent," the MVR must include what current work is being stopped.
3. **Rule of 8 Hours**: The request must be decomposable into tasks of roughly 8 hours or less.

**The 5 Buckets** (every Parent MVR must address):
1. **THE FINISH LINE**: Business definition of "Done" — goal and acceptance criteria.
2. **THE LOCATION**: Specific system, service, customer, and environment (DEV/STAGE/PROD).
3. **THE TRADE-OFF**: Urgency justification and specific work being paused.
4. **THE INFO**: Inventory of access, links, credentials, and documentation required.
5. **THE CHECK**: Verification method the requester will use to confirm delivery.

**Output**: An MVR is either APPROVED (all buckets filled, all laws satisfied) or UNAPPROVED (with a GAP ANALYSIS of specific questions to answer).

**Tools**: All tools. Uses Sonnet model.

#### task-architect

**Purpose**: Decomposes a Parent MVR into discrete, 8-hour, verifiable Child MVTs (Minimum Viable Tasks).

**Rules of the Firm**:
- **THE 8-HOUR RULE**: Each Child MVT must be completable by a single engineer in no more than 8 hours.
- **MUST BE VERIFIABLE**: Every MVT has a clear, objective "Definition of Done" answerable with Yes/No.
- **PRECISION IS PARAMOUNT**: Every MVT is a load-bearing, clearly defined task.
- **ADHERE TO THE PLAN**: No features or requirements beyond the Parent MVR.
- **STRUCTURAL INTEGRITY**: Clear relationship between Parent MVR and Child MVTs.

**Tools**: All tools. Uses Sonnet model.

---

## 5. Skills — Reusable Workflow Packages

Skills are self-contained workflow capability packages. Each skill lives in its own directory with a `SKILL.md` file defining the workflow steps, and optionally includes helper scripts (bash/python) and prompt files.

### 5.1 monthly-customer-scheduling

**Purpose**: Automates monthly maintenance scheduling by pulling customer data from Salesforce, mapping it to Jira fields, calculating deployment dates, and creating Jira Epics with Customer Deployment tickets.

**Mode Exempt**: This skill bypasses the engagement mode gates because it has its own comprehensive validation workflow.

**Workflow**:
1. Target month selection (user confirms month/year).
2. Salesforce binary and auth verification.
3. Data extraction via SOQL query using `fetch_maintenance_data.sh`.
4. Jira metadata and HuLoop Customer field mapping.
5. Date calculation using `calculate_next_deployment.py` (handles week ordinals, day-of-week, Pacific Time offsets).
6. Pre-flight summary tables for user review.
7. Jira Epic creation.
8. Individual Customer Deployment ticket creation.
9. Finalization and Epic URL.

**Helper Scripts**:
- `fetch_maintenance_data.sh`: Executes Salesforce SOQL query to extract maintenance window data.
- `calculate_next_deployment.py`: Calculates next deployment date from week ordinal and day-of-week, with Pacific Time timezone awareness (PST/PDT).

**Key Technical Details**:
- Uses ISO 8601 date format with timezone offsets.
- Maps Salesforce customer names to Jira HuLoop Customer field values.
- Generates pre-flight validation tables before creating any Jira tickets.

### 5.2 named-build-tagging

**Purpose**: Automates creating and pushing identical git tags across multiple repositories with comprehensive safety features.

**Workflow** (10 steps):
1. Configuration setup (`.env` file with paths, JSON config with repositories).
2. Load repository configuration.
3. Pre-flight repository validation (all repos exist and are accessible).
4. Get tag information (tag name and message from user).
5. Gather commit information for each repository.
6. Confirm or select specific commits per repo.
7. Check for existing tags across all repos.
8. Create tags locally.
9. Dry-run push validation (catches permission/network issues before real push).
10. Push tags to remote.

**Safety Features**:
- Pre-validation of all repositories before any tagging.
- Dry-run pushes before real pushes.
- Automatic rollback on failure (deletes local tags).
- Tag conflict detection.
- Absolute path enforcement in all scripts.

**Helper Scripts**: `common.sh` (shared library), `validate_repositories.sh`, `get_commit_info.sh`, `validate_branch.sh`, `validate_commit.sh`, `check_tag_exists.sh`, `create_tag.sh`, `delete_tag.sh`, `dry_run_push.sh`, `push_tag.sh`, `prepare_from_urls.sh`.

### 5.3 sonarqube-fixer

**Purpose**: Systematically analyzes and fixes SonarQube code quality issues with comprehensive safety checks and error recovery.

**Workflow** (8 steps):
1. Input validation and parsing (accepts SonarQube JSON export or pasted JSON).
2. Parse and categorize issues by type, file, severity, and language.
3. Pre-flight safety checks (git repo verification, uncommitted changes detection, file accessibility).
4. Show fix summary with categorized issue counts.
5. Ask clarifying questions (TODO handling, commit strategy).
6. Fix issues with edit safety (line number verification before and after edits).
7. Change verification before commit.
8. Commit with user approval.

**Issue Types Handled**:
- Python S7498: `dict()` constructor calls → dict literal syntax.
- Python S1192: Duplicated string literals → constants.
- Shell S7677: stderr redirection style.
- Shell S7688: `[` vs `[[` test syntax.
- S1135: TODO comment handling (per-TODO user decision).

**Four Guardrails**:
1. No file path escapes (no `..`, no symlink traversal).
2. Line verification before every edit.
3. Syntax validation after every edit.
4. Error recovery with rollback options.

### 5.4 devops-task-creator

**Purpose**: Automates creation of Jira issues in the DEVOPS project with full Atlassian Document Format (ADF) support.

**Workflow**:
1. Extract or ask for ticket details (Summary, Description, Acceptance Criteria, Customer).
2. Metadata lookup for project and issue type IDs.
3. Dynamic HuLoop Customer field resolution (maps customer name to Jira field value).
4. ADF construction for the Acceptance Criteria field.
5. Issue creation via Atlassian REST API.

**Key Configuration**:
- Cloud ID: `be0a9935-763b-48a6-b39b-38d8207312fb`
- Project Key: `DEVOPS`
- Issue Type: Task (ID: 10027)
- HuLoop Customer Field: `customfield_10962`
- Acceptance Criteria Field: `customfield_10037`

### 5.5 devops-task-retriever

**Purpose**: Fetches and parses existing Jira DEVOPS tickets, translating ADF content back to human-readable text.

**Workflow**:
1. Retrieve issue via Atlassian REST API.
2. Extract and translate ADF content (Acceptance Criteria) to readable text.
3. Map custom fields (HuLoop Customer) to human-readable values.
4. Present for Definition of Done verification.

**Used By**: The Mode A engagement flow in CLAUDE.md — when a user provides a ticket ID, this skill fetches the details.

### 5.6 huloop-task-definition

**Purpose**: Manages the decomposition of an approved Parent MVR into Child MVTs using a combination of the Task Architect agent and Google Gemini.

**Workflow**:
1. Acquire an approved MVR project from the vault.
2. Prepare the Task Architect workspace.
3. Invoke Gemini via the gemini-bridge for decomposition (using the `gemini-architect.md` prompt).
4. Finalize handoff — verify output follows the Rules of the Firm (8-hour rule, verifiability, etc.).

**Prompt File**: `prompts/gemini-architect.md` — Contains the Task Architect decomposition mission that is passed to Gemini. It instructs Gemini to produce Child MVT files as a JSON object with filenames as keys.

### 5.7 jira-monthly-scheduling

**Purpose**: Maps CSV customer names (from Salesforce exports) to Jira HuLoop Customer field values.

**Matching Strategy** (three tiers):
1. Exact match (case-insensitive).
2. Partial/substring match.
3. Common abbreviation matching.

Uncertain matches are flagged for manual review.

**Helper Scripts**:
- `filter_csv.py`: Filters CSV to required columns (defined in `COLUMNS_TO_KEEP`).

**Output**: Filtered CSV, customer mapping JSON, summary of mapped/unmapped customers.

### 5.8 gha-analyze

**Purpose**: Performs root cause analysis on failed GitHub Actions workflow runs.

**Workflow**:
1. Fetch workflow metadata via `gh` CLI.
2. Generate failure summary using `summarize-failures.sh`.
3. Filter error logs using `filter-errors.sh`.
4. Extract context around failure points using `extract-context.sh`.
5. Request RCA analysis with all gathered data.

**Usage**: `/gha-analyze <run-id>`

**Helper Scripts**:
- `summarize-failures.sh`: Generates concise summary of failed jobs.
- `filter-errors.sh`: Filters logs for error patterns (ERROR, FATAL, Exception, etc.).
- `extract-context.sh`: Shows surrounding lines around failure points.

### 5.9 gha-run

**Purpose**: Triggers and monitors GitHub Actions workflows, with optional RCA on failure.

**Mode Exempt**: This skill (as `github-workflow-monitor`) bypasses engagement mode gates.

**Workflow**:
1. Validate inputs (workflow file, branch).
2. Trigger workflow using `trigger.sh`.
3. Get run ID using `get-run-id.sh`.
4. Monitor until completion using `monitor.sh` (active polling every 15 seconds via API, never uses `sleep`).
5. Generate deterministic status report using `report.sh`.
6. On failure: offer to run `gha-analyze` for RCA.

**Usage**: `/gha-run <workflow-file> <branch> [optional: inputs]`

**Helper Scripts**: `trigger.sh`, `get-run-id.sh`, `monitor.sh`, `report.sh`, `run-all.sh` (orchestrator).

### 5.10 pr-generator

**Purpose**: Analyzes code changes on a branch and generates a complete PR description filling the team's PR template.

**Workflow**:
1. Analyze branch changes vs. base branch.
2. Find Jira ticket references in commits/branch name.
3. Generate conventional commit title (e.g., `feat(auth): add SSO login [DEVOPS-123]`).
4. Fill PR template sections: Overview, Related Tickets/PRs, Changelog, Test Plan, Review Requests, Deployment Requirements, Risk.
5. Present complete PR description for user review.
6. Create PR only after explicit approval.

**Commit Type Prefixes**: feat, fix, refactor, docs, test, chore, perf, style.

### 5.11 ansible-test-bed-loop

**Purpose**: Iteratively tests Ansible changes by triggering GitHub Actions workflows, analyzing failures, proposing fixes, and re-testing until success or abort.

**Mode Exempt**: Bypasses engagement mode gates.

**Iteration Cycle**:
1. Trigger GHA workflow.
2. Monitor run (active polling every 30 seconds via API, never uses `sleep`).
3. Analyze failures.
4. Propose minimal, surgical fixes.
5. Get user approval before applying any fix.
6. Apply approved fixes, commit, and push.
7. Check exit condition (success, max iterations, or 3 identical errors = abort).

**Safety Constraints**:
- Never applies changes without user approval.
- Never refactors code (only surgical fixes).
- Aborts if the same error appears 3 times (infinite loop detection).
- Always uses MCP GitHub tools for API access.
- Checks `MEMORY.md` for known gotchas.

### 5.12 huloop-request-triage

**Purpose**: Transforms chaotic DevOps requests from multiple input sources into formal MVRs.

**Workflow**:
1. **Vault Discovery**: Locate the `huloop-devcloud` vault root directory.
2. **Workspace Initialization**: Create project directory, handle CONFLUENCE_REFERENCES files, determine approval routing.
3. **Multi-Modal Cleaning Loop**: Process various input file types:
   - Native readable: `.md`, `.txt`, `.pdf`, `.docx`, `.json`, `.yaml`, `.yml`, `.csv`, `.png`, `.jpg`, `.py`, `.sh`, `.tf`
   - Specialized cleaning: `.vtt`/`.srt` (transcripts via voice-transcription-cleaner), `.msg` (Outlook emails via `msg_to_md.py`)
4. **Sheriff Invocation**: Pass cleaned context to the Triage Sheriff agent (or Gemini via `gemini-sheriff.md` prompt).
5. **MVR Synthesis**: Produce formal Parent MVR following the Three Immutable Laws and 5-Bucket structure.

**Helper Scripts**:
- `helper_scripts/cleaning/msg_to_md.py`: Converts Outlook `.msg` email files to markdown format.

**Gemini Prompt**: `prompts/gemini-sheriff.md` — Triage Sheriff synthesis mission for Gemini, producing MVRs with the Three Immutable Laws and 5-Bucket structure.

---

## 6. Helper Scripts — Repository Maintenance

### update_symlinks.sh

**Purpose**: Creates symlinks from `~/.claude/` to this repository, making all agents, skills, and global instructions available to Claude Code.

**What It Does**:
1. Determines the repository root path.
2. Ensures `~/.claude/` directory exists.
3. Symlinks each subdirectory in `agents/` to `~/.claude/agents/`.
4. Symlinks each subdirectory in `skills/` to `~/.claude/skills/`.
5. Symlinks `CLAUDE.md` to `~/.claude/CLAUDE.md`.
6. Backs up existing non-symlink directories before overwriting.

### analyze_claude_history.py

**Purpose**: Analyzes the Claude Code interaction history file (`~/.claude/history.jsonl`) and produces a JSON analysis.

**Analysis Includes**:
- Project distribution (which projects are used most).
- Technology focus (keyword frequency: ansible, python, docker, terragrunt, azure, github, sonarqube, obsidian, gemini).
- Monthly timeline of project activity.
- Date range and interaction count metadata.

### generate_markdown_report.py

**Purpose**: Takes the JSON output from `analyze_claude_history.py` and generates a human-readable Markdown report.

**Report Sections**:
1. Top Projects (cumulative).
2. Technology & Tooling Focus table.
3. Persistent Workflow Patterns (Execution Plan pattern, Gemini-Bridge orchestration, RHEL/Ansible constraint).
4. Friction Points (Obsidian link fragility, repeated maintenance tasks).
5. Project Evolution timeline.

---

## 7. Configuration Files

### .claudeignore

Patterns excluded from Claude's context window to keep it focused:
- `.git/` — Git internal files
- `.gitmodules` — Submodule config
- `.venv/` — Python virtual environments
- `__pycache__/`, `.pytest_cache/`, `*.pyc`, `*.pyo` — Python cache
- `.DS_Store` — macOS metadata
- `*.backup.*` — Backup files

### .gitmodules

Defines one Git submodule for private agents:
- Path: `agents/private`
- URL: `https://github.com/DerekMaggio/claude-code-private-agents.git`

---

## 8. Data Flows and Workflow Relationships

### How Components Connect

```
User Request
    │
    ▼
CLAUDE.md (Mode Selection Gate)
    │
    ├── Mode A: Scoped Work ──────────────────────────┐
    │   │                                              │
    │   ├─► devops-task-retriever (fetch ticket)       │
    │   │   OR                                         │
    │   ├─► devops-task-creator (create ticket)        │
    │   │                                              │
    │   ├─► Implementation work                        │
    │   │   ├─► sonarqube-fixer (code quality)         │
    │   │   ├─► named-build-tagging (release tags)     │
    │   │   └─► (any coding task)                      │
    │   │                                              │
    │   └─► pr-generator (create PR) ─────────────────►│ Done
    │                                                   │
    └── Mode B: Exploratory/Debug ────────────────────┐│
        │                                              ││
        ├─► gha-analyze (GitHub Actions RCA)           ││
        ├─► ansible-test-bed-loop (iterative testing)  ││
        └─► Discovery Ledger ─────────────────────────►│ Done
```

### Request-to-MVR Pipeline

```
Raw Input (emails, transcripts, PDFs, Slack messages)
    │
    ▼
huloop-request-triage (multi-modal cleaning)
    │
    ├─► voice-transcription-cleaner (for .vtt/.srt files)
    ├─► msg_to_md.py (for .msg Outlook emails)
    │
    ▼
triage-sheriff (agent) OR gemini-sheriff (Gemini prompt)
    │
    ▼
Parent MVR (Minimum Viable Request)
    │   ├── THE FINISH LINE (acceptance criteria)
    │   ├── THE LOCATION (system, environment)
    │   ├── THE TRADE-OFF (urgency justification)
    │   ├── THE INFO (access, links, docs)
    │   └── THE CHECK (verification method)
    │
    ▼
huloop-task-definition
    │
    ▼
task-architect (agent) OR gemini-architect (Gemini prompt)
    │
    ▼
Child MVTs (8-hour, verifiable tasks)
```

### Maintenance Scheduling Pipeline

```
Salesforce (maintenance windows)
    │
    ├─► fetch_maintenance_data.sh (SOQL query)
    │
    ▼
monthly-customer-scheduling (SKILL)
    │
    ├─► calculate_next_deployment.py (date math)
    ├─► jira-monthly-scheduling (customer mapping)
    │
    ▼
Jira Epic + Customer Deployment Tickets
```

### CI/CD and GitHub Actions Pipeline

```
Code Changes
    │
    ▼
gha-run (trigger workflow)
    │
    ├─► monitor.sh (active polling)
    │
    ├── Success ──► report.sh (deterministic report)
    │
    └── Failure ──► gha-analyze (RCA)
                        │
                        └──► ansible-test-bed-loop (iterative fix)
                                │
                                └──► Fix → Commit → Push → Re-trigger
```

---

## 9. Design Philosophy and Patterns

### Safety-First Approach

Every destructive or visible action requires explicit user approval. This manifests as:
- Hard gates in the engagement mode system.
- Dry-run pushes before real pushes in `named-build-tagging`.
- Pre-flight validation tables before creating Jira tickets.
- Per-file, per-TODO decision handling in `sonarqube-fixer`.
- User approval before applying any fix in `ansible-test-bed-loop`.
- Consent gates before PR creation.

### Evidence-Based Decisions

Agents and skills never assume or guess:
- `goss-test-architect` requires IaC source materials before creating any test.
- `triage-sheriff` enforces the Rule of Facts — no MVR is approved with missing information.
- `voice-transcription-cleaner` requires 2+ occurrences and explicit confirmation before learning new patterns.
- `install4j-doc-expert` follows a three-tier escalation rather than guessing answers.

### Incremental Processing

Work is done in small, reviewable batches:
- `goss-test-architect` adds maximum 5 test objects at a time.
- `sonarqube-fixer` handles TODOs individually with per-item decisions.
- `ansible-test-bed-loop` applies one fix at a time with approval gates.
- `named-build-tagging` validates each repository before proceeding to the next step.

### Composition Over Monoliths

The system uses focused, composable components:
- Small, single-purpose agents compose with multi-step skill workflows.
- `huloop-request-triage` chains together `voice-transcription-cleaner`, `msg_to_md.py`, and `triage-sheriff`.
- `huloop-task-definition` chains together `gemini-bridge` and `task-architect`.
- `gha-run` offers `gha-analyze` as an optional follow-up on failure.

### Gemini Bridge Pattern

A recurring architectural pattern is using Claude as an orchestrator that prepares context for Gemini without reading the files itself. This is a sophisticated way of managing token limits and context precision — Claude constructs the optimal prompt and directory scope, and Gemini handles the heavy analysis.

### The MVR/MVT Framework

The project management system uses a two-tier decomposition:
- **MVR (Minimum Viable Request)**: A formally defined request with 5 buckets and 3 immutable laws. This is the "what" and "why."
- **MVT (Minimum Viable Task)**: A discrete, 8-hour, verifiable unit of work derived from an MVR. This is the "how."

This framework ensures every piece of work is bounded, justified, and verifiable before engineering time is invested.

---

## 10. Technology Stack and Integrations

### Tools and Platforms Referenced

| Technology | Usage in This Repository |
|---|---|
| **Claude Code** | The primary AI assistant this repository configures |
| **Google Gemini CLI** | Delegated heavy analysis via gemini-bridge |
| **Jira (Atlassian Cloud)** | Ticket creation, retrieval, and management |
| **Salesforce CLI** | Maintenance window data extraction |
| **GitHub Actions** | CI/CD workflow triggering, monitoring, and RCA |
| **GitHub CLI (gh)** | PR creation, issue management |
| **Git** | Version control, tagging, branching |
| **Ansible** | Infrastructure automation and testing |
| **Goss** | Infrastructure validation testing |
| **SonarQube** | Code quality analysis and remediation |
| **pytest** | Python test framework (preferred over unittest) |
| **install4j** | Java installer toolkit (documentation reference) |
| **Obsidian** | Knowledge management vault (huloop-devcloud) |
| **Azure** | Cloud infrastructure (referenced in analysis) |
| **Docker** | Container orchestration (referenced in transcription patterns) |

### API Endpoints Used

- **Atlassian REST API**: `https://api.atlassian.com/ex/jira/{cloudId}/rest/api/3/issue` for Jira operations.
- **GitHub API**: Via `gh` CLI and MCP tools for workflow and PR operations.
- **Salesforce API**: Via `sf` CLI binary for SOQL queries.

---

## 11. Naming Conventions

| Entity | Convention | Examples |
|---|---|---|
| **Agents** | Lowercase with hyphens | `python-test-architect`, `gemini-bridge` |
| **Skills** | Lowercase with hyphens | `named-build-tagging`, `gha-analyze` |
| **Commits** | Conventional commits | `feat(auth): add SSO login [DEVOPS-123]` |
| **Goss tests** | Descriptive with hyphens | `database-postgres.yaml`, `web-server.yaml` |
| **Agent colors** | Semantic color coding | blue=code, green=testing, yellow=analysis, purple=meta, red=security, orange=build |

---

## 12. Glossary

| Term | Definition |
|---|---|
| **MVR** | Minimum Viable Request — A formally defined, bounded request with acceptance criteria, environment, urgency justification, required info, and verification method |
| **MVT** | Minimum Viable Task — A discrete, 8-hour, verifiable unit of work derived from a Parent MVR |
| **ADF** | Atlassian Document Format — The JSON format used for rich text fields in Jira Cloud |
| **Hard Gate** | A mandatory approval point where Claude must stop and wait for explicit user confirmation |
| **Functional Layer** | A commit that represents one complete capability (not a mechanical step) |
| **Discovery Ledger** | A hypothesis-tracking table used in Mode B (Exploratory/Debug) |
| **Gold-Plating** | Over-engineering or adding unnecessary features beyond what was requested |
| **Gemini Bridge** | The pattern of using Claude to orchestrate Gemini CLI for heavy analysis tasks |
| **Pre-Flight Check** | A validation summary presented before executing irreversible actions |
| **5-Bucket Plan** | The five pillars that every MVR must address: Finish Line, Location, Trade-off, Info, Check |
| **Three Immutable Laws** | Rule of Facts, Rule of Trade-offs, Rule of 8 Hours — enforced by the Triage Sheriff |

---

## 13. Quick Reference: All Components

### Agents (11 total)

| Agent | Category | Purpose | Model |
|---|---|---|---|
| gemini-bridge | utility | Delegate tasks to Gemini CLI | (inherits) |
| subagent-architect | utility | Design and create new agents | Sonnet |
| install4j-doc-expert | utility | install4j documentation lookup | (inherits) |
| voice-transcription-cleaner | utility | Fix speech-to-text errors | Sonnet |
| brain-dump-refiner | utility | Structure messy requirements | Sonnet |
| python-test-architect | python | Comprehensive pytest testing | Sonnet |
| python-class-architect | python | OOP class design | Sonnet |
| python-refactoring-specialist | python | Code refactoring | Sonnet |
| goss-test-architect | testing | Infrastructure validation | Sonnet |
| triage-sheriff | project_management | Create Parent MVRs | Sonnet |
| task-architect | project_management | Decompose MVRs into MVTs | Sonnet |

### Skills (12 total)

| Skill | Mode Exempt | Purpose |
|---|---|---|
| monthly-customer-scheduling | Yes | Salesforce-to-Jira maintenance scheduling |
| named-build-tagging | No | Multi-repo git tag automation |
| sonarqube-fixer | No | SonarQube issue remediation |
| devops-task-creator | No | Create Jira DEVOPS tickets |
| devops-task-retriever | No | Fetch and parse Jira tickets |
| huloop-task-definition | No | MVR-to-MVT decomposition |
| jira-monthly-scheduling | No | CSV customer mapping to Jira |
| gha-analyze | No | GitHub Actions failure RCA |
| gha-run | Yes | Trigger and monitor GHA workflows |
| pr-generator | No | Generate PR descriptions |
| ansible-test-bed-loop | Yes | Iterative Ansible test-fix loop |
| huloop-request-triage | No | Transform requests into MVRs |

### Helper Scripts (3 total)

| Script | Purpose |
|---|---|
| update_symlinks.sh | Symlink ~/.claude to this repo |
| analyze_claude_history.py | Analyze Claude interaction history |
| generate_markdown_report.py | Generate usage pattern reports |

---

*This document was generated from a complete analysis of the claude-code-config repository as of February 2026.*
