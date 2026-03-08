> CANON ROOT
> This file is part of the active Elevate Flow source of truth.
> Changes here define the operating canon.

# Elevate Flow — Runbook

## 1. Purpose

This repository is the **operational source of truth for Elevate Flow**, the AI factory / OS inside Elevate Studios.

- OpenClaw runs jobs.
- Agents emit packet output.
- Clerk normalizes packet output into canonical workspace files.
- Registry drives job‑to‑agent mapping and generated OpenClaw snapshots.
- Mission Control Dashboard visualises state; it does not run business logic.

Mission Control UI is out of scope for v1 of this runbook (it is an external repo).

## 2. Repository Map

- `docs/canon/` — constitutional docs and contracts (AGENTS, ARCHITECTURE, etc.)
- `registry/` — canonical agent/job registry (YAML)
- `openclaw/generated/` — generated OpenClaw snapshots from registry
- `services/clerk-service/` — deterministic normalization service
- `agents/` — agent identity and role docs (IDENTITY + SOUL)
- `projects/` — legacy project workstreams (Pete optimization, etc.)
- `RUNBOOK.md` — this operator guide

## 3. Prerequisites

- Node.js 20+
- npm 10+
- OpenClaw CLI installed and authenticated locally

## 4. Install

From repo root:

```bash
npm install
npm run validate:registry
```

For Clerk service:

```bash
cd services/clerk-service
npm install
npm run build
npm test
```

## 5. Configure Clerk

Edit `services/clerk-service/config.json`:

- `workspaceRoot` — root containing agent workspaces
- `reportWorkspace` — where `.clerk/*` outputs are stored
- `jobs` — map each job to `agentId` + `workspace`
- `host` — must remain `127.0.0.1`
- `port` — local port for health/status endpoints

Set auth key:

```bash
export MC_API_KEY="your-local-mc-key"
```

## 6. Run Clerk

```bash
cd services/clerk-service
MC_API_KEY="your-local-mc-key" npm start
```

Health check:

```bash
curl http://127.0.0.1:3008/health
```

Protected status check:

```bash
curl -H "X-MC-KEY: your-local-mc-key" http://127.0.0.1:3008/v1/status
```

## 7. Validate System Health (Daily)

1. `npm run validate:registry` passes.
2. Clerk `/health` returns `ok: true`.
3. Clerk `/v1/status` shows recent `lastPollAt`.
4. No unexplained files in `.clerk/dead-letter/`.
5. Agent workspaces contain expected canonical writes:
   - `STATUS.md`
   - `logs/YYYY-MM-DD.jsonl`
   - `OUTPUTS/*`
6. OpenClaw session store is pruned regularly:
   - `npm run sessions:prune:dry`
   - `npm run sessions:prune` (when stale sessions are present)
7. Telegram / chat reporting stays compact (digests first, no full transcript spam).

## 8. Onboard a New Agent

1. Define agent in `registry/agents.yml`.
2. Define one or more jobs in `registry/jobs.yml`.
3. Run:
   ```bash
   npm run generate:openclaw
   npm run validate:registry
   ```
4. Update OpenClaw config from `openclaw/generated/*` snapshots.
5. Add/update agent identity docs in `agents/<Name>/IDENTITY.md` and `agents/<Name>/SOUL.md`.
6. Add Clerk job mapping in `services/clerk-service/config.json`.
7. Dry‑run a job and verify packet contract compliance.

## 9. Pete & External Engines

- Pete is a **primary factory agent** whose runtime logic lives in the external **Pete Engine** repo.
- Elevate Flow:
  - Schedules Pete jobs via OpenClaw.
  - Sends structured payloads to Pete Engine.
  - Receives structured outputs and normalizes them via Clerk.
  - Owns monitoring, alerts, and risk guardrails.
- Do **not** implement or modify core quant logic for Pete inside this repo.

## 10. Operating Rules (Factory)

- Do not write secrets to Git.
- Do not bypass packet parser checks.
- Do not hand‑edit generated OpenClaw snapshots.
- Keep OpenClaw as the scheduler; Clerk is normalization only.
- Respect Coppa’s security vetoes.

## 11. Agents at a Glance

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

See `AGENTS.md` and `docs/canon/AGENTS.md` for full hierarchy and rules.

## 12. Token & Cost Controls

- SOP: `sops/token-efficiency.md`
- Session pruning script: `scripts/prune-openclaw-sessions.mjs`
- npm helpers:
  - `npm run sessions:prune:dry`
  - `npm run sessions:prune`

## 13. Escalation

- Operational ambiguity → escalate to JJ.
- Security or secrets risk → escalate to Coppa (and JJ where needed).
- Quant or betting risk → escalate to Pete.
- Human capacity / execution drift → escalate to Coach and JJ.
