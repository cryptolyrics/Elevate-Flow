# Token Efficiency SOP (OpenClaw + Telegram)

## Purpose
Keep factory token usage predictable and low while preserving reliability.

## Targets
- Active OpenClaw sessions: `<= 4` total (including `agent:main:main`).
- Stale cron sessions older than 8h: `0`.
- Telegram updates: summary-first, no transcript replay.

## OpenClaw Session Hygiene

### Daily Commands
Run dry-run first:

```bash
npm run sessions:prune:dry
```

If output looks correct, apply:

```bash
npm run sessions:prune
```

Defaults:
- keep key: `agent:main:main`
- prune stale sessions older than 8h
- keep max 4 sessions
- auto-backup `sessions.json` before write

### Optional Overrides

```bash
node scripts/prune-openclaw-sessions.mjs \
  --apply \
  --store "/Users/jjbot/.openclaw/agents/main/sessions/sessions.json" \
  --max-age-hours 6 \
  --max-sessions 3 \
  --keep-key "agent:main:main"
```

## Telegram Bloat Mitigation

### Rules
1. Send only state changes, blockers, or explicit asks.
2. Batch non-urgent updates into one digest (morning/evening).
3. Never paste long logs; link commit hash plus one-line summary instead.
4. Keep operational messages under 8 lines.
5. Avoid repeated "still working" updates without new information.
6. Use one final summary message per workflow:
   - Decisions
   - Actions
   - Outcomes

### Message Templates

Status update:

```text
Status: <PASS|BLOCKED>
Change: <what changed>
Impact: <why it matters>
Next: <next action + owner + ETA>
```

Daily digest:

```text
Today:
- <top outcome 1>
- <top outcome 2>

Blockers:
- <owner> <blocker> <next action>

Tomorrow:
- <priority 1>
- <priority 2>
```

## Escalation Rule
- If token/session hygiene drifts for 2 consecutive checks, escalate to JJ and create a decision record in `/decisions`.
