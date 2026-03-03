# 2026-03-02 V1 Done Criteria

V1 is DONE only if all pass:

## Install & bootstrap
- One command install succeeds on clean host.
- Gateway is a prerequisite managed outside this package; orchestrator worker scheduler assets install and run.
- DB migrations apply automatically.
- Default DB path resolves to `${OPENCLAW_HOME}/.openclaw/orchestrator/orchestrator.db` when `OPENCLAW_HOME` is home-base (e.g., `/home/<user>`).
- Scheduler installed for host OS:
  - Linux: `systemd` service + timer
  - macOS: `launchd` agent/plist

## Workflow behavior
- `/execute-plan` produces a structured plan.
- Plan decomposes into deterministic local atomic tasks (superpowers adapter deferred for this release line).
- Microtasks create tasks/runs in DB.
- Chad/Halbert dispatch happens via canonical path only.
- Routing respects explicit map + auto-discovered agent roster + Chad dev fallback.

## CI/PR loop
- For code tasks, PR is opened and CI status tracked.
- State transitions are reflected in runs/tasks.
- Merge policy enforces approval + green checks.
- Auto-merge default is OFF unless explicitly enabled.

## Observability
- Agent Runs shows active and historical runs.
- Task Board reflects run-driven lifecycle transitions.
- Live Feed + Logs show lifecycle events.
- Agent History is selectable and non-empty after activity.

## Reliability
- Worker loop recovers stale runs.
- Retry policy + escalation behavior works.
- No duplicate run creation under retries/replays.

## Discord integration
- Milestone notifications sent to configured thread/channel.
- One notification per milestone (no spam duplicates).
- Approval is captured from the same Discord thread used for task updates.


## Deferred / out-of-scope for v0.2.0
- Superpowers adapter integration is deferred.
- Current decomposition path is local deterministic parsing/decomposition.
