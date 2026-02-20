import json
import os
from collections import Counter
from datetime import datetime

# Path to the claude-code history file
history_path = os.path.expanduser("~/.claude/history.jsonl")
# Output paths
json_output_path = "{vault_path}/Generated Documents/Analysis/history_analysis.json"
md_output_path = "{vault_path}/Generated Documents/Analysis/Comprehensive_Pattern_Report.md"

def analyze_history():
    if not os.path.exists(history_path):
        print(f"Error: History file not found at {history_path}")
        return

    all_data = []
    with open(history_path, 'r') as f:
        for line in f:
            try:
                all_data.append(json.loads(line))
            except:
                continue

    if not all_data:
        return

    all_data.sort(key=lambda x: x.get('timestamp', 0))

    # 1. Project Distribution
    project_counts = Counter([d.get('project', 'unknown').split('/')[-1] for d in all_data])

    # 2. Tech Focus
    tech_keywords = ['ansible', 'python', 'docker', 'terragrunt', 'azure', 'github', 'sonarqube', 'obsidian', 'gemini']
    tech_counts = Counter()
    for d in all_data:
        p = d.get('display', '').lower()
        for tech in tech_keywords:
            if tech in p:
                tech_counts[tech] += 1

    # 3. Monthly Timeline
    history_by_month = {}
    for d in all_data:
        ts = d.get('timestamp', 0)
        if ts == 0: continue
        month = datetime.fromtimestamp(ts/1000).strftime('%Y-%m')
        if month not in history_by_month:
            history_by_month[month] = Counter()
        history_by_month[month][d.get('project', 'unknown').split('/')[-1]] += 1

    # Format timeline for JSON
    timeline = []
    for month in sorted(history_by_month.keys()):
        top_projects = [{"project": p, "count": c} for p, c in history_by_month[month].most_common(5)]
        timeline.append({
            "month": month,
            "top_projects": top_projects
        })

    analysis_results = {
        "metadata": {
            "generated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "interaction_count": len(all_data),
            "date_range": {
                "start": datetime.fromtimestamp(all_data[0]['timestamp']/1000).strftime('%Y-%m-%d'),
                "end": datetime.fromtimestamp(all_data[-1]['timestamp']/1000).strftime('%Y-%m-%d')
            }
        },
        "top_projects": [{"project": p, "count": c} for p, c in project_counts.most_common(10)],
        "tech_focus": dict(tech_counts),
        "timeline": timeline
    }

    # Save JSON
    os.makedirs(os.path.dirname(json_output_path), exist_ok=True)
    with open(json_output_path, 'w') as f:
        json.dump(analysis_results, f, indent=2)
    print(f"Analysis JSON saved to {json_output_path}")

if __name__ == "__main__":
    analyze_history()