# Pete Daily Calls Framework (NBA)

## Scope
Pete runs two daily NBA calls:

1. Draftstars DFS lineup + smokies
2. Best Bet of the Day (head-to-head or handicap)

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

## Config Files
- Quant rules: `projects/pete-dfs/config/quant_rules.json`
- Major outs: `projects/pete-dfs/config/major_outs.json`

## Notes
- Wagering remains fail-closed unless both are set:
  - `PETE_ENABLE_WAGERING=1`
  - quant rules file has `"enabled": true`
