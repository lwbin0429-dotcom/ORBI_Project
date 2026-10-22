"""Read-only latency diagnostics. No inference jobs or credentials are printed."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from main import app
from runpod_insight import InsightError, _request_json, check_connection, configuration


if __name__ == "__main__":
    config = configuration()
    if config["mode"] in {"public", "openai"}:
        try:
            print(json.dumps(check_connection()))
        except InsightError as error:
            print(str(error))
            raise SystemExit(1)
        raise SystemExit(0)
    base = "https://api.runpod.ai/v2/" + config["endpoint"]
    health = _request_json(base + "/health", None, config["key"])
    recent = _request_json(base + "/requests", None, config["key"])
    print(json.dumps({
        "jobs": health.get("jobs"),
        "workers": health.get("workers"),
        "recent_timings": [
            {key: row.get(key) for key in ["status", "delayTime", "executionTime"]}
            for row in recent.get("requests", [])[:5]
        ],
    }))
