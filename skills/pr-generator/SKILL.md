---
name: pr-generator
description: Generates pull request descriptions by analyzing code changes and filling PR templates. Use when creating pull requests, drafting PR descriptions, or preparing a PR. Analyzes actual code diffs and commit history to generate content.
allowed-tools: Bash(git:*), Read, Grep, Glob, AskUserQuestion
---

# Pull Request Generator

This skill generates comprehensive pull request descriptions by analyzing code changes and filling in the repository's PR template with a conventional commit-style title.

## Workflow

**CRITICAL: NEVER create the PR automatically. ALWAYS show the description and wait for explicit approval.**

### Step 1: Analyze Branch Changes

**Get the base branch first:**
```bash
# Common base branches: main, master, qa, develop
git remote show origin | grep 'HEAD branch'
```

**Analyze what changed on this branch:**

1. **Get commit list:**
   ```bash
   git log --oneline origin/qa..HEAD
   git log --format="%h - %s%n%b" origin/qa..HEAD
   ```

2. **Get file changes summary:**
   ```bash
   git diff --stat origin/qa..HEAD
   ```

3. **Get actual code changes:**
   ```bash
   git diff origin/qa..HEAD
   ```

4. **CRITICAL: Only analyze changes on the current branch. Never make assumptions about changes not in the diff.**

### Step 2: Find JIRA Ticket

Search for JIRA ticket references in this order:

1. **Branch name:**
   ```bash
   git branch --show-current
   ```
   Pattern: `JIRA-1234` or `DEVOPS-123` etc.

2. **Commit messages:**
   ```bash
   git log --format="%s %b" origin/qa..HEAD | grep -oE '[A-Z]+-[0-9]+'
   ```

**If found:** Present to user: "Found JIRA ticket: JIRA-1234. Is this correct?"

**If not found:** Ask user: "No JIRA ticket found in branch or commits. What ticket should this PR be associated with?"

### Step 3: Generate Conventional Commit Title

Based on the code analysis, determine the type:

**Types:**
- **feat:** New functionality, features, or capabilities added
- **fix:** Bug fixes, error corrections, issue resolutions
- **refactor:** Code restructuring without behavior change
- **docs:** Documentation only changes
- **test:** Adding or updating tests
- **chore:** Build, configuration, dependencies, tooling
- **perf:** Performance improvements
- **style:** Code formatting, whitespace, style changes

**Title format:** `<type>: <brief description>`

**Guidelines:**
- Keep under 72 characters
- Use imperative mood ("add" not "added" or "adds")
- Be specific but concise
- Focus on the "what" not the "how"

**Examples:**
- `feat: add user authentication with JWT`
- `fix: prevent memory leak in event handlers`
- `refactor: simplify database connection logic`
- `docs: add API documentation for v2 endpoints`

**Present the title to the user and request approval:**
```
I've analyzed the code changes and suggest this PR title:

feat: add search functionality to user list

Is this title acceptable, or would you like me to revise it?
```

**Wait for approval before proceeding.**

### Step 4: Fill PR Template

**Find the template:**
```bash
# Check common locations
if [ -f .github/pull_request_template.md ]; then
  cat .github/pull_request_template.md
elif [ -f .github/PULL_REQUEST_TEMPLATE.md ]; then
  cat .github/PULL_REQUEST_TEMPLATE.md
elif [ -f pull_request_template.md ]; then
  cat pull_request_template.md
fi
```

**Fill each section based on code analysis:**

#### Overview
- Synthesize code changes into 1-2 sentences
- Focus on **what** changed and **why** (infer from context)
- High-level business value, not technical details
- **Base only on actual code changes visible in the diff**

#### Related Tickets/PRs
- Use the JIRA ticket from Step 2
- Format as Atlassian URL:
  ```markdown
  - Closes: https://{jira_domain}/browse/JIRA-1234
  ```

#### Changelog
- Convert code changes to bulleted list
- Describe **what** was done, based on actual diffs:
  - New files added
  - Modified functions/classes
  - Deleted code
  - Configuration changes
- Group by functional area or file
- Be specific but concise
- **Only include changes visible in git diff**

**Example from code analysis:**
```markdown
- Add `SearchBar` component in `components/SearchBar.tsx`
- Implement client-side filtering in `UserList.tsx`
- Add search input state management
- Update user list to filter based on search term
```

#### Test Plan
- Generate checklist based on code changes
- Infer test scenarios from the changes:
  - New features: happy path + edge cases
  - Bug fixes: regression test
  - Refactors: verify behavior unchanged
- Mark as `[ ]` (unchecked) - user will check them off
- Be specific to the actual changes made

**Example:**
```markdown
- [ ] Verified search filters users correctly
- [ ] Tested with empty search term returns all users
- [ ] Confirmed case-insensitive search works
- [ ] Tested search with special characters
- [ ] Validated search updates on input change
```

#### Review Requests
- Identify complex areas from code analysis:
  - Large refactors
  - New patterns or architectures
  - Performance-critical code
  - Security-sensitive changes
  - Complex logic
- Suggest specific review focus areas
- Leave blank if straightforward changes

**Example:**
```markdown
- Please review the new filtering logic in `UserList.tsx:45-67` for performance
- Feedback welcome on the component structure
```

#### Deployment Requirements
- Analyze code for deployment needs:
  - Database migrations (look for migration files)
  - Environment variables (look for `.env` examples or config changes)
  - Configuration file changes
  - Infrastructure updates (Docker, K8s files)
  - Dependency changes (package.json, requirements.txt, etc.)
- List specific steps needed
- If none found, state: "No deployment changes required"

**Example:**
```markdown
- Install new dependencies: `npm install`
- No environment variable changes needed
```

#### Risk
- Assess based on code analysis:
  - **Low:** Small changes, isolated scope, well-tested
  - **Medium:** New features, moderate scope, some user impact
  - **High:** Breaking changes, large refactors, critical systems
- Consider:
  - Number of files changed
  - Complexity of changes
  - User-facing impact
  - Database/infrastructure changes
- Provide brief justification

**Example:**
```markdown
**Low Risk**
- Client-side only changes
- No API or database modifications
- Backward compatible
- Isolated to user list component
```

### Step 5: Present Complete PR Description

**Format:**
```
Here's the complete PR description based on the code analysis:

Title: feat: add search functionality to user list

---
[FULL PR BODY FROM TEMPLATE]
---

Should I create this pull request?
```

**Wait for explicit approval** (e.g., "yes", "looks good", "create it").

### Step 6: Create PR (Only After Approval)

```bash
gh pr create --title "feat: add search functionality to user list" --base qa --body "$(cat <<'EOF'
# Overview
Adds search functionality to filter users by name and email on the user list page.

# Related Tickets/PRs
- Closes: https://{jira_domain}/browse/JIRA-1234

# Changelog
- Add SearchBar component in components/SearchBar.tsx
- Implement client-side filtering in UserList.tsx
- Add search input state management
- Update user list to filter based on search term

# Test Plan
- [ ] Verified search filters users correctly
- [ ] Tested with empty search term returns all users
- [ ] Confirmed case-insensitive search works
- [ ] Tested search with special characters

# Review Requests
N/A

# Deployment Requirements
No deployment changes required

# Risk
**Low Risk**
- Client-side only changes
- No API or database modifications
EOF
)"
```

## Code Analysis Guidelines

### Understanding Changes

**For new files:**
- Note the file path and purpose
- Describe what the file does

**For modified files:**
- Look at the diff to understand what changed
- Focus on function/method changes
- Note deleted vs added code

**For deleted files:**
- Mention what was removed and why (if clear)

### Inferring Intent

From code changes, infer:
- **New functions/classes:** New feature or capability
- **Modified logic:** Bug fix, enhancement, or refactor
- **Deleted code:** Cleanup, deprecation, or simplification
- **Test additions:** Testing new or existing functionality
- **Config changes:** Deployment or environment updates

### Example Code Analysis

**Diff shows:**
```diff
+ import SearchBar from './SearchBar'
+ const [searchTerm, setSearchTerm] = useState('')
+ const filteredUsers = users.filter(u =>
+   u.name.toLowerCase().includes(searchTerm.toLowerCase())
+ )
```

**Analysis:**
- New import: SearchBar component added
- New state: searchTerm for managing search input
- New filtering logic: filters users by name, case-insensitive
- **Changelog entry:** "Add search functionality with case-insensitive name filtering"

## Common Patterns

### Pattern: New Feature
**Code shows:**
- New component files
- New functions
- New state management
- Tests for new functionality

**Generated:**
- **Title:** `feat: <description>`
- **Overview:** Focus on user value
- **Changelog:** List new components, functions, features
- **Test Plan:** Cover happy path and edge cases
- **Risk:** Medium (new functionality)

### Pattern: Bug Fix
**Code shows:**
- Modified existing function
- Added edge case handling
- Added regression test

**Generated:**
- **Title:** `fix: <description of bug>`
- **Overview:** What bug was fixed
- **Changelog:** Specific code changes
- **Test Plan:** Regression test for the bug
- **Risk:** Low (targeted fix)

### Pattern: Refactor
**Code shows:**
- Renamed functions
- Extracted methods
- Reorganized files
- No behavior change

**Generated:**
- **Title:** `refactor: <what was refactored>`
- **Overview:** Why refactor was done
- **Changelog:** Structural changes
- **Test Plan:** Verify behavior unchanged
- **Risk:** Low-Medium (depending on scope)

## Error Handling

**If cannot determine base branch:**
- Ask user: "What branch should this PR target? (main/qa/develop)"

**If no changes found:**
- Inform user: "No changes found between current branch and base. Have you committed your changes?"

**If diff is too large to analyze:**
- Focus on file-level changes (--stat output)
- Ask user for context: "This PR has many changes. Can you describe the main purpose?"

**If PR template not found:**
- Use generic template structure with the same sections
- Inform user: "Using standard PR format (no template found)"

## Integration with Workflow Policy

This skill enforces your PR creation policy:
1. ✅ Analyzes actual code changes (not assumptions)
2. ✅ Finds or prompts for JIRA ticket
3. ✅ Generates conventional commit title and gets approval
4. ✅ Generates complete PR description
5. ✅ Presents for review before creation
6. ✅ Waits for explicit approval
7. ✅ Only creates PR after "yes" confirmation

**Invocation phrases:**
- "Create a pull request"
- "Generate a PR"
- "Draft a PR description"
- "Prepare a pull request"
- "Make a PR"
