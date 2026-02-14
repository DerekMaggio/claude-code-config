---
name: huloop-request-intake
description: Transform chaotic DevOps requests into MVRs. Features status-based routing (approved/unapproved), parallel cleaning, and vault-discovery.
allowed-tools: [Task, Read, Write, Glob, Bash, AskUserQuestion, mcp__atlassian__getAccessibleAtlassianResources, mcp__atlassian__getConfluencePage]
---

# HuLoop Request Intake

This skill manages the transition from raw request chaos to a structured MVR by first locating the `huloop-devcloud` vault root.

## Workflow

### 1. Vault Discovery & Capabilities
1.  **Locate Vault**: Search for the `huloop-devcloud` directory root to ensure absolute pathing.
2.  **Define Routing Paths**:
    - **Approved**: `[VAULT_ROOT]/Workflows/huloop-request-intake/intake-sheriff-approved/`
    - **Unapproved**: `[VAULT_ROOT]/Workflows/huloop-request-intake/intake-sheriff-unapproved/`
3.  **Laser-Focused Discovery**: 
    - **Reserved List**: `.vtt, .srt, .msg` (Handled by specialized skill logic).
    - **Base Capability**: `.md, .txt, .pdf, .docx, .json, .yaml, .yml, .csv, .png, .jpg, .jpeg, .webp, .py, .sh, .tf`.
4.  **Minimal Check**: Ask `claude-code-guide` if any other extensions in the current path are native-readable.
5.  **Cache**: Store results in `[VAULT_ROOT]/_/.claude_capabilities.json` to prevent token-heavy re-runs.

### 2. Workspace Initialization & Routing
1.  **Project Directory**: The user passes a project directory path as input. All workspace subdirectories are created inside it.
2.  **Structure**: Create `needs_cleaning/`, `cleaned/`, and `provided_context/` inside the project directory.
    ```bash
    mkdir -p "[PROJECT_DIR]/needs_cleaning" "[PROJECT_DIR]/cleaned" "[PROJECT_DIR]/provided_context"
    ```
3.  **CONFLUENCE_REFERENCES Handling** (before general routing):
    - **IF** a file named `CONFLUENCE_REFERENCES` exists in the input:
      1.  Read the file. Each non-empty, non-comment line is a Confluence page URL or page ID.
          ```
          # Lines starting with # are comments
          https://huloop.atlassian.net/wiki/spaces/DEVOPS/pages/123456789/Page+Title
          987654321
          ```
      2.  Call `mcp__atlassian__getAccessibleAtlassianResources` once to resolve the Cloud ID.
      3.  For each entry, extract the page ID:
          - If a URL, parse the numeric page ID from the path (the segment after `/pages/`).
          - If already a numeric ID, use it directly.
      4.  Call `mcp__atlassian__getConfluencePage` for each page:
          - `cloudId`: resolved Cloud ID from step 2
          - `pageId`: extracted page ID
          - `contentFormat`: `"markdown"`
      5.  Write each page to `provided_context/confluence_[PAGE_ID].md` with a header:
          ```markdown
          <!-- Source: Confluence Page [PAGE_ID] - [PAGE_TITLE] -->
          [downloaded markdown content]
          ```
      6.  Do NOT route the `CONFLUENCE_REFERENCES` file itself into `needs_cleaning/` or `provided_context/`.
4.  **Priority Routing** (all other files):
    - **IF** file is `.vtt, .srt, .msg`: Move to `needs_cleaning/`.
    - **ELSE IF** extension is in Native Capability List: Move to `provided_context/`.
    - **ELSE**: Move to `needs_cleaning/` for Claude-direct refinement.

### 3. The Multi-Modal Cleaning Loop
Iterate through `needs_cleaning/`:

#### A. Transcripts (.vtt, .srt)
1.  **Split**: If >20k tokens, use `Bash` to `split -l 500`.
2.  **Parallel Clean**: Invoke `voice-transcription-cleaner` for each chunk.
3.  **Reassemble**: `cat` chunks alphabetically into `cleaned/[NAME].cleaned.md`.

#### B. Outlook Emails (.msg)
1.  **Execute**: `uv run helper_scripts/cleaning/msg_to_md.py "needs_cleaning/[FILE]" > "cleaned/[FILE].md"`.
    - *Note: Script collapses 3+ newlines into 2 to manage whitespace.*
2.  **Verify**: Confirm file is created and contains text via `[ -s "cleaned/[FILE].md" ]`.

#### C. Other Messy Files
1.  **Refine**: Claude reads and formats noise (logs/text) into `cleaned/[FILE].refined.md`.

### 4. Sheriff Invocation (Vault Rooted)
Spawn the `intake-sheriff` using the template at `[VAULT_ROOT]/_/templates/Minimum Viable Request (MVR) - Template.md`.



```text
subagent_type: intake-sheriff
prompt: |
  You are the HuLoop Intake Sheriff. 
  
  VAULT ROOT: [DISCOVERED_PATH]
  TEMPLATE: [DISCOVERED_PATH]/_/templates/Minimum Viable Request (MVR) - Template.md
  
  TASK:
  - Synthesize context from cleaned/ and provided_context/.
  - Apply the "Three Immutable Laws" and fill the "5 Buckets."
  - THREAD AWARENESS: Prioritize the latest technical consensus.
  - CONFLICT DETECTION: Flag contradictions as "Conflicts" in the MVR.
  
  STRICT TRUTH RULES:
  - DO NOT INVENT: IPs, IDs, or Deadlines.
  - USE [MISSING]: For any gaps in the 5 Buckets.