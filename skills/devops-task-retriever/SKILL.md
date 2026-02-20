---
name: devops-task-retriever
description: Automates retrieval and parsing of Jira issues in the DEVOPS project, translating ADF and custom fields into human-readable text for Definition of Done (DoD) verification.
allowed-tools: [atlassian.get_issue, AskUserQuestion]
---

# Jira Ticket Retriever (Dynamic DEVOPS)

## 1. Purpose
Automates the retrieval and parsing of Jira issues from the **DEVOPS** project. This skill ensures that technical data (Acceptance Criteria) and custom metadata (Customer) are extracted and translated back into human-readable text for the Definition of Done (DoD) interview.

## 2. Trigger
Invoke this skill when a user provides a **Ticket ID** (e.g., "DEVOPS-123") or asks to "pull up," "look at," or "work on" an existing task.

## 3. Workflow Logic

### Step 1: Retrieval
Call `atlassian.get_issue` with the following parameters:
- **cloudId**: `jira_cloud_id` from devops config
- **issueIdOrKey**: [The provided Ticket ID]
- **fields**: `summary,description,{jira_ac_field},{jira_customer_field}` (use field IDs from devops config)

### Step 2: Extraction & Translation
Extract the following fields from the JSON response:
- **Summary**: `fields.summary`
- **Description**: `fields.description`
- **Acceptance Criteria**: `fields.{jira_ac_field}` (Translate from ADF or raw string to plain text)
- **Customer**:
    - Access `fields.{jira_customer_field}`.
    - Map the `value` property of the items in the array (e.g., `[{"value": "Acme"}]` → "Acme").

### Step 3: Verification Presentation
Present the data to the user:
> "I've retrieved **[Ticket ID]**:
> - **Summary**: [Summary]
> - **Customer**: [Mapped Customer Value]
> - **Current Acceptance Criteria**: [Acceptance Criteria]
>
> I will use these Acceptance Criteria as the **Definition of Done (DoD)**. Does this match your expectations, or do we need to refine the verifiable facts?"

## 4. Technical Constraints
- **Cloud ID**: `jira_cloud_id` from devops config
- **Field IDs**: use `jira_ac_field` and `jira_customer_field` from devops config
- **Null Handling**: If Acceptance Criteria field is empty, flag this and initiate a DoD interview via `AskUserQuestion`.
- **Naming**: Never abbreviate "Acceptance Criteria" to "AC".

## 5. Circuit Breakers
- **Issue Not Found**: If 404 occurs, notify the user and offer to create a new ticket using the Creator skill.
- **Access Denied**: If 403 occurs, notify the user regarding DEVOPS project permissions.
