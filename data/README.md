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
- `sdg_ids` and `sdg_explanation` are reserved for Part 5 and currently blank.

Ranking is based on exact skill coverage, then degree relevance for exact ties,
then alphabetical career name and ID. There is no trend adjustment in Part 2.
