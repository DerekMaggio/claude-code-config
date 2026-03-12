---
name: github-task-creator
description: Creates GitHub Issues in DerekMaggio repositories with structured title, body (markdown), and labels. Returns the issue URL and number for use as a Mode A scoped work reference.
allowed-tools: [mcp__github__create_issue, AskUserQuestion]
---

# GitHub Issue Creator

## 1. Purpose
Automates the creation of GitHub Issues in **DerekMaggio** repositories. Ensures the issue body is structured with a description and a clear Acceptance Criteria checklist, and returns the issue URL and number as the scoped work reference.

## 2. Trigger
Invoke when the user asks to "create an issue," "open a task," or provides work details intended for a personal GitHub repo under the **DerekMaggio** account.

## 3. Extraction & Discovery
Extract or ask the user for:
- **Title**: A concise issue title.
- **Description**: Background and scope of the work.
- **Acceptance Criteria**: Verifiable outcomes (do not abbreviate to AC).
- **Labels**: Optional. Tags to apply (e.g., `enhancement`, `bug`, `documentation`).
- **Repository**: `owner/repo` — parse from `git remote get-url origin` if in a known repo context, otherwise ask via `AskUserQuestion`.

## 4. Workflow Logic

### Step A: Resolve Repository
If the repository is not already known from context, run:
```bash
git remote get-url origin
```
Parse `owner` and `repo` from the URL. If unavailable or ambiguous, use `AskUserQuestion` to ask the user.

### Step B: Construct Issue Body (Markdown)
Format the body as:

```markdown
## Description
{{DESCRIPTION}}

## Acceptance Criteria
- [ ] {{CRITERIA_ITEM_1}}
- [ ] {{CRITERIA_ITEM_2}}
...
```

Each Acceptance Criteria item becomes a separate `- [ ]` checklist item.

### Step C: Issue Creation
Call `mcp__github__create_issue` with:
- `owner`: resolved owner
- `repo`: resolved repo
- `title`: `[User Title]`
- `body`: `[Constructed Markdown Body]`
- `labels`: `[User Labels]` (omit if none provided)

### Step D: Confirmation
Present the result to the user:
> "GitHub Issue created: **[Title]**
> - **URL**: [html_url]
> - **Issue Number**: #[number]
> - **Repo**: [owner/repo]
>
> Scope is locked to **[owner/repo#number]**. Use this as the reference ID for Mode A."

## 5. Technical Constraints
- **Naming**: Never abbreviate "Acceptance Criteria" to "AC".
- **Org Scope**: This skill is for **DerekMaggio** repos only. For AgreeYa-HuLoop repos, use `devops-task-creator`.
- **No ADF**: GitHub uses plain Markdown — do not attempt Atlassian Document Format construction.

## 6. Circuit Breakers
- **Missing Repository**: If owner/repo cannot be determined from context, use `AskUserQuestion` before attempting creation.
- **Creation Failure**: If the API returns an error, present the raw error message and ask the user how to proceed. Do not retry automatically.
