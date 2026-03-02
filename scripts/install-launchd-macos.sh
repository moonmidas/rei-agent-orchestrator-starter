#!/usr/bin/env bash
set -euo pipefail

APP_DIR=${APP_DIR:-/opt/rei-agent-orchestrator}
INTERVAL_SECONDS=${INTERVAL_SECONDS:-60}
PLIST_SRC="$APP_DIR/launchd/com.rei.orchestrator.worker.plist"
PLIST_DST="$HOME/Library/LaunchAgents/com.rei.orchestrator.worker.plist"
LABEL="com.rei.orchestrator.worker"

install_plist() {
  mkdir -p "$HOME/Library/LaunchAgents"
  if [[ ! -f "$PLIST_SRC" ]]; then
    echo "missing template: $PLIST_SRC" >&2
    exit 1
  fi
  sed \
    -e "s|/opt/rei-agent-orchestrator|$APP_DIR|g" \
    -e "s|<integer>60</integer>|<integer>${INTERVAL_SECONDS}</integer>|g" \
    "$PLIST_SRC" > "$PLIST_DST"

  launchctl bootout "gui/$(id -u)/$LABEL" >/dev/null 2>&1 || true
  launchctl bootstrap "gui/$(id -u)" "$PLIST_DST"
  launchctl enable "gui/$(id -u)/$LABEL" || true
  echo "launchd installed: $PLIST_DST"
}

status_plist() {
  launchctl print "gui/$(id -u)/$LABEL" >/dev/null 2>&1 && echo "status=active" && return 0
  echo "status=inactive"
  return 1
}

uninstall_plist() {
  launchctl bootout "gui/$(id -u)/$LABEL" >/dev/null 2>&1 || true
  rm -f "$PLIST_DST"
  echo "launchd uninstalled: $PLIST_DST"
}

case "${1:-install}" in
  install) install_plist ;;
  status) status_plist ;;
  uninstall) uninstall_plist ;;
  *) echo "usage: $0 [install|status|uninstall]" >&2; exit 2 ;;
esac
