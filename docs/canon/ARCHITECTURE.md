# Elevate Flow Canon - ARCHITECTURE

## Top-Level Structure

```text
elevate-flow/
  docs/canon/                # contracts, rules, flow, security
  registry/                  # canonical agent + job registry
  openclaw/templates/        # template notes
  openclaw/generated/        # generated OpenClaw snapshots
  services/clerk-service/    # packet normalization sidecar
  agents/                    # existing agent identities/profiles
  projects/                  # project workstreams (Pete optimization)
  RUNBOOK.md                 # operator guide
```

## Plane Separation

- OpenClaw: execution and scheduling plane.
- Clerk: deterministic normalization plane.
- Registry: control configuration plane.
- Mission Control (future): visualization and operations UI plane.

## Data Flow

1. OpenClaw cron runs an agent job.
2. Agent emits packet output.
3. Clerk validates packet and normalizes writes.
4. Canonical workspace files drive digest/health/reporting.
