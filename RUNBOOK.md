# Elevate Flow Runbook

## 1. Purpose

This repository is the operational source of truth for Elevate Flow.

- OpenClaw runs jobs.
- Agents emit packet output.
- Clerk normalizes packet output into canonical workspace files.
- Registry drives job-to-agent mapping and generated OpenClaw snapshots.

Mission Control UI is out of scope for v1.

## 2. Repository Map

- `docs/canon/`: constitutional docs and contracts
- `registry/`: canonical agent/job registry (YAML)
- `openclaw/generated/`: generated snapshots from registry
- `services/clerk-service/`: deterministic normalization service
- `agents/`: existing agent identity and role docs
- `projects/`: project-specific pipelines (Pete optimization phase goes here)

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

For clerk-service:

```bash
cd services/clerk-service
npm install
npm run build
npm test
```

## 5. Configure Clerk

Edit `services/clerk-service/config.json`:

- `workspaceRoot`: root containing agent workspaces
- `reportWorkspace`: where `.clerk/*` outputs are stored
- `jobs`: map each job to `agentId` + `workspace`
- `host`: must remain `127.0.0.1`
- `port`: local port for health/status endpoints

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

## 7. Validate System Health

Daily checks:

1. `npm run validate:registry` passes.
2. Clerk `/health` returns `ok: true`.
3. Clerk `/v1/status` shows recent `lastPollAt`.
4. No unexplained files in `.clerk/dead-letter/`.
5. Agent workspaces contain expected canonical writes:
   - `STATUS.md`
   - `logs/YYYY-MM-DD.jsonl`
   - `OUTPUTS/*`
6. OpenClaw session store is pruned:
   - `npm run sessions:prune:dry`
   - `npm run sessions:prune` (when stale sessions are present)
7. Telegram reporting stays compact (no transcript replay, digest-first updates).

## 8. Onboard a New Agent

1. Add agent in `registry/agents.yml`.
2. Add one or more jobs in `registry/jobs.yml`.
3. Run:
   ```bash
   npm run generate:openclaw
   npm run validate:registry
   ```
4. Update OpenClaw config from `openclaw/generated/*` snapshots.
5. Add/update agent identity docs in `agents/<Name>/`.
6. Add Clerk job mapping in `services/clerk-service/config.json`.
7. Verify packet contract compliance with a dry run.

## 9. Operating Rules

- Do not write secrets to Git.
- Do not bypass packet parser checks.
- Do not hand-edit generated OpenClaw snapshots.
- Keep OpenClaw as the scheduler; Clerk is normalization only.

## 10. Pete Workstream

Current Pete scripts are preserved in place for continuity.
Optimization should be done as a dedicated phase with:

1. Baseline fixtures/tests
2. Profiling and API-call budgeting
3. Controlled algorithm refactors

## 11. Daily Handoff Contract

JJ daily reporting and review handoff are defined in:

- `docs/canon/HANDOFF-CONTRACT.md`
- `reports/daily/README.md`
- `reports/daily/templates/`

## 12. Token Efficiency Controls

- SOP: `sops/token-efficiency.md`
- OpenClaw session pruner script: `scripts/prune-openclaw-sessions.mjs`
- npm helpers:
  - `npm run sessions:prune:dry`
  - `npm run sessions:prune`
