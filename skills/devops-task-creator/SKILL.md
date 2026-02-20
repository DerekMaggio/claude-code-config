---
name: devops-task-creator
description: Automates creation of Jira issues in the DEVOPS project with full ADF (Atlassian Document Format) support for the Acceptance Criteria field and dynamic Customer field resolution.
allowed-tools: [atlassian.get_field_metadata, atlassian.create_issue, AskUserQuestion]
---

# Jira Ticket Creator (Consolidated DEVOPS Skill)

## 1. Purpose
Automates the creation of Jira Tasks in the DEVOPS project. This skill ensures that the Acceptance Criteria field is correctly formatted in Atlassian Document Format (ADF) and that the Customer field is dynamically resolved to prevent API errors.

## 2. Trigger
Invoke when the user asks to "create a ticket," "open a task," or provides work details intended for Jira.

## 3. Extraction & Discovery
Extract or ask the user for:
- **Summary**: A concise title.
- **Description**: Background/scope.
- **Acceptance Criteria**: Verifiable outcomes (Do not abbreviate to AC).
- **Customer**: Target entity.

**Metadata Lookup (Pre-Creation):**
Call `atlassian.get_field_metadata` for:
- **Cloud ID**: `jira_cloud_id` from devops config
- **Project Key**: `jira_project_key` from devops config
- **Issue Type**: Task (ID: `jira_task_type_id` from devops config)

## 4. Workflow Logic

### Step A: Dynamic Field Resolution (Customer)
1. Locate `jira_customer_field` from devops config in the metadata fields array.
2. Match user input against `allowedValues` (case-insensitive).
3. **DEFAULT**: If no match is found, use the default customer ID (`jira_default_customer_id` from devops config).

### Step B: ADF Construction (Acceptance Criteria)
Transform the `acceptance_criteria` string into the following JSON object for `jira_ac_field` from devops config:

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
- **cloudId**: `jira_cloud_id` from devops config
- **summary**: `[User Summary]`
- **description**: `[User Description]`
- **additional_fields**:
    - `jira_ac_field`: `[Constructed ADF Object]`
    - `jira_customer_field`: `[{"id": "MATCHED_ID"}]`
