# Rollback & Disaster Recovery

## Backup before upgrade

```bash
export OPENCLAW_HOME=${OPENCLAW_HOME:-$HOME}
mkdir -p "$OPENCLAW_HOME/.openclaw/orchestrator/backups"
sqlite3 "$OPENCLAW_HOME/.openclaw/orchestrator/orchestrator.db" ".backup '$OPENCLAW_HOME/.openclaw/orchestrator/backups/orchestrator-$(date +%Y%m%d-%H%M%S).db'"
```

## Roll back code to known-good revision

`v0.2.0` tag is not published yet in this repo. Use an explicit known-good commit SHA:

```bash
cd /opt/rei-agent-orchestrator
git fetch --all --tags
# Example: replace <known_good_sha> with the release commit recorded in your deploy log
git checkout <known_good_sha>
```

## Restore DB backup

```bash
cp "$OPENCLAW_HOME/.openclaw/orchestrator/backups/<backup>.db" "$OPENCLAW_HOME/.openclaw/orchestrator/orchestrator.db"
./scripts/doctor-runtime.sh
```

## Post-rollback verification

```bash
PYTHONPATH=. python3 -m src.orchestrator.cli migrate
./scripts/acceptance-e2e.sh --real-local
```
