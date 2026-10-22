# Part 4 learning resources and pathway rules

Reviewed **22 October 2026**. `courses.csv` contains one starting resource for
each of the 22 skills. Records distinguish courses, modules/selected sections
and tutorials. A resource does not guarantee proficiency, certification,
employment or complete coverage of its mapped discipline.

## Study budgets and source register

Direct URLs, companion sections, cost notes and source dates are stored in
each CSV record and displayed with the learning step. Compound resource names
describe ORBI's selection of linked material, not a new official qualification.

| Skill | Resource | Hours | Basis |
| --- | --- | ---: | --- |
| Python | Harvard CS50P foundations, Weeks 0-4 | 24 | ORBI estimate |
| Java | CMU OLI Introduction to Programming in Java, Open & Free | 24 | ORBI estimate |
| JavaScript | MDN Dynamic scripting with JavaScript | 20 | ORBI estimate |
| HTML & CSS | MDN HTML structure and CSS styling basics | 16 | ORBI estimate |
| SQL | Harvard CS50 SQL Week 0: Querying | 6 | ORBI estimate |
| Git & Version Control | Microsoft Learn Introduction to Git | 1 | ORBI estimate |
| Data Structures & Algorithms | Harvard CS50x Weeks 3 and 5 | 12 | ORBI estimate |
| Software Testing | Harvard CS50P Week 5: Unit Tests | 4 | ORBI estimate |
| API Development | FastAPI Tutorial - User Guide | 12 | ORBI estimate |
| UI/UX Design | OpenLearn An introduction to interaction design | 10 | Provider |
| Computer Graphics | MIT OCW Computer Graphics, Fall 2012 | 60 | ORBI estimate |
| 3D Modelling | CG Cookie Blender Basics | 8 | ORBI estimate |
| Data Analysis | Kaggle Learn Pandas | 4 | ORBI estimate |
| Statistics | OpenLearn Getting started with Jamovi | 8 | Provider |
| Data Visualisation | Kaggle Learn Data Visualization | 4 | ORBI estimate |
| Machine Learning | Kaggle Learn Intro to Machine Learning | 6 | ORBI estimate |
| Database Design | Harvard CS50 SQL Week 2: Designing | 4 | ORBI estimate |
| Computer Networks | Cisco Networking Basics | 22 | Provider |
| Linux | Canonical's Linux command-line beginner tutorial | 2 | ORBI estimate |
| Cloud Computing | Microsoft Learn Describe cloud computing | 0.4 | Provider (24 minutes) |
| Network Security | OpenLearn cyber security Week 6 | 3 | ORBI estimate |
| Security Risk Assessment | OpenLearn Week 8 risk-analysis sections | 2 | ORBI estimate |

ORBI estimates are editable planning assumptions for study and practice of the
specified material. They are not published provider workloads and have not
been calibrated against learner completion data. Provider estimates also vary
by learner. Totals exclude extra background study; no completion date is implied.

## Provider checks and limitations

- [Harvard CS50P](https://cs50.harvard.edu/python/) and
  [CS50 SQL](https://cs50.harvard.edu/sql/) provide free OpenCourseWare. Optional
  edX verified certificates are separate. Python Weeks 0-4 exclude the separately
  mapped Unit Tests module. Querying and Designing use different SQL modules;
  the entire SQL course is not assigned twice.
- [CMU OLI Java](https://oli.cmu.edu/courses/introduction-to-programming-in-java-o-f/)
  offers free independent study material, without a teacher, college credit or
  completion certificate in the Open & Free version.
- [MDN Core](https://developer.mozilla.org/en-US/docs/Learn_web_development/Core)
  supplies public HTML, CSS and JavaScript modules. HTML & CSS requires studying
  both linked components, not just opening the first URL.
- [Microsoft Learn's FAQ](https://learn.microsoft.com/en-us/training/support/faq)
  confirms free training. Certification exams or deployed cloud infrastructure
  may cost extra. The selected cloud module teaches concepts and does not
  require purchasing a deployment.
- [OpenLearn interaction design](https://www.open.edu/openlearn/science-maths-technology/an-introduction-interaction-design/content-section-0)
  introduces user-centred design. [Jamovi](https://www.open.edu/openlearn/health-sports-psychology/getting-started-jamovi/content-section-0)
  introduces applied descriptive and inferential statistics. Their listed
  study durations are 10 and 8 hours respectively.
- [OpenLearn cyber security](https://www.open.edu/openlearn/digital-computing/introduction-cyber-security-stay-safe-online/content-section-overview)
  includes Week 6 network protection and Week 8 risk analysis and practice.
  Only the stated sections are assigned. They are foundations, not professional
  security engineering or risk-assessment qualifications.
- [MIT OCW Computer Graphics](https://ocw.mit.edu/courses/6-837-computer-graphics-fall-2012/)
  provides historical graphics foundations. C/C++, mathematics and older tools
  may need extra preparation. OCW does not supply the original MIT computing
  environment; the application discloses that limitation.
- [CG Cookie Blender Basics](https://www.cgcookie.com/courses/blender-basics-an-introduction-to-blender-3d-4-5-lts/)
  offers free streaming with a free account. Other CG Cookie courses can be
  paid. Resource naming follows the linked page's version-specific title.
- [Kaggle Learn](https://www.kaggle.com/learn) provides introductory practical
  resources; hosted exercises require an account. JavaScript-heavy pages were
  reviewed using public indexed descriptions. Signed-in exercise execution and
  certificate issuance were not tested.
- [Cisco Networking Basics](https://www.netacad.com/courses/networking-basics)
  offers free beginner learning. Cisco course material gives 22 hours; see the
  [provider document](https://www.netacad.com/authoring-resources/courses/ff9e491c-49be-4734-803e-a79e6e83dab1/850c6c9b-b788-4915-b7d1-ac915f584548/en-US/assets/IPD%20-%20Shaping%20Future%20Tech%20Careers%20Empowering%20Educators%20with%20Cisco%20Certification-Aligned%20Pathways_en-US_1755107650203.pdf).
  JavaScript and an account are needed. Review does not mean ORBI enrolled or
  completed the course.
- [FastAPI](https://fastapi.tiangolo.com/tutorial/) and
  [Canonical](https://ubuntu.com/desktop/docs/en/latest/tutorial/the-linux-command-line-for-beginners/)
  provide public tutorials, labelled as tutorials in ORBI. Python or a suitable
  Linux environment is needed respectively. Unit testing, Linux shell work,
  Seaborn visualisation and other scoped resources cover introductory portions
  of their wider skills; the mapping notes make this explicit.

## Required fields

```text
course_id, skill_id, course_name, provider, course_url, estimated_hours,
cost_type, learning_order, source_checked_at, resource_type, duration_basis,
duration_note, cost_note, mapping_note, prerequisite_skill_ids,
prerequisite_note, supporting_urls
```

Keep IDs stable. Every `skill_id` must exist in the catalogue. Duplicate course
IDs invalidate all occurrences. Hours must be positive and finite; review dates
must be ISO dates and cannot be in the future. URLs must use HTTP(S).

`cost_type` accepts `free`, `paid` or `free_content_paid_certificate`. All initial
entries offer free learning content. Trials must not be labelled free content.
`resource_type` accepts `course`, `module` or `tutorial`; `duration_basis` accepts
`provider` or `orbi_estimate`. Notes must accurately explain each choice.

`learning_order` is a positive ORBI priority, not a provider fact or trend score.
Prerequisite skill IDs and supporting URLs use semicolons. Non-catalogue
background, such as linear algebra, belongs in `prerequisite_note`.

## Planning rules

1. Use only the career's missing required skills, removing duplicates and
   already selected skills. Learning does not change self-reported selections.
2. Choose one validated resource per missing skill. If alternatives are added,
   the lowest learning order, then course ID, wins deterministically. This is
   curated preference, not a measured course-quality or cheapest-course ranking.
3. Put prerequisites that also have steps before dependent topics; otherwise
   use learning order and course ID. Cycles produce unavailable-resource notices
   rather than an impossible sequence.
4. Show unselected background outside the plan as a preparation notice. Do not
   silently add skills outside the career's gap or include their time in totals.
5. Number the steps and sum only their time budgets. Missing resources receive
   an explicit notice and contribute no invented hours or links.

Changing the selected career switches plans. Editing profile skills and
submitting again rebuilds them. There is no progress storage, enrolment action,
AI inference or automatic completion tracking in Part 4.

## Maintenance and failures

The CSV is read on every analysis. Validated edits take effect without a server
restart. Sources are manually reviewed, not synchronised automatically from
provider websites. Before judging or submission, revisit availability, cost,
scope, prerequisites, duration basis and source dates together; account and
regional terms may change.

Invalid rows are excluded with notices. A file-level error preserves career
matching and shows unavailable learning resources. No missing skills means no
assigned steps and zero extra hours. These resource mappings do not resolve the
three remaining Part 3 trend gaps: a course is not evidence of demand growth.
