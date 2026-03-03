#!/usr/bin/env bash
set -euo pipefail

OPENCLAW_HOME=${OPENCLAW_HOME:-$HOME}

validate_openclaw_home() {
  case "$OPENCLAW_HOME" in
    */.openclaw)
      echo "ERROR: OPENCLAW_HOME must be the user home base (for example: $HOME), not the .openclaw directory." >&2
      echo "Fix: export OPENCLAW_HOME=$HOME" >&2
      exit 1
      ;;
  esac
}

validate_openclaw_home
export OPENCLAW_HOME

echo "== openclaw cli =="
if ! command -v openclaw >/dev/null 2>&1; then
  echo "ERROR: openclaw CLI not found in PATH"
  exit 1
fi
openclaw --version

echo "== gateway rpc =="
if ! openclaw gateway status; then
  echo "ERROR: OpenClaw gateway is unreachable"
  exit 1
fi

echo "== configured agents =="
openclaw config get agents.list


echo "== scheduler health =="
if command -v systemctl >/dev/null 2>&1; then
  if systemctl list-unit-files | grep -q '^rei-orchestrator-worker.timer'; then
    if systemctl is-active --quiet rei-orchestrator-worker.timer; then
      echo "scheduler=active (systemd timer)"
    else
      echo "ERROR: rei-orchestrator-worker.timer installed but inactive"
      exit 1
    fi
  else
    echo "scheduler=skip (timer not installed on this host)"
  fi
else
  echo "scheduler=skip (no systemctl)"
fi

echo "doctor: OK"


echo "== orchestrator runtime db =="
"$(dirname "$0")/doctor-runtime.sh"
