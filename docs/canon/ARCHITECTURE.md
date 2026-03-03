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
  projects/                  # local project workstreams (legacy only for Pete)
  RUNBOOK.md                 # operator guide
```

```text
external repos/
  mission-control-dashboard/ # web UI shell and module pages
  pete-engine/               # Pete quant logic, tests, and runtime
```

## Plane Separation

- OpenClaw: execution and scheduling plane.
- Clerk: deterministic normalization plane.
- Registry: control configuration plane.
- Mission Control: visualization and operations UI plane (`mission-control-dashboard`).
- Pete Engine: quant compute plane (`pete-engine`).

## Data Flow

1. OpenClaw cron runs an agent job.
2. Agent emits packet output.
3. Clerk validates packet and normalizes writes.
4. Canonical workspace files drive digest/health/reporting.

## Pete Cutover (March 2026)

- Pete source of truth moved to: `https://github.com/cryptolyrics/pete-engine`
- Elevate Flow keeps Pete contracts/docs only; do not modify Pete runtime logic here.
- Mission Control UI consumes Pete payload/contracts; no UI-side quant calculations.
