# Review of all 22 skill trends

Reviewed 22 October 2026. **19 classifications supported; three unresolved.**
The requested 22/22 directional coverage has not been achieved. This register
records the gaps instead of inventing Stable classifications.

Rising / Stable / Declining are ORBI interpretations. For numerical growth,
above +5% is Rising, below -5% is Declining, and the inclusive band is Stable.
Different source metrics and periods are not interchangeable. These directions
feed an illustrative scenario model, not a validated employment forecast.

For IT Jobs Watch rows below, numbers are **previous share -> current share**
of the source's UK permanent IT advert sample. They compare six-month windows
ending on the stated date with the same period in 2025. They are percentages,
not advert counts or percentage growth rates. Raw counts and shares are in
`trend_observations.csv`; full mapping explanations are in `trends.csv` and
displayed in the application. Snapshot dates differ between skills.

| ID | Skill | Direction | Evidence and scope |
| --- | --- | --- | --- |
| S01 | Python | Rising | HackerRank invites +35.6%, active tests +23.1%, 2024 vs 2023. [Source][hr] |
| S02 | Java | Stable | HackerRank invites -4.7%, active tests -7.7%; Stable applies to invites only. [Source][hr] |
| S03 | JavaScript | Stable | HackerRank invite-growth cell 3.3 in the percentage column, active tests -0.9%. [Source][hr] |
| S04 | HTML & CSS | Declining | HTML share 2.67% -> 0.91%, 2026-10-02; CSS 2.39% -> 0.99%, 2026-09-08. Both components agree. [HTML](https://www.itjobswatch.co.uk/jobs/uk/html.do), [CSS](https://www.itjobswatch.co.uk/jobs/uk/css.do) |
| S05 | SQL | Rising | HackerRank invites +25.5%, active tests +6.5%, 2024 vs 2023. [Source][hr] |
| S06 | Git & Version Control | Declining | Git share 2.28% -> 1.33%, 2026-10-20. Evidence concerns Git specifically. [Source](https://www.itjobswatch.co.uk/jobs/uk/git.do) |
| S07 | Data Structures & Algorithms | Declining | Data Structures 0.72% -> 0.38%, 2026-08-28; Algorithms 1.36% -> 0.52%, 2026-09-04. Both components agree. [Data Structures](https://www.itjobswatch.co.uk/jobs/uk/data%20structures.do), [Algorithms](https://www.itjobswatch.co.uk/jobs/uk/algorithms.do) |
| S08 | Software Testing | Declining | Share 0.94% -> 0.82%, 2026-10-21. [Source](https://www.itjobswatch.co.uk/jobs/uk/software%20testing.do) |
| S09 | API Development | Declining | Share 0.36% -> 0.26%, 2026-10-11. [Source](https://www.itjobswatch.co.uk/jobs/uk/api%20development.do) |
| S10 | UI/UX Design | Rising | WEF expects growth in design and user experience, 2025-2030, global employer survey; a corresponding-category mapping. [Source][wef] |
| S11 | Computer Graphics | Unverified | [Epic Games / Burning Glass](https://www.unrealengine.com/en-US/blog/demand-for-unreal-engine-and-real-time-3d-skills-at-all-time-high) reports historical growth in real-time 3D. This subset does not establish a current direction for all Computer Graphics. |
| S12 | 3D Modelling | Rising | Share 0.045% -> 0.093%, 2026-10-13; a small sample, counts 22 -> 110. [Source](https://www.itjobswatch.co.uk/jobs/uk/3d%20modelling.do) |
| S13 | Data Analysis | Declining | Share 2.62% -> 1.30%, 2026-10-20. [Source](https://www.itjobswatch.co.uk/jobs/uk/data%20analysis.do) |
| S14 | Statistics | Declining | Share 1.12% -> 0.32%, 2026-10-16. [Source](https://www.itjobswatch.co.uk/jobs/uk/statistics.do) |
| S15 | Data Visualisation | Declining | Share 0.94% -> 0.40%, 2026-10-19. [Source](https://www.itjobswatch.co.uk/jobs/uk/data%20visualisation.do) |
| S16 | Machine Learning | Declining | Share 4.95% -> 2.10%, 2026-10-21; absolute counts increase, so this is a share decline. [Source](https://www.itjobswatch.co.uk/jobs/uk/machine%20learning.do) |
| S17 | Database Design | Stable | [Miedema et al. (2025), Table 8](https://dbs-research.github.io/pdf/2025_recommendation.pdf): 13,926 postings, projected demand growth 2.7%. Projection horizon is unspecified; this is not an annual rate or current observed change. |
| S18 | Computer Networks | Unverified | [Skillenai Computer Networking](https://skillenai.com/data/skill/computer-networking), as of 2026-10-15, explicitly withholds an adjusted trend for insufficient comparable coverage. A count alone does not establish a direction. |
| S19 | Linux | Declining | Share 4.26% -> 2.21%, 2026-10-20. [Source](https://www.itjobswatch.co.uk/jobs/uk/linux.do) |
| S20 | Cloud Computing | Stable | Share 0.51% -> 0.50%, 2026-10-19, approximately -1.96% relative change within the band. [Source](https://www.itjobswatch.co.uk/jobs/uk/cloud%20computing.do) |
| S21 | Network Security | Declining | Share 1.07% -> 0.77%, 2026-10-20. [Source](https://www.itjobswatch.co.uk/jobs/uk/network%20security.do) |
| S22 | Security Risk Assessment | Unverified | [UK DSIT 2026 report](https://www.gov.uk/government/publications/cyber-security-skills-in-the-uk-labour-market-2026/cyber-security-skills-in-the-uk-labour-market-2026) covers broader risk analysis, governance and risk-management gaps. These do not isolate this skill's directional demand. |

## What remains necessary

- S11: comparable postings or an explicit forecast for Computer Graphics;
  separate a real-time 3D subset if the catalogue is intentionally narrowed.
- S18: a comparable Computer Networking series, not a single current count or
  a combined communications/cybersecurity category.
- S22: a comparable Security Risk Assessment series or explicit skill forecast;
  a skills-gap snapshot is not a demand-growth measurement.

Catalogue labels have not been changed to make broader evidence appear exact.
Unverified skills retain the existing insufficient-evidence state and contribute
no directional adjustment. They remain in the scoring denominator.

## Geographic and update limits

These are international evidence sources, not 22 Malaysian skill measurements.
DOSM's Malaysian Software Developers observations remain separate in
`market_signals.csv`. The sources are online and updateable; this implementation
uses manually reviewed snapshots, with no automatic website synchronisation.

When reviewing a source update, retain the metric, period, source date type and
raw values. Recheck both components of compound skills. If a source retracts or
invalidates a comparison, remove its directional classification rather than
carrying the last badge forward as a new observation.

[hr]: https://www.hackerrank.com/blog/top-developer-skills-in-2025-momentum-not-mayhem/
[wef]: https://www.weforum.org/publications/the-future-of-jobs-report-2025/in-full/3-skills-outlook/
