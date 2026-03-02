# 2026-03-02 OpenClaw CLI Interface Fix

## Decisions
- Prioritized compatibility with the current OpenClaw CLI interface for run listing (`--id`, optional `--limit`, no `--json`).
- Kept backward-compatible attempts to avoid regressions across mixed CLI versions.

## Actions
- Updated `services/clerk-service/src/openclaw-cli-provider.ts`:
  - Added multi-attempt run listing strategy that includes modern `cron runs --id <job> --limit 200`.
  - Added robust run-output parsing for object/array and line-delimited JSON variants.
- Updated `services/clerk-service/test/openclaw-cli-provider.test.ts`:
  - Added assertions for `--json` rejection and modern fallback path usage.
- Ran validation:
  - `npm run validate:registry`
  - `npm test -- --detectOpenHandles` in `services/clerk-service`
  - `npx tsc --noEmit` in `services/clerk-service`

## Outcomes
- Clerk polling no longer depends on deprecated `--json` and `--job` list flags.
- Backward compatibility remains for older OpenClaw CLI variants.
- Test suite remains green (`15` tests passing).
