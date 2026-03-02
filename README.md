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
7. **Installs and enables Linux scheduler wiring**:
   - systemd service `rei-orchestrator-worker.service`
   - systemd timer `rei-orchestrator-worker.timer`
   - default cadence every 60s (`WORKER_INTERVAL_SECONDS` configurable)
8. Runs healthcheck:
   - `scripts/doctor.sh`

## Runtime behavior now implemented

Under `src/orchestrator/`:
- SQLite migration runner
- DB repository primitives (plans/tasks/runs/events/approvals/artifacts/ci_checks)
- `/execute-plan` parse + plan/task creation flow
- Approval gate (`approve`) with thread-id checks
- Discord inbound approval bridge (`approve-from-discord`) using configurable `openclaw message read` polling
  - enforces same-thread approval only
- Dispatch with code-task PR enforcement via real OpenClaw CLI adapter (`openclaw agent --json` by default)
  - persists OpenClaw session linkage on `runs` (`openclaw_session_key`, command, raw response)
- GitHub integration via `gh` CLI:
  - PR auto-create/check for code tasks (`dispatch-next` with configured repo)
  - CI polling from GitHub Actions (`ci-poll`)
  - CI results persisted in `ci_checks` and mapped to run/task states
- Screenshot automation integration:
  - `capture-screenshot` command path (Playwright-compatible command template)
  - screenshot artifacts persisted to DB with metadata
- CLI entrypoints:
  - `migrate`, `execute-plan`, `approve`, `approve-from-discord`, `dispatch-next`, `ci-update`, `ci-poll`, `capture-screenshot`, `worker-tick`

## Remaining caveats

- Linux installer is production path; macOS uses a user-run helper (`scripts/install-launchd-macos.sh`) instead of a root cross-platform installer.
- GitHub integration currently uses GitHub CLI (`gh`) and assumes repository auth is already configured.
- Discord inbound approvals are poll-based (no webhook subscription in this package yet). Configure `discord.approval.fetchCommand` to match your OpenClaw message plugin wiring.
- OpenClaw dispatch command is configurable at `runtime.openclawDispatch.command`; default uses `openclaw agent --agent {agent} --session-id orchestrator:{run_id} --message {dispatch_message} --json` and extracts session id from JSON or key/value output.

## Requirements

- OpenClaw installed and gateway already running
- Linux host with `apt` for installer (`install-orchestrator.sh`)
- `sudo` privileges
- For GitHub automation: `gh` installed and authenticated
- For screenshot automation: Playwright CLI available (default uses `npx playwright screenshot`)

## Install (Linux)

```bash
curl -fsSL https://raw.githubusercontent.com/moonmidas/rei-agent-orchestrator-starter/main/install-orchestrator.sh | sudo bash
```

## macOS scheduler install helper

```bash
APP_DIR=/opt/rei-agent-orchestrator INTERVAL_SECONDS=60 /opt/rei-agent-orchestrator/scripts/install-launchd-macos.sh
```

## Important env defaults

- `APP_DIR` default: `/opt/rei-agent-orchestrator`
- `APP_USER` default: `clawdbot`
- `OPENCLAW_HOME` default: `/home/${APP_USER}/.openclaw`
- DB default path: `${OPENCLAW_HOME}/orchestrator/orchestrator.db`
- Worker cadence default: 60s (`WORKER_INTERVAL_SECONDS`)

## Verify

```bash
/opt/rei-agent-orchestrator/scripts/doctor.sh
```

Optional runtime checks:

```bash
PYTHONPATH=/opt/rei-agent-orchestrator python3 -m src.orchestrator.cli migrate
PYTHONPATH=/opt/rei-agent-orchestrator python3 -m src.orchestrator.cli worker-tick
/opt/rei-agent-orchestrator/scripts/acceptance-e2e.sh               # REAL mode (default)
ACCEPTANCE_MODE=mock /opt/rei-agent-orchestrator/scripts/acceptance-e2e.sh  # Optional mock mode
```

## Core CLI examples

```bash
PYTHONPATH=. python3 -m src.orchestrator.cli migrate
PYTHONPATH=. python3 -m src.orchestrator.cli execute-plan --thread-id <thread> --text '/execute-plan ...'
PYTHONPATH=. python3 -m src.orchestrator.cli approve --plan-id <id> --thread-id <thread> --approver <user>
PYTHONPATH=. python3 -m src.orchestrator.cli approve-from-discord --plan-id <id> --thread-id <thread>
PYTHONPATH=. python3 -m src.orchestrator.cli dispatch-next --plan-id <id> --branch task/<id> --github-repo owner/repo
PYTHONPATH=. python3 -m src.orchestrator.cli ci-poll --run-id <id> --branch task/<id> --github-repo owner/repo
PYTHONPATH=. python3 -m src.orchestrator.cli capture-screenshot --task-id <task-id> --run-id <run-id> --url https://example.com
PYTHONPATH=. python3 -m src.orchestrator.cli worker-tick
```

## Included files

- `install-orchestrator.sh`
- `uninstall.sh`
- `scripts/doctor.sh`
- `scripts/doctor-runtime.sh`
- `scripts/acceptance-e2e.sh`
- `scripts/install-launchd-macos.sh`
- `skills/execute-plan/*`
- `templates/openclaw.orchestrator.example.json`
- `templates/orchestrator.config.example.json`
- `templates/orchestrator.db.schema.sql`
- `templates/systemd/rei-orchestrator-worker.service`
- `templates/systemd/rei-orchestrator-worker.timer`
- `templates/scheduler/orchestrator.cron.example`
- `launchd/com.rei.orchestrator.worker.plist`

## Uninstall

```bash
/opt/rei-agent-orchestrator/uninstall.sh
```
