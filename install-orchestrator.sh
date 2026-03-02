#!/usr/bin/env bash
set -euo pipefail

APP_DIR=${APP_DIR:-/opt/rei-agent-orchestrator}
APP_USER=${APP_USER:-clawdbot}
REPO_URL=${REPO_URL:-https://github.com/moonmidas/rei-agent-orchestrator-starter.git}
BRANCH=${BRANCH:-main}

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

echo "Install profile: orchestrator-only"
echo "[preflight] checking prerequisites"
require_openclaw
require_gateway

echo "[1/5] install dependencies"
apt-get update -y
apt-get install -y git curl jq build-essential sqlite3

if ! id "$APP_USER" >/dev/null 2>&1; then
  useradd -m -s /bin/bash "$APP_USER"
fi

echo "[2/5] fetch starter repo"
if [[ -d "$APP_DIR/.git" ]]; then
  git -C "$APP_DIR" fetch origin "$BRANCH"
  git -C "$APP_DIR" checkout "$BRANCH"
  git -C "$APP_DIR" pull --ff-only origin "$BRANCH"
else
  rm -rf "$APP_DIR"
  git clone --branch "$BRANCH" "$REPO_URL" "$APP_DIR"
fi
chown -R "$APP_USER":"$APP_USER" "$APP_DIR"

echo "[3/5] install execute-plan skill"
SKILL_DST="/home/$APP_USER/.openclaw/workspace/skills/execute-plan"
mkdir -p "$SKILL_DST"
cp -r "$APP_DIR/skills/execute-plan/"* "$SKILL_DST/"
chown -R "$APP_USER":"$APP_USER" "/home/$APP_USER/.openclaw/workspace/skills"

echo "[4/5] openclaw config bootstrap (if missing)"
if [[ ! -f /home/$APP_USER/.openclaw/openclaw.json ]]; then
  mkdir -p /home/$APP_USER/.openclaw
  cp "$APP_DIR/templates/openclaw.orchestrator.example.json" /home/$APP_USER/.openclaw/openclaw.json
  chown -R "$APP_USER":"$APP_USER" /home/$APP_USER/.openclaw
fi

echo "[5/5] post-install checks"
"$APP_DIR/scripts/doctor.sh"

echo "done"
echo "Installed orchestrator starter to $APP_DIR"
echo "Profile: orchestrator-only"
echo "Next steps:"
echo "  1) Edit /home/$APP_USER/.openclaw/openclaw.json with real tokens"
echo "  2) Verify orchestrator: $APP_DIR/scripts/doctor.sh"
