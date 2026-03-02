#!/usr/bin/env python3
"""Pete DFS engine with ESPN history ingestion, lineup optimization, and rolling backtest."""

from __future__ import annotations

import argparse
import json
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
import requests

try:
    from scipy.optimize import Bounds, LinearConstraint, milp

    SCIPY_AVAILABLE = True
except Exception:
    SCIPY_AVAILABLE = False
    Bounds = None
    LinearConstraint = None
    milp = None

ESPN_SCOREBOARD_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={yyyymmdd}"
ESPN_SUMMARY_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary?event={event_id}"

ROSTER_SLOTS = {"PG": 2, "SG": 2, "SF": 2, "PF": 2, "C": 1}
DEFAULT_SALARY_CAP = 100_000
WORKSPACE = Path(os.environ.get("OPENCLAW_WORKSPACE", str(Path.cwd() / ".pete-workspace")))
LOG_DIR = WORKSPACE / "logs" / "Pete"

# Draftstars scoring weights
POINTS_WEIGHT = 1.0
REBOUNDS_WEIGHT = 1.25
ASSISTS_WEIGHT = 1.5
STEALS_WEIGHT = 2.0
BLOCKS_WEIGHT = 2.0
TURNOVERS_WEIGHT = -0.5


@dataclass
class EngineResult:
    success: bool
    reason: str
    lineup: List[dict]
    total_salary: float
    projected_form: float
    backtest: dict
    scrape: dict


def _clean_label(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value or "").lower())


def _clean_player_name(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def _safe_float(value, default: float = 0.0) -> float:
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()
    if not text:
        return default

    if ":" in text:
        return default
    if "/" in text:
        return default

    text = text.replace(",", "").replace("%", "")
    try:
        return float(text)
    except Exception:
        return default


def _request_json(session: requests.Session, url: str, timeout: int = 20, retries: int = 3, backoff_s: float = 0.35) -> Optional[dict]:
    for attempt in range(retries):
        try:
            response = session.get(url, timeout=timeout)
            if response.status_code == 200:
                payload = response.json()
                if isinstance(payload, dict):
                    return payload
            if response.status_code in {400, 401, 403, 404}:
                return None
        except Exception:
            pass
        if attempt < retries - 1:
            time.sleep(backoff_s * (attempt + 1))
    return None


def _find_event_ids(scoreboard_payload: dict) -> List[str]:
    events = scoreboard_payload.get("events", []) if isinstance(scoreboard_payload, dict) else []
    ids: List[str] = []
    for row in events if isinstance(events, list) else []:
        if not isinstance(row, dict):
            continue
        event_id = str(row.get("id", "")).strip()
        if event_id:
            ids.append(event_id)
    return ids


def _get_stat_labels(stat_group: dict) -> List[str]:
    for key in ("labels", "names", "keys"):
        raw = stat_group.get(key)
        if isinstance(raw, list) and raw:
            labels = [str(item).strip() for item in raw]
            if any(labels):
                return labels
    return []


def _stat_value(stats: Dict[str, float], labels: Sequence[str]) -> float:
    for label in labels:
        key = _clean_label(label)
        if key in stats:
            return _safe_float(stats[key], 0.0)
    return 0.0


def _to_stat_map(labels: Sequence[str], values: Sequence) -> Dict[str, float]:
    mapping: Dict[str, float] = {}
    if labels:
        for idx, raw in enumerate(values):
            if idx >= len(labels):
                continue
            mapping[_clean_label(labels[idx])] = _safe_float(raw, 0.0)
    else:
        fallback = {
            6: "reb",
            7: "ast",
            8: "stl",
            9: "blk",
            10: "to",
            12: "pts",
        }
        for idx, label in fallback.items():
            if idx < len(values):
                mapping[label] = _safe_float(values[idx], 0.0)
    return mapping


def _fpts_from_stats(stats: Dict[str, float]) -> float:
    points = _stat_value(stats, ["pts", "points"])
    rebounds = _stat_value(stats, ["reb", "rebounds", "totalrebounds"])
    assists = _stat_value(stats, ["ast", "assists"])
    steals = _stat_value(stats, ["stl", "steals"])
    blocks = _stat_value(stats, ["blk", "blocks"])
    turnovers = _stat_value(stats, ["to", "tov", "turnovers"])
    return (
        points * POINTS_WEIGHT
        + rebounds * REBOUNDS_WEIGHT
        + assists * ASSISTS_WEIGHT
        + steals * STEALS_WEIGHT
        + blocks * BLOCKS_WEIGHT
        + turnovers * TURNOVERS_WEIGHT
    )


def extract_player_fpts_from_summary(summary_payload: dict) -> List[dict]:
    rows: List[dict] = []
    boxscore = summary_payload.get("boxscore", {}) if isinstance(summary_payload, dict) else {}
    teams = boxscore.get("players", []) if isinstance(boxscore, dict) else []

    for team_blob in teams if isinstance(teams, list) else []:
        if not isinstance(team_blob, dict):
            continue
        team_info = team_blob.get("team", {}) if isinstance(team_blob.get("team"), dict) else {}
        team = str(team_info.get("abbreviation") or team_info.get("shortDisplayName") or "").strip().upper()

        stat_groups = team_blob.get("statistics", []) if isinstance(team_blob.get("statistics"), list) else []
        if not stat_groups:
            continue

        # First stat group usually has full totals and stable labels.
        stat_group = stat_groups[0] if isinstance(stat_groups[0], dict) else {}
        labels = _get_stat_labels(stat_group)
        athletes = stat_group.get("athletes", []) if isinstance(stat_group, dict) else []

        for athlete_blob in athletes if isinstance(athletes, list) else []:
            if not isinstance(athlete_blob, dict):
                continue
            athlete = athlete_blob.get("athlete", {}) if isinstance(athlete_blob.get("athlete"), dict) else {}
            name = str(athlete.get("displayName") or athlete.get("shortName") or "").strip()
            stats_raw = athlete_blob.get("stats", []) if isinstance(athlete_blob.get("stats"), list) else []
            if not name or not stats_raw:
                continue

            stats = _to_stat_map(labels, stats_raw)
            rows.append({"Name": name, "Team": team, "FP": round(_fpts_from_stats(stats), 4)})

    return rows


def collect_espn_history_logs(
    lookback_days: int = 10,
    now: Optional[datetime] = None,
    request_timeout: int = 20,
) -> Tuple[pd.DataFrame, dict]:
    pivot = now or datetime.now()

    records: List[dict] = []
    days_scanned = 0
    events_seen = 0
    events_loaded = 0

    with requests.Session() as session:
        session.headers.update({"User-Agent": "elevate-flow-pete-dfs/1.0"})

        for offset in range(max(1, lookback_days)):
            days_scanned += 1
            game_date = (pivot - timedelta(days=offset)).date()
            yyyymmdd = game_date.strftime("%Y%m%d")

            scoreboard = _request_json(session, ESPN_SCOREBOARD_URL.format(yyyymmdd=yyyymmdd), timeout=request_timeout)
            if not scoreboard:
                continue

            event_ids = _find_event_ids(scoreboard)
            events_seen += len(event_ids)

            for event_id in event_ids:
                summary = _request_json(session, ESPN_SUMMARY_URL.format(event_id=event_id), timeout=request_timeout)
                if not summary:
                    continue

                players = extract_player_fpts_from_summary(summary)
                if players:
                    events_loaded += 1
                for row in players:
                    row["Date"] = game_date.isoformat()
                    row["EventId"] = event_id
                    records.append(row)

    history_df = pd.DataFrame(records)
    scrape = {
        "days_scanned": days_scanned,
        "events_seen": events_seen,
        "events_loaded": events_loaded,
        "records": len(history_df.index),
    }
    return history_df, scrape


def compute_variance_map(history_df: pd.DataFrame) -> Dict[str, float]:
    if history_df.empty:
        return {}

    cols = set(history_df.columns)
    if "Name" not in cols or "FP" not in cols:
        return {}

    variance = history_df.groupby("Name")["FP"].std(ddof=0).fillna(0.0)
    return {_clean_player_name(name): float(value) for name, value in variance.items()}


def _canonical_column_map(columns: Iterable[str]) -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    for raw in columns:
        token = _clean_label(raw)
        mapping[token] = raw
    return mapping


def load_and_clean_daily_csv(daily_csv_path: str) -> pd.DataFrame:
    frame = pd.read_csv(daily_csv_path)
    colmap = _canonical_column_map(frame.columns)

    required = {
        "name": ["name", "player", "playername", "displayname"],
        "salary": ["salary", "sal"],
        "form": ["form", "projection", "projected", "fppg"],
        "position": ["position", "pos"],
    }

    resolved: Dict[str, str] = {}
    for key, candidates in required.items():
        source = next((colmap[c] for c in candidates if c in colmap), "")
        if not source:
            raise ValueError(f"Missing required column for {key}: {candidates}")
        resolved[key] = source

    status_col = next((colmap[c] for c in ["playingstatus", "status", "injurystatus"] if c in colmap), "")
    team_col = next((colmap[c] for c in ["team", "teamname"] if c in colmap), "")
    fppg_col = next((colmap[c] for c in ["fppg", "avg", "average"] if c in colmap), "")

    cleaned = pd.DataFrame()
    cleaned["Name"] = frame[resolved["name"]]
    cleaned["Position"] = frame[resolved["position"]]
    cleaned["Salary"] = pd.to_numeric(frame[resolved["salary"]], errors="coerce")
    cleaned["Form"] = pd.to_numeric(frame[resolved["form"]], errors="coerce")
    cleaned["FPPG"] = pd.to_numeric(frame[fppg_col], errors="coerce") if fppg_col else np.nan
    cleaned["Playing Status"] = frame[status_col] if status_col else ""
    cleaned["Team"] = frame[team_col] if team_col else ""

    cleaned = cleaned.dropna(subset=["Name", "Position", "Salary", "Form"]).copy()
    cleaned["Name"] = cleaned["Name"].astype(str).str.strip()
    cleaned["Position"] = cleaned["Position"].astype(str).str.upper().str.strip()
    cleaned["Playing Status"] = cleaned["Playing Status"].astype(str)

    # Keep PROBABLE players; remove true risk statuses.
    risk_mask = cleaned["Playing Status"].str.contains(r"OUT|QUESTIONABLE|DOUBTFUL|INACTIVE", case=False, na=False)
    cleaned = cleaned[~risk_mask].copy()

    return cleaned.reset_index(drop=True)


def _to_builtin_rows(rows: List[dict]) -> List[dict]:
    normalized: List[dict] = []
    for row in rows:
        clean: Dict[str, object] = {}
        for key, value in row.items():
            if isinstance(value, (np.floating, np.integer)):
                clean[key] = float(value)
            else:
                clean[key] = value
        normalized.append(clean)
    return normalized


def _slot_counts(lineup_rows: List[dict]) -> Dict[str, int]:
    counts = {slot: 0 for slot in ROSTER_SLOTS}
    for row in lineup_rows:
        for slot in _position_set(str(row.get("Position", ""))):
            counts[slot] += 1
    return counts


def _derive_smokies(candidate_df: pd.DataFrame, lineup_rows: List[dict], max_items: int = 3) -> List[dict]:
    if candidate_df.empty or not lineup_rows:
        return []

    if "FPPG" not in candidate_df.columns:
        return []

    work = candidate_df.copy()
    if work["FPPG"].isna().all():
        return []

    lineup_names = {_clean_player_name(row.get("Name", "")) for row in lineup_rows}
    work["NameKey"] = work["Name"].map(_clean_player_name)
    work["Delta"] = work["Form"] - work["FPPG"].fillna(work["Form"])
    work = work[work["NameKey"].isin(lineup_names)].copy()
    if work.empty:
        return []

    salary_cutoff = float(work["Salary"].quantile(0.45))
    work = work[(work["Salary"] <= salary_cutoff) & (work["Delta"] > 0.0)].copy()
    if work.empty:
        return []

    work = work.sort_values(["Delta", "Form"], ascending=[False, False]).head(max_items)
    smokies: List[dict] = []
    for _, row in work.iterrows():
        smokies.append(
            {
                "player": str(row.get("Name", "")),
                "team": str(row.get("Team", "")),
                "position": str(row.get("Position", "")),
                "salary": float(row.get("Salary", 0.0)),
                "projection": float(row.get("Form", 0.0)),
                "baseline": float(row.get("FPPG", 0.0)),
                "delta": float(round(row.get("Delta", 0.0), 3)),
            }
        )
    return smokies


def build_mission_control_payload(
    result: EngineResult,
    daily_csv_path: str,
    slot: str,
    lookback_days: int,
    salary_cap: int,
    risk_penalty: float,
    train_days: int,
    smokies: Optional[List[dict]] = None,
) -> dict:
    generated_at = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    status = "done" if result.success else "blocked"
    today = datetime.now().strftime("%Y-%m-%d")
    call_id = f"pete-dfs-{today}-{slot}"

    lineup_rows = _to_builtin_rows(result.lineup)
    salary_used = float(result.total_salary or 0.0)
    projected_form = float(result.projected_form or 0.0)
    smokie_rows = smokies or []

    return {
        "schema_version": "1.0",
        "module": "pete_dfs",
        "queue_item": {
            "call_id": call_id,
            "owner": "Pete",
            "due_at": f"{today}T09:00:00",
            "status": status,
            "priority": "high",
            "blocker": None if result.success else result.reason,
            "last_update": generated_at,
        },
        "config": {
            "daily_csv_path": str(daily_csv_path),
            "slot": slot,
            "lookback_days": int(lookback_days),
            "train_days": int(train_days),
            "salary_cap": int(salary_cap),
            "risk_penalty": float(risk_penalty),
        },
        "dfs_lineup": {
            "success": bool(result.success),
            "reason": result.reason,
            "format": "2 PG, 2 SG, 2 SF, 2 PF, 1 C",
            "selected_count": len(lineup_rows),
            "slot_counts": _slot_counts(lineup_rows),
            "salary_cap": int(salary_cap),
            "salary_used": round(salary_used, 2),
            "salary_remaining": round(float(salary_cap) - salary_used, 2),
            "projected_form": round(projected_form, 3),
            "lineup": lineup_rows,
            "smokies": smokie_rows,
        },
        "model_quality": {
            "backtest": result.backtest,
            "scrape": result.scrape,
        },
    }


def write_mission_control_payload(payload: dict, out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return out_path


def _position_set(raw_position: str) -> set:
    tokens = re.split(r"[\s,/|-]+", str(raw_position or "").upper())
    return {tok for tok in tokens if tok in ROSTER_SLOTS}


def _lineup_constraints(df: pd.DataFrame, salary_cap: int) -> List:
    n = len(df.index)
    constraints: List = []

    constraints.append(LinearConstraint(np.ones(n), 9, 9))

    for slot, count in ROSTER_SLOTS.items():
        mask = np.array([1.0 if slot in _position_set(pos) else 0.0 for pos in df["Position"]], dtype=float)
        constraints.append(LinearConstraint(mask, count, count))

    constraints.append(LinearConstraint(df["Salary"].astype(float).to_numpy(), -np.inf, salary_cap))

    for name in df["Name"].astype(str).tolist():
        mask = (df["Name"].astype(str) == name).astype(float).to_numpy()
        if mask.sum() > 1:
            constraints.append(LinearConstraint(mask, -np.inf, 1.0))

    return constraints


def optimize_dfs_lineup(df: pd.DataFrame, variance_map: Dict[str, float], salary_cap: int = DEFAULT_SALARY_CAP, risk_penalty: float = 0.15) -> dict:
    if not SCIPY_AVAILABLE:
        return {"success": False, "reason": "scipy unavailable", "lineup": pd.DataFrame()}

    if df.empty:
        return {"success": False, "reason": "no candidates after cleaning", "lineup": pd.DataFrame()}

    risk = np.array([variance_map.get(_clean_player_name(name), 0.0) for name in df["Name"]], dtype=float)
    objective = -(df["Form"].astype(float).to_numpy() - (risk_penalty * risk))

    constraints = _lineup_constraints(df, salary_cap=salary_cap)

    result = milp(
        c=objective,
        constraints=constraints,
        integrality=np.ones(len(df.index), dtype=int),
        bounds=Bounds(np.zeros(len(df.index)), np.ones(len(df.index))),
    )

    if not getattr(result, "success", False):
        return {
            "success": False,
            "reason": f"optimization failed: {getattr(result, 'message', 'unknown')}",
            "lineup": pd.DataFrame(),
        }

    picks = np.where(np.rint(result.x).astype(int) == 1)[0]
    lineup = df.iloc[picks].copy().reset_index(drop=True)
    lineup["RiskStd"] = lineup["Name"].map(lambda name: variance_map.get(_clean_player_name(name), 0.0))

    return {
        "success": True,
        "reason": "ok",
        "lineup": lineup,
        "solver_fun": float(getattr(result, "fun", 0.0)),
    }


def run_rolling_backtest(history_df: pd.DataFrame, train_days: int = 7) -> dict:
    if history_df.empty or "Date" not in history_df.columns:
        return {"samples": 0, "windows": 0, "mae": None, "rmse": None}

    work = history_df.copy()
    work["Date"] = pd.to_datetime(work["Date"], errors="coerce").dt.date
    work = work.dropna(subset=["Date", "Name", "FP"])
    if work.empty:
        return {"samples": 0, "windows": 0, "mae": None, "rmse": None}

    unique_dates = sorted(work["Date"].unique())
    if len(unique_dates) <= train_days:
        return {"samples": 0, "windows": 0, "mae": None, "rmse": None}

    abs_errors: List[float] = []
    sq_errors: List[float] = []
    windows = 0

    for idx in range(train_days, len(unique_dates)):
        train_set = set(unique_dates[idx - train_days : idx])
        test_date = unique_dates[idx]

        train_df = work[work["Date"].isin(train_set)]
        test_df = work[work["Date"] == test_date]
        if train_df.empty or test_df.empty:
            continue

        per_player_mean = train_df.groupby("Name")["FP"].mean().to_dict()
        test_df = test_df[test_df["Name"].isin(per_player_mean.keys())]
        if test_df.empty:
            continue

        pred = test_df["Name"].map(per_player_mean).astype(float)
        actual = test_df["FP"].astype(float)
        errs = (actual - pred).to_numpy()

        abs_errors.extend(np.abs(errs).tolist())
        sq_errors.extend((errs ** 2).tolist())
        windows += 1

    if not abs_errors:
        return {"samples": 0, "windows": windows, "mae": None, "rmse": None}

    mae = float(np.mean(abs_errors))
    rmse = float(np.sqrt(np.mean(sq_errors)))
    return {"samples": len(abs_errors), "windows": windows, "mae": round(mae, 4), "rmse": round(rmse, 4)}


def run_pete_dfs_engine(
    daily_csv_path: str,
    lookback_days: int = 10,
    salary_cap: int = DEFAULT_SALARY_CAP,
    risk_penalty: float = 0.15,
    train_days: int = 7,
) -> EngineResult:
    print(f"PETE DFS ENGINE: processing {daily_csv_path}")
    print(f"Collecting ESPN history over last {lookback_days} days...")

    history_df, scrape = collect_espn_history_logs(lookback_days=lookback_days)
    variance_map = compute_variance_map(history_df)
    backtest = run_rolling_backtest(history_df, train_days=train_days)

    df = load_and_clean_daily_csv(daily_csv_path)
    result = optimize_dfs_lineup(df, variance_map, salary_cap=salary_cap, risk_penalty=risk_penalty)

    if not result["success"]:
        print(f"Optimization failed: {result['reason']}")
        return EngineResult(
            success=False,
            reason=result["reason"],
            lineup=[],
            total_salary=0.0,
            projected_form=0.0,
            backtest=backtest,
            scrape=scrape,
        )

    lineup_df = result["lineup"].sort_values(["Position", "Name"]).reset_index(drop=True)
    total_salary = float(lineup_df["Salary"].sum())
    projected_form = float(lineup_df["Form"].sum())
    smokies = _derive_smokies(df, lineup_df.to_dict(orient="records"))

    print("\n--- FINAL OPTIMIZED LINEUP ---")
    print(lineup_df[["Position", "Name", "Team", "Salary", "Form", "RiskStd"]].to_string(index=False))
    print(f"\nTotal Salary: ${total_salary:,.0f} | Projected Form: {projected_form:.2f}")
    if smokies:
        print("Top Smokies:")
        for idx, row in enumerate(smokies, 1):
            print(f"{idx}. {row['player']} ({row['position']}) salary=${row['salary']:.0f} delta=+{row['delta']:.2f}")
    print(f"Backtest: {backtest}")
    print(f"Scrape: {scrape}")

    return EngineResult(
        success=True,
        reason="ok",
        lineup=lineup_df.to_dict(orient="records"),
        total_salary=total_salary,
        projected_form=projected_form,
        backtest=backtest,
        scrape=scrape,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Pete DFS engine with ESPN history and lineup optimization")
    parser.add_argument("daily_csv_path", help="Path to Draftstars daily player CSV")
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"), help="Run date in YYYY-MM-DD")
    parser.add_argument("--slot", choices=["all", "early", "late"], default="all", help="Slate window label")
    parser.add_argument("--lookback-days", type=int, default=10, help="Days of ESPN history to ingest")
    parser.add_argument("--salary-cap", type=int, default=DEFAULT_SALARY_CAP, help="Salary cap for optimizer")
    parser.add_argument("--risk-penalty", type=float, default=0.15, help="Penalty multiplier for high-variance players")
    parser.add_argument("--train-days", type=int, default=7, help="Rolling train window days for backtest")
    parser.add_argument(
        "--mission-control-json",
        default="",
        help="Output path for Mission Control JSON payload (default: OPENCLAW_WORKSPACE/logs/Pete/<date>-pete-dfs.json)",
    )
    args = parser.parse_args()

    result = run_pete_dfs_engine(
        args.daily_csv_path,
        lookback_days=max(1, args.lookback_days),
        salary_cap=max(1000, args.salary_cap),
        risk_penalty=max(0.0, args.risk_penalty),
        train_days=max(1, args.train_days),
    )

    lineup_rows = result.lineup if result.success else []
    smokies = []
    if lineup_rows:
        try:
            candidate_df = load_and_clean_daily_csv(args.daily_csv_path)
            smokies = _derive_smokies(candidate_df, lineup_rows)
        except Exception:
            smokies = []

    payload = build_mission_control_payload(
        result=result,
        daily_csv_path=args.daily_csv_path,
        slot=args.slot,
        lookback_days=max(1, args.lookback_days),
        salary_cap=max(1000, args.salary_cap),
        risk_penalty=max(0.0, args.risk_penalty),
        train_days=max(1, args.train_days),
        smokies=smokies,
    )

    target = (
        Path(args.mission_control_json)
        if args.mission_control_json
        else (LOG_DIR / f"{args.date}-pete-dfs.json")
    )
    saved = write_mission_control_payload(payload, target)
    print(f"Mission Control payload written: {saved}")


if __name__ == "__main__":
    main()
