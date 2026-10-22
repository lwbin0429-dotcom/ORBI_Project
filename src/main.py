"""Serve the ORBI HTML/CSS frontend and Python matching API."""

import os
from dataclasses import asdict
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from career_matching import load_careers, rank_careers
from profile_data import load_catalogue, validate_profile


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
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
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify(errors=["Send a valid JSON profile."]), 400
    degree_id = payload.get("degree_id")
    skill_ids = payload.get("user_skill_ids")
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
        careers, issues = load_careers(
            DATA_DIR / "careers.csv",
            {row["degree_id"] for row in degrees},
            {row["skill_id"] for row in skills},
        )
        matches = rank_careers(careers, profile["user_skill_ids"], degree_id)
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
            {**asdict(match), "match_score": match.match_score}
            for match in matches
        ],
        warnings=warnings,
        excluded_records=issues,
    )


if __name__ == "__main__":
    app.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", "8000")))
