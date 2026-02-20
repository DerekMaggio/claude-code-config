#!/usr/bin/env bash
# Fetches customer/server maintenance data from Salesforce
# Requires: sf CLI authenticated (alias set via salesforce_org_alias in devops config), jq
# Output: JSON with customer name and server maintenance fields

set -euo pipefail

sf data query \
  --query "SELECT Name, (SELECT Server_Type__c, VM_Name__c, Maintenance_Week__c, Maintenance_Day__c, Maintenance_Start__c, Maintenance_End__c FROM Servers__r) FROM Account WHERE Id IN (SELECT Account__c FROM Server__c) ORDER BY Name ASC" \
  -o "$(jq -r '.salesforce_org_alias // "default"' "${HOME}/.claude/devops.json" 2>/dev/null || echo "default")" \
  --json \
| jq '.result.records[] | {name: .Name, servers: [.Servers__r.records[] | {server_type: .Server_Type__c, vm_name: .VM_Name__c, maintenance_week: .Maintenance_Week__c, maintenance_day: .Maintenance_Day__c, maintenance_start: .Maintenance_Start__c, maintenance_end: .Maintenance_End__c}]}'
