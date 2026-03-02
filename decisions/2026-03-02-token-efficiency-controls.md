# Decision Log - 2026-03-02 (Token Efficiency Controls)

## Decision
Add first-class token-efficiency controls to the framework by automating OpenClaw session pruning and codifying Telegram communication limits.

## Why
- OpenClaw stale cron sessions accumulate context and inflate token usage.
- Telegram transcript-heavy updates increase unnecessary model context consumption.

## What Changed
- Added script: `scripts/prune-openclaw-sessions.mjs`.
- Added npm commands:
  - `sessions:prune:dry`
  - `sessions:prune`
- Added SOP: `sops/token-efficiency.md`.
- Updated operational docs (`RUNBOOK.md`, `TEAM-KICKOFF.md`) to include token hygiene checks.

## Expected Outcome
- Stable low-session posture (`agent:main:main` plus minimal active sessions).
- Reduced token spend from stale context and redundant Telegram chatter.
- Better daily operational discipline around token budgets.
