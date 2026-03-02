# Rei Agent Orchestrator Starter

This repo is a **starter bootstrap**, not a finished orchestration engine yet.

It currently provides install/runtime scaffolding for OpenClaw orchestration and (optionally) Mission Control.

---

## Current implementation (as of now)

### What the code actually does

`install-orchestrator.sh` currently:

1. Installs system dependencies (`git`, `curl`, `jq`, `build-essential`, `sqlite3`).
2. Installs Node (if missing).
3. Creates `clawdbot` user if missing.
4. Installs OpenClaw + PM2 globally for that user.
5. Clones/updates this starter repo into `/opt/rei-agent-orchestrator`.
6. Installs the `execute-plan` skill into:
   - `~/.openclaw/workspace/skills/execute-plan`
7. Installs systemd unit file:
   - `clawdbot-gateway.service`
   - then runs: `daemon-reload`, `enable`, `restart`.
8. If `~/.openclaw/openclaw.json` does not exist, copies template:
   - `templates/openclaw.orchestrator.example.json`
9. Optional full profile (`INSTALL_MISSION_CONTROL=true`):
   - clones/builds Mission Control
   - starts it with PM2 on port `3005`
   - runs `scripts/doctor-full.sh`.

---

## What this repo includes today

- `install-orchestrator.sh`
- `uninstall.sh`
- `systemd-clawdbot-gateway.service`
- `skills/execute-plan/*`
- `templates/openclaw.orchestrator.example.json`
- `templates/orchestrator.config.example.json` (spec template)
- `templates/orchestrator.db.schema.sql` (spec schema template)
- `scripts/doctor.sh`
- `scripts/doctor-full.sh` (for optional Mission Control profile)

---

## What is still template/spec only (not fully implemented engine)

These are defined in docs/templates, but **not yet wired as a full runtime orchestration product** in this starter:

- Dedicated orchestrator worker loop that executes task plans from DB
- Native cron/timer worker that polls and advances orchestration tasks
- Full run/task/event lifecycle engine using `orchestrator.db.schema.sql`
- CI/PR automation loop with approvals/auto-merge policy enforcement
- Screenshot-required completion gates integrated into orchestrator runtime

In short: the repo has the **contracts + scaffolding**, not the full production orchestrator engine yet.

---

## Agent defaults in current templates

- `openclaw.orchestrator.example.json` includes agents: `main`, `chad`, `halbert`
- `orchestrator.config.example.json` routes:
  - `code -> chad`
  - `content -> halbert`

If your current implementation removed/doesn’t use `halbert`, update templates before distribution.

---

## Install profiles

### A) Orchestrator-only (default)

```bash
curl -fsSL https://raw.githubusercontent.com/moonmidas/rei-agent-orchestrator-starter/main/install-orchestrator.sh | sudo bash
```

### B) Orchestrator + Mission Control

```bash
curl -fsSL https://raw.githubusercontent.com/moonmidas/rei-agent-orchestrator-starter/main/install-orchestrator.sh | sudo INSTALL_MISSION_CONTROL=true bash
```

Mission Control env overrides:

- `MISSION_CONTROL_DIR`
- `MISSION_CONTROL_REPO_URL`
- `MISSION_CONTROL_BRANCH`
- `MISSION_CONTROL_PORT`
- `MISSION_CONTROL_DB_PATH`

---

## Required post-install user steps

1. Edit `~/.openclaw/openclaw.json` with real secrets/tokens.
2. Restart gateway:
   ```bash
   sudo /bin/systemctl restart clawdbot-gateway
   ```
3. Run doctor:
   - Orchestrator-only:
     ```bash
     /opt/rei-agent-orchestrator/scripts/doctor.sh
     ```
   - Full profile:
     ```bash
     /opt/rei-agent-orchestrator/scripts/doctor-full.sh
     ```

---

## Operational commands

Gateway:

```bash
sudo /bin/systemctl status clawdbot-gateway
sudo /bin/systemctl restart clawdbot-gateway
```

Mission Control (if full profile):

```bash
pm2 ls
pm2 restart mission-control
pm2 logs mission-control
```

---

## Troubleshooting

### “bad unit file setting”
Reinstall service file from repo and reload daemon:

```bash
sudo install -m 0644 /opt/rei-agent-orchestrator/systemd-clawdbot-gateway.service /etc/systemd/system/clawdbot-gateway.service
sudo systemctl daemon-reload
sudo systemctl restart clawdbot-gateway
```

### Proxy warning (`untrusted address`)

```bash
openclaw config set gateway.trustedProxies '["127.0.0.1","::1"]'
sudo /bin/systemctl restart clawdbot-gateway
```

---

## Uninstall

```bash
/opt/rei-agent-orchestrator/uninstall.sh
```

---

## Status note

If you want this repo to become a true “drop-in 1000x coding orchestrator”, next work is implementing the runtime engine that uses the provided orchestrator DB schema/config templates (currently scaffold only).
