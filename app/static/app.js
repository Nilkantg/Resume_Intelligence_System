const form = document.querySelector("#analysis-form");
const submitButton = document.querySelector("#submit-button");
const statusEl = document.querySelector("#status");
const resultEl = document.querySelector("#result");
const rawOutputSection = document.querySelector("#raw-output-section");
const rawOutput = document.querySelector("#raw-output");

const scoreLabels = {
  ats_score: "ATS",
  semantic_match: "Semantic Match",
  skill_gap_score: "Skill Gap",
  section_quality: "Section Quality",
  keyword_optimization: "Keywords",
};

function setStatus(message, isError = false) {
  statusEl.textContent = message;
  statusEl.classList.toggle("error", isError);
}

function fillList(selector, items) {
  const list = document.querySelector(selector);
  list.innerHTML = "";

  if (!items || items.length === 0) {
    const item = document.createElement("li");
    item.textContent = "Not available.";
    list.appendChild(item);
    return;
  }

  items.forEach((value) => {
    const item = document.createElement("li");
    item.textContent = value;
    list.appendChild(item);
  });
}

function renderScores(scores) {
  const scoreGrid = document.querySelector("#scores");
  scoreGrid.innerHTML = "";

  Object.entries(scoreLabels).forEach(([key, label]) => {
    const value = scores?.[key] ?? 0;
    const card = document.createElement("article");
    card.className = "score-card";
    card.innerHTML = `<span>${label}</span><strong>${value}</strong>`;
    scoreGrid.appendChild(card);
  });
}

function setDownloadLink(selector, url) {
  const link = document.querySelector(selector);
  if (!url) {
    link.hidden = true;
    link.removeAttribute("href");
    return;
  }

  link.hidden = false;
  link.href = url;
}

function reportUrl(filename) {
  return filename ? `/reports/${filename}` : null;
}

function renderResult(data) {
  rawOutputSection.hidden = true;
  rawOutput.textContent = "";

  document.querySelector("#cache-label").textContent = data.cached
    ? `Loaded from cache: ${data.source_file || "resume"}`
    : `Fresh analysis: ${data.source_file || "resume"}`;
  document.querySelector("#candidate-name").textContent = data.candidate_name || "Candidate";
  document.querySelector("#candidate-email").textContent = data.candidate_email || "";
  document.querySelector("#summary").textContent = data.professional_summary || "Not available.";
  document.querySelector("#value-proposition").textContent =
    data.key_value_proposition || "Not available.";

  renderScores(data.overall_scores);
  fillList("#missing-skills", data.missing_skills);
  fillList("#keywords", data.recommended_keywords);
  fillList("#improvements", data.top_improvements);
  setDownloadLink("#json-download", data.download_urls?.json);
  setDownloadLink("#markdown-download", data.download_urls?.markdown);

  resultEl.hidden = false;
}

function renderMarkdown(markdown, response) {
  document.querySelector("#cache-label").textContent =
    response.headers.get("X-Resume-Analysis-Cached") === "true"
      ? `Loaded from cache: ${response.headers.get("X-Resume-Source-File") || "resume"}`
      : `Fresh analysis: ${response.headers.get("X-Resume-Source-File") || "resume"}`;
  document.querySelector("#candidate-name").textContent = "Markdown report";
  document.querySelector("#candidate-email").textContent = "";

  renderScores({});
  fillList("#missing-skills", []);
  fillList("#keywords", []);
  fillList("#improvements", []);
  document.querySelector("#summary").textContent = "Returned as Markdown.";
  document.querySelector("#value-proposition").textContent = "Use the report text below.";
  setDownloadLink("#json-download", reportUrl(response.headers.get("X-Resume-Json-Report")));
  setDownloadLink(
    "#markdown-download",
    reportUrl(response.headers.get("X-Resume-Markdown-Report"))
  );

  rawOutput.textContent = markdown;
  rawOutputSection.hidden = false;
  resultEl.hidden = false;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  submitButton.disabled = true;
  resultEl.hidden = true;
  setStatus("Processing resume. This can take a little while for the first run...");

  try {
    const formData = new FormData(form);
    const outputFormat = formData.get("output_format") || "json";
    const response = await fetch("/analyze", {
      method: "POST",
      body: formData,
    });

    if (outputFormat === "markdown" && response.ok) {
      const markdown = await response.text();
      renderMarkdown(markdown, response);
      setStatus(
        response.headers.get("X-Resume-Analysis-Cached") === "true"
          ? "Returned cached Markdown report."
          : "Markdown report complete."
      );
      return;
    }

    const data = await response.json();
    if (!response.ok || !data.success) {
      throw new Error(data.error || "Analysis failed.");
    }
    renderResult(data);
    setStatus(data.cached ? "Returned cached analysis." : "Analysis complete.");
  } catch (error) {
    setStatus(error.message, true);
  } finally {
    submitButton.disabled = false;
  }
});
