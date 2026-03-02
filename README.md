# Rei Agent Orchestrator Starter

This package installs **agent orchestration** (Rei orchestrator + Chad/Halbert workers) using OpenClaw.

It does **not** install Mission Control UI.

## What you get
- OpenClaw installed
- Gateway service supervised by systemd (`clawdbot-gateway`)
- Orchestrator-first config template (`openclaw.orchestrator.example.json`)
- Multi-agent roster:
  - `main` (Rei orchestrator)
  - `chad` (dev executor)
  - `halbert` (content executor)
- Discord thread-binding and persistent-session knobs

## Quick install

```bash
curl -fsSL https://raw.githubusercontent.com/moonmidas/rei-agent-orchestrator-starter/main/install-orchestrator.sh | bash
```

Then:
1. Copy template config:
   ```bash
   cp /opt/rei-agent-orchestrator/templates/openclaw.orchestrator.example.json ~/.openclaw/openclaw.json
   ```
2. Fill tokens/keys in `~/.openclaw/openclaw.json`
3. Start gateway:
   ```bash
   sudo /bin/systemctl restart clawdbot-gateway
   ```
4. Verify:
   ```bash
   /opt/rei-agent-orchestrator/scripts/doctor.sh
   ```

## Orchestration modes
- Default: one-off worker runs (clean + parallel)
- Optional: thread-bound persistent sessions on Discord

Enable/disable at runtime:
```bash
openclaw config set channels.discord.threadBindings.spawnSubagentSessions true
# or false
sudo /bin/systemctl restart clawdbot-gateway
```

## Uninstall
```bash
/opt/rei-agent-orchestrator/uninstall.sh
```
