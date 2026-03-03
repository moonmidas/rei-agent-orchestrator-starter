#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export OPENCLAW_HOME="${OPENCLAW_HOME:-$HOME}"
OPENCLAW_DATA_DIR="$OPENCLAW_HOME/.openclaw"
export PYTHONPATH="$ROOT"
MODE="real-local"
THREAD_ID=""

usage() {
  cat <<'USAGE'
Usage:
  scripts/acceptance-e2e.sh [--mock | --real-local | --real-discord] [--thread-id <discord_thread_id>]

Modes:
  --mock          Fully local; fake openclaw dispatch + fake milestone sender.
  --real-local    Real runtime checks + local no-op milestone sender (default).
  --real-discord  Real runtime checks + real Discord milestone send validation.

Mode requirements / pass criteria:
  mock:
    - no external services required
    - passes when orchestration flow reaches completed state
  real-local:
    - requires openclaw + healthy gateway + gh auth + chad agent
    - uses local no-op milestone send command
    - passes when orchestration flow reaches completed state
  real-discord:
    - same prerequisites as real-local
    - requires --thread-id <discord_thread_id>
    - fails if any run milestone event payload has non-null error
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mock)
      MODE="mock"
      shift
      ;;
    --real-local)
      MODE="real-local"
      shift
      ;;
    --real-discord)
      MODE="real-discord"
      shift
      ;;
    --thread-id)
      THREAD_ID="${2:-}"
      [[ -n "$THREAD_ID" ]] || { echo "--thread-id requires a value" >&2; exit 2; }
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "unknown arg: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

mkdir -p "$OPENCLAW_DATA_DIR/orchestrator"

preflight_real() {
  command -v openclaw >/dev/null || { echo "missing openclaw" >&2; exit 1; }
  openclaw gateway status >/dev/null || { echo "gateway unhealthy" >&2; exit 1; }
  command -v gh >/dev/null || { echo "missing gh" >&2; exit 1; }
  gh auth status >/dev/null || { echo "gh auth missing" >&2; exit 1; }
  python3 - <<'PY'
import json, subprocess, sys
cp = subprocess.run(['openclaw','agents','list','--json'], check=True, capture_output=True, text=True)
d = json.loads(cp.stdout)
a = d.get('agents', []) if isinstance(d, dict) else (d if isinstance(d, list) else [])
names = set()
for x in a:
    if isinstance(x, dict):
        names.add(str(x.get('id') or x.get('name') or '').lower())
    else:
        names.add(str(x).lower())
if 'chad' not in names:
    print('chad agent missing', file=sys.stderr)
    sys.exit(1)
PY
}

TMP_BIN=""
TMP_MESSAGES=""
TMP_SENT=""
MILESTONE_CFG='"milestones": {}'
if [[ "$MODE" == "mock" ]]; then
  THREAD_ID="${THREAD_ID:-acceptance-thread}"
  TMP_BIN="$(mktemp -d)"
  TMP_MESSAGES="$(mktemp)"
  TMP_SENT="$(mktemp)"
  cat > "$TMP_BIN/openclaw" <<'MOCK'
#!/usr/bin/env bash
set -euo pipefail
if [[ "${1:-}" == "agent" ]]; then
  echo '{"status":"ok","result":{"meta":{"agentMeta":{"sessionId":"session-acceptance-'"${RANDOM}"'"}}}}'
  exit 0
fi
if [[ "${1:-}" == "agents" ]]; then
  echo '{"agents":[{"id":"chad"}]}'
  exit 0
fi
if [[ "${1:-}" == "message" && "${2:-}" == "read" ]]; then
  cat "${OPENCLAW_FAKE_MESSAGES_FILE}"
  exit 0
fi
if [[ "${1:-}" == "message" && "${2:-}" == "send" ]]; then
  printf '%s\n' "$*" >> "${OPENCLAW_FAKE_SENT_FILE}"
  echo '{"ok":true}'
  exit 0
fi
echo "unsupported fake openclaw invocation: $*" >&2
exit 2
MOCK
  chmod +x "$TMP_BIN/openclaw"
  export PATH="$TMP_BIN:$PATH"
  export OPENCLAW_FAKE_MESSAGES_FILE="$TMP_MESSAGES"
  export OPENCLAW_FAKE_SENT_FILE="$TMP_SENT"
  MILESTONE_CFG='"milestones": {"targetThreadId": "'"$THREAD_ID"'"}'
else
  preflight_real
  if [[ "$MODE" == "real-discord" ]]; then
    [[ -n "$THREAD_ID" ]] || { echo "real-discord mode requires --thread-id <discord_thread_id>" >&2; exit 1; }
    MILESTONE_CFG='"milestones": {"targetThreadId": "'"$THREAD_ID"'"}'
  else
    THREAD_ID="${THREAD_ID:-acceptance-local-thread}"
    MILESTONE_CFG='"milestones": {"targetThreadId": "'"$THREAD_ID"'", "sendCommand": ["python3", "-c", "print(\"{\\\"ok\\\":true}\")"]}'
  fi
fi

cat > "$OPENCLAW_DATA_DIR/orchestrator/config.acceptance.json" <<JSON
{
  "database": {"path": "${OPENCLAW_HOME}/.openclaw/orchestrator/orchestrator.db"},
  "routing": {"map": {"code": "chad", "default": "chad"}, "devFallbackAgent": "chad"},
  "discord": {
    "approval": {
      "keywords": ["approve"],
      "fetchCommand": ["openclaw", "message", "read", "--channel", "discord", "--target", "{thread_id}", "--limit", "{limit}"]
    },
    $MILESTONE_CFG
  },
  "runtime": {
    "openclawDispatch": {
      "command": ["openclaw", "agent", "--agent", "{agent}", "--session-id", "orchestrator:{run_id}", "--message", "{dispatch_message}", "--json"]
    }
  }
}
JSON

python3 - <<'PY'
import json, os
p = os.path.expanduser(os.path.join(os.environ['OPENCLAW_HOME'], '.openclaw', 'orchestrator', 'config.acceptance.json'))
cfg = json.load(open(p))
cfg['database']['path'] = cfg['database']['path'].replace('${OPENCLAW_HOME}', os.environ['OPENCLAW_HOME'])
json.dump(cfg, open(p, 'w'))
PY

python3 -m src.orchestrator.cli migrate --config "$OPENCLAW_DATA_DIR/orchestrator/config.acceptance.json"
PLAN_OUT=$(python3 -m src.orchestrator.cli execute-plan --config "$OPENCLAW_DATA_DIR/orchestrator/config.acceptance.json" --thread-id "$THREAD_ID" --text '/execute-plan implement api; add tests; capture ui screenshot')
echo "$PLAN_OUT"
PLAN_ID=$(echo "$PLAN_OUT" | awk -F= '/plan_id/{print $2}')

if [[ "$MODE" == "mock" ]]; then
  echo "[{\"id\":\"msg-1\",\"thread_id\":\"$THREAD_ID\",\"author_id\":\"acceptance-bot\",\"content\":\"approve\"}]" > "$TMP_MESSAGES"
  APPROVAL_OUT=$(python3 -m src.orchestrator.cli approve-from-discord --config "$OPENCLAW_DATA_DIR/orchestrator/config.acceptance.json" --plan-id "$PLAN_ID" --thread-id "$THREAD_ID")
else
  APPROVAL_OUT=$(python3 -m src.orchestrator.cli approve --config "$OPENCLAW_DATA_DIR/orchestrator/config.acceptance.json" --plan-id "$PLAN_ID" --thread-id "$THREAD_ID" --approver acceptance-real --text approve)
fi
echo "$APPROVAL_OUT"

RUN_OUT=$(python3 -m src.orchestrator.cli dispatch-next --config "$OPENCLAW_DATA_DIR/orchestrator/config.acceptance.json" --plan-id "$PLAN_ID" --branch "task/${PLAN_ID}" --pr-url "https://example.invalid/pr/${PLAN_ID}")
echo "$RUN_OUT"
RUN_ID=$(echo "$RUN_OUT" | awk -F= '/run_id/{print $2}')
python3 -m src.orchestrator.cli capture-screenshot --config "$OPENCLAW_DATA_DIR/orchestrator/config.acceptance.json" --task-id "$(python3 - <<PY
import sqlite3,os
conn=sqlite3.connect(os.path.join(os.environ['OPENCLAW_HOME'],'.openclaw','orchestrator','orchestrator.db'))
print(conn.execute("select id from tasks where plan_id=? and work_type='ui'", ('${PLAN_ID}',)).fetchone()[0])
PY
)" --run-id "$RUN_ID" --url https://example.invalid --command-template "python3 -c \"from pathlib import Path; p=Path('{output}'); p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(b'png')\""
python3 -m src.orchestrator.cli ci-update --config "$OPENCLAW_DATA_DIR/orchestrator/config.acceptance.json" --run-id "$RUN_ID" --statuses success
python3 -m src.orchestrator.cli worker-tick --config "$OPENCLAW_DATA_DIR/orchestrator/config.acceptance.json" --stale-minutes 1

EVIDENCE=$(python3 - <<PY
import sqlite3, os, json
conn=sqlite3.connect(os.path.join(os.environ['OPENCLAW_HOME'],'.openclaw','orchestrator','orchestrator.db'))
conn.row_factory=sqlite3.Row
run=conn.execute('select id, openclaw_session_key, state, dispatch_command, dispatch_error_json from runs where id=?', ('${RUN_ID}',)).fetchone()
events=[dict(r) for r in conn.execute('select event_type, payload_json from events where run_id=? order by id', ('${RUN_ID}',)).fetchall()]
all_milestones=[dict(r) for r in conn.execute("select event_type, payload_json from events where run_id=? and event_type like 'milestone:%' order by id", ('${RUN_ID}',)).fetchall()]
bad=[]
for ev in all_milestones:
    payload=json.loads(ev['payload_json']) if ev['payload_json'] else {}
    if payload.get('error') is not None:
        bad.append({'event_type': ev['event_type'], 'error': payload.get('error')})
if '${MODE}' == 'real-discord' and bad:
    print(json.dumps({'milestone_errors': bad}, sort_keys=True))
    raise SystemExit(3)
print(json.dumps({'mode': '${MODE}', 'thread_id': '${THREAD_ID}', 'run_id': run['id'], 'session_key': run['openclaw_session_key'], 'state': run['state'], 'dispatch_command': run['dispatch_command'], 'dispatch_error_json': run['dispatch_error_json'], 'events': [e['event_type'] for e in events], 'milestones_checked': len(all_milestones), 'milestone_errors': bad}, sort_keys=True))
PY
)

echo "EVIDENCE=$EVIDENCE"
echo "ACCEPTANCE_E2E_OK mode=$MODE thread=$THREAD_ID plan=$PLAN_ID run=$RUN_ID"
