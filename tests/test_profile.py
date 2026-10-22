"""Part 1 acceptance checks for CSV integrity, validation and session changes."""

import shutil
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from profile_data import load_catalogue, validate_profile


class TestProfileData(unittest.TestCase):
    def setUp(self):
        self.degrees, self.skills = load_catalogue(ROOT / "data")

    def test_supported_degrees(self):
        self.assertEqual(
            [degree["degree_name"] for degree in self.degrees],
            [
                "Bachelor of Engineering in Software Engineering (Honours)",
                "Bachelor of Engineering in Digital Media Technology (Honours)",
                "Bachelor of Engineering in Computer Science and Technology (Honours)",
                "Bachelor of Engineering in Data Science (Honours)",
                "Bachelor of Engineering in Cyber Security (Honours)",
            ],
        )

    def test_invalid_and_valid_profiles(self):
        for degree, skills in [
            (None, []),
            ("D1", []),
            (None, ["S01"]),
            ("D6", ["S01"]),
            ("D1", ["unknown"]),
        ]:
            with self.subTest(degree=degree, skills=skills):
                self.assertTrue(
                    validate_profile(degree, skills, self.degrees, self.skills)
                )
        self.assertEqual(
            validate_profile("D2", ["S01", "S05"], self.degrees, self.skills),
            [],
        )

    def test_invalid_catalogues_are_rejected(self):
        bad_catalogues = [
            "skill_id,skill_name\nS01,Python\n",
            "skill_id,skill_name,sdg_ids,sdg_explanation\n",
            "skill_id,skill_name,sdg_ids,sdg_explanation\nS01,Python,,\nS01,SQL,,\n",
            "skill_id,skill_name,sdg_ids,sdg_explanation\nS01,Python\n",
        ]
        with tempfile.TemporaryDirectory() as directory:
            data_dir = Path(directory)
            shutil.copy(ROOT / "data" / "degrees.csv", data_dir)
            for contents in bad_catalogues:
                with self.subTest(contents=contents):
                    (data_dir / "skills.csv").write_text(contents, encoding="utf-8")
                    with self.assertRaises(ValueError):
                        load_catalogue(data_dir)


if __name__ == "__main__":
    unittest.main()
