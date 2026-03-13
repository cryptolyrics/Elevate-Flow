# Canon Doctrine Manifest
# Defines which files are canon-managed and where they sync to
# Format: source_path|target_workspace|target_path

# === CANON ROOT STRUCTURE ===
# Files in workspace-elevate-flow root that apply to ALL agents
ZERO-MISSION-CANON.md|ALL|./ZERO-MISSION-CANON.md
AGENTS.md|ALL|./AGENTS.md
RUNBOOK.md|ALL|./RUNBOOK.md

# === PER-AGENT DOCTRINE ===
# Agent-specific files sync to their workspaces
agents/JJ/SOUL.md|workspace-jj|./SOUL.md
agents/JJ/LANE.md|workspace-jj|./LANE.md
agents/Vlad/SOUL.md|workspace-vlad|./SOUL.md
agents/Vlad/LANE.md|workspace-vlad|./LANE.md
agents/Pete/SOUL.md|workspace-pete|./SOUL.md
agents/Pete/LANE.md|workspace-pete|./LANE.md
agents/Ali/SOUL.md|workspace-ali|./SOUL.md
agents/Ali/LANE.md|workspace-ali|./LANE.md
agents/Coppa/SOUL.md|workspace-coppa|./SOUL.md
agents/Coppa/LANE.md|workspace-coppa|./LANE.md
agents/Coach/SOUL.md|workspace-coach|./SOUL.md
agents/Coach/LANE.md|workspace-coach|./LANE.md
agents/Scout/SOUL.md|workspace-scout|./SOUL.md

# === SUBAGENTS ===
agents/baby-vlad/SOUL.md|workspace-baby-vlad|./SOUL.md
agents/baby-vlad/LANE.md|workspace-baby-vlad|./LANE.md
