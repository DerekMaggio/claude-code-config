# Jira Monthly Scheduling Skill

> **Summary:** Maps CSV customer names to JIRA HuLoop Customer field values for maintenance scheduling.

## Trigger

Use this skill when the user needs to:
- Schedule monthly maintenance windows
- Map customer names from a CSV to JIRA
- Create JIRA tickets for scheduled maintenance

## Procedure

### Step 1: Request CSV File

Ask the user for the path to the CSV file containing the maintenance schedule.

### Step 2: Filter CSV to Required Columns

Run the filter script to extract only the needed columns:

```bash
python /home/derek-maggio/workspace/claude-code-config/skills/jira-monthly-scheduling/filter_csv.py <input.csv>
```

This produces a filtered CSV with columns:
- VM name
- Customer name
- Next Scheduled Window (Pacific Time)
- Regular Maintenance Week
- Regular Maintenance Day
- Regular Maintenance Window (Pacific)

### Step 3: Query JIRA for HuLoop Customer Field Values

Use the Atlassian MCP tools to get the available values for the "HuLoop Customer" custom field:

1. Get the cloud ID using `getAccessibleAtlassianResources`
2. Query JIRA for existing issues or field metadata to retrieve valid HuLoop Customer values

### Step 4: Create Customer Name Mapping

Compare each unique customer name from the CSV against the JIRA HuLoop Customer field values.

**Matching Strategy:**
1. Exact match (case-insensitive)
2. Partial/substring match
3. Common abbreviation matching (e.g., "TCB" -> "Tri Counties Bank")

### Step 5: Output Mappings for Review

Present the mappings in this format:

```
CSV Customer Name -> JIRA Customer Name
--------------------------------------------
Tri Counties Bank -> Tri Counties Bank
WAB -> WAB
Verizon Wireless -> Verizon
[UNCERTAIN] Some Customer -> ???
```

### Step 6: Resolve Uncertain Mappings

For any mappings marked as `[UNCERTAIN]`, ask the user:

> "I couldn't confidently match these customers. Please provide the correct JIRA customer name:"
> - `<CSV Customer Name>` - Did you mean `<closest match>` or something else?

### Step 7: Save Final Mapping

Once confirmed, save the mapping to a file for future reference:
- `customer_mapping.json` - JSON format for programmatic use

## Required Files

- `filter_csv.py` - CSV column filter script
- `COLUMNS_TO_KEEP` - List of columns to retain

## Output

- Filtered CSV file (`*_filtered.csv`)
- Customer mapping file (`customer_mapping.json`)
- Summary of mapped vs unmapped customers
