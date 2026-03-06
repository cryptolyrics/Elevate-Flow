#!/usr/bin/env python3
"""
Pete's Daily NBA Pipeline
Runs: 8am Brisbane (10am AEDT / 00:00 UTC)
Output: /workspace/logs/Pete/YYYY-MM-DD.md

APIs:
- balldontlie.io: Game schedules, team info
- the-odds-api.com: Betting odds
"""
import os
import json
import argparse
import subprocess
import warnings
import io
import contextlib
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    from zoneinfo import ZoneInfo
except ImportError:  # Python < 3.9
    ZoneInfo = None


def get_usa_date() -> str:
    """
    Get the current USA Eastern Time date.
    
    NBA games are scheduled in US time, so all data collection and API calls
    should use USA date (Eastern Time) rather than local Australia date.
    
    Australia (AEST/AEDT) is typically 14-15 hours ahead of US Eastern Time,
    meaning when it's the next day in Australia, it's still the previous day in the US.
    
    Returns:
        USA date in YYYY-MM-DD format (Eastern Time)
    """
    now_utc = datetime.now(timezone.utc)
    
    if ZoneInfo:
        try:
            usa_tz = ZoneInfo("America/New_York")
            now_usa = now_utc.astimezone(usa_tz)
            return now_usa.strftime("%Y-%m-%d")
        except Exception:
            pass
    
    # Fallback: manually calculate USA date (approximately -14 hours from AEST)
    au_now = datetime.now()
    usa_date = au_now - timedelta(hours=14)
    if au_now.hour < 14:  # Before 2pm AU time
        usa_date = usa_date - timedelta(days=1)
    return usa_date.strftime("%Y-%m-%d")


# Config
WORKSPACE = Path("/Users/jjbot/.openclaw/workspace")
LOG_DIR = WORKSPACE / "logs" / "Pete"
# USA date for NBA data - Australia is always 1 day ahead of US NBA schedule
USA_TODAY = get_usa_date()
TODAY = USA_TODAY  # Use USA date for all NBA data operations

# Silence urllib3 LibreSSL warnings
try:
    from urllib3.exceptions import NotOpenSSLWarning
    warnings.filterwarnings("ignore", category=NotOpenSSLWarning)
except Exception:
    pass


def load_env_secrets():
    """Load secrets from ~/.env.pete (gitignored)"""
    env_file = Path.home() / ".env.pete"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if "=" in line and not line.strip().startswith("#"):
                    key, val = line.strip().split("=", 1)
                    os.environ[key] = val
    return os.environ.get("ODDS_API_KEY", ""), os.environ.get("BALLDONTLIE_API_KEY", "")


def curl_get(url, headers=None):
    """Make curl request, return JSON"""
    cmd = ["curl", "-s", "--max-time", "30"]
    if headers:
        for k, v in headers.items():
            cmd.extend(["-H", f"{k}: {v}"])
    cmd.append(url)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=35)
        return json.loads(result.stdout) if result.stdout else None
    except Exception as e:
        print(f"Curl error: {e}")
        return None


def get_todays_games():
    """Fetch today's NBA games from balldontlie API using official SDK"""
    from balldontlie import BalldontlieAPI
    
    api_key = os.environ.get("BALLDONTLIE_API_KEY", "")
    if not api_key:
        return {"games": [], "note": "No balldontlie API key"}
    
    try:
        api = BalldontlieAPI(api_key=api_key)
        # Suppress any SDK stdout noise
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            games_response = api.nba.games.list(dates=[TODAY])
        games_data = games_response.data
        
        games = []
        for g in games_data:
            home = g.home_team if hasattr(g, 'home_team') else None
            away = g.visitor_team if hasattr(g, 'visitor_team') else None
            games.append({
                "game_id": g.id,
                "home_team": home.abbreviation if home else "",
                "away_team": away.abbreviation if away else "",
                "home_name": home.full_name if home else "",
                "away_name": away.full_name if away else "",
                "status": g.status,
                "start_time": g.status or g.date,
            })
        
        return {"games": games, "note": f"Found {len(games)} games today"}
    except Exception as e:
        return {"games": [], "note": f"Error: {e}"}


def get_odds():
    """Fetch NBA odds from the-odds-api"""
    api_key = os.environ.get("ODDS_API_KEY", "")
    if not api_key:
        return {"games": [], "note": "No odds API key"}
    
    url = f"https://api.the-odds-api.com/v4/sports/basketball_nba/odds?apiKey={api_key}&regions=us"
    data = curl_get(url)
    
    if not data:
        return {"games": [], "note": "Failed to fetch odds"}
    
    games = []
    for g in data:
        markets = g.get("bookmakers", [])
        best_odds = {}
        for bm in markets:
            for market in bm.get("markets", []):
                if market.get("key") == "h2h":
                    for outcome in market.get("outcomes", []):
                        team = outcome.get("name")
                        price = outcome.get("price")
                        if team and price:
                            if team not in best_odds or price > best_odds[team]:
                                best_odds[team] = price
        
        games.append({
            "home": g.get("home_team"),
            "away": g.get("away_team"),
            "start": g.get("commence_time"),
            "odds": best_odds
        })
    
    return {"games": games, "note": f"Found odds for {len(games)} games"}


def build_best_lineup(games_data):
    """Build optimal Draftstars lineup"""
    # TODO: Need player stats for lineup optimization
    return {
        "lineup": [],
        "format": "classic",
        "total_salary": 0,
        "note": "Awaiting player stats API"
    }


def get_pivots(games_data):
    """Identify 2 pivots for late news"""
    return [
        {"player": "TBD", "reason": "Awaiting injury reports"},
        {"player": "TBD", "reason": "Awaiting lineup news"}
    ]


def decimal_to_aus(decimal_odds):
    """Convert decimal to Australian odds (line style)"""
    if decimal_odds >= 2:
        # Positive: +325 for 4.25
        return f"+{int((decimal_odds - 1) * 100)}"
    else:
        # Negative: -200 for 1.50
        return f"-{int(100 / (decimal_odds - 1))}"


def build_parlay(games_data, odds_data):
    """Build 5-leg parlay with edge notes"""
    legs = []
    for g in odds_data.get("games", [])[:5]:
        odds = g.get("odds", {})
        # Find underdog with best odds
        for team, price in odds.items():
            if price > 1.5:
                legs.append({
                    "team": team,
                    "odds": price,
                    "aus_odds": decimal_to_aus(price),
                    "game": f"{g.get('away')} @ {g.get('home')}"
                })
                break
    
    total_odds = 1.0
    for leg in legs:
        total_odds *= leg["odds"]
    
    return {
        "legs": legs[:5],
        "total_odds": round(total_odds, 2),
        "edge_notes": "Top underdogs from odds API"
    }


def get_bet_pick(games_data, odds_data):
    """Bet of the day with implied vs model prob"""
    # Simple: pick favorite with best edge
    best_bet = None
    best_value = 0
    
    for g in odds_data.get("games", []):
        odds = g.get("odds", {})
        if not odds or len(odds) < 2:
            continue
        
        # Find favorite (lowest odds)
        try:
            sorted_odds = sorted(odds.items(), key=lambda x: x[1])
            fav_team, price = sorted_odds[0]
        except:
            continue
        
        # Implied probability
        if price <= 0:
            continue
        implied_prob = 1 / price
        
        # Placeholder model: assume 55% for favorites
        model_prob = 0.55
        edge = model_prob - implied_prob
        
        if edge > best_value:
            best_value = edge
            best_bet = {
                "pick": fav_team,
                "odds": price,
                "implied_prob": implied_prob,
                "model_prob": model_prob,
                "edge": edge,
                "game": f"{g.get('away')} @ {g.get('home')}"
            }
    
    if not best_bet:
        return {"pick": "N/A", "odds": 0, "implied_prob": 0, "model_prob": 0, "edge": 0, "band": "N/A"}
    
    # Return band
    ret = (best_bet["odds"] - 1) * 100
    if ret < 30:
        band = "30-60%"
    elif ret < 90:
        band = "30-90%"
    else:
        band = "90%+"
    
    return {
        "pick": best_bet["pick"],
        "odds": best_bet["odds"],
        "aus_odds": decimal_to_aus(best_bet["odds"]),
        "implied_prob": best_bet["implied_prob"],
        "model_prob": best_bet["model_prob"],
        "edge": best_bet["edge"],
        "band": band,
        "game": best_bet["game"]
    }


def generate_report(games_data, odds_data, lineup, pivots, parlay, bet):
    """Generate daily report"""
    report = f"""# Pete NBA Daily - {TODAY}
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M %Z")}

## Games Today ({games_data.get('note', '')})
"""
    for g in games_data.get("games", [])[:5]:
        report += f"- {g.get('away_team')} @ {g.get('home_team')} ({g.get('start_time', 'TBD')})\n"
    
    report += f"""
## Best Lineup ({lineup['format']})
- Total Salary: ${lineup['total_salary']:,}
- Note: {lineup['note']}

## Late News Pivots
1. **{pivots[0]['player']}**: {pivots[0]['reason']}
2. **{pivots[1]['player']}**: {pivots[1]['reason']}

## 5-Leg Parlay ({parlay['total_odds']}x)
"""
    for i, leg in enumerate(parlay["legs"], 1):
        report += f"{i}. {leg['team']} @ {leg['aus_odds']} ({leg['odds']})\n"
    report += f"- Edge: {parlay['edge_notes']}\n"
    
    report += f"""
## Bet of Day
- **Pick**: {bet['pick']}
- **Odds**: {bet['aus_odds']} ({bet['odds']})
- **Implied Prob**: {bet['implied_prob']*100:.1f}%
- **Model Prob**: {bet['model_prob']*100:.1f}%
- **Edge**: {bet['edge']*100:.1f}%
- **Return Band**: {bet['band']}
- **Game**: {bet.get('game', 'N/A')}

---
*Pipeline v0.2 - balldontlie + Odds API*
"""
    return report


def main():
    parser = argparse.ArgumentParser(description="Pete's Daily NBA Pipeline")
    parser.add_argument("--dry-run", action="store_true", help="Print to stdout only")
    parser.add_argument("--date", default=TODAY, help="Override date")
    args = parser.parse_args()

    print(f"[Pete NBA] Starting pipeline for {args.date}")
    
    # Load secrets
    odds_key, bdl_key = load_env_secrets()
    if not odds_key:
        print("[Pete NBA] WARNING: No ODDS_API_KEY")
    if not bdl_key:
        print("[Pete NBA] WARNING: No BALLDONTLIE_API_KEY")
    
    # Fetch data
    games_data = get_todays_games()
    odds_data = get_odds()
    
    # Build outputs
    lineup = build_best_lineup(games_data)
    pivots = get_pivots(games_data)
    parlay = build_parlay(games_data, odds_data)
    bet = get_bet_pick(games_data, odds_data)
    
    # Generate report
    report = generate_report(games_data, odds_data, lineup, pivots, parlay, bet)
    
    if args.dry_run:
        print(report)
        return
    
    # Write to log
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    output_file = LOG_DIR / f"{args.date}.md"
    with open(output_file, "w") as f:
        f.write(report)
    
    print(f"[Pete NBA] Report written: {output_file}")


if __name__ == "__main__":
    main()
