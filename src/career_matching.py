"""Source-backed career catalogue and deterministic skill coverage ranking."""

# This module computes scores locally; it does not call AI or fetch online evidence.
# Career requirements are ORBI's curated subsets, not universal employer requirements.

from dataclasses import dataclass
from datetime import date
from fractions import Fraction
from pathlib import Path
from urllib.parse import urlparse

from profile_data import _read_csv


@dataclass(frozen=True)
class Career:
    # Immutable occupation record with both its source and ORBI's mapping rationale.
    career_id: str
    career_name: str
    related_degrees: tuple[str, ...]
    required_skills: tuple[str, ...]
    source_name: str
    source_url: str
    source_checked_at: str
    evidence_note: str
    skill_source_url: str
    sdg_ids: tuple[str, ...] = ()
    sdg_explanation: str = ""


@dataclass(frozen=True)
class CareerMatch:
    # Keep selected-skill coverage separate from the scenario-adjusted ranking.
    career: Career
    matched_skill_ids: tuple[str, ...]
    missing_skill_ids: tuple[str, ...]
    degree_related: bool
    trend_adjustment: Fraction = Fraction(0)
    scenario_multiplier: int = 0
    known_trend_count: int = 0

    @property
    def coverage(self) -> Fraction:
        # Fractions preserve exact comparisons; duplicate requirements count once.
        return Fraction(
            len(self.matched_skill_ids),
            len(set(self.career.required_skills)),
        )

    @property
    def match_score(self) -> float:
        # Convert to a percentage only for the JSON response and display.
        return float(self.coverage * 100)

    @property
    def ranking_value(self) -> Fraction:
        # Scenario weights change ranking, while raw coverage and skill gaps stay fixed.
        adjusted = (
            self.coverage * 100
            + self.scenario_multiplier * self.trend_adjustment
        )
        return max(Fraction(0), min(Fraction(100), adjusted))

    @property
    def ranking_score(self) -> float:
        # Keep the precise ranking_value available for sorting before presentation.
        return float(self.ranking_value)


# CSV multi-value fields use semicolons; remove blanks and duplicates in source order.
def _ids(value: str) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(item.strip() for item in value.split(";") if item.strip())
    )


# Validate link structure only; this does not check availability or source accuracy.
def _valid_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"https", "http"} and bool(parsed.netloc)


# Validate mappings against the degree/skill catalogues and report excluded records.
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
        # Reject an invalid requirement set instead of shrinking the score denominator.
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
                sdg_ids=_ids(row["sdg_ids"]),
                sdg_explanation=row["sdg_explanation"],
            )
        )
    return careers, issues


# All degrees may explore all careers; degree relevance only resolves score ties.
def rank_careers(
    careers: list[Career],
    selected_skill_ids: list[str],
    degree_id: str,
    limit: int = 3,
    *,
    trend_codes: dict[str, int] | None = None,
    scenario_multiplier: int = 0,
) -> list[CareerMatch]:
    selected = set(selected_skill_ids)
    results = []
    for career in careers:
        required = tuple(dict.fromkeys(career.required_skills))
        if not required:
            continue
        codes = trend_codes or {}
        # Missing trend evidence contributes zero but remains in the denominator.
        adjustment = Fraction(
            10 * sum(codes.get(sid, 0) for sid in required),
            len(required),
        )
        results.append(
            CareerMatch(
                career=career,
                matched_skill_ids=tuple(sid for sid in required if sid in selected),
                missing_skill_ids=tuple(sid for sid in required if sid not in selected),
                degree_related=degree_id in career.related_degrees,
                trend_adjustment=adjustment,
                scenario_multiplier=scenario_multiplier,
                known_trend_count=sum(sid in codes for sid in required),
            )
        )
    # Exact fractions prevent rounded display values from creating false ties.
    results.sort(
        key=lambda match: (
            -match.ranking_value,
            -match.coverage,
            not match.degree_related,
            match.career.career_name.casefold(),
            match.career.career_id,
        )
    )
    # Return at most the requested number of valid matches (three in the web app).
    return results[:max(0, limit)]
