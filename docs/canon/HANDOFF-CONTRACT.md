# Elevate Flow Canon - JJ Handoff Contract

## Purpose

Define a strict Git-based handoff from JJ operations to technical review/optimization.

This contract keeps sessions siloed while preserving reliable continuity.

## Daily Required Outputs

JJ must create both files every operating day:

1. `reports/daily/YYYY-MM-DD-jj.md`
2. `reports/daily/YYYY-MM-DD-jj.json`

Date uses local operating timezone (`Australia/Brisbane`) unless explicitly overridden.

## Markdown Report Required Sections

`reports/daily/YYYY-MM-DD-jj.md` must include these headings exactly:

1. `Summary`
2. `Completed Today`
3. `Failed or Blocked`
4. `Open Decisions Needed`
5. `Agent Health`
6. `Cost and Runtime Notes`
7. `Tomorrow Plan`

### Agent Health Format

For each tracked agent, JJ must record one status:
- `OK`
- `BLOCKED`
- `NO_WRITE`

## JSON Report Required Schema

`reports/daily/YYYY-MM-DD-jj.json` must include:

- `date` (string)
- `timezone` (string)
- `jobs_run` (integer)
- `jobs_failed` (integer)
- `dead_letters` (integer)
- `agents` (array)
- `blockers` (array)
- `decisions_needed` (array)
- `cost_notes` (string)
- `runtime_notes` (string)

Each `agents[]` entry must include:
- `agent_id`
- `status` (`OK|BLOCKED|NO_WRITE`)
- `note`

## Commit Rule

JJ must commit daily handoff with:

- commit message: `ops(daily): jj report YYYY-MM-DD`
- one daily report commit per day

## Review Trigger

When operator requests review, the reviewer should:

1. Read today + previous day markdown and JSON reports.
2. Compare trend deltas (failures, dead letters, blockers, costs).
3. Propose optimization patches and safety fixes.
4. Return prioritized findings and concrete changes.

## Failure Handling

If report is missing required sections or JSON keys:

1. Mark handoff as invalid.
2. Request JJ reissue the report.
3. Skip optimization decisions until valid handoff is provided.
