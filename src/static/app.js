"use strict";

// Frontend controller: read the rendered catalogue, submit profiles to Flask,
// render server-calculated results, and request optional personalised AI advice.
// Scores and evidence come from the backend; this file manages browser state/UI.

// Build ID-to-label maps from Jinja's JSON block instead of duplicating CSV labels.
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

// Analysis and AI have separate request versions/controllers so stale responses
// cannot replace results after the user changes their profile or chosen career.
let matches = [];
let requestVersion = 0;
let controller = null;
let analysisData = null;
let insightVersion = 0;
let insightController = null;
let insightConfig = null;
let nextInsightVariant = "initial";
let hasInsight = false;
const insightButton = document.querySelector("#generate-insight");

// Clear advice tied to old inputs and stop waiting on its browser request.
function clearInsight() {
  nextInsightVariant = "initial";
  hasInsight = false;
  insightVersion += 1;
  if (insightController) insightController.abort();
  insightController = null;
  insightButton.disabled = insightConfig?.configured === false;
  insightButton.textContent = "Generate AI Insight";
  document.querySelector("#insight-output").replaceChildren();
  document.querySelector("#insight-output").setAttribute("aria-busy", "false");
  document.querySelector("#insight-status").textContent =
    insightConfig?.configured === false ? insightConfig.message : "";
}

// Read only public configuration status; this does not call the model or expose keys.
async function checkInsightConfiguration() {
  try {
    const response = await fetch("/api/insight/status");
    if (!response.ok) return;
    insightConfig = await response.json();
    document.querySelector("#insight-model").textContent = insightConfig.configured
      ? `Model: ${insightConfig.model}`
      : insightConfig.message;
    if (!insightController) {
      insightButton.disabled = !insightConfig.configured;
    }
  } catch {
    document.querySelector("#insight-model").textContent =
      "Model configuration could not be checked. You can try generating an insight.";
  }
}

checkInsightConfiguration();

// Treat server/model text as textContent, never executable HTML.
function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

// Resolve stable skill IDs for display, retaining an ID if a label is unavailable.
function skillList(ids) {
  return ids.map((id) => skillNames.get(id) || id).join(", ");
}

// Keep inline validation and the degree field's accessible error state in sync.
function showErrors(messages) {
  errors.replaceChildren(...messages.map((message) => element("div", "", message)));
  errors.hidden = messages.length === 0;
  degree.setAttribute("aria-invalid", String(!degree.value && messages.length > 0));
}

// A profile edit invalidates previous matches until the user analyses again.
function resetResults() {
  clearInsight();
  analysisData = null;
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

// Profile changes clear stale output; search only filters visible skill choices.
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

// Open learning resources without allowing access to the opener page.
function resourceLink(label, url) {
  const link = element("a", "", label);
  // Catalogue validation also checks the scheme on the server.
  const parsed = new URL(url);
  if (["http:", "https:"].includes(parsed.protocol)) link.href = parsed.href;
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  return link;
}

// Display raw coverage and the scenario estimate separately for one ranked career.
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
  const scenarioScore = element("div", "scenario-score");
  scenarioScore.append(
    element("span", "", "Scenario ranking score · estimate"),
    element("strong", "", `${match.ranking_score.toFixed(1)} / 100`),
  );
  const adjustment = element(
    "p",
    "field-help",
    `Trend evidence: ${match.known_trend_count}/${match.career.required_skills.length} skills`,
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
  );
  return card;
}

// Unknown evidence is an explicit state, not a substitute for a Stable classification.
function trendBadge(direction) {
  return element(
    "span",
    `trend-badge trend-${direction}`,
    direction === "unknown"
      ? "Unknown · insufficient evidence"
      : direction.charAt(0).toUpperCase() + direction.slice(1),
  );
}

// Display the skill name and trend direction.
function renderTrend(trend) {
  const card = element("article", "trend-card");
  card.append(
    element("h4", "", skillNames.get(trend.skill_id) || trend.skill_id),
    trendBadge(trend.trend_direction),
  );
  return card;
}

// Preserve the backend's prerequisite order, cost notes and estimate/provider labels.
function renderLearningPath(match) {
  const path = match.learning_path;
  const steps = document.querySelector("#learning-steps");
  const unavailable = document.querySelector("#learning-unavailable");
  steps.replaceChildren();
  unavailable.replaceChildren();
  document.querySelector("#learning-career").textContent = match.career.career_name;
  document.querySelector("#learning-summary").textContent = path.missing_skill_count
    ? `${path.covered_skill_count}/${path.missing_skill_count} skill gaps covered · ` +
      `${path.total_estimated_hours.toLocaleString("en", { maximumFractionDigits: 2 })} estimated hours`
    : "No skill gaps in this catalogue.";
  const typeLabels = {
    course: "Course",
    module: "Module / selected sections",
    tutorial: "Tutorial",
  };
  const costLabels = {
    free: "Free learning content",
    paid: "Paid learning content",
    free_content_paid_certificate: "Free content · paid certificate option",
  };
  path.steps.forEach((step) => {
    const course = step.course;
    const item = element("li", "learning-step");
    const number = element(
      "span",
      "learning-number",
      String(step.sequence).padStart(2, "0"),
    );
    number.setAttribute("aria-hidden", "true");
    const body = element("div", "learning-body");
    body.append(
      element("p", "eyebrow", skillNames.get(course.skill_id)),
      element("h4", "", course.course_name),
      element(
        "p",
        "learning-provider",
        `${course.provider} · ${typeLabels[course.resource_type]}`,
      ),
    );
    const meta = element("p", "learning-meta");
    meta.append(
      element("span", "small-tag", costLabels[course.cost_type]),
      element(
        "span",
        "",
        `${course.estimated_hours} hours · ${course.duration_basis === "provider" ? "provider duration" : "ORBI estimate"}`,
      ),
    );
    body.append(meta, resourceLink("Open learning resource ↗", course.course_url));
    // Disclose preparation outside the plan without silently assigning extra courses.
    if (step.suggested_background_ids.length) {
      body.append(
        element(
          "p",
          "notice",
          `Additional preparation: ${skillList(step.suggested_background_ids)}`,
        ),
      );
    }
    item.append(number, body);
    steps.append(item);
  });
  path.unavailable.forEach((record) => {
    unavailable.append(
      element(
        "p",
        "notice",
        `${skillNames.get(record.skill_id) || record.skill_id}: ${record.reason}`,
      ),
    );
  });
}

// Display SDG names and ORBI contribution rationales.
function sdgCard(label, mapping) {
  const card = element("article", "sdg-card");
  card.append(element("h4", "", label));
  const goals = element("div", "sdg-goals");
  mapping.goals.forEach((goal) => {
    goals.append(element("span", "", `SDG ${goal.sdg_id} · ${goal.sdg_name}`));
  });
  card.append(goals, element("p", "", mapping.explanation));
  return card;
}

// Update chosen-career and required-skill contributions from the same result object.
function renderSDGs(match) {
  document
    .querySelector("#career-sdg")
    .replaceChildren(sdgCard(match.career.career_name, match.sdg_mapping));
  document
    .querySelector("#required-sdgs")
    .replaceChildren(
      ...match.required_skill_sdgs.map((mapping) =>
        sdgCard(skillNames.get(mapping.skill_id), mapping),
      ),
    );
}

// A career switch refreshes all dependent detail panels and invalidates old advice.
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
  renderLearningPath(match);
  renderSDGs(match);
  clearInsight();
}

document.querySelector("#career-select").addEventListener("change", renderGap);

// Render one complete analysis response so profile/scenario panels stay consistent.
function renderResults(data, scroll = true) {
  analysisData = data;
  matches = data.matches;
  document.querySelector(`#scenario-${data.scenario}`).checked = true;
  document.querySelector("#scenario-state").textContent = data.trends_available
    ? `${data.scenario === "fast" ? "Fast" : "Moderate"} scenario · multiplier ${data.scenario_multiplier} · estimate`
    : "Trend evidence unavailable · skill coverage ranking";
  // Group unresolved evidence separately while keeping its coverage count visible.
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
    `${supportedTrends.length}/${data.skill_trends.length} skills with trend evidence`;
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
  document.querySelector("#learning-section").hidden = matches.length === 0;
  document.querySelector("#sdg-section").hidden = matches.length === 0;
  document.querySelector("#insight-section").hidden = matches.length === 0;
  document
    .querySelector("#selected-sdgs")
    .replaceChildren(
      ...data.selected_skill_sdgs.map((mapping) =>
        sdgCard(skillNames.get(mapping.skill_id), mapping),
      ),
    );
  document.querySelector("#excluded-details").hidden =
    data.excluded_records.length === 0;
  document
    .querySelector("#excluded-list")
    .replaceChildren(
      ...data.excluded_records.map((message) => element("li", "", message)),
    );
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

// Validate basic inputs for fast feedback, then let Flask perform authoritative checks.
async function analyseProfile(scroll = true) {
  clearInsight();
  analysisData = null;
  insightButton.disabled = true;
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
  // The version check also protects against a response arriving after fetch abort.
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

// AI runs only on this explicit action. After success, another perspective gets
// a fresh generation identifier to encourage a different project theme.
insightButton.addEventListener("click", async () => {
  if (!analysisData) return;
  const match = matches.find(
    (item) => item.career.career_id === document.querySelector("#career-select").value,
  );
  if (!match) return;
  const variant = nextInsightVariant;
  clearInsight();
  nextInsightVariant = variant;
  const version = insightVersion;
  const requestController = new AbortController();
  insightController = requestController;
  const timeout = setTimeout(() => requestController.abort(), 600000);
  const message = document.querySelector("#insight-status");
  const output = document.querySelector("#insight-output");
  const started = Date.now();
  const stageMessage = "Generating suggestions…";
  const progress = setInterval(() => {
    if (version === insightVersion) {
      message.textContent = `${stageMessage} · ${Math.floor((Date.now() - started) / 1000)}s elapsed`;
    }
  }, 1000);
  insightButton.disabled = true;
  insightButton.textContent = "Generating insight…";
  output.setAttribute("aria-busy", "true");
  message.textContent = stageMessage;
  try {
    const response = await fetch("/api/insight", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ...analysisData.profile,
        scenario: analysisData.scenario,
        career_id: document.querySelector("#career-select").value,
        request_variant: variant,
      }),
      signal: requestController.signal,
    });
    const data = await response.json();
    if (version !== insightVersion) return;
    if (!response.ok) {
      message.textContent = (data.errors || ["AI insight is unavailable."]).join(" ");
      return;
    }
    // Render the accepted proposals with backend-resolved resource links.
    const panels = data.recommendations.map((advice) => {
      const panel = element("section", "insight-result");
      panel.append(
        element("span", "small-tag", `AI PROPOSAL · ${advice.category}`),
        element("h4", "", advice.title),
      );
      [
        ["Try this", advice.action],
        ["Create", advice.deliverable],
        ["Check your work", advice.success_check],
        ["Why it fits you", advice.reason],
      ].forEach(([label, text]) => {
        const line = element("p");
        line.append(element("strong", "", `${label}: `), document.createTextNode(text));
        panel.append(line);
      });
      panel.append(element("p", "field-help", `Skills: ${advice.skills.join(", ")}`));
      const sources = element("div", "insight-resources");
      advice.sources.forEach((source) =>
        sources.append(
          resourceLink(`Learning resource: ${source.label} ↗`, source.url),
        ),
      );
      panel.append(sources);
      return panel;
    });
    output.replaceChildren(...panels);
    hasInsight = true;
    // A new perspective may incur a new inference charge only when clicked again.
    nextInsightVariant = crypto.randomUUID();
    message.textContent = "Ready";
    // Total direct API time includes network overhead; it is not model time alone.
    if (data.timings?.request_seconds !== undefined) {
      message.textContent += ` · ${data.timings.request_seconds}s`;
    }
    document.querySelector("#insight-model").textContent = `Model: ${data.model}`;
  } catch (error) {
    if (version === insightVersion) {
      message.textContent =
        error.name === "AbortError"
          ? "The AI request timed out. Your career results remain available."
          : "AI insight could not be loaded. Your career results remain available.";
    }
  } finally {
    clearInterval(progress);
    clearTimeout(timeout);
    if (version === insightVersion) {
      insightController = null;
      insightButton.disabled = insightConfig?.configured === false;
      insightButton.textContent = hasInsight
        ? "Generate another perspective"
        : "Generate AI Insight";
      output.setAttribute("aria-busy", "false");
    }
  }
});

// Keep form submission on-page; changing a scenario reanalyses without auto-scrolling.
form.addEventListener("submit", (event) => {
  event.preventDefault();
  analyseProfile();
});

document.querySelectorAll('input[name="scenario"]').forEach((input) => {
  input.addEventListener("change", () => {
    if (!content.hidden) analyseProfile(false);
  });
});
