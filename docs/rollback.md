# Rollback & Disaster Recovery

## Backup before upgrade

```bash
export OPENCLAW_HOME=${OPENCLAW_HOME:-$HOME}
mkdir -p "$OPENCLAW_HOME/.openclaw/orchestrator/backups"
sqlite3 "$OPENCLAW_HOME/.openclaw/orchestrator/orchestrator.db" ".backup '$OPENCLAW_HOME/.openclaw/orchestrator/backups/orchestrator-$(date +%Y%m%d-%H%M%S).db'"
```

## Roll back code to known-good release tag

```bash
cd /opt/rei-agent-orchestrator
git fetch --all --tags
git checkout v0.2.0
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
