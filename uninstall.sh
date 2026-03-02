#!/usr/bin/env bash
set -euo pipefail
APP_DIR=${APP_DIR:-/opt/rei-agent-orchestrator}

if [[ $EUID -ne 0 ]]; then
  echo "Run as root"
  exit 1
fi

systemctl disable --now rei-orchestrator-worker.timer >/dev/null 2>&1 || true
rm -f /etc/systemd/system/rei-orchestrator-worker.timer /etc/systemd/system/rei-orchestrator-worker.service
systemctl daemon-reload || true

rm -rf "$APP_DIR"
echo "Uninstalled orchestrator starter"
