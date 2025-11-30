const API_BASE = "https://gpt-findability-backend.onrender.com";
const SIGNAL_FIELD_MAP = {
  contact_page: "has_contact_page",
  services_page: "has_clear_services_page",
  maps_listing: "has_gmb_or_maps_listing",
  recent_updates: "has_recent_updates",
  reviews: "has_reviews_or_testimonials",
  online_booking: "has_online_booking_or_form",
  schema_markup: "uses_basic_schema_markup",
  nap_consistent: "has_consistent_name_address_phone",
  loads_fast: "has_fast_load_time_claim",
  matches_intent: "content_matches_intent",
};

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("company-form");
  const resultsContainer = document.getElementById("results-content");
  const submitButton = form?.querySelector('button[type="submit"]');
  const signalInputs = Array.from(document.querySelectorAll("input[data-signal]"));
  const idleButtonLabel = submitButton?.textContent?.trim() || "Evaluate findability";

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

  const normalizeDetail = (detail) => {
    if (Array.isArray(detail)) {
      return detail
        .map((entry) => {
          if (typeof entry === "string") {
            return entry;
          }
          const loc = Array.isArray(entry?.loc) ? entry.loc.at(-1) : undefined;
          const msg = entry?.msg || entry?.message;
          if (loc && msg) {
            return `${loc}: ${msg}`;
          }
          return msg || JSON.stringify(entry);
        })
        .join("; ");
    }

    if (detail && typeof detail === "object") {
      if (detail.message) return detail.message;
      return JSON.stringify(detail);
    }

    return detail;
  };

  const fetchJson = async (path, options = {}) => {
    const response = await fetch(`${API_BASE}${path}`, options);
    let payload = null;

    try {
      payload = await response.json();
    } catch (err) {
      payload = null;
    }

    if (!response.ok) {
      const detail =
        normalizeDetail(payload?.detail) ||
        payload?.message ||
        (typeof payload === "string" ? payload : response.statusText || `status ${response.status}`);
      const friendly = detail
        ? `The server returned an error: ${detail}`
        : "The server returned an unexpected error.";
      throw new Error(friendly);
    }

    return payload;
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
      submitButton.textContent = "Evaluating...";
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

    const signalPayload = signalInputs.reduce((acc, input) => {
      const apiField = SIGNAL_FIELD_MAP[input.dataset.signal];
      if (!apiField) {
        return acc;
      }
      return { ...acc, [apiField]: input.checked };
    }, {});

    try {
      const companyData = await fetchJson("/companies", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(companyPayload),
      });

      const companyId = companyData?.company_id ?? companyData?.id;

      if (!companyId) {
        throw new Error("The backend did not return a company_id.");
      }

      const evaluationData = await fetchJson("/evaluate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ company_id: companyId, ...signalPayload }),
      });

      renderResult({
        score: evaluationData?.score,
        badge: evaluationData?.badge,
        evidence: evaluationData?.evidence,
      });
    } catch (error) {
      if (error instanceof TypeError) {
        renderMessage("Could not reach the backend. Please try again in a moment.", true);
      } else if (error instanceof Error) {
        renderMessage(error.message, true);
      } else {
        renderMessage("Something went wrong while evaluating.", true);
      }
    } finally {
      if (submitButton) {
        submitButton.disabled = false;
        submitButton.textContent = idleButtonLabel;
      }
    }
  });
});

