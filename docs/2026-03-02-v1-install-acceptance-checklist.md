# 2026-03-02 V1 Install Acceptance Checklist

_Use `docs/2026-03-03-release-finalization-plan.md` for owner/status tracking; this checklist only covers the criteria that must be satisfied._

## Preflight
- [ ] Domain/DNS ready (if web UI/proxy used)
- [ ] Discord bot token
- [ ] OpenClaw gateway token
- [ ] GitHub token/app creds for PR automation

## Install
- [ ] `install-orchestrator.sh` runs cleanly
- [ ] `clawdbot-gateway` active under systemd
- [ ] orchestrator worker service active (if split process)
- [ ] DB created + migrations applied at `${OPENCLAW_HOME}/.openclaw/orchestrator/orchestrator.db`
- [ ] Artifacts directory created at `${OPENCLAW_HOME}/.openclaw/orchestrator/artifacts`
- [ ] scheduler installed for platform:
  - [ ] Linux `systemd` timer
  - [ ] macOS `launchd` plist

## Config validation
- [ ] `gateway.trustedProxies` set
- [ ] `channels.discord.threadBindings.spawnSubagentSessions` explicitly set
- [ ] agent roster includes `main`, `chad`, `halbert`
- [ ] `routing.map` configured for code/content
- [ ] auto-discovery enabled (or explicitly disabled) and documented
- [ ] execute-plan skill present in workspace

## Functional smoke tests
- [ ] `/execute-plan` accepted and parsed
- [ ] One code task dispatches Chad and creates task+run rows
- [ ] One content task dispatches Halbert and creates task+run rows
- [ ] CI/PR status updates run state
- [ ] At least one milestone notification appears in Discord
- [ ] Approval command/event in same Discord thread transitions review gate
- [ ] Logs/live feed/history surfaces show events

## Failure-mode tests
- [ ] Simulated failed run transitions to failed + retry
- [ ] Duplicate dispatch input does not create duplicate active run
- [ ] Restart services and verify state recovery from DB
- [ ] Verify auto-merge remains OFF by default
