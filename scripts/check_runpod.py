"""Explicit opt-in smoke test using a synthetic profile and the local API.

This submits one paid inference job to the configured endpoint. It does not
deploy workers or resubmit a queued job. Credentials are never printed.
"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from main import app
from profile_data import load_catalogue
import runpod_insight as ai


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--check", action="store_true",
                        help="Read chat API model metadata; do not generate advice")
    parser.add_argument("--resume-job")
    parser.add_argument("--show-synthetic-output", action="store_true",
                        help="Print raw advice from this synthetic profile for diagnosis")
    args = parser.parse_args()
    if args.check:
        try:
            result = ai.check_connection()
        except ai.InsightError as error:
            print(str(error))
            return 1
        print("API model ready:", result["model"])
        return 0
    if not args.live:
        parser.error("Use --live to submit one real inference job.")
    if args.show_synthetic_output:
        import json
        finish = ai._finish

        def inspect_output(advice, model, constraints, config):
            print("Synthetic model output:", json.dumps(advice), flush=True)
            return finish(advice, model, constraints, config)

        ai._finish = inspect_output
    client = app.test_client()
    profile = {
        "degree_id": "D1", "user_skill_ids": ["S01", "S05", "S06"],
        "scenario": "moderate", "career_id": "C01",
    }
    if args.resume_job:
        if ai.configuration()["mode"] != "serverless":
            parser.error("--resume-job is only supported in Serverless queue mode.")
        analysis = client.post("/api/analyse", json=profile).json
        match = next(m for m in analysis["matches"] if m["career"]["career_id"] == "C01")
        _, skills = load_catalogue(Path(__file__).resolve().parents[1] / "data")
        ai._JOBS["smoke-resume"] = {
            "id": args.resume_job, "config": ai.configuration(),
            "constraints": ai.advice_constraints(analysis, match, skills),
            "created": time.monotonic(), "last_poll": 0,
            "fingerprint": "smoke-resume",
        }
        response = client.get("/api/insight/jobs/smoke-resume")
    else:
        response = client.post("/api/insight", json=profile)
    deadline = time.monotonic() + 300
    while response.status_code == 202 and time.monotonic() < deadline:
        print("RunPod job pending; polling the same job.", flush=True)
        token = response.json["request_token"]
        time.sleep(5)
        response = client.get("/api/insight/jobs/" + token)
    if response.status_code != 200:
        print("HTTP", response.status_code)
        print(response.json.get("errors", ["Still pending; check the RunPod console."]))
        return 1
    print("Model:", response.json["model"])
    print("Model disclosure:", response.json["model_source"])
    print("Validated action proposals:", len(response.json["recommendations"]))
    for item in response.json["recommendations"]:
        print(item["category"] + ":", item["title"])
        print("Action:", item["action"])
        print("Deliverable:", item["deliverable"])
        print("Check:", item["success_check"])
    print("Provider timings:", response.json.get("timings", {}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
