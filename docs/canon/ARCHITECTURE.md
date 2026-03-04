# Canonical v1 Architecture

## Overview
This document defines the canonical structure for Elevate Flow agent services.

## Directory Structure

```
elevate-flow/
├── docs/
│   └── canon/          # Canonical specs
│       ├── AGENTS.md   # Agent definitions
│       ├── WORKFLOWS.md # Trigger definitions
│       └── API.md      # API contract
├── registry/           # Agent task registries
├── services/
│   └── clerk-service/ # Output verification service
├── openclaw/          # OpenClaw config snapshots
├── agents/            # Agent profiles
├── workflows/         # Cron definitions
└── RUNBOOK.md         # Operations manual
```

## Agent Contract

Each agent must:
1. Read TASKS.md from workspace
2. Execute tasks
3. Write STATUS.md on completion
4. Append to logs/YYYY-MM-DD.jsonl

## API Contract

### GET /v1/status
Returns agent status.

### GET /v1/logs?agent=&date=&tail=
Returns log entries.

### GET /v1/digest?date=
Returns daily digest.

### GET /v1/health-alarm?date=
Returns health alarm report.

## Workflow Triggers

- Cron: Time-based execution
- Heartbeat: Periodic check-ins
- Webhook: External events
