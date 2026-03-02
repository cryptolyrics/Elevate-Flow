# Elevate Flow Canon - PACKET CONTRACT

## Version
- `PACKET_VERSION: 1.0`

## Required Blocks (Exact Order)
1. `AGENT_ID`
2. `STATUS_MD`
3. `LOG_JSONL`
4. `ARTIFACTS`

Optional trailing blocks (order-preserving):
- `PACKET_VERSION`
- `RUN_ID`
- `GENERATED_AT`

## Block Delimiter

```text
===BLOCK_NAME===
<content>
====
```

## Validation Rules

- Reject missing required blocks.
- Reject out-of-order required blocks.
- Reject invalid `AGENT_ID` or `RUN_ID`.
- Reject invalid JSONL entries.
- Reject invalid `ARTIFACTS` JSON payload.

## Artifact Schema

`ARTIFACTS` is a JSON array of:
- `path`: relative path under `OUTPUTS/`
- `content`: UTF-8 string
