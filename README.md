# Rei Agent Orchestrator Starter

This package installs **agent orchestration** (Rei orchestrator + Chad/Halbert workers) using OpenClaw.

It does **not** install Mission Control UI or its SQLite-backed job board by default.

## What this package does today
- Installs OpenClaw
- Installs/starts systemd-supervised Gateway (`clawdbot-gateway`)
- Ships orchestrator-focused `openclaw.json` template
- Configures agent roster:
  - `main` (Rei orchestrator)
  - `chad` (dev executor)
  - `halbert` (content executor)
- Enables Discord thread-bound persistence toggle in template
- Installs the `execute-plan` skill into workspace skills path

## What this package does NOT include (yet)
- Mission Control app install/deploy
- SQLite task board (`tasks`, `agent_runs`) and UI panels
- CI watcher/review auto-merge loops
- Superpowers repository/tooling integration out of the box

## Quick install

```bash
curl -fsSL https://raw.githubusercontent.com/moonmidas/rei-agent-orchestrator-starter/main/install-orchestrator.sh | bash
```

Then:
1. Edit `/home/clawdbot/.openclaw/openclaw.json` with real tokens.
2. Restart gateway:
   ```bash
   sudo /bin/systemctl restart clawdbot-gateway
   ```
3. Verify:
   ```bash
   /opt/rei-agent-orchestrator/scripts/doctor.sh
   ```

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
