"""HTTP acceptance tests for the HTML frontend and matching API."""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from main import app
from career_matching import load_careers, rank_careers
from profile_data import load_catalogue


class TestWebApp(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_page_and_assets(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn('<html lang="en">', html)
        self.assertIn('id="profile-form"', html)
        for i in range(1, 6):
            self.assertIn(f'<option value="D{i}">', html)
        self.assertEqual(html.count('name="skill_ids"'), 22)
        self.assertIn("/static/style.css", html)
        self.assertIn("/static/app.js", html)
        for url in ["/static/style.css", "/static/app.js"]:
            asset = self.client.get(url)
            self.assertEqual(asset.status_code, 200)
            asset.close()

    def test_profile_validation(self):
        for profile in [
            None,
            [],
            {"degree_id": None, "user_skill_ids": []},
            {"degree_id": "D1", "user_skill_ids": []},
            {"degree_id": "D99", "user_skill_ids": ["S01"]},
            {"degree_id": "D1", "user_skill_ids": ["UNKNOWN"]},
            {"degree_id": [], "user_skill_ids": ["S01"]},
            {"degree_id": "D1", "user_skill_ids": [None]},
            {"degree_id": "D1", "user_skill_ids": "S01"},
        ]:
            with self.subTest(profile=profile):
                response = self.client.post("/api/analyse", json=profile)
                self.assertEqual(response.status_code, 400)
                self.assertTrue(response.json["errors"])

    def test_ranked_results_match_core_and_recompute(self):
        profile = {"degree_id": "D4", "user_skill_ids": ["S13", "S14", "S13"]}
        response = self.client.post("/api/analyse", json=profile)
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertEqual(data["profile"]["user_skill_ids"], ["S13", "S14"])
        degrees, skills = load_catalogue(ROOT / "data")
        careers, _ = load_careers(
            ROOT / "data" / "careers.csv",
            {d["degree_id"] for d in degrees},
            {s["skill_id"] for s in skills},
        )
        expected = rank_careers(careers, profile["user_skill_ids"], "D4")
        self.assertEqual(len(data["matches"]), 3)
        self.assertEqual(
            [m["career"]["career_id"] for m in data["matches"]],
            [m.career.career_id for m in expected],
        )
        for result, match in zip(data["matches"], expected):
            self.assertEqual(result["match_score"], match.match_score)
            self.assertEqual(result["missing_skill_ids"], list(match.missing_skill_ids))
            self.assertTrue(result["career"]["source_url"].startswith("https://"))
        changed = self.client.post(
            "/api/analyse",
            json={"degree_id": "D1", "user_skill_ids": ["S11", "S12"]},
        ).json
        self.assertEqual(changed["matches"][0]["career"]["career_id"], "C15")
        self.assertEqual(changed["matches"][0]["match_score"], 100)
        self.assertFalse(changed["matches"][0]["degree_related"])

    def test_unavailable_career_catalogue_keeps_profile(self):
        with patch("main.load_careers", side_effect=OSError("Unavailable")):
            response = self.client.post(
                "/api/analyse",
                json={"degree_id": "D1", "user_skill_ids": ["S01"]},
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["profile"]["degree_id"], "D1")
        self.assertEqual(response.json["matches"], [])
        self.assertTrue(response.json["warnings"])

    def test_no_valid_roles_and_excluded_records(self):
        with patch(
            "main.load_careers",
            return_value=([], ["C1 excluded: no required skills."]),
        ):
            response = self.client.post(
                "/api/analyse",
                json={"degree_id": "D1", "user_skill_ids": ["S01"]},
            )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json["warnings"])
        self.assertEqual(len(response.json["excluded_records"]), 1)

    def test_unavailable_skills_catalogue(self):
        with patch("main.load_catalogue", side_effect=OSError("Unavailable")):
            page = self.client.get("/")
            response = self.client.post(
                "/api/analyse",
                json={"degree_id": "D1", "user_skill_ids": ["S01"]},
            )
        self.assertIn(
            "The skills catalogue is unavailable",
            page.get_data(as_text=True),
        )
        self.assertEqual(response.status_code, 503)


if __name__ == "__main__":
    unittest.main()
