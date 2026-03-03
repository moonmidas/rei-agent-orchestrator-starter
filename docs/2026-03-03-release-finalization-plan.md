# 2026-03-03 Release Finalization Plan

## Objective
Ship `rei-agent-orchestrator-starter` with zero known release blockers: consistent pathing, aligned docs, passing validation, and published release metadata.

## Scope
This plan replaces prior plan docs and is now the single active release plan.

## Definition of Done
- No known runtime path mismatches (`OPENCLAW_HOME`, DB path, artifacts path).
- README/docs reflect actual implementation and verification behavior.
- Full validation matrix passes (tests + doctor + acceptance modes).
- Branch is merged to `main`, release tag is published, install path is verifiably usable.

---

## Atomic Tasks

### A-01 Fix template DB path consistency
- **Status:** done (2026-03-03)
- **Goal:** Align example config DB path with runtime/doctor expectations.
- **Files:**
  - `templates/orchestrator.config.example.json`
- **Done when:**
  - template uses `${OPENCLAW_HOME}/.openclaw/orchestrator/orchestrator.db`
  - clean-home simulation does not produce DB path split.

### A-02 Fix screenshot default artifact path consistency
- **Status:** todo
- **Goal:** Ensure screenshot defaults write under `.openclaw/orchestrator/artifacts`.
- **Files:**
  - `src/orchestrator/cli.py`
- **Done when:**
  - default output dir resolves to `${OPENCLAW_HOME}/.openclaw/orchestrator/artifacts`
  - captured artifact path matches DB/runtime conventions.

### A-03 Add regression checks for path consistency
- **Status:** todo
- **Goal:** Prevent future drift between config defaults, CLI defaults, and doctor/runtime expectations.
- **Files:**
  - `tests/test_config.py` (new)
  - `tests/test_screenshot.py` (or adjacent CLI-path test)
- **Done when:**
  - tests fail on old path behavior and pass on corrected behavior.

### A-04 Verify clean-home bootstrap behavior
- **Status:** todo
- **Goal:** Confirm fresh env (`OPENCLAW_HOME=/tmp/...`) produces expected config + DB + artifacts locations.
- **Files:**
  - `scripts/doctor-runtime.sh` (only if needed)
  - evidence output in PR notes
- **Done when:**
  - one scripted dry run proves expected path layout end-to-end.

### B-01 Align README with final runtime behavior
- **Status:** todo
- **Goal:** Ensure README claims map to validated behavior only.
- **Files:**
  - `README.md`
- **Done when:**
  - verify section exactly matches current commands/modes
  - caveats mention required Discord thread id + permissions for `--real-discord`.

### B-02 Align docs with single-source release plan
- **Status:** todo
- **Goal:** Remove ambiguity between legacy docs and this plan.
- **Files:**
  - `docs/2026-03-02-v1-done-criteria.md`
  - `docs/2026-03-02-v1-single-source-of-truth-spec.md`
  - `docs/2026-03-02-v1-install-acceptance-checklist.md`
- **Done when:**
  - no conflicting path defaults or completion claims remain.

### C-01 Run full automated verification matrix
- **Status:** todo
- **Goal:** Prove release candidate health.
- **Commands:**
  - `python3 -m unittest discover -s tests -v`
  - `scripts/doctor.sh`
  - `scripts/doctor-runtime.sh`
  - `scripts/acceptance-e2e.sh --mock`
  - `scripts/acceptance-e2e.sh --real-local`
  - `scripts/acceptance-e2e.sh --real-discord --thread-id <thread_id>`
- **Done when:**
  - all commands pass with captured outputs.

### C-02 Run one real thread smoke flow
- **Status:** todo
- **Goal:** Validate live `/execute-plan` lifecycle in a Discord thread.
- **Done when:**
  - approve + dispatch + CI update + milestone lifecycle observed
  - no milestone payload errors.

### D-01 Publish code changes
- **Status:** todo
- **Goal:** Move local release-go-blockers work to remote and review path.
- **Done when:**
  - branch pushed
  - PR opened to `main` with evidence checklist.

### D-02 Merge and release tag
- **Status:** todo
- **Goal:** Finalize releasable state and immutable version marker.
- **Files/metadata:**
  - `docs/releases/v0.2.0.md`
  - Git tag `v0.2.0`
- **Done when:**
  - PR merged to `main`
  - `v0.2.0` tag created + pushed.

### D-03 Post-merge install sanity check
- **Status:** todo
- **Goal:** Confirm install command from `main` matches shipped behavior.
- **Done when:**
  - fresh install smoke succeeds on target host profile
  - no pathing regressions observed.

---

## Execution Order (strict)
1. A-01 → A-04
2. B-01 → B-02
3. C-01 → C-02
4. D-01 → D-03

---

## Release Gate Checklist
- [ ] All atomic tasks marked done
- [ ] Verification outputs captured
- [ ] README/docs aligned with actual behavior
- [ ] Main branch updated
- [ ] Tag `v0.2.0` published
