> CANON ROOT
> This file is part of the active Elevate Flow source of truth.
> Changes here define the operating canon.

# SYSTEM_CANON.md — Elevate Flow

## Purpose
Elevate Flow is the AI factory / operating system inside **Elevate Studios**. This document is the top‑level index for the factory’s operating canon: who runs it, where truth lives, and how agents are expected to behave.

## Canon root
- The single source of truth for Elevate Flow canon is:
  - `~/.openclaw/workspace-elevate-flow/`
- Canonical files:
  - `AGENTS.md` — factory mission, rules, primary agents, cadence
  - `AGENT-PROFILES.md` — canonical agent model + system configs
  - `RUNBOOK.md` — operator guide for running Elevate Flow
  - `docs/canon/AGENTS.md` — constitutional AGENTS canon
  - `docs/canon/ARCHITECTURE.md` — architecture and plane separation
  - `SYSTEM_CANON.md` — this index
  - `REPO_OWNERSHIP.md` — repo + plane ownership
  - `agents/<Name>/{IDENTITY.md,SOUL.md}` — per‑agent identity canon

Everything else (mirrors, legacy, derived copies) must point back to these files.

## Brand hierarchy
- **Elevate Studios** — umbrella brand / company.
- **Elevate Flow** — the AI factory + operating system **inside** Elevate Studios:
  - Runs agents, packet pipelines, and factory rituals.
  - Exists to hit the factory mission (currently: $3k/month net profit).

Branding rules:
- Use **“Elevate Flow”** for factory‑specific docs and operations.
- Use **“Elevate Studios”** when referring to the broader umbrella, clients, or studio‑wide strategy.

## Source‑of‑truth policy
- Canon lives only under `workspace-elevate-flow/` in the files listed above.
- Other locations are one of:
  - **LOCAL WORKSPACE MIRROR** — runtime convenience only.
  - **DERIVED COPY** — generated from canon; do not hand‑edit.
  - **LEGACY REFERENCE ONLY** — historical; not authoritative.
  - **ARCHIVE / HISTORICAL SNAPSHOT** — frozen past state.
- When canon and any mirror conflict, **canon wins**.

## Agent hierarchy

### Primary persistent agents
- **JJ (main)** — COO and orchestration lead
  - JJ **is** the `main` runtime identity; `main` is not a separate persona.
  - Owns orchestration, prioritisation, delegation, escalation, and operational clarity across the factory.
- **Vlad** — engineering lead reporting into JJ
  - Owns architecture, code, automation, infra, deployments, and implementation.
- **Pete** — quant lead (Pete Engine operator)
  - Owns wagering/quant strategy, risk, and contracts with the external Pete Engine runtime.
- **Ali** — growth & GTM lead
  - Owns offers, funnels, experiments, and paid acquisition.
- **Coppa** — security & compliance lead
  - Owns security posture, allowlists, incident response, and vetoes on unsafe changes.
- **Coach** — Jax’s productivity & performance coach
  - ADHD‑aware. Owns plans, routines, accountability, and execution support for Jax.

### Subagents
- **Baby Vlad** — subagent under Vlad
  - Junior developer on scoped, low‑risk implementation work.
  - Does **not** redesign architecture or touch high‑risk paths without escalation.
- **Scout** — subagent under Ali
  - Recon + research support: market scanning, competitor intel, opportunity discovery.
  - Does **not** own growth strategy or offers; Ali does.

### Pete scope
- Pete remains a **primary factory agent** in canon.
- Pete’s runtime / engine logic lives in the external **Pete Engine** repo.
- Elevate Flow owns:
  - Pete’s role and responsibilities.
  - Contracts and schemas for packets to/from Pete Engine.
  - Routing configuration and scheduling for Pete jobs.
  - Monitoring, reporting, and risk/guardrail expectations.
- Elevate Flow **does not** implement or modify Pete’s quant logic here.

### Coach scope
- Coach is a **primary agent** focused on Jax as a human system:
  - ADHD‑aware planning, realistic scopes, and recovery from drift.
  - Accountability, energy, routines, fitness, and goal progress.
- Coach explicitly **does not**:
  - Replace JJ as COO.
  - Act as therapist or clinician.
  - Replace specialist agents (Vlad, Ali, Pete, Coppa).

## Workspace vs canon policy
- Canon root: `workspace-elevate-flow/`.
- Per‑agent workspaces (e.g. `workspace-vlad/`, `workspace-ali/`, `workspace-coach/`) are **execution mirrors**, not canon.
- Rules:
  - Mirrors must either carry a LOCAL WORKSPACE MIRROR header or be clearly derived from canon.
  - Behavioural or mission changes must land in canon root first, then propagate outward.

## Artifacts and archives
- `workspace-*.ARCHIVE.*` directories under `~/.openclaw/` are **archive snapshots**.
  - They are never treated as live canon.
  - Use them only to salvage examples or prior context.
- `~/elevate-flow-jj/` and its docs are **legacy/reference only**.
  - Elevate Flow canon has moved into `workspace-elevate-flow/`.

## Open questions
The following require explicit human decisions in later phases:
- Final model matrix per agent (MiniMax vs OpenAI models in production).
- Long‑term mission target after the $3k/month baseline is hit.
- Additional planes or repos (new products like SwapBot) and how tightly they couple to Elevate Flow vs Elevate Studios more broadly.
