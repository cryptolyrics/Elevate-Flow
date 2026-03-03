import importlib.util
import json
import os
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[3]
SCRIPT_PATH = ROOT / "projects" / "pete-dfs" / "scripts" / "pete-nba-pipeline.py"
FIXTURES = ROOT / "projects" / "pete-dfs" / "fixtures"
MARKETS = {"PTS", "REB", "AST", "STL", "BLK", "TOV", "3PM", "PR", "PA", "RA", "PRA", "SB"}


def load_module():
    spec = importlib.util.spec_from_file_location("pete_nba_pipeline", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module spec for {SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class PetePipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()

    def setUp(self):
        self._prev_enable = os.environ.get("PETE_ENABLE_WAGERING")

    def tearDown(self):
        if self._prev_enable is None:
            os.environ.pop("PETE_ENABLE_WAGERING", None)
        else:
            os.environ["PETE_ENABLE_WAGERING"] = self._prev_enable

    def test_decimal_to_aus_conversion(self):
        self.assertEqual(self.module.decimal_to_aus(2.25), "+125")
        self.assertEqual(self.module.decimal_to_aus(1.50), "-200")

    def test_build_parlay_disabled_without_quant_enable(self):
        odds_data = json.loads((FIXTURES / "sample_odds.json").read_text())
        games_data = json.loads((FIXTURES / "sample_games.json").read_text())

        rules = {
            "enabled": False,
            "max_single_bet_decimal_odds": 3.0,
            "max_parlay_legs": 3,
        }
        parlay = self.module.build_parlay(games_data, odds_data, rules)
        self.assertEqual(parlay["legs"], [])
        self.assertIn("NO_PARLAY", parlay["edge_notes"])

    def test_get_bet_pick_returns_no_bet_by_default(self):
        odds_data = json.loads((FIXTURES / "sample_odds.json").read_text())
        games_data = json.loads((FIXTURES / "sample_games.json").read_text())

        rules = {
            "enabled": False,
            "min_edge_pct": 0.03,
            "min_model_prob": 0.52,
            "max_single_bet_decimal_odds": 3.0,
        }
        bet = self.module.get_bet_pick(games_data, odds_data, rules)
        self.assertEqual(bet["pick"], "NO_BET")
        self.assertIn("reason", bet)

    def test_get_bet_pick_respects_b2b_filter(self):
        os.environ["PETE_ENABLE_WAGERING"] = "1"
        odds_data = {
            "games": [
                {
                    "home": "Lakers",
                    "away": "Warriors",
                    "odds": {"Lakers": 1.90},
                }
            ]
        }
        rules = {
            "enabled": True,
            "min_edge_pct": 0.02,
            "min_model_prob": 0.52,
            "min_edge_dollars_per_1u": 0.01,
            "home_team_model_boost_pct": 0.10,
            "max_single_bet_decimal_odds": 3.0,
        }
        bet = self.module.get_bet_pick(
            {},
            odds_data,
            rules=rules,
            no_b2b_teams={"lakers"},
            major_out_teams=set(),
        )
        self.assertEqual(bet["pick"], "NO_BET")
        self.assertIn("B2B", bet["reason"].upper())

    def test_get_bet_pick_selects_candidate_when_enabled(self):
        os.environ["PETE_ENABLE_WAGERING"] = "1"
        odds_data = {
            "games": [
                {
                    "home": "Lakers",
                    "away": "Warriors",
                    "odds": {"Lakers": 2.30, "Warriors": 1.70},
                }
            ]
        }
        rules = {
            "enabled": True,
            "min_edge_pct": 0.02,
            "min_model_prob": 0.52,
            "min_edge_dollars_per_1u": 0.01,
            "home_team_model_boost_pct": 0.10,
            "max_single_bet_decimal_odds": 3.0,
        }
        bet = self.module.get_bet_pick(
            {},
            odds_data,
            rules=rules,
            learning_state={"team_adjustments": {}},
            no_b2b_teams=set(),
            major_out_teams=set(),
        )
        self.assertNotEqual(bet["pick"], "NO_BET")
        self.assertGreaterEqual(bet["edge_dollars_per_1u"], 0.01)

    def test_get_bet_pick_reason_reports_ev_gate(self):
        os.environ["PETE_ENABLE_WAGERING"] = "1"
        odds_data = {
            "games": [
                {
                    "home": "Lakers",
                    "away": "Warriors",
                    "odds": {"Lakers": 2.30, "Warriors": 1.70},
                }
            ]
        }
        rules = {
            "enabled": True,
            "min_edge_pct": 0.02,
            "min_model_prob": 0.52,
            "min_edge_dollars_per_1u": 0.50,
            "home_team_model_boost_pct": 0.10,
            "max_single_bet_decimal_odds": 3.0,
        }
        bet = self.module.get_bet_pick(
            {},
            odds_data,
            rules=rules,
            learning_state={"team_adjustments": {}},
            no_b2b_teams=set(),
            major_out_teams=set(),
        )
        self.assertEqual(bet["pick"], "NO_BET")
        self.assertIn("min_edge_dollars_per_1u", bet.get("reason", ""))

    def test_team_parlay_can_be_looser_than_single_bet(self):
        os.environ["PETE_ENABLE_WAGERING"] = "1"
        odds_data = {
            "games": [
                {"home": "Lakers", "away": "Warriors", "odds": {"Lakers": 2.30, "Warriors": 1.70}},
                {"home": "Bucks", "away": "Celtics", "odds": {"Bucks": 2.20, "Celtics": 1.75}},
            ]
        }
        rules = {
            "enabled": True,
            "min_edge_pct": 0.03,
            "min_model_prob": 0.52,
            "min_edge_dollars_per_1u": 0.30,
            "parlay_min_edge_pct": 0.03,
            "parlay_min_edge_dollars_per_1u": 0.10,
            "parlay_min_legs": 2,
            "home_team_model_boost_pct": 0.10,
            "max_single_bet_decimal_odds": 3.0,
            "max_parlay_legs": 3,
        }

        bet = self.module.get_bet_pick(
            {},
            odds_data,
            rules=rules,
            learning_state={"team_adjustments": {}},
            no_b2b_teams=set(),
            major_out_teams=set(),
        )
        self.assertEqual(bet["pick"], "NO_BET")

        parlay = self.module.build_parlay(
            {},
            odds_data,
            rules,
            learning_state={"team_adjustments": {}},
            no_b2b_teams=set(),
            major_out_teams=set(),
        )
        self.assertGreaterEqual(len(parlay["legs"]), 2)

    def test_load_prop_candidates_reads_last5_data(self):
        props = self.module.load_prop_candidates(str(FIXTURES / "sample_props.json"))
        self.assertGreaterEqual(len(props), 1)
        first = props[0]
        self.assertIn(first["market"], MARKETS)
        self.assertEqual(len(first["last5"]), 5)

    def test_build_player_prop_parlay_applies_safety_haircut(self):
        os.environ["PETE_ENABLE_WAGERING"] = "1"
        props = self.module.load_prop_candidates(str(FIXTURES / "sample_props.json"))
        rules = {
            "enabled": True,
            "prop_call_haircut_pct": 0.10,
            "prop_min_line_edge": 0.2,
            "prop_min_model_edge_pct": 0.01,
            "prop_max_legs": 3,
            "prop_trend_weight": 0.35,
        }
        parlay = self.module.build_player_prop_parlay(
            props,
            rules,
            learning_state={"player_prop_adjustments": {}},
            dfs_projection_map={"j murray": 42.0},
        )
        self.assertTrue(parlay["legs"])
        leg = parlay["legs"][0]
        self.assertGreaterEqual(leg["haircut_pct"], 10.0)
        self.assertIn(leg["direction"], {"OVER", "UNDER"})

    def test_build_player_prop_parlay_disabled_without_quant_enable(self):
        props = self.module.load_prop_candidates(str(FIXTURES / "sample_props.json"))
        parlay = self.module.build_player_prop_parlay(props, {"enabled": False})
        self.assertEqual(parlay["legs"], [])
        self.assertIn("NO_PROP_PARLAY", parlay["note"])

    def test_build_player_prop_parlay_avoids_same_player_multi_market(self):
        os.environ["PETE_ENABLE_WAGERING"] = "1"
        candidates = [
            {
                "player": "Player A",
                "team": "AAA",
                "opponent": "BBB",
                "market": "PTS",
                "line": 20.5,
                "odds_over": 1.9,
                "odds_under": 1.9,
                "last5": [26, 25, 24, 23, 22],
                "game": "AAA @ BBB",
            },
            {
                "player": "Player A",
                "team": "AAA",
                "opponent": "BBB",
                "market": "AST",
                "line": 5.5,
                "odds_over": 1.9,
                "odds_under": 1.9,
                "last5": [8, 8, 7, 7, 6],
                "game": "AAA @ BBB",
            },
            {
                "player": "Player B",
                "team": "CCC",
                "opponent": "DDD",
                "market": "REB",
                "line": 7.5,
                "odds_over": 1.9,
                "odds_under": 1.9,
                "last5": [11, 10, 9, 9, 8],
                "game": "CCC @ DDD",
            },
            {
                "player": "Player C",
                "team": "EEE",
                "opponent": "FFF",
                "market": "3PM",
                "line": 2.5,
                "odds_over": 1.9,
                "odds_under": 1.9,
                "last5": [5, 4, 4, 3, 3],
                "game": "EEE @ FFF",
            },
        ]
        rules = {
            "enabled": True,
            "prop_call_haircut_pct": 0.10,
            "prop_min_line_edge": 0.2,
            "prop_min_model_edge_pct": 0.01,
            "prop_max_legs": 3,
            "prop_trend_weight": 0.35,
        }
        parlay = self.module.build_player_prop_parlay(candidates, rules, learning_state={"player_prop_adjustments": {}}, dfs_projection_map={})
        players = [row.get("player") for row in parlay.get("legs", [])]
        self.assertEqual(len(players), len(set(players)))

    def test_load_espn_major_out_teams_from_fixture(self):
        teams = self.module.load_espn_major_out_teams(str(FIXTURES / "sample_espn_injuries.json"))
        self.assertIn("lal", teams)

    def test_load_tank01_odds_and_merge(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = pathlib.Path(tmpdir)
            props_dir = root / "nba" / "betting-props"
            props_dir.mkdir(parents=True, exist_ok=True)
            sample_props = json.loads((FIXTURES / "sample_tank01_props.json").read_text())
            (props_dir / "2026-03-02.json").write_text(json.dumps(sample_props), encoding="utf-8")

            tank01 = self.module.load_tank01_odds("2026-03-03", str(root), max_lag_days=2)
            self.assertEqual(len(tank01["games"]), 1)
            self.assertEqual(tank01["source_lag_days"], 1)

            merged = self.module.merge_odds_data({"games": []}, tank01)
            self.assertEqual(len(merged["games"]), 1)
            game = merged["games"][0]
            self.assertIn("BOS", game["odds"])
            self.assertIn("MIL", game["odds"])
            self.assertGreater(game["odds"]["BOS"], 1.0)
            self.assertIsInstance(game.get("market_context", {}), dict)

    def test_prop_context_bias_penalizes_under_for_high_total_favorite(self):
        odds_data = {
            "games": [
                {
                    "home": "UTA",
                    "away": "DEN",
                    "home_code": "UTA",
                    "away_code": "DEN",
                    "odds": {"DEN": 1.20, "UTA": 4.50},
                    "market_context": {
                        "consensus_total": 241.5,
                        "spread_by_team": {"DEN": -12.0, "UTA": 12.0},
                    },
                }
            ]
        }
        context = self.module.build_prop_game_context(odds_data)
        rules = {
            "prop_context_bias_step": 0.02,
            "prop_context_max_bias": 0.05,
            "prop_context_total_over_threshold": 233.0,
            "prop_context_total_under_threshold": 220.0,
            "prop_context_favorite_spread_threshold": 6.5,
        }
        under_bias = self.module.prop_game_context_bias(
            {"team": "DEN", "opponent": "UTA", "market": "PTS"},
            "UNDER",
            context,
            rules,
        )
        over_bias = self.module.prop_game_context_bias(
            {"team": "DEN", "opponent": "UTA", "market": "PTS"},
            "OVER",
            context,
            rules,
        )
        self.assertLess(under_bias, 0.0)
        self.assertGreater(over_bias, 0.0)

    def test_load_tank01_games_from_props_snapshot(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = pathlib.Path(tmpdir)
            props_dir = root / "nba" / "betting-props"
            props_dir.mkdir(parents=True, exist_ok=True)
            sample_props = json.loads((FIXTURES / "sample_tank01_props.json").read_text())
            (props_dir / "2026-03-02.json").write_text(json.dumps(sample_props), encoding="utf-8")

            games = self.module.load_tank01_games("2026-03-03", str(root), max_lag_days=2)
            self.assertEqual(len(games["games"]), 1)
            first = games["games"][0]
            self.assertEqual(first["home_code"], "MIL")
            self.assertEqual(first["away_code"], "BOS")
            self.assertEqual(games["source_lag_days"], 1)

    def test_infer_slate_date_prefers_tank01_snapshot_path(self):
        inferred = self.module.infer_slate_date(
            "2026-03-03",
            {"tank01_odds_source": "/tmp/snapshots/2026-03-02.json"},
            {"games": []},
        )
        self.assertEqual(inferred, "2026-03-02")

    def test_infer_slate_date_uses_odds_start_when_path_missing(self):
        inferred = self.module.infer_slate_date(
            "2026-03-03",
            {"tank01_odds_source": ""},
            {"games": [{"start": "20260302"}]},
        )
        self.assertEqual(inferred, "2026-03-02")

    def test_resolve_market_feeds_prefers_tank01(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = pathlib.Path(tmpdir)
            props_dir = root / "nba" / "betting-props"
            props_dir.mkdir(parents=True, exist_ok=True)
            sample_props = json.loads((FIXTURES / "sample_tank01_props.json").read_text())
            (props_dir / "2026-03-02.json").write_text(json.dumps(sample_props), encoding="utf-8")

            games, odds, summary = self.module.resolve_market_feeds(
                season="2026",
                run_date="2026-03-03",
                tank01_enable=True,
                tank01_data_root=str(root),
                tank01_max_lag_days=2,
                api_sports_fallback=True,
            )
            self.assertEqual(summary["primary"], "tank01")
            self.assertFalse(summary["fallback_used"])
            self.assertEqual(len(games["games"]), 1)
            self.assertEqual(len(odds["games"]), 1)

    def test_load_tank01_major_out_teams_from_fixture(self):
        teams = self.module.load_tank01_major_out_teams(
            "2026-03-03",
            str(FIXTURES),
            max_lag_days=2,
            explicit_injuries_json=str(FIXTURES / "sample_tank01_injuries.json"),
        )
        self.assertIn("lal", teams)

    def test_load_tank01_prop_candidates_with_h2h(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = pathlib.Path(tmpdir)
            props_dir = root / "nba" / "betting-props"
            players_dir = root / "nba" / "players"
            props_dir.mkdir(parents=True, exist_ok=True)
            players_dir.mkdir(parents=True, exist_ok=True)

            sample_props = json.loads((FIXTURES / "sample_tank01_props.json").read_text())
            sample_players = json.loads((FIXTURES / "sample_tank01_players.json").read_text())
            (props_dir / "2026-03-02.json").write_text(json.dumps(sample_props), encoding="utf-8")
            (players_dir / "2026-03-02.json").write_text(json.dumps(sample_players), encoding="utf-8")

            h2h = {
                "matchups": [
                    {
                        "player": "Jaylen Brown",
                        "team": "BOS",
                        "opponent": "MIL",
                        "market": "PTS",
                        "values": [27, 25, 31, 22, 29],
                    }
                ]
            }
            h2h_path = root / "h2h.json"
            h2h_path.write_text(json.dumps(h2h), encoding="utf-8")

            candidates, meta = self.module.load_tank01_prop_candidates(
                "2026-03-03",
                str(root),
                h2h_json_path=str(h2h_path),
                max_lag_days=2,
                default_odds=1.9,
            )
            self.assertGreaterEqual(len(candidates), 1)
            first = candidates[0]
            self.assertIn(first["market"], MARKETS)
            self.assertEqual(len(first["last5"]), 5)
            self.assertEqual(meta["source_lag_days"], 1)

    def test_load_tank01_prop_candidates_falls_back_to_seeded_history(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = pathlib.Path(tmpdir)
            props_dir = root / "nba" / "betting-props"
            players_dir = root / "nba" / "players"
            props_dir.mkdir(parents=True, exist_ok=True)
            players_dir.mkdir(parents=True, exist_ok=True)

            sample_props = json.loads((FIXTURES / "sample_tank01_props.json").read_text())
            sample_players = json.loads((FIXTURES / "sample_tank01_players.json").read_text())
            (props_dir / "2026-03-02.json").write_text(json.dumps(sample_props), encoding="utf-8")
            (players_dir / "2026-03-02.json").write_text(json.dumps(sample_players), encoding="utf-8")

            candidates, meta = self.module.load_tank01_prop_candidates(
                "2026-03-03",
                str(root),
                h2h_json_path="",
                max_lag_days=2,
                default_odds=1.9,
            )
            self.assertGreaterEqual(len(candidates), 1)
            self.assertGreater(meta.get("synthetic_history_candidates", 0), 0)
            first = candidates[0]
            self.assertEqual(first.get("history_source"), "synthetic_line")
            self.assertEqual(len(first.get("last5", [])), 5)
            markets = {row.get("market") for row in candidates}
            self.assertTrue({"PTS", "REB", "AST", "STL", "3PM"}.issubset(markets))

    def test_load_tank01_prop_candidates_prefers_local_opponent_h2h_and_filters_low_minutes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = pathlib.Path(tmpdir)
            props_dir = root / "nba" / "betting-props"
            players_dir = root / "nba" / "players"
            boxscore_dir = root / "nba" / "season=2025-26" / "processed" / "player_boxscore_jsonl"
            props_dir.mkdir(parents=True, exist_ok=True)
            players_dir.mkdir(parents=True, exist_ok=True)
            boxscore_dir.mkdir(parents=True, exist_ok=True)

            sample_props = json.loads((FIXTURES / "sample_tank01_props.json").read_text())
            sample_players = json.loads((FIXTURES / "sample_tank01_players.json").read_text())
            (props_dir / "2026-03-02.json").write_text(json.dumps(sample_props), encoding="utf-8")
            (players_dir / "2026-03-02.json").write_text(json.dumps(sample_players), encoding="utf-8")

            # 6 BOS vs MIL games for Jaylen Brown PTS; one low-minute game should be filtered as injury-noise.
            game_rows = [
                ("g1", "2026-02-28", 34.0, 27.0),
                ("g2", "2026-02-24", 36.0, 29.0),
                ("g3", "2026-02-20", 35.0, 31.0),
                ("g4", "2026-02-15", 33.0, 26.0),
                ("g5", "2026-02-10", 32.0, 28.0),
                ("g6", "2026-02-05", 6.0, 2.0),
            ]
            for gid, game_date, minutes, points in game_rows:
                rows = [
                    {
                        "game_id": gid,
                        "game_date": game_date,
                        "team": "BOS",
                        "player_name": "Jaylen Brown",
                        "minutes": minutes,
                        "points": points,
                        "rebounds": 6,
                        "assists": 4,
                        "steals": 1,
                        "three_pm": 3,
                    },
                    {
                        "game_id": gid,
                        "game_date": game_date,
                        "team": "MIL",
                        "player_name": "Giannis Antetokounmpo",
                        "minutes": 36.0,
                        "points": 30,
                        "rebounds": 10,
                        "assists": 6,
                        "steals": 1,
                        "three_pm": 1,
                    },
                ]
                (boxscore_dir / f"{gid}.jsonl").write_text(
                    "\n".join(json.dumps(row) for row in rows) + "\n",
                    encoding="utf-8",
                )

            candidates, meta = self.module.load_tank01_prop_candidates(
                "2026-03-03",
                str(root),
                h2h_json_path="",
                max_lag_days=2,
                default_odds=1.9,
            )
            target = next(
                (row for row in candidates if row.get("player") == "Jaylen Brown" and row.get("market") == "PTS"),
                None,
            )
            self.assertIsNotNone(target)
            self.assertEqual(target.get("history_source"), "local_h2h")
            self.assertEqual(len(target.get("last5", [])), 5)
            self.assertGreater(target.get("history_noise_removed", 0), 0)
            self.assertGreater(meta.get("history_noise_removed_total", 0), 0)
            self.assertGreater(min(target.get("last5", [0])), 5.0)


if __name__ == "__main__":
    unittest.main()
