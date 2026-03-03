# NOW.md - Current Priorities

_Last updated: 2026-03-03_

## Active Projects
- Mission Control MVP rebuild (Pete page + Agents docs page)
- Pete runtime cutover to dedicated repo
- Clerk reliability and status visibility

## Current Repo Boundaries
- `elevate-flow/agency`: control plane, contracts, registry, clerk, ops docs
- `mission-control-dashboard`: web UI shell/modules
- `pete-engine`: Pete quant logic/runtime/tests

## Agent Status (48h sprint)
- JJ: Operating cadence, cutover checks, daily 9am run verification
- Vlad: Mission Control web rebuild in `mission-control-dashboard`
- Pete: Quant outputs from `pete-engine`
- Baby Vlad: On-demand support only

## Pete Runtime Source Of Truth
- Repo: `https://github.com/cryptolyrics/pete-engine`
- Branch: `codex/pete-engine-hardening` (current migration branch)
- Elevate Flow local Pete scripts are legacy references only.

## Daily 9:00 AM AEST Run (JJ)
```bash
cd /Users/Jax/Documents/GitHub/pete-engine
PETE_ENABLE_WAGERING=1 python3 projects/pete-dfs/scripts/pete-nba-pipeline.py \
  --date "$(TZ=Australia/Brisbane date +%F)" \
  --season "$(TZ=Australia/Brisbane date +%Y)" \
  --tank01-enable \
  --tank01-data-root projects/pete-dfs/data-lake \
  --no-api-sports-fallback
```

## Quick Wins
1. Finalize Mission Control MVP shell in `mission-control-dashboard`.
2. Keep Pete output contract wired to UI with no duplicated logic.
