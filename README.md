# Rei Agent Orchestrator Starter

Orchestrator runtime bootstrap for machines that **already have OpenClaw installed and gateway running**.

> Scope: orchestrator runtime only (no Mission Control installer, no gateway service supervision logic).

---

## What this repo currently provides

- SQLite-backed orchestration runtime (`plans`, `tasks`, `runs`, `approvals`, `events`, `artifacts`, `ci_checks`)
- `/execute-plan` parser integration + atomic task persistence
- Same-thread approval flow (`approve` and `approve-from-discord` polling bridge)
- Dispatch engine with OpenClaw command adapter
- CI polling integration and run/task transitions
- Screenshot artifact capture command integration
- Watchdog loop (`worker-tick`) + scheduler templates (systemd timer + launchd)
- Install/bootstrap script and runtime doctor checks

---

## Pre-requisites (hard requirements)

The installer assumes these are already true:

1. OpenClaw CLI is installed and usable by the target user.
2. OpenClaw gateway is running and healthy.
3. Target runtime user exists (default `clawdbot`).

If any of these fail, installer exits with a clear error.

---

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/moonmidas/rei-agent-orchestrator-starter/main/install-orchestrator.sh | sudo bash
```

### Installer behavior (actual)

`install-orchestrator.sh`:
1. verifies user exists (`APP_USER`, default `clawdbot`)
2. verifies OpenClaw CLI can be found
3. verifies gateway status (`openclaw gateway status`)
4. installs OS deps (`git`, `curl`, `jq`, `build-essential`, `sqlite3`)
5. clones/updates this repo to `APP_DIR` (default `/opt/rei-agent-orchestrator`)
6. installs `/execute-plan` skill to `~/.openclaw/workspace/skills/execute-plan`
7. bootstraps OpenClaw config template if missing
8. bootstraps orchestrator config under `${OPENCLAW_HOME}/orchestrator/config.json`
9. creates runtime dirs (`logs`, `artifacts`)
10. checks for `chad` agent and **auto-adds it if missing**
11. installs and enables Linux scheduler timer for worker loop
12. runs doctor checks

---

## Paths and defaults

- `APP_DIR`: `/opt/rei-agent-orchestrator`
- `APP_USER`: `clawdbot`
- `OPENCLAW_HOME`: `/home/${APP_USER}/.openclaw`
- DB path: `${OPENCLAW_HOME}/orchestrator/orchestrator.db`

---

## Verify runtime

```bash
/opt/rei-agent-orchestrator/scripts/doctor.sh
```

Optional deeper checks:

```bash
PYTHONPATH=/opt/rei-agent-orchestrator python3 -m src.orchestrator.cli migrate
PYTHONPATH=/opt/rei-agent-orchestrator python3 -m src.orchestrator.cli worker-tick
```

---

## Core runtime commands

```bash
PYTHONPATH=. python3 -m src.orchestrator.cli migrate
PYTHONPATH=. python3 -m src.orchestrator.cli execute-plan --thread-id <thread> --text '/execute-plan ...'
PYTHONPATH=. python3 -m src.orchestrator.cli approve --plan-id <id> --thread-id <thread> --approver <user>
PYTHONPATH=. python3 -m src.orchestrator.cli approve-from-discord --plan-id <id> --thread-id <thread>
PYTHONPATH=. python3 -m src.orchestrator.cli dispatch-next --plan-id <id> --branch task/<id> --github-repo <owner/repo>
PYTHONPATH=. python3 -m src.orchestrator.cli ci-poll --run-id <id> --branch <branch> --github-repo <owner/repo>
PYTHONPATH=. python3 -m src.orchestrator.cli worker-tick
PYTHONPATH=. python3 -m src.orchestrator.cli capture-screenshot --task-id <id> --run-id <id> --url <url>
```

---

## Acceptance

`acceptance-e2e.sh` supports two modes:

- `ACCEPTANCE_MODE=real` (default): uses real OpenClaw dispatch command path
- `ACCEPTANCE_MODE=mock`: mock fallback for isolated dev environments

Run:

```bash
/opt/rei-agent-orchestrator/scripts/acceptance-e2e.sh
```

---

## Scheduler

### Linux (auto-installed by installer)
- `rei-orchestrator-worker.service`
- `rei-orchestrator-worker.timer`

Check:

```bash
systemctl status rei-orchestrator-worker.timer
```

### macOS
Use helper:

```bash
/opt/rei-agent-orchestrator/scripts/install-launchd-macos.sh
```

---

## Known caveats (current)

- `dispatch.commandTemplate` depends on OpenClaw CLI behavior/version in target environment.
- `approve-from-discord` is polling-based via configurable fetch command (not event-stream subscription).
- GitHub PR/CI flow requires `gh` auth in runtime environment.
- Screenshot capture requires Playwright/CLI availability in runtime environment.

---

## Included files

- `install-orchestrator.sh`
- `uninstall.sh`
- `scripts/doctor.sh`
- `scripts/doctor-runtime.sh`
- `scripts/acceptance-e2e.sh`
- `scripts/orchestrator-worker.sh`
- `scripts/install-launchd-macos.sh`
- `skills/execute-plan/*`
- `templates/openclaw.orchestrator.example.json`
- `templates/orchestrator.config.example.json`
- `templates/orchestrator.db.schema.sql`
- `templates/systemd/rei-orchestrator-worker.service`
- `templates/systemd/rei-orchestrator-worker.timer`
- `launchd/com.rei.orchestrator.worker.plist`

---

## Uninstall

```bash
/opt/rei-agent-orchestrator/uninstall.sh
```
