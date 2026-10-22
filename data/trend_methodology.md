# Part 3 evidence and scenario methodology

ORBI uses manually reviewed public publications as updateable trend sources.
The CSV files are reviewed snapshots, not live feeds. Each analysis reads the
files again, so a validated data edit takes effect without restarting the server.
No web scraping, API credentials, automatic web synchronisation, or real user
profiles are involved in this part.

## Verified initial coverage

Reviewed on **22 October 2026**:

| Evidence | Initial coverage | Scope |
| --- | --- | --- |
| WEF Future of Jobs Report 2025 | One directional mapping: UI/UX Design, Rising | Global employer expectations for 2025–2030 |
| HackerRank skill demand analysis, published 3 April 2025 | Python and SQL Rising; Java and JavaScript Stable under ORBI's threshold | Historical platform assessment activity, 2024 vs 2023 |
| IT Jobs Watch | 13 skills: 11 Declining, 3D Modelling Rising, Cloud Computing Stable | UK permanent advert-share comparisons; 15 component observations |
| Miedema et al. (2025), Table 8 | Database Design Stable under ORBI's band | Published 2.7% demand-growth projection; horizon not specified |
| Remaining gaps | Computer Graphics, Computer Networks and Security Risk Assessment | No validated directional classification |
| DOSM Job Market Insights | Software Developers, 2026-Q1 and 2026-Q2 | Published Malaysian online recruitment observations |

The remaining careers have no local market records in the initial snapshot.
There are **19 supported and three unverified classifications**. See the full
[22-skill audit](trend_evidence_audit.md). Missing data is never interpreted as
zero job demand. Unknown does not mean
that no evidence exists anywhere; it means ORBI has not validated a direct
classification for that catalogue skill.

## Skill source and mapping

Source: [WEF Future of Jobs Report 2025, Chapter 3](https://www.weforum.org/publications/the-future-of-jobs-report-2025/in-full/3-skills-outlook/).
The [report publication page](https://www.weforum.org/publications/the-future-of-jobs-report-2025/)
dates the report to **7 January 2025**.

Chapter 3, section 3.2, under Technological change, describes anticipated growth
in the source category Design and user experience. ORBI maps that category to
S10 UI/UX Design. This is an editorial mapping of a closely corresponding label,
not a claim that WEF assessed every tool or specialisation in UI/UX.

Broader categories such as AI and big data, networks and cybersecurity,
analytical thinking, programming, or mathematics are not assigned automatically
to Machine Learning, Network Security, Data Analysis, Python, SQL, or Statistics.
The URL in an Unknown record is the source reviewed, not evidence that the
source officially classified that skill as Unknown. `source_skill` is empty for
Unknown records and names the source category for directional records.

## Tool-specific hiring activity

Source: [HackerRank's skill demand analysis](https://www.hackerrank.com/blog/top-developer-skills-in-2025-momentum-not-mayhem/),
published **3 April 2025**, covering full-year **2024** activity and year-over-year
comparison. The primary metric is the percentage change in assessment invites.
Active-test growth is retained as context and is not averaged with invite growth.

| Skill | Invite growth | Active-test growth | ORBI direction |
| --- | --- | --- | --- |
| Python | +35.6% | +23.1% | Rising |
| SQL | +25.5% | +6.5% | Rising |
| Java | −4.7% | −7.7% | Stable |
| JavaScript | 3.3 in the table's percentage-growth column | −0.9% | Stable |

ORBI's classification rule is above +5% = Rising, below −5% = Declining,
otherwise Stable, including both boundaries. This band is a project heuristic,
not a significance test or an official HackerRank classification. Java's Stable
badge does not hide its observed decline; both numbers appear in the evidence.
JavaScript's source table omits the percent symbol for its 3.3 cell; the original
column context and wording are preserved rather than presenting it as a more
precise independent measurement.

These signals measure hiring assessments on the source platform, not the whole
labour market, Malaysian vacancies, or future employment. The scenario model is
now informed by both historical observations and forecast expectations; it does
not convert historical growth percentages into forecasts. The source also warns
that observed AI benchmark performance does not establish a statistically useful
correlation with skill demand. ORBI makes no AI-causation claim from these data.

## UK skill-specific recruitment observations

IT Jobs Watch publishes six-month UK permanent IT advert counts and their
share of all permanent adverts, compared with the same period in prior years.
ORBI uses the **relative change in the published share**, calculated as
`100 * (current_share / previous_share - 1)`, with the same +/-5% band.
The denominator is the source's recruitment sample, not the entire economy.
Published shares are rounded; the band is not a statistical significance test.
Declining share does not necessarily mean declining absolute advert counts.
For example, Git counts increase from 1,114 to 1,601 while share falls from
2.28% to 1.33%. Both measures are disclosed; only share sets the direction.

The 15 raw component observations are retained in `trend_observations.csv`.
HTML & CSS and Data Structures & Algorithms each require both named components
to independently support the assigned direction. Their different snapshot end
dates are preserved, and overlapping adverts are never added together. A future
disagreement between component directions requires editorial review; it must
not be resolved by silently picking one component.

These are historical UK signals, not Malaysian measurements or predictions.
Each source URL and snapshot end date appears in the evidence panel. The
snapshot date is not presented as a publication date. Pages can change after
review; this committed data records what was reviewed on 22 October 2026.

## Database-design projection

[Miedema et al. (2025), Table 8](https://dbs-research.github.io/pdf/2025_recommendation.pdf)
reports Database Design explicitly: 13,926 postings and 2.7% projected growth.
ORBI classifies this as Stable under its +/-5% band. The paper's table does not
state a projection horizon, so this record is less specific than a dated
historical comparison and cannot be treated as an annual growth rate. Its
publication year is 2025. The stored date is labelled as our review date because
an exact publication day has not been established. This limitation is visible
in the UI and the audit. It is not a Malaysian forecast.

## Malaysian market observations

The two records come from the Software Developers occupation in these releases:

- [DOSM 2026-Q1 release](https://www.dosm.gov.my/site/downloadrelease?id=big-data-analytics-job-market-insights-q12026&lang=English),
  released **25 June 2026**: **20,089** online job offerings.
- [DOSM 2026-Q2 release](https://www.dosm.gov.my/site/downloadrelease?id=big-data-analytics-job-market-insights-q22026&lang=English),
  released **18 August 2026**: **19,899** online job offerings.

These are observations from major private recruitment platforms, not all
vacancies or hires in Malaysia. The exact occupation title matches C01 Software
Developers. The releases do not state an occupation code, so `occupation_code`
is intentionally blank rather than inferred from another taxonomy.

Quarter-on-quarter change is calculated as:

```text
100 × (latest count − preceding count) / preceding count
```

This gives approximately **−0.95%** for the two initial records. A comparison
requires consecutive quarters, the same source name, occupation name/code and
mapping note. Curators must also check that collection scope and definitions
remain comparable; those editorial checks cannot be automated from these fields.
Nonconsecutive periods, an incompatible mapping, fewer than two records, or a
zero base count produce no percentage. This signal does not establish AI
causation, predict future demand, classify individual skills, or alter ranking.

## Scenario model

```text
Rising = +1
Stable = 0
Declining = −1
Unknown or missing/invalid evidence = 0

Trend Adjustment = 10 × sum(required skill codes) / number of required skills
Moderate Score = clamp(Skill Coverage + 1 × Trend Adjustment, 0, 100)
Fast Score = clamp(Skill Coverage + 2 × Trend Adjustment, 0, 100)
```

Unknown skills remain in the denominator. The model uses every required skill
for the career, not just selected or matched skills. The page shows how many
required skills have validated directional evidence, including Stable records.
The original coverage score and skills gap remain unchanged.

Both scenarios are transparent ORBI heuristics. The weights 10, 1 and 2 are
project design choices from the SRS, not estimates measured by WEF or DOSM.
They are not probabilities of employment or validated forecasts of AI effects.
Scores are calculated with exact fractions before display rounding. Order is
scenario score, coverage, degree relevance, career name, then career ID.

With the reviewed snapshot, C04 has a -2.5-point adjustment: selecting HTML &
CSS gives 25 coverage, 22.5 Moderate and 20 Fast. Its Computer Graphics skill
still has no validated direction. It is valid for both scenarios to have the same
career order. Do not manufacture changes to make a demo look more dramatic.

## Update procedure

1. Check the official publication pages for new evidence or revisions. Confirm
   publication date, reference period, geographical scope and applicable labels.
2. Edit `trends.csv` only when the evidence supports the exact mapping. Use
   `rising`, `stable`, `declining` or `unknown`. Keep one record per skill ID.
3. Record the date in `source_date` with `source_date_kind` set to `publication`,
   `snapshot` or `review`. Never invent a publication day. Record the covered
   period in `reference_period`, and the curator's review date in `updated_at`.
   Include `geography`, `metric`, and any semicolon-separated `supporting_urls`.
   Update `trend_observations.csv` when changing IT Jobs Watch evidence. Explain
   the mapping in `evidence_note`. Do not update the date without reviewing data.
4. Add new quarters to `market_signals.csv`, retaining older observations and
   one record per career/quarter. Verify occupation identity and methodology.
5. Run `python -m unittest discover tests`. Submit or reanalyse a profile;
   confirm the source dates, known/Unknown badges and recalculated scores.

Maintain evidence snapshots through version control. A file edit is not
automatic online synchronisation; the UI explicitly describes manual review.
The automated update test uses a temporary synthetic mutation to prove that
edits change scores. Its changed direction is not a real-world claim and is
never written to the shipped evidence file.

## Failure behaviour

- Missing/malformed trend files fall back to coverage-only ranking.
- Unsupported IDs, directions, unsafe/missing URLs, dates, missing source labels
  or explanations exclude the affected trend and treat it as Unknown.
- Duplicate skill records invalidate that skill rather than selecting an
  arbitrary conflicting record. Duplicate market career/quarter records are
  excluded. Validation notices are displayed.
- A market-file error leaves skill trends and scenario matching operational.
- A career-file error preserves intake and selected skill evidence.

The requested 22/22 directional coverage is not yet achieved. Three reviewed
gaps are documented in the audit. Expand it with comparable evidence for the
actual skill, not broad category or occupation growth presented as an exact
skill measurement.
