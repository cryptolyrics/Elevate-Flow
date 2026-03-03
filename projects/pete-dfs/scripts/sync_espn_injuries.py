#!/usr/bin/env python3
"""
Sync daily NBA injuries from ESPN endpoints into local JSON for Pete.

Design:
- Pull today's scoreboard from ESPN.
- For each event, pull summary endpoint.
- Extract injury signals from multiple possible JSON shapes.
- Emit local file with per-team injured players + major-out team set.
"""

import argparse
import json
import time
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set

import requests

ESPN_SCOREBOARD = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={yyyymmdd}"
ESPN_SUMMARY = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary?event={event_id}"

MAJOR_OUT_TAGS = {"out", "doubtful", "inactive", "ruled out"}


def normalize_team(value: str) -> str:
    return str(value or "").strip().upper()


def safe_get_json(session: requests.Session, url: str, timeout: int = 25) -> Optional[dict]:
    try:
        resp = session.get(url, timeout=timeout)
        if resp.status_code != 200:
            return None
        payload = resp.json()
        if isinstance(payload, dict):
            return payload
    except Exception:
        return None
    return None


def extract_events(scoreboard_payload: dict) -> List[dict]:
    events = scoreboard_payload.get("events", []) if isinstance(scoreboard_payload, dict) else []
    rows: List[dict] = []
    for event in events if isinstance(events, list) else []:
        if not isinstance(event, dict):
            continue
        event_id = str(event.get("id", "")).strip()
        competitions = event.get("competitions", [])
        competition = competitions[0] if isinstance(competitions, list) and competitions else {}
        competitors = competition.get("competitors", []) if isinstance(competition, dict) else []
        home = ""
        away = ""
        for comp in competitors if isinstance(competitors, list) else []:
            if not isinstance(comp, dict):
                continue
            team = comp.get("team", {}) if isinstance(comp.get("team"), dict) else {}
            abbr = str(team.get("abbreviation", "")).strip().upper()
            if str(comp.get("homeAway", "")).lower() == "home":
                home = abbr
            elif str(comp.get("homeAway", "")).lower() == "away":
                away = abbr
        if event_id:
            rows.append({"event_id": event_id, "home": home, "away": away})
    return rows


def _collect_injuries_from_athlete(player_name: str, team: str, athlete_blob: dict) -> List[dict]:
    records: List[dict] = []
    injuries = athlete_blob.get("injuries", []) if isinstance(athlete_blob, dict) else []
    for injury in injuries if isinstance(injuries, list) else []:
        if not isinstance(injury, dict):
            continue
        status = str(injury.get("status") or injury.get("type") or "").strip()
        detail = str(injury.get("details") or injury.get("description") or "").strip()
        if not status and not detail:
            continue
        records.append(
            {
                "player": player_name,
                "team": team,
                "status": status,
                "detail": detail,
            }
        )
    return records


def extract_injuries_from_summary(summary_payload: dict, fallback_home: str = "", fallback_away: str = "") -> List[dict]:
    records: List[dict] = []

    def scan_boxscore_players() -> None:
        boxscore = summary_payload.get("boxscore", {}) if isinstance(summary_payload, dict) else {}
        teams = boxscore.get("players", []) if isinstance(boxscore, dict) else []
        for team_blob in teams if isinstance(teams, list) else []:
            if not isinstance(team_blob, dict):
                continue
            team_info = team_blob.get("team", {}) if isinstance(team_blob.get("team"), dict) else {}
            team = normalize_team(team_info.get("abbreviation") or team_info.get("shortDisplayName") or "")
            athletes = team_blob.get("statistics", []) if isinstance(team_blob.get("statistics"), list) else []
            for stat_group in athletes:
                if not isinstance(stat_group, dict):
                    continue
                for athlete in stat_group.get("athletes", []) if isinstance(stat_group.get("athletes"), list) else []:
                    if not isinstance(athlete, dict):
                        continue
                    player = athlete.get("athlete", {}) if isinstance(athlete.get("athlete"), dict) else {}
                    name = str(player.get("displayName") or player.get("shortName") or "").strip()
                    records.extend(_collect_injuries_from_athlete(name, team, athlete))
                    records.extend(_collect_injuries_from_athlete(name, team, player))

    def scan_injuries_sections() -> None:
        for key in ["injuries", "news"]:
            section = summary_payload.get(key, []) if isinstance(summary_payload, dict) else []
            for row in section if isinstance(section, list) else []:
                if not isinstance(row, dict):
                    continue
                athlete = row.get("athlete", {}) if isinstance(row.get("athlete"), dict) else {}
                team_blob = row.get("team", {}) if isinstance(row.get("team"), dict) else {}
                name = str(athlete.get("displayName") or row.get("name") or "").strip()
                team = normalize_team(team_blob.get("abbreviation") or team_blob.get("shortDisplayName") or "")
                status = str(row.get("status") or row.get("type") or "").strip()
                detail = str(row.get("description") or row.get("detail") or "").strip()
                if name and (status or detail):
                    records.append({"player": name, "team": team, "status": status, "detail": detail})

    scan_boxscore_players()
    scan_injuries_sections()

    # Fallback team assignment when ESPN omits team in injury rows.
    for record in records:
        if record.get("team"):
            continue
        text = f"{record.get('detail', '')} {record.get('status', '')}".lower()
        if "home" in text and fallback_home:
            record["team"] = fallback_home
        elif "away" in text and fallback_away:
            record["team"] = fallback_away

    # Deduplicate
    seen = set()
    deduped = []
    for rec in records:
        key = (
            rec.get("player", "").strip().lower(),
            normalize_team(rec.get("team", "")),
            rec.get("status", "").strip().lower(),
            rec.get("detail", "").strip().lower(),
        )
        if key in seen:
            continue
        seen.add(key)
        rec["team"] = normalize_team(rec.get("team", ""))
        deduped.append(rec)
    return deduped


def is_major_out(record: dict) -> bool:
    status = str(record.get("status", "")).strip().lower()
    detail = str(record.get("detail", "")).strip().lower()
    text = f"{status} {detail}"
    return any(tag in text for tag in MAJOR_OUT_TAGS)


def build_output(game_date: str, injuries: List[dict]) -> dict:
    teams: Dict[str, List[dict]] = {}
    for row in injuries:
        team = normalize_team(row.get("team", ""))
        if not team:
            continue
        teams.setdefault(team, []).append(
            {
                "player": row.get("player", ""),
                "status": row.get("status", ""),
                "detail": row.get("detail", ""),
                "major_out": is_major_out(row),
            }
        )

    major_out_teams = sorted([team for team, items in teams.items() if any(item.get("major_out") for item in items)])

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "date": game_date,
        "source": "espn",
        "teams": teams,
        "major_out_teams": major_out_teams,
    }


def sync_espn_injuries(target_date: str, out_path: Path, sleep_ms: int = 120) -> Path:
    yyyymmdd = target_date.replace("-", "")
    with requests.Session() as session:
        session.headers.update({"User-Agent": "elevate-flow-pete-injury-sync/1.0"})
        scoreboard = safe_get_json(session, ESPN_SCOREBOARD.format(yyyymmdd=yyyymmdd))
        events = extract_events(scoreboard or {})
        records: List[dict] = []
        for event in events:
            summary = safe_get_json(session, ESPN_SUMMARY.format(event_id=event["event_id"]))
            if summary:
                records.extend(
                    extract_injuries_from_summary(
                        summary,
                        fallback_home=normalize_team(event.get("home", "")),
                        fallback_away=normalize_team(event.get("away", "")),
                    )
                )
            if sleep_ms > 0:
                time.sleep(sleep_ms / 1000.0)

    payload = build_output(target_date, records)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync daily ESPN NBA injuries for Pete")
    parser.add_argument("--date", default=date.today().isoformat(), help="Date (YYYY-MM-DD)")
    parser.add_argument(
        "--out",
        default=str(Path.cwd() / "projects" / "pete-dfs" / "data-lake" / "nba" / "injuries" / "latest.json"),
        help="Output JSON path",
    )
    parser.add_argument("--sleep-ms", type=int, default=120, help="Delay between ESPN event calls")
    args = parser.parse_args()

    output = sync_espn_injuries(target_date=args.date, out_path=Path(args.out), sleep_ms=max(0, args.sleep_ms))
    print(f"Wrote ESPN injuries: {output}")


if __name__ == "__main__":
    main()
