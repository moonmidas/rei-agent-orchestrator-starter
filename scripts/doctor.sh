#!/usr/bin/env bash
set -euo pipefail

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

echo "doctor: OK"
