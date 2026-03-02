#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export OPENCLAW_HOME="${OPENCLAW_HOME:-$HOME/.openclaw}"
export PYTHONPATH="$ROOT"

mkdir -p "$OPENCLAW_HOME/orchestrator"

python3 -m src.orchestrator.cli migrate
PLAN_OUT=$(python3 -m src.orchestrator.cli execute-plan --thread-id acceptance-thread --text '/execute-plan implement api; add tests; capture ui screenshot')
echo "$PLAN_OUT"
PLAN_ID=$(echo "$PLAN_OUT" | awk -F= '/plan_id/{print $2}')
python3 -m src.orchestrator.cli approve --plan-id "$PLAN_ID" --thread-id acceptance-thread --approver acceptance-bot
RUN_OUT=$(python3 -m src.orchestrator.cli dispatch-next --plan-id "$PLAN_ID" --branch "task/${PLAN_ID}" --pr-url "https://example.invalid/pr/${PLAN_ID}")
echo "$RUN_OUT"
RUN_ID=$(echo "$RUN_OUT" | awk -F= '/run_id/{print $2}')
python3 -m src.orchestrator.cli ci-update --run-id "$RUN_ID" --statuses success
python3 -m src.orchestrator.cli worker-tick --stale-minutes 1

echo "ACCEPTANCE_E2E_OK plan=$PLAN_ID run=$RUN_ID"
