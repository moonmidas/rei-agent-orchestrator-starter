# 2026-03-03 Release Go-Blockers Plan

## Objective
Close the release blockers found in the repo audit so `rei-agent-orchestrator-starter` is truly installable + verifiable on a clean OpenClaw host.

## Scope (from audit)
1. `OPENCLAW_HOME` semantics are wrong in installer/runtime scripts (double `.openclaw` path bug).
2. `ensure_chad_agent` detection is brittle vs current `openclaw agents list --json` shape.
3. UI screenshot gate can leave inconsistent run/task state on CI success.
4. Routing can fail before capabilities are probed (non-code tasks, valid agents present).
5. Real acceptance flow can pass while Discord milestone sends fail.
6. README/docs over-claim vs current behavior/evidence.

## Definition of Done
- Fresh install works with default settings (no manual env patching).
- Real acceptance script fails on real failures and passes only with true success.
- Run/task states remain consistent across CI + screenshot gates.
- Routing/dispatch behave correctly with current OpenClaw CLI outputs.
- README + docs match the code and verified behavior.

---

## Atomic Tasks

### A-01 Normalize `OPENCLAW_HOME` contract everywhere
- **Status:** todo
- **Goal:** Use OpenClaw’s expected home base (`/home/<user>`) instead of `/home/<user>/.openclaw`.
- **Files:**
  - `install-orchestrator.sh`
  - `templates/systemd/rei-orchestrator-worker.service`
  - `scripts/acceptance-e2e.sh`
  - `scripts/doctor.sh`
  - `scripts/doctor-runtime.sh`
  - `scripts/install-launchd-macos.sh` (if env references are added/updated)
- **Done when:**
  - `openclaw config get` and `openclaw agents list --json` resolve the expected user config/agents under default install.
  - Real acceptance can run without overriding `OPENCLAW_HOME` manually.

### A-02 Add preflight guard for broken home resolution
- **Status:** todo
- **Goal:** Fail fast with actionable error if `OPENCLAW_HOME` points at `.openclaw` leaf directory.
- **Files:**
  - `install-orchestrator.sh`
  - `scripts/doctor.sh`
- **Done when:**
  - installer/doctor emit clear guidance and non-zero exit for invalid home base.

### B-01 Fix Chad detection for current OpenClaw JSON output
- **Status:** todo
- **Goal:** Handle both top-level array and `{ agents: [...] }` response shapes.
- **Files:**
  - `install-orchestrator.sh`
- **Done when:**
  - existing Chad agent is detected correctly (no false auto-add).
  - missing Chad path still auto-creates Chad correctly.

### B-02 Probe capabilities before routing resolution
- **Status:** todo
- **Goal:** Ensure non-code tasks don’t fail early when mapped agent exists but `_known_agents` is still empty.
- **Files:**
  - `src/orchestrator/dispatch.py`
  - `src/orchestrator/openclaw_dispatch.py` (if helper needed)
  - `tests/test_dispatch.py`
  - `tests/test_routing.py`
- **Done when:**
  - routing resolves against actual probed agent list before dispatch.
  - non-code mapped agent path passes under test.

### C-01 Fix CI + screenshot gate state consistency
- **Status:** todo
- **Goal:** Never set run `completed` before artifact gate passes.
- **Files:**
  - `src/orchestrator/dispatch.py`
  - `tests/test_dispatch.py`
- **Done when:**
  - UI task without screenshot cannot result in `runs.state='completed'`.
  - task/run states remain aligned on both success and gate-failure paths.

### C-02 Define explicit failure/review state for missing required artifacts
- **Status:** todo
- **Goal:** Make gate-failure deterministic (`failed` or `waiting_review`) with event trail.
- **Files:**
  - `src/orchestrator/dispatch.py`
  - `src/orchestrator/artifacts.py` (if richer error typing is needed)
  - `tests/test_dispatch.py`
- **Done when:**
  - artifact gate failure emits an event + deterministic run/task status.

### D-01 Harden real acceptance validation
- **Status:** done
- **Goal:** Acceptance should fail if milestone sends fail or target thread is invalid.
- **Files:**
  - `scripts/acceptance-e2e.sh`
  - `README.md`
- **Done when:**
  - real mode requires valid Discord target/thread input.
  - script checks milestone event payload errors and fails on non-null error.

### D-02 Add acceptance modes explicitly
- **Status:** done
- **Goal:** Separate concerns: local runtime acceptance vs full Discord-integrated acceptance.
- **Files:**
  - `scripts/acceptance-e2e.sh`
  - `README.md`
- **Done when:**
  - documented modes (e.g., `--mock`, `--real-local`, `--real-discord`) are explicit.
  - each mode has clear prerequisites and pass/fail criteria.

### E-01 Align README claims with proven behavior
- **Status:** done
- **Goal:** Remove over-claims; state exact guarantees and caveats.
- **Files:**
  - `README.md`
- **Done when:**
  - every “Current behavior” bullet is backed by tests or acceptance evidence.
  - caveats include current constraints honestly.

### E-02 Sync planning docs with execution reality
- **Status:** done
- **Goal:** Reflect current phase progress + remaining gaps in atomic docs.
- **Files:**
  - `docs/2026-03-02-orchestrator-hard-reset-atomic-tasks.md`
  - `docs/2026-03-02-v1-done-criteria.md`
  - `docs/2026-03-02-v1-single-source-of-truth-spec.md` (if needed)
- **Done when:**
  - status fields are accurate (not all `todo` if completed).
  - deferred gaps (e.g., superpowers adapter) are explicitly marked as deferred/out-of-scope.

### E-03 Release metadata integrity
- **Status:** todo
- **Goal:** Ensure rollback docs and release notes reference real tags/versions.
- **Files:**
  - `docs/rollback.md`
  - `docs/releases/v0.2.0.md`
  - git tags (release process)
- **Done when:**
  - referenced tag exists, or docs are updated to real rollback target.

---

## Execution Order (strict)
1. `A-01` -> `A-02`
2. `B-01` -> `B-02`
3. `C-01` -> `C-02`
4. `D-01` -> `D-02`
5. `E-01` -> `E-03`

---

## Validation Checklist (release gate)
- [ ] `python3 -m unittest discover -s tests -v`
- [ ] `scripts/doctor.sh`
- [ ] `scripts/doctor-runtime.sh`
- [ ] `scripts/acceptance-e2e.sh --mock`
- [ ] `scripts/acceptance-e2e.sh` (real mode with valid Discord target)
- [ ] Manual smoke: one `/execute-plan` flow with approval + dispatch + CI update + milestone post

## Evidence requirements per atomic task
- command(s) run
- output proof
- files changed
- rollback note
- any residual risk
