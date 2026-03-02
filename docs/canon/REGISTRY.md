# Elevate Flow Canon - REGISTRY

Registry files are the single source of truth.

## Files

- `registry/agents.yml`
- `registry/jobs.yml`

## Required Mapping

Each job maps:
- `job_id`
- `agent_id`
- `workspace`
- `schedule` (`cron` + `timezone`)
- `runtime.target` (`isolated` or `main`)

## Invariants

1. `agent_id` in jobs must exist in agents.
2. `workspace` in job must match the agent workspace.
3. `job_id` is unique.
4. Generated OpenClaw snapshots must match registry.
