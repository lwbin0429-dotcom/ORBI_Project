"""Check public model metadata and optionally one tiny synthetic generation."""

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from main import app
from runpod_insight import _NoRedirect, configuration


def probe(url, key, payload=None):
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8") if payload is not None else None,
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
        method="POST" if payload is not None else "GET",
    )
    started = time.monotonic()
    try:
        opener = urllib.request.build_opener(_NoRedirect())
        with opener.open(request, timeout=40) as response:
            data = json.load(response)
        print("HTTP 200; elapsed seconds:", round(time.monotonic() - started, 3))
        if payload is None:
            print("Models:", [item.get("id") for item in data.get("data", [])])
        else:
            print("Model:", data.get("model"))
            for choice in data.get("choices", []):
                print("Finish reason:", choice.get("finish_reason"))
                print("Synthetic reply:", repr(choice.get("message", {}).get("content")))
        return True
    except urllib.error.HTTPError as error:
        body = error.read(4096).decode("utf-8", errors="replace")
        body = body.replace(key, "[REDACTED]")
        body = re.sub(r"rpa_[A-Za-z0-9]+", "[REDACTED]", body)
        print("HTTP", error.code, "; elapsed seconds:",
              round(time.monotonic() - started, 3))
        print("Content type:", error.headers.get("Content-Type"))
        print("Server:", error.headers.get("Server"))
        print("Error response:", body[:1500])
    except (urllib.error.URLError, TimeoutError, ValueError):
        print("Network timeout, unavailable service or invalid JSON response.")
    return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generate", action="store_true",
                        help="Send one minimal paid generation with no profile data")
    args = parser.parse_args()
    config = configuration()
    if config["missing"] or config["mode"] != "public":
        parser.error("Configure the public model API before running this probe.")
    base = f"https://api.runpod.ai/v2/{config['endpoint']}/openai/v1"
    print("Metadata check:")
    metadata_ok = probe(base + "/models", config["key"])
    if args.generate:
        print("Minimal generation (non-thinking mode):")
        generation_ok = probe(base + "/chat/completions", config["key"], {
            "model": config["model"],
            "messages": [{"role": "user", "content": "Reply only with OK."}],
            "max_tokens": 32,
            "thinking": {"type": "disabled"},
            "stream": False,
        })
        return 0 if metadata_ok and generation_ok else 1
    return 0 if metadata_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
