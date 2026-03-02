# Rollback & Disaster Recovery

## Backup before upgrade

```bash
export OPENCLAW_HOME=${OPENCLAW_HOME:-$HOME/.openclaw}
mkdir -p "$OPENCLAW_HOME/orchestrator/backups"
sqlite3 "$OPENCLAW_HOME/orchestrator/orchestrator.db" ".backup '$OPENCLAW_HOME/orchestrator/backups/orchestrator-$(date +%Y%m%d-%H%M%S).db'"
```

## Roll back code to known-good tag

```bash
cd /opt/rei-agent-orchestrator
git fetch --tags
git checkout v0.2.0
```

## Restore DB backup

```bash
cp "$OPENCLAW_HOME/orchestrator/backups/<backup>.db" "$OPENCLAW_HOME/orchestrator/orchestrator.db"
./scripts/doctor-runtime.sh
```

## Post-rollback verification

```bash
PYTHONPATH=. python3 -m src.orchestrator.cli migrate
./scripts/acceptance-e2e.sh
```
