# Elevate Flow Canon - SECURITY

## Service Safety

- Bind to `127.0.0.1` only.
- Use `X-MC-KEY` on protected endpoints.
- Fail closed if auth key is missing.

## Access Boundary (Hard Rule)

- Elevate Flow agents do **not** have access to Jax local drives.
- Never assume paths like `/Users/Jax/...` are readable by agents.
- Cross-machine exchange must be via Git commits, API endpoints, or explicit message payloads.
- If data is not in Git/API/messages, treat it as unavailable.

## Execution Safety

- No `execSync` for dynamic commands.
- Use `spawn` with argument arrays and `shell: false`.
- Validate job/run/agent IDs.

## File Safety

- Enforce sandbox paths for all writes.
- Use atomic writes for `STATUS.md` and `state.json`.
- Keep dead-letter artifacts for failed runs.

## Secret Safety

- No secrets in repository or logs.
- Use environment variables.
- Rotate leaked credentials immediately.
