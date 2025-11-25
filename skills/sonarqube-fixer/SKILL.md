---
name: sonarqube-fixer
description: Systematically analyze and fix SonarQube code quality issues. Categorizes issues by type (Python constructors, duplicated strings, shell script best practices), performs pre-flight safety checks, asks clarifying questions about TODOs and commit strategy, fixes issues methodically with edit safety validation, shows change verification before committing, and provides error recovery options. Use when working with SonarQube reports, code quality issues, static analysis results, or when you have SonarQube JSON output to process.
---

# SonarQube Issue Fixer

Automate fixing SonarQube code quality issues with comprehensive safety checks and error recovery.

## Workflow

### 1. Input & Validation

Accept SonarQube issue data in one of two formats:

**Option 1: JSON File Path**
- User provides path to SonarQube JSON export
- Read and parse the JSON file
- Validate file exists and is readable

**Option 2: Pasted JSON**
- User pastes SonarQube API response
- Parse the JSON from input

**JSON Structure Validation**:
```json
{
  "total": number,
  "issues": [
    {
      "key": "issue-id",
      "rule": "rule-id",
      "severity": "MINOR|MAJOR|CRITICAL|INFO",
      "component": "file-path",
      "line": number,
      "message": "description"
    }
  ],
  "components": [...]
}
```

**Validation Requirements**:
- Verify JSON is parseable
- Check `issues` array exists
- Check `components` array exists
- Verify each issue has: key, rule, severity, component, line, message
- If validation fails: Display error and EXIT

**Handle Empty Issues**:
- If `issues` array is empty or `total` is 0:
  - Display: "No issues found in SonarQube report"
  - EXIT gracefully

### 2. Parse & Categorize Issues

Group issues by:
- **File** (component path)
- **Rule type** (e.g., S7498, S1192, S7677, S7688, S1135)
- **Severity** (CRITICAL → INFO)
- **Language** (Python, Shell, YAML, etc.)

Display summary:
```
SonarQube Issues Summary
========================
Total Issues: 18

By Severity:
  CRITICAL: 1
  MAJOR: 7
  MINOR: 6
  INFO: 2

By Language:
  Python: 8 issues (3 files)
  Shell: 8 issues (2 files)
  YAML: 2 issues (2 files)

By Rule:
  S7498 (Python constructor calls): 6 issues
  S1192 (Duplicated literals): 2 issues
  S7677 (Shell stderr): 4 issues
  S7688 (Shell [[ vs [): 4 issues
  S1135 (TODO comments): 2 issues
```

### 3. Pre-Flight Safety Checks

**CRITICAL**: Perform ALL safety checks before proceeding with any fixes.

#### 3.1 Git Repository Check
```bash
git rev-parse --is-inside-work-tree
```
- Exit code 0: In git repo (proceed)
- Exit code non-zero: Not in git repo
  - Display: "ERROR: Not in a git repository. This skill requires git for safety."
  - EXIT

#### 3.2 Git Status Check
```bash
git status --porcelain
```
Parse output:
- If uncommitted changes exist (M, A, D, ??, etc.):
  - Display warning:
    ```
    ⚠️  WARNING: You have uncommitted changes:

    [show git status output]

    This skill will make additional changes. Consider:
    1. Commit or stash your current changes first
    2. Continue anyway (changes will be mixed)

    Continue? (yes/no)
    ```
  - If no: EXIT
  - If yes: Proceed (note this in final commit message)

#### 3.3 File Existence & Permission Check

For EACH file referenced in SonarQube issues:

**Read File** (REQUIRED):
```bash
Read tool with file_path
```
- If file doesn't exist:
  - Add to "missing files" list
  - Continue checking other files
- If file exists: Store content hash for later verification
- If file is not readable:
  - Add to "permission denied" list
  - Continue checking other files

**After checking all files**:
- If ANY files are missing or unreadable:
  - Display:
    ```
    ERROR: Cannot proceed - some files are missing or unreadable:

    Missing files:
      - path/to/file1.py
      - path/to/file2.sh

    Permission denied:
      - path/to/file3.yml

    These files were referenced in the SonarQube report but cannot be accessed.
    Possible reasons:
    - Files were deleted after scan
    - Files were moved/renamed
    - Insufficient permissions

    Please update your codebase or re-run SonarQube scan.
    ```
  - EXIT

#### 3.4 File Boundary Check

For each file path:
- Verify it's within the current project directory
- Reject any paths with:
  - `..` (parent directory escape)
  - Absolute paths outside project
  - Symlinks to external locations

If ANY file fails boundary check:
- Display: "ERROR: File [path] is outside project boundaries"
- EXIT

**Pre-Flight Success**:
If all checks pass, display:
```
✓ Pre-flight checks passed
  - Git repository: ✓
  - All files accessible: ✓ (N files)
  - File permissions: ✓
  - Security boundaries: ✓
```

### 4. Show Fix Summary (Confirmation Gate)

Display comprehensive summary BEFORE making any changes:

```
╔════════════════════════════════════════════════════════════╗
║                    Fix Summary                              ║
╚════════════════════════════════════════════════════════════╝

Files to modify: 5
Total issues to fix: 16

Breakdown by file:
┌─────────────────────────────────────────────┬────────┐
│ File                                        │ Issues │
├─────────────────────────────────────────────┼────────┤
│ ansible/action_plugins/prompt.py            │ 3      │
│ ansible/library/prompt.py                   │ 3      │
│ ansible/callback_plugins/wizard_minimal.py  │ 2      │
│ ansible/scripts/bootstrap_controller.sh     │ 2      │
│ ansible/scripts/run_preflight.sh            │ 6      │
└─────────────────────────────────────────────┴────────┘

Issue types:
  • Python S7498 (dict() → literal): 6 fixes
  • Python S1192 (extract constant): 1 fix
  • Shell S7677 (stderr redirect): 4 fixes
  • Shell S7688 ([ → [[): 4 fixes
  • Shell S1192 (extract constant): 1 fix

Estimated changes: ~35 lines across 5 files

Proceed with fixes? (yes/no)
```

**If user says no**: EXIT
**If user says yes**: Continue to step 5

**High File Count Warning**:
If modifying 10+ files, add additional warning:
```
⚠️  WARNING: This will modify 15 files. This is a large change set.
Consider reviewing issues in smaller batches.

Continue anyway? (yes/no)
```

### 5. Ask Clarifying Questions

#### 5.1 TODO Handling (Guardrail #11)

**CRITICAL**: NEVER auto-remove or auto-fix TODO comments without explicit user approval.

For EACH file with TODO issues (S1135):

Display the TODO context:
```
TODO found in [file]:[line]

Context:
  [show 3 lines before]
→ [show TODO line]
  [show 3 lines after]

How should this TODO be handled?

1. Keep TODO (ignore this issue)
   - Leaves code as-is
   - Will not fix this issue

2. Remove TODO (implement or resolve it)
   - I will help implement or clean up
   - Fixes the SonarQube issue

3. Convert to GitHub issue
   - Creates a GitHub issue with context
   - Removes TODO from code with reference
   - Fixes the SonarQube issue

Your choice (1/2/3):
```

Store decision for each TODO:
- **Keep**: Add to skip list, don't modify
- **Remove**: Include in fixes (user will handle separately)
- **Convert**: Create issue, replace with comment

**Skip List**:
If user chooses "Keep" for any TODO, maintain a skip list:
```
Skipped issues (user requested to keep):
  - [file]:[line] - TODO about Azure SSO
  - [file]:[line] - TODO about feature flag
```

#### 5.2 Commit Strategy

Ask once for all fixes:
```
How should these fixes be committed?

1. Single commit (recommended)
   - All fixes in one commit: "fix: address SonarQube issues"
   - Faster, simpler
   - Better for atomic changes

2. Multiple commits by language
   - Separate commits: Python fixes, Shell fixes, etc.
   - Better git history granularity
   - More commits to track

Your choice (1/2):
```

Store decision for commit step.

### 6. Fix Issues (with Edit Safety & Error Recovery)

**CRITICAL**: This step includes Guardrails #4 (Edit Safety) and #8 (Error Recovery)

Initialize tracking:
```
- Fixed files: [] (empty list)
- Failed files: [] (empty list)
- Syntax errors: [] (empty list)
```

#### 6.1 Process Issues by Category

Order of fixes:
1. Python constructor calls (S7498)
2. Python duplicated strings (S1192)
3. Shell stderr redirections (S7677)
4. Shell conditionals (S7688)
5. Shell duplicated strings (S1192)
6. Skipped TODOs (report only, no changes)

#### 6.2 Edit Safety (Guardrail #4)

For EACH file being edited:

**Before Edit**:
1. **Verify File Read** (REQUIRED):
   - Check if we read this file in step 3.3
   - If NOT: "FATAL ERROR: Attempting to edit file we haven't read"
   - EXIT immediately

2. **Line Number Verification**:
   - Compare current file content with SonarQube line references
   - If line content doesn't match expected:
     ```
     ⚠️  WARNING: File may have changed since SonarQube scan

     File: [path]
     Line: [line number]

     Expected (from SonarQube):
       [expected content]

     Actual (current file):
       [actual content]

     The file may have been modified after the scan.

     Continue with this fix? (yes/no/show-diff)
     ```
   - **yes**: Proceed with edit
   - **no**: Skip this file, add to "skipped files" list
   - **show-diff**: Display full context, ask again

**During Edit**:
3. Use Edit tool with exact old_string and new_string
4. Verify edit succeeded (no error from Edit tool)

**After Edit**:
5. **Syntax Validation** (CRITICAL):

   For Python files:
   ```bash
   python3 -m py_compile [file]
   ```
   - Exit code 0: Syntax valid
   - Exit code non-zero: **SYNTAX ERROR**

   For Shell scripts:
   ```bash
   bash -n [file]
   ```
   - Exit code 0: Syntax valid
   - Exit code non-zero: **SYNTAX ERROR**

   **If syntax validation fails**:
   - IMMEDIATELY trigger Error Recovery (step 6.3)
   - DO NOT CONTINUE to next file

6. **Track Success**:
   - Add file to "fixed files" list
   - Record: `{file: path, issues_fixed: count}`

#### 6.3 Error Recovery (Guardrail #8)

**Trigger on ANY of**:
- Syntax validation failure
- Edit tool failure
- Unexpected error during fixing

**Immediate Actions**:
1. **STOP IMMEDIATELY** - do not attempt to fix more files
2. Record the error details
3. Show current state:
   ```
   ╔════════════════════════════════════════════════════════════╗
   ║                    ERROR OCCURRED                           ║
   ╚════════════════════════════════════════════════════════════╝

   Error: [error message]

   Progress before error:
   ✓ Successfully fixed: [count] files
     - file1.py (3 issues)
     - file2.sh (2 issues)

   ✗ Failed at: [current file]
     Error: [specific error]

   ⧗ Not attempted: [count] files remaining

   Repository Status:
   - Modified files: [count]
   - All changes are uncommitted
   ```

4. **Offer Recovery Options**:
   ```
   How would you like to proceed?

   1. Revert ALL changes (git reset --hard)
      - Returns to clean state
      - Loses all fixes made so far
      - Safest option

   2. Keep changes and fix manually
      - Keeps successful fixes
      - You manually fix the error
      - Can commit partial progress

   3. Show me the specific error details
      - Display full error output
      - Show file diff for failed file
      - Then return to this menu

   Your choice (1/2/3):
   ```

5. **Execute User Choice**:

   **Choice 1 - Revert**:
   ```bash
   git reset --hard HEAD
   git clean -fd
   ```
   - Confirm: "All changes reverted. Repository is clean."
   - EXIT

   **Choice 2 - Keep**:
   - Display git status
   - Provide commands:
     ```
     Changes kept. To review:
       git status
       git diff

     To commit partial progress:
       git add [files]
       git commit -m "fix: partial SonarQube fixes"

     To revert later:
       git reset --hard HEAD
     ```
   - EXIT

   **Choice 3 - Show Details**:
   - Display full error
   - Show `git diff [failed-file]`
   - Return to recovery options menu

**Never Continue After Error**:
- Do NOT attempt to fix remaining files
- Do NOT try alternative approaches automatically
- Do NOT commit partial changes automatically
- Let user decide recovery path

#### 6.4 Success Tracking

After ALL files processed successfully (no errors):
```
✓ All fixes completed successfully

Summary:
  Files modified: [count]
  Issues fixed: [count]
  Syntax validation: ✓ All passed
```

Proceed to step 7 (Change Verification).

### 7. Change Verification (Guardrail #6)

Display comprehensive diff summary before commit:

#### 7.1 Git Diff Summary
```bash
git diff --stat
```

Display:
```
╔════════════════════════════════════════════════════════════╗
║                  Change Verification                        ║
╚════════════════════════════════════════════════════════════╝

Modified Files:
  ansible/action_plugins/prompt.py          | 6 +--
  ansible/callback_plugins/wizard_minimal.py| 4 +-
  ansible/library/prompt.py                 | 6 +--
  ansible/scripts/bootstrap_controller.sh   | 4 +-
  ansible/scripts/run_preflight.sh          | 12 ++--

  5 files changed, 18 insertions(+), 14 deletions(-)
```

#### 7.2 Per-File Change Summary

For each file:
```bash
git diff [file] --numstat
```

Display:
```
File: ansible/action_plugins/prompt.py
  Lines changed: +3, -3
  Issues fixed:
    • S7498: Replaced dict() with {} (lines 20, 35, 42)
```

#### 7.3 Highlight Risky Changes

**Scan diffs for risky patterns**:
- Changes to `except` blocks
- Changes to `if`/`elif` conditions
- Changes to `return` statements
- Changes near `auth`, `password`, `token`, `secret`
- Changes to error handling

If risky changes detected:
```
⚠️  ATTENTION: Some changes may need careful review:

  ansible/callback_plugins/wizard_minimal.py:54
    Changed error message handling
    - Old: inline string 'ERROR: %s'
    + New: class constant ERROR_FORMAT

  ansible/scripts/run_preflight.sh:68
    Changed error output redirection
    + Added: >&2 (redirect to stderr)

These changes look safe but verify they don't affect:
  - Error handling behavior
  - Logging/monitoring integrations
  - Downstream error consumers
```

#### 7.4 Final Verification Prompt

```
Review changes above. Do you want to:

1. View full diff (git diff)
2. View specific file diff
3. Proceed to commit
4. Cancel (revert all changes)

Your choice (1/2/3/4):
```

**Execute Choice**:
- **1**: Run `git diff`, display output, return to menu
- **2**: Ask which file, run `git diff [file]`, return to menu
- **3**: Proceed to step 8 (Commit)
- **4**: Run `git reset --hard`, display "Changes reverted", EXIT

### 8. Commit (Confirmation Gate #7)

#### 8.1 Generate Commit Message

Build conventional commit message:

```
fix: address SonarQube code quality issues

Resolves [count] code quality issues identified by SonarQube:
- Python: Replace dict() constructor calls with literal syntax (S7498)
- Python: Extract duplicated error message string to constant (S1192)
- Shell: Add stderr redirection (>&2) to error messages (S7677)
- Shell: Replace [ with [[ for safer conditional tests (S7688)
- Shell: Extract duplicated separator line to constant (S1192)

[if TODOs were kept, add:]
Skipped TODOs (user requested to keep):
- [file]:[line] - Azure SSO feature (planned for future)

[if uncommitted changes existed:]
Note: Pre-existing uncommitted changes were present in repository.

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>
```

#### 8.2 Commit Confirmation (Final Gate)

**CRITICAL**: ALWAYS show commit message and ask for approval before committing.

```
╔════════════════════════════════════════════════════════════╗
║              Ready to Commit                                ║
╚════════════════════════════════════════════════════════════╝

Commit message:
─────────────────────────────────────────────────────────────
[show full commit message above]
─────────────────────────────────────────────────────────────

Files to be committed: [count]
[list files]

Would you like me to commit these changes? (yes/no/edit)
```

**Response Options**:
- **yes**: Proceed with commit
- **no**: Stop, don't commit (changes remain staged)
- **edit**: Allow user to modify commit message, ask again

#### 8.3 Execute Commit

**Stage files**:
```bash
git add [file1] [file2] [file3] ...
```

**Create commit**:
```bash
git commit -m "[commit message]"
```

**Verify commit**:
```bash
git log -1 --oneline
```

#### 8.4 Display Success

```
✓ Commit created successfully

Commit: [short-sha] - fix: address SonarQube code quality issues

Summary:
  Issues fixed: [count]
  Files changed: [count]
  Lines changed: +[insertions] -[deletions]

Your changes have been committed locally.
To push: git push origin [branch]
```

## Error Handling Philosophy

### Safety-First Approach

1. **Validate Early**: Check everything before making changes
2. **Fail Fast**: Stop immediately on any error
3. **Never Guess**: Always ask user for ambiguous decisions
4. **Provide Options**: Give user control over recovery
5. **Clear State**: Always show what was done and what remains

### Never Auto-Proceed Through

- File permission errors
- Syntax validation failures
- Missing files
- TODO removals
- Commits without confirmation
- Recovery without user choice

### Always Provide Rollback

Every step that modifies state includes:
- Clear description of what changed
- Commands to undo the change
- Current repository status
- User choice in how to proceed

## Examples

### Example 1: Basic Usage

```
User: I have SonarQube issues to fix
[pastes JSON]

Skill:
1. Parses 16 issues
2. Shows summary by language/severity
3. Runs pre-flight checks (all pass)
4. Shows fix summary (5 files, 16 issues)
5. Asks about TODOs (user chooses "keep")
6. Asks commit strategy (user chooses "single commit")
7. Fixes all issues with syntax validation
8. Shows change verification
9. Displays commit message, user approves
10. Commits successfully
```

### Example 2: Error Recovery

```
User: Fix these SonarQube issues
[pastes JSON]

Skill:
1. Parses issues, runs pre-flight (pass)
2. Shows summary, user approves
3. Fixes file1.py ✓
4. Fixes file2.py ✓
5. Fixes file3.sh ✗ SYNTAX ERROR
   - STOPS immediately
   - Shows: 2 files fixed, 1 failed, 3 remaining
   - Offers options:
     1. Revert all (git reset)
     2. Keep partial progress
     3. Show error details
   - User chooses: Show details
   - Displays error and diff
   - User chooses: Keep partial progress
6. Exits with partial fixes committed
```

### Example 3: File Changed Since Scan

```
User: Fix SonarQube issues
[provides JSON]

Skill:
1. Pre-flight checks pass
2. Attempts to fix script.sh
3. Detects line mismatch
   ⚠️  WARNING: File may have changed
   Expected: old_function_call()
   Actual: new_function_call()

   Continue? (yes/no/show-diff)

User: show-diff
Skill: [displays context]
User: no
Skill: Skipped script.sh, continues with other files
```

## Configuration

No configuration file needed - all decisions made interactively during execution.

User preferences are asked on each run:
- TODO handling (per-TODO decision)
- Commit strategy (single vs multiple)
- Recovery options (if errors occur)

## Notes

- This skill requires git for safety (rollback capability)
- All changes are syntax-validated before commit
- User maintains full control through confirmation gates
- Partial progress can be committed if errors occur
- Never modifies files outside project boundaries
