#!/usr/bin/env bash
set -euo pipefail

OPENCLAW_HOME=${OPENCLAW_HOME:-$HOME/.openclaw}
ORCH_HOME="$OPENCLAW_HOME/orchestrator"
DB_PATH=${ORCHESTRATOR_DB_PATH:-$ORCH_HOME/orchestrator.db}

mkdir -p "$ORCH_HOME"
PYTHONPATH="${PYTHONPATH:-.}" python3 -m src.orchestrator.cli migrate >/tmp/orchestrator-migrate.out

echo "== orchestrator db =="
echo "db path: $DB_PATH"
[[ -f "$DB_PATH" ]] || { echo "ERROR: db not created"; exit 1; }

for t in plans tasks runs approvals events artifacts ci_checks; do
  sqlite3 "$DB_PATH" "SELECT name FROM sqlite_master WHERE type='table' AND name='$t';" | grep -qx "$t" || {
    echo "ERROR: missing table: $t"
    exit 1
  }
done

echo "runtime-doctor: OK"
