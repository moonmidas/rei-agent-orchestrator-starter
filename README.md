# Rei Agent Orchestrator Starter

Bootstrap package for OpenClaw-based orchestration with two install profiles:

- `orchestrator-only` (default)
- `orchestrator+mission-control` (optional via `INSTALL_MISSION_CONTROL=true`)

## Install profile matrix

- **orchestrator-only** (default)
  - Installs OpenClaw CLI
  - Installs/starts systemd gateway (`clawdbot-gateway`)
  - Installs execute-plan skill
  - Bootstraps orchestrator-focused `openclaw.json`
  - Verification script: `scripts/doctor.sh`

- **orchestrator+mission-control** (`INSTALL_MISSION_CONTROL=true`)
  - Everything in `orchestrator-only`
  - Clones/builds Mission Control app
  - Runs Mission Control with PM2 on `:3005`
  - Runs full post-install checks for:
    - gateway service active
    - mission-control PM2 process active
    - sqlite DB file present
    - sqlite tables `tasks` and `agent_runs` present
  - Verification script: `scripts/doctor-full.sh`

## Quick install

### Default profile (orchestrator-only)

```bash
curl -fsSL https://raw.githubusercontent.com/moonmidas/rei-agent-orchestrator-starter/main/install-orchestrator.sh | bash
```

### Full profile (orchestrator + mission-control)

```bash
curl -fsSL https://raw.githubusercontent.com/moonmidas/rei-agent-orchestrator-starter/main/install-orchestrator.sh | sudo INSTALL_MISSION_CONTROL=true bash
```

Optional mission-control install vars:

- `MISSION_CONTROL_DIR` (default `/opt/rei-mission-control`)
- `MISSION_CONTROL_REPO_URL` (default `https://github.com/crshdn/mission-control.git`)
- `MISSION_CONTROL_BRANCH` (default `main`)
- `MISSION_CONTROL_PORT` (default `3005`)
- `MISSION_CONTROL_DB_PATH` (default `$MISSION_CONTROL_DIR/mission-control.db`)

## Health checks

- Orchestrator-only:
  ```bash
  /opt/rei-agent-orchestrator/scripts/doctor.sh
  ```

- Orchestrator+Mission Control:
  ```bash
  /opt/rei-agent-orchestrator/scripts/doctor-full.sh
  ```

Dry-run mode for deterministic command preview:

```bash
/opt/rei-agent-orchestrator/scripts/doctor-full.sh --dry-run
```

## Objective coverage (Phase-0/1 bootstrap parity)

Covered now:

- Profile-based installer (`orchestrator-only`, `orchestrator+mission-control`)
- Mission Control bootstrap/build/run under PM2 at `:3005`
- Post-install verification gates for gateway + mission-control + sqlite DB/tables
- Deterministic full-stack doctor script (`scripts/doctor-full.sh`)

Not yet covered in this starter:

- Mission Control feature development beyond install/runtime bootstrap
- CI watcher/review auto-merge loops
- Superpowers repo integration and workflow automation out of the box

## Hybrid mode toggle (one-off vs persistent)

```bash
openclaw config set channels.discord.threadBindings.spawnSubagentSessions true
# or false
sudo /bin/systemctl restart clawdbot-gateway
```

## Uninstall

```bash
/opt/rei-agent-orchestrator/uninstall.sh
```
