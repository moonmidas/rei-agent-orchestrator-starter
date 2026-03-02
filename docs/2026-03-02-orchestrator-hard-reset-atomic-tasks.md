# 2026-03-02 Orchestrator Hard-Reset — Atomic Task Breakdown

Source plan: `docs/2026-03-02-orchestrator-hard-reset-plan.md`

## Conventions
- Status: `todo | doing | blocked | done`
- Each task must include evidence (commands/output) in PR description.
- Commit strategy: one commit per atomic task.

---

## Phase A — Hard reset scope cleanup

### A-01 Remove Mission Control from installer
- Status: todo
- Goal: eliminate `INSTALL_MISSION_CONTROL` profile and all mission-control install logic.
- Files:
  - `install-orchestrator.sh`
- Done when:
  - no mission-control env vars or install branches remain.

### A-02 Remove gateway supervision from package
- Status: todo
- Goal: package must not manage gateway service.
- Files:
  - `systemd-clawdbot-gateway.service` (delete)
  - `install-orchestrator.sh`
  - `uninstall.sh`
  - `README.md`
- Done when:
  - repo has zero `clawdbot-gateway.service` references.

### A-03 Add hard prerequisite checks
- Status: todo
- Goal: fail fast if OpenClaw or gateway are missing/unreachable.
- Files:
  - `install-orchestrator.sh`
  - `scripts/doctor.sh`
- Done when:
  - installer exits with clear errors if `openclaw` missing or gateway probe fails.

### A-04 Rewrite README to true scope
- Status: todo
- Goal: docs describe only orchestrator runtime product.
- Files:
  - `README.md`
- Done when:
  - no mismatch between README claims and code behavior.

---

## Phase B — Runtime foundation

### B-01 Create orchestrator runtime directory layout
- Status: todo
- Goal: standard app paths under OpenClaw home.
- Files:
  - `install-orchestrator.sh`
  - `templates/orchestrator.config.example.json`
- Done when:
  - defaults resolve to `${OPENCLAW_HOME}/orchestrator/*`.

### B-02 Implement migration runner
- Status: todo
- Goal: db schema auto-applies on startup.
- Files:
  - `src/` (new runtime app files)
  - `templates/orchestrator.db.schema.sql` (or migration split)
- Done when:
  - fresh install creates DB and all core tables.

### B-03 Implement persistence primitives
- Status: todo
- Goal: CRUD helpers for tasks/runs/approvals/events/artifacts.
- Files:
  - `src/db/*`
- Done when:
  - unit checks pass for create/read/update transitions.

### B-04 Add deterministic doctor check for runtime DB
- Status: todo
- Goal: healthcheck validates DB path + required tables.
- Files:
  - `scripts/doctor.sh`
  - optional `scripts/doctor-runtime.sh`
- Done when:
  - doctor exits non-zero on missing schema.

---

## Phase C — `/execute-plan` engine integration

### C-01 Wire parser to orchestration service
- Status: todo
- Goal: `/execute-plan` persists a plan record and generated tasks.
- Files:
  - `skills/execute-plan/*`
  - `src/orchestrator/plan-service.*`
- Done when:
  - execute-plan produces persisted tasks in DB.

### C-02 Atomic task decomposition implementation
- Status: todo
- Goal: deterministic microtask generation + ordering.
- Files:
  - `src/orchestrator/decompose.*`
- Done when:
  - plan is split into atomic tasks with dependency edges.

### C-03 Discord-thread approval gate
- Status: todo
- Goal: approval captured in same origin thread.
- Files:
  - `src/orchestrator/approval.*`
  - config templates
- Done when:
  - no dispatch occurs before approval event.

---

## Phase D — Dispatch + CI/PR + screenshots

### D-01 Canonical dispatch path only
- Status: todo
- Goal: every run created via one dispatch module.
- Files:
  - `src/orchestrator/dispatch.*`
- Done when:
  - out-of-band spawn path disabled for tracked workflows.

### D-02 Routing + agent discovery + Chad bootstrap
- Status: todo
- Goal: routing map + fallback to Chad for dev tasks.
- Files:
  - `src/orchestrator/routing.*`
  - `templates/orchestrator.config.example.json`
- Done when:
  - missing dev mapping auto-resolves to chad.

### D-03 Branch + PR mandatory for code tasks
- Status: todo
- Goal: enforce branch-per-task and PR creation for code work.
- Files:
  - `src/orchestrator/git-pr.*`
- Done when:
  - code task cannot complete without PR URL.

### D-04 CI polling adapter
- Status: todo
- Goal: local checks and/or GitHub Actions status integration.
- Files:
  - `src/orchestrator/ci.*`
- Done when:
  - run transitions to waiting_ci/review based on checks.

### D-05 Screenshot evidence gate
- Status: todo
- Goal: require Playwright/browser snapshots for UI tasks.
- Files:
  - `src/orchestrator/artifacts.*`
- Done when:
  - UI task cannot move to done without screenshot artifact.

---

## Phase E — Watchdog and reliability

### E-01 Linux scheduler wiring (systemd timer)
- Status: todo
- Goal: every-minute worker loop invocation.
- Files:
  - `systemd/rei-orchestrator-worker.service`
  - `systemd/rei-orchestrator-worker.timer`
  - installer hooks
- Done when:
  - timer active and triggering worker.

### E-02 macOS scheduler wiring (launchd)
- Status: todo
- Goal: parity with Linux loop cadence.
- Files:
  - `launchd/com.rei.orchestrator.worker.plist`
  - installer hooks
- Done when:
  - launchctl loads and triggers worker.

### E-03 Stale run detection + retry-once policy
- Status: todo
- Goal: detect stuck runs, retry once, then escalate.
- Files:
  - `src/orchestrator/watchdog.*`
- Done when:
  - simulated stuck run flows through retry + escalation.

### E-04 Idempotency key enforcement
- Status: todo
- Goal: prevent duplicate active runs for same transition.
- Files:
  - `src/db/*`
  - dispatch layer
- Done when:
  - replayed trigger yields no duplicate run.

---

## Phase F — Acceptance + packaging

### F-01 End-to-end acceptance script
- Status: todo
- Goal: run install -> execute-plan -> approval -> dispatch -> CI/PR -> completion.
- Files:
  - `scripts/acceptance-e2e.sh`
- Done when:
  - script passes on clean host.

### F-02 Versioned release + install URL docs
- Status: todo
- Goal: publish release tag + immutable install instructions.
- Files:
  - `README.md`
  - release notes
- Done when:
  - user can install specific version via URL.

### F-03 Rollback and disaster recovery doc
- Status: todo
- Goal: safe rollback path for failed upgrades.
- Files:
  - `docs/rollback.md`
- Done when:
  - rollback procedure tested once.

---

## Dependency order (must respect)
- A-* before B-*
- B-* before C-*
- C-* before D-*
- D-* before E-*
- E-* before F-*

## Minimal next sprint recommendation
1. A-01, A-02, A-03, A-04
2. B-01, B-02, B-03, B-04
3. C-01, C-02, C-03
