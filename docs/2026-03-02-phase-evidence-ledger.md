# 2026-03-02 Orchestrator Hard-Reset — Phase Evidence Ledger

Source docs:
- `docs/2026-03-02-orchestrator-hard-reset-plan.md`
- `docs/2026-03-02-orchestrator-hard-reset-atomic-tasks.md`

Purpose:
- Single evidence ledger for Phase A→F execution.
- Each phase/atomic task must be provable with reproducible commands and immutable links (PR + merge commit).

---

## Baseline (from `main` at audit start)
Audit timestamp (UTC): 2026-03-02 20:59+
Repository: `moonmidas/rei-agent-orchestrator-starter` (worktree: `rei-agent-orchestrator-starter-evidence`)

### High-level status through Phase A
- **A-01 Remove legacy optional profile from installer**: **Mostly complete / functionally complete**
  - `install-orchestrator.sh` uses orchestrator-only flow and no `INSTALL_LEGACY_PROFILE` branch.
- **A-02 Remove gateway supervision/service-management scope**: **Partially complete**
  - Main installer/readme no longer manage gateway services.
  - Residual legacy helper still references systemd gateway supervision (`scripts/doctor-full.sh`).
- **A-03 Add hard prerequisite checks**: **Complete**
  - Installer fails fast on missing `openclaw` and unreachable gateway.
  - `scripts/doctor.sh` validates CLI and gateway availability.
- **A-04 Rewrite README to true scope**: **Complete**
  - README now explicitly states orchestrator-only scope and non-goals.

### Baseline evidence snapshot commands/results
```bash
# Baseline scan for legacy/scope references
grep -RInE "legacy|profile|gateway service|systemd-gateway|INSTALL_LEGACY_PROFILE|optional profile|gateway supervision" .

# Baseline files inspected
sed -n '1,220p' install-orchestrator.sh
sed -n '1,220p' README.md
sed -n '1,220p' scripts/doctor.sh
sed -n '1,260p' scripts/doctor-full.sh
```

Observed highlights:
- `install-orchestrator.sh`: preflight checks for `openclaw` and `openclaw gateway status`; no legacy profile installer branch.
- `README.md`: states installer does **not** manage gateway services; orchestrator-only scope.
- `scripts/doctor-full.sh`: contains legacy gateway service/systemctl checks (residual scope leakage).

---

## Evidence requirements (MANDATORY for every phase)

Each phase PR must include all fields below. If a field is not applicable, explicitly set `N/A` with reason.

### Required evidence fields (exact)
1. **Phase / Atomic Task IDs**
   - Example: `Phase B: B-01, B-02`
2. **Objective statement**
   - One sentence: what changed and why.
3. **Pre-state proof**
   - Commands + output proving initial state before change.
4. **Change proof**
   - `git diff --name-only` and relevant file snippets.
5. **Verification commands**
   - Exact commands used to validate behavior.
6. **Verification output**
   - Raw/trimmed outputs showing pass/fail criteria.
7. **Database proof** (required when phase touches runtime state)
   - DB path used.
   - Schema/table/query outputs before and after.
   - Example queries + returned rows/counts.
8. **Artifact proof** (required for UI/screenshot phases)
   - Artifact file path(s), hash(es), and capture command(s).
9. **PR URL**
   - Link to implementation PR for the phase work.
10. **Merge commit**
   - Final merge SHA + branch/tag context.
11. **Rollback note**
   - Concrete rollback steps + command(s) tested or ready.
12. **Risk / follow-up note**
   - Remaining risk and next action.

---

## Evidence template (copy per phase)

```md
## Phase <A-F> Evidence Record
- Phase: <A|B|C|D|E|F>
- Atomic tasks: <IDs>
- Owner: <name>
- Date (UTC): <timestamp>
- Status: <done|blocked>

### 1) Objective
<one sentence>

### 2) Pre-state proof
Commands:
```bash
<commands>
```
Output:
```text
<output>
```

### 3) Change proof
Files changed:
```bash
git diff --name-only <base>...HEAD
```
Snippet(s):
```diff
<key diff>
```

### 4) Verification commands
```bash
<commands>
```

### 5) Verification outputs
```text
<outputs>
```

### 6) Database proof (required for DB-affecting work)
DB path:
```text
${OPENCLAW_HOME}/orchestrator/orchestrator.db
```
Queries:
```bash
sqlite3 "${OPENCLAW_HOME}/orchestrator/orchestrator.db" "<query>"
```
Results:
```text
<rows/counts>
```

### 7) Artifact proof (required for UI tasks)
Capture command(s):
```bash
<playwright/browser command>
```
Artifacts:
```text
<path>
<sha256>
```

### 8) PR and merge
- PR URL: <url>
- Merge commit: <sha>
- Merge timestamp (UTC): <timestamp>

### 9) Rollback note
```bash
<rollback commands>
```

### 10) Risk/follow-up
<notes>
```

---

## Phase-by-phase ledger stubs

## Phase A — Hard reset
- Atomic tasks: A-01, A-02, A-03, A-04
- Baseline status: See “Baseline (from main at audit start)” above.
- Evidence record: _pending update in execution PR_

## Phase B — Runtime foundation
- Atomic tasks: B-01, B-02, B-03, B-04
- Evidence record: _pending_

## Phase C — Execute-plan engine
- Atomic tasks: C-01, C-02, C-03
- Evidence record: _pending_

## Phase D — Dispatch + CI/PR + screenshots
- Atomic tasks: D-01, D-02, D-03, D-04, D-05
- Evidence record: _pending_

## Phase E — Watchdog + reliability
- Atomic tasks: E-01, E-02, E-03, E-04
- Evidence record: _pending_

## Phase F — Acceptance + packaging
- Atomic tasks: F-01, F-02, F-03
- Evidence record: _pending_

---

## Quick evidence checklist (review gate)
- [ ] Commands are copy/paste reproducible
- [ ] Outputs included (not just claims)
- [ ] DB proofs included where applicable
- [ ] UI artifact proofs included where applicable
- [ ] PR URL recorded
- [ ] Merge SHA recorded
- [ ] Rollback procedure recorded
