# Pete Local NBA Data Lake

## Why
Keep season data local so Pete's daily calls do not rely on live external fetches.

This improves:
- speed
- reliability
- token efficiency (less context spent on repeated fetch workflows)

## What Is Stored
For each season:
- full schedule index
- raw boxscore payload per game
- raw play-by-play payload per game
- flattened JSONL extracts for quick local parsing
- sync manifest (what is already downloaded)

Path pattern:

`projects/pete-dfs/data-lake/nba/season=YYYY-YY/...`

## Script

[projects/pete-dfs/scripts/sync_nba_season_data.py](/Users/Jax/Documents/Cobault%20Website/elevate-flow/projects/pete-dfs/scripts/sync_nba_season_data.py)

## First Run (Full Season Backfill)

```bash
python3 projects/pete-dfs/scripts/sync_nba_season_data.py \
  --season-start-year 2025
```

## Weekly Tuesday Update (Incremental)

```bash
python3 projects/pete-dfs/scripts/sync_nba_season_data.py \
  --season-start-year 2025 \
  --weekly \
  --lookback-days 10
```

## Granular Play Data
Granular data is stored at per-action level via:
- `raw/playbyplay/<game_id>.json`
- `processed/play_by_play_jsonl/<game_id>.jsonl`

This supports player props analysis for:
- points
- rebounds
- assists
- steals
- three-pointers made

## Tuesday Automation (MacBook cron)

Run every Tuesday at 06:10 local:

```bash
10 6 * * 2 cd /path/to/elevate-flow && /usr/bin/python3 projects/pete-dfs/scripts/sync_nba_season_data.py --season-start-year 2025 --weekly --lookback-days 10 >> logs/pete-data-sync.log 2>&1
```

## Safety Notes
- Daily Pete pipeline should consume local files first.
- Weekly sync is the only external dependency refresh window.
- If Tuesday sync fails, keep existing local cache and retry manually.
