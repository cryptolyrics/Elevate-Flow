# Mission Control Baseline UX Framework (Cavallo-Style)

## Purpose
Define the baseline UX and UI system for Elevate Flow Mission Control using the Cavallo-style operations dashboard pattern as the primary reference.

## Baseline Reference
- Source pattern: Cavallo Mission Control dashboard style (operations-first, queue + profitability + human performance).
- Design intent: fast operational clarity, low navigation friction, immediate action on blockers.

## Product Goal
- Build a web Mission Control that drives execution quality and protects margin.
- Phase 1 focus: Pete daily calls flow only, with JJ oversight visibility.

## Core UX Principles
1. Pulse first
- Show today's operational health in the first viewport without scrolling.

2. Queue over pages
- Prioritize work queues and statuses over deep navigation trees.

3. Action in context
- Resolve, escalate, or reroute work from the same view (minimal context switching).

4. Alert discipline
- Critical alerts are obvious; non-critical noise is suppressed.

5. Operator speed
- Keyboard-first interactions and predictable layout zones.

## Information Architecture (Baseline)
- Dashboard
- Calls Queue (Pete)
- Run Status
- Alerts
- Decisions Log
- Settings (restricted)

## Layout System
### Top bar
- Left: environment + timestamp.
- Center: global search / jump.
- Right: alerts bell, operator identity, quick actions.

### Left rail
- Fixed navigation with icons + labels.
- Collapsible, but expanded by default on desktop.

### Main workspace (3-zone)
1. KPI strip (top)
- Calls scheduled today
- Calls completed
- Blocked items
- SLA risk (next 2h)

2. Queue + status board (middle)
- Primary pane: calls queue table (sortable/filterable).
- Secondary pane: selected item detail + actions.

3. Activity + decisions (bottom/right)
- Recent actions feed.
- Linked decisions from `/decisions`.

## Data Modules (MVP)
1. Calls Queue
- Fields: call_id, owner, due_at, status, priority, blocker, last_update.
- Statuses: `queued`, `in_progress`, `blocked`, `done`.

2. Operational Health
- Last successful sync time.
- Failed jobs (24h).
- Poll latency band.

3. Alert Stack
- `critical`: security, outage, SLA breach.
- `warning`: delayed handoff, stale update.
- `info`: routine completions.

## Interaction Model
- Single-click row select opens side panel.
- Side panel actions:
  - Mark done
  - Add blocker note
  - Escalate to JJ
  - Assign to Vlad
- Bulk actions limited to non-destructive updates.
- Command palette (`Cmd/Ctrl+K`) for jump + action dispatch.

## Visual Direction
- Dark operations theme as default.
- Strong semantic colors:
  - Success: green
  - Warning: amber
  - Critical: red
  - Neutral metadata: slate
- Typography:
  - UI text: readable sans
  - Metrics/timestamps: mono
- Density:
  - Compact data rows
  - Clear spacing around critical actions

## Alert and Noise Controls
- Group repeated Telegram-origin updates into one digest card per window.
- Collapse duplicate events by `source + type + target` within a time bucket.
- Default feed view: only `critical` + `warning`; `info` behind toggle.
- Hard cap visible feed items; overflow requires explicit expand.

## Security and Compliance UX Constraints
- No secrets rendered in UI, logs, or toast notifications.
- Protected endpoints require API key headers.
- Redact token-like strings in event payload previews.
- Coppa veto path always visible for risky actions.

## MVP Acceptance Criteria (Phase 1)
1. Operator can see today's Pete call queue and status in under 5 seconds.
2. Operator can identify blocked calls without opening a second page.
3. Operator can escalate a blocked item to JJ in <= 2 clicks.
4. Critical alerts are visible in top bar and queue rows.
5. Activity feed stays readable under burst conditions (dedupe active).

## Out of Scope (Phase 1)
- Full multi-agent orchestration UI.
- Advanced custom dashboards per role.
- Deep mobile workflow parity.

## Build Sequence
1. Static shell + layout zones.
2. Calls queue table + detail drawer.
3. Alert stack + dedupe logic.
4. Activity/decisions feed integration.
5. Keyboard command palette.

## Handoff Notes for Vlad
- Implement thin vertical slice first: queue read view -> item update -> alert reflection.
- Defer polish until queue actions and escalation path are stable.
- Instrument render and interaction timings from day one.
