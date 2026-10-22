"""UN goal definitions and explicitly editorial ORBI contribution mappings."""

from datetime import date
from pathlib import Path

from career_matching import _ids
from trend_data import _records


def load_sdgs(path: Path) -> dict[str, dict]:
    rows = _records(path, {
        "sdg_id", "sdg_name", "source_url", "source_checked_at",
    })
    goals = {}
    for row in rows:
        sid = row["sdg_id"]
        if sid not in {str(number) for number in range(1, 18)}:
            raise ValueError("unsupported SDG number")
        if sid in goals or not row["sdg_name"]:
            raise ValueError("duplicate SDG or missing name")
        if row["source_url"] != f"https://sdgs.un.org/goals/goal{sid}":
            raise ValueError("SDG definitions must link to the UN goal page")
        if date.fromisoformat(row["source_checked_at"]) > date.today():
            raise ValueError("SDG review date is in the future")
        goals[sid] = row
    return goals


def describe_sdg(ids, explanation: str, goals: dict[str, dict]) -> dict:
    """Return no partial mapping when a referenced definition is unavailable."""
    ids = _ids(ids) if isinstance(ids, str) else tuple(ids)
    valid = bool(ids and explanation.strip()) and all(sid in goals for sid in ids)
    return {
        "goals": [goals[sid] for sid in ids] if valid else [],
        "explanation": explanation if valid else "SDG mapping currently unavailable.",
        "interpretation": "ORBI interpretation; not a UN endorsement or measured impact.",
    }
