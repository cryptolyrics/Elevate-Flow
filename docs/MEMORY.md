# MEMORY.md - Long-Term Memory

## Team Members
- **JJ (me)** — 🤖🍼 — COO/operations — main agent (MiniMax M2.5)
- **Vlad** 👨‍💻 — openai-codex/gpt-5.3-codex — builds Mission Dashboard, UX research
- **Ali (Alison)** 🚀 — minimax/MiniMax-M2.5 — X growth/marketing, UX research
- **Pete** 📈 — openai/gpt-5-mini — math engine, DFS optimization
- **Coppa** 🛡️ — openai/gpt-5-mini — security sub-agent (needs respawning)
- **Coach** ⏰ — minimax/MiniMax-M2.5
- **Scout** 🔎 — minimax/MiniMax-M2.5 — data scraper (DFS)
- **Bruce** — Codex — product architect
- **Max** — offline, was doing dashboard charts

## The DFS Factory
Daily pipeline for fantasy sports:
- 8AM: Trigger Scout (data scrape from Draftstars)
- 8:30AM: QC check (verify no OUT players, correct data)
- 9AM: Pete (MILP optimization)
- 9:30AM: Deliver lineup to Jax

PeteDFS_engine.py saved in workspace-pete - uses ESPN scraping + MILP

## Projects

### Mission Control / Elevate Flow
- Vlad built: Next.js + Tailwind, mobile responsive
- Rebranded to "Elevate Flow"
- Target: $3k/week, Milestone: $1k/week by June
- Deployed: https://github.com/cryptolyrics/mission-control-dashboard
- Hosting goal: mission.elevatestudios.io (needs DNS CNAME)
- **v2 task**: Ali did UX research, referenced Stripe/Linear/Notion/Cavallo Mission Control
- Vlad working on v2 with new dark theme, sidebar nav, KPI cards, pipeline viz

### DFS Pipeline (Pete)
- Daily: 8am gather → 8:30 QC → 9am optimize → 9:30 deliver
- Scripts: draftstars-optimizer.py, pete-nba-pipeline.py
- Uses Draftstars CSV, Odds API, balldontlie
- QC: OUT players, $100k cap, 250+ fppg target

### GAS Lottery
- MVP complete: Phantom wallet + Devnet USDC transfers working
- Mini-app UI done (Vite + Phantom)
- Entries API at localhost:8788
- Treasury wallet deployed on Solana devnet
- Next: real on-chain USDC transfers to treasury

### iMessage via BlueBubbles
- Goal: send from jjbotbro@icloud.com
- JJ doesn't want FDA on main instance (security concern)
- Decision: Use BlueBubbles on separate Mac/VM
- BlueBubbles skill already installed in OpenClaw, needs config (serverUrl + password)
- JJ has ngrok already - just needs to run BlueBubbles server

### X Engagement
- Wanted to grow Jax's X channel
- Coppa audited skills: 15-20% of ClawHub skills are compromised/malware
- Recommended opentweet/x-poster ($5.99/mo, credentials on their server)

## Daily Schedule
- 7am: Scout runs (pre-DFS data scrape)
- 8am: JJ Daily Digest (reads all agent OUTPUTS.md → posts to Telegram)
- 8am: Pete runs (pre-game DFS)
- 9am: Vlad, Ali, Coach morning runs
- 2pm: Vlad, Ali afternoon runs
- 5pm: Coach evening run
- 7pm: Vlad, Ali evening runs
- Memory updates: twice-daily (morning + evening)

## Worker Pattern (Feb 2026)
**File structure per agent:**
- `workspace-{agent}/TASKS.md` - JJ assigns tasks (ID, priority, DoD, next action, due, owner)
- `workspace-{agent}/STATUS.md` - Overwritten each run (shipped, blockers, next action, links)
- `workspace-{agent}/OUTPUTS/` - Artifacts
- `workspace-{agent}/logs/YYYY-MM-DD.jsonl` - Timestamped activity

**Daily flow:**
1. 8:30am JJ Kickoff: Read NOW.md → Generate TASKS.md per agent → Post 5-line plan to Telegram
2. Scheduled runs: Agent reads TASKS.md → Execute 1-3 actions → Write OUTPUTS/ → Update STATUS.md → Append to logs/
3. 5:30pm JJ Digest: Read STATUS.md + logs → Compile → Post to Telegram → Prune NOW.md → Archive stale to STATE_ARCHIVE.md

## Misc
- Gateway had restart issue (SIGTERM + port issue) - resolved
- Session was reset at some point - recovered context from session logs
- MiniMax M2.5 was being tested as "second brain" - Codex for heavy coding, MiniMax for daily ops

## Mission (Elevate Flow)
**Goal:** $3,000 USD/week by June 2026

**Agents:**
- Scout (MiniMax) — market validation
- Bruce (Codex) — product architect
- Alison (MiniMax) — growth/marketing
- Alan (MiniMax) — revenue modeling
- Frank (MiniMax) — risk/compliance
- Vlad (Codex) — head of development
- Coppa (Codex) — security
- Pete (MiniMax) — sportsbet operator
- Productivity Coach (MiniMax) — ADHD accountability
- JJ (me) — COO

## Session Context Info
- Model: MiniMax-M2.5 (200k context)
- Current session: 154k tokens (77% full)
- Context = entire thread + workspace files (SOUL.md, USER.md, memory/*.md, MEMORY.md)
- To reduce: can switch to last N messages instead of full thread
