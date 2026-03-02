#!/usr/bin/env bash
set -euo pipefail
APP_DIR=${APP_DIR:-/opt/rei-agent-orchestrator}

if [[ $EUID -ne 0 ]]; then
  echo "Run as root"
  exit 1
fi

systemctl stop clawdbot-gateway || true
systemctl disable clawdbot-gateway || true
rm -f /etc/systemd/system/clawdbot-gateway.service
systemctl daemon-reload
rm -rf "$APP_DIR"
echo "Uninstalled orchestrator starter"
