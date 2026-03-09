# Repo Boundaries

**Updated: 2026-03-09**

## Principle

ElevateFlow-V2 is the **factory operating repo** — the single source of truth for how the factory runs.
It contains only canonical definitions, not runtime code.

---

## Repo Ownership Model

| Repo | Purpose | What's Inside |
|------|---------|---------------|
| **ElevateFlow-V2** | Factory operating truth | AGENTS.md, RUNBOOK.md, agent identities/souls/lanes, docs, schemas |
| **Pete Runtime** | Live quant execution | Adapters, brain, settlement, pipelines, storage, tests |
| **Dashboard** | Web UI / service | package.json, services/, frontend code |

---

## ElevateFlow-V2 Contents

**KEEP (Factory Definition):**
- `AGENTS.md` — Factory agent roster
- `RUNBOOK.md` — Operating procedures
- `AGENT-PROFILES.md` — Agent capability profiles
- `agents/*/IDENTITY.md` — Agent identity
- `agents/*/SOUL.md` — Agent persona
- `agents/*/LANE.md` — Agent responsibilities
- `agents/*/README.md` — Agent overview
- `docs/*` — Factory documentation
- `schemas/*.json` — Shared schemas

**DO NOT KEEP:**
- Runtime code (PeteDFS_engine.py, pipelines)
- Adapters, brain logic
- Settlement, storage, logs
- Data lakes, fixtures
- Tests
- Service code (dashboard)

---

## Git Discipline

Every major session ends as:
- **PUSHED** — Committed and pushed to remote
- **PARKED** — Committed locally, not yet pushed
- **DISCARDED** — Uncommitted changes intentionally dropped

---

## Branch Naming

| Prefix | Use For |
|--------|---------|
| `main` | Production-ready |
| `feature/<name>` | New work |
| `fix/<name>` | Bug fixes |
