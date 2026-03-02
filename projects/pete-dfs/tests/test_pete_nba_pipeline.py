import importlib.util
import json
import os
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[3]
SCRIPT_PATH = ROOT / "projects" / "pete-dfs" / "scripts" / "pete-nba-pipeline.py"
FIXTURES = ROOT / "projects" / "pete-dfs" / "fixtures"


def load_module():
    spec = importlib.util.spec_from_file_location("pete_nba_pipeline", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
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

    def test_load_prop_candidates_reads_last5_data(self):
        props = self.module.load_prop_candidates(str(FIXTURES / "sample_props.json"))
        self.assertGreaterEqual(len(props), 1)
        first = props[0]
        self.assertIn(first["market"], {"PTS", "REB", "AST", "STL", "3PM"})
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


if __name__ == "__main__":
    unittest.main()
