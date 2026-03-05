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

- `main` branch on all repos = source of truth
- Agent workspaces are local copies/pointers
- Submodules track specific commits from agent repos

## Agent Repos (Submodules)

| Submodule | Repo URL | Purpose |
|-----------|----------|---------|
| agents/pete-engine | github.com/cryptolyrics/pete-engine | DFS optimization |
| agents/ali_growth_engine | github.com/cryptolyrics/ali_growth_engine | Growth operations |

## Sync Protocol

Run `scripts/sync.sh` to sync local state with canon:

```bash
./scripts/sync.sh
```

This fetches latest, resets to origin/main, and updates submodules.
