# ORBI

> A career exploration and reskilling platform for students and graduates from five computing degree programmes.

## Team Information

| Field | Details |
| --- | --- |
| **Team Name** | CV |
| **Team Domain** | Domain 1 |
| **SDG Track (1–17)** | SDG 8 |
| **Team Leader** | Lee Wei Bin |
| **University** | Xiamen University Malaysia |
| **Number of Members** | 1 |

## Links

| Resource | Link |
| --- | --- |
| GitHub Repository | https://github.com/lwbin0429-dotcom/ORBI_Project |
| Replit Project | To be added |
| Live Demo | To be added |
| RunPod Endpoint | https://api.runpod.ai/v2/moonshot-kimi/openai/v1/chat/completions |
| Slide Deck | To be added |
| Demo Video | To be added |

---

## Overview

### Problem

Rapid advancements in artificial intelligence and shifting industry demands create
immense career uncertainty for computing students and recent graduates. Many learners
struggle to understand how their coursework maps to viable roles, which technical skills
are rising or declining, and how to bridge their individual competency gaps. Without
transparent, evidence-grounded guidance, graduates risk pursuing obsolete skills or
facing underemployment, exacerbating the digital talent mismatch targeted by UN SDG 8.

### Solution

ORBI is an evidence-grounded career exploration and reskilling platform tailored for
computing students. It combines deterministic skill-coverage matching against 15
O*NET-sourced occupations with empirical trend adjustments across Moderate and Fast AI
disruption scenarios. To turn identified skill gaps into immediate action, ORBI leverages
GPU-accelerated LLM inference via RunPod (Kimi K2.6) to generate personalized portfolio
projects, deliberate practice tasks, and interview preparation. Crucially, the AI is
strictly constrained to verified curriculum resources and student profile data, delivering
trustworthy, hallucination-resistant career guidance.

### Key Features

- **Transparent Career Matching & Gap Analysis** — Evaluates self-reported skills
  against 15 curated computing occupations using deterministic coverage formulas,
  highlighting exact missing competencies without black-box bias.
- **Empirical Market Trends & Disruption Scenarios** — Integrates real-world market
  evidence and dynamic AI disruption modeling (Moderate vs. Fast) to rank careers by
  future resilience alongside published Malaysian market signals.
- **Curated Reskilling Paths & Grounded AI Insights** — Generates ordered,
  prerequisite-aware learning roadmaps with vetted free resources, complemented by
  on-demand RunPod GPU-powered AI proposals for portfolio projects, targeted practice,
  and interview preparation.

### Tech Stack

| Layer | Technology |
| --- | --- |
| Frontend | HTML5, CSS3, Modern JavaScript |
| Backend | Python 3, Flask |
| Database | Structured CSV Catalogues (O*NET, DOSM, SDGs) |
| AI / Compute | RunPod Public Endpoints (GPU-accelerated Kimi K2.6) |
| Hosting / Dev | Replit |

---

## Project Structure

```
.
├── data/                    # Degree, skill, career, trend and course catalogues
├── runpod/
│   └── handler.py           # Optional legacy worker; not used by the public API
├── src/
│   ├── main.py              # Flask application entry point and API routes
│   ├── profile_data.py      # Catalogue loading and profile validation
│   ├── career_matching.py   # Career matching, scoring and skill gaps
│   ├── trend_data.py        # Trend evidence and Malaysian market summaries
│   ├── learning_path.py     # Prerequisite-aware learning paths
│   ├── sdg_data.py          # SDG definitions and contribution mappings
│   ├── runpod_insight.py    # Kimi API requests and advice validation
│   ├── templates/
│   │   └── index.html       # English HTML/Jinja interface
│   └── static/
│       ├── style.css        # Black/red styling and rotating AI-chip Hero
│       └── app.js           # Profile, matching and AI interactions
├── submission/              # Required submission documents
│   ├── REPLIT PROOF OF USE.pdf
│   ├── RUNPOD PROOF OF USE.pdf
│   └── Submission Template SDC Hackathon.pdf
├── .env.example             # Example environment variables
├── .gitignore
├── .replit                  # Replit run configuration
├── LICENSE
├── requirements.txt         # Python dependencies
└── README.md
```

### Architecture

```
User ──► Flask App / API (local or Replit) ──► RunPod Public API (Kimi K2.6)
                    │                                  │
                    ├──► CSV catalogues                │
                    └──► Career results + validated AI advice ──► User
```

---

## How to Run

### Option 1 — Run on Replit (Recommended)

1. Import [this repository](https://github.com/lwbin0429-dotcom/ORBI_Project) into Replit.
2. Open **Secrets** and add the variables listed in `.env.example`:
   - `RUNPOD_API_KEY`
   - `RUNPOD_MODEL=kimi-k2.6`
   - `RUNPOD_API_MODE=public`
3. Click **Run**. Replit uses `.replit` to start Flask on port 8000. Core career
   analysis works without secrets; AI advice requires a RunPod key and credits.

### Option 2 — Run Locally

```bash
# 1. Clone the repository
git clone https://github.com/lwbin0429-dotcom/ORBI_Project.git
cd ORBI_Project

# 2. Create and activate a virtual environment (Python 3.10+)
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env            # Only if .env does not already exist
# Set RUNPOD_API_KEY to your own key.
# Keep RUNPOD_MODEL=kimi-k2.6 and RUNPOD_API_MODE=public.

# 5. Run the app
python src/main.py
```

Open http://127.0.0.1:8000. On Windows PowerShell, use
`Copy-Item .env.example .env` instead of `cp`. Restart Flask after editing `.env`.

---

## How We Use Replit *(Required)*

- **Development:** The repository provides a Flask entry point and
  `requirements.txt` for importing and running the application on Replit.
- **Hosting:** `.replit` configures the app to run on `0.0.0.0:8000`.
  The actual Replit project and deployed demo URLs still need to be added.
- **Secrets:** The app reads RunPod credentials from environment variables,
  allowing deployment with Replit Secrets instead of credentials in source code.

📄 Proof of use: [`submission/REPLIT PROOF OF USE.pdf`](submission/REPLIT%20PROOF%20OF%20USE.pdf)

## How We Use RunPod *(Required)*

- **Workload:** Kimi K2.6 generates personalized portfolio projects, practice
  tasks and interview preparation with deliverables and success checks.
- **Setup:** ORBI calls RunPod's pre-deployed Public Endpoint. No Pod or
  user-owned Serverless endpoint is created, and `runpod/handler.py` is not deployed.
- **Integration:** Flask sends the recomputed profile and approved skill/resource
  references using `RUNPOD_API_KEY`, `RUNPOD_MODEL=kimi-k2.6` and
  `RUNPOD_API_MODE=public`. Python validates the response and resolves course links.

📄 Proof of use: [`submission/RUNPOD PROOF OF USE.pdf`](submission/RUNPOD%20PROOF%20OF%20USE.pdf)

---

## Challenges & Learnings

- **Challenges:** Trend sources use different metrics, regions and dates.
  ORBI records their scope and review dates, while unsupported classifications
  remain unresolved. API latency, provider failures and varying model output
  formats required explicit error handling and response validation.
- **Learnings:** Keep deterministic scoring separate from generated advice,
  distinguish scenario estimates from forecasts, and validate skill/resource
  references while allowing AI to propose useful new actions.

## Future Improvements

- [ ] Add scheduled source updates and expand comparable Malaysian trend evidence,
  including the three currently unresolved skill classifications.
- [ ] Add alternative learning resources and optional progress tracking, and
  evaluate AI advice with feedback from students and graduates.

## Team

| Name | Role | GitHub |
| --- | --- | --- |
| Lee Wei Bin | Team Lead / Frontend / Backend / AI Integration | To be confirmed |

---

## Submission Checklist

- [x] Team name, domain (Domain 1 / Domain 2) and SDG track filled in
- [ ] Slide deck link added
- [ ] Demo video link added
- [ ] Replit used, with proof of use in `submission/`
- [ ] RunPod used, with proof of use in `submission/`
- [ ] Submission template completed in `submission/`
- [ ] "How to Run" steps verified
- [ ] No API keys or secrets committed to the repository

## License

This project is licensed under the [Apache License 2.0](LICENSE).
