# Elevate Flow Team Kickoff (v1 Framework)

## Goal

Align all agents to the new registry-driven framework and deterministic operations flow.

## Kickoff Sequence

1. Confirm source of truth
- Canon docs: `docs/canon/`
- Registry: `registry/`
- OpenClaw generated snapshots: `openclaw/generated/`

2. Confirm runtime services
- Clerk service running locally (`127.0.0.1:3008`)
- `X-MC-KEY` configured

3. Confirm scheduling posture
- Active scheduled jobs from registry:
  - pete-dfs-morning
  - jj-daily-digest
  - jj-health-alarm
- Manual-only agents (no scheduled run):
  - vlad
  - baby-vlad
  - scout
  - ali
  - coppa
  - coach

4. Confirm safety posture
- No secrets in Git
- Packet contract enforced
- Dead-letter monitored daily
- Pete wagering remains fail-closed unless explicitly enabled

5. Confirm communication contract
- JJ publishes daily report files:
  - `reports/daily/YYYY-MM-DD-jj.md`
  - `reports/daily/YYYY-MM-DD-jj.json`
- Commit message format:
  - `ops(daily): jj report YYYY-MM-DD`

## Agent Instructions (Initial)

## JJ
- Operate daily loop and produce handoff reports.
- Escalate blockers and decisions clearly.

## Vlad and Baby Vlad
- On-demand only for now.
- Must finish assigned tasks before taking new work.
- If blocked/unclear, ask JJ every 2 hours until completion.

## Pete
- API-Sports data path active.
- Output must remain `NO_BET` until quant gating is explicitly enabled.

## Scout, Ali, Coach, Coppa
- Paused during MVP sprint window.
- Do not run unless JJ explicitly reactivates.

## Operator Checklist (You)

1. Run `npm run validate:registry`
2. Check Clerk:
   - `curl http://127.0.0.1:3008/health`
   - `curl -H "X-MC-KEY: <key>" http://127.0.0.1:3008/v1/status`
3. Verify no unexpected `.clerk/dead-letter/*` growth
4. Confirm JJ posted daily reports in `reports/daily/`

## Day-1 Success Criteria

- Registry validates
- Clerk healthy
- Daily digest and health alarm produced
- JJ handoff files committed
- No unauthorized wagering output from Pete
