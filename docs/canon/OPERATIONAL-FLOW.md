# Elevate Flow Canon - OPERATIONAL FLOW

## Daily Loop

1. Kickoff
- Confirm active priorities and scheduled jobs.

2. Runs
- OpenClaw executes cron jobs (main or isolated).
- Agents emit packet output.
- Specialist execution should be routed through internal session/runtime paths, not Telegram/group chat.

3. Normalize
- Clerk polls unprocessed runs by job.
- Clerk processes oldest to newest.
- Invalid runs are dead-lettered.

4. Digest and Health
- Main jobs consume canonical files for digest and alarms.

5. Review
- Update registry and tasks via Git commits.
- When a task completes, post a visible completion update so the team knows the task is closed.
- Do not treat canonical closeout alone as sufficient operating communication.
- For technical tasks, every continuation and checkpoint must state the exact repo/path.
- If work occurred in the wrong repo/path, record the mistake visibly and re-execute in the approved repo before claiming progress.
- JJ must use the technical-task checklist before reporting `running`, `waiting_review`, or `done`.

## Incident Flow

1. Detect via dead-letter or missing writes.
2. Triage root cause.
3. Patch in Git.
4. Re-run and verify normalization.
