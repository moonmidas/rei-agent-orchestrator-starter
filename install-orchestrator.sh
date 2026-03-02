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

echo "[1/7] install dependencies"
apt-get update -y
apt-get install -y git curl jq build-essential

if ! command -v node >/dev/null 2>&1; then
  curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
  apt-get install -y nodejs
fi

if ! id "$APP_USER" >/dev/null 2>&1; then
  useradd -m -s /bin/bash "$APP_USER"
fi

echo "[2/7] install openclaw"
sudo -u "$APP_USER" mkdir -p /home/$APP_USER/.npm-global
sudo -u "$APP_USER" npm config set prefix /home/$APP_USER/.npm-global
sudo -u "$APP_USER" env PATH="/home/$APP_USER/.npm-global/bin:$PATH" npm i -g @openclaw/openclaw

echo "[3/7] fetch starter repo"
if [[ -d "$APP_DIR/.git" ]]; then
  git -C "$APP_DIR" fetch origin "$BRANCH"
  git -C "$APP_DIR" checkout "$BRANCH"
  git -C "$APP_DIR" pull --ff-only origin "$BRANCH"
else
  rm -rf "$APP_DIR"
  git clone --branch "$BRANCH" "$REPO_URL" "$APP_DIR"
fi
chown -R "$APP_USER":"$APP_USER" "$APP_DIR"

echo "[4/7] install execute-plan skill"
SKILL_DST="/home/$APP_USER/.openclaw/workspace/skills/execute-plan"
mkdir -p "$SKILL_DST"
cp -r "$APP_DIR/skills/execute-plan/"* "$SKILL_DST/"
chown -R "$APP_USER":"$APP_USER" "/home/$APP_USER/.openclaw/workspace/skills"

echo "[5/7] install systemd gateway unit"
install -m 0644 "$APP_DIR/systemd-clawdbot-gateway.service" /etc/systemd/system/clawdbot-gateway.service
systemctl daemon-reload
systemctl enable clawdbot-gateway
systemctl restart clawdbot-gateway

echo "[6/7] openclaw config bootstrap (if missing)"
if [[ ! -f /home/$APP_USER/.openclaw/openclaw.json ]]; then
  mkdir -p /home/$APP_USER/.openclaw
  cp "$APP_DIR/templates/openclaw.orchestrator.example.json" /home/$APP_USER/.openclaw/openclaw.json
  chown -R "$APP_USER":"$APP_USER" /home/$APP_USER/.openclaw
fi

echo "[7/7] done"
echo "Installed orchestrator starter to $APP_DIR"
echo "Next steps:"
echo "  1) Edit /home/$APP_USER/.openclaw/openclaw.json with real tokens"
echo "  2) Restart: sudo /bin/systemctl restart clawdbot-gateway"
echo "  3) Verify: $APP_DIR/scripts/doctor.sh"
