> CANON ROOT
> This file is part of the active Elevate Flow source of truth.
> Changes here define the operating canon.

# REPO_OWNERSHIP.md — Elevate Flow

## Purpose
Define who owns which repositories and planes for Elevate Flow and related projects, so changes, incidents, and reviews always have a clear accountable owner.

## Elevate Flow ownership
- **Repo:** `elevate-flow` (this canon root)
- **Brand context:** Elevate Flow is the factory/OS inside **Elevate Studios**.
- **Canonical path on this machine:** `~/.openclaw/workspace-elevate-flow/`

**Accountable owner:**
- JJ (main) — COO / orchestration lead.

**Supporting owners:**
- Vlad — engineering lead.
- Ali — growth lead.
- Pete — quant lead (contracts + routing, not runtime).
- Coppa — security lead.

## External repo ownership
These repos are **part of the overall system** but not hosted under this canon root.

- **Pete Engine**
  - Purpose: Pete's quant runtime (models, tests, execution engine).
  - Role in Elevate Flow: external compute plane for Pete strategies; Elevate Flow only owns contracts, routing, monitoring, and guardrails.
  - Accountable owner: Pete.

- **Mission Control Dashboard**
  - Purpose: Web UI shell and module pages for visualising factory state.
  - Role in Elevate Flow: visualisation/operations UI plane for agents, jobs, and health.
  - Accountable owner: Vlad (implementation) with JJ (product/ops).

- **Other product repos (e.g. SwapBot)**
  - Purpose: product‑specific implementations that may use Elevate Flow as execution fabric.
  - Role in Elevate Flow: treated as separate products; may consume Elevate Flow outputs or run via its scheduling, but are not part of this canon root.
  - Accountable owners: to be documented per product (default: Vlad + Ali shared, with JJ as escalation).

## Per‑agent workspace ownership
Per‑agent workspaces (e.g. `workspace-vlad/`, `workspace-ali/`, `workspace-coach/`) are **execution mirrors**, not canon roots.

- JJ → `workspace-jj/`
- Vlad → `workspace-vlad/`
- Ali → `workspace-ali/`
- Pete → `workspace-pete/`
- Coppa → `workspace-coppa/`
- Coach → `workspace-coach/`

Rules:
- Behavioural or mission changes must land in canon under `workspace-elevate-flow/` first.
- Per‑agent workspaces should carry LOCAL WORKSPACE MIRROR headers in overlapping canon‑like files.

Subagents:
- Baby Vlad → `workspace-baby-vlad/` under Vlad’s supervision.
- Scout → `workspace-scout/` under Ali’s supervision.

## Project‑level architecture docs
- Elevate Flow core architecture:
  - `~/.openclaw/workspace-elevate-flow/docs/canon/ARCHITECTURE.md`
- Product‑specific architecture (examples):
  - SwapBot: `~/.openclaw/workspace/SwapBot/ARCHITECTURE.md` (owned by Vlad + Ali, with JJ for alignment).

Rule:
- Project docs should reference Elevate Flow **as execution fabric** where relevant, not duplicate its canon.

## Legacy / reference repos
- `~/elevate-flow-jj/`
  - Status: LEGACY REFERENCE ONLY.
  - Use: salvage previous docs and contracts; do not treat as active SOT.

- `workspace-*.ARCHIVE.*` under `~/.openclaw/`
  - Status: ARCHIVE / HISTORICAL SNAPSHOT.
  - Use: historical context; never updated for new work.

## Open questions
- Final ownership split for future products (e.g. dedicated repos for new “studios” under Elevate Studios).
- Whether some per‑agent workspaces should be collapsed or regenerated from canon on demand.
