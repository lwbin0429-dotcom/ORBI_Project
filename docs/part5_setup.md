# Part 5: SDG contributions and RunPod insights

## Local configuration

Install the application requirements, copy `.env.example` to `.env`, and set:

```dotenv
RUNPOD_API_KEY=your-runpod-api-key
RUNPOD_MODEL=kimi-k2.6
RUNPOD_API_MODE=public
```

The key stays on the Flask server. `.env` is ignored by Git, and environment
variables take precedence over that file. Restart the server after changing
credentials or endpoint configuration. Replit should use Secrets with the same
names. Do not install the optional GPU worker requirements on the web server.

The selected mode now uses RunPod's pre-deployed **Public Endpoint** for
Kimi K2.6. It requires an API key and account credits, with no Pod creation or
user-owned Serverless deployment. ORBI directly calls
`https://api.runpod.ai/v2/moonshot-kimi/openai/v1/chat/completions`.
The public route ignores the old endpoint ID and checks the model name matches.
It requests non-thinking mode for concise action advice. No fallback to the old
deployment or automatic inference retry is sent on failure.

Run `python scripts/check_runpod.py --check` to read the live model list without
generating advice. `--live` explicitly sends one synthetic advice request.
Metadata readiness does not guarantee the next generation will succeed.

Public endpoint use is billed by usage; it does not create an idle GPU rental.
RunPod's published Kimi K2.6 price on 22 October 2026 is $0.95 per million input
tokens and $4 per million output tokens;
check its model page for current terms. Shared infrastructure may still have
latency and capacity limits. This change removes management of your own worker,
not every possible provider-side delay.

Legacy modes remain available: `serverless` uses the earlier managed vLLM queue
worker and `openai` uses the chat API for a user-deployed endpoint. Both require
`RUNPOD_ENDPOINT_ID` and that deployment's actual model name. The optional
`runpod/handler.py` is not used by Public Endpoints.

For an OpenAI-compatible RunPod endpoint, use `RUNPOD_API_MODE=openai` and the
actual model configured there. ORBI calls the fixed RunPod host and constructs
paths from a validated endpoint ID. Arbitrary browser-supplied provider URLs
are never accepted. Automatic HTTP redirects are disabled for credential safety.

Official interface references:

- [Public Endpoints overview](https://docs.runpod.io/public-endpoints/overview)
- [Kimi API and pricing](https://docs.runpod.io/public-endpoints/models/moonshot-kimi)
- [RunPod request lifecycle](https://docs.runpod.io/serverless/endpoints/send-requests)
- [vLLM request input](https://docs.runpod.io/serverless/vllm/vllm-requests)
- [OpenAI-compatible endpoint](https://docs.runpod.io/serverless/vllm/openai-compatibility)

## SDG coverage and evidence

All 15 career rows and 22 skill rows contain `sdg_ids` and `sdg_explanation`.
Goal definitions are stored in `data/sdgs.csv`. The page shows the selected
career's contribution, all required skill contributions and selected skills.
References use official UN pages:

- [4: Quality Education](https://sdgs.un.org/goals/goal4), especially skills
  development under target 4.4 for educational visualisation applications.
- [8: Decent Work and Economic Growth](https://sdgs.un.org/goals/goal8), especially
  technological upgrading and productivity under target 8.2.
- [9: Industry, Innovation and Infrastructure](https://sdgs.un.org/goals/goal9),
  including resilience (9.1), research capability (9.5) and ICT access (9.c).
- [10: Reduced Inequalities](https://sdgs.un.org/goals/goal10), especially
  participation and inclusion under target 10.2 for accessible interface design.
- [16: Peace, Justice and Strong Institutions](https://sdgs.un.org/goals/goal16),
  especially accountable and transparent institutions under target 16.6.

These are ORBI's editorial interpretations of possible applications. They are
not official UN mappings, endorsements or measured impact claims. A technology
does not automatically create a positive outcome. Invalid definitions or
incomplete mappings show an unavailable state without disabling career matching.

## Personal action advice contract

Clicking Generate AI Insight recomputes the career result on the server.
Public mode sends a compact coaching context: degree, selected skills, target
career, missing skills and verified resource references. Scores, trend tables
and SDGs remain in their result panels. The server ignores client-supplied
scores, courses and URLs. Legacy modes include the fuller evidence context.
The chosen career must be one of the freshly recomputed top-three results.

The model generates new English proposals rather than selecting existing fact
sentences. The root object contains exactly three `recommendations`, one each
of type `portfolio_project`, `skill_practice` and `interview_preparation`.
Each recommendation uses this structure (one illustrative example):

```json
{
  "type": "portfolio_project",
  "title": "Testable expense parser",
  "action": "Build a Python parser using synthetic receipt data.",
  "deliverable": "A repository with documented test cases.",
  "success_check": "Valid receipts pass and malformed entries are rejected.",
  "reason": "Apply Python while practising the Software Testing gap.",
  "skill_ids": ["S01", "S08"],
  "resource_ids": ["R08"]
}
```

IDs vary with the actual profile. Python checks the required schema, text lengths,
distinct types/titles and approved skill/resource references. It also accepts
equivalent category-keyed recommendation objects returned by some workers,
normalising known type labels such as `Portfolio Project`. At least one current
gap must be referenced when gaps exist. Referenced resources also contribute their
server-mapped skills if the model omits those IDs. Links and labels come from
Python, never model URLs. Direct
URLs, numeric percentages and currency claims in prose are rejected, except
the proposed success criterion `100% pass rate` for a testing exercise. Advice may
use no course references.

Prompts request small synthetic-data projects, distinct practice tasks and mock
interview exercises with observable success criteria. They prohibit invented
courses, market statistics and job guarantees. The UI labels text as AI proposals.
Structural checks do not establish semantic accuracy or guarantee usefulness.
Scores, evidence and the ordered learning path remain separate server results.
Advice does not change the user's reported skills.

After success, Generate another perspective explicitly requests fresh inference
with a new request identifier. Temperature is 0.6 and output is capped at 1,100
tokens. A different project theme is requested; uniqueness is not guaranteed.
Retries using the same identifier reuse pending/cached queue jobs. Additional
generations may incur RunPod charges.

The UI discloses the model reported in the response. If a worker omits that
field, it labels the configured deployment model as unreported rather than
claiming independent verification. No AI request runs during ordinary analysis
or when the user changes careers or scenarios.

## Response timing and legacy queue handling

Public mode waits for the direct chat response and reports total API request
seconds, including transport and inference. It does not invent separate queue
or generation timings. The same advice validation and instant local preview
apply. Each click generates a new direct request; the following queue cache
applies only to legacy `serverless` mode.

Legacy queue mode submits one `/run` job, returns HTTP 202 with an opaque local token,
and polls the existing provider job through `/status`. The browser waits about
two seconds while queued and one second while generating, using provider phase
updates. Status I/O uses a per-job lock so one slow provider call does not block
all job lookups. Identical requests reuse the same in-process job for 15 minutes; no
automatic retry submits a second inference job. Provider model loading can take
longer than generation itself.

The prototype keeps at most 32 cached jobs in one server process. Request tokens
expire after 15 minutes; stale entries are removed during later job cleanup or
server restart. Advice constraints and proposals remain in process memory until that
cleanup. No profile is written to disk. RunPod processes submitted data under its
own service policies. The cache is not shared across multiple web processes.

The Generate button immediately displays a clearly labelled local summary from
existing results. It is not presented as a RunPod response. The real AI result
replaces it only after output validation. Waiting shows elapsed time and the
provider phase; completed output separates provider queue and generation times.
The prompt removes repeated UI fields and duplicate source links while retaining
the relevant source evidence, dates, scores, course references and SDG mapping.

Read-only diagnostics on 22 October 2026 observed queue delays of 102.469,
106.613 and 176.019 seconds, versus generation times of 3.370, 2.996 and 3.476
seconds. These are observations, not latency guarantees. App optimisations do
not eliminate a provider cold start. See [RunPod optimisation guidance](https://docs.runpod.io/serverless/development/optimization).
Keeping an active worker can avoid cold starts but incurs continuing charges
while idle. No active-worker, idle-timeout or other billing setting was changed.

Changing inputs clears stale UI output and stops polling, but does not cancel
an already submitted provider job. The browser's wait is capped at 10 minutes;
provider requests have bounded network timeouts. Authentication errors, malformed
responses, timeouts and failures show an explicit message and leave local career
matching, trends, SDGs and learning paths available.

## Verification

Run the offline suite with `python -B -m unittest discover tests -v`. These tests
mock provider requests; they never incur inference charges. The optional command
`python -B scripts/check_runpod.py --live` explicitly submits a synthetic test
and polls it. Its `--resume-job` option reads an existing test job without a new
submission. Live checks are separate from unit tests.

See [the recorded live verification](part5_verification.md). The Part 3 evidence
gaps remain separate; adding SDG mappings or AI text does not resolve them.
