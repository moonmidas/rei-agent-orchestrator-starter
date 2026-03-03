# Rei Agent Orchestrator Starter

Orchestrator runtime bootstrap for machines that already have OpenClaw installed and gateway running.

## Current behavior (verified in unit tests and/or acceptance script)

- SQLite runtime with persisted entities: plans, tasks, runs, approvals, events, artifacts, ci_checks, dispatch_attempts
- `/execute-plan` persists a decomposed task list with deterministic sequence ordering
- Approval is enforced in the originating thread for both manual approve and Discord-polled approve
- Dispatch path uses one engine and records dispatch attempt/session linkage
  - runtime capability probe (`openclaw agents list --json`) is used before routing when needed
  - routing supports explicit map plus dev/code fallback to `chad`
- CI updates enforce screenshot artifact gate before a UI task can finalize as completed
- Milestone notifier emits deduped lifecycle events (queued/dispatched/waiting_ci/failed/completed)
- Watchdog performs stale-run retry-once then escalation
- Scheduler assets are included for Linux (`systemd`) and macOS (`launchd` helper script)

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/moonmidas/rei-agent-orchestrator-starter/main/install-orchestrator.sh | sudo bash
```

Linux installer checks `rei-orchestrator-worker.timer` activation on Linux hosts.

## Verify

```bash
python3 -m unittest discover -s tests -v
scripts/doctor.sh
scripts/acceptance-e2e.sh --real-local
```

Acceptance modes are explicit:

```bash
# Fully local/fake path
scripts/acceptance-e2e.sh --mock

# Real runtime, local no-op milestone sender (default if no mode flag)
scripts/acceptance-e2e.sh --real-local

# Full Discord-integrated acceptance
scripts/acceptance-e2e.sh --real-discord --thread-id <discord_thread_id>
```

## Acceptance preflight

`--real-local` and `--real-discord` fail fast unless all are healthy:

- `openclaw gateway status`
- `gh auth status`
- `chad` agent present

`--real-discord` additionally requires `--thread-id <discord_thread_id>` and hard-fails if any persisted milestone event payload contains a non-null `error`.

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
- [ ] `scripts/acceptance-e2e.sh --real-local`
- [ ] `scripts/acceptance-e2e.sh --real-discord --thread-id <discord_thread_id>`
- [ ] Optional: `scripts/acceptance-e2e.sh --mock`
- [ ] Confirm milestone notifications in origin Discord thread
- [ ] Confirm UI-task completion blocked without screenshot artifact

## Known caveats

- Discord approval is polling-based (not event-stream push).
- `--real-discord` acceptance requires a valid Discord thread id and send permissions for the active OpenClaw account.
- Dispatch and milestone posting behavior depend on local OpenClaw CLI behavior/version.
- GitHub workflows require `gh` authentication in runtime environment.
- Screenshot capture requires configured command/tool availability (e.g., Playwright).
- `--mock` acceptance validates orchestration flow mechanics but does not validate external Discord delivery.
