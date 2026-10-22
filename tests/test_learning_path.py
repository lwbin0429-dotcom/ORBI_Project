"""Acceptance checks for sourced resources, missing-skill plans and failures."""

import csv
import shutil
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from learning_path import build_learning_path, load_courses
from main import app


SKILL_IDS = {f"S{number:02}" for number in range(1, 23)}


class TestLearningPath(unittest.TestCase):
    def setUp(self):
        self.courses, self.issues = load_courses(
            ROOT / "data" / "courses.csv", SKILL_IDS
        )

    def test_catalogue_covers_all_skills_with_sourced_resources(self):
        self.assertEqual(self.issues, [])
        self.assertEqual(len(self.courses), 22)
        self.assertEqual({c.skill_id for c in self.courses}, SKILL_IDS)
        for course in self.courses:
            self.assertEqual(course.cost_type, "free")
            self.assertTrue(course.course_url.startswith("https://"))
            self.assertTrue(course.mapping_note)
        cloud = next(c for c in self.courses if c.skill_id == "S20")
        self.assertEqual(cloud.estimated_hours, 0.4)
        self.assertEqual(cloud.duration_basis, "provider")

    def test_only_missing_skills_and_prerequisites_are_ordered(self):
        plan = build_learning_path(
            ("S16", "S01", "S13", "S14", "S01"), [], self.courses
        )
        ordered = [step["course"]["skill_id"] for step in plan["steps"]]
        self.assertEqual(set(ordered), {"S16", "S01", "S13", "S14"})
        self.assertLess(ordered.index("S01"), ordered.index("S13"))
        self.assertLess(ordered.index("S13"), ordered.index("S16"))
        self.assertLess(ordered.index("S14"), ordered.index("S16"))
        self.assertEqual(plan["total_estimated_hours"], 42)
        self.assertEqual([s["sequence"] for s in plan["steps"]], [1, 2, 3, 4])
        remaining = build_learning_path(
            ("S01", "S13", "S16"), ["S01", "S13"], self.courses
        )
        self.assertEqual(len(remaining["steps"]), 1)
        self.assertEqual(remaining["steps"][0]["course"]["skill_id"], "S16")
        self.assertEqual(remaining["steps"][0]["suggested_background_ids"], ["S14"])

    def test_prerequisite_edges_take_precedence_over_curated_order(self):
        python = next(c for c in self.courses if c.skill_id == "S01")
        api = next(c for c in self.courses if c.skill_id == "S09")
        plan = build_learning_path(
            ("S09", "S01"), [], [replace(api, learning_order=1), python]
        )
        self.assertEqual(
            [step["course"]["skill_id"] for step in plan["steps"]],
            ["S01", "S09"],
        )

    def test_no_gaps_does_not_assign_courses(self):
        plan = build_learning_path((), ["S01"], self.courses)
        self.assertEqual(plan["steps"], [])
        self.assertEqual(plan["unavailable"], [])
        self.assertEqual(plan["total_estimated_hours"], 0)

    def test_unavailable_resource_and_external_background_are_explicit(self):
        api = next(c for c in self.courses if c.skill_id == "S09")
        plan = build_learning_path(("S09", "S05"), [], [api])
        self.assertEqual(plan["covered_skill_count"], 1)
        self.assertEqual(plan["missing_skill_count"], 2)
        self.assertEqual(plan["steps"][0]["suggested_background_ids"], ["S01"])
        self.assertEqual(plan["unavailable"][0]["skill_id"], "S05")
        self.assertEqual(plan["total_estimated_hours"], 12)

    def test_circular_prerequisites_do_not_produce_a_false_sequence(self):
        python = next(c for c in self.courses if c.skill_id == "S01")
        api = next(c for c in self.courses if c.skill_id == "S09")
        plan = build_learning_path(
            ("S01", "S09"), [],
            [replace(python, prerequisite_skill_ids=("S09",)), api],
        )
        self.assertEqual(plan["steps"], [])
        self.assertEqual(len(plan["unavailable"]), 2)
        self.assertEqual(plan["total_estimated_hours"], 0)

    def test_invalid_and_duplicate_records_are_excluded(self):
        with (ROOT / "data" / "courses.csv").open(
            encoding="utf-8", newline=""
        ) as handle:
            reader = csv.DictReader(handle)
            fields = reader.fieldnames
            original = next(reader)
        changes = [
            {"estimated_hours": "NaN"},
            {"estimated_hours": "Infinity"},
            {"estimated_hours": "-2"},
            {"estimated_hours": "0"},
            {"course_url": "javascript:alert(1)"},
            {"supporting_urls": "javascript:alert(1)"},
            {"skill_id": "S99"},
            {"source_checked_at": "2099-01-01"},
            {"source_checked_at": "invalid"},
            {"prerequisite_skill_ids": "S99"},
            {"prerequisite_skill_ids": "S01"},
            {"duration_basis": "invented"},
            {"mapping_note": ""},
            {"cost_type": "free_trial"},
            {"learning_order": "0"},
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "courses.csv"
            for change in changes:
                with self.subTest(change=change):
                    self.write_rows(path, fields, [{**original, **change}])
                    courses, issues = load_courses(path, SKILL_IDS)
                    self.assertEqual(courses, [])
                    self.assertTrue(issues)
            self.write_rows(path, fields, [original, original, original])
            courses, issues = load_courses(path, SKILL_IDS)
            self.assertEqual(courses, [])
            self.assertTrue(issues)

    @staticmethod
    def write_rows(path, fields, rows):
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)


class TestLearningAPI(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def analyse(self, selected):
        return self.client.post(
            "/api/analyse",
            json={"degree_id": "D1", "user_skill_ids": selected},
        )

    def test_each_career_plan_matches_its_missing_skills(self):
        response = self.analyse(["S01"])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["course_issues"], [])
        for match in response.json["matches"]:
            plan = match["learning_path"]
            self.assertEqual(plan["unavailable"], [])
            self.assertEqual(
                {s["course"]["skill_id"] for s in plan["steps"]},
                set(match["missing_skill_ids"]),
            )
            self.assertNotIn("S01", [s["course"]["skill_id"] for s in plan["steps"]])
        completed = self.analyse(sorted(SKILL_IDS)).json
        self.assertTrue(all(
            not match["learning_path"]["steps"] for match in completed["matches"]
        ))

    def test_file_failure_preserves_matching_and_reports_unavailable_resources(self):
        with patch("main.load_courses", side_effect=ValueError("bad CSV")):
            response = self.analyse(["S01"])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json["matches"]), 3)
        self.assertTrue(response.json["warnings"])
        for match in response.json["matches"]:
            self.assertEqual(match["learning_path"]["steps"], [])
            self.assertEqual(
                len(match["learning_path"]["unavailable"]),
                len(match["missing_skill_ids"]),
            )

    def test_csv_edit_is_reloaded_on_next_analysis(self):
        with tempfile.TemporaryDirectory() as directory:
            data_dir = Path(directory) / "data"
            shutil.copytree(ROOT / "data", data_dir)
            with patch("main.DATA_DIR", data_dir):
                before = self.analyse(["S01"]).json
                path = data_dir / "courses.csv"
                with path.open(encoding="utf-8", newline="") as handle:
                    reader = csv.DictReader(handle)
                    fields = reader.fieldnames
                    rows = list(reader)
                for row in rows:
                    row["estimated_hours"] = str(float(row["estimated_hours"]) + 1)
                TestLearningPath.write_rows(path, fields, rows)
                after = self.analyse(["S01"]).json
        for old, new in zip(before["matches"], after["matches"]):
            self.assertEqual(old["ranking_score"], new["ranking_score"])
            self.assertAlmostEqual(
                new["learning_path"]["total_estimated_hours"],
                old["learning_path"]["total_estimated_hours"]
                + len(old["learning_path"]["steps"]),
            )


if __name__ == "__main__":
    unittest.main()
