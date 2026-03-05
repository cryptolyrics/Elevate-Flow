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

## NBA Data Timing Rule 🇦🇺→🇺🇸

**Australia (AEST/AEDT) is always one day ahead of the US NBA schedule.**

- NBA games are played in the US on date X (e.g., March 6)
- In Australia, it's already date X+1 (March 7)
- Tank01/Draftstars data for "tonight's" games is available the **previous day** in AU time

**Operational Law:**
- Run DFS data collection on the **day before** the NBA date you want to bet
- Example: For March 6 NBA games, pull data on March 5 AU time
- The cron job should run at ~8-9am AU time on the day prior to capture evening US games

## Sync Protocol

Run `scripts/sync.sh` to sync local state with canon:

```bash
./scripts/sync.sh
```

This fetches latest, resets to origin/main, and updates submodules.
