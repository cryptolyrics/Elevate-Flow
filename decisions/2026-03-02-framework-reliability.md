# Decision Log - 2026-03-02 (Framework Reliability)

## Decision
Adopt and keep the Clerk reliability hardening set on `codex/framework-reset-v1` while preserving compatibility with the remote branch fixes.

## Why
- Poll overlap risk existed with `setInterval` when poll cycles exceeded interval.
- External CLI calls had no timeout, creating a stall risk in polling loops.
- Branch divergence introduced review drift where expected commits appeared missing.

## What Changed
- Kept compatibility fallback behavior for OpenClaw run commands (`--job/--run` to `--id`).
- Added `openClawTimeoutMs` guardrail and timeout handling in CLI provider.
- Reworked poll scheduling to sequential `setTimeout` flow.
- Kept startup non-blocking for initial poll failure scenarios.
- Merged remote review updates and resolved conflicts without rewriting required commit history.

## Expected Outcome
- Stable polling behavior with reduced hang/overlap risk.
- Clearer and deterministic reliability posture for JJ review and Vlad deployment.
- Hash-based checklist commits remain traceable in branch history.
