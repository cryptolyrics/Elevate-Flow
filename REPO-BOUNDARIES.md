# Repo Boundaries

This document defines which repository each agent should work in and what belongs where.

## Principle

**One agent, one repo** (with exceptions for shared infrastructure). Agents should not modify code in repositories they don't own unless explicitly coordinated.

---

## Elevate-Flow

**Owner:** System / All agents (shared)

**What belongs here:**
- Core CLI tools and utilities
- Shared infrastructure code
- Operations scripts (deployment, monitoring, etc.)
- Generic agents and workflows that aren't tied to a specific project

**What does NOT belong here:**
- Project-specific business logic
- Customer or product code
- Feature work for specific agents

---

## pete-engine

**Owner:** Pete

**What belongs here:**
- Pete's personal agent configuration
- Pete's custom tools and workflows
- Any code Pete is actively developing
- Experiments and prototypes specific to Pete's work

**What does NOT belong here:**
- Code belonging to other agents
- Shared infrastructure (use Elevate-Flow)
- Ali's work

---

## ali-growth

**Owner:** Ali

**What belongs here:**
- Ali's personal agent configuration
- Ali's custom tools and workflows
- Growth-specific automation and experiments
- Any code Ali is actively developing

**What does NOT belong here:**
- Code belonging to other agents
- Shared infrastructure (use Elevate-Flow)
- Pete's work

---

## Working Across Repos

If an agent needs to work in a repository they don't own:

1. **Coordinate first** - Get permission from the repo owner
2. **Create a branch** - Use `codex/<task>` or `feature/<name>` pattern
3. **PR review** - Owner reviews before merge
4. **Minimal changes** - Only what's needed, don't refactor unrelated code

---

## Branch Naming Convention

| Prefix | Use For |
|--------|---------|
| `main` | Production-ready code only |
| `codex/<task>` | Codex investigations, research tasks |
| `feature/<name>` | New features, experiments, prototypes |

Example: `codex/investigate-auth-issue`, `feature/add-analytics-dashboard`
