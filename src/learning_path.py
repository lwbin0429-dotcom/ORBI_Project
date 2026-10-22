"""Validated learning resources and ordered plans for missing required skills."""

# courses.csv supplies reviewed links, time budgets and prerequisite skill IDs.
# Plans are suggestions: completing a step does not update the user's skill profile.

from dataclasses import asdict, dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from career_matching import _ids, _valid_url
from trend_data import _records


@dataclass(frozen=True)
class Course:
    # One skill-to-resource mapping, including its scope and duration/cost disclosures.
    course_id: str
    skill_id: str
    course_name: str
    provider: str
    course_url: str
    estimated_hours: float
    cost_type: str
    learning_order: int
    source_checked_at: str
    resource_type: str
    duration_basis: str
    duration_note: str
    cost_note: str
    mapping_note: str
    prerequisite_skill_ids: tuple[str, ...]
    prerequisite_note: str
    supporting_urls: tuple[str, ...]


def load_courses(
    path: Path,
    skill_ids: set[str],
) -> tuple[list[Course], list[str]]:
    """Exclude invalid records; a duplicate ID invalidates every occurrence."""
    # Reuse the comment-aware CSV reader and require every resource metadata column.
    rows = _records(path, set(Course.__dataclass_fields__))
    courses, issues, seen = {}, [], set()
    for row in rows:
        course_id = row["course_id"]
        if course_id in seen:
            courses.pop(course_id, None)
            issues.append(f"{course_id}: duplicate course ID; excluded.")
            continue
        seen.add(course_id)
        try:
            if not course_id or row["skill_id"] not in skill_ids:
                raise ValueError("missing course ID or unsupported skill")
            for field in [
                "course_name", "provider", "duration_note", "cost_note",
                "mapping_note",
            ]:
                if not row[field]:
                    raise ValueError(f"missing {field}")
            if not _valid_url(row["course_url"]):
                raise ValueError("invalid course URL")
            supporting = _ids(row["supporting_urls"])
            if any(not _valid_url(url) for url in supporting):
                raise ValueError("invalid supporting URL")
            # Reject non-finite budgets before converting values for JSON output.
            hours = Decimal(row["estimated_hours"])
            if not hours.is_finite() or hours <= 0 or hours > 10000:
                raise ValueError("duration must be finite and positive")
            order = int(row["learning_order"])
            if order < 1:
                raise ValueError("learning order must be positive")
            if row["cost_type"] not in {
                "free", "paid", "free_content_paid_certificate",
            }:
                raise ValueError("unsupported cost type")
            if row["resource_type"] not in {"course", "module", "tutorial"}:
                raise ValueError("unsupported resource type")
            if row["duration_basis"] not in {"provider", "orbi_estimate"}:
                raise ValueError("unsupported duration basis")
            checked = date.fromisoformat(row["source_checked_at"])
            if checked > date.today():
                raise ValueError("source review date is in the future")
            # Prerequisites refer to catalogue skills, not arbitrary course IDs.
            prerequisites = _ids(row["prerequisite_skill_ids"])
            if not set(prerequisites).issubset(skill_ids):
                raise ValueError("unsupported prerequisite skill")
            if row["skill_id"] in prerequisites:
                raise ValueError("a skill cannot require itself")
            values = dict(row)
            values.update(
                estimated_hours=float(hours),
                learning_order=order,
                prerequisite_skill_ids=prerequisites,
                supporting_urls=supporting,
            )
            courses[course_id] = Course(
                **{field: values[field] for field in Course.__dataclass_fields__}
            )
        except (ValueError, InvalidOperation) as exc:
            issues.append(f"{course_id or 'Unnamed course'}: {exc}; excluded.")
    return list(courses.values()), issues


def build_learning_path(
    missing_skill_ids: tuple[str, ...],
    selected_skill_ids: list[str],
    courses: list[Course],
) -> dict:
    """Plan only missing skills; order applicable prerequisites before dependants."""
    # Never assign extra courses for skills the user already selected.
    selected = set(selected_skill_ids)
    missing = set(missing_skill_ids) - selected
    choices = {}
    ordered_courses = sorted(
        courses, key=lambda item: (item.learning_order, item.course_id)
    )
    # Prefer the first valid resource by editorial learning order, then course ID.
    for course in ordered_courses:
        if course.skill_id in missing:
            choices.setdefault(course.skill_id, course)
    unavailable = [
        {"skill_id": sid, "reason": "Resource currently unavailable."}
        for sid in sorted(missing - choices.keys())
    ]
    pending = dict(choices)
    prepared = set(selected)
    steps = []
    # Resolve prerequisites within this plan before selecting the next resource.
    while pending:
        ready = [
            course
            for course in pending.values()
            if not (set(course.prerequisite_skill_ids) & pending.keys())
        ]
        # A dependency cycle cannot produce a valid order; report it explicitly.
        if not ready:
            unavailable.extend(
                {
                    "skill_id": sid,
                    "reason": (
                        "Resource currently unavailable: conflicting prerequisites."
                    ),
                }
                for sid in sorted(pending)
            )
            break
        course = min(ready, key=lambda item: (item.learning_order, item.course_id))
        steps.append(
            {
                "sequence": len(steps) + 1,
                "course": asdict(course),
                # External background is disclosed rather than added as hidden tasks.
                "suggested_background_ids": sorted(
                    set(course.prerequisite_skill_ids) - prepared
                ),
            }
        )
        prepared.add(course.skill_id)
        del pending[course.skill_id]
    return {
        "steps": steps,
        "unavailable": unavailable,
        "missing_skill_count": len(missing),
        "covered_skill_count": len(steps),
        # Sum with Decimal so ordinary decimal time budgets do not accumulate noise.
        "total_estimated_hours": float(
            sum(
                (
                    Decimal(str(step["course"]["estimated_hours"]))
                    for step in steps
                ),
                Decimal(0),
            )
        ),
        "has_orbi_estimates": any(
            step["course"]["duration_basis"] == "orbi_estimate" for step in steps
        ),
    }
