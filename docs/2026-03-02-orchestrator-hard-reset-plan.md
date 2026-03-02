# 2026-03-02 Orchestrator Hard-Reset Plan

## Objective
Transform `rei-agent-orchestrator-starter` from bootstrap/scaffolding into a **fully fledged orchestrator package** that can be installed into an existing OpenClaw setup and execute plans end-to-end.

## Non-negotiables (locked)
1. Assume OpenClaw + Gateway are already installed/running.
2. No Mission Control dependency in this repo.
3. No gateway supervision/service management in this repo.
4. Runtime data stored under OpenClaw home:
   - `${OPENCLAW_HOME}/orchestrator/orchestrator.db`
5. `/execute-plan` is the orchestration entrypoint.
6. Approval happens in the same Discord thread where plan is initiated.
7. Auto-merge default = OFF.
8. Scheduler watchdog runs from OS scheduler (system cron/timer / launchd), not OpenClaw cron.

---

## Current gap summary
- Repo still contains Mission Control profile/install logic.
- Repo still contains gateway systemd unit + references.
- Runtime engine not implemented (DB writes, worker loop, dispatch lifecycle).
- CI/PR loop not implemented as deterministic orchestration path.
- Screenshot evidence gating not fully wired into completion criteria.

---

## Target architecture (v1)

## Components
1. **Orchestrator CLI/runner**
   - command entry: `orchestrator run` (or equivalent npm script)
   - reads orchestrator config + DB

2. **SQLite store**
   - tasks, runs, approvals, events, artifacts, ci_checks
   - migration system included and run on startup

3. **Execute-plan pipeline**
   - parse `/execute-plan`
   - generate plan + atomic tasks
   - pause for approval
   - on approval, dispatch tasks

4. **Dispatch engine**
   - route to agent map with auto-discovery
   - fallback dev agent bootstrap (`chad`) if missing
   - idempotent run creation and transition handling

5. **CI/PR loop**
   - create branch per code task
   - open PR mandatory for code tasks
   - poll local checks and/or GH Actions
   - auto-merge only if approved + green + auto-merge enabled

6. **Screenshot evidence gate**
   - Playwright/browser snapshot support for UI tasks
   - required artifact before task can move to done

7. **Watchdog loop**
   - scheduler every minute (configurable)
   - detect stalled runs
   - refresh run status
   - one retry then escalate

8. **Discord notifier**
   - milestones to source thread by default
   - optional channel/topic override in config

---

## Routing policy (v1)
- Use config map as source of truth:
  - `routing.map.code -> <agent>`
  - `routing.map.content -> <agent>` (optional)
  - `routing.map.default -> <agent>`
- `target_agent` override allowed per task.
- If mapped agent missing:
  - for code tasks, auto-bootstrap/install `chad` and continue
  - for others, fail with actionable config error

---

## Implementation phases

## Phase A — Hard reset (remove wrong scope)
1. Remove Mission Control install/profile logic from installer and docs.
2. Remove `clawdbot-gateway.service` file and all gateway-supervision references.
3. Rewrite README to reflect orchestrator-only runtime product.
4. Add explicit prerequisites check:
   - OpenClaw present
   - Gateway reachable
   - fail fast if missing

**Exit criteria**
- Repo has zero Mission Control references.
- Repo has zero gateway service-management logic.

## Phase B — Runtime foundation
1. Implement migration runner + sqlite schema.
2. Add orchestrator config loader with defaults from `OPENCLAW_HOME`.
3. Implement core task/run/event persistence primitives.
4. Add deterministic healthcheck script for runtime engine.

**Exit criteria**
- Fresh install creates DB + schema + can pass healthcheck.

## Phase C — Execute-plan engine
1. Wire execute-plan parser to orchestration service.
2. Atomic task decomposition pipeline.
3. Approval gate in same Discord thread.
4. Persist plan->tasks->approval state transitions.

**Exit criteria**
- `/execute-plan` creates plan + tasks and waits for approval.

## Phase D — Dispatch + CI/PR + screenshots
1. Dispatch approved tasks via canonical path only.
2. For code tasks:
   - branch creation required
   - PR creation required
3. CI state ingestion (local and/or GH actions polling).
4. Screenshot artifact capture required for UI tasks.

**Exit criteria**
- One real code task can go from approved -> branch -> PR -> CI -> done.

## Phase E — Watchdog + reliability
1. Linux scheduler: systemd timer every minute (configurable).
2. macOS scheduler: launchd equivalent.
3. Stale-run detection + single retry + escalation.
4. Idempotency/dedupe key enforcement.

**Exit criteria**
- Killing a run is auto-detected and recovery path executes correctly.

## Phase F — Acceptance + packaging
1. End-to-end acceptance script:
   - install
   - execute-plan
   - approval
   - dispatch
   - ci/pr
   - completion
2. Provide example config for common scenarios.
3. Publish release tag with install URL + known-good version.

**Exit criteria**
- “Point OpenClaw to URL and run” works on clean Linux/Mac install.

---

## Testing and evidence requirements
For each phase:
- include command transcript
- include before/after DB state proof
- include logs/events screenshots or text traces
- include rollback path

Definition of done (global):
- all phases complete
- all acceptance tests green
- no Mission Control/gateway service scope leakage in repo

---

## Risks and mitigations
1. **Scope creep back into infra mgmt**
   - Mitigation: hard boundary checks in PR template.
2. **Out-of-band spawn bypassing DB tracking**
   - Mitigation: enforce canonical dispatch module only.
3. **Cross-platform scheduler drift**
   - Mitigation: parity tests Linux vs macOS.
4. **PR/CI provider variance**
   - Mitigation: provider adapters with capability checks.

---

## Immediate next execution order
1. Phase A (hard reset) implementation PR.
2. Phase B foundational runtime PR.
3. Phase C execute-plan integration PR.
4. Phase D delivery PR (dispatch/CI/screenshots).
5. Phase E reliability PR.
6. Phase F release PR.
