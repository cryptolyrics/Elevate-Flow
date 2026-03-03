# Pete DFS Project

This is Pete's preserved workstream and optimization track.

## Current Safety State

- Market data in `scripts/pete-nba-pipeline.py` is Tank01-first.
- API-Sports is fallback-only (optional via `--api-sports-fallback`).
- Betting recommendations are fail-closed by default:
  - output is `NO_BET` unless quant rules are enabled and env gating is explicit.

Enable wagering only when both are true:
1. `PETE_ENABLE_WAGERING=1`
2. `projects/pete-dfs/config/quant_rules.json` has `"enabled": true`

Current live baseline in `quant_rules.json`:
- `min_edge_pct: 0.03`
- `min_edge_dollars_per_1u: 0.30`
- `parlay_min_edge_pct: 0.03`
- `parlay_min_edge_dollars_per_1u: 0.10`
- `parlay_min_legs: 2`
- `prop_min_line_edge: 0.20`
- `prop_min_model_edge_pct: 0.02`
- `prop_min_success_rate: 0.55`
- `prop_min_abs_trend: 0.10`
- `prop_relaxed_line_edge_scale: 0.60`
- `prop_relaxed_model_edge_scale: 0.60`

Hard risk filters for wagering:
- home-team model boost configured in quant rules
- back-to-back team filter
- major-out team filter via `projects/pete-dfs/config/major_outs.json`

## Scripts

- `scripts/pete-nba-pipeline.py`
- `scripts/PeteDFS_engine.py`
- `scripts/draftstars_final.py`

`scripts/pete-nba-pipeline.py` Tank01 support:
- Bet of the Day: uses Tank01 moneyline odds as primary feed
- Parlay of the Day: ingests Tank01 player props (+ players mapping) into prop candidate engine
- Date-lag fallback for AU runs via `--tank01-max-lag-days`
- Prop markets scanned: `PTS, REB, AST, STL, BLK, TOV, 3PM, PR, PA, RA, PRA, SB`
- Prop history quality guards:
  - prioritize player-vs-opponent local history when available
  - filter low-minute historical outliers to reduce injury-noise distortion
  - apply spread/total context bias so heavy-favorite high-total games don't default to weak UNDERS
  - fallback to relaxed prop gates when strict gates yield zero candidates (still edge/EV gated)

Learning updates:
- If `pandas` is available, feedback updates are aggregated by player/team/market for more stable learning.
- Fallback is pure-Python updates when pandas is unavailable.
- Optional switch to force fallback: `PETE_DISABLE_PANDAS_LEARNING=1`

`scripts/PeteDFS_engine.py` now emits Mission Control JSON output by default:
- `OPENCLAW_WORKSPACE/logs/Pete/<YYYY-MM-DD>-pete-dfs.json`
- override with `--mission-control-json <path>`
- includes `injury_source_summary`, `h2h_summary`, and per-player `selection_reasons`

DFS engine reliability features:
- Draftstars CSV is injury source-of-truth
- optional ESPN injury sync + CSV merge (`--refresh-espn-injuries`, default off)
- soft penalty for `QUESTIONABLE` players, hard block for `OUT/DOUBTFUL/INACTIVE`
- capped H2H last-5 opponent adjustment from local data-lake (`--data-root`, `--h2h-*`)
- Tank01 integration for all 3 tasks:
  - DFS optimization: name->ID mapping + props projection blend (`--tank01-props-*`)
  - Backtest summary: props vs boxscore files (`--tank01-backtest-days`)
  - Value detection: salary vs prop-implied FP edges in Mission Control payload
  - Live date lag support: auto-fallback to latest prior dated file (`--tank01-max-lag-days`, default 2)
  - Name-matching fallback: canonical team+name match (handles suffix variants like `II/Jr`)

## Fixtures

- `fixtures/sample_games.json`
- `fixtures/sample_odds.json`

## Tests

Run baseline tests:

```bash
python3 -m unittest discover -s projects/pete-dfs/tests -v
```

## Optimization Roadmap

See `OPTIMIZATION-PLAN.md`.

## Daily Calls Contract

See `docs/pete-daily-calls-framework.md`.

Player-prop parlay inputs:
- `--props-json` for the slate props feed
- `--h2h-json` for optional last-five matchup history

## Local Season Data Lake

Use local season storage for speed and reliability:
- Script: `projects/pete-dfs/scripts/sync_nba_season_data.py`
- Daily injuries: `projects/pete-dfs/scripts/sync_espn_injuries.py`
- Ops doc: `docs/pete-local-nba-data-lake.md`
