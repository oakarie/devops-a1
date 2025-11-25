const API_BASE_URL = "http://127.0.0.1:8000";

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("company-form");
  const resultsContainer = document.getElementById("results-content");
  const submitButton = form?.querySelector('button[type="submit"]');
  const signalInputs = Array.from(document.querySelectorAll("input[data-signal]"));

  if (!form || !resultsContainer) {
    return;
  }

  const escapeHtml = (value = "") =>
    value
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");

  const cleanString = (value) => {
    const trimmed = value?.trim();
    return trimmed ? trimmed : null;
  };

  const compactObject = (obj) =>
    Object.fromEntries(
      Object.entries(obj).filter(([, value]) => value !== null && value !== undefined)
    );

  const renderMessage = (message, isError = false) => {
    resultsContainer.innerHTML = `<p class="${isError ? "status status-error" : "status"}">${escapeHtml(
      message
    )}</p>`;
  };

  const renderResult = ({ score, badge, evidence }) => {
    const evidenceItems = Array.isArray(evidence)
      ? evidence
      : evidence
      ? [evidence]
      : [];

    const evidenceMarkup =
      evidenceItems.length > 0
        ? `<ul class="evidence-list">
            ${evidenceItems.map((item) => `<li>${escapeHtml(String(item))}</li>`).join("")}
          </ul>`
        : `<p class="muted">No evidence returned by the evaluator.</p>`;

    resultsContainer.innerHTML = `
      <div class="result-grid">
        <div>
          <p class="result-label">Score</p>
          <p class="result-value">${score ?? "—"}</p>
        </div>
        <div>
          <p class="result-label">Badge</p>
          <p class="result-value">${escapeHtml(badge || "Not awarded")}</p>
        </div>
      </div>
      <div class="result-evidence">
        <p class="result-label">Evidence</p>
        ${evidenceMarkup}
      </div>
    `;
  };

  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    if (submitButton) {
      submitButton.disabled = true;
    }

    renderMessage("Evaluating…");

    const formData = new FormData(form);
    const companyPayload = compactObject({
      name: cleanString(formData.get("name")),
      website: cleanString(formData.get("website")),
      country: cleanString(formData.get("country")),
      state: cleanString(formData.get("state")),
      city: cleanString(formData.get("city")),
      industry: cleanString(formData.get("industry")),
      niche: cleanString(formData.get("niche")),
    });

    if (!companyPayload.name) {
      renderMessage("Please provide a company name before evaluating.", true);
      if (submitButton) {
        submitButton.disabled = false;
      }
      form.querySelector("#name")?.focus();
      return;
    }

    const signalPayload = signalInputs.reduce(
      (acc, input) => ({ ...acc, [input.dataset.signal]: input.checked }),
      {}
    );

    try {
      const companyResponse = await fetch(`${API_BASE_URL}/companies`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(companyPayload),
      });

      if (!companyResponse.ok) {
        throw new Error("Unable to create the company record.");
      }

      const companyData = await companyResponse.json();
      const companyId = companyData?.company_id ?? companyData?.id;

      if (!companyId) {
        throw new Error("The backend did not return a company_id.");
      }

      const evaluationResponse = await fetch(`${API_BASE_URL}/evaluate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ company_id: companyId, ...signalPayload }),
      });

      if (!evaluationResponse.ok) {
        throw new Error("Evaluation request failed.");
      }

      const evaluationData = await evaluationResponse.json();
      renderResult({
        score: evaluationData?.score,
        badge: evaluationData?.badge,
        evidence: evaluationData?.evidence,
      });
    } catch (error) {
      // Keep the failure visible but friendly for the class demo.
      renderMessage(
        error instanceof Error
          ? error.message
          : "Something went wrong while evaluating.",
        true
      );
    } finally {
      if (submitButton) {
        submitButton.disabled = false;
      }
    }
  });
});

