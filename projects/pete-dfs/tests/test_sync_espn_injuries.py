import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[3]
SCRIPT_PATH = ROOT / "projects" / "pete-dfs" / "scripts" / "sync_espn_injuries.py"


def load_module():
    spec = importlib.util.spec_from_file_location("sync_espn_injuries", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SyncEspnInjuriesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()

    def test_extract_events(self):
        payload = {
            "events": [
                {
                    "id": "401123456",
                    "competitions": [
                        {
                            "competitors": [
                                {"homeAway": "home", "team": {"abbreviation": "LAL"}},
                                {"homeAway": "away", "team": {"abbreviation": "DEN"}},
                            ]
                        }
                    ],
                }
            ]
        }
        rows = self.module.extract_events(payload)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["home"], "LAL")
        self.assertEqual(rows[0]["away"], "DEN")

    def test_extract_injuries_from_summary(self):
        payload = {
            "boxscore": {
                "players": [
                    {
                        "team": {"abbreviation": "LAL"},
                        "statistics": [
                            {
                                "athletes": [
                                    {
                                        "athlete": {"displayName": "LeBron James"},
                                        "injuries": [{"status": "Out", "details": "ankle"}],
                                    }
                                ]
                            }
                        ],
                    }
                ]
            }
        }
        rows = self.module.extract_injuries_from_summary(payload)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["team"], "LAL")
        self.assertEqual(rows[0]["player"], "LeBron James")

    def test_build_output_major_out_team(self):
        rows = [{"player": "LeBron James", "team": "LAL", "status": "Out", "detail": "ankle"}]
        out = self.module.build_output("2026-03-02", rows)
        self.assertIn("LAL", out["major_out_teams"])


if __name__ == "__main__":
    unittest.main()
