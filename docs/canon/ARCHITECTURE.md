> CANON ROOT
> This file is part of the active Elevate Flow source of truth.
> Changes here define the operating canon.

# Elevate Flow Canon — ARCHITECTURE

Elevate Flow is the AI factory / operating system running inside **Elevate Studios**.  
This document defines how the factory is structured across planes and repos.

## Top‑Level Structure (Factory Repo)

```text
elevate-flow/
  docs/canon/                # contracts, rules, flow, security
  registry/                  # canonical agent + job registry
  openclaw/templates/        # template notes
  openclaw/generated/        # generated OpenClaw snapshots
  services/clerk-service/    # packet normalization sidecar
  agents/                    # agent identities + SOUL docs
  projects/                  # local project workstreams (legacy only for Pete)
  RUNBOOK.md                 # operator guide
```

```text
external repos/
  mission-control-dashboard/ # web UI shell and module pages
  pete-engine/               # Pete quant logic, tests, and runtime
```

## Plane Separation

- **Execution / Scheduling Plane — OpenClaw**
  - Runs agents and cron jobs.
  - Enforces schedules and runtime configs derived from `registry/`.

- **Normalization Plane — Clerk**
  - Validates packet outputs from agents.
  - Normalizes into canonical workspace files (`TASKS.md`, `STATUS.md`, `logs/*`, `OUTPUTS/`).
  - No LLM calls; purely deterministic.

- **Control Configuration Plane — Registry**
  - Defines agents, jobs, schedules, and workspaces.
  - Drives generation of OpenClaw snapshots in `openclaw/generated/`.

- **Visualization / Ops UI Plane — Mission Control Dashboard**
  - Reads canonical workspaces and Registry state.
  - Renders digests, health views, and job/agent status.
  - Contains **no quant or core business logic**; display only.

- **Quant Compute Plane — Pete Engine**
  - Hosts Pete’s runtime strategies, backtests, and execution engine.
  - Receives structured inputs from Elevate Flow; returns structured outputs.
  - Elevate Flow owns contracts, routing, and guardrails, not implementation.

## Data Flow (High‑Level)

1. OpenClaw cron executes a job according to `registry/`.
2. The job runs an agent with a defined system prompt and context.
3. The agent emits **packet output** (no direct file writes to canon).
4. Clerk validates the packet against the packet contract.
5. Clerk normalizes the packet into canonical workspace files.
6. Mission Control Dashboard and other consumers read canonical files for digests, alerts, and reports.

## Pete Cutover (March 2026)

- Quant runtime moved to external repo:  
  `https://github.com/cryptolyrics/pete-engine`
- Elevate Flow now:
  - Defines Pete’s **contracts** (schemas, expected fields).
  - Calls Pete Engine as an external compute plane.
  - Owns **routing, monitoring, and risk guardrails** for Pete jobs.
- Elevate Flow **must not** implement or modify Pete’s core quant logic here.
- Mission Control UI consumes Pete payloads/contracts only; **no UI‑side quant calculations**.

## Brand Relationship

- **Elevate Studios** owns the broader business, clients, and product portfolio.
- **Elevate Flow** is the dedicated factory/OS used by Elevate Studios to:
  - Coordinate agents (JJ, Vlad, Ali, Pete, Coppa, Coach, subagents).
  - Run packet pipelines.
  - Generate canonical artifacts for reporting and operations.

All new factory features must fit into this architecture or explicitly document why they do not.
