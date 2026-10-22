"""UN goal definitions and explicitly editorial ORBI contribution mappings."""

# sdgs.csv defines official goal names/URLs. skills.csv and careers.csv supply
# ORBI's contribution explanations; those interpretations are not UN endorsements.

from datetime import date
from pathlib import Path

from career_matching import _ids
from trend_data import _records


# Reject inconsistent definitions instead of displaying a misleading official link.
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
        # Only the exact UN goal page is accepted for each definition.
        if row["source_url"] != f"https://sdgs.un.org/goals/goal{sid}":
            raise ValueError("SDG definitions must link to the UN goal page")
        if date.fromisoformat(row["source_checked_at"]) > date.today():
            raise ValueError("SDG review date is in the future")
        goals[sid] = row
    return goals


def describe_sdg(ids, explanation: str, goals: dict[str, dict]) -> dict:
    """Return no partial mapping when a referenced definition is unavailable."""
    ids = _ids(ids) if isinstance(ids, str) else tuple(ids)
    # Require both a rationale and every referenced definition for a complete mapping.
    valid = bool(ids and explanation.strip()) and all(sid in goals for sid in ids)
    return {
        "goals": [goals[sid] for sid in ids] if valid else [],
        "explanation": explanation if valid else "SDG mapping currently unavailable.",
        "interpretation": "ORBI interpretation; not a UN endorsement or measured impact.",
    }
