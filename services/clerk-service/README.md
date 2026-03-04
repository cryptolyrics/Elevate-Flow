# Clerk Service

Local Node/TS service for OpenClaw that polls run outputs, parses strict packet blocks, writes canonical files, and generates clerk reports.

## Quick Start

```bash
# Install dependencies
cd clerk-service
npm install

# Build
npm run build

# Run (requires config.json - see below)
npm start
```

## Configuration

Create `config.json` in the service directory:

```json
{
  "workspaceRoot": "/path/to/workspace-jj",
  "pollIntervalSec": 120,
  "fetchMode": "cli",
  "reportWorkspace": "/path/to/workspace-jj",
  "jobs": [
    {
      "agentId": "baby-vlad",
      "jobId": "bv-001",
      "workspace": "workspace-baby-vlad"
    }
  ]
}
```

## Running

```bash
# Development mode
npm run dev

# Production
npm start

# With custom config path
CLERK_CONFIG=/path/to/config.json npm start
```

## API Endpoints

- `GET /health` - Health check (always returns `{"status":"ok"}`)
- `GET /status` - Service status

## Output Structure

The service writes to the configured `workspaceRoot`:

```
outputs/
├── clerk-state.json          # Last processed run per job
├── clerk-report.md           # Latest poll report
├── clerk-dead-letter/        # Failed runs
│   └── YYYY-MM-DD/
│       └── <jobId>-<runId>.json
└── <jobId>/
    ├── STATUS.md             # Latest status (overwritten)
    ├── logs/
    │   └── YYYY-MM-DD.jsonl # Appended logs
    └── artifacts/
        └── <files>           # Written artifacts
```

## Packet Format

Run outputs must use strict block format:

```
===AGENT_ID===
baby-vlad
====

===STATUS_MD===
# Status content here
====

===LOG_JSONL===
{"level":"info","msg":"hello"}
{"level":"warn","msg":"caution"}
====

===ARTIFACTS===
[{"filename":"output.json","content":"{}"}]
====

===PACKET_VERSION===
1.0
====

===RUN_ID===
run-123
====

===GENERATED_AT===
2026-02-27T10:00:00Z
====
```

Required blocks (in exact order): `AGENT_ID`, `STATUS_MD`, `LOG_JSONL`, `ARTIFACTS`

Optional blocks: `PACKET_VERSION`, `RUN_ID`, `GENERATED_AT`

## Testing

```bash
npm test
```

## Design Principles

- **No LLM calls** - Deterministic behavior only
- **Minimal code** - Understandable in 5 minutes
- **Idempotent** - Same input produces same output, state tracks progress
- **Sandboxed** - All writes validated to stay within workspace root
- **Strict parsing** - Rejects malformed packets
