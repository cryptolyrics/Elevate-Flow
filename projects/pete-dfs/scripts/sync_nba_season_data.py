#!/usr/bin/env python3
"""
Sync NBA season data into a local lake for Pete.

Goals:
- Minimize external calls during daily Pete runs.
- Keep full-season schedule + per-game boxscore + per-game play-by-play locally.
- Support weekly Tuesday incremental updates.

Data Sources:
- Schedule: data.nba.com scoreboard endpoint
- Boxscore/PBP: cdn.nba.com liveData endpoints
"""

import argparse
import json
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import requests

SCOREBOARD_URL = "https://data.nba.com/data/10s/prod/v2/{yyyymmdd}/scoreboard.json"
BOXSCORE_URL = "https://cdn.nba.com/static/json/liveData/boxscore/boxscore_{game_id}.json"
PBP_URL = "https://cdn.nba.com/static/json/liveData/playbyplay/playbyplay_{game_id}.json"


@dataclass
class SyncPaths:
    root: Path
    season_dir: Path
    raw_boxscore_dir: Path
    raw_pbp_dir: Path
    processed_boxscore_dir: Path
    processed_pbp_dir: Path
    manifest_path: Path
    schedule_path: Path


def season_label(start_year: int) -> str:
    return f"{start_year}-{str(start_year + 1)[-2:]}"


def default_season_start_year(today: Optional[date] = None) -> int:
    today = today or date.today()
    return today.year if today.month >= 7 else today.year - 1


def season_date_bounds(start_year: int) -> Tuple[date, date]:
    # Includes preseason through finals window.
    return (date(start_year, 9, 25), date(start_year + 1, 6, 30))


def daterange(start: date, end: date) -> Iterable[date]:
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def build_paths(root: Path, start_year: int) -> SyncPaths:
    season = season_label(start_year)
    season_dir = root / "nba" / f"season={season}"
    raw_dir = season_dir / "raw"
    processed_dir = season_dir / "processed"
    return SyncPaths(
        root=root,
        season_dir=season_dir,
        raw_boxscore_dir=raw_dir / "boxscore",
        raw_pbp_dir=raw_dir / "playbyplay",
        processed_boxscore_dir=processed_dir / "player_boxscore_jsonl",
        processed_pbp_dir=processed_dir / "play_by_play_jsonl",
        manifest_path=season_dir / "sync-manifest.json",
        schedule_path=season_dir / "schedule.json",
    )


def ensure_dirs(paths: SyncPaths) -> None:
    for target in [
        paths.season_dir,
        paths.raw_boxscore_dir,
        paths.raw_pbp_dir,
        paths.processed_boxscore_dir,
        paths.processed_pbp_dir,
    ]:
        target.mkdir(parents=True, exist_ok=True)


def fetch_json(session: requests.Session, url: str, timeout: int = 30) -> Optional[dict]:
    try:
        resp = session.get(url, timeout=timeout)
        if resp.status_code != 200:
            return None
        payload = resp.json()
        if isinstance(payload, dict):
            return payload
        return None
    except Exception:
        return None


def parse_schedule_games(payload: dict, game_date: str) -> List[dict]:
    rows = []
    games = payload.get("games", []) if isinstance(payload, dict) else []
    for game in games if isinstance(games, list) else []:
        if not isinstance(game, dict):
            continue
        rows.append(
            {
                "game_id": str(game.get("gameId", "")).strip(),
                "game_date": game_date,
                "status_num": game.get("statusNum"),
                "status_text": game.get("statusText"),
                "home_team": game.get("hTeam", {}).get("triCode") if isinstance(game.get("hTeam"), dict) else "",
                "away_team": game.get("vTeam", {}).get("triCode") if isinstance(game.get("vTeam"), dict) else "",
            }
        )
    return [row for row in rows if row.get("game_id")]


def collect_schedule(session: requests.Session, start_year: int, sleep_ms: int = 120) -> List[dict]:
    start, end = season_date_bounds(start_year)
    schedule_rows: List[dict] = []

    for day in daterange(start, end):
        yyyymmdd = day.strftime("%Y%m%d")
        payload = fetch_json(session, SCOREBOARD_URL.format(yyyymmdd=yyyymmdd))
        if payload:
            schedule_rows.extend(parse_schedule_games(payload, day.isoformat()))
        if sleep_ms > 0:
            time.sleep(sleep_ms / 1000.0)

    deduped: Dict[str, dict] = {}
    for row in schedule_rows:
        deduped[row["game_id"]] = row
    rows = list(deduped.values())
    rows.sort(key=lambda item: (item["game_date"], item["game_id"]))
    return rows


def load_manifest(path: Path) -> dict:
    if not path.exists():
        return {"games": {}, "meta": {"updated_at": ""}}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            payload.setdefault("games", {})
            payload.setdefault("meta", {})
            return payload
    except Exception:
        pass
    return {"games": {}, "meta": {"updated_at": ""}}


def save_manifest(path: Path, manifest: dict) -> None:
    manifest.setdefault("meta", {})["updated_at"] = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def flatten_boxscore(payload: dict, game_id: str, game_date: str) -> List[dict]:
    game = payload.get("game", {}) if isinstance(payload, dict) else {}
    teams = game.get("homeTeam", {}), game.get("awayTeam", {})
    rows: List[dict] = []
    for team in teams:
        players = team.get("players", []) if isinstance(team, dict) else []
        team_code = team.get("teamTricode", "")
        for player in players if isinstance(players, list) else []:
            if not isinstance(player, dict):
                continue
            stats = player.get("statistics", {}) if isinstance(player.get("statistics"), dict) else {}
            rows.append(
                {
                    "game_id": game_id,
                    "game_date": game_date,
                    "team": team_code,
                    "player_id": player.get("personId"),
                    "player_name": player.get("name"),
                    "minutes": stats.get("minutes"),
                    "points": stats.get("points"),
                    "rebounds": stats.get("reboundsTotal"),
                    "assists": stats.get("assists"),
                    "steals": stats.get("steals"),
                    "three_pm": stats.get("threePointersMade"),
                    "turnovers": stats.get("turnovers"),
                }
            )
    return rows


def flatten_playbyplay(payload: dict, game_id: str, game_date: str) -> List[dict]:
    game = payload.get("game", {}) if isinstance(payload, dict) else {}
    actions = game.get("actions", []) if isinstance(game, dict) else []
    rows: List[dict] = []
    for action in actions if isinstance(actions, list) else []:
        if not isinstance(action, dict):
            continue
        rows.append(
            {
                "game_id": game_id,
                "game_date": game_date,
                "action_number": action.get("actionNumber"),
                "period": action.get("period"),
                "clock": action.get("clock"),
                "team_id": action.get("teamId"),
                "player_id": action.get("personId"),
                "action_type": action.get("actionType"),
                "sub_type": action.get("subType"),
                "description": action.get("description"),
                "x_legacy": action.get("xLegacy"),
                "y_legacy": action.get("yLegacy"),
                "shot_result": action.get("shotResult"),
                "points_total": action.get("pointsTotal"),
            }
        )
    return rows


def write_jsonl(path: Path, rows: List[dict]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")


def target_game_ids(schedule: List[dict], manifest: dict, weekly: bool, lookback_days: int) -> List[str]:
    if not weekly:
        return [row["game_id"] for row in schedule]

    cutoff = date.today() - timedelta(days=lookback_days)
    selected: List[str] = []
    for row in schedule:
        game_id = row["game_id"]
        game_date = datetime.strptime(row["game_date"], "%Y-%m-%d").date()
        status_num = int(row.get("status_num") or 0)
        existing = manifest.get("games", {}).get(game_id, {})
        has_all = bool(existing.get("boxscore")) and bool(existing.get("playbyplay"))
        needs_recent_refresh = game_date >= cutoff
        not_final = status_num < 3
        if needs_recent_refresh or not has_all or not_final:
            selected.append(game_id)
    return selected


def sync_games(
    session: requests.Session,
    schedule: List[dict],
    manifest: dict,
    paths: SyncPaths,
    weekly: bool,
    lookback_days: int,
    overwrite: bool,
    sleep_ms: int = 120,
) -> dict:
    index_by_id = {row["game_id"]: row for row in schedule}
    ids = target_game_ids(schedule, manifest, weekly=weekly, lookback_days=lookback_days)
    games_state = manifest.setdefault("games", {})

    for game_id in ids:
        game_row = index_by_id.get(game_id, {})
        game_date = game_row.get("game_date", "")

        boxscore_raw_path = paths.raw_boxscore_dir / f"{game_id}.json"
        pbp_raw_path = paths.raw_pbp_dir / f"{game_id}.json"
        boxscore_jsonl_path = paths.processed_boxscore_dir / f"{game_id}.jsonl"
        pbp_jsonl_path = paths.processed_pbp_dir / f"{game_id}.jsonl"

        state = games_state.setdefault(game_id, {"boxscore": False, "playbyplay": False, "last_sync": ""})

        if overwrite or not boxscore_raw_path.exists():
            box_payload = fetch_json(session, BOXSCORE_URL.format(game_id=game_id))
            if box_payload:
                write_json(boxscore_raw_path, box_payload)
                rows = flatten_boxscore(box_payload, game_id, game_date)
                write_jsonl(boxscore_jsonl_path, rows)
                state["boxscore"] = True

        if overwrite or not pbp_raw_path.exists():
            pbp_payload = fetch_json(session, PBP_URL.format(game_id=game_id))
            if pbp_payload:
                write_json(pbp_raw_path, pbp_payload)
                rows = flatten_playbyplay(pbp_payload, game_id, game_date)
                write_jsonl(pbp_jsonl_path, rows)
                state["playbyplay"] = True

        state["last_sync"] = datetime.utcnow().isoformat(timespec="seconds") + "Z"
        if sleep_ms > 0:
            time.sleep(sleep_ms / 1000.0)

    return manifest


def run_sync(
    start_year: int,
    data_root: Path,
    weekly: bool,
    lookback_days: int,
    overwrite: bool,
    sleep_ms: int,
) -> SyncPaths:
    paths = build_paths(data_root, start_year)
    ensure_dirs(paths)

    with requests.Session() as session:
        session.headers.update({"User-Agent": "elevate-flow-pete-sync/1.0"})
        schedule = collect_schedule(session, start_year, sleep_ms=sleep_ms)
        paths.schedule_path.write_text(json.dumps({"season": season_label(start_year), "games": schedule}, indent=2), encoding="utf-8")

        manifest = load_manifest(paths.manifest_path)
        manifest = sync_games(
            session,
            schedule,
            manifest,
            paths,
            weekly=weekly,
            lookback_days=lookback_days,
            overwrite=overwrite,
            sleep_ms=sleep_ms,
        )
        save_manifest(paths.manifest_path, manifest)

    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync NBA season data for Pete local analytics")
    parser.add_argument("--season-start-year", type=int, default=default_season_start_year(), help="NBA season start year (e.g., 2025 for 2025-26)")
    parser.add_argument(
        "--data-root",
        default=str(Path.cwd() / "projects" / "pete-dfs" / "data-lake"),
        help="Root directory for local data lake",
    )
    parser.add_argument("--weekly", action="store_true", help="Weekly incremental sync mode (Tuesday-friendly)")
    parser.add_argument("--lookback-days", type=int, default=10, help="Lookback window for weekly refresh")
    parser.add_argument("--overwrite", action="store_true", help="Force re-download of raw payloads")
    parser.add_argument("--sleep-ms", type=int, default=120, help="Delay between API calls (ms)")
    args = parser.parse_args()

    paths = run_sync(
        start_year=args.season_start_year,
        data_root=Path(args.data_root),
        weekly=args.weekly,
        lookback_days=args.lookback_days,
        overwrite=args.overwrite,
        sleep_ms=max(0, args.sleep_ms),
    )

    print(f"Synced season data into: {paths.season_dir}")
    print(f"Schedule: {paths.schedule_path}")
    print(f"Manifest: {paths.manifest_path}")


if __name__ == "__main__":
    main()
