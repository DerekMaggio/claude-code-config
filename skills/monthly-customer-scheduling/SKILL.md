---
name: monthly-customer-scheduling
description: Retrieves customer maintenance windows from Salesforce, validates schedules, maps to Jira fields, and creates a monthly Epic with Customer Deployment tickets.
allowed-tools: [Bash, AskUserQuestion, mcp__atlassian__createJiraIssue, mcp__atlassian__getJiraIssueTypeMetaWithFields]
---

# Monthly Customer Scheduling

## 1. Purpose
Automates the monthly maintenance scheduling workflow by:
1. Pulling customer/server maintenance data from Salesforce.
2. Mapping Salesforce Customer Names to Jira "HuLoop Customer" custom field options.
3. Calculating deployment dates/times with correct Pacific Time offsets.
4. Validating all windows for safety.
5. Creating a Jira Epic (Classic Project) with Customer Deployment tickets.

## 2. Trigger
Invoke when requested to "schedule monthly maintenance," "create maintenance tickets," or "set up deployment windows for [Month]."

**Mode Exemption:** This skill is exempt from the Mode A / Mode B engagement gates. When invoked, skip mode selection and execute the workflow directly.

## 3. Workflow Logic

### Step A: Target Month Selection
1. Ask the user for the target month and year (e.g., "March 2026").
2. Store as `TARGET_MONTH` and `TARGET_YEAR`.

### Step B: Salesforce Binary & Auth Verification
1. Locate the `sf` binary.
2. Run `sf org list auth --json`.
3. **If not logged in** (`"result": []`):
   - Run `sf org login web` and wait for completion.
4. **If logged in**:
   - Run `sf alias set huloop=<username>` to ensure the alias is active.

### Step C: Data Extraction
Execute the helper script to retrieve customer/server maintenance records:

```bash
bash skills/monthly-customer-scheduling/helper_scripts/fetch_maintenance_data.sh
```

**Important:** The `maintenance_start` and `maintenance_end` times from Salesforce are in **Pacific Time** (PST/PDT). These must be converted to ISO 8601 with the correct offset in Step E.

### Step D: Jira Metadata & Field Mapping (Crucial Step)
Before calculating dates, fetch Jira metadata to ensure correct field mapping for a Classic Project.

1. **Fetch Field Data:**
   ```
   Tool: mcp__atlassian__getJiraIssueTypeMetaWithFields
   - cloudId: be0a9935-763b-48a6-b39b-38d8207312fb
   - projectIdOrKey: DEVOPS
   - issueTypeId: 10244 (Customer Deployment)
   ```

2. **Locate "Epic Link" Field:**
   - Since this is a **Classic Project**, look for a custom field explicitly named "Epic Link" (e.g., `customfield_10008` or similar).
   - Store this Field ID as `EPIC_LINK_FIELD_ID`.
   - *Note: If no specific "Epic Link" field is found, fallback to using the `parent` field, but prioritize the custom field.*

3. **Build Customer Lookup Map:**
   - Locate `customfield_10962` (HuLoop Customer).
   - Create a mapping dictionary: `{ "lowercase_jira_name": "option_id" }`.

### Step E: Date Calculation & Data Merging
For each server in the Salesforce JSON:

1. **Calculate Date:**
   - Run `python3 skills/monthly-customer-scheduling/helper_scripts/calculate_next_deployment.py [WEEK] [DAY] [MONTH] [YEAR]`.
   - **CRITICAL:** Do not "guess" or do mental math. If the script errors (e.g., "No 5th Wednesday"), mark the Date as "ERROR".

2. **Calculate ISO 8601 Times (Timezone Aware):**
   - Determine if the date falls in PST (`-08:00`) or PDT (`-07:00`).
   - Construct `deployment_window_begin`: `YYYY-MM-DDTHH:MM:00[OFFSET]`
   - Construct `deployment_window_end`: `YYYY-MM-DDTHH:MM:00[OFFSET]`

3. **Perform Customer Name Match:**
   - Normalize Salesforce Name (lowercase, trimmed).
   - Check against the Jira Customer Lookup Map from Step D.
   - **If Match Found:** Store `jira_option_id` and `jira_customer_name`.
   - **If No Match:** Store `jira_option_id = 11033` (Internal) and label status as "MATCH_FAIL".

### Step F: Pre-Flight Summary Tables
Present these tables to the user **BEFORE** creating any tickets.

**Table 1 — Schedule Validation**
Verify calculated dates match the SF schedule input.

```
┌──────────────────┬──────────────┬───────────────────┬─────────────────────┬──────────────────┬────────┐
│ Customer (SF)    │ Server       │ SF Schedule       │ Calculated Date     │ Window (PT)      │ Status │
├──────────────────┼──────────────┼───────────────────┼─────────────────────┼──────────────────┼────────┤
│ Acme Corp        │ prod-web-01  │ Third Wednesday   │ Wed, Mar 18, 2026   │ 6:00 PM - 10:00 PM │ ✅     │
│ Beta LLC         │ app-01       │ Fifth Monday      │ ERROR: No 5th Mon   │ N/A              │ ❌     │
│ Gamma Inc        │ db-02        │ Second Thursday   │ Thu, Mar 12, 2026   │ 8:00 PM - 11:00 PM │ ✅     │
└──────────────────┴──────────────┴───────────────────┴─────────────────────┴──────────────────┴────────┘
```

**Table 2 — Customer Mapping**
Verify SF customer names map correctly to Jira options.

```
┌──────────────────┬──────────────────────┬────────┐
│ SF Customer      │ Jira Match           │ Status │
├──────────────────┼──────────────────────┼────────┤
│ Acme Corp        │ Acme Inc. (10947)    │ ✅     │
│ Beta LLC         │ Beta LLC (10951)     │ ✅     │
│ Gamma Inc        │ INTERNAL (11033)     │ ⚠️     │
└──────────────────┴──────────────────────┴────────┘
```

**Status Legend:**
- ✅ Valid
- ❌ Date calculation error — will be skipped
- ⚠️ No Jira match found — will use "Internal"

**Action:** Ask user: "Review both tables. Rows with ❌ will be skipped. Rows with ⚠️ will default to Internal. Proceed?"

### Step G: Epic Creation
Create the monthly Epic:

```
Tool: mcp__atlassian__createJiraIssue
- projectKey: DEVOPS
- issueTypeName: Epic
- summary: "{TARGET_MONTH} {TARGET_YEAR} Maintenance"
- description: "Monthly maintenance deployment window."
- additional_fields:
    - customfield_10962: [{"id": "11032"}]   # All Customers
```
Store `EPIC_KEY` (e.g., DEVOPS-1234).

### Step H: Ticket Creation
Loop through **VALID** rows only.

```
Tool: mcp__atlassian__createJiraIssue
- projectKey: DEVOPS
- issueTypeName: Customer Deployment
- summary: "{Jira_Match_Name} - {TARGET_MONTH} {TARGET_YEAR} Deployment"
- description: "SF Customer: {SF_Name}\nServer: {vm_name}\nWindow: {deployment_window_begin} to {deployment_window_end}"
- additional_fields:
    - {EPIC_LINK_FIELD_ID}: "[EPIC_KEY]"   <-- Uses the field ID found in Step D
    - customfield_10962: [{"id": "[jira_option_id]"}]
    - customfield_10110: "[deployment_window_begin ISO]"
    - customfield_10111: "[deployment_window_end ISO]"
```

*Note: If `EPIC_LINK_FIELD_ID` was not found in Step D, use `parent: {"key": "[EPIC_KEY]"}` as fallback.*

### Step I: Finalize
1. Open the Epic: `xdg-open "https://huloop.atlassian.net/browse/[EPIC_KEY]"`
2. Output summary:
   - "Created Epic [EPIC_KEY]"
   - "Created X tickets."
   - "Skipped Y records due to errors."

## 4. Error Handling
- **Mapping Failures:** If a customer maps to "Internal" unexpectedly, the user *must* catch this in Step F. If they proceed, log a warning.
- **Classic Project Linking:** If ticket creation fails due to "Field 'parent' cannot be set", retry immediately using the `EPIC_LINK_FIELD_ID` identified in metadata.

## 5. Files
- **`helper_scripts/fetch_maintenance_data.sh`**: Fetches SF data.
- **`helper_scripts/calculate_next_deployment.py`**: Calculates dates from week/day.
  - Accepts numeric (1-5) or ordinal words (First, Second, Third, Fourth, Fifth)
  - Example: `python3 calculate_next_deployment.py Third Wednesday March 2026`
  - Returns error for invalid dates (e.g., "Fifth Monday" in a 4-Monday month)