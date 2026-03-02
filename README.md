# Rei Agent Orchestrator Starter

A production-oriented starter package to install an **OpenClaw orchestration stack** with:

- **Rei (`main`)** as orchestrator
- **Chad (`chad`)** as dev executor
- **Halbert (`halbert`)** as content executor

This repo is focused on **installation + runtime bootstrap**.
It supports two install profiles:

1) `orchestrator-only` (default)
2) `orchestrator+mission-control` (optional)

---

## What this package does

### Always (both profiles)
- Installs Node + OpenClaw CLI (if missing)
- Installs and configures a supervised gateway service (`clawdbot-gateway.service`)
- Installs `/execute-plan` skill assets into workspace skills path
- Bootstraps orchestrator config template if missing (`~/.openclaw/openclaw.json`)
- Provides baseline healthcheck script (`scripts/doctor.sh`)

### Optional profile: `orchestrator+mission-control`
- Clones + builds Mission Control
- Starts Mission Control via PM2 (default port `3005`)
- Runs full-stack checks via `scripts/doctor-full.sh`:
  - gateway service active
  - PM2 `mission-control` online
  - sqlite DB exists
  - sqlite tables `tasks` and `agent_runs` exist

---

## What this package does **not** do (yet)

- Full superpowers automation integration out-of-the-box
- Full CI/review/merge automation loops by itself
- End-to-end Mission Control feature orchestration logic (beyond install/runtime bootstrap)

> This starter gives you a clean install baseline. Workflow automation layers are added on top.

---

## Architecture at a glance

- **Gateway**: OpenClaw gateway process, supervised by systemd
- **Orchestrator**: Rei (`main`) routes work to Chad/Halbert
- **Skill contract**: `/execute-plan` parser + dispatch contract shipped
- **Optional** Mission Control: UI/DB runtime managed by PM2

---

## Prerequisites

- Ubuntu/Debian-like Linux with `sudo`
- Internet access for package installs + git clone
- If using Discord:
  - bot token
  - guild/channel permissions

---

## Install

### 1) Orchestrator-only (default)

```bash
curl -fsSL https://raw.githubusercontent.com/moonmidas/rei-agent-orchestrator-starter/main/install-orchestrator.sh | sudo bash
```

### 2) Orchestrator + Mission Control

```bash
curl -fsSL https://raw.githubusercontent.com/moonmidas/rei-agent-orchestrator-starter/main/install-orchestrator.sh | sudo INSTALL_MISSION_CONTROL=true bash
```

### Optional Mission Control env vars

- `MISSION_CONTROL_DIR` (default `/opt/rei-mission-control`)
- `MISSION_CONTROL_REPO_URL` (default `https://github.com/crshdn/mission-control.git`)
- `MISSION_CONTROL_BRANCH` (default `main`)
- `MISSION_CONTROL_PORT` (default `3005`)
- `MISSION_CONTROL_DB_PATH` (default `$MISSION_CONTROL_DIR/mission-control.db`)

Example:

```bash
curl -fsSL https://raw.githubusercontent.com/moonmidas/rei-agent-orchestrator-starter/main/install-orchestrator.sh | \
  sudo INSTALL_MISSION_CONTROL=true MISSION_CONTROL_PORT=3010 bash
```

---

## Post-install: required user steps

After install, edit:

### A) OpenClaw runtime config
`/home/clawdbot/.openclaw/openclaw.json`

Set at minimum:
- `gateway.auth.token`
- Discord settings (if used): token + channel config
- Agent roster/models if needed

Template:
- `templates/openclaw.orchestrator.example.json`

### B) Restart gateway after config edits

```bash
sudo /bin/systemctl restart clawdbot-gateway
```

### C) Trust reverse proxy (if using nginx/caddy)

```bash
openclaw config set gateway.trustedProxies '["127.0.0.1","::1"]'
sudo /bin/systemctl restart clawdbot-gateway
```

---

## Verification

### Orchestrator-only

```bash
/opt/rei-agent-orchestrator/scripts/doctor.sh
```

### Full profile

```bash
/opt/rei-agent-orchestrator/scripts/doctor-full.sh
```

Dry-run command preview:

```bash
/opt/rei-agent-orchestrator/scripts/doctor-full.sh --dry-run
```

---

## Daily operations

### Gateway

```bash
sudo /bin/systemctl status clawdbot-gateway
sudo /bin/systemctl restart clawdbot-gateway
```

### Mission Control (if installed)

```bash
pm2 ls
pm2 restart mission-control
pm2 logs mission-control
```

---

## Hybrid mode: one-off vs persistent worker sessions

Toggle Discord thread-bound persistent sessions:

```bash
openclaw config set channels.discord.threadBindings.spawnSubagentSessions true
# or false
sudo /bin/systemctl restart clawdbot-gateway
```

- `true` = persistent thread-bound sessions allowed
- `false` = one-off run mode only

---

## Troubleshooting

### “bad unit file setting”
Reinstall the unit and reload:

```bash
sudo install -m 0644 /opt/rei-agent-orchestrator/systemd-clawdbot-gateway.service /etc/systemd/system/clawdbot-gateway.service
sudo systemctl daemon-reload
sudo systemctl restart clawdbot-gateway
```

### “Proxy headers detected from untrusted address”
Set `gateway.trustedProxies` (see post-install section).

### “device identity required” in web clients
Verify token + runtime config + restart gateway.

---

## Security notes

- Never commit real tokens to git
- Keep `openclaw.json` private
- Keep `gateway.trustedProxies` narrow (only real proxy IPs)
- Prefer supervised services (systemd) over ad-hoc runs

---

## Included files

- `install-orchestrator.sh`
- `uninstall.sh`
- `scripts/doctor.sh`
- `scripts/doctor-full.sh` (when present in full profile path)
- `templates/openclaw.orchestrator.example.json`
- `systemd-clawdbot-gateway.service`
- `skills/execute-plan/*`

---

## Uninstall

```bash
/opt/rei-agent-orchestrator/uninstall.sh
```
