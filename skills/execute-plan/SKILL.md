---
name: execute-plan
description: Deterministic Discord command workflow for `/execute-plan`, `/xp`, `/xp-safe`, `/xp-fast`, and `/xp-ship`. Use when Esteban asks to execute a multi-step plan in any Discord channel/thread and wants standardized routing, Chad/Halbert dispatch, verification gates, and explicit dispatch receipts.
---

# Execute Plan

Run plan orchestration through a strict contract so behavior is consistent across channels.

## Command forms

Treat these as equivalent triggers:

- `/execute-plan ...`
- `/skill execute-plan ...`
- `/xp ...`
- `/xp-safe ...`
- `/xp-fast ...`
- `/xp-ship ...`
- `execute plan: ...`
- `xp: ...`

## Step 1 — Parse command deterministically

Run:

```bash
node /home/clawdbot/.openclaw/workspace/skills/execute-plan/scripts/parse_execute_plan.js --text "<raw user message>"
```

Parser accepts both full triggers (`/execute-plan`, `/xp*`) and direct `/skill execute-plan` input blocks.

Use parser output as source of truth for:

- plan
- mode
- execution
- task_granularity
- verification_gate
- commit_strategy
- reporting_cadence
- stop_conditions
- definition_of_done
- thread_preference (`auto` | `new` | `current`)
- agents

If parser returns `requires_clarification=true`, ask one focused question and stop.

## Step 2 — Resolve execution context (channel vs thread)

Follow `references/dispatch-contract.md`.

Use `thread_preference` from parser:

- `auto` (default):
  - if current channel is `type=0`, create a thread and run there
  - if current channel is `type=11`, run in place
- `new`:
  - always create a new work thread (if currently in a thread, create a sibling thread in the parent channel)
- `current`:
  - run in the current context; do not create a new thread

Thread control input examples:

- `thread: new`
- `thread: current`
- `thread=auto`

## Step 3 — Dispatch agents

Use explicit agents when provided (`agent` / `agents`).

Fallback routing:

- engineering/coding/system implementation -> `chad`
- copywriting/marketing/content -> `halbert`

Dispatch with `sessions_spawn` using:

- `runtime: "subagent"`
- explicit `agentId`
- clear task payload including parsed plan settings

For multi-agent requests:

- if execution is `allow_parallel`, dispatch independent tasks in parallel
- else dispatch sequentially

## Step 4 — Enforce receipt semantics

Never claim “started” until `sessions_spawn` returns `childSessionKey`.

On success, first status line must include:

- `DISPATCH_OK`
- execution context (`new thread` or `current thread`)
- agent id(s)
- `childSessionKey` (per agent)

On failure, first status line must include:

- `DISPATCH_BLOCKED`
- exact reason
- next action

## Step 5 — Execute task cadence

Default sequence:

1. decompose plan
2. execute first task
3. run verification gate for that task
4. report evidence
5. continue to next task

If `mode=approval_gated`, pause after each task and wait for “continue”.

## Guardrails

- Do not route to ACP harness unless user explicitly requests codex/claude/gemini harness flow.
- Do not skip verification gates.
- Do not post false-positive progress updates.
- Keep updates short and evidence-based.
