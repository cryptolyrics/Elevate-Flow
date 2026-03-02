# Framework Brief - JJ + Vlad (2026-03-02)

## Current State
- Branch: `codex/framework-reset-v1`
- Clerk runtime (JJ verified): healthy
  - `/health`: `ok: true`
  - `/v1/status`: `jobsConfigured=2`, `totalFailures=0`, `lastPollAt=2026-03-02T04:47:32Z`
- Registry validation: passing (`npm run validate:registry`)

## New Framework Commits
- `7b99ab2` `fix(clerk): harden polling loop and OpenClaw CLI timeouts`
- `5ea30dd` `ops(log): record framework audit decisions and outcomes`
- Prior compatibility fix already on branch:
  - `6c58aed` `fix(clerk): fallback to --id for OpenClaw CLI run commands`

## What Changed (Reliability Only)
- Added `openClawTimeoutMs` config guardrail (default `15000ms`, min `1000ms`).
- Added OpenClaw CLI per-call timeout and clearer fallback error context.
- Switched poll scheduling to sequential loop to prevent overlapping polls.
- Made initial poll non-blocking so service can stay up on transient upstream errors.
- Added regression tests for fallback behavior and timeout behavior.

## JJ - Immediate Actions
1. Confirm this branch and commits are the deployment target.
2. Track today as framework reliability complete (no Mission Control UI scope).
3. Continue daily status checks:
   - `curl -H "X-MC-KEY: <key>" http://127.0.0.1:3008/v1/status`
4. Watch `.clerk/dead-letter/` growth and escalate if non-zero trend appears.

## Vlad - Immediate Actions
1. Pull latest branch on Clerk host:
   - `git checkout codex/framework-reset-v1`
   - `git pull`
2. Restart clerk-service with updated config including:
   - `"openClawTimeoutMs": 15000`
3. Verify post-restart:
   - `/health` returns `ok: true`
   - `/v1/status` shows `jobsConfigured=2`
   - `totalFailures` remains `0` after at least one poll interval
4. If blocked, follow 2-hour escalation cadence to JJ until resolved.

## Notes
- Scope intentionally limited to framework reliability.
- No secrets were added to repo, logs, or commit content.
