# 2026-03-02 V1 Install Acceptance Checklist

## Preflight
- [ ] Domain/DNS ready (if web UI/proxy used)
- [ ] Discord bot token
- [ ] OpenClaw gateway token
- [ ] GitHub token/app creds for PR automation

## Install
- [ ] `install-orchestrator.sh` runs cleanly
- [ ] `clawdbot-gateway` active under systemd
- [ ] orchestrator worker service active (if split process)
- [ ] DB created + migrations applied

## Config validation
- [ ] `gateway.trustedProxies` set
- [ ] `channels.discord.threadBindings.spawnSubagentSessions` explicitly set
- [ ] agent roster includes `main`, `chad`, `halbert`
- [ ] execute-plan skill present in workspace

## Functional smoke tests
- [ ] `/execute-plan` accepted and parsed
- [ ] One code task dispatches Chad and creates task+run rows
- [ ] One content task dispatches Halbert and creates task+run rows
- [ ] CI/PR status updates run state
- [ ] At least one milestone notification appears in Discord
- [ ] Logs/live feed/history surfaces show events

## Failure-mode tests
- [ ] Simulated failed run transitions to failed + retry
- [ ] Duplicate dispatch input does not create duplicate active run
- [ ] Restart services and verify state recovery from DB

