import importlib.util
import json
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[3]
SCRIPT_PATH = ROOT / "projects" / "pete-dfs" / "scripts" / "PeteDFS_engine.py"


def _find_spec(name: str):
    return importlib.util.find_spec(name)


PANDAS_AVAILABLE = _find_spec("pandas") is not None
NUMPY_AVAILABLE = _find_spec("numpy") is not None


def load_module():
    spec = importlib.util.spec_from_file_location("pete_dfs_engine", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module spec for {SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    # Python 3.9 dataclass/module inspection needs this entry before exec_module.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@unittest.skipUnless(PANDAS_AVAILABLE and NUMPY_AVAILABLE, "pandas/numpy not available in this environment")
class PeteDFSEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import pandas as pd

        cls.pd = pd
        cls.module = load_module()

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
            result = self.module.run_pete_dfs_engine(
                path,
                run_date="2026-03-03",
                lookback_days=5,
                train_days=2,
                refresh_injuries=False,
            )

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
            run_date="2026-03-03",
            smokies=[{"player": "PG A", "delta": 3.2}],
        )

        self.assertEqual(payload["module"], "pete_dfs")
        self.assertEqual(payload["queue_item"]["status"], "done")
        self.assertEqual(payload["dfs_lineup"]["selected_count"], 2)
        self.assertEqual(payload["dfs_lineup"]["salary_used"], 19700.0)
        self.assertEqual(len(payload["dfs_lineup"]["smokies"]), 1)
        self.assertIn("injury_source_summary", payload)
        self.assertIn("h2h_summary", payload)
        self.assertEqual(payload["queue_item"]["call_id"], "pete-dfs-2026-03-03-early")

    def test_apply_injury_overlays_uses_csv_as_source_of_truth(self):
        candidates = self.pd.DataFrame(
            [
                {"Name": "Player Out", "Position": "PG", "Salary": 9000, "Form": 30, "Playing Status": "Probable", "Team": "LAL"},
                {"Name": "Player Q", "Position": "SG", "Salary": 8800, "Form": 28, "Playing Status": "Questionable", "Team": "LAL"},
                {"Name": "Player Ok", "Position": "SF", "Salary": 8500, "Form": 27, "Playing Status": "", "Team": "LAL"},
            ]
        )
        injury_index = {
            "records": {
                ("LAL", "player out"): {"status": "Out", "detail": "ankle", "category": "out"},
                ("LAL", "player q"): {"status": "Questionable", "detail": "illness", "category": "questionable"},
            },
            "name_records": {},
            "count": 2,
            "source": "/tmp/latest.json",
        }
        out, summary = self.module.apply_injury_overlays(candidates, injury_index, questionable_penalty=1.25)

        # CSV says Probable, so ESPN "Out" does not override.
        self.assertEqual(summary["rows_removed_hard_out"], 0)
        self.assertEqual(summary["questionable_soft_penalized"], 1)
        self.assertEqual(summary["source_of_truth"], "draftstars_csv")
        self.assertEqual(len(out.index), 3)
        q_row = out[out["Name"] == "Player Q"].iloc[0]
        self.assertEqual(q_row["Merged Status"], "questionable")
        self.assertAlmostEqual(float(q_row["InjuryPenalty"]), 1.25, places=3)
        out_row = out[out["Name"] == "Player Out"].iloc[0]
        self.assertEqual(out_row["Merged Status"], "probable")

    def test_apply_h2h_adjustments_blends_and_caps(self):
        candidates = self.pd.DataFrame(
            [
                {"Name": "Test Player", "Position": "PG", "Salary": 9000, "Form": 20.0, "Playing Status": "", "Team": "LAL"},
            ]
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            root = pathlib.Path(tmpdir)
            season_dir = root / "nba" / "season=2025-26"
            processed = season_dir / "processed" / "player_boxscore_jsonl"
            processed.mkdir(parents=True, exist_ok=True)

            schedule = {
                "games": [
                    {"game_id": "g_today", "game_date": "2026-03-03", "home_team": "LAL", "away_team": "DEN", "status_num": 1},
                    {"game_id": "g1", "game_date": "2026-02-25", "home_team": "LAL", "away_team": "DEN", "status_num": 3},
                    {"game_id": "g2", "game_date": "2026-02-20", "home_team": "DEN", "away_team": "LAL", "status_num": 3},
                    {"game_id": "g3", "game_date": "2026-02-15", "home_team": "LAL", "away_team": "DEN", "status_num": 3},
                ]
            }
            (season_dir / "schedule.json").write_text(json.dumps(schedule), encoding="utf-8")

            game_rows = [
                {"game_id": "g1", "game_date": "2026-02-25", "team": "LAL", "player_name": "Test Player", "points": 25, "rebounds": 6, "assists": 4, "steals": 2, "turnovers": 2},
                {"game_id": "g2", "game_date": "2026-02-20", "team": "LAL", "player_name": "Test Player", "points": 22, "rebounds": 5, "assists": 5, "steals": 1, "turnovers": 1},
                {"game_id": "g3", "game_date": "2026-02-15", "team": "LAL", "player_name": "Test Player", "points": 24, "rebounds": 7, "assists": 3, "steals": 1, "turnovers": 2},
            ]
            for gid in ["g1", "g2", "g3"]:
                rows = [row for row in game_rows if row["game_id"] == gid]
                text = "\n".join(json.dumps(row) for row in rows)
                (processed / f"{gid}.jsonl").write_text(text + "\n", encoding="utf-8")

            out, summary = self.module.apply_h2h_adjustments(
                candidates,
                run_date="2026-03-03",
                data_root=root,
                weight=0.5,
                cap_abs=4.0,
                min_samples=3,
            )
            self.assertEqual(summary["players_with_h2h"], 1)
            self.assertEqual(summary["players_adjusted"], 1)
            row = out.iloc[0]
            self.assertEqual(row["Opponent"], "DEN")
            self.assertEqual(int(row["H2HSamples"]), 3)
            self.assertLessEqual(abs(float(row["H2HAdj"])), 4.0)

    def test_tank01_mapping_and_props_adjustment(self):
        candidates = self.pd.DataFrame(
            [
                {"Name": "Jaylen Brown", "Position": "SG", "Salary": 12000, "Form": 40.0, "Playing Status": "", "Team": "BOS"},
                {"Name": "Unknown Player", "Position": "PF", "Salary": 7000, "Form": 24.0, "Playing Status": "", "Team": "LAL"},
            ]
        )
        players_index = {
            "source": "/tmp/players.json",
            "by_name": {
                "jaylen brown": {"player_id": "111", "name": "Jaylen Brown", "team": "BOS", "pos": "SG"},
            },
            "by_id": {},
        }
        props_index = {
            "source": "/tmp/props.json",
            "games": 1,
            "players_with_props": 1,
            "by_player_id": {
                "111": {"player_id": "111", "prop_fp": 46.0, "prop_bets": {"pts": "25.5", "reb": "6.5", "ast": "5.5"}}
            },
        }

        mapped, map_summary = self.module.apply_tank01_player_mapping(candidates, players_index)
        self.assertEqual(map_summary["matched"], 1)
        self.assertEqual(mapped.iloc[0]["Tank01PlayerID"], "111")

        adjusted, prop_summary = self.module.apply_tank01_prop_projection_signal(mapped, props_index, weight=0.2, cap_abs=8.0)
        self.assertEqual(prop_summary["players_with_props"], 1)
        self.assertGreater(float(adjusted.iloc[0]["Tank01PropAdj"]), 0)
        self.assertTrue(self.pd.isna(adjusted.iloc[1]["Tank01PropFP"]))

    def test_write_mission_control_payload_creates_json_file(self):
        payload = {"module": "pete_dfs", "queue_item": {"status": "done"}}
        with tempfile.TemporaryDirectory() as tmpdir:
            target = pathlib.Path(tmpdir) / "out" / "pete-dfs.json"
            saved = self.module.write_mission_control_payload(payload, target)
            self.assertEqual(saved, target)
            self.assertTrue(saved.exists())


if __name__ == "__main__":
    unittest.main()
