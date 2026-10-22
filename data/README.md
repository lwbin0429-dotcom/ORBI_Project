# ORBI catalogue provenance

The five degree names follow the supplied ORBI SRS. The 22 skills form a manually
curated self-report catalogue. They are not an imported ESCO taxonomy.

## Career evidence

The 15 distinct occupation titles in `careers.csv` were checked against their
individual O*NET OnLine occupation pages on **21 October 2026**. Each row stores
its occupation URL, skill evidence URL, check date and an explanation of how ORBI
maps occupational tasks or software tools to our skill IDs. The UI displays these
links and explanations. The check date is our review date, not a publication date.

Source: O*NET OnLine, National Center for O*NET Development, U.S. Department of
Labor, Employment and Training Administration. Source material is available under
[Creative Commons Attribution 4.0](https://creativecommons.org/licenses/by/4.0/).
ORBI adapts the evidence into simplified skill subsets and degree associations;
these adaptations are not endorsed by O*NET. Full source records are linked in
each CSV row, for example [Data Scientists](https://www.onetonline.org/link/summary/15-2051.00).

`required_skills` means the skills required **by ORBI's comparison model**, not
that every employer requires every listed skill or tool. It is a small subset of
the occupation's capabilities. Tool availability is evidence of relevance, not
proof of a universal mandatory requirement. Some broad task descriptions are
interpreted into our catalogue labels, as stated in `evidence_note`. For example,
mathematical modelling is represented by Statistics for the research occupation.
Programming languages are selected examples rather than mandatory combinations.
Advanced roles may require further qualifications and experience beyond these
skills. A 100% result only covers this subset.

Degree associations are ORBI editorial choices used only for tie-breaking; they
are not official degree requirements. O*NET describes U.S. occupations and is not
evidence of Malaysian vacancies, salaries, demand or AI trends. No such claims
are made by Part 2.

## Editing the CSV files

- Keep IDs stable. Use semicolons inside multi-value fields such as
  `related_degrees` and `required_skills`.
- Use only degree and skill IDs present in the other catalogues. Unknown required
  skill IDs exclude the entire career so an incomplete denominator cannot inflate
  its score. Empty skill requirements also exclude the career.
- Provide valid HTTP(S) occupation and skill evidence URLs, a source name, a
  mapping explanation and an ISO `YYYY-MM-DD` review date. Recheck evidence when
  changing a mapping; loading a CSV only validates its structure, not its claims.
- Duplicate skill IDs are counted once. Duplicate career IDs and malformed CSV
  files are treated as catalogue errors.
- Add or revise skills only with corresponding review of affected career mappings.
  New data is read on each analysis request; no external API calls are made while matching.
- `sdg_ids` and `sdg_explanation` hold curated Part 5 contribution mappings.
  Every career and skill must have at least one goal and an explicit rationale.

Part 2 ranking uses exact skill coverage. Part 3 adds sourced skill trend
adjustments and Moderate/Fast estimates, then breaks ties with coverage, degree
relevance, career name and ID. See [trend methodology](trend_methodology.md) for
the evidence scope, formulas, sources and manual update procedure.

The 22-skill evidence audit is in [trend_evidence_audit.md](trend_evidence_audit.md).
As of 22 October 2026, 19 skills have directional evidence and three remain
unverified. Raw UK advert shares and counts are retained in
`trend_observations.csv`. These observations measure the UK permanent IT
recruitment sample; they do not establish Malaysian demand or AI causation.
Update the raw observations and trend explanation together after reviewing the
online source. A CSV edit is not automatic online synchronisation.

## Part 4 learning resources

`courses.csv` contains 22 resource-to-skill mappings reviewed on 22 October 2026.
Every catalogue skill has a starting resource. Records distinguish complete
courses, modules/selected sections and tutorials. All current entries have free
learning content; optional certificates and account requirements are disclosed.
Provider durations and ORBI planning estimates are explicitly separated.

See [course_methodology.md](course_methodology.md) for source scope, estimates,
required fields, prerequisite ordering and the manual update process.
These course mappings do not resolve the three remaining Part 3 trend-evidence
gaps: a course's existence is not evidence that job demand is rising.

## Part 5 SDG mappings

All 15 careers and 22 skills have reviewed goal IDs and contribution rationales.
`sdgs.csv` supplies official short goal names, UN definition URLs and source check
dates for SDGs 4, 8, 9, 10 and 16. The explanations refer to relevant targets and
state possible applications, not measured outcomes or UN endorsement. Recheck
the goal definitions and the mapping together when editing either catalogue.
Invalid or missing goal definitions produce unavailable mappings while leaving
career matching functional. Details: [Part 5 setup](../docs/part5_setup.md).
