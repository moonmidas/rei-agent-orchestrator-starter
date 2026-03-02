# Rei Agent Orchestrator Starter

Orchestrator-only starter for OpenClaw environments.

This repo installs one thing: the `execute-plan` skill and supporting templates into an existing OpenClaw setup. It does **not** install or manage gateway services.

## Scope

What this starter does:
- clones/updates this repository into `/opt/rei-agent-orchestrator` (default)
- installs `skills/execute-plan` into `~/.openclaw/workspace/skills/execute-plan`
- bootstraps `~/.openclaw/openclaw.json` from template if missing
- runs `scripts/doctor.sh` checks

What this starter does not do:
- does not install OpenClaw for you
- does not start/stop/restart gateway services
- does not provide a full runtime orchestration engine yet (DB worker/dispatcher lifecycle still scaffold/template)

## Hard prerequisites

Before running installer:
- `openclaw` CLI must be installed and in `PATH`
- `openclaw gateway status` must succeed

Installer fails fast if either prerequisite is missing.

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/moonmidas/rei-agent-orchestrator-starter/main/install-orchestrator.sh | sudo bash
```

## Post-install

1. Edit `~/.openclaw/openclaw.json` with real tokens/secrets.
2. Run doctor:

```bash
/opt/rei-agent-orchestrator/scripts/doctor.sh
```

## Validate prerequisites manually

```bash
openclaw --version
openclaw gateway status
```

## Uninstall

```bash
/opt/rei-agent-orchestrator/uninstall.sh
```

## Included files

- `install-orchestrator.sh`
- `uninstall.sh`
- `skills/execute-plan/*`
- `scripts/doctor.sh`
- `scripts/doctor-full.sh` (legacy helper script)
- `templates/openclaw.orchestrator.example.json`
- `templates/orchestrator.config.example.json`
- `templates/orchestrator.db.schema.sql`

## Status

This repo is a starter/scaffold for orchestrator workflows. Phase A hard reset aligns package behavior to orchestrator-only installation and prerequisite validation.
