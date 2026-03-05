# Skills

Slash-command skills for Claude Code. Invoke with `/skill-name` in any session.

Each skill has a `SKILL.md` (the execution definition Claude reads) and lives in its own directory.

## Available Skills

| Skill | Description |
|---|---|
| `ansible-test-bed-loop` | Iteratively trigger Ansible GHA deploy, analyze failures, apply fixes, re-test until clean |
| `copilot-usage-report` | Pull GitHub Copilot usage metrics and seat activity, compile into Obsidian markdown report |
| `devops-task-creator` | Create Jira tasks in the DEVOPS project with ADF-formatted Acceptance Criteria |
| `devops-task-retriever` | Fetch and parse a DEVOPS Jira issue, extract AC and Customer fields for DoD review |
| `gha-analyze` | Root cause analysis on a failed GitHub Actions run — fetches logs, identifies failure, suggests fixes |
| `gha-run` | Trigger and monitor a GHA workflow; chains to `gha-analyze` on failure |
| `monthly-customer-scheduling` | Pull Salesforce maintenance windows, map to Jira, create monthly Epic with deployment tickets |
| `named-build-tagging` | Tag multiple repos with the same version tag safely — dry-run, rollback, conflict detection |
| `pr-generator` | Analyze branch diff and generate a full PR description; waits for approval before creating |
| `request-triage` | Transform raw DevOps requests into structured MVRs with vault-based routing |
| `sonarqube-fixer` | Parse SonarQube JSON, categorize issues, fix with safety checks and commit strategy |
| `task-definition` | Decompose an approved Parent MVR into verifiable Child MVTs via the task-architect agent |
