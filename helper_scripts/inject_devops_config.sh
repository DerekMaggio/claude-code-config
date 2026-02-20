#!/bin/bash
# Injects devops config into Claude conversation context via UserPromptSubmit hook.
# Reads ~/.claude/devops.json and emits a <devops-config> block to stdout.

CONFIG="$HOME/.claude/devops.json"
[ -f "$CONFIG" ] || exit 0

python3 - "$CONFIG" <<'EOF'
import json, sys

with open(sys.argv[1]) as f:
    cfg = json.load(f)

print("<devops-config>")
for k, v in cfg.items():
    print(f"  {k}: {v}")
print("</devops-config>")
print("Use these values whenever a skill references a config key (e.g. jira_cloud_id, vault_root_name).")
EOF
