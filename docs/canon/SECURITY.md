# Elevate Flow Canon - SECURITY

## Service Safety

- Bind to `127.0.0.1` only.
- Use `X-MC-KEY` on protected endpoints.
- Fail closed if auth key is missing.

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
