# 2026-03-02 V1 Done Criteria

V1 is DONE only if all pass:

## Install & bootstrap
- One command install succeeds on clean host.
- Services start under supervision (gateway + orchestrator workers).
- DB migrations apply automatically.

## Workflow behavior
- `/execute-plan` produces a structured plan.
- Plan decomposes into microtasks via superpowers adapter.
- Microtasks create tasks/runs in DB.
- Chad/Halbert dispatch happens via canonical path only.

## CI/PR loop
- For code tasks, PR is opened and CI status tracked.
- State transitions are reflected in runs/tasks.
- Merge policy enforces approval + green checks.

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

