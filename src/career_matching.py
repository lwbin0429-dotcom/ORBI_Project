"""Source-backed career catalogue and deterministic skill coverage ranking."""

from dataclasses import dataclass
from datetime import date
from fractions import Fraction
from pathlib import Path
from urllib.parse import urlparse

from profile_data import _read_csv


@dataclass(frozen=True)
class Career:
    career_id: str
    career_name: str
    related_degrees: tuple[str, ...]
    required_skills: tuple[str, ...]
    source_name: str
    source_url: str
    source_checked_at: str
    evidence_note: str
    skill_source_url: str


@dataclass(frozen=True)
class CareerMatch:
    career: Career
    matched_skill_ids: tuple[str, ...]
    missing_skill_ids: tuple[str, ...]
    degree_related: bool

    @property
    def coverage(self) -> Fraction:
        return Fraction(
            len(self.matched_skill_ids),
            len(set(self.career.required_skills)),
        )

    @property
    def match_score(self) -> float:
        return float(self.coverage * 100)


def _ids(value: str) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(item.strip() for item in value.split(";") if item.strip())
    )


def _valid_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"https", "http"} and bool(parsed.netloc)


def load_careers(
    path: Path,
    degree_ids: set[str],
    skill_ids: set[str],
) -> tuple[list[Career], list[str]]:
    rows = _read_csv(
        path,
        {
            "career_id",
            "career_name",
            "related_degrees",
            "required_skills",
            "source_name",
            "source_url",
            "source_checked_at",
            "evidence_note",
            "skill_source_url",
            "sdg_ids",
            "sdg_explanation",
        },
        "career_id",
    )
    careers, issues = [], []
    for row in rows:
        required = _ids(row["required_skills"])
        related = _ids(row["related_degrees"])
        reason = None
        if not required:
            reason = "no required skills"
        elif not set(required).issubset(skill_ids):
            reason = "unknown required skill IDs"
        elif not set(related).issubset(degree_ids):
            reason = "unknown related degree IDs"
        elif not row["source_name"] or not row["evidence_note"]:
            reason = "missing source or mapping explanation"
        elif (
            not _valid_url(row["source_url"])
            or not _valid_url(row["skill_source_url"])
        ):
            reason = "missing or invalid source URL"
        else:
            try:
                date.fromisoformat(row["source_checked_at"])
            except ValueError:
                reason = "missing or invalid source check date"
        if reason:
            issues.append(f"{row['career_id']} excluded: {reason}.")
            continue
        careers.append(
            Career(
                career_id=row["career_id"],
                career_name=row["career_name"],
                related_degrees=related,
                required_skills=required,
                source_name=row["source_name"],
                source_url=row["source_url"],
                source_checked_at=row["source_checked_at"],
                evidence_note=row["evidence_note"],
                skill_source_url=row["skill_source_url"],
            )
        )
    return careers, issues


def rank_careers(
    careers: list[Career],
    selected_skill_ids: list[str],
    degree_id: str,
    limit: int = 3,
) -> list[CareerMatch]:
    selected = set(selected_skill_ids)
    results = []
    for career in careers:
        required = tuple(dict.fromkeys(career.required_skills))
        if not required:
            continue
        results.append(
            CareerMatch(
                career=career,
                matched_skill_ids=tuple(sid for sid in required if sid in selected),
                missing_skill_ids=tuple(sid for sid in required if sid not in selected),
                degree_related=degree_id in career.related_degrees,
            )
        )
    # Exact fractions prevent rounded display values from creating false ties.
    results.sort(
        key=lambda match: (
            -match.coverage,
            not match.degree_related,
            match.career.career_name.casefold(),
            match.career.career_id,
        )
    )
    return results[:max(0, limit)]
