"use strict";

const catalogue = JSON.parse(document.querySelector("#catalogue-data").textContent);
const skillNames = new Map(
  catalogue.skills.map((skill) => [skill.skill_id, skill.skill_name]),
);
const degreeNames = new Map(
  catalogue.degrees.map((degree) => [degree.degree_id, degree.degree_name]),
);
const form = document.querySelector("#profile-form");
const degree = document.querySelector("#degree");
const search = document.querySelector("#skill-search");
const checkboxes = [...form.querySelectorAll('input[type="checkbox"]')];
const submitButton = form.querySelector('button[type="submit"]');
const errors = document.querySelector("#form-errors");
const empty = document.querySelector("#results-empty");
const content = document.querySelector("#results-content");
const status = document.querySelector("#results-status");
let matches = [];
let requestVersion = 0;
let controller = null;

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function skillList(ids) {
  return ids.map((id) => skillNames.get(id) || id).join(", ");
}

function showErrors(messages) {
  errors.replaceChildren(...messages.map((message) => element("div", "", message)));
  errors.hidden = messages.length === 0;
  degree.setAttribute("aria-invalid", String(!degree.value && messages.length > 0));
}

function resetResults() {
  requestVersion += 1;
  if (controller) controller.abort();
  controller = null;
  submitButton.disabled = false;
  form.setAttribute("aria-busy", "false");
  document.querySelector("#analyse-label").textContent = "Analyse My Future";
  document.querySelector("#skill-count").textContent =
    `${checkboxes.filter((input) => input.checked).length} selected`;
  content.hidden = true;
  empty.hidden = false;
  status.textContent = "WAITING FOR YOUR PROFILE";
  matches = [];
  document.querySelector("#results-content").setAttribute("aria-busy", "false");
  showErrors([]);
}

degree.addEventListener("change", resetResults);
checkboxes.forEach((input) => input.addEventListener("change", resetResults));
search.addEventListener("input", () => {
  const query = search.value.trim().toLowerCase();
  let visible = 0;
  checkboxes.forEach((input) => {
    const show = skillNames.get(input.value).toLowerCase().includes(query);
    input.closest("label").hidden = !show;
    if (show) visible += 1;
  });
  document.querySelector("#no-skills").hidden = visible > 0;
});

function sourceLink(label, url) {
  const link = element("a", "", label);
  // Catalogue validation also checks the scheme on the server.
  const parsed = new URL(url);
  if (["http:", "https:"].includes(parsed.protocol)) link.href = parsed.href;
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  return link;
}

function renderCard(match, index) {
  const card = element("article", "career-card");
  const rank = element("div", "card-rank");
  rank.append(
    element("span", "", `0${index + 1} / CAREER MATCH`),
    element(
      "span",
      "small-tag",
      match.degree_related ? "DEGREE RELATED" : "CROSS-DEGREE",
    ),
  );
  const heading = element("h3", "", match.career.career_name);
  const score = element("div", "coverage", `${match.match_score.toFixed(1)}%`);
  score.append(element("span", "", "skill coverage"));
  const track = element("div", "coverage-track");
  track.setAttribute("aria-hidden", "true");
  const bar = element("span");
  bar.style.width = `${match.match_score}%`;
  track.append(bar);
  const count = element(
    "p",
    "coverage-count",
    `${match.matched_skill_ids.length} of ${match.career.required_skills.length} required skills selected`,
  );
  const matched = element("p", "skill-list");
  matched.append(
    element("strong", "", "Matched skills"),
    document.createTextNode(skillList(match.matched_skill_ids) || "None yet"),
  );
  const missing = element("p", "skill-list missing");
  missing.append(
    element("strong", "", "Skills to build"),
    document.createTextNode(
      skillList(match.missing_skill_ids) || "None in this skill subset",
    ),
  );
  const sources = element("div", "card-sources");
  sources.append(
    sourceLink(match.career.source_name, match.career.source_url),
    sourceLink("Skill evidence ↗", match.career.skill_source_url),
    element("small", "", `Source checked: ${match.career.source_checked_at}`),
  );
  const scenarioScore = element("div", "scenario-score");
  scenarioScore.append(
    element("span", "", "Scenario ranking score · estimate"),
    element("strong", "", `${match.ranking_score.toFixed(1)} / 100`),
  );
  const adjustment = element(
    "p",
    "field-help",
    `Trend adjustment: ${match.trend_adjustment >= 0 ? "+" : ""}${match.trend_adjustment.toFixed(2)} × ${match.scenario_multiplier}. ` +
      `Directional evidence: ${match.known_trend_count}/${match.career.required_skills.length} required skills. Unknown counts as 0, not Stable.`,
  );
  card.append(
    rank,
    heading,
    score,
    track,
    count,
    scenarioScore,
    adjustment,
    matched,
    missing,
    sources,
  );
  return card;
}

function trendBadge(direction) {
  return element(
    "span",
    `trend-badge trend-${direction}`,
    direction === "unknown"
      ? "Unknown · insufficient evidence"
      : direction.charAt(0).toUpperCase() + direction.slice(1),
  );
}

function renderTrend(trend) {
  const card = element("article", "trend-card");
  card.append(
    element("h4", "", skillNames.get(trend.skill_id) || trend.skill_id),
    trendBadge(trend.trend_direction),
  );
  const details = element("details", "trend-evidence");
  details.append(
    element("summary", "", "Evidence & dates"),
    element("p", "", trend.evidence_note),
  );
  if (trend.source_url) {
    const label = trend.trend_direction === "unknown" ? "Reviewed source" : "Source";
    details.append(
      sourceLink(`${label}: ${trend.source_name} ↗`, trend.source_url),
      element(
        "p",
        "",
        `${{ publication: "Published", snapshot: "Snapshot as of", review: "Reviewed" }[trend.source_date_kind] || "Source date"}: ${trend.source_date} · Period: ${trend.reference_period} · Reviewed: ${trend.updated_at}`,
      ),
    );
  }
  if (trend.source_skill) {
    details.append(element("p", "", `Source category: ${trend.source_skill}`));
  }
  if (trend.geography || trend.metric) {
    details.append(
      element("p", "", `Scope: ${trend.geography} · Metric: ${trend.metric}`),
    );
  }
  if (trend.supporting_urls) {
    trend.supporting_urls.split(";").forEach((url, index) => {
      details.append(sourceLink(`Supporting source ${index + 1} ↗`, url));
    });
  }
  card.append(details);
  return card;
}

function renderMarket(signal) {
  const target = document.querySelector("#market-content");
  target.replaceChildren();
  if (!signal.records.length) {
    target.append(
      element("p", "field-help", "Local market evidence unavailable for this career."),
    );
    return;
  }
  const records = element("div", "market-records");
  signal.records.forEach((record) => {
    const card = element("article", "market-record");
    card.append(
      element("h4", "", record.period),
      element("strong", "market-count", record.job_offerings.toLocaleString("en")),
      element("p", "", `Online job offerings · ${record.occupation_name}`),
      sourceLink(`${record.source_name} ↗`, record.source_url),
      element(
        "p",
        "field-help",
        `Published: ${record.source_date} · Data updated: ${record.updated_at}`,
      ),
      element("p", "field-help", record.mapping_note),
    );
    records.append(card);
  });
  target.append(records);
  if (signal.change_percent !== null) {
    target.append(
      element(
        "p",
        "market-change",
        `Quarter-on-quarter change: ${signal.change_percent >= 0 ? "+" : ""}${signal.change_percent.toFixed(2)}%`,
      ),
    );
  }
  target.append(element("p", "field-help", signal.comparison_note));
}

function renderGap() {
  const match = matches.find(
    (item) => item.career.career_id === document.querySelector("#career-select").value,
  );
  if (!match) return;
  document.querySelector("#gap-career-name").textContent = match.career.career_name;
  const matched = new Set(match.matched_skill_ids);
  document.querySelector("#gap-rows").replaceChildren(
    ...match.career.required_skills.map((id) => {
      const row = element("tr");
      const statusCell = element("td");
      statusCell.append(
        element(
          "span",
          matched.has(id) ? "skill-status" : "skill-status missing",
          matched.has(id) ? "✓ Selected" : "+ Missing",
        ),
      );
      row.append(element("td", "", skillNames.get(id) || id), statusCell);
      const trend = match.required_skill_trends.find((item) => item.skill_id === id);
      const trendCell = element("td");
      trendCell.append(trendBadge(trend.trend_direction));
      row.append(trendCell);
      return row;
    }),
  );
  document.querySelector("#evidence-note").textContent = match.career.evidence_note;
  document
    .querySelector("#required-trends")
    .replaceChildren(...match.required_skill_trends.map(renderTrend));
  renderMarket(match.market_signal);
}

document.querySelector("#career-select").addEventListener("change", renderGap);

function renderResults(data, scroll = true) {
  matches = data.matches;
  document.querySelector(`#scenario-${data.scenario}`).checked = true;
  document.querySelector("#scenario-state").textContent = data.trends_available
    ? `${data.scenario === "fast" ? "Fast" : "Moderate"} scenario · multiplier ${data.scenario_multiplier} · estimate`
    : "Trend evidence unavailable · skill coverage ranking";
  const supportedTrends = data.skill_trends.filter(
    (trend) => trend.trend_direction !== "unknown",
  );
  const unknownTrends = data.skill_trends.filter(
    (trend) => trend.trend_direction === "unknown",
  );
  document
    .querySelector("#skill-trends")
    .replaceChildren(...supportedTrends.map(renderTrend));
  document.querySelector("#trend-coverage-summary").textContent =
    `${supportedTrends.length} of ${data.skill_trends.length} selected skills have validated signals. ` +
    (supportedTrends.length
      ? "Review the metric and period in each evidence panel."
      : "No direct trend evidence is available for your selection; career requirements may have additional evidence below.");
  document.querySelector("#unknown-trends-details").hidden = unknownTrends.length === 0;
  document.querySelector("#unknown-trends-summary").textContent =
    `${unknownTrends.length} selected skills awaiting direct evidence (Unknown)`;
  document
    .querySelector("#unknown-skill-trends")
    .replaceChildren(...unknownTrends.map(renderTrend));
  document.querySelector("#profile-summary").textContent =
    `${degreeNames.get(data.profile.degree_id)} · ${data.profile.user_skill_ids.length} skills selected`;
  document
    .querySelector("#results-warnings")
    .replaceChildren(
      ...data.warnings.map((message) => element("p", "notice", message)),
    );
  document.querySelector("#career-cards").replaceChildren(...matches.map(renderCard));
  const select = document.querySelector("#career-select");
  select.replaceChildren(
    ...matches.map((match) => {
      const option = element("option", "", match.career.career_name);
      option.value = match.career.career_id;
      return option;
    }),
  );
  document.querySelector("#gap-section").hidden = matches.length === 0;
  if (matches.length) renderGap();
  document.querySelector("#market-section").hidden = matches.length === 0;
  document.querySelector("#excluded-details").hidden =
    data.excluded_records.length === 0;
  document
    .querySelector("#excluded-list")
    .replaceChildren(
      ...data.excluded_records.map((message) => element("li", "", message)),
    );
  const evidenceIssues = [...data.trend_issues, ...data.market_issues];
  document.querySelector("#evidence-issues").hidden = evidenceIssues.length === 0;
  document
    .querySelector("#evidence-issues-list")
    .replaceChildren(...evidenceIssues.map((issue) => element("li", "", issue)));
  status.textContent = matches.length
    ? `${matches.length} PATHS TO EXPLORE`
    : "PROFILE READY";
  empty.hidden = true;
  content.hidden = false;
  if (scroll)
    document.querySelector("#results").scrollIntoView({
      behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches
        ? "instant"
        : "smooth",
      block: "start",
    });
}

async function analyseProfile(scroll = true) {
  const selected = checkboxes
    .filter((input) => input.checked)
    .map((input) => input.value);
  const messages = [];
  if (!degree.value) messages.push("Select a supported degree.");
  if (!selected.length) messages.push("Select at least one skill.");
  showErrors(messages);
  if (messages.length) {
    (degree.value ? checkboxes[0] : degree)?.focus();
    return;
  }
  controller?.abort();
  const requestController = new AbortController();
  controller = requestController;
  const current = ++requestVersion;
  const timeout = setTimeout(() => requestController.abort(), 15000);
  submitButton.disabled = true;
  document.querySelector("#analyse-label").textContent = "Finding your direction…";
  form.setAttribute("aria-busy", "true");
  content.setAttribute("aria-busy", "true");
  status.textContent = "UPDATING RESULTS…";
  try {
    const response = await fetch("/api/analyse", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        degree_id: degree.value,
        user_skill_ids: selected,
        scenario: document.querySelector('input[name="scenario"]:checked').value,
      }),
      signal: requestController.signal,
    });
    const data = await response.json();
    if (current !== requestVersion) return;
    if (!response.ok) {
      resetResults();
      showErrors(data.errors || ["Unable to analyse your profile. Please try again."]);
      return;
    }
    renderResults(data, scroll);
  } catch (error) {
    if (current === requestVersion) {
      resetResults();
      showErrors([
        error.name === "AbortError"
          ? "The request timed out. Please try again."
          : "Unable to connect. Please try again.",
      ]);
    }
  } finally {
    clearTimeout(timeout);
    if (current === requestVersion) {
      controller = null;
      submitButton.disabled = false;
      document.querySelector("#analyse-label").textContent = "Analyse My Future";
      form.setAttribute("aria-busy", "false");
      content.setAttribute("aria-busy", "false");
    }
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  analyseProfile();
});

document.querySelectorAll('input[name="scenario"]').forEach((input) => {
  input.addEventListener("change", () => {
    if (!content.hidden) analyseProfile(false);
  });
});
