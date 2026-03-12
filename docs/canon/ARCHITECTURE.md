# Elevate Flow Architecture

## Infrastructure

- **Mission Control API:** localhost:3008 (loopback only)
- **Gateway:** localhost:18789 (loopback only)
- **Clerk:** localhost:3008 (loopback only)
- **Cloudflare Tunnel:** Exposes ONLY Mission Control hostname

## Authentication

- Auth header required for protected endpoints: `X-MC-KEY`
- No public API exposure (loopback only)

## Git Strategy

> **"Git main is canon. Workspaces are pointers only."**

- `main` branch on canon repos = source of truth
- Agent workspaces are local execution mirrors
- External runtimes and service layers must follow explicit repo boundaries

## External Runtime Repos

| Runtime | Repo URL | Purpose |
|---------|----------|---------|
| Pete Engine | github.com/cryptolyrics/pete-engine | Quant runtime and wagering logic |
| Ali Growth Engine | github.com/cryptolyrics/ali_growth_engine | Growth operations |

## Factory Control-Plane Boundary

Elevate Flow keeps the factory operating layer:
- canon docs and contracts
- agent definitions
- Clerk and task-state normalization
- routing, monitoring, and guardrails

Elevate Flow does not own Pete runtime execution logic.
That remains external to the control-plane repo.

## Task-State Model

Canonical task truth lives under:
- `tasks/open/*.json`
- `tasks/closed/*.json`
- `tasks/events/YYYY-MM-DD.jsonl`
- `tasks/index.json`

Rendered visibility layers:
- `TASKS.md`
- `STATUS.md`

Rendered markdown is visibility only, not source of truth.

## Pete Timing Note

Australia is typically ahead of US market time, so Pete runtime date handling should follow the active external Pete Engine runtime rules, not local mirror assumptions.

## Sync Protocol

Run `scripts/sync.sh` to sync local state with canon when that script is still part of the active workspace contract.
