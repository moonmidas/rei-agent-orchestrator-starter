#!/usr/bin/env bash
set -euo pipefail

echo "== gateway service =="
sudo /bin/systemctl status clawdbot-gateway --no-pager | sed -n '1,24p'

echo "== gateway rpc =="
openclaw gateway status || true

echo "== configured agents =="
openclaw config get agents.list || true

