"""Part 2 coverage, ranking, catalogue integrity and page acceptance checks."""

import csv
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from career_matching import Career, load_careers, rank_careers
from profile_data import load_catalogue


def career(
    cid="C1",
    name="Example",
    required=("S01", "S05", "S14", "S16"),
    degrees=("D4",),
):
    return Career(
        cid,
        name,
        degrees,
        required,
        "Example source",
        "https://example.org/role",
        "2026-10-21",
        "Test fixture only",
        "https://example.org/skills",
    )


class TestCareerMatching(unittest.TestCase):
    def test_half_coverage_and_exact_gap(self):
        result = rank_careers([career()], ["S01", "S05", "S05", "unrelated"], "D1")[0]
        self.assertEqual(result.match_score, 50)
        self.assertEqual(result.matched_skill_ids, ("S01", "S05"))
        self.assertEqual(result.missing_skill_ids, ("S14", "S16"))

    def test_zero_full_and_empty_requirements(self):
        role = career()
        self.assertEqual(rank_careers([role], [], "D1")[0].match_score, 0)
        full = rank_careers([role], list(role.required_skills), "D1")[0]
        self.assertEqual(full.match_score, 100)
        self.assertEqual(full.missing_skill_ids, ())
        self.assertEqual(rank_careers([career(required=())], ["S01"], "D1"), [])

    def test_coverage_precedes_degree_and_ties_are_stable(self):
        roles = [
            career("C3", "Zulu", ("S01", "S05"), ("D1",)),
            career("C2", "Alpha", ("S01", "S05"), ("D1",)),
            career("C1", "Cross degree", ("S01",), ("D4",)),
            career("C4", "Aardvark", ("S01", "S05"), ("D4",)),
        ]
        result = rank_careers(roles, ["S01"], "D1")
        self.assertEqual([m.career.career_id for m in result], ["C1", "C2", "C3"])
        self.assertFalse(result[0].degree_related)
        self.assertEqual(len(rank_careers(roles[:1], ["S01"], "D1")), 1)
        self.assertEqual(rank_careers([], ["S01"], "D1"), [])

    def test_rounding_does_not_create_degree_tie(self):
        # Both display as 50.0%, but the cross-degree role has greater coverage.
        selected = [f"S{i}" for i in range(1001)]
        lower = career("C1", "Related", tuple(f"S{i}" for i in range(2002)), ("D1",))
        higher = career(
            "C2",
            "Cross degree",
            tuple(f"S{i}" for i in range(2001)),
            ("D4",),
        )
        self.assertEqual(
            rank_careers([lower, higher], selected, "D1")[0].career.career_id,
            "C2",
        )

    def test_duplicate_required_ids_are_counted_once(self):
        result = rank_careers(
            [career(required=("S01", "S01", "S05"))],
            ["S01"],
            "D1",
        )[0]
        self.assertEqual(result.match_score, 50)


class TestCareerCatalogue(unittest.TestCase):
    def setUp(self):
        degrees, skills = load_catalogue(ROOT / "data")
        self.degree_ids = {d["degree_id"] for d in degrees}
        self.skill_ids = {s["skill_id"] for s in skills}

    def test_shipped_catalogue_has_fifteen_valid_unique_roles(self):
        roles, issues = load_careers(
            ROOT / "data" / "careers.csv",
            self.degree_ids,
            self.skill_ids,
        )
        self.assertEqual(issues, [])
        self.assertEqual(len(roles), 15)
        self.assertEqual(len({r.career_name for r in roles}), 15)
        self.assertEqual(
            set().union(*(set(r.related_degrees) for r in roles)),
            self.degree_ids,
        )

    def test_invalid_records_are_excluded_without_inflating_scores(self):
        with (ROOT / "data" / "careers.csv").open(
            encoding="utf-8", newline=""
        ) as handle:
            reader = csv.DictReader(handle)
            fields = reader.fieldnames
            valid = next(reader)
        changes = [
            {"required_skills": ""},
            {"required_skills": "S01;UNKNOWN"},
            {"source_url": ""},
            {"related_degrees": "D99"},
            {"source_checked_at": "not a date"},
            {"skill_source_url": "javascript:alert(1)"},
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "careers.csv"
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                writer.writerow(valid)
                for i, change in enumerate(changes):
                    writer.writerow({**valid, **change, "career_id": f"BAD{i}"})
            roles, issues = load_careers(path, self.degree_ids, self.skill_ids)
        self.assertEqual(len(roles), 1)
        self.assertEqual(len(issues), len(changes))


if __name__ == "__main__":
    unittest.main()
