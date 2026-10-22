"""Validated, manually maintained trend evidence and local market observations."""

import csv
import re
from dataclasses import MISSING, asdict, dataclass
from datetime import date
from pathlib import Path

from career_matching import _valid_url


TREND_CODES = {"rising": 1, "stable": 0, "declining": -1, "unknown": 0}
SCENARIOS = {"moderate": 1, "fast": 2}


@dataclass(frozen=True)
class SkillTrend:
    skill_id: str
    trend_direction: str
    source_name: str
    source_url: str
    source_date: str
    reference_period: str
    updated_at: str
    evidence_note: str
    source_skill: str
    source_date_kind: str = "publication"
    geography: str = ""
    metric: str = ""
    supporting_urls: str = ""


@dataclass(frozen=True)
class MarketSignal:
    career_id: str
    occupation_code: str
    occupation_name: str
    period: str
    job_offerings: int
    source_name: str
    source_url: str
    source_date: str
    updated_at: str
    mapping_note: str


def _records(path: Path, fields: set[str]) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not fields.issubset(reader.fieldnames or []):
            raise ValueError(f"{path.name}: required columns are missing")
        records = []
        for row in reader:
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"{path.name}: malformed CSV row")
            records.append({key: value.strip() for key, value in row.items()})
        return records


def _check_evidence(row: dict[str, str]) -> None:
    if not row["source_name"] or not _valid_url(row["source_url"]):
        raise ValueError("missing source name or valid source URL")
    published = date.fromisoformat(row["source_date"])
    updated = date.fromisoformat(row["updated_at"])
    if updated < published:
        raise ValueError("review date precedes publication date")


def load_trends(
    path: Path,
    skill_ids: set[str],
) -> tuple[dict[str, SkillTrend], list[str]]:
    required = {
        name
        for name, field in SkillTrend.__dataclass_fields__.items()
        if field.default is MISSING
    }
    rows = _records(path, required)
    trends, issues, seen = {}, [], set()
    for row in rows:
        sid = row["skill_id"]
        if sid in seen:
            trends.pop(sid, None)
            issues.append(f"{sid}: duplicate trend records; treated as Unknown.")
            continue
        seen.add(sid)
        try:
            if sid not in skill_ids:
                raise ValueError("unknown skill ID")
            if row["trend_direction"] not in TREND_CODES:
                raise ValueError("invalid trend direction")
            _check_evidence(row)
            date_kind = row.get("source_date_kind", "publication")
            if date_kind not in {"publication", "snapshot", "review"}:
                raise ValueError("invalid source date kind")
            supporting_urls = row.get("supporting_urls", "")
            if supporting_urls and any(
                not _valid_url(url) for url in supporting_urls.split(";")
            ):
                raise ValueError("invalid supporting source URL")
            if not row["reference_period"] or not row["evidence_note"]:
                raise ValueError("missing period or evidence explanation")
            if row["trend_direction"] != "unknown" and not row["source_skill"]:
                raise ValueError("missing source skill label")
            trends[sid] = SkillTrend(
                **{
                    key: row[key]
                    for key in SkillTrend.__dataclass_fields__
                    if key in row
                }
            )
        except ValueError as exc:
            issues.append(f"{sid or 'Unnamed skill'}: {exc}; treated as Unknown.")
    return trends, issues


def describe_trend(skill_id: str, trends: dict[str, SkillTrend]) -> dict:
    trend = trends.get(skill_id)
    if trend:
        return asdict(trend)
    return {
        "skill_id": skill_id,
        "trend_direction": "unknown",
        "source_name": "",
        "source_url": "",
        "source_date": "",
        "reference_period": "",
        "updated_at": "",
        "source_skill": "",
        "evidence_note": "No validated trend record. Insufficient evidence.",
    }


def load_market_signals(
    path: Path,
    career_ids: set[str],
) -> tuple[list[MarketSignal], list[str]]:
    rows = _records(path, set(MarketSignal.__dataclass_fields__))
    signals, issues, seen = {}, [], set()
    for row in rows:
        key = (row["career_id"], row["period"])
        if key in seen:
            signals.pop(key, None)
            issues.append(f"{key[0]} {key[1]}: duplicate market records excluded.")
            continue
        seen.add(key)
        try:
            if row["career_id"] not in career_ids:
                raise ValueError("unknown career ID")
            if not re.fullmatch(r"[0-9]{4}-Q[1-4]", row["period"]):
                raise ValueError("invalid quarter")
            count = int(row["job_offerings"])
            if count < 0:
                raise ValueError("negative job offerings")
            _check_evidence(row)
            if not row["occupation_name"] or not row["mapping_note"]:
                raise ValueError("missing occupation or mapping explanation")
            values = {
                name: row[name]
                for name in MarketSignal.__dataclass_fields__
            }
            values["job_offerings"] = count
            signals[key] = MarketSignal(**values)
        except ValueError as exc:
            issues.append(f"{key[0]} {key[1]}: {exc}; market record excluded.")
    return list(signals.values()), issues


def market_summary(career_id: str, signals: list[MarketSignal]) -> dict:
    records = sorted(
        (record for record in signals if record.career_id == career_id),
        key=lambda record: record.period,
    )
    result = {
        "records": [asdict(record) for record in records],
        "change_percent": None,
        "comparison_note": "Local market evidence unavailable.",
    }
    if not records:
        return result
    result["comparison_note"] = "Two comparable consecutive quarters are needed."
    if len(records) < 2:
        return result
    previous, current = records[-2:]
    previous_index = int(previous.period[:4]) * 4 + int(previous.period[-1])
    current_index = int(current.period[:4]) * 4 + int(current.period[-1])
    comparable = (
        current_index - previous_index == 1
        and previous.source_name == current.source_name
        and previous.occupation_code == current.occupation_code
        and previous.occupation_name == current.occupation_name
        and previous.mapping_note == current.mapping_note
    )
    if comparable and previous.job_offerings > 0:
        result["change_percent"] = (
            100 * (current.job_offerings - previous.job_offerings)
            / previous.job_offerings
        )
        result["comparison_note"] = (
            f"{previous.period} to {current.period}: change in published online "
            "job offerings, not a forecast or evidence of AI causation."
        )
    elif comparable:
        result["comparison_note"] = (
            "Change is undefined because the base count is zero."
        )
    return result
