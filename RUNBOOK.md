# Elevate Flow — Runbook

## Mission
Generate $3,000 USD net profit per month using Elevate Flow AI factory frameworks.

## Agents

| Agent | Role | Model |
|-------|------|-------|
| JJ (COO) | Routing, cadence, reporting | MiniMax |
| Vlad (Dev) | Code, automation, infra | Codex |
| Ali (Growth) | Offer, funnel, distribution | MiniMax |
| Pete (Quant) | Models, backtests, risk | GPT-5 Mini |
| Coppa (Security) | Allowlist, scans, incident response | GPT-5 Mini |
| Coach | Accountability | MiniMax |
| Scout | Data scraping | MiniMax |

## Daily Cadence

- **8:00 AM:** Scout → Pete (DFS pipeline)
- **9:00 AM:** Team morning runs
- **5:30 PM:** Daily digest
- **6:00 PM:** Health alarm

## Services

### Clerk Service
- Location: `services/clerk-service/`
- Purpose: Agent output verification
- Run: `pnpm start`

### Mission Control API
- Port: 3008
- Auth: X-MC-KEY header

## Quick Commands

```bash
# Health check
curl localhost:3008/health

# Agent status
curl -H "X-MC-KEY: xxx" localhost:3008/v1/status
```

## Troubleshooting

- Agent not writing STATUS.md → check cron schedule
- API down → check tunnel/DNS
- Push fails → verify deploy key has write access
