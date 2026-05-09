#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

python3 skills/branch-builder/scripts/branch_builder_checkpoint.py --state examples/github_intro/branch_state_start.yaml --events /tmp/branch_builder_events.ndjson --checkpoint task_start --emit-summary >/tmp/branch_builder_task_start.json
echo "[1/5] task_start fixture: $(python3 -c 'import json; p=json.load(open("/tmp/branch_builder_task_start.json")); print(p["status"], p["status_marker"])')"

python3 skills/branch-builder/scripts/branch_builder_checkpoint.py --state examples/github_intro/branch_state_start.yaml --events /tmp/branch_builder_events.ndjson --checkpoint pre_dispatch >/tmp/branch_builder_pre_dispatch.json
echo "[2/5] pre_dispatch fixture: $(python3 -c 'import json; p=json.load(open("/tmp/branch_builder_pre_dispatch.json")); print(p["status"], p["status_marker"])')"

python3 skills/branch-builder/scripts/branch_builder_checkpoint.py --state examples/github_intro/branch_state_pre_merge.yaml --events /tmp/branch_builder_events.ndjson --checkpoint pre_merge >/tmp/branch_builder_pre_merge.json
echo "[3/5] pre_merge fixture: $(python3 -c 'import json; p=json.load(open("/tmp/branch_builder_pre_merge.json")); print(p["status"], p["status_marker"])')"

python3 skills/branch-builder/scripts/branch_builder_checkpoint.py --state examples/github_intro/branch_state_final.yaml --events /tmp/branch_builder_events.ndjson --checkpoint final_response --emit-delta >/tmp/branch_builder_final_response.json
echo "[4/5] final_response fixture: $(python3 -c 'import json; p=json.load(open("/tmp/branch_builder_final_response.json")); print(p["status"], p["status_marker"])')"

if python3 skills/branch-builder/scripts/branch_builder_checkpoint.py --state examples/github_intro/branch_state_start.yaml --events /tmp/branch_builder_events.ndjson --checkpoint final_response >/tmp/branch_builder_unresolved_final.json 2>&1; then
  echo "[5/5] unresolved final_response guard: failed"
  cat /tmp/branch_builder_unresolved_final.json
  exit 1
fi
echo "[5/5] unresolved final_response guard: $(python3 -c 'import json; p=json.load(open("/tmp/branch_builder_unresolved_final.json")); print("ok", p["status_marker"])')"

echo "Branch Builder GitHub intro test passed."
