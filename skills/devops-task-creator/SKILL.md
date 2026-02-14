---
name: devops-task-creator
description: Automates creation of Jira issues in the DEVOPS project with full ADF (Atlassian Document Format) support for the Acceptance Criteria field and dynamic customer ID resolution.
allowed-tools: [atlassian.get_field_metadata, atlassian.create_issue, AskUserQuestion]
---

# HuLoop Jira Ticket Creator (Consolidated DEVOPS Skill)

## 1. Purpose
Automates the creation of Jira Tasks in the DEVOPS project. This skill ensures that the Acceptance Criteria field is correctly formatted in Atlassian Document Format (ADF) and that the HuLoop Customer field is dynamically resolved to prevent API errors.

## 2. Trigger
Invoke when the user asks to "create a ticket," "open a task," or provides work details intended for Jira.

## 3. Extraction & Discovery
Extract or ask the user for:
- **Summary**: A concise title.
- **Description**: Background/scope.
- **Acceptance Criteria**: Verifiable outcomes (Do not abbreviate to AC).
- **HuLoop Customer**: Target entity (e.g., Internal, All Customers, Clutch).

**Metadata Lookup (Pre-Creation):**
Call `atlassian.get_field_metadata` for:
- **Cloud ID**: `be0a9935-763b-48a6-b39b-38d8207312fb`
- **Project Key**: `DEVOPS`
- **Issue Type**: `Task` (ID: `10027`)

## 4. Workflow Logic

### Step A: Dynamic Field Resolution (HuLoop Customer)
1. Locate `customfield_10962` in the metadata fields array.
2. Match user input against `allowedValues` (case-insensitive).
3. **DEFAULT**: If no match is found, use **Internal (ID: 11033)**.

### Step B: ADF Construction (Acceptance Criteria)
Transform the `acceptance_criteria` string into the following JSON object for `customfield_10037`:

{
  "version": 1,
  "type": "doc",
  "content": [
    {
      "type": "paragraph",
      "content": [
        {
          "type": "text",
          "text": "{{ACCEPTANCE_CRITERIA_STRING}}"
        }
      ]
    }
  ]
}

### Step C: Issue Creation
Call `atlassian.create_issue`:
- **cloudId**: `be0a9935-763b-48a6-b39b-38d8207312fb`
- **summary**: `[User Summary]`
- **description**: `[User Description]`
- **additional_fields**:
    - `customfield_10037`: `[Constructed ADF Object]`
    - `customfield_10962`: `[{"id": "MATCHED_ID"}]`