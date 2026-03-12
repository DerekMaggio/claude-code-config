---
name: github-task-retriever
description: Retrieves and parses a GitHub Issue by owner/repo#number or URL, extracting title, body, labels, and checklist items as a human-readable Definition of Done for personal DerekMaggio repos.
allowed-tools: [mcp__github__get_issue, AskUserQuestion]
---

# GitHub Issue Retriever

## 1. Purpose
Automates retrieval and parsing of GitHub Issues from **DerekMaggio** repositories. Extracts the issue title, body, labels, and any checklist items to serve as the Definition of Done (DoD) for Mode A scoped work.

## 2. Trigger
Invoke this skill when a user provides a **GitHub Issue reference** (e.g., `DerekMaggio/my-repo#42`) or a full GitHub issue URL, and the working repository is under the **DerekMaggio** org/account.

## 3. Workflow Logic

### Step 1: Parse the Issue Reference
Accept any of the following formats:
- `owner/repo#number` (e.g., `DerekMaggio/my-repo#42`)
- Full URL (e.g., `https://github.com/DerekMaggio/my-repo/issues/42`)
- Just a number if the current repo context is known (parse owner/repo from `git remote get-url origin`)

Extract:
- `owner`
- `repo`
- `issue_number`

### Step 2: Retrieval
Call `mcp__github__get_issue` with:
- `owner`: parsed owner
- `repo`: parsed repo
- `issue_number`: parsed number

### Step 3: Extraction & Translation
Extract from the response:
- **Title**: `title`
- **Body**: `body` (raw markdown)
- **Labels**: `labels[].name` joined as a comma-separated list
- **Acceptance Criteria (DoD)**: Scan `body` for markdown checklist items (`- [ ]` or `- [x]`). If found, extract them as the DoD list. If none found, use the full body text.

### Step 4: Verification Presentation
Present the data to the user:
> "I've retrieved **[owner/repo#number]**:
> - **Title**: [Title]
> - **Labels**: [Labels or 'none']
> - **Current Acceptance Criteria**: [Checklist items or full body]
>
> I will use these Acceptance Criteria as the **Definition of Done (DoD)**. Does this match your expectations, or do we need to refine the verifiable facts?"

## 4. Technical Constraints
- **Null Handling**: If the body is empty or has no checklist, flag this and initiate a DoD interview via `AskUserQuestion`.
- **Naming**: Never abbreviate "Acceptance Criteria" to "AC".
- **Org Scope**: This skill is for **DerekMaggio** repos only. For AgreeYa-HuLoop repos, use `devops-task-retriever`.

## 5. Circuit Breakers
- **Issue Not Found (404)**: Notify the user and offer to create a new issue using the `github-task-creator` skill.
- **Access Denied (403)**: Notify the user regarding repository permissions.
- **Ambiguous Reference**: If owner/repo cannot be determined, use `AskUserQuestion` to ask the user to provide the full `owner/repo#number` reference.
