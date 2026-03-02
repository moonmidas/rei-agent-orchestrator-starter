#!/usr/bin/env bash
set -euo pipefail

APP_DIR=${APP_DIR:-/opt/rei-agent-orchestrator}
INTERVAL_SECONDS=${INTERVAL_SECONDS:-60}
PLIST_SRC="$APP_DIR/launchd/com.rei.orchestrator.worker.plist"
PLIST_DST="$HOME/Library/LaunchAgents/com.rei.orchestrator.worker.plist"

mkdir -p "$HOME/Library/LaunchAgents"
if [[ ! -f "$PLIST_SRC" ]]; then
  echo "missing template: $PLIST_SRC" >&2
  exit 1
fi

sed \
  -e "s|/opt/rei-agent-orchestrator|$APP_DIR|g" \
  -e "s|<integer>60</integer>|<integer>${INTERVAL_SECONDS}</integer>|g" \
  "$PLIST_SRC" > "$PLIST_DST"

launchctl unload "$PLIST_DST" >/dev/null 2>&1 || true
launchctl load "$PLIST_DST"
launchctl enable "gui/$(id -u)/com.rei.orchestrator.worker" || true

echo "launchd installed: $PLIST_DST"
echo "verify: launchctl list | grep com.rei.orchestrator.worker"
