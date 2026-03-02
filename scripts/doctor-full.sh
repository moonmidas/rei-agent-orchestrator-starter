#!/usr/bin/env bash
set -euo pipefail

APP_USER=${APP_USER:-clawdbot}
MISSION_CONTROL_DIR=${MISSION_CONTROL_DIR:-/opt/rei-mission-control}
MISSION_CONTROL_DB_PATH=${MISSION_CONTROL_DB_PATH:-$MISSION_CONTROL_DIR/mission-control.db}
DRY_RUN=${DRY_RUN:-false}

if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=true
fi

run_cmd() {
  if [[ "$DRY_RUN" == "true" ]]; then
    echo "[DRY-RUN] $*"
    return 0
  fi
  "$@"
}

echo "== full doctor: orchestrator + mission-control =="
echo "APP_USER=$APP_USER"
echo "MISSION_CONTROL_DIR=$MISSION_CONTROL_DIR"
echo "MISSION_CONTROL_DB_PATH=$MISSION_CONTROL_DB_PATH"

printf "\n[1/4] gateway service active\n"
if [[ "$DRY_RUN" == "true" ]]; then
  echo "[DRY-RUN] /bin/systemctl is-active clawdbot-gateway"
else
  state=$(/bin/systemctl is-active clawdbot-gateway)
  [[ "$state" == "active" ]] || { echo "gateway not active: $state"; exit 1; }
  echo "gateway: $state"
fi

printf "\n[2/4] mission-control PM2 process active\n"
if [[ "$DRY_RUN" == "true" ]]; then
  echo "[DRY-RUN] sudo -u $APP_USER pm2 jlist | jq status checks"
else
  pm2_json=$(sudo -u "$APP_USER" env PATH="/home/$APP_USER/.npm-global/bin:$PATH" pm2 jlist)
  echo "$pm2_json" | jq -e '.[] | select(.name=="mission-control" and .pm2_env.status=="online")' >/dev/null \
    || { echo "mission-control pm2 process is not online"; exit 1; }
  echo "mission-control pm2 process: online"
fi

printf "\n[3/4] sqlite DB file exists\n"
if [[ "$DRY_RUN" == "true" ]]; then
  echo "[DRY-RUN] test -f $MISSION_CONTROL_DB_PATH"
else
  [[ -f "$MISSION_CONTROL_DB_PATH" ]] || { echo "DB file missing: $MISSION_CONTROL_DB_PATH"; exit 1; }
  echo "db file present: $MISSION_CONTROL_DB_PATH"
fi

printf "\n[4/4] sqlite core tables exist (tasks, agent_runs)\n"
if [[ "$DRY_RUN" == "true" ]]; then
  echo "[DRY-RUN] sqlite3 $MISSION_CONTROL_DB_PATH \"SELECT name FROM sqlite_master WHERE type='table' AND name IN ('tasks','agent_runs') ORDER BY name;\""
else
  tables=$(sqlite3 "$MISSION_CONTROL_DB_PATH" "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('tasks','agent_runs') ORDER BY name;")
  echo "$tables" | grep -qx "agent_runs" || { echo "missing table: agent_runs"; exit 1; }
  echo "$tables" | grep -qx "tasks" || { echo "missing table: tasks"; exit 1; }
  echo "core tables present:"
  echo "$tables"
fi

printf "\nOK: full profile healthcheck passed\n"
