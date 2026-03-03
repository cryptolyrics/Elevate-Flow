# Pete Engine Repo Migration Plan

## Objective
Move Pete quant logic into a dedicated repo (`pete-engine`) while keeping Elevate Flow as the control plane.

## Target Repo Model
- `elevate-flow/agency`: mission SOT, registry, contracts, orchestration, clerk, runbooks.
- `mission-control-dashboard`: UI shell and module rendering.
- `pete-engine`: Pete pipeline, data sync, backtests, learning engine, quant tests.

## Scope To Move
- `projects/pete-dfs/`
- Root mirrors:
  - `pete-nba-pipeline.py`
  - `PeteDFS_engine.py`
  - `draftstars_final.py`
- Pete-only docs:
  - `docs/pete-*.md` (if present)

## Keep In Elevate Flow
- Agent registry and canon docs.
- Cross-agent contracts.
- Mission control operating docs.
- Clerk service.

## Contract First (No UI Coupling)
Pete output contract must be versioned and consumed by UI as data only.

Required payload sections:
- `best_bet`
- `team_parlay`
- `player_prop_parlay`
- `logic_summary`
- `goal_tracker`

## Migration Steps
1. Create new GitHub repo: `cryptolyrics/pete-engine` (private recommended).
2. Initialize local clone under `/Users/Jax/Documents/GitHub/pete-engine`.
3. Copy Pete code and docs from `agency` into `pete-engine`.
4. Add minimal repo structure:
   - `src/` or `scripts/`
   - `tests/`
   - `docs/`
   - `config/`
   - `.github/workflows/ci.yml`
5. Run tests and fix path assumptions.
6. Push `main` + create branch `codex/pete-engine-hardening`.
7. In `agency`, replace Pete code paths with integration references and contract links.
8. Update mission-control-dashboard to consume Pete contract artifact/API only.

## Suggested Command Sequence (JJ/Vlad)
```bash
# 1) create local repo
cd /Users/Jax/Documents/GitHub
git clone https://github.com/cryptolyrics/pete-engine.git
cd pete-engine

# 2) copy from agency
rsync -av --exclude '__pycache__' \
  /Users/Jax/Documents/GitHub/elevate-flow/agency/projects/pete-dfs/ \
  /Users/Jax/Documents/GitHub/pete-engine/projects/pete-dfs/

cp /Users/Jax/Documents/GitHub/elevate-flow/agency/pete-nba-pipeline.py .
cp /Users/Jax/Documents/GitHub/elevate-flow/agency/PeteDFS_engine.py .
cp /Users/Jax/Documents/GitHub/elevate-flow/agency/draftstars_final.py .

# 3) baseline checks
python3 -m unittest discover -s projects/pete-dfs/tests -v

# 4) commit
git checkout -b codex/pete-engine-hardening
git add .
git commit -m "chore(pete): bootstrap dedicated pete-engine repo"
git push -u origin codex/pete-engine-hardening
```

## Cutover Criteria
- Pete tests pass in `pete-engine`.
- 9:00 AM pipeline run succeeds from `pete-engine`.
- Mission control reads Pete payload without local code imports.
- No secrets in repo/config/docs.

## Rollback
If cutover breaks morning run:
1. Keep running current pipeline from `agency` for that day.
2. Fix in `pete-engine`.
3. Retry cutover next run window.

## Owners
- Vlad: migration execution + CI + runtime stability.
- JJ: go/no-go checklist and daily verification.
- Jax: final cutover approval.
