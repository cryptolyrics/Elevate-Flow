# 2026-03-02 Token Efficiency Controls

## Decisions
- Added built-in OpenClaw session hygiene controls to prevent stale-session token bloat.
- Added explicit Telegram communication constraints to reduce context replay waste.

## Actions
- Added `scripts/prune-openclaw-sessions.mjs` with:
  - dry-run mode (default)
  - apply mode with automatic backup
  - keep-key support (defaults to `agent:main:main`)
  - stale-age and max-session limits
- Added npm commands:
  - `npm run sessions:prune:dry`
  - `npm run sessions:prune`
- Added SOP: `sops/token-efficiency.md`.
- Updated:
  - `RUNBOOK.md` daily checks + token controls section
  - `TEAM-KICKOFF.md` operator checklist

## Outcomes
- Session pruning is now a repeatable operational control, not an ad hoc fix.
- Telegram bloat mitigation rules are codified for JJ/Vlad operations.
