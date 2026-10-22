# ORBI

> A career exploration and reskilling platform for students and graduates from five computing degree programmes.

## Current implementation — Parts 1 to 5

Part 1 provides an English-language HTML/CSS page for selecting one of the five supported
degrees and multiple self-reported skills. Click **Analyse My Future** to validate
and confirm the profile. A degree and at least one skill are required. Changing
either input clears the previous confirmation; submit again to confirm the new
profile. Choosing a degree never automatically selects skills.

The HTML/CSS frontend sends degree and skill IDs to a Flask API for validation
and matching. No profile is written to disk, and no identity or CV is requested.
Analysis works without RunPod. Part 5 sends sourced results to RunPod only when
the user clicks Generate AI Insight. Pending AI jobs and derived statements are
cached in server process memory; job handles expire after 15 minutes and entries
are cleared on subsequent job cleanup or server restart. RunPod also processes
the submitted data under its own service policies.

Part 2 ranks 15 sourced occupations from `data/careers.csv` and shows the top
three (or fewer if fewer valid records exist). Each result includes skill coverage,
matched and missing skills, occupation and skill evidence links, and a source check
date. Select a career below the results to inspect its required skills and mapping
explanation. No API key or network connection is needed to calculate matches.

```text
Skill coverage (%) = 100 × matched required skills / all required skills
```

Scores measure coverage of ORBI's curated skill subset, not employment probability
or complete job readiness. All careers remain eligible across degrees. Degree
relevance breaks exact score ties only; remaining ties use career name and ID.
Part 3 adds scenario ranking while keeping coverage separate and unchanged.
Sorting uses exact fractions before display rounding. A 0% result is labelled as
an exploration option. Changing inputs hides old results until you submit again.

The catalogue lives in `data/degrees.csv`, `data/skills.csv` and `data/careers.csv`.
The 22 skills have stable IDs. Occupation titles and task/technology evidence were
checked against O*NET OnLine on 21 October 2026. Skill subsets and degree
associations are ORBI interpretations; O*NET is a U.S. occupational source, not
local vacancy data. See [data provenance](data/README.md) for curation details.
Missing required skills, unknown skill/degree IDs, or missing source evidence
exclude a career with an explanation. File-level catalogue errors leave profile
intake available and display a warning.

Part 3 reads manually reviewed evidence from `data/trends.csv` and
`data/market_signals.csv` on every analysis. It displays selected skill signals,
required-skill evidence, source links, publication dates, data review dates and
reference periods. Moderate/Fast controls recompute the top three using:

```text
Trend Adjustment = 10 × average trend code over all required skills
Moderate Score = clamp(coverage + Trend Adjustment, 0, 100)
Fast Score = clamp(coverage + 2 × Trend Adjustment, 0, 100)
```

Rising = +1, Stable = 0, Declining = −1, Unknown = 0 with an insufficient-evidence
badge. Unknown remains in the denominator and never appears as Stable. Rank by
scenario score, coverage, degree relevance, career name, then ID. Scenario scores
are ORBI heuristic estimates, not employment probabilities or measured AI effects.
They can change scores without changing the order. Failed trend loading falls
back to coverage-only matching.

Reviewed evidence covers **19 of 22 skills**. Three classifications remain
unverified: Computer Graphics, Computer Networks and Security Risk Assessment.
The snapshot combines HackerRank assessment activity, UK IT Jobs Watch advert
shares, WEF employer expectations and a published database-design projection.
Each panel identifies its metric, geography and period. Historical advert shares
are not Malaysian demand or forecasts. Source snapshot dates and review dates
are labelled separately from publication dates.
The selected-skill panel highlights validated signals and groups Unknown records
in an expandable section while displaying the full evidence coverage count.
The WEF source describes a
closely corresponding design/user experience category; broad AI, programming or
cybersecurity evidence is not assigned to narrower tools. DOSM records cover
**Software Developers in 2026-Q1 and 2026-Q2 only**. The selected career's local
market panel shows those observations when available, or explicitly reports
missing evidence. Local market counts never alter skill scores.

Sources are real public publications, maintained manually in CSV. This is not a
live API feed or automatic web sync. Updating a reviewed CSV changes the next
analysis without restarting the server. See [evidence and update methodology](data/trend_methodology.md)
for source URLs, mapping decisions, dates, limitations and review steps.

To demonstrate scenarios, select any degree and HTML & CSS. The interface design
career has 25% coverage, 22.5 Moderate score and 20 Fast score in the reviewed
snapshot. To see DOSM evidence, select Python, SQL and Git & Version Control,
then explore Software Developers. These are fictional demo skill profiles.

Part 4 builds an ordered learning path for the selected career's missing skills
from `data/courses.csv`. There are 22 reviewed resource records, one per skill,
including courses, modules and tutorials. All current resources offer free
learning content; account requirements and separate certificate costs are
disclosed. A resource provides a starting point, not proof of skill mastery.
The page shows provider, links, cost notes, estimated hours, mapping scope and
source check date. Provider durations and ORBI planning estimates are labelled
separately. Compound steps link every included section.

Only missing required skills create steps. Applicable prerequisite steps come
first; background outside the career's gap is reported without silently adding
extra tasks. Changing the career updates the plan; editing the profile requires
analysis again. No progress is persisted and completing a resource does not
automatically update self-reported skills. A resource-file failure keeps matching
working and explicitly reports unavailable learning resources. See
[course curation and learning-path rules](data/course_methodology.md).

Part 5 maps all 15 careers and 22 skills to at least one SDG, with an explicit
contribution rationale. `data/sdgs.csv` links goal names to official UN definitions.
Mappings are ORBI interpretations, not UN endorsements or measured impacts.
The page shows the chosen career, required skills and selected skills with links.

Generate AI Insight recomputes all facts on the server, ignoring browser-supplied
scores, courses or source claims. RunPod generates three personalised action
proposals: a portfolio project, focused practice and interview preparation.
Each includes an action, a deliverable, a success check and a reason tied to the
profile. These are new AI proposals rather than summaries of the result panels.
Python validates the structure and skill/resource references, and resolves all
resource links from the current learning path. Prose is labelled as AI advice,
not verified outcomes; these checks cannot prove every statement is correct.
Unsupported output is withheld. The page discloses
the returned model, or explicitly labels the deployment configuration if the
worker does not report its model.

The selected integration uses RunPod's pre-deployed **Kimi K2.6 Public
Endpoint**, directly through its chat API. Only an account API key and credits
are needed: no Pod or user-deployed Serverless endpoint is created. The app uses
non-thinking mode and reports total API request time. This is shared hosted
inference, so latency is still subject to provider capacity.

The optional legacy queue integration submits once with `/run` and polls `/status` using an opaque
local request token. Repeated identical requests reuse the same in-process job
for 15 minutes. After success, **Generate another perspective** explicitly requests
a fresh generation; additional inference may incur RunPod charges. Variety is
encouraged, not guaranteed. Switching inputs clears stale UI output; it does not cancel the
provider job. API, model and transport failures leave matching operational.
The button shows an instant local summary while RunPod works, then replaces it
with the validated AI explanation. Elapsed time, queue status and actual provider
timings distinguish a cold-start wait from inference. Polling is about one to
two seconds; compact prompts remove repeated analysis data. These changes do
not eliminate provider queue delays or change cloud billing settings.
The current Kimi integration passed a full synthetic advice request in 13.594
seconds. This is one observation, not a latency guarantee; see
[verification evidence](docs/part5_verification.md).

For local AI use, copy `.env.example` to `.env` and set `RUNPOD_API_KEY`,
`RUNPOD_MODEL=kimi-k2.6` and `RUNPOD_API_MODE=public`. No endpoint ID
is needed in public mode. The app loads `.env`
without overriding existing environment variables. `.env` is ignored by Git;
Replit deployments should use Secrets. Keys are never sent to the browser.
Use `serverless` or `openai` only for an optional user-deployed endpoint, with
its own endpoint ID and model name. `runpod/handler.py` is an optional custom
Serverless worker, not the Public Endpoint implementation.

See [Part 5 setup and grounding](docs/part5_setup.md). The remaining competition
sections below are a submission template and still need to be completed.

### Quick start

Requires Python 3.10 or newer. From the repository root:

```bash
python -m pip install -r requirements.txt
python src/main.py
```

Open http://localhost:8000 in your browser. On Replit, the Run button starts Flask
on port 8000. Set HOST and PORT environment variables to change the bind address
and port. The frontend uses semantic HTML, responsive CSS and vanilla JavaScript
in a black and red theme.

### Implementation files

- `src/main.py`: Flask page route and matching API.
- `src/templates/index.html`: English-language page structure.
- `src/static/style.css`: responsive black and red styling.
- `src/static/app.js`: skill search, selections and results interaction.
- `src/profile_data.py`: CSV loading and input validation.
- `src/career_matching.py`: career validation, skill gaps and deterministic ranking.
- `src/trend_data.py`: trend/market validation, evidence payloads and comparisons.
- `src/learning_path.py`: resource validation and missing-skill learning paths.
- `src/sdg_data.py`: official SDG definitions and curated mapping descriptions.
- `src/runpod_insight.py`: private RunPod transport, queue handling and grounding.
- `data/degrees.csv`: exactly five supported degree programmes.
- `data/skills.csv`: editable computing skills catalogue.
- `data/careers.csv`: 15 careers with required skills and source evidence.
- `data/trends.csv`: 22 reviewed skill records with explicit Unknowns.
- `data/trend_observations.csv`: 15 raw UK advert-share observations for 13 skills.
- `data/trend_evidence_audit.md`: the complete 22-skill evidence and gap register.
- `data/market_signals.csv`: two DOSM quarterly observations for Software Developers.
- `data/courses.csv`: 22 reviewed course/module/tutorial mappings.
- `data/sdgs.csv`: five referenced UN goal definitions and review dates.
- `data/course_methodology.md`: resource scope, estimates and update rules.
- `data/trend_methodology.md`: Part 3 sources, calculations and update process.
- `data/README.md`: data provenance and editing rules.
- `tests/test_profile.py`: profile validation and data integrity checks.
- `tests/test_career_matching.py`: scoring, sorting and invalid records.
- `tests/test_web.py`: page, assets, API validation and matching responses.
- `tests/test_trends.py`: scenarios, evidence validation, fallback and reload checks.
- `tests/test_learning_path.py`: resource validation, ordering, gaps and reload checks.
- `tests/test_part5.py`: SDG completeness, grounding, credentials and queue handling.

Run checks with `python -m unittest discover tests` after installing dependencies.

### Code formatting

Keep source expanded and readable: one CSS declaration or code statement per
line, indented HTML elements, and wrapped long expressions. Use two spaces for
HTML/CSS/JavaScript and four for Python. Follow `.editorconfig`,
`.prettierrc.json`, `pyproject.toml` and [project instructions](AGENTS.md).
Format Jinja templates manually or with a Jinja-aware formatter; they are excluded
from generic Prettier HTML formatting to preserve template syntax.

---

## Team Information

| Field                  | Details                                     |
| ---------------------- | ------------------------------------------- |
| **Team Name**          | Your Team Name                              |
| **Team Domain**        | Domain 1 / Domain 2 *(choose one)*          |
| **SDG Track (1–17)**   | e.g. SDG 11 — Sustainable Cities and Communities |
| **Team Leader**        | Leader Name                                 |
| **University**         | University Name(s)                          |
| **Number of Members**  | e.g. 4                                      |

## Links

| Resource          | Link                                           |
| ----------------- | ---------------------------------------------- |
| GitHub Repository | https://github.com/your-username/your-project  |
| Replit Project    | https://replit.com/@your-username/your-project |
| Live Demo         | https://your-project.replit.app                |
| RunPod Endpoint   | https://api.runpod.ai/v2/your-endpoint-id      |
| Slide Deck        | https://example.com/slides                     |
| Demo Video        | https://example.com/demo-video                 |

---

## Overview

### Problem

Describe the real-world problem you are solving in 2–4 sentences. Who is affected, and why does it matter?

### Solution

Explain how your project uses AI to solve the problem and what makes it valuable.

### Key Features

- **Feature 1** — Short description.
- **Feature 2** — Short description.
- **Feature 3** — Short description.

### Tech Stack

| Layer         | Technology                   |
| ------------- | ---------------------------- |
| Frontend      | e.g. HTML, React             |
| Backend       | e.g. Python, Flask / FastAPI |
| Database      | e.g. PostgreSQL, SQLite      |
| AI / Compute  | RunPod (GPU)                 |
| Hosting / Dev | Replit                       |

---

## Project Structure

```
.
├── docs/                    # Screenshots, diagrams
├── runpod/
│   └── handler.py           # RunPod serverless handler (GPU workload)
├── src/
│   ├── main.py              # Application entry point
│   └── utils.py             # Helper functions
├── submission/              # Required submission documents
│   ├── REPLIT PROOF OF USE.pdf
│   ├── RUNPOD PROOF OF USE.pdf
│   └── Submission Template SDC Hackathon.pdf
├── tests/
│   └── test_utils.py        # Unit tests
├── .env.example             # Example environment variables
├── .gitignore
├── .replit                  # Replit run configuration
├── LICENSE
├── requirements.txt         # Python dependencies
└── README.md
```

### Architecture

```
User ──► Replit (App / API) ──► RunPod Endpoint (GPU model)
                │
                └──► Response returned to user
```

---

## How to Run

### Option 1 — Run on Replit (Recommended)

1. Open the [Replit Project](https://replit.com/@your-username/your-project), or import this repository via **Create Repl → Import from GitHub**.
2. Open the **Secrets** tab (🔒) and add the variables listed in `.env.example`:
   - `RUNPOD_API_KEY`
   - `RUNPOD_ENDPOINT_ID`
3. Click **Run**. Replit uses `.replit` to start Flask. Part 1 needs no secrets; RunPod configuration is for a later part.

### Option 2 — Run Locally

```bash
# 1. Clone the repository
git clone https://github.com/your-username/your-project.git
cd your-project

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env            # then fill in your values

# 5. Run the app
python src/main.py
```

### Run Tests

```bash
python -m unittest discover tests
```

---

## How We Use Replit *(Required)*

Describe how your team used Replit. For example:

- **Development:** Collaborative coding in a shared Repl using Multiplayer.
- **Hosting:** The app is deployed with Replit Deployments at the Live Demo link above.
- **Secrets:** API keys are stored in Replit Secrets, never in the code.

📄 Proof of use: [`submission/REPLIT PROOF OF USE.pdf`](submission/REPLIT%20PROOF%20OF%20USE.pdf)

## How We Use RunPod *(Required)*

Describe how your team used RunPod. For example:

- **Workload:** Model inference (e.g. text generation, image processing) runs on a RunPod GPU.
- **Setup:** `runpod/handler.py` is deployed as a **RunPod Serverless Endpoint**.
- **Integration:** The Replit app sends requests to the endpoint using `RUNPOD_API_KEY` and `RUNPOD_ENDPOINT_ID`.

Example request:

```bash
curl -X POST https://api.runpod.ai/v2/$RUNPOD_ENDPOINT_ID/runsync \
  -H "Authorization: Bearer $RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"input": {"prompt": "Hello"}}'
```

📄 Proof of use: [`submission/RUNPOD PROOF OF USE.pdf`](submission/RUNPOD%20PROOF%20OF%20USE.pdf)

---

## Challenges & Learnings

- What challenges did you face, and how did you overcome them?
- What did your team learn?

## Future Improvements

- [ ] Improvement 1
- [ ] Improvement 2

## Team

| Name        | Role                | GitHub                                   |
| ----------- | ------------------- | ---------------------------------------- |
| Member Name | Team Lead / Backend | [@username](https://github.com/username) |
| Member Name | Frontend            | [@username](https://github.com/username) |
| Member Name | AI / RunPod         | [@username](https://github.com/username) |

---

## Submission Checklist

- [ ] Team name, domain (Domain 1 / Domain 2) and SDG track filled in
- [ ] Slide deck link added
- [ ] Demo video link added
- [ ] Replit used, with proof of use in `submission/`
- [ ] RunPod used, with proof of use in `submission/`
- [ ] Submission template completed in `submission/`
- [ ] "How to Run" steps verified
- [ ] No API keys or secrets committed to the repository

## License

This project is licensed under the [Apache License 2.0](LICENSE).
