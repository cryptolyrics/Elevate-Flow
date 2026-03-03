# TASKS (JJ)

## P0. Pete Repo Cutover
- ID: PETE-REPO-001
- DoD: Pete runs only from `cryptolyrics/pete-engine`; no runtime dependence on `elevate-flow/agency` Pete scripts.
- Status: **DONE** - migration completed, tests passing, dry-run validated.
- Next action: enforce 9am run path from `pete-engine` and monitor for 3 consecutive days.
- Output: dedicated Pete compute repo operational.

## P1. Mission Control MVP (Web)
- ID: MC-WEB-001
- DoD: Deploy MVP with only:
  - Pete page (Best Bet, Team Parlay, Player Prop Parlay, Logic, Goal Tracker)
  - Agents docs page
- Status: **IN PROGRESS**
- Next action: Vlad to implement in `mission-control-dashboard` branch `codex/pete-page-mvp`.
- Output: live web source of truth MVP.

## P2. Clerk Runtime Verification
- ID: CLERK-002
- DoD: `/health` healthy and `/v1/status` stable with `jobsConfigured=2`, `totalFailures=0` on daily checks.
- Status: **IN PROGRESS**
- Next action: JJ posts daily status snapshot after Pete run window.
- Output: reliability trend tracked in decisions/logs.

## P3. Daily Operations Digest
- ID: DIGEST-002
- DoD: Daily telegram digest with decisions/actions/outcomes and Pete bet result updates.
- Status: **PENDING**
- Next action: publish daily after 9am run and after result settlement.
