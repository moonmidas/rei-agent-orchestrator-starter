#!/usr/bin/env bash
set -euo pipefail

APP_DIR=${APP_DIR:-/opt/rei-agent-orchestrator}
APP_USER=${APP_USER:-clawdbot}

if [[ $EUID -ne 0 ]]; then
  echo "Run as root (sudo bash install-orchestrator.sh)"
  exit 1
fi

apt-get update -y
apt-get install -y git curl jq build-essential

if ! command -v node >/dev/null 2>&1; then
  curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
  apt-get install -y nodejs
fi

if ! id "$APP_USER" >/dev/null 2>&1; then
  useradd -m -s /bin/bash "$APP_USER"
fi

sudo -u "$APP_USER" mkdir -p /home/$APP_USER/.npm-global
sudo -u "$APP_USER" npm config set prefix /home/$APP_USER/.npm-global
sudo -u "$APP_USER" env PATH="/home/$APP_USER/.npm-global/bin:$PATH" npm i -g @openclaw/openclaw

mkdir -p "$APP_DIR"
cp -r . "$APP_DIR" 2>/dev/null || true
chown -R "$APP_USER":"$APP_USER" "$APP_DIR"

install -m 0644 "$APP_DIR/systemd-clawdbot-gateway.service" /etc/systemd/system/clawdbot-gateway.service
systemctl daemon-reload
systemctl enable clawdbot-gateway
systemctl restart clawdbot-gateway

echo "Installed orchestrator starter to $APP_DIR"
echo "Next: copy template config and fill tokens"
