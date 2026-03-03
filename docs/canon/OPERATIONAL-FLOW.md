# Elevate Flow Canon - OPERATIONAL FLOW

## Daily Loop

1. Kickoff
- Confirm active priorities and scheduled jobs.

2. Runs
- OpenClaw executes cron jobs (main or isolated).
- Agents emit packet output.

3. Normalize
- Clerk polls unprocessed runs by job.
- Clerk processes oldest to newest.
- Invalid runs are dead-lettered.

4. Digest and Health
- Main jobs consume canonical files for digest and alarms.

5. Review
- Update registry and tasks via Git commits.

## Incident Flow

1. Detect via dead-letter or missing writes.
2. Triage root cause.
3. Patch in Git.
4. Re-run and verify normalization.
