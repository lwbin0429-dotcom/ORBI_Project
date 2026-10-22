"""Serve the ORBI HTML/CSS frontend and Python matching API."""

import os
import re
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from dotenv import load_dotenv

from career_matching import load_careers, rank_careers
from learning_path import build_learning_path, load_courses
from profile_data import load_catalogue, validate_profile
from runpod_insight import (
    InsightError, advice_constraints, generate_insight, poll_insight, public_status,
)
from sdg_data import describe_sdg, load_sdgs
from trend_data import (
    SCENARIOS,
    TREND_CODES,
    describe_trend,
    load_market_signals,
    load_trends,
    market_summary,
)


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
load_dotenv(DATA_DIR.parent / ".env", override=False)
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024


@app.get("/")
def index():
    error = None
    degrees, skills = [], []
    career_count = 0
    try:
        degrees, skills = load_catalogue(DATA_DIR)
        try:
            careers, _ = load_careers(
                DATA_DIR / "careers.csv",
                {row["degree_id"] for row in degrees},
                {row["skill_id"] for row in skills},
            )
            career_count = len(careers)
        except (OSError, ValueError):
            pass  # Intake stays available if the career catalogue is unavailable.
    except (OSError, ValueError):
        error = "The skills catalogue is unavailable. Please try again later."
    return render_template(
        "index.html",
        degrees=degrees,
        skills=skills,
        career_count=career_count,
        catalogue={"degrees": degrees, "skills": skills},
        catalogue_error=error,
    )


@app.post("/api/analyse")
def analyse():
    return analyse_payload(request.get_json(silent=True))


def analyse_payload(payload):
    """Recompute server-owned results for both analysis and AI requests."""
    if not isinstance(payload, dict):
        return jsonify(errors=["Send a valid JSON profile."]), 400
    degree_id = payload.get("degree_id")
    skill_ids = payload.get("user_skill_ids")
    scenario = payload.get("scenario", "moderate")
    if not isinstance(scenario, str) or scenario not in SCENARIOS:
        return jsonify(errors=["Choose Moderate or Fast scenario."]), 400
    if (
        (degree_id is not None and not isinstance(degree_id, str))
        or not isinstance(skill_ids, list)
        or not all(isinstance(sid, str) for sid in skill_ids)
    ):
        return (
            jsonify(
                errors=["Select a supported degree and skills from the catalogue."]
            ),
            400,
        )
    try:
        degrees, skills = load_catalogue(DATA_DIR)
    except (OSError, ValueError):
        return (
            jsonify(
                errors=["The skills catalogue is unavailable. Please try again later."]
            ),
            503,
        )
    errors = validate_profile(degree_id, skill_ids, degrees, skills)
    if errors:
        return jsonify(errors=errors), 400

    profile = {"degree_id": degree_id, "user_skill_ids": list(dict.fromkeys(skill_ids))}
    warnings = []
    try:
        goals = load_sdgs(DATA_DIR / "sdgs.csv")
    except (OSError, ValueError):
        goals = {}
        warnings.append("SDG definitions are currently unavailable.")
    skill_index = {row["skill_id"]: row for row in skills}
    skill_catalogue_ids = {row["skill_id"] for row in skills}
    course_issues = []
    try:
        courses, course_issues = load_courses(
            DATA_DIR / "courses.csv",
            skill_catalogue_ids,
        )
    except (OSError, ValueError):
        courses = []
        warnings.append(
            "Learning resources are currently unavailable. "
            "Career matching and skill gaps remain available."
        )
    trend_issues = []
    try:
        trends, trend_issues = load_trends(
            DATA_DIR / "trends.csv",
            skill_catalogue_ids,
        )
    except (OSError, ValueError):
        trends = {}
        warnings.append(
            "Trend evidence is unavailable. Ranking uses skill coverage only."
        )
    trend_codes = {
        sid: TREND_CODES[trend.trend_direction]
        for sid, trend in trends.items()
        if trend.trend_direction != "unknown"
    }
    if not trend_codes and not warnings:
        warnings.append(
            "No validated directional skill evidence is available. "
            "Ranking uses skill coverage only; Unknown does not mean Stable."
        )
    market_signals = []
    market_issues = []
    try:
        careers, issues = load_careers(
            DATA_DIR / "careers.csv",
            {row["degree_id"] for row in degrees},
            {row["skill_id"] for row in skills},
        )
        matches = rank_careers(
            careers,
            profile["user_skill_ids"],
            degree_id,
            trend_codes=trend_codes,
            scenario_multiplier=SCENARIOS[scenario] if trend_codes else 0,
        )
        try:
            market_signals, market_issues = load_market_signals(
                DATA_DIR / "market_signals.csv",
                {career.career_id for career in careers},
            )
        except (OSError, ValueError):
            warnings.append("Malaysia market evidence is currently unavailable.")
    except (OSError, ValueError):
        matches, issues = [], []
        warnings.append(
            "Career matching is unavailable. Your profile is ready; "
            "please try analysing again later."
        )

    if not matches and not warnings:
        warnings.append("No valid careers are available in the catalogue.")
    elif matches and not any(match.matched_skill_ids for match in matches):
        warnings.append(
            "No selected skills overlap with these careers. "
            "Treat the 0% results as exploration options."
        )
    elif 0 < len(matches) < 3:
        warnings.append(f"Only {len(matches)} valid career(s) are available.")
    return jsonify(
        profile=profile,
        matches=[
            {
                **asdict(match),
                "trend_adjustment": float(match.trend_adjustment),
                "match_score": match.match_score,
                "ranking_score": match.ranking_score,
                "required_skill_trends": [
                    describe_trend(sid, trends)
                    for sid in match.career.required_skills
                ],
                "market_signal": market_summary(
                    match.career.career_id,
                    market_signals,
                ),
                "learning_path": build_learning_path(
                    match.missing_skill_ids,
                    profile["user_skill_ids"],
                    courses,
                ),
                "sdg_mapping": describe_sdg(
                    match.career.sdg_ids, match.career.sdg_explanation, goals,
                ),
                "required_skill_sdgs": [
                    {
                        "skill_id": sid,
                        **describe_sdg(
                            skill_index[sid]["sdg_ids"],
                            skill_index[sid]["sdg_explanation"],
                            goals,
                        ),
                    }
                    for sid in match.career.required_skills
                ],
            }
            for match in matches
        ],
        warnings=warnings,
        excluded_records=issues,
        scenario=scenario,
        scenario_multiplier=SCENARIOS[scenario],
        trends_available=bool(trend_codes),
        skill_trends=[
            describe_trend(sid, trends)
            for sid in profile["user_skill_ids"]
        ],
        trend_issues=trend_issues,
        market_issues=market_issues,
        course_issues=course_issues,
        selected_skill_sdgs=[
            {
                "skill_id": sid,
                **describe_sdg(
                    skill_index[sid]["sdg_ids"],
                    skill_index[sid]["sdg_explanation"],
                    goals,
                ),
            }
            for sid in profile["user_skill_ids"]
        ],
    )


@app.get("/api/insight/status")
def insight_status():
    return jsonify(public_status())


@app.post("/api/insight")
def insight():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict) or not isinstance(payload.get("career_id"), str):
        return jsonify(errors=["Choose a career from your current results."]), 400
    variant = payload.get("request_variant", "initial")
    if not isinstance(variant, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", variant):
        return jsonify(errors=["Use a valid advice request identifier."]), 400
    response = app.make_response(analyse_payload(payload))
    if response.status_code != 200:
        return response
    analysis = response.get_json()
    match = next(
        (item for item in analysis["matches"]
         if item["career"]["career_id"] == payload["career_id"]),
        None,
    )
    if match is None:
        return jsonify(errors=["Reanalyse and choose a current top-three career."]), 400
    try:
        degrees, skills = load_catalogue(DATA_DIR)
    except (OSError, ValueError):
        return jsonify(errors=["The skills catalogue is unavailable."]), 503
    degree = next(
        d for d in degrees if d["degree_id"] == analysis["profile"]["degree_id"]
    )
    selected = set(analysis["profile"]["user_skill_ids"])
    context = {
        "degree": degree,
        "profile": analysis["profile"],
        "selected_skills": [s for s in skills if s["skill_id"] in selected],
        "scenario": analysis["scenario"],
        "selected_career_result": match,
        "warnings": analysis["warnings"],
        "request_variant": variant,
    }
    try:
        result = generate_insight(context, advice_constraints(analysis, match, skills))
    except InsightError as error:
        return jsonify(errors=[str(error)]), error.status
    if result.get("pending"):
        return jsonify(result), 202
    return jsonify(
        **result,
        career_id=match["career"]["career_id"],
        scenario=analysis["scenario"],
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


@app.get("/api/insight/jobs/<token>")
def insight_job(token):
    try:
        result = poll_insight(token)
    except InsightError as error:
        return jsonify(errors=[str(error)]), error.status
    return jsonify(result), 202 if result.get("pending") else 200


if __name__ == "__main__":
    app.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", "8000")))
