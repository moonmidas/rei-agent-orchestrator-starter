# Rei Agent Orchestrator Starter

Orchestrator runtime package for existing OpenClaw installs.

## Install from versioned URL

Pin to an immutable tag (`v0.2.0` example):

```bash
curl -fsSL https://raw.githubusercontent.com/moonmidas/rei-agent-orchestrator-starter/v0.2.0/install-orchestrator.sh | sudo bash
```

## Runtime defaults

- `OPENCLAW_HOME` default: `~/.openclaw`
- Runtime home: `${OPENCLAW_HOME}/orchestrator`
- DB path: `${OPENCLAW_HOME}/orchestrator/orchestrator.db`
- Entrypoint: `/execute-plan`
- Approval: same Discord thread
- Auto-merge default: off

## Core commands

```bash
PYTHONPATH=. python3 -m src.orchestrator.cli migrate
PYTHONPATH=. python3 -m src.orchestrator.cli execute-plan --thread-id <thread> --text '/execute-plan ...'
PYTHONPATH=. python3 -m src.orchestrator.cli approve --plan-id <id> --thread-id <thread> --approver <user>
PYTHONPATH=. python3 -m src.orchestrator.cli dispatch-next --plan-id <id> --branch task/<id> --pr-url <url>
PYTHONPATH=. python3 -m src.orchestrator.cli ci-update --run-id <id> --statuses pending,success
PYTHONPATH=. python3 -m src.orchestrator.cli worker-tick
```

## Validation

```bash
./scripts/doctor.sh
./scripts/acceptance-e2e.sh
```
