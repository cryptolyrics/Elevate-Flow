# Elevate Flow Canon - AGENTS

This document is the constitutional source for how Elevate Flow operates.

Mission and active operating priorities are defined in `ELEVATE-MISSION-CONTROL.md`.

## Scope Hierarchy
- This canon controls framework architecture, contracts, and non-negotiable controls.
- `ELEVATE-MISSION-CONTROL.md` controls mission target, active roster, and phase priorities.
- Mission Control cannot override canon security or contract requirements.

## Architecture Planes

### Compute Plane
- OpenClaw agents run scheduled jobs.
- Agents emit packet-only output.
- Agents do not directly write canonical workspace files.

### Control Plane
- OpenClaw gateway handles scheduling and execution.
- Clerk service normalizes packet outputs into canonical files.
- Registry maps job, agent, workspace, schedule, and runtime target.

## Non-Negotiables

1. Git is source of truth for framework and contracts.
2. Registry is the source of truth for jobs and agent mappings.
3. Packet contract is strict and versioned.
4. Clerk performs deterministic normalization only (no LLM calls).
5. Status/state writes are atomic.
6. Logs are append-only by date.
7. Artifact writes are sandbox-validated.
8. Services bind to `127.0.0.1`.
9. Protected endpoints require `X-MC-KEY`.
10. No secrets in commits, logs, or packets.
11. Elevate Flow agents have no access to local drives on Jax machines.
12. Agent handoffs must use Git/API/message payloads only (no local-path assumptions).

## Canonical Workspace Model

Each workspace normalized by Clerk contains:
- `TASKS.md`
- `STATUS.md`
- `logs/YYYY-MM-DD.jsonl`
- `OUTPUTS/`
- optional `CONTEXT.md`, `IDENTITY.md`, `SOUL.md`

## Agent Escalation Cadence (Vlad + Baby Vlad)

- Both agents must complete assigned/scheduled tasks before taking new work.
- If blocked, unclear, or waiting on decisions, they must ask JJ for next steps.
- They must re-check with JJ every 2 hours until the task is completed.
