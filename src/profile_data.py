"""CSV loading and input validation for the Part 1 profile."""

import csv
from pathlib import Path


def _read_csv(
    path: Path,
    required_fields: set[str],
    id_field: str,
) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not required_fields.issubset(reader.fieldnames or []):
            raise ValueError(f"{path.name}: required columns are missing")
        rows = []
        seen_ids = set()
        for row in reader:
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"{path.name}: malformed CSV row")
            cleaned = {key: value.strip() for key, value in row.items()}
            item_id = cleaned[id_field]
            name_field = id_field.removesuffix("_id") + "_name"
            if not item_id or not cleaned[name_field] or item_id in seen_ids:
                raise ValueError(f"{path.name}: empty name/ID or duplicate ID")
            seen_ids.add(item_id)
            rows.append(cleaned)
        if not rows:
            raise ValueError(f"{path.name}: catalogue is empty")
        return rows


def load_catalogue(data_dir: Path) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    degrees = _read_csv(
        data_dir / "degrees.csv",
        {"degree_id", "degree_name", "description"},
        "degree_id",
    )
    if (
        len(degrees) != 5
        or {row["degree_id"] for row in degrees} != {"D1", "D2", "D3", "D4", "D5"}
    ):
        raise ValueError(
            "degrees.csv: exactly five supported degrees (D1–D5) are required"
        )
    skills = _read_csv(
        data_dir / "skills.csv",
        {"skill_id", "skill_name", "sdg_ids", "sdg_explanation"},
        "skill_id",
    )
    return degrees, skills


def validate_profile(
    degree_id: str | None,
    skill_ids: list[str],
    degrees: list[dict[str, str]],
    skills: list[dict[str, str]],
) -> list[str]:
    errors = []
    if degree_id not in {row["degree_id"] for row in degrees}:
        errors.append("Select a supported degree.")
    if not skill_ids:
        errors.append("Select at least one skill.")
    elif not set(skill_ids).issubset({row["skill_id"] for row in skills}):
        errors.append("Select skills from the catalogue.")
    return errors
