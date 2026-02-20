# GHA Analyze

Performs root cause analysis on GitHub Actions workflow runs.

## Purpose

This skill is designed to **analyze failures** and provide actionable fixes. Use it when you need Gemini to investigate why a workflow failed.

## Usage

```bash
/gha-analyze <run-id>
```

**Example:**
```bash
/gha-analyze 12345678
```

## What It Does

1. Fetches comprehensive workflow metadata (name, branch, SHA, event type)
2. Lists all jobs and their status
3. Retrieves logs from failed steps only
4. **Explicitly asks Gemini to perform RCA:**
   - Identify root cause
   - Explain why it happened
   - Suggest specific fixes

## Workflow with gha-run

These two skills work together:

### 1. Run (for status checking)
```bash
/gha-run deploy.yml main
```
- Triggers workflow
- Monitors completion
- Shows clean status report

### 2. Analyze (for troubleshooting)
```bash
# Get the run ID from monitor output, then:
/gha-analyze 12345678
```
- Fetches detailed failure logs
- **Performs RCA** and suggests fixes

## When to Use

- ✅ Workflow failed and you need to know why
- ✅ Tests are failing and you need root cause
- ✅ Deployment failed and you need a fix
- ✅ You have a run ID from a failed workflow

## When NOT to Use

- ❌ Just checking if a workflow is running (use monitor)
- ❌ Workflow succeeded (nothing to analyze)
- ❌ You just want quick status (use monitor)

## Output Format

The skill outputs structured data that invites Claude's analysis:
- Workflow metadata (name, branch, SHA)
- Job summaries
- Failed step logs
- Explicit request for RCA

This format is designed to trigger Claude's analytical capabilities.
