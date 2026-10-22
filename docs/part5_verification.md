# Part 5 verification record

Date: **22 October 2026** (Asia/Kuala_Lumpur).

## Kimi Public Endpoint: current state

The active model is now **kimi-k2.6**, using
`https://api.runpod.ai/v2/moonshot-kimi/openai/v1/chat/completions`.
The application needs only the RunPod account key and credits. It ignores legacy
endpoint IDs and does not create a Pod or user-owned Serverless endpoint.
Non-thinking mode is requested using `thinking: {"type": "disabled"}`.

The model list returned HTTP 200. A tiny non-thinking request returned `OK` with
finish reason `stop` in 1.313 seconds. A full synthetic D1 / S01, S05, S06 / C01
career-advice request then passed all validation in **13.594 seconds**, with
the worker reporting `kimi-k2.6`. The three proposals were:

- A library-checkout analytics CLI project using Python and SQL.
- Unit-testing practice for a CSV parser, addressing Software Testing.
- A mock system-design interview with a concrete recorded/written deliverable.

The test exposed an overly broad local rejection of `100% pass rate` as a market
statistic. That phrase is now allowed only as a proposed success criterion;
employment percentages and other unsupported numeric claims remain rejected.
The regression test includes rejection of a job-probability claim alongside a
pass-rate target. The complete offline suite passes **71 tests**.

These timings are observations, not promises of future latency. No browser visual
verification was available. Older Qwen results below are historical, not the
current runtime model.

## Earlier Qwen public API migration

The selected runtime configuration is now `RUNPOD_API_MODE=public`, with the
pre-deployed `Qwen/Qwen3-32B-AWQ` model. No Pod, GPU rental or user-owned
Serverless endpoint was created. The supplied replacement account key was saved
only in the ignored `.env`; it is not recorded here.

The authenticated `/v2/qwen3-32b-awq/openai/v1/models` check succeeded and included
the configured model. This verifies metadata access, not generation reliability.
Initial chat requests returned generated advice, but did not pass the existing
output contract. One inspected response used category-keyed objects and
human-readable type names. Equivalent-shape normalisation and a concrete output
example were added while retaining reference and gap validation.

Tests of stronger response-format constraints included a 40-second timeout.
Later live requests, including a request without response-format constraints,
returned HTTP 502. Those optional constraints were removed. No successful final
end-to-end public-model generation is claimed. Re-run the explicit synthetic
check once the provider is available:

```bash
python scripts/check_runpod.py --check
python scripts/check_runpod.py --live --show-synthetic-output
```

The diagnostic output is limited to that script's synthetic profile. No
automatic inference retry or fallback to the older deployment is implemented.
The final offline suite passes 70 tests. Historical latency measurements and
successful tests below apply to the older self-deployed endpoint, not the new
public model.

### Isolated API diagnosis

`python scripts/diagnose_runpod.py --generate` sends no user profile and uses
only standard chat parameters with a 16-token output limit. Observed results:

- Model list: HTTP 200 in 1.235 seconds; `Qwen/Qwen3-32B-AWQ` was listed.
- Minimal chat generation: HTTP 502 in 0.750 seconds.
- Error response: plain text `error code: 502`, with a Cloudflare server header.

The failure reproduces without career data, a long prompt, structured output
parameters or local advice validation. The observed failing boundary is the
remote chat-generation HTTP request. These observations do not identify whether
the fault is the provider gateway, an upstream model worker or another
intermediary, and do not establish a platform-wide outage. Metadata success
alone does not prove inference entitlement, balance or backend health.

## Personal action advice update

The earlier fact-selection contract below is historical. The current version
generates three action proposals. One new synthetic inference job was submitted:
`52e4587d-cbd9-40f5-a6b6-22d14cc41ed5-e1`, with the same D1 / S01, S05, S06 /
C01 profile. The worker reported `Qwen/Qwen2.5-3B-Instruct` and returned:

- A Python/SQL e-commerce product catalogue project, with a working CRUD
  application as its deliverable.
- A Git workflow practice task, with a versioned repository as its deliverable.
- A mock software-testing interview exercise, referencing the existing R08
  testing resource.

Each recommendation contained action, deliverable, success-check and reason
fields. These were generated proposals, not copied catalogue sentences. Provider
waiting time was **1.348 seconds**, and execution time was **5.473 seconds**.
These are one observation, not a latency guarantee.

Initial validation found that the model referenced R08 without repeating its
S08 skill ID. The validator now resolves that skill from the authoritative
course mapping. Re-reading the same completed job passed all checks; no duplicate
inference was submitted to fix the reference. The prompt was also tightened to
focus practice on a missing skill and use skill names in prose. Those final
wording changes were not separately live-tested.

The offline suite now passes **64 tests**, including unknown resource rejection,
gap coverage, no-gap profiles, resource-to-skill resolution, response parsing,
queue deduplication and explicit fresh-generation identifiers. JavaScript syntax
and Git whitespace checks passed. No browser visual verification was available.

## Earlier fact-selection verification

A live request was made to the user-supplied RunPod vLLM Serverless endpoint.
The local API submitted a synthetic profile and polled the same job. This was
real inference, separate from the mocked unit tests.

| Check | Observed result |
| --- | --- |
| Endpoint health | HTTP 200 |
| Synthetic degree | D1, Software Engineering |
| Selected skill IDs | S01, S05, S06: Python, SQL, Git |
| Chosen career | C01, Software Developers |
| Coverage / Moderate scenario score | 75 / 75 |
| Missing skill | S08, Software Testing |
| Learning resource | R08, CS50 Python Unit Tests module |
| Provider job used for final validation | c17b0274-d598-425f-9b04-5d873341d8fb-e1 |
| Reported model | Qwen/Qwen2.5-3B-Instruct |
| Model identity source | Reported by the worker's chat-completion response |
| Explanation validation | Four sections accepted: fit, gaps, learning route, caveats |
| Core data authority | Python; returned fact IDs validated before rendering |
| Offline test suite | 59 tests passed |
| JavaScript | Syntax and Prettier formatting checks passed |
| Source hygiene | Git diff whitespace check passed; no API-key literals found outside ignored .env |

The first completed test exposed a different chat-completion response shape
than the token-chunk example. The parser and fact-ID prompt were corrected;
the final validation above used the corrected implementation. Completed output
was retrieved by polling rather than by submitting another duplicate job.

No API key is recorded in this file or browser output. Credentials are held in
the ignored local `.env`. Model weights were not loaded on the web application.
The managed worker was already deployed by the user; this work did not create
or change cloud worker scaling settings.

The environment had no enabled browser surface, so this record does not claim
visual browser verification. The automated suite covers catalogue integrity,
API output, unsupported facts, study order, caveats, secret handling, queued-job
reuse, timeouts and graceful fallback. JavaScript syntax and formatting are
checked separately. This synthetic test does not establish advice quality for
all profiles or future availability of the provider.
