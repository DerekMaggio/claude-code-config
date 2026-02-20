---
name: task-definition
description: This skill orchestrates the decomposition of an approved Parent MVR (from a Triage Sheriff approved project) into a series of verifiable Child MVTs by invoking the 'task-architect' agent.
allowed-tools: [Task, Read, Write, Glob, Bash, AskUserQuestion, Skill]
---

# Task Definition

This skill manages the second major stage of the MVR workflow: taking an approved Parent MVR project and breaking it down into a series of actionable Child MVTs (Minimum Viable Tasks).

## Workflow

### 1. Acquire Approved MVR Project
1.  **Monitor Input**: The skill monitors the `[VAULT_ROOT]/Workflows/request-triage/triage-sheriff-approved/` directory for new project folders.
2.  **Selection**: The skill displays a list of all identified projects to the user, clearly categorized by their state (New, In Progress, Finished, Approved).
    -   **Default**: The skill automatically selects all "New" projects for processing.
    -   **Manual Override**: The user can manually select any existing project (In Progress, Finished, or Approved) for re-processing.

### 2. Prepare the Task Architect's Workspace
1.  **Create Project Folder**: The skill creates a new folder of the same name within the Task Architect's unapproved workspace: `[VAULT_ROOT]/Workflows/task-definition/task-architect-unapproved/<project-name>/`.
2.  **Copy Parent MVR**: It copies the essential `MVR.md` file from the source project directory (e.g., `triage-sheriff-approved/cloud-to-on-prem-failover/MVR.md`) into the newly created folder.

### 3. Invoke Task Architect for Decomposition

Spawn the `task-architect` Claude subagent:

```text
subagent_type: task-architect
prompt: |
  You are the Task Architect. You have been placed inside a project directory that contains a Parent MVR. Execute your mission as defined in your persona file.

  TASK:
  - Decompose the `MVR.md` in this directory into multiple, verifiable, 8-hour Child MVT files.
  - Place the new Child MVT files in this same directory.
  - Ensure all "Rules of the Firm" are followed.
```

### 4. Finalize Handoff
1.  **Verify Output**: Confirm that the task-architect successfully populated the project directory with new Child MVT files (check for `MVT-*.md` pattern).
2.  **Signal Completion**: Report that the decomposition is complete and the resulting Child MVTs are now awaiting human review in the `task-architect-unapproved/<project-name>/` directory.
