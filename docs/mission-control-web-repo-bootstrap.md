# Mission Control Web Repo Bootstrap (JJ/Vlad)

## Goal
Stand up the web repo cleanly without mixing framework operations code.

## Repo
- Name: `mission-control-dashboard`
- Owner: Vlad
- Deploy: Vercel (or Cloudflare Pages)

## Required Env Vars (web repo)
- `MC_API_BASE_URL`
- `MC_API_KEY` (sent as `X-MC-KEY` from server-side routes only)
- `TZ=Australia/Brisbane`

## Build Scope (Phase 1 Only)
1. `/` Dashboard shell
2. `/pete` Pete Page
  - Best Bet
  - Team Parlay
  - Player Prop Parlay
  - Logic Summary
  - Goal Tracker
3. `/agents` Agent Docs list/read view

DFS UI is out of scope.

## Data Inputs
- Clerk endpoints:
  - `GET /health`
  - `GET /v1/status`
- Pete payload follows:
  - `docs/contracts/mission-control-pete-v1.json`

## Security Constraints
- Never expose `MC_API_KEY` in browser code.
- Use server routes/proxy for protected calls.
- Redact token-like strings in logs and UI.

## Acceptance Criteria
1. Pete page loads in < 3s on desktop.
2. 9:00 AM AEST update path is documented and runnable.
3. Goal tracker can be updated by JJ/Jax without code changes.
4. `/agents` renders docs links from registry/source files.
5. No secrets in repo, issues, or build logs.

## Handoff Sequence
1. Vlad opens PR in web repo.
2. JJ validates with checklist in `docs/repo-boundary-and-handoff.md`.
3. JJ posts GO/NO-GO.
4. Deploy to production.
