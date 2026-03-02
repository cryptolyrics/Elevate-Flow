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

## API Key (for reference)
```
Host: tank01-fantasy-stats.p.rapidapi.com
Key: 4e79ce67e3msh078608159eb2c89p1c42c5jsn587bb0769f45
```

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

## Integration Ideas for Pete's Engine

### 1. Cross-Reference Player IDs
- Match Draftstars player names → Tank01 player IDs
- Use for injury cross-checking and prop data lookup

### 2. Value Detection
- Compare Draftstars salary vs projected fantasy points from Tank01
- Find mispriced players (high projection, low salary)

### 3. Prop-Based Adjustments
- Use prop lines as confidence indicators
- If a player's pts line is 25+, they're expected to play big minutes
- Use over/under to gauge upside

### 4. Injury Overlay
- `getNBAInjuryList` returns 64 players with:
  - `designation` (Out, Day-To-Day)
  - `injDate`, `injReturnDate`
  - `description`

### 5. Projections Backup
- `getNBAProjections` as secondary projection source if Draftstars FPPG is stale

---

## Files Added

```
projects/pete-dfs/data-lake/nba/betting-props/2026-03-02.json
projects/pete-dfs/data-lake/nba/players/2026-03-02.json
```

---

## Next Steps

1. CodeX to build logic into PeteDFS_engine.py:
   - Load Tank01 player list
   - Match Draftstars CSV → Tank01 IDs
   - Load betting props for today's games
   - Calculate value scores (projected FP / salary)
   - Filter by injury status

2. Re-run optimizer with Tank01 data as secondary signal

---

*JJ - 2026-03-03*
