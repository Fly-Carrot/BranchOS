#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

validator="skills/branch-builder/scripts/validate_branch_state.py"

python3 "$validator" examples/github_intro/branch_state_start.yaml --checkpoint task_start >/tmp/branch_builder_task_start.json
echo "[1/5] task_start fixture: $(python3 -c 'import json; print(json.load(open("/tmp/branch_builder_task_start.json"))["status"])')"

python3 "$validator" examples/github_intro/branch_state_start.yaml --checkpoint pre_dispatch >/tmp/branch_builder_pre_dispatch.json
echo "[2/5] pre_dispatch fixture: $(python3 -c 'import json; print(json.load(open("/tmp/branch_builder_pre_dispatch.json"))["status"])')"

python3 "$validator" examples/github_intro/branch_state_pre_merge.yaml --checkpoint pre_merge >/tmp/branch_builder_pre_merge.json
echo "[3/5] pre_merge fixture: $(python3 -c 'import json; print(json.load(open("/tmp/branch_builder_pre_merge.json"))["status"])')"

python3 "$validator" examples/github_intro/branch_state_final.yaml --checkpoint final_response >/tmp/branch_builder_final_response.json
echo "[4/5] final_response fixture: $(python3 -c 'import json; print(json.load(open("/tmp/branch_builder_final_response.json"))["status"])')"

if python3 "$validator" examples/github_intro/branch_state_start.yaml --checkpoint final_response >/tmp/branch_builder_unresolved_final.json 2>&1; then
  echo "[5/5] unresolved final_response guard: failed"
  cat /tmp/branch_builder_unresolved_final.json
  exit 1
fi
echo "[5/5] unresolved final_response guard: ok"

echo "Branch Builder GitHub intro test passed."
