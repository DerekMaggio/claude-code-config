import json
import os

json_input_path = "{vault_path}/Generated Documents/Analysis/history_analysis.json"
md_output_path = "{vault_path}/Generated Documents/Analysis/Comprehensive_Pattern_Report.md"

def generate_report():
    if not os.path.exists(json_input_path):
        print("Error: JSON input not found at {}".format(json_input_path))
        return

    with open(json_input_path, 'r') as f:
        data = json.load(f)

    with open(md_output_path, 'w') as f:
        f.write("# Comprehensive Interaction & Workflow Pattern Report\n\n")
        f.write("Generated on: {}\n".format(data['metadata']['generated_at']))
        f.write("Data Scope: {} interactions from {} to {}\n\n".format(
            data['metadata']['interaction_count'],
            data['metadata']['date_range']['start'],
            data['metadata']['date_range']['end']
        ))
        
        f.write("## 1. Top Projects (Cumulative)\n")
        for item in data['top_projects']:
            f.write("- **{}**: {} interactions\n".format(item['project'], item['count']))
        
        f.write("\n## 2. Technology & Tooling Focus\n")
        f.write("| Technology | Frequency |\n| :--- | :--- |\n")
        sorted_tech = sorted(data['tech_focus'].items(), key=lambda x: x[1], reverse=True)
        for tech, count in sorted_tech:
            f.write("| {} | {} |\n".format(tech.capitalize(), count))
        
        f.write("\n## 3. Persistent Workflow Patterns\n")
        f.write("### The 'Execution Plan' Pattern\n")
        f.write("You consistently use your vault as a storage layer for 'Claude Execution Plans'. This suggests a structured hand-off between planning and execution phases.\n\n")
        
        f.write("### The 'Gemini-Bridge' Orchestration\n")
        f.write("A recurring high-level pattern is using one agent to 'prep' context for Gemini without the agent itself reading the files. This is a sophisticated way of managing token limits and context precision.\n\n")
        
        f.write("### The 'RHEL/Ansible' Constraint\n")
        f.write("In Ansible work, you have a hard preference for `raw: dnf` over the standard module to bypass Python interpreter issues on RHEL systems.\n\n")

        f.write("## 4. Friction Points (Areas for Optimization)\n")
        f.write("### Obsidian Link Fragility\n")
        f.write("Most issues stem from emojis in headers or incorrect anchor formatting. Links like `[Name](#Section%20Name)` are the required Obsidian standard.\n\n")
        
        f.write("### Repeated Maintenance Tasks\n")
        f.write("- **Symlink Syncing**: You manually request symlink updates frequently (30+ occurrences).\n")
        f.write("- **Azcopy Backups**: A repeated request pattern for Azure uploads.\n\n")
        
        f.write("## 5. Project Evolution (Timeline)\n")
        f.write("| Month | Primary Project | Secondary Project |\n| :--- | :--- | :--- |\n")
        for entry in data['timeline']:
            top_two = entry['top_projects']
            p1 = "{} ({})".format(top_two[0]['project'], top_two[0]['count']) if len(top_two) > 0 else "-"
            p2 = "{} ({})".format(top_two[1]['project'], top_two[1]['count']) if len(top_two) > 1 else "-"
            f.write("| {} | {} | {} |\n".format(entry['month'], p1, p2))

    print("Markdown report generated at {}".format(md_output_path))

if __name__ == "__main__":
    generate_report()