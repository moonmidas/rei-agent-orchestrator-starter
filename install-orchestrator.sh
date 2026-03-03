#!/usr/bin/env bash
set -euo pipefail

APP_DIR=${APP_DIR:-/opt/rei-agent-orchestrator}
APP_USER=${APP_USER:-clawdbot}
REPO_URL=${REPO_URL:-https://github.com/moonmidas/rei-agent-orchestrator-starter.git}
BRANCH=${BRANCH:-main}
WORKER_INTERVAL_SECONDS=${WORKER_INTERVAL_SECONDS:-60}
CHAD_MODEL=${CHAD_MODEL:-openai-codex/gpt-5.3-codex}

OPENCLAW_HOME=${OPENCLAW_HOME:-/home/$APP_USER}
OPENCLAW_DATA_DIR="$OPENCLAW_HOME/.openclaw"
ORCH_HOME="$OPENCLAW_DATA_DIR/orchestrator"
OPENCLAW_BIN=${OPENCLAW_BIN:-openclaw}

if [[ $EUID -ne 0 ]]; then
  echo "Run as root (sudo bash install-orchestrator.sh)"
  exit 1
fi


validate_openclaw_home() {
  case "$OPENCLAW_HOME" in
    */.openclaw)
      echo "ERROR: OPENCLAW_HOME must be the user home base (e.g. /home/$APP_USER), not the .openclaw directory."
      echo "Fix: export OPENCLAW_HOME=/home/$APP_USER"
      exit 1
      ;;
  esac
}

resolve_openclaw_bin() {
  if command -v "$OPENCLAW_BIN" >/dev/null 2>&1; then
    OPENCLAW_BIN=$(command -v "$OPENCLAW_BIN")
    return
  fi

  local user_bin="/home/$APP_USER/.npm-global/bin/openclaw"
  if [[ -x "$user_bin" ]]; then
    OPENCLAW_BIN="$user_bin"
    return
  fi

  echo "ERROR: openclaw CLI is required but not found."
  echo "Expected in PATH or at $user_bin"
  exit 1
}

run_as_app_user() {
  sudo -u "$APP_USER" env \
    HOME="/home/$APP_USER" \
    OPENCLAW_HOME="$OPENCLAW_HOME" \
    PATH="/home/$APP_USER/.npm-global/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" \
    "$@"
}

require_gateway() {
  if ! run_as_app_user "$OPENCLAW_BIN" gateway status >/dev/null 2>&1; then
    echo "ERROR: OpenClaw gateway is unreachable for user '$APP_USER'."
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
  if ! systemctl is-active --quiet rei-orchestrator-worker.timer; then
    echo "ERROR: rei-orchestrator-worker.timer is not active after install"
    systemctl status rei-orchestrator-worker.timer --no-pager || true
    exit 1
  fi
}

ensure_chad_agent() {
  echo "[agent-check] verifying chad agent"

  if run_as_app_user "$OPENCLAW_BIN" agents list --json | jq -e '((if type=="array" then . elif type=="object" then (.agents // []) else [] end)[]? | (.id // .name // . // "") | tostring | ascii_downcase) == "chad"' >/dev/null; then
    echo "[agent-check] chad already present"
    return
  fi

  echo "[agent-check] chad not found. adding default dev agent (model=$CHAD_MODEL)"
  mkdir -p "$OPENCLAW_DATA_DIR/workspace-chad"
  chown -R "$APP_USER":"$APP_USER" "$OPENCLAW_DATA_DIR"

  if ! run_as_app_user "$OPENCLAW_BIN" agents add chad \
      --model "$CHAD_MODEL" \
      --workspace "$OPENCLAW_DATA_DIR/workspace-chad" \
      --non-interactive \
      --json >/tmp/rei-orch-agent-add.json 2>/tmp/rei-orch-agent-add.err; then
    echo "ERROR: failed to auto-add chad agent."
    echo "stderr:"
    sed -n '1,120p' /tmp/rei-orch-agent-add.err || true
    exit 1
  fi

  echo "[agent-check] chad created"
}

echo "Install profile: orchestrator-only"

echo "[preflight] ensure app user exists"
if ! id "$APP_USER" >/dev/null 2>&1; then
  echo "ERROR: app user '$APP_USER' does not exist."
  echo "This package assumes an existing OpenClaw installation for that user."
  exit 1
fi

echo "[preflight] checking prerequisites"
validate_openclaw_home
resolve_openclaw_bin
require_gateway

echo "[1/7] install dependencies"
apt-get update -y
apt-get install -y git curl jq build-essential sqlite3

echo "[2/7] fetch starter repo"
if [[ -d "$APP_DIR/.git" ]]; then
  git -C "$APP_DIR" fetch origin "$BRANCH"
  git -C "$APP_DIR" checkout "$BRANCH"
  git -C "$APP_DIR" pull --ff-only origin "$BRANCH"
else
  rm -rf "$APP_DIR"
  git clone --branch "$BRANCH" "$REPO_URL" "$APP_DIR"
fi
chown -R "$APP_USER":"$APP_USER" "$APP_DIR"

echo "[3/7] install execute-plan skill"
SKILL_DST="$OPENCLAW_DATA_DIR/workspace/skills/execute-plan"
mkdir -p "$SKILL_DST"
cp -r "$APP_DIR/skills/execute-plan/"* "$SKILL_DST/"
chown -R "$APP_USER":"$APP_USER" "$OPENCLAW_DATA_DIR/workspace/skills"

echo "[4/7] openclaw config bootstrap (if missing)"
if [[ ! -f "$OPENCLAW_DATA_DIR/openclaw.json" ]]; then
  mkdir -p "$OPENCLAW_DATA_DIR"
  cp "$APP_DIR/templates/openclaw.orchestrator.example.json" "$OPENCLAW_DATA_DIR/openclaw.json"
fi

echo "[5/7] orchestrator runtime layout"
mkdir -p "$ORCH_HOME" "$ORCH_HOME/logs" "$ORCH_HOME/artifacts"
if [[ ! -f "$ORCH_HOME/config.json" ]]; then
  cp "$APP_DIR/templates/orchestrator.config.example.json" "$ORCH_HOME/config.json"
fi

chown -R "$APP_USER":"$APP_USER" "$OPENCLAW_DATA_DIR"

echo "[6/7] ensure required dev agent is available"
ensure_chad_agent

echo "[7/7] install and enable scheduler"
install_scheduler_linux

echo "[post-install] checks"
OPENCLAW_HOME="$OPENCLAW_HOME" "$APP_DIR/scripts/doctor.sh"

echo "done"
echo "Installed orchestrator starter to $APP_DIR"
echo "Worker timer: systemctl status rei-orchestrator-worker.timer"
echo "macOS helper (run as user): $APP_DIR/scripts/install-launchd-macos.sh"
