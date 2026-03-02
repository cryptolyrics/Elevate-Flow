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

`scripts/PeteDFS_engine.py` now emits Mission Control JSON output by default:
- `OPENCLAW_WORKSPACE/logs/Pete/<YYYY-MM-DD>-pete-dfs.json`
- override with `--mission-control-json <path>`
- includes `injury_source_summary`, `h2h_summary`, and per-player `selection_reasons`

DFS engine reliability features:
- Draftstars CSV is injury source-of-truth
- optional ESPN injury sync + CSV merge (`--refresh-espn-injuries`, default off)
- soft penalty for `QUESTIONABLE` players, hard block for `OUT/DOUBTFUL/INACTIVE`
- capped H2H last-5 opponent adjustment from local data-lake (`--data-root`, `--h2h-*`)

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
