#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export OPENCLAW_HOME="${OPENCLAW_HOME:-$HOME/.openclaw}"
export PYTHONPATH="$ROOT"
MODE="${ACCEPTANCE_MODE:-real}" # real (default) | mock

mkdir -p "$OPENCLAW_HOME/orchestrator"

TMP_BIN=""
TMP_MESSAGES=""
if [[ "$MODE" == "mock" ]]; then
  TMP_BIN="$(mktemp -d)"
  TMP_MESSAGES="$(mktemp)"
  cat > "$TMP_BIN/openclaw" <<'MOCK'
#!/usr/bin/env bash
set -euo pipefail
if [[ "${1:-}" == "agent" ]]; then
  echo '{"status":"ok","result":{"meta":{"agentMeta":{"sessionId":"session-acceptance-'"${RANDOM}"'"}}}}'
  exit 0
fi
if [[ "${1:-}" == "message" && "${2:-}" == "read" ]]; then
  cat "${OPENCLAW_FAKE_MESSAGES_FILE}"
  exit 0
fi
echo "unsupported fake openclaw invocation: $*" >&2
exit 2
MOCK
  chmod +x "$TMP_BIN/openclaw"
  export PATH="$TMP_BIN:$PATH"
  export OPENCLAW_FAKE_MESSAGES_FILE="$TMP_MESSAGES"
else
  command -v openclaw >/dev/null
  openclaw gateway status >/dev/null
fi

cat > "$OPENCLAW_HOME/orchestrator/config.acceptance.json" <<'JSON'
{
  "database": {"path": "${OPENCLAW_HOME}/orchestrator/orchestrator.db"},
  "routing": {"map": {"code": "chad", "default": "chad"}, "devFallbackAgent": "chad"},
  "discord": {
    "approval": {
      "keywords": ["approve"],
      "fetchCommand": ["openclaw", "message", "read", "--channel", "discord", "--target", "{thread_id}", "--limit", "{limit}"]
    }
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
p = os.path.expanduser(os.path.join(os.environ['OPENCLAW_HOME'], 'orchestrator', 'config.acceptance.json'))
cfg = json.load(open(p))
cfg['database']['path'] = cfg['database']['path'].replace('${OPENCLAW_HOME}', os.environ['OPENCLAW_HOME'])
json.dump(cfg, open(p, 'w'))
PY

python3 -m src.orchestrator.cli migrate --config "$OPENCLAW_HOME/orchestrator/config.acceptance.json"
PLAN_OUT=$(python3 -m src.orchestrator.cli execute-plan --config "$OPENCLAW_HOME/orchestrator/config.acceptance.json" --thread-id acceptance-thread --text '/execute-plan implement api; add tests; capture ui screenshot')
echo "$PLAN_OUT"
PLAN_ID=$(echo "$PLAN_OUT" | awk -F= '/plan_id/{print $2}')

if [[ "$MODE" == "mock" ]]; then
  echo '[{"id":"msg-1","thread_id":"acceptance-thread","author_id":"acceptance-bot","content":"approve"}]' > "$TMP_MESSAGES"
  APPROVAL_OUT=$(python3 -m src.orchestrator.cli approve-from-discord --config "$OPENCLAW_HOME/orchestrator/config.acceptance.json" --plan-id "$PLAN_ID" --thread-id acceptance-thread)
else
  APPROVAL_OUT=$(python3 -m src.orchestrator.cli approve --config "$OPENCLAW_HOME/orchestrator/config.acceptance.json" --plan-id "$PLAN_ID" --thread-id acceptance-thread --approver acceptance-real --text approve)
fi
echo "$APPROVAL_OUT"

RUN_OUT=$(python3 -m src.orchestrator.cli dispatch-next --config "$OPENCLAW_HOME/orchestrator/config.acceptance.json" --plan-id "$PLAN_ID" --branch "task/${PLAN_ID}" --pr-url "https://example.invalid/pr/${PLAN_ID}")
echo "$RUN_OUT"
RUN_ID=$(echo "$RUN_OUT" | awk -F= '/run_id/{print $2}')
python3 -m src.orchestrator.cli ci-update --config "$OPENCLAW_HOME/orchestrator/config.acceptance.json" --run-id "$RUN_ID" --statuses success
python3 -m src.orchestrator.cli worker-tick --config "$OPENCLAW_HOME/orchestrator/config.acceptance.json" --stale-minutes 1

EVIDENCE=$(python3 - <<PY
import sqlite3, os, json
conn=sqlite3.connect(os.path.join(os.environ['OPENCLAW_HOME'],'orchestrator','orchestrator.db'))
conn.row_factory=sqlite3.Row
run=conn.execute('select id, openclaw_session_key, state, dispatch_command from runs where id=?', ('${RUN_ID}',)).fetchone()
events=[dict(r) for r in conn.execute('select event_type from events where run_id=? order by id', ('${RUN_ID}',)).fetchall()]
print(json.dumps({'mode': '${MODE}', 'run_id': run['id'], 'session_key': run['openclaw_session_key'], 'state': run['state'], 'dispatch_command': run['dispatch_command'], 'events': [e['event_type'] for e in events]}))
PY
)

echo "EVIDENCE=$EVIDENCE"
echo "ACCEPTANCE_E2E_OK mode=$MODE plan=$PLAN_ID run=$RUN_ID"
