# clerk-service

Deterministic normalization service for Elevate Flow.

## Scope

- Poll OpenClaw run outputs via CLI adapter.
- Parse strict packet format.
- Normalize output into canonical workspace files.
- Track idempotent progress in `state.json`.
- Dead-letter invalid runs.

No LLM calls. No scheduling ownership. OpenClaw remains the orchestrator.

## Endpoints

- `GET /health` public
- `GET /v1/status` requires `X-MC-KEY`
- `GET /v1/jobs` requires `X-MC-KEY`

Service binds to `127.0.0.1` only.

## Config

Default config path: `services/clerk-service/config.json`
Override with: `CLERK_CONFIG=/path/to/config.json`

Config fields:

- `workspaceRoot`: sandbox root for canonical writes
- `reportWorkspace`: root for `.clerk/report.md` and dead-letter
- `pollIntervalSec`: polling interval in seconds (minimum 15)
- `fetchMode`: `cli`
- `openClawBin`: CLI binary name/path
- `openClawTimeoutMs`: per-CLI call timeout in milliseconds (minimum 1000)
- `host`: must be `127.0.0.1`
- `port`: HTTP port
- `jobs[]`: `jobId`, `agentId`, `workspace`

## Packet Contract

Required blocks, in exact order:

1. `AGENT_ID`
2. `STATUS_MD`
3. `LOG_JSONL`
4. `ARTIFACTS`

Optional trailing blocks:

- `PACKET_VERSION`
- `RUN_ID`
- `GENERATED_AT`

`ARTIFACTS` must be JSON array of `{ "path": string, "content": string }`.

## Canonical Writes

Legacy packet normalization writes only:

- `logs/YYYY-MM-DD.jsonl` (append-only)
- `OUTPUTS/**` (sandboxed artifact writes)

Clerk V1 task-state truth lives separately under canonical `tasks/` and rendered root visibility files.

Clerk internals:

- `.clerk/state.json`
- `.clerk/report.md`
- `.clerk/dead-letter/YYYY-MM-DD/*.json`

## Security

- `X-MC-KEY` auth for protected endpoints (`MC_API_KEY` env var)
- fail-closed if `MC_API_KEY` is missing
- no `execSync`; CLI calls use `spawn(..., { shell: false })`
- ID validation on `agentId`, `jobId`, `runId`
- path traversal and absolute path rejection

## Development

```bash
cd services/clerk-service
npm install
npm run build
npm test
MC_API_KEY=local-dev-key npm start
```

## Testing Coverage

- packet parser strictness
- sandbox path protection
- state idempotency behavior
- ordered processing of runs
