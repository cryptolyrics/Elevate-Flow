# Task Header Template

Use this header at the start of every task to ensure clarity and prevent working in the wrong repo.

---

## Template

```
# Task: <title>
# Owner: <agent-name>
# Repo: <repo-name>
# Branch: <branch-type>/<task-name>
# Priority: P0|P1|P2|P3
# DoD: <definition of done>
```

---

## Example

```
# Task: Add FB Ads integration to Ali
# Owner: Ali
# Repo: ali-growth
# Branch: codex/fb-ads-integration
# Priority: P1
# DoD: FB campaign creates ads, tracks CAC, reports to dashboard
```

---

## Quick Ref: Which Repo?

| Agent | Repo |
|-------|------|
| Pete | pete-engine |
| Ali | ali-growth |
| Vlad | vlad-infra (or Elevate-Flow for shared) |
| JJ | Elevate-Flow (core ops) |
| Scout | pete-engine (data) |
| Coach | Elevate-Flow (productivity) |
| Coppa | Elevate-Flow (security) |

---

## Branch Types

- `codex/` — AI/Codex tasks
- `feature/` — Manual features
- `bugfix/` — Bug fixes
- `docs/` — Documentation only
