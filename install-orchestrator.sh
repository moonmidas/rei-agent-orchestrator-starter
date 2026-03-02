#!/usr/bin/env bash
set -euo pipefail

APP_DIR=${APP_DIR:-/opt/rei-agent-orchestrator}
APP_USER=${APP_USER:-clawdbot}
REPO_URL=${REPO_URL:-https://github.com/moonmidas/rei-agent-orchestrator-starter.git}
BRANCH=${BRANCH:-main}

INSTALL_MISSION_CONTROL=${INSTALL_MISSION_CONTROL:-false}
MISSION_CONTROL_DIR=${MISSION_CONTROL_DIR:-/opt/rei-mission-control}
MISSION_CONTROL_REPO_URL=${MISSION_CONTROL_REPO_URL:-https://github.com/crshdn/mission-control.git}
MISSION_CONTROL_BRANCH=${MISSION_CONTROL_BRANCH:-main}
MISSION_CONTROL_PORT=${MISSION_CONTROL_PORT:-3005}
MISSION_CONTROL_DB_PATH=${MISSION_CONTROL_DB_PATH:-$MISSION_CONTROL_DIR/mission-control.db}

if [[ $EUID -ne 0 ]]; then
  echo "Run as root (sudo bash install-orchestrator.sh)"
  exit 1
fi

if [[ "$INSTALL_MISSION_CONTROL" != "true" && "$INSTALL_MISSION_CONTROL" != "false" ]]; then
  echo "INSTALL_MISSION_CONTROL must be true|false (got: $INSTALL_MISSION_CONTROL)"
  exit 1
fi

PROFILE="orchestrator-only"
if [[ "$INSTALL_MISSION_CONTROL" == "true" ]]; then
  PROFILE="orchestrator+mission-control"
fi

echo "Install profile: $PROFILE"

echo "[1/9] install dependencies"
apt-get update -y
apt-get install -y git curl jq build-essential sqlite3

if ! command -v node >/dev/null 2>&1; then
  curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
  apt-get install -y nodejs
fi

if ! id "$APP_USER" >/dev/null 2>&1; then
  useradd -m -s /bin/bash "$APP_USER"
fi

echo "[2/9] install openclaw + pm2"
sudo -u "$APP_USER" mkdir -p /home/$APP_USER/.npm-global
sudo -u "$APP_USER" npm config set prefix /home/$APP_USER/.npm-global
sudo -u "$APP_USER" env PATH="/home/$APP_USER/.npm-global/bin:$PATH" npm i -g @openclaw/openclaw pm2

echo "[3/9] fetch starter repo"
if [[ -d "$APP_DIR/.git" ]]; then
  git -C "$APP_DIR" fetch origin "$BRANCH"
  git -C "$APP_DIR" checkout "$BRANCH"
  git -C "$APP_DIR" pull --ff-only origin "$BRANCH"
else
  rm -rf "$APP_DIR"
  git clone --branch "$BRANCH" "$REPO_URL" "$APP_DIR"
fi
chown -R "$APP_USER":"$APP_USER" "$APP_DIR"

echo "[4/9] install execute-plan skill"
SKILL_DST="/home/$APP_USER/.openclaw/workspace/skills/execute-plan"
mkdir -p "$SKILL_DST"
cp -r "$APP_DIR/skills/execute-plan/"* "$SKILL_DST/"
chown -R "$APP_USER":"$APP_USER" "/home/$APP_USER/.openclaw/workspace/skills"

echo "[5/9] install systemd gateway unit"
install -m 0644 "$APP_DIR/systemd-clawdbot-gateway.service" /etc/systemd/system/clawdbot-gateway.service
systemctl daemon-reload
systemctl enable clawdbot-gateway
systemctl restart clawdbot-gateway

echo "[6/9] openclaw config bootstrap (if missing)"
if [[ ! -f /home/$APP_USER/.openclaw/openclaw.json ]]; then
  mkdir -p /home/$APP_USER/.openclaw
  cp "$APP_DIR/templates/openclaw.orchestrator.example.json" /home/$APP_USER/.openclaw/openclaw.json
  chown -R "$APP_USER":"$APP_USER" /home/$APP_USER/.openclaw
fi

echo "[7/9] optional mission-control install"
if [[ "$INSTALL_MISSION_CONTROL" == "true" ]]; then
  if [[ -d "$MISSION_CONTROL_DIR/.git" ]]; then
    git -C "$MISSION_CONTROL_DIR" fetch origin "$MISSION_CONTROL_BRANCH"
    git -C "$MISSION_CONTROL_DIR" checkout "$MISSION_CONTROL_BRANCH"
    git -C "$MISSION_CONTROL_DIR" pull --ff-only origin "$MISSION_CONTROL_BRANCH"
  else
    rm -rf "$MISSION_CONTROL_DIR"
    git clone --branch "$MISSION_CONTROL_BRANCH" "$MISSION_CONTROL_REPO_URL" "$MISSION_CONTROL_DIR"
  fi

  chown -R "$APP_USER":"$APP_USER" "$MISSION_CONTROL_DIR"

  sudo -u "$APP_USER" env PATH="/home/$APP_USER/.npm-global/bin:$PATH" bash -lc "cd '$MISSION_CONTROL_DIR' && npm install && npm run build"

  sudo -u "$APP_USER" env PATH="/home/$APP_USER/.npm-global/bin:$PATH" bash -lc "cd '$MISSION_CONTROL_DIR' && pm2 delete mission-control >/dev/null 2>&1 || true"
  sudo -u "$APP_USER" env PATH="/home/$APP_USER/.npm-global/bin:$PATH" bash -lc "cd '$MISSION_CONTROL_DIR' && pm2 start 'npm run start -- -p $MISSION_CONTROL_PORT' --name mission-control --update-env"
  sudo -u "$APP_USER" env PATH="/home/$APP_USER/.npm-global/bin:$PATH" pm2 save
fi

echo "[8/9] post-install checks"
if [[ "$INSTALL_MISSION_CONTROL" == "true" ]]; then
  APP_USER="$APP_USER" MISSION_CONTROL_DIR="$MISSION_CONTROL_DIR" MISSION_CONTROL_DB_PATH="$MISSION_CONTROL_DB_PATH" "$APP_DIR/scripts/doctor-full.sh"
else
  "$APP_DIR/scripts/doctor.sh"
fi

echo "[9/9] done"
echo "Installed orchestrator starter to $APP_DIR"
echo "Profile: $PROFILE"
echo "Next steps:"
echo "  1) Edit /home/$APP_USER/.openclaw/openclaw.json with real tokens"
echo "  2) Restart: sudo /bin/systemctl restart clawdbot-gateway"
if [[ "$INSTALL_MISSION_CONTROL" == "true" ]]; then
  echo "  3) Verify full stack: $APP_DIR/scripts/doctor-full.sh"
else
  echo "  3) Verify orchestrator: $APP_DIR/scripts/doctor.sh"
fi
