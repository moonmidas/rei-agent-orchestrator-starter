# Execute Plan Dispatch Contract

Use this contract to keep orchestration deterministic across Discord channels and threads.

## Channel/Thread routing

1. Read current channel metadata with `message action=channel-info`.
2. Apply parsed `thread_preference` (`auto` | `new` | `current`).

### `thread_preference=auto`

- If channel `type=0` (normal text channel):
  - create a thread via `message action=thread-create`
  - run all execution updates inside that thread
- If channel `type=11` (thread):
  - run in the current thread

### `thread_preference=current`

- Always run in current context.
- Do not create a new thread.

### `thread_preference=new`

- Always create a new work thread.
- If current channel is `type=0`, create thread from request message.
- If current channel is `type=11`, create a **sibling thread** in the parent channel:
  1) send a bootstrap message to parent channel (`message action=send`)
  2) call `message action=thread-create` using that parent message id
  3) continue execution in the new sibling thread

## Dispatch requirements

Before saying a run started:

1. Parse command with `scripts/parse_execute_plan.js`.
2. Resolve target agent(s):
   - explicit `agent` or `agents` wins
   - fallback: coding/engineering plans -> `chad`, copy/content plans -> `halbert`
3. Dispatch using `sessions_spawn` with `runtime:"subagent"` and explicit `agentId`.

## Mandatory receipt semantics

- Success message must include:
  - `DISPATCH_OK`
  - execution context (`new thread` / `current thread`)
  - agent id(s)
  - `childSessionKey` per dispatch
- Failure message must include:
  - `DISPATCH_BLOCKED`
  - exact blocking reason
  - next action

Never send progress claims before a valid dispatch receipt exists.

## Sequential behavior

Default sequence:

1. break plan into tasks
2. execute first task
3. verify task gate
4. report evidence
5. move to next task

For `mode=approval_gated`, pause after each task and wait for “continue”.
