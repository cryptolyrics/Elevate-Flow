# Decision Log - 2026-03-02 (OpenClaw CLI Interface)

## Decision
Update Clerk's OpenClaw provider to support the current CLI interface for runs list commands.

## Why
- Current runtime reports failures due to unsupported flags in list commands (`--json`, `--job`).
- Service requires compatibility with both current and historical OpenClaw CLI variants during transition.

## What Changed
- Added a prioritized attempt sequence for `listRunsAfter`:
  1. Legacy `cron runs list --job ... --json`
  2. Legacy `cron runs list --id ... --json`
  3. Current `cron runs --id ... --limit 200`
  4. Current `cron runs --id ...`
- Added tolerant JSON parsing for run-list outputs (array/object/line-delimited JSON).
- Updated provider tests to enforce fallback into the modern no-`--json` interface.

## Expected Outcome
- Poll failures caused by outdated flags are eliminated on current OpenClaw CLI.
- Existing deployments on older CLI shapes keep working.
