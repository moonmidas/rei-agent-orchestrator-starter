# Rei Agent Orchestrator Starter

Orchestrator runtime bootstrap for machines that already have OpenClaw installed and gateway running.

## Current behavior

- SQLite runtime: plans/tasks/runs/approvals/events/artifacts/ci_checks/dispatch_attempts
- `/execute-plan` parsing + atomic task persistence
- Approval: same-thread enforced for both manual and Discord-polled approval
- Dispatch hardening:
  - runtime capability probe (`openclaw agents list --json`)
  - canonical dispatch command template (`runtime.openclawDispatch.command`)
  - agent existence guard (default fallback `chad`)
  - dispatch attempt persistence (run_id/session_key/raw response/error)
- CI transitions with screenshot gate enforced on completion paths (including `ci-update`)
- Discord milestone notifier states: queued, dispatched, waiting_ci, failed, completed/merged
  - default destination: origin thread
  - optional override: `discord.milestones.targetThreadId`
  - dedupe key prevents duplicate milestone posts
- Watchdog stale-run retry/escalation
- Linux systemd timer + macOS launchd helper

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/moonmidas/rei-agent-orchestrator-starter/main/install-orchestrator.sh | sudo bash
```

Linux installer now verifies `rei-orchestrator-worker.timer` is active before success.

## Verify

```bash
python3 -m unittest discover -s tests -v
scripts/doctor.sh
scripts/acceptance-e2e.sh --thread-id <discord_thread_id>
```

Mock acceptance is explicit opt-in only:

```bash
scripts/acceptance-e2e.sh --mock
```

## Acceptance preflight (real mode)

`scripts/acceptance-e2e.sh` real mode fails fast unless all are healthy:

- `openclaw gateway status`
- `gh auth status`
- `chad` agent present
- `--thread-id <discord_thread_id>` is provided and used for milestone posts

The script now hard-fails if any persisted milestone event payload contains a non-null `error`.

## Scheduler

Linux:
- `rei-orchestrator-worker.service`
- `rei-orchestrator-worker.timer`

macOS helper:

```bash
scripts/install-launchd-macos.sh install
scripts/install-launchd-macos.sh status
scripts/install-launchd-macos.sh uninstall
```

## Release checklist

- [ ] `python3 -m unittest discover -s tests -v`
- [ ] `scripts/doctor.sh`
- [ ] `scripts/acceptance-e2e.sh` (real mode)
- [ ] Optional: `scripts/acceptance-e2e.sh --mock`
- [ ] Confirm milestone notifications in origin Discord thread
- [ ] Confirm UI-task completion blocked without screenshot artifact

## Known caveats

- Discord approval is polling-based (not event-stream push).
- Dispatch and milestone posting depend on local OpenClaw CLI behavior/version.
- GitHub workflows require `gh` authentication in runtime environment.
- Screenshot capture requires configured command/tool availability (e.g., Playwright).
