---
name: named-build-tagging
description: Automates creating and pushing identical git tags across multiple repositories. Walks you through selecting commits for each repo (defaulting to latest on default branch), validates all operations before making changes, performs dry-run pushes to catch errors, and provides a summary of results. Includes safety features like automatic rollback on errors and tag conflict detection. Use this when you need to tag multiple repositories with the same version tag and description in a coordinated, safe manner.
---

# Named Build Tagging

Automate tagging multiple repositories with the same tag name and description.

## Script-Based Architecture

This skill uses dedicated bash scripts located in the `scripts/` directory to ensure:
- **Absolute path enforcement** - Scripts validate and require absolute paths
- **Consistent behavior** - No command improvisation possible
- **Reliable error handling** - All scripts use proper exit codes
- **DRY principle** - Common logic shared via `common.sh` library

### Available Scripts

All scripts are located in `scripts/` directory relative to this skill:

- **common.sh** - Shared library (sourced by other scripts)
- **validate_repositories.sh** - Validates repository paths
- **get_commit_info.sh** - Gets commit information
- **validate_branch.sh** - Validates branch exists
- **validate_commit.sh** - Validates commit SHA exists
- **check_tag_exists.sh** - Checks if tag exists, outputs "FOUND <SHA>" or "NOT_FOUND"
- **create_tag.sh** - Creates annotated tag
- **delete_tag.sh** - Deletes local tag (for rollback)
- **dry_run_push.sh** - Performs dry-run push validation
- **push_tag.sh** - Pushes tag to remote

### CRITICAL EXECUTION RULES

**EXTREMELY IMPORTANT - HIGHEST PRIORITY DIRECTIVE**:

1. **ONLY use scripts from the `scripts/` directory** - Do NOT create inline bash commands
2. **ALWAYS pass absolute paths to scripts** - Scripts will reject relative paths
3. **If ANY script fails:**
   - Use recorded cleanup commands to revert all local tag changes made so far
   - Display the error message to the user
   - Exit IMMEDIATELY - do NOT investigate, try alternatives, show options, list branches, or continue
   - Let the user decide how to proceed

### Script Path Resolution

Get the scripts directory path dynamically at the start of execution:
```bash
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPTS_DIR="$SKILL_DIR/scripts"
```

Or if running from Claude Code context, use the skill base directory provided by the environment.

All script calls must use the `$SCRIPTS_DIR` variable.

## Workflow

You are helping the user create and push identical tags across multiple repositories. Follow this process:

### 0. Configuration Setup

Check if the `.env` file exists in the skill directory.

**If .env file EXISTS:**
- Read the `DEFAULT_CONFIGURATION_FILE_PATH` value
- Continue to step 1

**If .env file does NOT exist:**

Prompt the user with options:

```
Configuration file not found. Please choose an option:

1. Enter the path to your existing configuration file
2. Create me an example configuration file
```

**Option 1 - User provides a path:**
1. Verify the file exists at the provided path
2. Verify the file contains valid JSON structure (can be parsed)
3. Create the `.env` file with:
   ```
   DEFAULT_CONFIGURATION_FILE_PATH=[user-provided-path]
   ```
4. Continue to step 1 (do NOT validate repository paths yet)

**Option 2 - Create example configuration:**
1. Ask user for the path where they want to create the config file
   - Default: Current working directory + `/named-build-tagging-config.json`
   - Display: "Where would you like to create the configuration file? (default: [current-dir]/named-build-tagging-config.json)"
2. Create a sample JSON file at that location with this structure:
   ```json
   {
     "repositories": [
       {
         "name": "Example Service 1",
         "path": "/path/to/your/repository1"
       },
       {
         "name": "Example Service 2",
         "path": "/path/to/your/repository2"
       }
     ]
   }
   ```
3. Create the `.env` file with:
   ```
   DEFAULT_CONFIGURATION_FILE_PATH=[created-file-path]
   ```
4. Display message and EXIT:
   ```
   ✓ Created example configuration file at: [path]
   ✓ Created .env file

   Please edit the configuration file to add your repository paths, then re-run this skill.
   ```

### 1. Load Repository Configuration

Read the repository configuration from the path specified in the `.env` file (`DEFAULT_CONFIGURATION_FILE_PATH`).

Expected JSON structure:
```json
{
  "repositories": [
    {
      "name": "My Service",
      "path": "/path/to/repo"
    }
  ]
}
```

If the file doesn't exist or has invalid JSON:
- Display error message
- EXIT

### 2. Pre-flight Repository Validation

**CRITICAL**: Before doing ANY git operations, validate all repositories exist.

Use the validation script with absolute paths:
```bash
$SCRIPTS_DIR/validate_repositories.sh "/absolute/path1" "/absolute/path2" "/absolute/path3"
```

**Script output:**
- `OK: /path` - Repository is valid
- `MISSING: /path` - Directory doesn't exist
- `NOT A GIT REPO: /path` - Directory exists but isn't a git repository
- `Error: Path must be absolute: path` - Relative path was provided (exits immediately)

**Exit code:** 0 if all valid, 1 if any invalid

If ANY repository is missing or invalid:
- Display which repositories are missing/invalid
- **EXIT immediately** - do not proceed with any operations

This ensures we don't partially complete work before discovering a missing repo.

### 3. Get Tag Information

Prompt the user for:
- **Tag name**: The name of the tag to create (e.g., "v1.2.3", "release-2024-10")
- **Tag description**: A description for the tag (will be used as the annotated tag message)

### 4. Gather Commit Information

For each repository in the config, get commit information from the default branch:

```bash
$SCRIPTS_DIR/get_commit_info.sh "/absolute/path/to/repo"
```

**Script output** (one per line):
1. Short commit SHA
2. Commit message (first line)
3. Author and date
4. Branch/ref name used

**Example:**
```
7fe332f
feat: Check Extraction (MICR Line) (#53)
Prakhar Sinha on 2025-10-22
main
```

Parse this output and display to the user in a clear format:
```
Repository: [name]
Path: [path]
Default Branch: [branch]
Latest Commit: [short-sha] - [message]
Author: [author] on [date]
```

### 5. Confirm or Select Commits

For each repository, ask the user:
- "Use the latest commit shown above? (yes/no)"
- If no, prompt the user with options:
  - Enter a **branch name** to use the latest commit from that branch
  - Enter a **commit SHA** to use a specific commit

**Branch validation:**
```bash
$SCRIPTS_DIR/validate_branch.sh "/absolute/path/to/repo" "branch-name"
```
- Exit code 0: Branch exists
- Exit code 1: Branch doesn't exist
- If validation fails:
  - Display error message: "Branch [branch-name] not found in repository [name]"
  - **EXIT immediately** - do not investigate, show branch lists, or continue
  - Let the user verify the correct branch name and re-run the skill

**Commit SHA validation:**
```bash
$SCRIPTS_DIR/validate_commit.sh "/absolute/path/to/repo" "commit-sha"
```
- Exit code 0: Commit exists
- Exit code 1: Commit doesn't exist
- If validation fails:
  - Display error message: "Commit [sha] not found in repository [name]"
  - **EXIT immediately** - do not re-prompt or continue
  - Let the user verify the correct commit SHA and re-run the skill

**When a branch name or commit SHA is provided:**
1. Validate it exists using the appropriate script above
2. Fetch the commit information:
   ```bash
   $SCRIPTS_DIR/get_commit_info.sh "/absolute/path/to/repo" "branch-or-sha"
   ```
3. Display the commit information (SHA, message, author, date)
4. Confirm with the user before proceeding

Store the selected commit SHA for each repository.

### 6. Check for Existing Tags (ALL Repositories)

**CRITICAL**: This validation must be completed for ALL repositories before proceeding to step 7.

For each repository and its selected commit, check if the tag already exists:

```bash
$SCRIPTS_DIR/check_tag_exists.sh "/absolute/path/to/repo" "tag-name"
```

**Script behavior:**
- Always exits with code 0
- Output: "FOUND <SHA>" if tag exists, "NOT_FOUND" if it doesn't exist

**Parse the output:**
- If output starts with "FOUND": Extract the SHA that follows
- If output is "NOT_FOUND": Tag doesn't exist, no action needed

**If the tag exists (output starts with "FOUND"):**
1. Extract the SHA from the output (second word after "FOUND")
2. Compare with the selected commit SHA:

   **If SHAs match:**
   - Display: "Tag '[tag-name]' already exists at commit [sha] in [repo-name]"
   - Mark this repository for description-only update (use `--force` flag)
   - Continue checking other repositories

   **If SHAs do NOT match:**
   - Display: "Tag '[tag-name]' exists at [existing-sha] but you want to tag [selected-sha] in [repo-name]"
   - Prompt: "Do you want to override the existing tag? (yes/no)"
   - If no: **EXIT immediately** - do not create any tags
   - If yes: Mark this repository for force tag creation (use `--force` flag) and continue checking

Complete this check for ALL repositories before moving to step 7. This ensures we have user approval for all overrides before making any local changes.

### 7. Create Tags Locally

For each repository with its selected commit:

1. Create an annotated tag:
   ```bash
   $SCRIPTS_DIR/create_tag.sh "/absolute/path/to/repo" "tag-name" "commit-sha" "tag-description"
   ```

   Or with force flag if overriding:
   ```bash
   $SCRIPTS_DIR/create_tag.sh "/absolute/path/to/repo" "tag-name" "commit-sha" "tag-description" --force
   ```

   **Exit code:** 0 if successful, 1 if failed

2. **Record the cleanup command**: Store the delete command for this tag:
   ```bash
   $SCRIPTS_DIR/delete_tag.sh "/absolute/path/to/repo" "tag-name"
   ```
   Keep a list of these commands for each repository where a tag was successfully created.

3. Handle any errors gracefully - if ANY error occurs:
   - Execute the recorded cleanup commands to **REVERT all local tag changes** that were successfully created
   - Display the error
   - **EXIT**

**Do NOT push yet** - all tags must be created locally first.

**Maintain cleanup command list**: As each tag is successfully created, add the cleanup command to a list. This list will be used if we need to revert.

### 8. Dry Run Push Validation

Before pushing any tags, perform a dry run to validate pushes will succeed:

```bash
$SCRIPTS_DIR/dry_run_push.sh "/absolute/path/to/repo" "tag-name"
```

**Exit code:** 0 if dry run succeeds, 1 if failed
**Output:** The output from `git push --dry-run`

For each repository:
1. Run the dry-run push script
2. Check the exit code and output for errors (rejected pushes, authentication issues, etc.)
3. Collect any errors

If ANY dry run fails:
- Display all errors found during dry run
- Execute the recorded cleanup commands to **REVERT all local tag changes across all repositories**
- **EXIT** - do not proceed with actual pushes

This ensures we catch ALL potential push errors before making any remote changes.

### 9. Push Tags to Remote

Only if all dry runs succeeded, proceed with actual pushes:

For each repository:
1. Push the tag to remote:
   ```bash
   $SCRIPTS_DIR/push_tag.sh "/absolute/path/to/repo" "tag-name"
   ```

   Or with force flag if overriding:
   ```bash
   $SCRIPTS_DIR/push_tag.sh "/absolute/path/to/repo" "tag-name" --force
   ```

   **Exit code:** 0 if successful, 1 if failed

2. If the push fails:
   - Display the error message
   - **EXIT immediately** - do not continue pushing to other repositories

3. Track success for the summary (only reached if all pushes succeed)

### 10. Provide Summary

After all tags are created and pushed, display a summary table:

```
=== Tagging Summary ===

Tag Name: [tag-name]
Tag Description: [tag-description]

Repositories Tagged:
┌─────────────────────┬──────────────┬────────────┐
│ Repository          │ Commit SHA   │ Status     │
├─────────────────────┼──────────────┼────────────┤
│ [name]             │ [short-sha]  │ ✓ Success  │
│ [name]             │ [short-sha]  │ ✗ Failed   │
└─────────────────────┴──────────────┴────────────┘
```

Include any error messages for failed operations.

## Error Handling Philosophy

**Safety First**: The goal is to catch ALL errors BEFORE making remote changes.

- Validate configuration file exists and is valid JSON (step 0)
- Validate all repository paths exist before starting (step 2)
- Validate all branches and commit SHAs before proceeding (step 5)
- Check for tag conflicts in ALL repositories before creating any local tags (step 6)
- Record cleanup commands as tags are created locally (step 7)
- Create all tags locally before pushing (step 7)
- Dry run all pushes before actual pushes (step 8)
- For ANY unhandled error at ANY step:
  - Use recorded cleanup commands to **REVERT all local tag changes**
  - Display clear error message
  - **EXIT immediately**

This ensures we never leave repositories in an inconsistent state and never push problematic tags.

## Configuration Files

### .env File
Located in the skill directory, contains:
```
DEFAULT_CONFIGURATION_FILE_PATH=/path/to/your/config.json
```

This file is gitignored. Use `example.env` as a template.

### Repository Configuration File
Location specified in `.env` file. JSON structure:
```json
{
  "repositories": [
    {
      "name": "Frontend Service",
      "path": "/home/user/projects/frontend"
    },
    {
      "name": "Backend API",
      "path": "/home/user/projects/backend"
    }
  ]
}
```
