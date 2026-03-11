# Clerk Operator Contract — V1 Task-State

## Input contract
Clerk accepts `task_packet.v1` JSON packets on the live processing path.

Bridge behavior:
- Clerk attempts `task_packet.v1` first
- falls back to the legacy block packet parser only when input is not valid V1 JSON
- bridge is temporary and should be removed as soon as upstream packet producers are cut over

## Canonical task paths
- `tasks/open/*.json`
- `tasks/closed/*.json`
- `tasks/events/YYYY-MM-DD.jsonl`
- `tasks/rejections/YYYY-MM-DD.jsonl`
- `tasks/index.json`
- `TASKS.md`
- `STATUS.md`

## Truth model
- canonical truth = task records + append-only event history
- `tasks/index.json` = derived acceleration layer only
- `TASKS.md` / `STATUS.md` = rendered visibility only

## Rejection handling
Rejected V1 packets are appended to:
- `tasks/rejections/YYYY-MM-DD.jsonl`

Each rejection should preserve packet/job/run metadata where available.

## Render timing
`TASKS.md` and `STATUS.md` render immediately after each accepted V1 mutation.
