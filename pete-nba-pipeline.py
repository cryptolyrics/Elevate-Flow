#!/usr/bin/env python3
"""
Pete's Daily NBA Pipeline

Current mode:
- Data source: API-Sports (NBA) + optional Draftstars CSV input
- Wagering output: fail-closed by default until quant controls are enabled

Environment:
- NBA_API_KEY (required for API calls)
- NBA_API_BASE_URL (optional, default: https://v2.nba.api-sports.io)
- OPENCLAW_WORKSPACE (optional, default: ./.pete-workspace)
- PETE_ENABLE_WAGERING=1 to allow bet recommendations
- PETE_QUANT_RULES_PATH (optional) custom quant rules JSON path
- PETE_LEARNING_STATE_PATH (optional) custom learning state JSON path
- PETE_MAJOR_OUTS_PATH (optional) JSON file of major injury outs
"""

import argparse
import csv
import json
import math
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set

import requests

WORKSPACE = Path(os.environ.get("OPENCLAW_WORKSPACE", str(Path.cwd() / ".pete-workspace")))
LOG_DIR = WORKSPACE / "logs" / "Pete"
TODAY = datetime.now().strftime("%Y-%m-%d")
DEFAULT_SEASON = str(datetime.now().year)
NBA_API_BASE_URL = os.environ.get("NBA_API_BASE_URL", "https://v2.nba.api-sports.io").rstrip("/")
NBA_API_TIMEOUT = int(os.environ.get("NBA_API_TIMEOUT", "30"))


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def normalize_team_key(name: str) -> str:
    return str(name or "").strip().lower()


def safe_float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def load_env_secrets() -> str:
    """Load secrets from ~/.env.pete and return NBA API key."""
    env_file = Path.home() / ".env.pete"
    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    key, val = line.split("=", 1)
                    os.environ[key] = val

    return os.environ.get("NBA_API_KEY", "")


def api_sports_get(path: str, params: dict) -> dict:
    api_key = os.environ.get("NBA_API_KEY", "")
    if not api_key:
        return {"response": [], "errors": {"auth": "NBA_API_KEY missing"}}

    url = f"{NBA_API_BASE_URL}/{path.lstrip('/')}"
    headers = {
        "x-apisports-key": api_key,
        "Accept": "application/json",
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=NBA_API_TIMEOUT)
        if response.status_code != 200:
            return {
                "response": [],
                "errors": {"http": f"status={response.status_code}", "body": response.text[:500]},
            }

        data = response.json()
        if not isinstance(data, dict):
            return {"response": [], "errors": {"format": "non-object response"}}
        return data
    except Exception as exc:
        return {"response": [], "errors": {"exception": str(exc)}}


def _response_list(payload: dict) -> list:
    values = payload.get("response", [])
    if isinstance(values, list):
        return values
    return []


def _parse_time(value: str) -> Optional[datetime]:
    if not value:
        return None
    text = str(value).strip()
    if not text:
        return None

    formats = [
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%H:%M",
    ]
    for fmt in formats:
        try:
            parsed = datetime.strptime(text, fmt)
            if fmt == "%H:%M":
                today = datetime.now()
                parsed = parsed.replace(year=today.year, month=today.month, day=today.day)
            return parsed
        except Exception:
            continue

    return None


def fetch_nba_games(season: str, date: str) -> dict:
    """Fetch game slate from API-Sports."""
    payload = api_sports_get("games", {"season": season, "date": date})
    rows = _response_list(payload)

    games = []
    for row in rows:
        teams = row.get("teams", {}) if isinstance(row, dict) else {}
        home = teams.get("home", {}) if isinstance(teams, dict) else {}
        away = teams.get("visitors", {}) if isinstance(teams, dict) else {}
        status = row.get("status", {}) if isinstance(row, dict) else {}

        games.append(
            {
                "game_id": row.get("id"),
                "home_team": home.get("code") or home.get("name") or "",
                "away_team": away.get("code") or away.get("name") or "",
                "home_name": home.get("name") or "",
                "away_name": away.get("name") or "",
                "home_code": home.get("code") or "",
                "away_code": away.get("code") or "",
                "status": status.get("long") or status.get("short") or "",
                "start_time": row.get("date") or "",
            }
        )

    note = f"Found {len(games)} games"
    if payload.get("errors"):
        note = f"{note}; errors={payload.get('errors')}"

    return {"games": games, "note": note}


def fetch_nba_odds(date: str, season: str) -> dict:
    """Fetch odds from API-Sports and normalize to internal shape."""
    payload = api_sports_get("odds", {"date": date, "season": season})
    rows = _response_list(payload)

    games = []
    for row in rows:
        if not isinstance(row, dict):
            continue

        teams_blob = row.get("teams", {}) if isinstance(row.get("teams"), dict) else {}
        home_blob = teams_blob.get("home", {}) if isinstance(teams_blob, dict) else {}
        away_blob = teams_blob.get("visitors", {}) if isinstance(teams_blob, dict) else {}

        home_name = home_blob.get("name") or row.get("home") or ""
        away_name = away_blob.get("name") or row.get("away") or ""

        normalized = {
            "home": home_name,
            "away": away_name,
            "home_code": home_blob.get("code") or "",
            "away_code": away_blob.get("code") or "",
            "start": row.get("date"),
            "odds": {},
        }

        bookmakers = row.get("bookmakers", [])
        if isinstance(bookmakers, list):
            for book in bookmakers:
                bets = book.get("bets", []) if isinstance(book, dict) else []
                for bet in bets:
                    values = bet.get("values", []) if isinstance(bet, dict) else []
                    for value in values:
                        team = value.get("value") if isinstance(value, dict) else None
                        odd_raw = value.get("odd") if isinstance(value, dict) else None
                        if not team or odd_raw is None:
                            continue
                        odd = safe_float(odd_raw, 0.0)
                        if odd <= 1.0:
                            continue
                        previous = normalized["odds"].get(team)
                        if previous is None or odd > previous:
                            normalized["odds"][team] = odd

        if normalized["odds"]:
            games.append(normalized)

    note = f"Found odds for {len(games)} games"
    if payload.get("errors"):
        note = f"{note}; errors={payload.get('errors')}"

    return {"games": games, "note": note}


def _candidate_rules_paths() -> List[Path]:
    script_dir = Path(__file__).resolve().parent
    return [
        Path(os.environ.get("PETE_QUANT_RULES_PATH", "")),
        script_dir.parent / "config" / "quant_rules.json",
        Path.cwd() / "projects" / "pete-dfs" / "config" / "quant_rules.json",
    ]


def _candidate_major_outs_paths() -> List[Path]:
    script_dir = Path(__file__).resolve().parent
    return [
        Path(os.environ.get("PETE_MAJOR_OUTS_PATH", "")),
        script_dir.parent / "config" / "major_outs.json",
        Path.cwd() / "projects" / "pete-dfs" / "config" / "major_outs.json",
    ]


def learning_state_path() -> Path:
    env = os.environ.get("PETE_LEARNING_STATE_PATH", "").strip()
    if env:
        return Path(env)
    return LOG_DIR / "learning_state.json"


def load_quant_rules() -> dict:
    defaults = {
        "enabled": False,
        "min_edge_pct": 0.03,
        "min_model_prob": 0.52,
        "min_edge_dollars_per_1u": 0.40,
        "home_team_model_boost_pct": 0.10,
        "max_single_bet_decimal_odds": 3.0,
        "max_parlay_legs": 3,
        "smokie_percentile": 0.35,
        "smokie_min_projection_delta": 1.0,
        "prop_call_haircut_pct": 0.10,
        "prop_min_line_edge": 0.35,
        "prop_min_model_edge_pct": 0.03,
        "prop_max_legs": 3,
        "prop_trend_weight": 0.35,
        "prop_market_prior_weight": 0.25,
    }

    for candidate in _candidate_rules_paths():
        if not candidate or str(candidate).strip() == "":
            continue
        if candidate.exists():
            try:
                parsed = json.loads(candidate.read_text(encoding="utf-8"))
                if isinstance(parsed, dict):
                    defaults.update(parsed)
                break
            except Exception:
                pass

    return defaults


def load_major_out_teams(override_path: Optional[str] = None) -> Set[str]:
    candidates: List[Path] = []
    if override_path:
        candidates.append(Path(override_path))
    candidates.extend(_candidate_major_outs_paths())

    for candidate in candidates:
        if not candidate or str(candidate).strip() == "":
            continue
        if not candidate.exists():
            continue

        try:
            parsed = json.loads(candidate.read_text(encoding="utf-8"))
        except Exception:
            continue

        values: List[str] = []
        if isinstance(parsed, dict):
            teams = parsed.get("teams", [])
            if isinstance(teams, list):
                values.extend(str(v) for v in teams)
            for team, is_out in parsed.get("flags", {}).items() if isinstance(parsed.get("flags"), dict) else []:
                if bool(is_out):
                    values.append(str(team))
        elif isinstance(parsed, list):
            values.extend(str(v) for v in parsed)

        return {normalize_team_key(v) for v in values if str(v).strip()}

    return set()


def default_prop_market_stats() -> dict:
    return {
        "PTS": {"over_hits": 1, "over_misses": 1, "under_hits": 1, "under_misses": 1},
        "REB": {"over_hits": 1, "over_misses": 1, "under_hits": 1, "under_misses": 1},
        "AST": {"over_hits": 1, "over_misses": 1, "under_hits": 1, "under_misses": 1},
        "STL": {"over_hits": 1, "over_misses": 1, "under_hits": 1, "under_misses": 1},
        "3PM": {"over_hits": 1, "over_misses": 1, "under_hits": 1, "under_misses": 1},
    }


def _coerce_market_stats(raw: dict) -> dict:
    base = default_prop_market_stats()
    if not isinstance(raw, dict):
        return base

    for market, values in raw.items():
        key = normalize_market(market)
        if key not in base or not isinstance(values, dict):
            continue
        for field in ["over_hits", "over_misses", "under_hits", "under_misses"]:
            base[key][field] = int(max(0, safe_float(values.get(field), base[key][field])))
    return base


def load_learning_state() -> dict:
    defaults = {
        "player_adjustments": {},
        "team_adjustments": {},
        "player_prop_adjustments": {},
        "player_prop_opp_adjustments": {},
        "prop_market_stats": default_prop_market_stats(),
        "meta": {"dfs_samples": 0, "bet_samples": 0, "prop_samples": 0, "updated_at": "", "last_feedback_file": ""},
    }

    path = learning_state_path()
    if not path.exists():
        return defaults

    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(parsed, dict):
            defaults.update(parsed)
            if not isinstance(defaults.get("player_adjustments"), dict):
                defaults["player_adjustments"] = {}
            if not isinstance(defaults.get("team_adjustments"), dict):
                defaults["team_adjustments"] = {}
            if not isinstance(defaults.get("player_prop_adjustments"), dict):
                defaults["player_prop_adjustments"] = {}
            if not isinstance(defaults.get("player_prop_opp_adjustments"), dict):
                defaults["player_prop_opp_adjustments"] = {}
            defaults["prop_market_stats"] = _coerce_market_stats(defaults.get("prop_market_stats"))
            if not isinstance(defaults.get("meta"), dict):
                defaults["meta"] = {
                    "dfs_samples": 0,
                    "bet_samples": 0,
                    "prop_samples": 0,
                    "updated_at": "",
                    "last_feedback_file": "",
                }
    except Exception:
        return defaults

    return defaults


def save_learning_state(state: dict) -> None:
    path = learning_state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    state.setdefault("meta", {})["updated_at"] = datetime.now().isoformat(timespec="seconds")
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")


def update_learning_state_from_feedback(state: dict, feedback_path: Optional[str]) -> dict:
    if not feedback_path:
        return state

    path = Path(feedback_path)
    if not path.exists():
        return state

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return state

    dfs_samples = payload.get("dfs", []) if isinstance(payload, dict) else []
    bet_samples = payload.get("bets", []) if isinstance(payload, dict) else []
    prop_samples = payload.get("props", []) if isinstance(payload, dict) else []

    player_adj = state.setdefault("player_adjustments", {})
    team_adj = state.setdefault("team_adjustments", {})
    prop_adj = state.setdefault("player_prop_adjustments", {})
    prop_opp_adj = state.setdefault("player_prop_opp_adjustments", {})
    market_stats = _coerce_market_stats(state.get("prop_market_stats"))
    state["prop_market_stats"] = market_stats
    meta = state.setdefault("meta", {})

    learning_rate_dfs = 0.08
    learning_rate_bet = 0.06

    for sample in dfs_samples if isinstance(dfs_samples, list) else []:
        if not isinstance(sample, dict):
            continue
        player = str(sample.get("player", "")).strip()
        projected = safe_float(sample.get("projected_fp"), 0.0)
        actual = safe_float(sample.get("actual_fp"), 0.0)
        if not player:
            continue

        error = actual - projected
        current = safe_float(player_adj.get(player, 0.0), 0.0)
        player_adj[player] = round(clamp(current + learning_rate_dfs * error, -8.0, 8.0), 4)
        meta["dfs_samples"] = int(meta.get("dfs_samples", 0)) + 1

    for sample in bet_samples if isinstance(bet_samples, list) else []:
        if not isinstance(sample, dict):
            continue
        team = str(sample.get("team", "")).strip()
        model_prob = safe_float(sample.get("model_prob"), 0.5)
        won = 1.0 if bool(sample.get("won", False)) else 0.0
        if not team:
            continue

        calibration_error = won - clamp(model_prob, 0.01, 0.99)
        key = normalize_team_key(team)
        current = safe_float(team_adj.get(key, 0.0), 0.0)
        team_adj[key] = round(clamp(current + learning_rate_bet * calibration_error, -0.12, 0.12), 6)
        meta["bet_samples"] = int(meta.get("bet_samples", 0)) + 1

    learning_rate_prop = 0.08
    for sample in prop_samples if isinstance(prop_samples, list) else []:
        if not isinstance(sample, dict):
            continue
        player = str(sample.get("player", "")).strip()
        market = normalize_market(sample.get("market"))
        projected = safe_float(sample.get("projected"), 0.0)
        actual = safe_float(sample.get("actual"), 0.0)
        if not player or not market:
            continue

        key = f"{player.lower()}::{market}"
        error = actual - projected
        current = safe_float(prop_adj.get(key, 0.0), 0.0)
        prop_adj[key] = round(clamp(current + learning_rate_prop * error, -3.0, 3.0), 4)

        opponent = normalize_team_key(sample.get("opponent", ""))
        if opponent:
            opp_key = f"{player.lower()}::{opponent}::{market}"
            opp_current = safe_float(prop_opp_adj.get(opp_key, 0.0), 0.0)
            prop_opp_adj[opp_key] = round(clamp(opp_current + (0.10 * error), -2.5, 2.5), 4)

        direction = str(sample.get("direction", "")).strip().upper()
        line = safe_float(sample.get("line"), math.nan)
        won_value = sample.get("won")
        if won_value is None and direction in {"OVER", "UNDER"} and not math.isnan(line):
            if direction == "OVER":
                won_value = actual > line
            else:
                won_value = actual < line

        if direction in {"OVER", "UNDER"} and won_value is not None:
            stats = market_stats.setdefault(
                market, {"over_hits": 1, "over_misses": 1, "under_hits": 1, "under_misses": 1}
            )
            if direction == "OVER":
                key_name = "over_hits" if bool(won_value) else "over_misses"
            else:
                key_name = "under_hits" if bool(won_value) else "under_misses"
            stats[key_name] = int(stats.get(key_name, 0)) + 1

        meta["prop_samples"] = int(meta.get("prop_samples", 0)) + 1

    if feedback_path:
        meta["last_feedback_file"] = str(Path(feedback_path))

    return state


def _split_positions(value: str) -> List[str]:
    text = str(value or "").replace(" ", "")
    if not text:
        return []
    return [part for part in text.split("/") if part]


def _draftstars_slot_filter(players: List[dict], slot: str) -> List[dict]:
    if slot == "all":
        return players

    with_times = [p for p in players if p.get("start_dt") is not None]
    if not with_times:
        return players

    sorted_times = sorted(p["start_dt"] for p in with_times)
    pivot = sorted_times[len(sorted_times) // 2]

    if slot == "early":
        return [p for p in players if p.get("start_dt") is None or p["start_dt"] <= pivot]
    return [p for p in players if p.get("start_dt") is None or p["start_dt"] > pivot]


def load_draftstars_players(csv_path: str, slot: str, learning_state: dict) -> List[dict]:
    path = Path(csv_path)
    if not path.exists():
        return []

    rows: List[dict] = []
    player_adj = learning_state.get("player_adjustments", {}) if isinstance(learning_state, dict) else {}

    with path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for raw in reader:
            status = str(raw.get("Playing Status", "")).upper()
            if "OUT" in status or "QUESTIONABLE" in status:
                continue

            salary = int(safe_float(raw.get("Salary"), 0.0))
            if salary <= 0:
                continue

            fppg = safe_float(raw.get("FPPG"), 0.0)
            form = safe_float(raw.get("Form"), fppg)
            name = str(raw.get("Name", "")).strip()
            team = str(raw.get("Team", "")).strip()
            positions = _split_positions(raw.get("Position", ""))
            if not name or not positions:
                continue

            start_raw = raw.get("Start") or raw.get("Start Time") or raw.get("Game Start") or ""
            start_dt = _parse_time(start_raw)

            adjustment = safe_float(player_adj.get(name, 0.0), 0.0)
            projected = (0.65 * form) + (0.35 * fppg) + adjustment
            projected = round(max(projected, 0.0), 3)

            rows.append(
                {
                    "name": name,
                    "team": team,
                    "positions": positions,
                    "salary": salary,
                    "fppg": round(fppg, 3),
                    "form": round(form, 3),
                    "projected": projected,
                    "value_score": round((projected / salary) * 1000.0, 4),
                    "start_dt": start_dt,
                }
            )

    return _draftstars_slot_filter(rows, slot)


def _lineup_optimizer(players: List[dict], salary_cap: int = 100000) -> List[dict]:
    slot_order = ["PG", "PG", "SG", "SG", "SF", "SF", "PF", "PF", "C"]

    candidates_by_slot: Dict[str, List[dict]] = {}
    for slot in set(slot_order):
        candidates = [p for p in players if slot in p.get("positions", [])]
        candidates.sort(key=lambda p: (p["projected"], p["value_score"]), reverse=True)
        candidates_by_slot[slot] = candidates[:22]

    for slot in set(slot_order):
        if not candidates_by_slot.get(slot):
            return []

    best_lineup: List[dict] = []
    best_projection = -1.0

    def dfs(idx: int, chosen: List[dict], used_names: Set[str], salary_used: int, projection_sum: float) -> None:
        nonlocal best_lineup, best_projection

        if salary_used > salary_cap:
            return

        if idx == len(slot_order):
            if projection_sum > best_projection:
                best_projection = projection_sum
                best_lineup = chosen.copy()
            return

        slot = slot_order[idx]
        remaining_slots = slot_order[idx:]
        optimistic_remaining = 0.0
        for rem in remaining_slots:
            top = candidates_by_slot.get(rem, [])
            if top:
                optimistic_remaining += top[0]["projected"]
        if projection_sum + optimistic_remaining <= best_projection:
            return

        for player in candidates_by_slot.get(slot, []):
            if player["name"] in used_names:
                continue

            used_names.add(player["name"])
            chosen.append({**player, "slot": slot})
            dfs(
                idx + 1,
                chosen,
                used_names,
                salary_used + player["salary"],
                projection_sum + player["projected"],
            )
            chosen.pop()
            used_names.remove(player["name"])

    dfs(0, [], set(), 0, 0.0)
    return best_lineup


def find_smokies(players: List[dict], rules: dict) -> List[dict]:
    if not players:
        return []

    sorted_salaries = sorted(p["salary"] for p in players)
    pct = clamp(safe_float(rules.get("smokie_percentile", 0.35), 0.35), 0.1, 0.6)
    index = max(0, min(len(sorted_salaries) - 1, int((len(sorted_salaries) - 1) * pct)))
    salary_cutoff = sorted_salaries[index]
    min_delta = safe_float(rules.get("smokie_min_projection_delta", 1.0), 1.0)

    candidates = []
    for player in players:
        if player["salary"] > salary_cutoff:
            continue
        delta = player["projected"] - player["fppg"]
        if delta < min_delta:
            continue
        score = delta + (0.25 * player["value_score"])
        candidates.append(
            {
                "player": player["name"],
                "team": player["team"],
                "salary": player["salary"],
                "fppg": player["fppg"],
                "projected": player["projected"],
                "delta": round(delta, 3),
                "value_score": player["value_score"],
                "score": round(score, 3),
            }
        )

    candidates.sort(key=lambda item: (item["score"], item["projected"]), reverse=True)
    return candidates[:3]


def build_best_lineup(
    _games_data: dict,
    draftstars_csv: Optional[str] = None,
    slot: str = "all",
    learning_state: Optional[dict] = None,
    rules: Optional[dict] = None,
) -> dict:
    if not draftstars_csv:
        return {
            "lineup": [],
            "format": "draftstars-classic",
            "total_salary": 0,
            "projected_points": 0,
            "smokies": [],
            "projection_map": {},
            "note": "No Draftstars CSV supplied. Pass --draftstars-csv to build lineup.",
        }

    state = learning_state or load_learning_state()
    quant_rules = rules or load_quant_rules()

    players = load_draftstars_players(draftstars_csv, slot, state)
    if not players:
        return {
            "lineup": [],
            "format": "draftstars-classic",
            "total_salary": 0,
            "projected_points": 0,
            "smokies": [],
            "projection_map": {},
            "note": "No eligible players after filtering.",
        }

    lineup = _lineup_optimizer(players)
    smokies = find_smokies(players, quant_rules)

    if not lineup:
        return {
            "lineup": [],
            "format": "draftstars-classic",
            "total_salary": 0,
            "projected_points": 0,
            "smokies": smokies,
            "projection_map": {p["name"].lower(): p["projected"] for p in players},
            "note": "Optimization failed to find a valid lineup under constraints.",
        }

    total_salary = sum(player["salary"] for player in lineup)
    projected_points = sum(player["projected"] for player in lineup)
    lineup_rows = [
        {
            "slot": player["slot"],
            "name": player["name"],
            "team": player["team"],
            "salary": player["salary"],
            "projected": player["projected"],
            "fppg": player["fppg"],
        }
        for player in lineup
    ]

    return {
        "lineup": lineup_rows,
        "format": "draftstars-classic-2-2-2-2-1",
        "total_salary": total_salary,
        "projected_points": round(projected_points, 3),
        "smokies": smokies,
        "projection_map": {p["name"].lower(): p["projected"] for p in players},
        "note": f"Optimized from CSV using slot={slot}",
    }


def get_pivots(lineup: dict) -> List[dict]:
    smokies = lineup.get("smokies", []) if isinstance(lineup, dict) else []
    if len(smokies) >= 2:
        return [
            {
                "player": smokies[0]["player"],
                "reason": f"Smokie candidate: +{smokies[0]['delta']} vs FPPG at ${smokies[0]['salary']}",
            },
            {
                "player": smokies[1]["player"],
                "reason": f"Smokie candidate: +{smokies[1]['delta']} vs FPPG at ${smokies[1]['salary']}",
            },
        ]

    return [
        {"player": "TBD", "reason": "Awaiting stronger value delta from live slate"},
        {"player": "TBD", "reason": "Awaiting late injury confirmation"},
    ]


def decimal_to_aus(decimal_odds: float) -> str:
    if decimal_odds >= 2:
        return f"+{int((decimal_odds - 1) * 100)}"
    return f"-{int(100 / (decimal_odds - 1))}"


def wagering_enabled(rules: dict) -> bool:
    env_enabled = os.environ.get("PETE_ENABLE_WAGERING", "0") == "1"
    rules_enabled = bool(rules.get("enabled", False))
    return env_enabled and rules_enabled


def fetch_teams_played_on_date(season: str, date: str) -> Set[str]:
    if not date:
        return set()

    payload = fetch_nba_games(season, date)
    teams = set()
    for game in payload.get("games", []):
        for key in ["home_team", "away_team", "home_name", "away_name", "home_code", "away_code"]:
            value = game.get(key)
            if value:
                teams.add(normalize_team_key(value))
    return teams


def team_is_blocked(team: str, blocked_set: Set[str]) -> bool:
    return normalize_team_key(team) in blocked_set


def candidate_expected_return(model_prob: float, odds: float) -> float:
    return (model_prob * odds) - 1.0


def _is_home_team(team: str, game: dict) -> bool:
    key = normalize_team_key(team)
    return key in {normalize_team_key(game.get("home")), normalize_team_key(game.get("home_code"))}


def model_probability_for_team(team: str, game: dict, implied_prob: float, learning_state: dict, rules: dict) -> float:
    model = implied_prob
    if _is_home_team(team, game):
        model *= 1.0 + safe_float(rules.get("home_team_model_boost_pct", 0.10), 0.10)

    team_adjustments = learning_state.get("team_adjustments", {}) if isinstance(learning_state, dict) else {}
    model += safe_float(team_adjustments.get(normalize_team_key(team), 0.0), 0.0)

    model = max(model, safe_float(rules.get("min_model_prob", 0.52), 0.52))
    return clamp(model, 0.01, 0.95)


def _iter_candidates(
    odds_data: dict,
    rules: dict,
    learning_state: dict,
    no_b2b_teams: Optional[Set[str]] = None,
    major_out_teams: Optional[Set[str]] = None,
) -> Iterable[dict]:
    blocked_b2b = no_b2b_teams or set()
    blocked_major = major_out_teams or set()

    for game in odds_data.get("games", []):
        home_tags = {
            normalize_team_key(game.get("home")),
            normalize_team_key(game.get("home_code")),
        }
        away_tags = {
            normalize_team_key(game.get("away")),
            normalize_team_key(game.get("away_code")),
        }

        if (home_tags & blocked_b2b) or (away_tags & blocked_b2b):
            continue
        if (home_tags & blocked_major) or (away_tags & blocked_major):
            continue

        odds = game.get("odds", {})
        for team, odd in odds.items():
            price = safe_float(odd, 0.0)
            if price <= 1.0 or price > safe_float(rules.get("max_single_bet_decimal_odds", 3.0), 3.0):
                continue

            implied = 1.0 / price
            model = model_probability_for_team(team, game, implied, learning_state, rules)
            edge = model - implied
            expected_return = candidate_expected_return(model, price)

            yield {
                "pick": team,
                "odds": price,
                "aus_odds": decimal_to_aus(price),
                "implied_prob": implied,
                "model_prob": model,
                "edge": edge,
                "edge_dollars_per_1u": expected_return,
                "game": f"{game.get('away')} @ {game.get('home')}",
            }


def build_parlay(
    _games_data: dict,
    odds_data: dict,
    rules: dict,
    learning_state: Optional[dict] = None,
    no_b2b_teams: Optional[Set[str]] = None,
    major_out_teams: Optional[Set[str]] = None,
) -> dict:
    if not wagering_enabled(rules):
        return {
            "legs": [],
            "total_odds": 0,
            "edge_notes": "NO_PARLAY: wagering disabled until quant controls are enabled",
        }

    state = learning_state or load_learning_state()
    min_edge_pct = safe_float(rules.get("min_edge_pct", 0.03), 0.03)
    min_edge_dollars = safe_float(rules.get("min_edge_dollars_per_1u", 0.40), 0.40)

    candidates = [
        c
        for c in _iter_candidates(
            odds_data,
            rules,
            state,
            no_b2b_teams=no_b2b_teams,
            major_out_teams=major_out_teams,
        )
        if c["edge"] >= min_edge_pct and c["edge_dollars_per_1u"] >= min_edge_dollars
    ]

    candidates.sort(key=lambda c: (c["edge_dollars_per_1u"], c["edge"]), reverse=True)

    legs = []
    seen_games = set()
    for candidate in candidates:
        if candidate["game"] in seen_games:
            continue
        seen_games.add(candidate["game"])
        legs.append(
            {
                "team": candidate["pick"],
                "odds": candidate["odds"],
                "aus_odds": candidate["aus_odds"],
                "game": candidate["game"],
                "edge": round(candidate["edge"], 4),
                "edge_dollars_per_1u": round(candidate["edge_dollars_per_1u"], 4),
            }
        )
        if len(legs) >= int(rules.get("max_parlay_legs", 3)):
            break

    total_odds = 1.0
    for leg in legs:
        total_odds *= leg["odds"]

    return {
        "legs": legs,
        "total_odds": round(total_odds, 2) if legs else 0,
        "edge_notes": "Quant-gated candidate parlay" if legs else "NO_PARLAY: no eligible legs",
    }


def get_bet_pick(
    _games_data: dict,
    odds_data: dict,
    rules: dict = None,
    learning_state: Optional[dict] = None,
    no_b2b_teams: Optional[Set[str]] = None,
    major_out_teams: Optional[Set[str]] = None,
) -> dict:
    rules = rules or load_quant_rules()

    if not wagering_enabled(rules):
        return {
            "pick": "NO_BET",
            "odds": 0,
            "aus_odds": "N/A",
            "implied_prob": 0,
            "model_prob": 0,
            "edge": 0,
            "edge_dollars_per_1u": 0,
            "band": "N/A",
            "game": "N/A",
            "reason": "Wagering disabled. Set PETE_ENABLE_WAGERING=1 and enable quant_rules.json",
        }

    state = learning_state or load_learning_state()
    min_edge_pct = safe_float(rules.get("min_edge_pct", 0.03), 0.03)
    min_edge_dollars = safe_float(rules.get("min_edge_dollars_per_1u", 0.40), 0.40)

    best = None
    for candidate in _iter_candidates(
        odds_data,
        rules,
        state,
        no_b2b_teams=no_b2b_teams,
        major_out_teams=major_out_teams,
    ):
        if candidate["edge"] < min_edge_pct:
            continue
        if candidate["edge_dollars_per_1u"] < min_edge_dollars:
            continue

        candidate["band"] = "rule-gated"
        candidate["reason"] = "Candidate passed quant, edge, and risk filters"

        if best is None or candidate["edge_dollars_per_1u"] > best["edge_dollars_per_1u"]:
            best = candidate

    if best is None:
        return {
            "pick": "NO_BET",
            "odds": 0,
            "aus_odds": "N/A",
            "implied_prob": 0,
            "model_prob": 0,
            "edge": 0,
            "edge_dollars_per_1u": 0,
            "band": "N/A",
            "game": "N/A",
            "reason": "No candidate met quant thresholds after B2B/major-out filters",
        }

    return best


def normalize_market(value) -> str:
    token = str(value or "").strip().lower().replace(" ", "")
    aliases = {
        "points": "PTS",
        "pts": "PTS",
        "rebounds": "REB",
        "reb": "REB",
        "assists": "AST",
        "ast": "AST",
        "steals": "STL",
        "stl": "STL",
        "threes": "3PM",
        "3ptm": "3PM",
        "3pm": "3PM",
        "threepointersmade": "3PM",
    }
    return aliases.get(token, token.upper())


def market_prior_success_rate(learning_state: dict, market: str, direction: str) -> float:
    stats_map = _coerce_market_stats(learning_state.get("prop_market_stats", {}))
    stats = stats_map.get(normalize_market(market), {})
    if str(direction).upper() == "OVER":
        hits = int(stats.get("over_hits", 1))
        misses = int(stats.get("over_misses", 1))
    else:
        hits = int(stats.get("under_hits", 1))
        misses = int(stats.get("under_misses", 1))
    return clamp(hits / max(1, hits + misses), 0.05, 0.95)


def build_learning_summary(learning_state: dict) -> dict:
    meta = learning_state.get("meta", {}) if isinstance(learning_state, dict) else {}
    player_adj = learning_state.get("player_adjustments", {}) if isinstance(learning_state, dict) else {}
    prop_adj = learning_state.get("player_prop_adjustments", {}) if isinstance(learning_state, dict) else {}

    top_dfs = sorted(player_adj.items(), key=lambda item: abs(safe_float(item[1])), reverse=True)[:3]
    top_prop = sorted(prop_adj.items(), key=lambda item: abs(safe_float(item[1])), reverse=True)[:3]

    return {
        "dfs_samples": int(meta.get("dfs_samples", 0)),
        "bet_samples": int(meta.get("bet_samples", 0)),
        "prop_samples": int(meta.get("prop_samples", 0)),
        "last_feedback_file": str(meta.get("last_feedback_file", "")),
        "top_dfs_adjustments": [{"player": k, "adj": round(safe_float(v), 4)} for k, v in top_dfs],
        "top_prop_adjustments": [{"player_market": k, "adj": round(safe_float(v), 4)} for k, v in top_prop],
    }


def _prop_history_values(prop: dict, h2h_lookup: dict) -> List[float]:
    direct = (
        prop.get("last5_vs_opp")
        or prop.get("last5_vs_opponent")
        or prop.get("last_5")
        or prop.get("history")
        or []
    )
    values = [safe_float(v, math.nan) for v in direct if str(v).strip() != ""]
    values = [v for v in values if not math.isnan(v)]
    if values:
        return values

    player_key = str(prop.get("player", "")).strip().lower()
    team_key = normalize_team_key(prop.get("team", ""))
    opp_key = normalize_team_key(prop.get("opponent", ""))
    market = normalize_market(prop.get("market"))
    return h2h_lookup.get(f"{player_key}::{team_key}::{opp_key}::{market}", [])


def load_h2h_lookup(path: str) -> dict:
    if not path:
        return {}
    file_path = Path(path)
    if not file_path.exists():
        return {}
    try:
        payload = json.loads(file_path.read_text(encoding="utf-8"))
    except Exception:
        return {}

    rows = payload.get("matchups", []) if isinstance(payload, dict) else []
    if not isinstance(rows, list):
        return {}

    lookup = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        player = str(row.get("player", "")).strip().lower()
        team = normalize_team_key(row.get("team", ""))
        opp = normalize_team_key(row.get("opponent", ""))
        market = normalize_market(row.get("market"))
        values = [safe_float(v, math.nan) for v in row.get("values", []) if str(v).strip() != ""]
        values = [v for v in values if not math.isnan(v)]
        if not player or not team or not opp or not market or not values:
            continue
        lookup[f"{player}::{team}::{opp}::{market}"] = values
    return lookup


def load_prop_candidates(props_json_path: str, h2h_json_path: str = "") -> List[dict]:
    if not props_json_path:
        return []
    props_path = Path(props_json_path)
    if not props_path.exists():
        return []

    try:
        payload = json.loads(props_path.read_text(encoding="utf-8"))
    except Exception:
        return []

    games = payload.get("games", []) if isinstance(payload, dict) else []
    if not isinstance(games, list):
        return []

    h2h_lookup = load_h2h_lookup(h2h_json_path)
    candidates: List[dict] = []

    for game in games:
        if not isinstance(game, dict):
            continue
        home = str(game.get("home", "")).strip()
        away = str(game.get("away", "")).strip()
        props = game.get("props", [])
        if not isinstance(props, list):
            continue

        for prop in props:
            if not isinstance(prop, dict):
                continue
            player = str(prop.get("player", "")).strip()
            team = str(prop.get("team", "")).strip()
            if not player or not team:
                continue

            opponent = str(prop.get("opponent", "")).strip() or (away if normalize_team_key(team) == normalize_team_key(home) else home)
            market = normalize_market(prop.get("market"))
            if market not in {"PTS", "REB", "AST", "STL", "3PM"}:
                continue

            line = safe_float(prop.get("line"), math.nan)
            if math.isnan(line):
                continue

            history = _prop_history_values({**prop, "opponent": opponent, "market": market}, h2h_lookup)
            if len(history) < 5:
                continue

            candidates.append(
                {
                    "player": player,
                    "team": team,
                    "opponent": opponent,
                    "market": market,
                    "line": line,
                    "odds_over": safe_float(prop.get("odds_over"), safe_float(prop.get("odds"), 1.87)),
                    "odds_under": safe_float(prop.get("odds_under"), safe_float(prop.get("odds"), 1.87)),
                    "last5": history[:5],
                    "game": f"{away} @ {home}",
                }
            )
    return candidates


def _prop_projection(candidate: dict, rules: dict, learning_state: dict, dfs_projection_map: dict) -> dict:
    values = candidate.get("last5", [])
    avg_last5 = sum(values) / len(values)
    trend = (values[-1] - values[0]) / max(1, len(values) - 1)

    player_key = str(candidate.get("player", "")).strip().lower()
    market = normalize_market(candidate.get("market"))
    prop_adj = learning_state.get("player_prop_adjustments", {}) if isinstance(learning_state, dict) else {}
    prop_opp_adj = learning_state.get("player_prop_opp_adjustments", {}) if isinstance(learning_state, dict) else {}
    learned = safe_float(prop_adj.get(f"{player_key}::{market}", 0.0), 0.0)
    opponent_key = normalize_team_key(candidate.get("opponent", ""))
    learned_opp = safe_float(prop_opp_adj.get(f"{player_key}::{opponent_key}::{market}", 0.0), 0.0)

    dfs_proj = safe_float(dfs_projection_map.get(player_key, 0.0), 0.0)
    dfs_bonus = clamp((dfs_proj - 30.0) * 0.015, -0.4, 0.4) if dfs_proj > 0 else 0.0

    trend_weight = safe_float(rules.get("prop_trend_weight", 0.35), 0.35)
    projected = avg_last5 + (trend * trend_weight) + learned + learned_opp + dfs_bonus

    haircut = clamp(safe_float(rules.get("prop_call_haircut_pct", 0.10), 0.10), 0.10, 0.35)
    safe_projection = projected * (1.0 - haircut)

    return {
        "avg_last5": avg_last5,
        "trend": trend,
        "learned_adj": learned,
        "learned_opp_adj": learned_opp,
        "dfs_bonus": dfs_bonus,
        "projected": projected,
        "safe_projection": safe_projection,
        "haircut_pct": haircut,
    }


def build_player_prop_parlay(
    prop_candidates: List[dict],
    rules: dict,
    learning_state: Optional[dict] = None,
    dfs_projection_map: Optional[dict] = None,
) -> dict:
    if not wagering_enabled(rules):
        return {"legs": [], "total_odds": 0, "note": "NO_PROP_PARLAY: wagering disabled"}
    if not prop_candidates:
        return {"legs": [], "total_odds": 0, "note": "NO_PROP_PARLAY: no eligible prop candidates"}

    state = learning_state or load_learning_state()
    projection_map = dfs_projection_map or {}
    min_line_edge = safe_float(rules.get("prop_min_line_edge", 0.35), 0.35)
    min_model_edge = safe_float(rules.get("prop_min_model_edge_pct", 0.03), 0.03)
    market_prior_weight = clamp(safe_float(rules.get("prop_market_prior_weight", 0.25), 0.25), 0.0, 0.6)

    scored = []
    for candidate in prop_candidates:
        model = _prop_projection(candidate, rules, state, projection_map)
        safe_projection = model["safe_projection"]
        line = safe_float(candidate.get("line"), 0.0)
        line_edge = safe_projection - line
        if abs(line_edge) < min_line_edge:
            continue

        direction = "OVER" if line_edge > 0 else "UNDER"
        odds = candidate["odds_over"] if direction == "OVER" else candidate["odds_under"]
        if odds <= 1.0:
            continue

        values = candidate.get("last5", [])
        over_rate = sum(1 for v in values if v > line) / len(values)
        under_rate = sum(1 for v in values if v < line) / len(values)
        success_rate = over_rate if direction == "OVER" else under_rate
        prior_rate = market_prior_success_rate(state, candidate["market"], direction)
        trend = model["trend"]
        if success_rate < 0.60 and abs(trend) < 0.15:
            continue

        implied = 1.0 / odds
        trend_signal = clamp(trend * 0.05, -0.1, 0.1)
        line_signal = clamp(abs(line_edge) * 0.05, 0.0, 0.12)
        blended_rate = ((1.0 - market_prior_weight) * success_rate) + (market_prior_weight * prior_rate)
        model_prob = clamp(blended_rate + trend_signal + line_signal, 0.05, 0.92)
        edge_prob = model_prob - implied
        if edge_prob < min_model_edge:
            continue

        ev = candidate_expected_return(model_prob, odds)
        if ev <= 0:
            continue

        safe_call = math.floor(safe_projection) if direction == "OVER" else math.ceil(safe_projection)
        safe_call = max(safe_call, 0)
        scored.append(
            {
                "player": candidate["player"],
                "team": candidate["team"],
                "opponent": candidate["opponent"],
                "market": candidate["market"],
                "direction": direction,
                "line": round(line, 2),
                "safe_call": safe_call,
                "projected_raw": round(model["projected"], 3),
                "projected_safe": round(safe_projection, 3),
                "haircut_pct": round(model["haircut_pct"] * 100.0, 1),
                "odds": odds,
                "aus_odds": decimal_to_aus(odds),
                "last5": values,
                "last5_avg": round(model["avg_last5"], 3),
                "trend": round(trend, 3),
                "success_rate": round(success_rate, 3),
                "market_prior_rate": round(prior_rate, 3),
                "implied_prob": round(implied, 4),
                "model_prob": round(model_prob, 4),
                "edge_prob": round(edge_prob, 4),
                "ev": round(ev, 4),
                "learned_adj": round(model["learned_adj"], 3),
                "learned_opp_adj": round(model["learned_opp_adj"], 3),
                "game": candidate["game"],
            }
        )

    if not scored:
        return {"legs": [], "total_odds": 0, "note": "NO_PROP_PARLAY: candidates failed edge/safety filters"}

    scored.sort(key=lambda row: (row["edge_prob"], row["ev"], row["success_rate"]), reverse=True)
    legs = []
    seen = set()
    for row in scored:
        key = f"{row['player']}::{row['market']}"
        if key in seen:
            continue
        seen.add(key)
        legs.append(row)
        if len(legs) >= int(rules.get("prop_max_legs", 3)):
            break

    total_odds = 1.0
    for leg in legs:
        total_odds *= leg["odds"]

    return {
        "legs": legs,
        "total_odds": round(total_odds, 3) if legs else 0,
        "note": "Prop parlay built from last-5 matchup history with 10%+ safety haircut",
    }


def generate_report(
    games_data: dict,
    odds_data: dict,
    lineup: dict,
    pivots: list,
    parlay: dict,
    prop_parlay: dict,
    bet: dict,
    season: str,
    slot: str,
    b2b_count: int,
    major_out_count: int,
    learning_summary: dict,
) -> str:
    report = f"""# Pete NBA Daily - {TODAY}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M %Z')}
Season: {season}

## Data Sources
- Games/Odds: API-Sports ({NBA_API_BASE_URL})

## Games Today ({games_data.get('note', '')})
"""

    for game in games_data.get("games", [])[:10]:
        report += f"- {game.get('away_team')} @ {game.get('home_team')} ({game.get('start_time', 'TBD')})\n"

    report += f"""
## Odds Snapshot ({odds_data.get('note', '')})
- Games with normalized odds: {len(odds_data.get('games', []))}

## Best Lineup ({lineup['format']})
- Slot window: {slot}
- Total Salary: ${lineup['total_salary']:,}
- Projected Points: {lineup.get('projected_points', 0)}
- Note: {lineup['note']}
"""

    if lineup.get("lineup"):
        report += "- Selected Lineup:\n"
        for row in lineup["lineup"]:
            report += (
                f"  - {row['slot']}: {row['name']} ({row['team']}) "
                f"${row['salary']} proj={row['projected']}\n"
            )

    smokies = lineup.get("smokies", [])
    report += "\n## Smokies\n"
    if smokies:
        for idx, smokie in enumerate(smokies, 1):
            report += (
                f"{idx}. {smokie['player']} ({smokie['team']}) - salary ${smokie['salary']}, "
                f"proj delta +{smokie['delta']}\n"
            )
    else:
        report += "- No smokies met threshold\n"

    report += f"""
## Late News Pivots
1. **{pivots[0]['player']}**: {pivots[0]['reason']}
2. **{pivots[1]['player']}**: {pivots[1]['reason']}

## Quant-Gated Parlay ({parlay.get('total_odds', 0)}x)
"""

    if parlay.get("legs"):
        for idx, leg in enumerate(parlay["legs"], 1):
            report += (
                f"{idx}. {leg['team']} @ {leg['aus_odds']} ({leg['odds']}) - {leg['game']} "
                f"edge={leg.get('edge', 0) * 100:.2f}% ev={leg.get('edge_dollars_per_1u', 0):.2f}\n"
            )
    else:
        report += "- NO_PARLAY\n"

    report += f"- Note: {parlay.get('edge_notes', '')}\n"

    report += f"""
## Bet Decision
- Pick: **{bet['pick']}**
- Odds: {bet.get('aus_odds', 'N/A')} ({bet.get('odds', 0)})
- Edge: {bet.get('edge', 0) * 100:.2f}%
- EV per 1u: {bet.get('edge_dollars_per_1u', 0):.2f}
- Game: {bet.get('game', 'N/A')}
- Reason: {bet.get('reason', 'N/A')}
"""

    report += f"""
## Parlay of the Day (Player Props) ({prop_parlay.get('total_odds', 0)}x)
"""
    if prop_parlay.get("legs"):
        for idx, leg in enumerate(prop_parlay["legs"], 1):
            report += (
                f"{idx}. {leg['player']} {leg['direction']} {leg['safe_call']} {leg['market']} "
                f"(book line {leg['line']}) @ {leg['aus_odds']} ({leg['odds']}) - {leg['game']} "
                f"edge={leg['edge_prob'] * 100:.2f}% ev={leg['ev']:.2f}\n"
            )
            report += (
                f"   last5={leg['last5']} avg={leg['last5_avg']} trend={leg['trend']} "
                f"haircut={leg['haircut_pct']}%\n"
            )
    else:
        report += "- NO_PROP_PARLAY\n"

    report += f"- Note: {prop_parlay.get('note', '')}\n"

    report += f"""
## Risk Filters
- B2B blocked teams tracked: {b2b_count}
- Major-out teams blocked: {major_out_count}
- Rule: Home teams get +{safe_float(load_quant_rules().get('home_team_model_boost_pct', 0.10), 0.10) * 100:.0f}% model boost
"""

    report += f"""
## Learning Engine
- DFS samples learned: {learning_summary.get('dfs_samples', 0)}
- Bet samples learned: {learning_summary.get('bet_samples', 0)}
- Prop samples learned: {learning_summary.get('prop_samples', 0)}
- Last feedback file: {learning_summary.get('last_feedback_file') or 'N/A'}
"""

    if learning_summary.get("top_dfs_adjustments"):
        report += "- Top DFS adjustments:\n"
        for row in learning_summary["top_dfs_adjustments"]:
            report += f"  - {row['player']}: {row['adj']:+.3f}\n"

    if learning_summary.get("top_prop_adjustments"):
        report += "- Top prop adjustments:\n"
        for row in learning_summary["top_prop_adjustments"]:
            report += f"  - {row['player_market']}: {row['adj']:+.3f}\n"

    report += """
---
Safety: Script defaults to NO_BET until quant controls are explicitly enabled.
"""

    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Pete NBA Daily Pipeline")
    parser.add_argument("--dry-run", action="store_true", help="Print report to stdout")
    parser.add_argument("--date", default=TODAY, help="Date in YYYY-MM-DD")
    parser.add_argument("--season", default=DEFAULT_SEASON, help="Season start year (e.g., 2026)")
    parser.add_argument("--draftstars-csv", default="", help="Path to Draftstars player CSV")
    parser.add_argument("--slot", choices=["all", "early", "late"], default="all", help="Slate slot window")
    parser.add_argument("--feedback-json", default="", help="Path to feedback JSON for learning updates")
    parser.add_argument("--major-outs-json", default="", help="Override path to major-out teams JSON")
    parser.add_argument("--props-json", default="", help="Path to player props JSON payload")
    parser.add_argument("--h2h-json", default="", help="Path to optional last-5 matchup JSON payload")
    args = parser.parse_args()

    print(f"[Pete NBA] Starting pipeline for date={args.date} season={args.season} slot={args.slot}")

    api_key = load_env_secrets()
    if not api_key:
        print("[Pete NBA] WARNING: NBA_API_KEY not set")

    rules = load_quant_rules()
    learning_state = load_learning_state()
    learning_state = update_learning_state_from_feedback(learning_state, args.feedback_json)
    save_learning_state(learning_state)

    games_data = fetch_nba_games(args.season, args.date)
    odds_data = fetch_nba_odds(args.date, args.season)

    previous_date = (datetime.strptime(args.date, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
    b2b_teams = fetch_teams_played_on_date(args.season, previous_date)
    major_out_teams = load_major_out_teams(args.major_outs_json)

    lineup = build_best_lineup(
        games_data,
        draftstars_csv=args.draftstars_csv,
        slot=args.slot,
        learning_state=learning_state,
        rules=rules,
    )
    pivots = get_pivots(lineup)
    parlay = build_parlay(
        games_data,
        odds_data,
        rules,
        learning_state=learning_state,
        no_b2b_teams=b2b_teams,
        major_out_teams=major_out_teams,
    )
    bet = get_bet_pick(
        games_data,
        odds_data,
        rules,
        learning_state=learning_state,
        no_b2b_teams=b2b_teams,
        major_out_teams=major_out_teams,
    )
    prop_candidates = load_prop_candidates(args.props_json, args.h2h_json)
    prop_parlay = build_player_prop_parlay(
        prop_candidates,
        rules,
        learning_state=learning_state,
        dfs_projection_map=lineup.get("projection_map", {}),
    )
    learning_summary = build_learning_summary(learning_state)

    report = generate_report(
        games_data,
        odds_data,
        lineup,
        pivots,
        parlay,
        prop_parlay,
        bet,
        args.season,
        slot=args.slot,
        b2b_count=len(b2b_teams),
        major_out_count=len(major_out_teams),
        learning_summary=learning_summary,
    )

    if args.dry_run:
        print(report)
        return

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    output_file = LOG_DIR / f"{args.date}.md"
    with open(output_file, "w", encoding="utf-8") as handle:
        handle.write(report)

    print(f"[Pete NBA] Report written: {output_file}")


if __name__ == "__main__":
    main()
