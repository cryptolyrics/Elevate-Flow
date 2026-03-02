# Tank01 API Integration Notes

**Date:** 2026-03-03 (Australia) = 2026-03-02 (US)
**Status:** Data retrieved, ready for engine integration

---

## What We Have

### 1. Betting Props (`data-lake/nba/betting-props/2026-03-02.json`)
- **4 games** with player props
- **51 players** with prop lines
- **Props available:** pts, reb, ast, threes, stl, blk, turnover, combos (pts+reb, pts+ast, pts+reb+ast)
- **9 sportsbooks:** DraftKings, FanDuel, BetMGM, Bet365, Caesars, Fanatics, HardRock, ESPNBet, BetRivers

### 2. Player List (`data-lake/nba/players/2026-03-02.json`)
- **1,172 NBA players** with:
  - `playerID` (Tank01 internal ID)
  - `longName`
  - `team` (abbreviation)
  - `teamID`
  - `pos` (position)

---

## API Key

Stored in: `projects/pete-dfs/.env` (add to `.gitignore`)

---

## Working Endpoints

| Endpoint | Status | Notes |
|----------|--------|-------|
| `getNBATeams` | ✅ | Team list |
| `getNBACurrentInfo` | ✅ | Current date info |
| `getNBAPlayerList` | ✅ | All players (1172) |
| `getNBAInjuryList` | ✅ | Injury data |
| `getNBAProjections` | ✅ | 7-day projections |
| `getNBADFS` | ✅ | DFS salaries by platform |
| `getNBABoxScore` | ✅ | Game box scores |
| **`getNBABettingOdds`** | ✅ | Player props + odds |
| `getNBASchedule` | ❌ | Not available |
| `getNBAPlayerGameLogs` | ❌ | Not available |

---

## Data Latency

- **Current API data:** US March 2, 2026
- **Australia (today):** March 3, 2026
- **Status:** API is 1 day behind US date

---

## Integration Ideas for Pete's Engine (All 3 Tasks)

### Task 1: DFS Optimization (Daily Lineup Building)
- Cross-reference Draftstars names → Tank01 player IDs
- Use `getNBAInjuryList` to filter OUT players
- Use `getNBAProjections` as backup projection source

### Task 2: Backtesting (Historical Performance)
- Historical betting props available by date
- Box scores (`getNBABoxScore`) for actual results
- Compare projected vs actual fantasy points

### Task 3: Value Detection (Mispriced Players)
- Compare Draftstars salary vs Tank01 projected FP
- Find players with high props but low salary
- Use over/under lines as confidence gauge

---

## Files Added

```
projects/pete-dfs/data-lake/nba/betting-props/2026-03-02.json
projects/pete-dfs/data-lake/nba/players/2026-03-02.json
```

---

## Next Steps

1. Implemented in `PeteDFS_engine.py`:
   - Load Tank01 player list and map Draftstars names -> `Tank01PlayerID`
   - Load betting props and apply capped secondary projection adjustment
   - Emit value detection edges (salary vs Tank01 prop FP)
   - Emit Tank01 backtest summary (props vs local boxscore files when available)
   - Keep Draftstars CSV as injury source-of-truth

2. Optional follow-up:
   - Add scheduled pulls for `getNBAInjuryList`, `getNBAProjections`, and boxscore snapshots into `data-lake/nba/`

---

*JJ - 2026-03-03*
