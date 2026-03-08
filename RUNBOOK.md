> LOCAL WORKSPACE MIRROR
> Canonical source lives in ~/.openclaw/workspace-elevate-flow/
> Do not treat this file as the source of truth unless an intentional local deviation is documented.

# Elevate Flow — Runbook

## 1. Purpose

This workspace mirrors the **operational source of truth for Elevate Flow**, the AI factory / OS inside Elevate Studios.

- OpenClaw runs jobs.
- Agents emit packet output.
- Clerk normalizes packet output into canonical workspace files.
- Registry drives job‑to‑agent mapping and generated OpenClaw snapshots.
- Mission Control Dashboard visualises state; it does not run business logic.

## 2. Repository Map (Canon Reference)

See canon root for full details:
- `docs/canon/` — constitutional docs and contracts (AGENTS, ARCHITECTURE, etc.)
- `registry/` — agent/job registry (YAML)
- `openclaw/generated/` — generated OpenClaw snapshots
- `services/clerk-service/` — deterministic normalization service
- `agents/` — agent identity + SOUL docs
- `projects/` — legacy project workstreams

## 3. Prerequisites
- Node.js 20+
- npm 10+
- OpenClaw CLI installed and authenticated locally

## 4. Health & Clerk
Use the same commands as the canon RUNBOOK for install, Clerk config, health checks, and status endpoints. When in doubt, open the canonical RUNBOOK in `workspace-elevate-flow/`.

## 5. Agents at a Glance

Primary agents:
- JJ (main) — COO / orchestration
- Vlad — engineering lead
- Ali — growth & GTM
- Pete — quant lead (Pete Engine operator)
- Coppa — security & compliance
- Coach — Jax’s productivity & performance coach

Subagents:
- Baby Vlad — junior developer under Vlad
- Scout — research/recon under Ali

## 6. Pete & External Engines
This mirror follows the same Pete Engine pattern as canon:
- Pete is a primary agent.
- Runtime logic is in the external Pete Engine repo.
- Elevate Flow handles contracts, routing, monitoring, and guardrails only.

## 7. Escalation
For JJ’s workspace, escalation rules mirror canon:
- Operational ambiguity → JJ.
- Security → Coppa (+ JJ).
- Quant/betting → Pete.
- Human capacity / execution drift → Coach (+ JJ).
