# Pete Daily Calls Framework (NBA)

## Scope
Pete runs three daily NBA calls:

1. Draftstars DFS lineup + smokies
2. Best Bet of the Day (head-to-head or handicap)
3. Parlay of the Day (player props multi)

This framework codifies inputs, constraints, and learning updates so quality improves over time.

## Call 1: Draftstars DFS Lineup + Smokies

## Input
- Daily Draftstars player CSV (typically around 9:00am).
- Optional slot targeting: `early`, `late`, or `all`.

## Required Output
- Valid 9-player lineup with format `2 PG, 2 SG, 2 SF, 2 PF, 1 C`.
- Salary cap compliance (`<= 100000`).
- Top smokie candidates:
  - lower-salary players expected to outperform their baseline
  - ranked by projection delta + value score

## Current Model Behavior
- Filters out ineligible statuses (`OUT`, `QUESTIONABLE`).
- Projects player output from weighted form/FPPG + learned player adjustment.
- Optimizes lineup using constrained slot-based search.
- Emits smokies in report and pivot notes.

## Call 2: Best Bet of the Day

## Input
- API-Sports games + odds feed.
- Optional major-out teams JSON.

## Required Output
- One `NO_BET` or one best pick with edge and EV metrics.

## Hard Rules
- Home teams get +10% model boost vs implied baseline.
- No bets on teams playing back-to-back (B2B filter).
- No bets on games where either team has major player outs (major-out filter).
- Minimum edge gates must pass:
  - probability edge threshold
- expected return threshold (`edge_dollars_per_1u`)

## Call 3: Parlay of the Day (Player Props)

## Inputs
- Player props payload (`--props-json`) covering full day slate.
- Optional matchup history payload (`--h2h-json`) with last five meetings.
- Optional Draftstars CSV projection map to reinforce player confidence.

Example props payload:

```json
{
  "games": [
    {
      "home": "Nuggets",
      "away": "Lakers",
      "props": [
        {
          "player": "J Murray",
          "team": "Nuggets",
          "opponent": "Lakers",
          "market": "3PM",
          "line": 2.5,
          "odds_over": 1.95,
          "odds_under": 1.85,
          "last5_vs_opp": [4, 3, 3, 5, 4]
        }
      ]
    }
  ]
}
```

Example optional `--h2h-json` payload:

```json
{
  "matchups": [
    {
      "player": "J Murray",
      "team": "Nuggets",
      "opponent": "Lakers",
      "market": "3PM",
      "values": [4, 3, 3, 5, 4]
    }
  ]
}
```

## Supported Prop Markets
- `PTS`, `REB`, `AST`, `STL`, `3PM`

## Required Logic
- Cross-reference each prop with last five meetings for that matchup.
- Keep only candidates with clear success/progression:
  - matchup hit-rate and/or trend signal
- Apply safety haircut: reduce projected call by at least 10%.
  - Example: projected 3.0 threes -> safe call 2.
- Build top multi from edge-qualified legs only.

## Risk and Safety
- Uses quant gates plus probability edge checks.
- Rejects weak/noisy candidates.
- Returns `NO_PROP_PARLAY` when edge criteria are not met.

## Learning Engine

## State
- File-backed JSON state:
  - `player_adjustments`
  - `team_adjustments`
  - `meta` sample counters

## Feedback Loop
- Optional feedback JSON updates model:
  - DFS samples adjust player projections
  - Bet samples adjust team calibration
- State is persisted each run for incremental improvement.

## Runtime Commands

Dry run:

```bash
python3 pete-nba-pipeline.py --dry-run --date 2026-03-02 --season 2026
```

Run with DFS CSV:

```bash
python3 PeteDFS_engine.py \
  --date 2026-03-02 \
  /path/to/draftstars.csv \
  --lookback-days 10 \
  --slot early \
  --mission-control-json .pete-workspace/logs/Pete/2026-03-02-pete-dfs.json
```

Run full daily report pipeline:

```bash
python3 pete-nba-pipeline.py \
  --date 2026-03-02 \
  --season 2026 \
  --draftstars-csv /path/to/draftstars.csv \
  --slot early
```

Run with learning feedback + major-outs:

```bash
python3 pete-nba-pipeline.py \
  --date 2026-03-02 \
  --season 2026 \
  --draftstars-csv /path/to/draftstars.csv \
  --feedback-json /path/to/pete-feedback.json \
  --major-outs-json /path/to/major_outs.json
```

Run with player props and matchup history:

```bash
python3 pete-nba-pipeline.py \
  --date 2026-03-02 \
  --season 2026 \
  --props-json /path/to/props.json \
  --h2h-json /path/to/h2h-last5.json
```

Run with ESPN injuries feed:

```bash
python3 pete-nba-pipeline.py \
  --date 2026-03-02 \
  --season 2026 \
  --espn-injuries-json projects/pete-dfs/data-lake/nba/injuries/latest.json
```

## Config Files
- Quant rules: `projects/pete-dfs/config/quant_rules.json`
- Major outs: `projects/pete-dfs/config/major_outs.json`
- ESPN injuries: `projects/pete-dfs/data-lake/nba/injuries/latest.json`

## Notes
- Wagering remains fail-closed unless both are set:
  - `PETE_ENABLE_WAGERING=1`
  - quant rules file has `"enabled": true`
