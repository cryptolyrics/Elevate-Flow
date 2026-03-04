# Pete DFS Pipeline - Operational Playbook

## Objective
Manage daily operational pipeline: trigger data → QC → deliver slips to Jax.

---

## Pipeline Flow

### 1. DATA GATHERING (Morning)
- [ ] Pull Draftstars CSV (browser automation or manual upload)
- [ ] Fetch Odds API (the-odds-api.com)
- [ ] Fetch balldontlie games

### 2. QUALITY CONTROL
- [ ] Filter OUT players
- [ ] Verify salary cap ($100k)
- [ ] Check for duplicates
- [ ] Validate position requirements (2 PG, 2 SG, 2 SF, 2 PF, 1 C)

### 3. OPTIMIZATION
- [ ] Run lineup optimizer
- [ ] Target 250+ fppg
- [ ] Stay under $100k cap

### 4. DELIVERY
- [ ] Format for Jax (table format)
- [ ] Include: player, salary, FPPG, position
- [ ] Total salary + projected points

---

## Scripts
- `scripts/draftstars-optimizer.py` - Main lineup builder
- `scripts/pete-nba-pipeline.py` - Odds/picks

## Daily Schedule
- 8am Brisbane: Run pipeline
- 9am: Review with Jax
- 9:30am: Enter before tip-off

## QC Checklist Before Delivery
- [ ] All 9 positions filled
- [ ] No OUT players
- [ ] Under $100k
- [ ] No duplicates
