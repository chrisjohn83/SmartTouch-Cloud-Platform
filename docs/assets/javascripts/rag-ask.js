const localApiBaseUrl = "http://127.0.0.1:8000";
const productionApiBaseUrl = "";
const chatRootId = "smarttouch-chat";
const insufficientInformationMessage =
  "The SmartTouch documentation does not provide enough cited information to answer this question.";

function initializeSmartTouchChat() {
  if (document.getElementById(chatRootId)) {
    return;
  }

  const root = document.createElement("div");
  root.id = chatRootId;
  root.className = "st-chat";
  root.dataset.open = "false";
  root.innerHTML = `
    <button class="st-chat-launcher" type="button" aria-expanded="false" aria-controls="st-chat-panel">
      <span class="st-chat-launcher-icon" aria-hidden="true">✦</span>
      <span>Ask SmartTouch</span>
    </button>
    <aside id="st-chat-panel" class="st-chat-panel" aria-label="Ask SmartTouch" aria-hidden="true">
      <header class="st-chat-header">
        <div>
          <span class="st-chat-eyebrow">Documentation assistant</span>
          <h2>Ask SmartTouch</h2>
        </div>
        <button class="st-chat-close" type="button" aria-label="Close Ask SmartTouch">×</button>
      </header>
      <div class="st-chat-messages" aria-live="polite">
        <div class="st-chat-message st-chat-message-assistant">
          Ask me about devices, deployments, remote access, APIs, or platform troubleshooting.
        </div>
      </div>
      <div class="st-chat-suggestions" aria-label="Example questions">
        <button type="button" data-st-query="Agent cannot reach the broker">Broker connection</button>
        <button type="button" data-st-query="How do I roll back a failed release?">Rollback a release</button>
      </div>
      <form class="st-chat-form">
        <label class="st-chat-visually-hidden" for="st-chat-query">Ask a documentation question</label>
        <textarea id="st-chat-query" rows="2" placeholder="Ask about SmartTouch…" required></textarea>
        <div class="st-chat-controls">
          <label class="st-chat-toggle">
            <input class="st-chat-use-kg" type="checkbox" checked>
            <span>Knowledge graph</span>
          </label>
          <button class="st-chat-submit" type="submit">Send</button>
        </div>
      </form>
    </aside>
  `;

  document.body.appendChild(root);
  bindSmartTouchChat(root);
}

function bindSmartTouchChat(root) {
  const launcher = root.querySelector(".st-chat-launcher");
  const panel = root.querySelector(".st-chat-panel");
  const closeButton = root.querySelector(".st-chat-close");
  const form = root.querySelector(".st-chat-form");
  const queryInput = root.querySelector("#st-chat-query");
  const knowledgeGraphToggle = root.querySelector(".st-chat-use-kg");
  const submit = root.querySelector(".st-chat-submit");
  const messages = root.querySelector(".st-chat-messages");

  const setOpen = (isOpen) => {
    root.dataset.open = String(isOpen);
    launcher.setAttribute("aria-expanded", String(isOpen));
    panel.setAttribute("aria-hidden", String(!isOpen));

    if (isOpen) {
      window.setTimeout(() => queryInput.focus(), 180);
    } else {
      launcher.focus();
    }
  };

  launcher.addEventListener("click", () => setOpen(true));
  closeButton.addEventListener("click", () => setOpen(false));

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && root.dataset.open === "true") {
      setOpen(false);
    }
  });

  root.querySelectorAll("[data-st-query]").forEach((button) => {
    button.addEventListener("click", () => {
      queryInput.value = button.dataset.stQuery || "";
      queryInput.focus();
    });
  });

  queryInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      form.requestSubmit();
    }
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const query = queryInput.value.trim();
    if (!query || submit.disabled) {
      return;
    }

    appendMessage(messages, "user", query);
    queryInput.value = "";
    const pendingMessage = appendMessage(
      messages,
      "assistant",
      "Searching SmartTouch documentation…",
      true
    );
    const apiBaseUrl = resolveApiBaseUrl();

    if (!apiBaseUrl) {
      replaceMessage(
        pendingMessage,
        "The production documentation assistant is not connected yet. Configure SMARTTOUCH_RAG_API_BASE_URL to enable answers."
      );
      return;
    }

    setBusy(submit, true);

    try {
      const response = await fetch(`${apiBaseUrl}/answer`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query,
          limit: 3,
          use_knowledge_graph: Boolean(knowledgeGraphToggle.checked)
        })
      });

      if (!response.ok) {
        throw new Error(`Request failed: ${response.status}`);
      }

      const data = await response.json();
      const answer =
        cleanAnswer(data.answer || "") || "No cited answer was returned for this question.";
      replaceMessage(pendingMessage, answer, data.sources || []);
    } catch (error) {
      replaceMessage(pendingMessage, friendlyError(error));
    } finally {
      setBusy(submit, false);
      queryInput.focus();
    }
  });
}

function appendMessage(container, role, text, pending = false) {
  const message = document.createElement("div");
  message.className = `st-chat-message st-chat-message-${role}`;
  message.textContent = text;

  if (pending) {
    message.classList.add("st-chat-message-pending");
  }

  container.appendChild(message);
  container.scrollTop = container.scrollHeight;
  return message;
}

function replaceMessage(message, text, sources = []) {
  message.classList.remove("st-chat-message-pending");
  message.textContent = text;

  if (sources.length) {
    const sourceList = document.createElement("div");
    sourceList.className = "st-chat-sources";

    sources.forEach((source, index) => {
      const link = document.createElement("a");
      link.href = safeSourceUrl(source.source_url);
      link.target = "_blank";
      link.rel = "noopener";
      link.textContent =
        source.heading || source.heading_label || source.title || `Source ${index + 1}`;
      sourceList.appendChild(link);
    });

    message.appendChild(sourceList);
  }

  message.parentElement.scrollTop = message.parentElement.scrollHeight;
}

function resolveApiBaseUrl() {
  const override = window.SMARTTOUCH_RAG_API_BASE_URL;

  if (override) {
    return String(override).replace(/\/$/, "");
  }

  if (window.location.hostname === "127.0.0.1" || window.location.hostname === "localhost") {
    return localApiBaseUrl;
  }

  return productionApiBaseUrl.replace(/\/$/, "");
}

function cleanAnswer(answer) {
  return String(answer).replace(insufficientInformationMessage, "").trim();
}

function friendlyError(error) {
  const message = String(error?.message || error);

  if (message.includes("Failed to fetch")) {
    return "I could not reach the SmartTouch documentation service. Check the API connection and try again.";
  }

  return `I could not complete that request. ${message}`;
}

function safeSourceUrl(value) {
  try {
    const url = new URL(value || "", window.location.href);
    return ["http:", "https:"].includes(url.protocol) ? url.href : "#";
  } catch (_error) {
    return "#";
  }
}

function setBusy(button, busy) {
  button.disabled = busy;
  button.textContent = busy ? "Sending…" : "Send";
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initializeSmartTouchChat);
} else {
  initializeSmartTouchChat();
}
