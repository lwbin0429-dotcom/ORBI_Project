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
  card.append(rank, heading, score, track, count, matched, missing, sources);
  return card;
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
      return row;
    }),
  );
  document.querySelector("#evidence-note").textContent = match.career.evidence_note;
}

document.querySelector("#career-select").addEventListener("change", renderGap);

function renderResults(data) {
  matches = data.matches;
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
  document.querySelector("#results").scrollIntoView({
    behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches
      ? "instant"
      : "smooth",
    block: "start",
  });
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
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
  try {
    const response = await fetch("/api/analyse", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ degree_id: degree.value, user_skill_ids: selected }),
      signal: requestController.signal,
    });
    const data = await response.json();
    if (current !== requestVersion) return;
    if (!response.ok) {
      showErrors(data.errors || ["Unable to analyse your profile. Please try again."]);
      return;
    }
    renderResults(data);
  } catch (error) {
    if (current === requestVersion)
      showErrors([
        error.name === "AbortError"
          ? "The request timed out. Please try again."
          : "Unable to connect. Please try again.",
      ]);
  } finally {
    clearTimeout(timeout);
    if (current === requestVersion) {
      controller = null;
      submitButton.disabled = false;
      document.querySelector("#analyse-label").textContent = "Analyse My Future";
      form.setAttribute("aria-busy", "false");
    }
  }
});
