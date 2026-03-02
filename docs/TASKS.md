# TASKS (JJ)

## P0. Factory API extension
- ID: API-001
- DoD: Extend factory API to support: GET /v1/status, GET /v1/logs?agent=&date=&tail=, GET /v1/digest?date=, GET /v1/health-alarm?date= - all behind X-MC-KEY
- Status: **BLOCKED** - DNS for mc-api.elevatestudios.io still propagating (per NOW.md)
- Next action: Wait for DNS, then add endpoints to factory API
- Output: API at mc-api.elevatestudios.io

## P1. Clerk verification
- ID: CLERK-001
- DoD: After JJ Clerk runs, verify it wrote STATUS.md + logs for each agent that ran. If any missing, mark agent as "NO WRITE" in JJ STATUS and in health-alarm file
- Status: **DONE** - Health-alarm generated, verified Ali has NO WRITE for STATUS.md
- Next action: Ensure JJ Health Alarm cron runs daily at 6pm
- Output: Verified writes, no silent failures
- Notes: Cron re-enabled (was showing "disabled" error)

## P2. Daily Digest
- ID: DIGEST-001
- DoD: Compile and post daily digest to Telegram at 5:30pm
- Status: **PENDING** - Scheduled for 5:30pm
- Next action: Run daily at 5:30pm
