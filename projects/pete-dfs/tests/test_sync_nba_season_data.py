import importlib.util
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[3]
SCRIPT_PATH = ROOT / "projects" / "pete-dfs" / "scripts" / "sync_nba_season_data.py"


def load_module():
    spec = importlib.util.spec_from_file_location("sync_nba_season_data", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module spec for {SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class SyncNbaSeasonDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()

    def test_season_label_and_bounds(self):
        self.assertEqual(self.module.season_label(2025), "2025-26")
        start, end = self.module.season_date_bounds(2025)
        self.assertEqual(start.isoformat(), "2025-09-25")
        self.assertEqual(end.isoformat(), "2026-06-30")

    def test_parse_schedule_games(self):
        payload = {
            "games": [
                {
                    "gameId": "0022500001",
                    "statusNum": 3,
                    "statusText": "Final",
                    "hTeam": {"triCode": "LAL"},
                    "vTeam": {"triCode": "DEN"},
                }
            ]
        }
        rows = self.module.parse_schedule_games(payload, "2025-10-22")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["home_team"], "LAL")
        self.assertEqual(rows[0]["away_team"], "DEN")

    def test_target_game_ids_weekly_selection(self):
        schedule = [
            {"game_id": "1", "game_date": "2026-03-01", "status_num": 2},
            {"game_id": "2", "game_date": "2026-02-01", "status_num": 3},
        ]
        manifest = {"games": {"2": {"boxscore": True, "playbyplay": True}}}
        ids = self.module.target_game_ids(schedule, manifest, weekly=True, lookback_days=10)
        self.assertIn("1", ids)

    def test_flatten_playbyplay(self):
        payload = {
            "game": {
                "actions": [
                    {
                        "actionNumber": 1,
                        "period": 1,
                        "clock": "PT11M55.00S",
                        "teamId": 1610612747,
                        "personId": 2544,
                        "actionType": "shot",
                        "description": "Jumper",
                    }
                ]
            }
        }
        rows = self.module.flatten_playbyplay(payload, "0022500001", "2025-10-22")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["action_type"], "shot")


if __name__ == "__main__":
    unittest.main()
