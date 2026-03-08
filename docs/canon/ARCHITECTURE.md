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

### USA Timezone Implementation in Pete's Code

Pete's pipeline (`pete-nba-pipeline.py`) now uses **USA Eastern Time** as the reference for all NBA data:

1. **Automatic USA Date Calculation:**
   - The `get_usa_date()` function converts local AU time to USA Eastern Time
   - Uses `zoneinfo.ZoneInfo("America/New_York")` when available (Python 3.9+)
   - Falls back to manual calculation (~14 hours behind AU time)

2. **Data File Naming:**
   - All Tank01 API calls use USA date (e.g., `2026-03-05.json`)
   - Data files are saved with USA date in filename
   - Example: If it's March 6 in Australia, files are named `2026-03-05.json` (USA date)

3. **API Calls:**
   - Tank01 API `gameDate` parameter uses USA date
   - All date-dependent operations default to USA date
   - `--date` argument accepts USA date in YYYY-MM-DD format

4. **Why This Matters:**
   - NBA games are scheduled in US time zone
   - "Tonight's" games in the US correspond to tomorrow in Australia
   - Running data collection with AU date would fetch wrong day's games
   - Using USA date ensures we always get the correct NBA schedule

## Sync Protocol

Run `scripts/sync.sh` to sync local state with canon:

```bash
./scripts/sync.sh
```

This fetches latest, resets to origin/main, and updates submodules.
