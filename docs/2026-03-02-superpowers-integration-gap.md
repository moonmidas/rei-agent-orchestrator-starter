# 2026-03-02 Superpowers integration gap

## Current status
This starter installs orchestrator baseline only.

Integrated now:
- OpenClaw gateway + systemd supervision
- Rei/Chad/Halbert roster template
- execute-plan skill installed to workspace

Missing:
- superpowers repo clone
- superpowers tool wrappers in orchestrator prompts/skills
- deterministic CI/review automation loop from superpowers patterns
- sqlite run/task board (legacy-profile layer)

## Fastest integration path
1. Add `scripts/install-superpowers.sh` to clone `obra/superpowers` into `/opt/superpowers`.
2. Add optional config flag `ENABLE_SUPERPOWERS=true` in installer.
3. Add execute-plan extension docs showing when to invoke superpowers scripts.
4. Add orchestrator template snippets for superpowers command contracts.
5. Add doctor check verifying superpowers binaries/scripts are reachable.
