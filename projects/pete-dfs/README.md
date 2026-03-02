# Pete DFS Project

This is Pete's preserved workstream and optimization track.

## Current Safety State

- Data source moved to API-Sports in `scripts/pete-nba-pipeline.py`.
- Betting recommendations are fail-closed by default:
  - output is `NO_BET` unless quant rules are enabled and env gating is explicit.

Enable wagering only when both are true:
1. `PETE_ENABLE_WAGERING=1`
2. `projects/pete-dfs/config/quant_rules.json` has `"enabled": true`

Hard risk filters for wagering:
- home-team model boost configured in quant rules
- back-to-back team filter
- major-out team filter via `projects/pete-dfs/config/major_outs.json`

## Scripts

- `scripts/pete-nba-pipeline.py`
- `scripts/PeteDFS_engine.py`
- `scripts/draftstars_final.py`

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
