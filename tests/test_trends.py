"""Evidence validation, scenario calculation, data updates and API acceptance."""

import csv
import shutil
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from career_matching import rank_careers
from main import app
from profile_data import load_catalogue
from test_career_matching import career
from trend_data import (
    describe_trend,
    load_market_signals,
    load_trends,
    market_summary,
)


class TestScenarioScoring(unittest.TestCase):
    def test_scenarios_average_all_required_skills(self):
        role = career()
        moderate = rank_careers(
            [role], ["S01", "S05"], "D1",
            trend_codes={"S01": 1}, scenario_multiplier=1,
        )[0]
        fast = rank_careers(
            [role], ["S01", "S05"], "D1",
            trend_codes={"S01": 1}, scenario_multiplier=2,
        )[0]
        self.assertEqual(moderate.match_score, 50)
        self.assertEqual(moderate.trend_adjustment, 2.5)
        self.assertEqual(moderate.ranking_score, 52.5)
        self.assertEqual(fast.ranking_score, 55)
        self.assertEqual(moderate.known_trend_count, 1)

    def test_score_clamps_and_declines(self):
        role = career(required=("S01",))
        rising = rank_careers(
            [role], ["S01"], "D1",
            trend_codes={"S01": 1}, scenario_multiplier=2,
        )[0]
        declining = rank_careers(
            [role], [], "D1",
            trend_codes={"S01": -1}, scenario_multiplier=2,
        )[0]
        self.assertEqual(rising.ranking_score, 100)
        self.assertEqual(declining.ranking_score, 0)

    def test_trends_affect_ranking_before_degree_tie(self):
        related = career("C1", "A", ("S01", "S05"), ("D1",))
        cross_degree = career("C2", "B", ("S01", "S10"), ("D2",))
        results = rank_careers(
            [related, cross_degree], ["S01"], "D1",
            trend_codes={"S10": 1}, scenario_multiplier=1,
        )
        self.assertEqual(results[0].career.career_id, "C2")
        self.assertEqual(results[0].match_score, results[1].match_score)


class TestEvidenceData(unittest.TestCase):
    def setUp(self):
        _, skills = load_catalogue(ROOT / "data")
        self.skill_ids = {skill["skill_id"] for skill in skills}

    def test_shipped_evidence_and_unknowns(self):
        trends, issues = load_trends(ROOT / "data" / "trends.csv", self.skill_ids)
        self.assertEqual(issues, [])
        self.assertEqual(len(trends), 22)
        self.assertEqual(trends["S10"].trend_direction, "rising")
        self.assertEqual(trends["S01"].trend_direction, "rising")
        self.assertEqual(trends["S02"].trend_direction, "stable")
        self.assertEqual(trends["S03"].trend_direction, "stable")
        self.assertEqual(trends["S05"].trend_direction, "rising")
        self.assertEqual(
            sum(t.trend_direction == "unknown" for t in trends.values()), 3
        )
        self.assertEqual(
            {sid for sid, t in trends.items() if t.trend_direction == "unknown"},
            {"S11", "S18", "S22"},
        )
        self.assertEqual(trends["S12"].trend_direction, "rising")
        self.assertEqual(trends["S20"].trend_direction, "stable")
        self.assertEqual(trends["S17"].source_date_kind, "review")
        missing = describe_trend("UNKNOWN", trends)
        self.assertEqual(missing["trend_direction"], "unknown")
        self.assertEqual(missing["source_url"], "")

    def test_ad_share_directions_match_reviewed_component_observations(self):
        trends, _ = load_trends(ROOT / "data" / "trends.csv", self.skill_ids)
        observed = set()
        with (ROOT / "data" / "trend_observations.csv").open(
            encoding="utf-8", newline=""
        ) as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 15)
        for row in rows:
            growth = (
                Decimal(row["current_share_percent"])
                / Decimal(row["previous_share_percent"]) - 1
            ) * 100
            expected = "stable"
            if growth > 5:
                expected = "rising"
            elif growth < -5:
                expected = "declining"
            trend = trends[row["skill_id"]]
            self.assertEqual(trend.trend_direction, expected)
            self.assertEqual(trend.source_date_kind, "snapshot")
            self.assertIn(
                row["source_url"],
                [trend.source_url, *trend.supporting_urls.split(";")],
            )
            observed.add(row["skill_id"])
        self.assertEqual(len(observed), 13)

    def test_bad_and_duplicate_evidence_cannot_influence_scores(self):
        with (ROOT / "data" / "trends.csv").open(
            encoding="utf-8", newline=""
        ) as handle:
            reader = csv.DictReader(handle)
            fields = reader.fieldnames
            original = next(row for row in reader if row["skill_id"] == "S10")
        changes = [
            {"source_url": "javascript:alert(1)"},
            {"source_name": ""},
            {"source_date": "invalid"},
            {"updated_at": "2020-01-01"},
            {"source_skill": ""},
            {"trend_direction": "invented"},
            {"skill_id": "UNKNOWN"},
            {"source_date_kind": "invented"},
            {"supporting_urls": "javascript:alert(1)"},
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "trends.csv"
            for changeset in changes:
                with self.subTest(changes=changeset):
                    self.write_csv(path, fields, [{**original, **changeset}])
                    trends, issues = load_trends(path, self.skill_ids)
                    self.assertEqual(trends, {})
                    self.assertTrue(issues)
            self.write_csv(path, fields, [original, original, original])
            trends, issues = load_trends(path, self.skill_ids)
            self.assertEqual(trends, {})
            self.assertTrue(issues)

    @staticmethod
    def write_csv(path, fields, rows):
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

    def test_market_comparison_is_separate_and_missing_is_not_zero(self):
        signals, issues = load_market_signals(
            ROOT / "data" / "market_signals.csv", {"C01"}
        )
        self.assertEqual(issues, [])
        summary = market_summary("C01", signals)
        self.assertEqual(
            [row["job_offerings"] for row in summary["records"]], [20089, 19899]
        )
        self.assertAlmostEqual(
            summary["change_percent"], 100 * (19899 - 20089) / 20089
        )
        self.assertIsNone(market_summary("C02", signals)["change_percent"])
        self.assertEqual(market_summary("C02", signals)["records"], [])

    def test_market_zero_base_and_incomparable_periods(self):
        from dataclasses import replace

        signals, _ = load_market_signals(
            ROOT / "data" / "market_signals.csv", {"C01"}
        )
        for replacement in [
            replace(signals[0], job_offerings=0),
            replace(signals[0], period="2025-Q4"),
            replace(signals[0], occupation_name="Different occupation"),
        ]:
            with self.subTest(record=replacement):
                result = market_summary("C01", [replacement, signals[1]])
                self.assertIsNone(result["change_percent"])

    def test_bad_market_records_are_excluded(self):
        with (ROOT / "data" / "market_signals.csv").open(
            encoding="utf-8", newline=""
        ) as handle:
            reader = csv.DictReader(handle)
            fields = reader.fieldnames
            original = next(reader)
        changes = [
            {"period": "2026-Q5"},
            {"job_offerings": "-1"},
            {"job_offerings": "unavailable"},
            {"source_url": ""},
            {"career_id": "UNKNOWN"},
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "market_signals.csv"
            for change in changes:
                with self.subTest(change=change):
                    self.write_csv(path, fields, [{**original, **change}])
                    records, issues = load_market_signals(path, {"C01"})
                    self.assertEqual(records, [])
                    self.assertTrue(issues)
            self.write_csv(path, fields, [original, original])
            records, issues = load_market_signals(path, {"C01"})
            self.assertEqual(records, [])
            self.assertTrue(issues)


class TestTrendsAPI(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def analyse(self, scenario="moderate"):
        return self.client.post(
            "/api/analyse",
            json={
                "degree_id": "D1",
                "user_skill_ids": ["S04"],
                "scenario": scenario,
            },
        )

    def test_scenario_switch_and_evidence_payload(self):
        moderate = self.analyse().json
        fast = self.analyse("fast").json
        first = moderate["matches"][0]
        second = fast["matches"][0]
        self.assertEqual(first["career"]["career_id"], "C04")
        self.assertEqual(first["match_score"], 25)
        self.assertEqual(first["ranking_score"], 22.5)
        self.assertEqual(second["ranking_score"], 20)
        self.assertEqual(first["known_trend_count"], 3)
        self.assertEqual(first["market_signal"]["records"], [])
        self.assertEqual(
            moderate["skill_trends"][0]["trend_direction"], "declining"
        )
        selected = moderate["skill_trends"][0]
        self.assertEqual(selected["source_date_kind"], "snapshot")
        self.assertIn("css.do", selected["supporting_urls"])
        self.assertIn("United Kingdom", selected["geography"])
        source = first["required_skill_trends"][0]
        self.assertTrue(source["source_url"].startswith("https://"))
        self.assertTrue(source["source_date"])
        for invalid in ["invalid", None, [], {}]:
            self.assertEqual(self.analyse(invalid).status_code, 400)

    def test_saved_data_edit_is_reloaded_without_server_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            data_dir = Path(directory) / "data"
            shutil.copytree(ROOT / "data", data_dir)
            with patch("main.DATA_DIR", data_dir):
                original = self.analyse().json
                path = data_dir / "trends.csv"
                # A synthetic test mutation; the shipped evidence is never edited.
                source = path.read_text(encoding="utf-8")
                path.write_text(
                    source.replace("S10,rising,", "S10,declining,"),
                    encoding="utf-8",
                )
                changed = self.analyse().json
        before = next(
            m for m in original["matches"] if m["career"]["career_id"] == "C04"
        )
        after = next(
            m for m in changed["matches"] if m["career"]["career_id"] == "C04"
        )
        self.assertEqual(before["ranking_score"], 22.5)
        self.assertEqual(after["ranking_score"], 17.5)
        self.assertEqual(before["match_score"], after["match_score"])

    def test_trend_failure_falls_back_to_coverage(self):
        with patch("main.load_trends", side_effect=ValueError("Bad CSV")):
            result = self.analyse("fast")
        self.assertEqual(result.status_code, 200)
        self.assertFalse(result.json["trends_available"])
        self.assertTrue(result.json["warnings"])
        for match in result.json["matches"]:
            self.assertEqual(match["ranking_score"], match["match_score"])
            self.assertEqual(match["scenario_multiplier"], 0)

    def test_market_failure_does_not_disable_skill_trends(self):
        with patch("main.load_market_signals", side_effect=OSError("Missing")):
            result = self.analyse()
        self.assertEqual(result.status_code, 200)
        self.assertTrue(result.json["trends_available"])
        self.assertEqual(result.json["matches"][0]["ranking_score"], 22.5)
        self.assertTrue(result.json["warnings"])

    def test_selected_career_has_real_dosm_observations(self):
        result = self.client.post(
            "/api/analyse",
            json={
                "degree_id": "D1",
                "user_skill_ids": ["S01", "S05", "S06"],
            },
        )
        match = next(
            m for m in result.json["matches"] if m["career"]["career_id"] == "C01"
        )
        self.assertEqual(match["match_score"], 75)
        self.assertEqual(match["ranking_score"], 75)
        self.assertEqual(len(match["market_signal"]["records"]), 2)
        self.assertAlmostEqual(
            match["market_signal"]["change_percent"], -19000 / 20089
        )


if __name__ == "__main__":
    unittest.main()
