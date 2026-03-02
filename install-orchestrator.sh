#!/usr/bin/env bash
set -euo pipefail

APP_DIR=${APP_DIR:-/opt/rei-agent-orchestrator}
APP_USER=${APP_USER:-clawdbot}
REPO_URL=${REPO_URL:-https://github.com/moonmidas/rei-agent-orchestrator-starter.git}
BRANCH=${BRANCH:-main}
WORKER_INTERVAL_SECONDS=${WORKER_INTERVAL_SECONDS:-60}

if [[ $EUID -ne 0 ]]; then
  echo "Run as root (sudo bash install-orchestrator.sh)"
  exit 1
fi

require_openclaw() {
  if ! command -v openclaw >/dev/null 2>&1; then
    echo "ERROR: openclaw CLI is required but not found in PATH."
    echo "Install OpenClaw first, then re-run this installer."
    exit 1
  fi
}

require_gateway() {
  if ! openclaw gateway status >/dev/null 2>&1; then
    echo "ERROR: OpenClaw gateway is unreachable."
    echo "Start/fix gateway first, then re-run this installer."
    exit 1
  fi
}

install_scheduler_linux() {
  local service_out=/etc/systemd/system/rei-orchestrator-worker.service
  local timer_out=/etc/systemd/system/rei-orchestrator-worker.timer
  sed \
    -e "s|{{APP_USER}}|$APP_USER|g" \
    -e "s|{{APP_DIR}}|$APP_DIR|g" \
    -e "s|{{OPENCLAW_HOME}}|$OPENCLAW_HOME|g" \
    "$APP_DIR/templates/systemd/rei-orchestrator-worker.service" > "$service_out"
  sed -e "s|{{INTERVAL_SECONDS}}|$WORKER_INTERVAL_SECONDS|g" \
    "$APP_DIR/templates/systemd/rei-orchestrator-worker.timer" > "$timer_out"

  systemctl daemon-reload
  systemctl enable --now rei-orchestrator-worker.timer
}

echo "Install profile: orchestrator-only"
echo "[preflight] checking prerequisites"
require_openclaw
require_gateway

echo "[1/6] install dependencies"
apt-get update -y
apt-get install -y git curl jq build-essential sqlite3

if ! id "$APP_USER" >/dev/null 2>&1; then
  useradd -m -s /bin/bash "$APP_USER"
fi

echo "[2/6] fetch starter repo"
if [[ -d "$APP_DIR/.git" ]]; then
  git -C "$APP_DIR" fetch origin "$BRANCH"
  git -C "$APP_DIR" checkout "$BRANCH"
  git -C "$APP_DIR" pull --ff-only origin "$BRANCH"
else
  rm -rf "$APP_DIR"
  git clone --branch "$BRANCH" "$REPO_URL" "$APP_DIR"
fi
chown -R "$APP_USER":"$APP_USER" "$APP_DIR"

echo "[3/6] install execute-plan skill"
SKILL_DST="/home/$APP_USER/.openclaw/workspace/skills/execute-plan"
mkdir -p "$SKILL_DST"
cp -r "$APP_DIR/skills/execute-plan/"* "$SKILL_DST/"
chown -R "$APP_USER":"$APP_USER" "/home/$APP_USER/.openclaw/workspace/skills"

OPENCLAW_HOME=${OPENCLAW_HOME:-/home/$APP_USER/.openclaw}
ORCH_HOME="$OPENCLAW_HOME/orchestrator"

echo "[4/6] openclaw config bootstrap (if missing)"
if [[ ! -f "$OPENCLAW_HOME/openclaw.json" ]]; then
  mkdir -p "$OPENCLAW_HOME"
  cp "$APP_DIR/templates/openclaw.orchestrator.example.json" "$OPENCLAW_HOME/openclaw.json"
fi

echo "[5/6] orchestrator runtime layout"
mkdir -p "$ORCH_HOME" "$ORCH_HOME/logs" "$ORCH_HOME/artifacts"
if [[ ! -f "$ORCH_HOME/config.json" ]]; then
  cp "$APP_DIR/templates/orchestrator.config.example.json" "$ORCH_HOME/config.json"
fi

chown -R "$APP_USER":"$APP_USER" "$OPENCLAW_HOME"

echo "[6/6] install and enable scheduler"
install_scheduler_linux

echo "[post-install] checks"
OPENCLAW_HOME="$OPENCLAW_HOME" "$APP_DIR/scripts/doctor.sh"

echo "done"
echo "Installed orchestrator starter to $APP_DIR"
echo "Worker timer: systemctl status rei-orchestrator-worker.timer"
echo "macOS helper (run as user): $APP_DIR/scripts/install-launchd-macos.sh"
