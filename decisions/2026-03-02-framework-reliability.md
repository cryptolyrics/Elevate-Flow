# Decision Log - 2026-03-02

## Decision
Implement additional Clerk framework reliability safeguards after the OpenClaw flag-compatibility patch.

## Why
- Poll overlap risk existed with `setInterval` when poll durations exceed interval.
- External CLI calls had no timeout, creating risk of stalled poll loops.
- Startup was coupled to first poll completion, reducing service survivability on transient upstream failures.

## What Changed
- Added `openClawTimeoutMs` config with validation floor (`>= 1000ms`).
- Added timeout handling and richer fallback error context in OpenClaw CLI provider.
- Reworked poll scheduler to sequential `setTimeout` scheduling.
- Made startup non-blocking for initial poll.
- Added tests for fallback compatibility and timeout failure behavior.

## Expected Outcome
- Improved resilience under OpenClaw CLI instability and long-running command scenarios.
- Cleaner failure telemetry while preserving compatibility fallback behavior.
- Lower risk of duplicate/overlapping polling side effects.
