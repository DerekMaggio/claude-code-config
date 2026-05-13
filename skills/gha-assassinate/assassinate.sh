#!/usr/bin/env bash
# gha-assassinate: watch a GitHub Actions workflow and cancel any run on sight.
#
# Usage: assassinate.sh <repo> <workflow> <timeout-seconds>
#   <repo>     "owner/repo" or just "repo" (owner inferred from current git remote, else AgreeYa-HuLoop)
#   <workflow> workflow filename (deploy.yml), numeric id, or display name
#   <timeout>  total wall-clock budget in seconds for the poll loop
#
# Output discipline:
#   - one banner line on start
#   - heartbeat once every ~60s while polling (every-10s polls are silent)
#   - immediate line on detection + final report

set -euo pipefail

POLL_INTERVAL=10
HEARTBEAT_INTERVAL=60

# ---------- helpers ----------

die() {
  echo "[!] ERROR: $*" >&2
  exit 1
}

validate_args() {
  [[ $# -eq 3 ]] || die "repo, workflow, and timeout are all required. Usage: assassinate.sh <repo> <workflow> <timeout-seconds>"
  [[ "$3" =~ ^[1-9][0-9]*$ ]] || die "timeout must be a positive integer (got: $3)"
}

resolve_owner_repo() {
  # Echoes: "<owner> <repo>"
  local repo_arg="$1" owner repo origin_url
  if [[ "$repo_arg" == */* ]]; then
    owner="${repo_arg%%/*}"
    repo="${repo_arg##*/}"
  else
    repo="$repo_arg"
    origin_url="$(git remote get-url origin 2>/dev/null || true)"
    if [[ "$origin_url" =~ github\.com[:/]([^/]+)/ ]]; then
      owner="${BASH_REMATCH[1]}"
    else
      owner="AgreeYa-HuLoop"
    fi
  fi
  echo "$owner $repo"
}

list_workflows() {
  # Args: owner repo
  gh api "repos/$1/$2/actions/workflows" --paginate \
    || die "failed to list workflows for $1/$2"
}

match_workflows() {
  # Args: workflows_json query
  # Echoes: JSON array of matches with {id, name, path, state}
  echo "$1" | jq --arg q "$2" '
    [ .workflows[]
      | . as $w
      | select(
          ($w.id|tostring) == $q
          or ($w.path | ascii_downcase) == ($q | ascii_downcase)
          or ($w.path | split("/") | last | ascii_downcase) == ($q | ascii_downcase)
          or ($w.name | ascii_downcase) == ($q | ascii_downcase)
        )
      | {id, name, path, state}
    ]
  '
}

resolve_workflow() {
  # Args: owner repo workflow_arg
  # Echoes: "<workflow_id> <workflow_name>" on success
  # Exits non-zero with diagnostics on no/ambiguous match
  local owner="$1" repo="$2" query="$3" workflows matches count
  workflows="$(list_workflows "$owner" "$repo")"
  matches="$(match_workflows "$workflows" "$query")"
  count="$(echo "$matches" | jq 'length')"

  if [[ "$count" -eq 0 ]]; then
    echo "[!] No workflow matched \"$query\" in $owner/$repo. Available:" >&2
    echo "$workflows" | jq -r '.workflows[] | "  - \(.name)  (\(.path))  id=\(.id)"' >&2
    exit 2
  fi
  if [[ "$count" -gt 1 ]]; then
    echo "[!] Ambiguous workflow \"$query\" — $count matches:" >&2
    echo "$matches" | jq -r '.[] | "  - \(.name)  (\(.path))  id=\(.id)"' >&2
    exit 3
  fi

  local id name
  id="$(echo "$matches" | jq -r '.[0].id')"
  name="$(echo "$matches" | jq -r '.[0].name')"
  echo "$id $name"
}

fetch_live_run() {
  # Args: owner repo workflow_id
  # Echoes: JSON object for the live run, or empty string if none
  gh api "repos/$1/$2/actions/workflows/$3/runs?per_page=5" \
    --jq '[.workflow_runs[] | select(.status=="queued" or .status=="in_progress" or .status=="waiting" or .status=="requested" or .status=="pending")] | .[0] // empty' \
    2>/dev/null || true
}

poll_for_run() {
  # Args: owner repo workflow_id workflow_name timeout
  # Echoes (on detection): JSON object for the run
  # Returns 1 on timeout (caller checks); error message emitted to stderr
  local owner="$1" repo="$2" wf_id="$3" wf_name="$4" timeout="$5"
  local start now elapsed last_heartbeat run_json
  start=$(date +%s)
  last_heartbeat=$start

  while :; do
    run_json="$(fetch_live_run "$owner" "$repo" "$wf_id")"
    if [[ -n "$run_json" ]]; then
      echo "$run_json"
      return 0
    fi

    now=$(date +%s)
    elapsed=$((now - start))
    if [[ "$elapsed" -ge "$timeout" ]]; then
      echo "[!] Timeout reached (${timeout}s). No run of \"$wf_name\" appeared on $owner/$repo." >&2
      return 1
    fi

    if [[ $((now - last_heartbeat)) -ge $HEARTBEAT_INTERVAL ]]; then
      echo "[.] ${elapsed}s elapsed — no run yet." >&2
      last_heartbeat=$now
    fi

    sleep "$POLL_INTERVAL"
  done
}

cancel_run() {
  # Args: owner repo run_id
  # Echoes: "killed" or "failed:<reason>"
  local owner="$1" repo="$2" run_id="$3"
  if gh api -X POST "repos/$owner/$repo/actions/runs/$run_id/cancel" >/dev/null 2>&1; then
    echo "killed"
    return
  fi
  if gh api -X POST "repos/$owner/$repo/actions/runs/$run_id/force-cancel" >/dev/null 2>&1; then
    echo "killed"
    return
  fi
  echo "failed:both cancel and force-cancel rejected (run may have already terminated)"
}

confirm_run_state() {
  # Args: owner repo run_id
  # Echoes: "<status> <conclusion>"
  local owner="$1" repo="$2" run_id="$3" final
  final="$(gh api "repos/$owner/$repo/actions/runs/$run_id" 2>/dev/null || echo '{}')"
  local status conclusion
  status="$(echo "$final" | jq -r '.status // "unknown"')"
  conclusion="$(echo "$final" | jq -r '.conclusion // "null"')"
  echo "$status $conclusion"
}

print_report() {
  # Args: wf_name run_id branch final_status final_conclusion elapsed cancel_outcome
  local cancel_outcome="$7"
  echo
  echo "Workflow:   $1"
  echo "Run ID:     $2"
  echo "Branch:     $3"
  echo "Final:      $4 / $5"
  echo "Elapsed:    ${6}s"
  if [[ "$cancel_outcome" == "killed" ]]; then
    echo "Outcome:    [+] Killed"
  else
    echo "Outcome:    [-] Could not cancel (${cancel_outcome#failed:})"
  fi
}

# ---------- main ----------

main() {
  validate_args "$@"
  local repo_arg="$1" workflow_arg="$2" timeout="$3"

  read -r OWNER REPO < <(resolve_owner_repo "$repo_arg")
  read -r WORKFLOW_ID WORKFLOW_NAME < <(resolve_workflow "$OWNER" "$REPO" "$workflow_arg")

  echo "[+] Watching workflow: $WORKFLOW_NAME (id=$WORKFLOW_ID) on $OWNER/$REPO. Will cancel any run on sight. Timeout: ${timeout}s."

  local start run_json
  start=$(date +%s)
  if ! run_json="$(poll_for_run "$OWNER" "$REPO" "$WORKFLOW_ID" "$WORKFLOW_NAME" "$timeout")"; then
    exit 0  # timeout, message already emitted
  fi

  local run_id run_status run_branch
  run_id="$(echo "$run_json" | jq -r '.id')"
  run_status="$(echo "$run_json" | jq -r '.status')"
  run_branch="$(echo "$run_json" | jq -r '.head_branch')"

  echo "[!] RUN DETECTED — id=$run_id status=$run_status branch=$run_branch. Cancelling now."

  local cancel_outcome final_status final_conclusion elapsed
  cancel_outcome="$(cancel_run "$OWNER" "$REPO" "$run_id")"
  read -r final_status final_conclusion < <(confirm_run_state "$OWNER" "$REPO" "$run_id")
  elapsed=$(( $(date +%s) - start ))

  print_report "$WORKFLOW_NAME" "$run_id" "$run_branch" "$final_status" "$final_conclusion" "$elapsed" "$cancel_outcome"
}

main "$@"
