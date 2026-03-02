# 2026-03-02 V1 Single Source of Truth Spec

## Objective
A fresh OpenClaw install can run the Rei orchestrator stack reliably end-to-end:
plan -> microtasks -> agent dispatch -> CI/PR -> review/merge/report, with full observability.

## Finalized v1 decisions (locked)
- **DB default path:** `${OPENCLAW_HOME}/orchestrator/orchestrator.db` (default OPENCLAW_HOME is `~/.openclaw`).
- **Review/approval location:** approval is captured in the **same Discord thread** where task milestones are posted.
- **Auto-merge default:** **OFF**. Merge is opt-in via config and still requires policy gates.
- **Routing model:** static `routing.map` config + optional agent auto-discovery from OpenClaw agent roster.
- **Dev fallback bootstrap:** if no explicit route exists, default dev/code route falls back to `chad`.
- **Scheduling:** Linux uses `systemd` service + timer; macOS uses `launchd` plist scheduler.

## Canonical truth model
- **Task** = unit of intent (what to do)
- **Run** = unit of execution (who is doing it now)
- **Agent session** = runtime container for a run
- **Event** = immutable lifecycle fact (queued, started, failed, completed, merged)

## Hard rule: canonical dispatch path
All execution MUST go through one orchestrator dispatch API/service.
No direct/out-of-band `sessions_spawn` for production workflow jobs.

## Required modules (v1 scaffolding target)
1. Execute-plan parser + contract (`/execute-plan`, `/xp*`)
2. Routing resolver (`routing.map`, auto-discovery, fallback bootstrap)
3. Task store (SQLite)
4. Run store (SQLite)
5. Dispatch engine (Rei -> Chad/Halbert)
6. CI/PR watcher loop
7. Recovery/scheduler worker loop (`systemd timer` / `launchd`)
8. Observability surfaces (runs, tasks, feed, logs, history)
9. Discord notifier (thread milestones + review state)

## Agent routing contract
- `work_type=code` -> Chad
- `work_type=content` -> Halbert
- optional override: `target_agent`
- optional project overlays: repo/path/test gates/branch conventions
- auto-discovery may populate candidates, but explicit map wins
- if unresolved and `work_type=code`, fallback bootstrap route is Chad

## Idempotency contract
- Dedup key: `task_id + transition + target_agent + hash(payload)`
- Replays must not create duplicate active runs.

## Lifecycle states
### Task states
inbox -> assigned -> in_progress -> review -> done

### Run states
queued -> running -> waiting_ci -> waiting_review -> failed|completed|merged

### Mapping
- queued -> task assigned
- running -> task in_progress
- waiting_review/waiting_ci -> task review
- merged/completed -> task done (gates satisfied)
- failed -> task remains actionable + retry policy

## Review + merge policy (v1)
- Approval is thread-local and read from the same Discord thread used for run updates.
- Auto-merge is disabled by default.
- Merge requires approval + green required checks.

## Security baseline
- gateway auth token required
- trusted proxies configured
- secrets never committed
- env validation before startup
