const localApiBaseUrl = "http://127.0.0.1:8000";
const productionApiBaseUrl = "";
const insufficientInformationMessage =
  "The SmartTouch documentation does not provide enough cited information to answer this question.";

let lastAnswerText = "";

document.addEventListener("DOMContentLoaded", () => {
  const submit = document.getElementById("rag-submit");
  const queryInput = document.getElementById("rag-query");
  const knowledgeGraphToggle = document.getElementById("rag-use-kg");
  const status = document.getElementById("rag-status");
  const answerCard = document.getElementById("rag-answer-card");
  const sourcesCard = document.getElementById("rag-sources-card");
  const answer = document.getElementById("rag-answer");
  const sources = document.getElementById("rag-sources");
  const copyButton = document.getElementById("rag-copy-answer");

  if (!submit || !queryInput || !status || !answer || !sources) {
    return;
  }

  document.querySelectorAll("[data-query]").forEach((button) => {
    button.addEventListener("click", () => {
      queryInput.value = button.getAttribute("data-query") || "";
      queryInput.focus();
    });
  });

  queryInput.addEventListener("keydown", (event) => {
    if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
      submit.click();
    }
  });

  if (copyButton) {
    copyButton.addEventListener("click", async () => {
      if (!lastAnswerText) {
        return;
      }

      await navigator.clipboard.writeText(lastAnswerText);
      const originalText = copyButton.textContent;
      copyButton.textContent = "Copied";
      window.setTimeout(() => {
        copyButton.textContent = originalText;
      }, 1200);
    });
  }

  submit.addEventListener("click", async () => {
    const query = queryInput.value.trim();
    const useKnowledgeGraph = Boolean(knowledgeGraphToggle?.checked);
    const apiBaseUrl = resolveApiBaseUrl();

    resetResponse({ answerCard, sourcesCard, answer, sources, status });

    if (!query) {
      setStatus(status, "Enter a question first.", "error");
      return;
    }

    if (!apiBaseUrl) {
      setStatus(
        status,
        "The production SmartTouch RAG API URL is not configured yet. Use the local MkDocs site with the local API, or set productionApiBaseUrl in rag-ask.js.",
        "error"
      );
      return;
    }

    submit.disabled = true;
    submit.textContent = "Asking...";
    setStatus(status, "Searching SmartTouch documentation and preparing a cited answer...", "loading");

    try {
      const response = await fetch(`${apiBaseUrl}/answer`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          query,
          limit: 3,
          use_knowledge_graph: useKnowledgeGraph
        })
      });

      if (!response.ok) {
        throw new Error(`Request failed: ${response.status}`);
      }

      const data = await response.json();
      const displayAnswer = cleanAnswer(data.answer || "");
      lastAnswerText = displayAnswer;

      renderAnswer(answer, displayAnswer);
      renderSources(sources, data.sources || []);

      answerCard?.classList.remove("rag-hidden");
      sourcesCard?.classList.remove("rag-hidden");
      setStatus(status, "Answer generated from SmartTouch documentation.", "success");
    } catch (error) {
      setStatus(status, friendlyError(error), "error");
    } finally {
      submit.disabled = false;
      submit.textContent = "Ask SmartTouch Docs";
    }
  });
});

function resolveApiBaseUrl() {
  const hostname = window.location.hostname;
  const override = window.SMARTTOUCH_RAG_API_BASE_URL;

  if (override) {
    return String(override).replace(/\/$/, "");
  }

  if (hostname === "127.0.0.1" || hostname === "localhost") {
    return localApiBaseUrl;
  }

  return productionApiBaseUrl.replace(/\/$/, "");
}

function friendlyError(error) {
  const message = String(error?.message || error);

  if (message.includes("Failed to fetch")) {
    return "Could not reach the SmartTouch RAG API. Check that the API is running and CORS allows this site.";
  }

  return `Error: ${message}`;
}

function resetResponse({ answerCard, sourcesCard, answer, sources, status }) {
  lastAnswerText = "";
  answer.innerHTML = "";
  sources.innerHTML = "";
  answerCard?.classList.add("rag-hidden");
  sourcesCard?.classList.add("rag-hidden");
  setStatus(status, "", "");
}

function setStatus(element, message, state) {
  element.textContent = message;
  element.dataset.state = state;
}

function cleanAnswer(answer) {
  return String(answer)
    .replace(insufficientInformationMessage, "")
    .trim();
}

function renderAnswer(container, answerText) {
  if (!answerText) {
    container.innerHTML = `<p class="rag-muted">No cited answer was returned for this question.</p>`;
    return;
  }

  container.innerHTML = `<div class="rag-answer-text">${formatAnswer(answerText)}</div>`;
}

function renderSources(container, sourceList) {
  if (!sourceList.length) {
    container.innerHTML = `<p class="rag-muted">No sources were returned.</p>`;
    return;
  }

  container.innerHTML = `
    <div class="rag-sources-grid">
      ${sourceList.map(renderSource).join("")}
    </div>
  `;
}

function renderSource(source) {
  const title = source.title || "SmartTouch documentation";
  const heading = source.heading || source.heading_label || source.source_path || "Source";
  const detail = source.heading_label || source.source_path || "";
  const url = source.source_url || "#";

  return `
    <article class="rag-source">
      <div class="rag-source-topline">
        <span class="rag-citation">${escapeHtml(source.citation_id || "source")}</span>
        <span>${escapeHtml(title)}</span>
      </div>
      <h3>${escapeHtml(heading)}</h3>
      <p>${escapeHtml(detail)}</p>
      <a href="${escapeAttribute(url)}" target="_blank" rel="noopener">Open source</a>
    </article>
  `;
}

function formatAnswer(value) {
  return escapeHtml(value)
    .replace(/```([\s\S]*?)```/g, (_match, code) => `<pre class="rag-code">${code.trim()}</pre>`)
    .replace(/\n/g, "<br>");
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function escapeAttribute(value) {
  return escapeHtml(value).replaceAll("`", "&#096;");
}
