# Rei Agent Orchestrator Starter

Orchestrator runtime bootstrap for machines that **already have OpenClaw + Gateway running**.

This repo now targets **orchestrator-only** scope (no Mission Control install, no gateway service management).

## What it does today (actual behavior)

`install-orchestrator.sh` currently:
1. Validates prerequisites:
   - `openclaw` CLI exists
   - `openclaw gateway status` is healthy
2. Installs Linux packages (`apt`):
   - `git`, `curl`, `jq`, `build-essential`, `sqlite3`
3. Clones/updates this repo into `/opt/rei-agent-orchestrator`
4. Installs `/execute-plan` skill into:
   - `/home/<APP_USER>/.openclaw/workspace/skills/execute-plan`
5. Bootstraps config files if missing:
   - `${OPENCLAW_HOME}/openclaw.json` from `templates/openclaw.orchestrator.example.json`
   - `${OPENCLAW_HOME}/orchestrator/config.json` from `templates/orchestrator.config.example.json`
6. Creates orchestrator runtime folders:
   - `${OPENCLAW_HOME}/orchestrator/`
   - `${OPENCLAW_HOME}/orchestrator/logs`
   - `${OPENCLAW_HOME}/orchestrator/artifacts`
7. Runs healthcheck:
   - `scripts/doctor.sh`

## What is implemented in runtime code

Under `src/orchestrator/`:
- SQLite migration runner
- DB repository primitives (plans/tasks/runs/events/approvals/artifacts/ci_checks)
- `/execute-plan` parse + plan/task creation flow
- Approval gate (`approve`) with thread-id checks
- Dispatch/routing/CI/watchdog module scaffolding + tests
- CLI entrypoints:
  - `migrate`, `execute-plan`, `approve`, `dispatch-next`, `ci-update`, `worker-tick`

## What is NOT fully automated yet

- No OS scheduler install wiring in installer yet (cron/launchd templates exist, not auto-installed).
- No direct GitHub API PR/CI automation wiring yet (policy/state flow is scaffolded).
- Screenshot requirement logic exists in runtime module, but full browser capture automation is not yet integrated in installer workflow.

## Requirements

- OpenClaw installed and gateway already running
- Linux host with `apt` for installer (`install-orchestrator.sh` is Linux-oriented today)
- `sudo` privileges

> macOS scheduler template exists (`launchd/`), but installer is not yet cross-platform.

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/moonmidas/rei-agent-orchestrator-starter/main/install-orchestrator.sh | sudo bash
```

## Important env defaults

- `APP_DIR` default: `/opt/rei-agent-orchestrator`
- `APP_USER` default: `clawdbot`
- `OPENCLAW_HOME` default: `/home/${APP_USER}/.openclaw`
- DB default path: `${OPENCLAW_HOME}/orchestrator/orchestrator.db`

## Verify

```bash
/opt/rei-agent-orchestrator/scripts/doctor.sh
```

Optional runtime checks:

```bash
PYTHONPATH=/opt/rei-agent-orchestrator python3 -m src.orchestrator.cli migrate
PYTHONPATH=/opt/rei-agent-orchestrator python3 -m src.orchestrator.cli worker-tick
/opt/rei-agent-orchestrator/scripts/acceptance-e2e.sh
```

## Core CLI examples

```bash
PYTHONPATH=. python3 -m src.orchestrator.cli migrate
PYTHONPATH=. python3 -m src.orchestrator.cli execute-plan --thread-id <thread> --text '/execute-plan ...'
PYTHONPATH=. python3 -m src.orchestrator.cli approve --plan-id <id> --thread-id <thread> --approver <user>
PYTHONPATH=. python3 -m src.orchestrator.cli dispatch-next --plan-id <id> --branch task/<id> --pr-url <url>
PYTHONPATH=. python3 -m src.orchestrator.cli ci-update --run-id <id> --statuses pending,success
PYTHONPATH=. python3 -m src.orchestrator.cli worker-tick
```

## Included files

- `install-orchestrator.sh`
- `uninstall.sh`
- `scripts/doctor.sh`
- `scripts/doctor-runtime.sh`
- `scripts/acceptance-e2e.sh`
- `skills/execute-plan/*`
- `templates/openclaw.orchestrator.example.json`
- `templates/orchestrator.config.example.json`
- `templates/orchestrator.db.schema.sql`
- `templates/scheduler/orchestrator.cron.example`
- `launchd/com.rei.orchestrator.worker.plist`

## Uninstall

```bash
/opt/rei-agent-orchestrator/uninstall.sh
```
