import importlib.util
import pathlib
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[3]
SCRIPT_PATH = ROOT / "projects" / "pete-dfs" / "scripts" / "PeteDFS_engine.py"


def _find_spec(name: str):
    return importlib.util.find_spec(name)


PANDAS_AVAILABLE = _find_spec("pandas") is not None
NUMPY_AVAILABLE = _find_spec("numpy") is not None


@unittest.skipUnless(PANDAS_AVAILABLE and NUMPY_AVAILABLE, "pandas/numpy not available in this environment")
class PeteDFSEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import pandas as pd

        cls.pd = pd
        spec = importlib.util.spec_from_file_location("pete_dfs_engine", SCRIPT_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        cls.module = module

    def test_extract_player_fpts_from_summary_uses_labels(self):
        payload = {
            "boxscore": {
                "players": [
                    {
                        "team": {"abbreviation": "LAL"},
                        "statistics": [
                            {
                                "labels": [
                                    "MIN",
                                    "FG",
                                    "3PT",
                                    "FT",
                                    "OREB",
                                    "DREB",
                                    "REB",
                                    "AST",
                                    "STL",
                                    "BLK",
                                    "TO",
                                    "PF",
                                    "PTS",
                                ],
                                "athletes": [
                                    {
                                        "athlete": {"displayName": "Test Player"},
                                        "stats": ["33", "8-16", "2-7", "2-2", "2", "8", "10", "5", "2", "1", "3", "2", "20"],
                                    }
                                ],
                            }
                        ],
                    }
                ]
            }
        }

        rows = self.module.extract_player_fpts_from_summary(payload)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["Name"], "Test Player")
        self.assertAlmostEqual(rows[0]["FP"], 44.5, places=4)

    def test_run_rolling_backtest_returns_metrics(self):
        rows = []
        for day in range(1, 10):
            date = f"2026-02-{day:02d}"
            rows.extend(
                [
                    {"Date": date, "Name": "Player A", "FP": 30 + day},
                    {"Date": date, "Name": "Player B", "FP": 20 + day * 0.5},
                    {"Date": date, "Name": "Player C", "FP": 15 + day * 0.2},
                ]
            )
        history = self.pd.DataFrame(rows)
        metrics = self.module.run_rolling_backtest(history, train_days=3)

        self.assertGreater(metrics["samples"], 0)
        self.assertGreater(metrics["windows"], 0)
        self.assertIsInstance(metrics["mae"], float)
        self.assertIsInstance(metrics["rmse"], float)

    def test_optimize_dfs_lineup_respects_unique_player_constraint(self):
        if not self.module.SCIPY_AVAILABLE:
            self.skipTest("scipy not available")

        candidates = self.pd.DataFrame(
            [
                {"Name": "PG A", "Position": "PG", "Salary": 10000, "Form": 40, "Playing Status": ""},
                {"Name": "PG B", "Position": "PG/SG", "Salary": 9900, "Form": 39, "Playing Status": ""},
                {"Name": "PG B", "Position": "PG", "Salary": 9800, "Form": 37, "Playing Status": ""},
                {"Name": "SG A", "Position": "SG", "Salary": 9200, "Form": 36, "Playing Status": ""},
                {"Name": "SG B", "Position": "SG", "Salary": 9000, "Form": 35, "Playing Status": ""},
                {"Name": "SF A", "Position": "SF", "Salary": 9100, "Form": 36, "Playing Status": ""},
                {"Name": "SF B", "Position": "SF", "Salary": 8800, "Form": 34, "Playing Status": ""},
                {"Name": "PF A", "Position": "PF", "Salary": 9300, "Form": 37, "Playing Status": ""},
                {"Name": "PF B", "Position": "PF", "Salary": 8600, "Form": 33, "Playing Status": ""},
                {"Name": "C A", "Position": "C", "Salary": 9700, "Form": 38, "Playing Status": ""},
            ]
        )

        result = self.module.optimize_dfs_lineup(candidates, variance_map={}, salary_cap=100000, risk_penalty=0.1)
        self.assertTrue(result["success"])

        lineup = result["lineup"]
        self.assertEqual(len(lineup.index), 9)
        self.assertEqual(len(lineup["Name"].unique()), 9)

    def test_run_engine_with_stubbed_history(self):
        if not self.module.SCIPY_AVAILABLE:
            self.skipTest("scipy not available")

        daily = self.pd.DataFrame(
            [
                {"Name": "PG A", "Position": "PG", "Salary": 10000, "Form": 40, "Playing Status": ""},
                {"Name": "PG B", "Position": "PG", "Salary": 9900, "Form": 39, "Playing Status": ""},
                {"Name": "SG A", "Position": "SG", "Salary": 9200, "Form": 36, "Playing Status": ""},
                {"Name": "SG B", "Position": "SG", "Salary": 9000, "Form": 35, "Playing Status": ""},
                {"Name": "SF A", "Position": "SF", "Salary": 9100, "Form": 36, "Playing Status": ""},
                {"Name": "SF B", "Position": "SF", "Salary": 8800, "Form": 34, "Playing Status": ""},
                {"Name": "PF A", "Position": "PF", "Salary": 9300, "Form": 37, "Playing Status": ""},
                {"Name": "PF B", "Position": "PF", "Salary": 8600, "Form": 33, "Playing Status": ""},
                {"Name": "C A", "Position": "C", "Salary": 9700, "Form": 38, "Playing Status": ""},
            ]
        )

        history = self.pd.DataFrame(
            [
                {"Date": "2026-02-20", "Name": "PG A", "FP": 40.0},
                {"Date": "2026-02-20", "Name": "C A", "FP": 37.0},
                {"Date": "2026-02-21", "Name": "PG A", "FP": 42.0},
                {"Date": "2026-02-21", "Name": "C A", "FP": 35.0},
                {"Date": "2026-02-22", "Name": "PG A", "FP": 41.0},
                {"Date": "2026-02-22", "Name": "C A", "FP": 38.0},
                {"Date": "2026-02-23", "Name": "PG A", "FP": 39.0},
                {"Date": "2026-02-23", "Name": "C A", "FP": 36.0},
            ]
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as handle:
            daily.to_csv(handle.name, index=False)
            path = handle.name

        with mock.patch.object(self.module, "collect_espn_history_logs", return_value=(history, {"records": 8})):
            result = self.module.run_pete_dfs_engine(path, lookback_days=5, train_days=2)

        self.assertTrue(result.success)
        self.assertEqual(len(result.lineup), 9)
        self.assertIn("records", result.scrape)

    def test_build_mission_control_payload_shapes_queue_item(self):
        result = self.module.EngineResult(
            success=True,
            reason="ok",
            lineup=[
                {"Name": "PG A", "Position": "PG", "Team": "LAL", "Salary": 10000.0, "Form": 40.0, "RiskStd": 1.2},
                {"Name": "C A", "Position": "C", "Team": "DEN", "Salary": 9700.0, "Form": 38.0, "RiskStd": 1.1},
            ],
            total_salary=19700.0,
            projected_form=78.0,
            backtest={"samples": 25, "mae": 6.2},
            scrape={"records": 88},
        )
        payload = self.module.build_mission_control_payload(
            result=result,
            daily_csv_path="/tmp/draftstars.csv",
            slot="early",
            lookback_days=10,
            salary_cap=100000,
            risk_penalty=0.15,
            train_days=7,
            smokies=[{"player": "PG A", "delta": 3.2}],
        )

        self.assertEqual(payload["module"], "pete_dfs")
        self.assertEqual(payload["queue_item"]["status"], "done")
        self.assertEqual(payload["dfs_lineup"]["selected_count"], 2)
        self.assertEqual(payload["dfs_lineup"]["salary_used"], 19700.0)
        self.assertEqual(len(payload["dfs_lineup"]["smokies"]), 1)

    def test_write_mission_control_payload_creates_json_file(self):
        payload = {"module": "pete_dfs", "queue_item": {"status": "done"}}
        with tempfile.TemporaryDirectory() as tmpdir:
            target = pathlib.Path(tmpdir) / "out" / "pete-dfs.json"
            saved = self.module.write_mission_control_payload(payload, target)
            self.assertEqual(saved, target)
            self.assertTrue(saved.exists())


if __name__ == "__main__":
    unittest.main()
