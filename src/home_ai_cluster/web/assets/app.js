(() => {
  const byteLimit = 65536;
  const messages = [];
  const assistantAttribution = new WeakMap();
  let requestActive = false;
  const error = document.querySelector("#request-error");
  const status = document.querySelector("#request-status");

  function setRequestActive(active, message = "") {
    requestActive = active;
    status.dataset.active = String(active);
    status.textContent = active ? message : "";
    document.querySelectorAll("[data-submit]").forEach((button) => {
      button.disabled = active;
    });
  }

  function clearError() { error.textContent = ""; }

  function showError(message) { error.textContent = message; }

  async function safeFailure(response) {
    let detail = "Request failed";
    try {
      const body = await response.json();
      if (typeof body.detail === "string") detail = body.detail;
    } catch (_) {
      // The existing safe response detail is unavailable.
    }
    return `${response.status}: ${detail}`;
  }

  async function post(path, body, activeMessage) {
    if (requestActive) return null;
    setRequestActive(true, activeMessage);
    clearError();
    try {
      const response = await fetch(path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!response.ok) {
        showError(await safeFailure(response));
        return null;
      }
      try {
        return await response.json();
      } catch (_) {
        showError("Request failed");
        return null;
      }
    } catch (_) {
      showError("Request failed");
      return null;
    } finally {
      setRequestActive(false);
    }
  }

  function renderChat() {
    const container = document.querySelector("#chat-conversation");
    container.replaceChildren();
    messages.forEach((message) => {
      const entry = document.createElement("article");
      entry.className = `message message-${message.role}`;
      const label = document.createElement("div");
      label.className = "message-label";
      label.textContent = message.role === "user" ? "You" : "Home AI Cluster";
      const content = document.createElement("div");
      content.className = "message-content";
      content.textContent = message.content;
      entry.append(label, content);
      const nodeId = assistantAttribution.get(message);
      if (nodeId) {
        const attribution = document.createElement("div");
        attribution.className = "attribution";
        attribution.textContent = `Handled by node ${nodeId}`;
        entry.append(attribution);
      }
      container.append(entry);
    });
  }

  function rollbackPendingMessage(pendingMessage) {
    const pendingIndex = messages.indexOf(pendingMessage);
    if (pendingIndex !== -1) messages.splice(pendingIndex, 1);
    renderChat();
  }

  function renderResult(container, content, nodeId) {
    container.hidden = false;
    container.replaceChildren();
    const value = document.createElement("div");
    value.textContent = content;
    const attribution = document.createElement("div");
    attribution.className = "attribution";
    attribution.textContent = `Handled by node ${nodeId}`;
    container.append(value, attribution);
  }

  document.querySelector("#chat-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const input = document.querySelector("#chat-message");
    if (!input.value.trim()) return showError("Message is required");
    const pendingMessage = { role: "user", content: input.value };
    messages.push(pendingMessage);
    renderChat();
    const result = await post("/v1/chat", { capability: "chat", messages }, "Sending…");
    if (result && typeof result.content === "string" && typeof result.node_id === "string") {
      const assistantMessage = { role: "assistant", content: result.content };
      assistantAttribution.set(assistantMessage, result.node_id);
      messages.push(assistantMessage);
      input.value = "";
      renderChat();
    } else {
      rollbackPendingMessage(pendingMessage);
      if (result) showError("Request failed");
    }
  });

  document.querySelector("#summarize-file").addEventListener("change", async (event) => {
    const [file] = event.target.files;
    if (!file) return;
    try {
      const text = new TextDecoder("utf-8", { fatal: true }).decode(await file.arrayBuffer());
      document.querySelector("#summarize-text").value = text;
    } catch (_) {
      showError("Selected file is not valid UTF-8 text");
    }
  });

  document.querySelector("#summarize-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const text = document.querySelector("#summarize-text").value;
    if (!text.trim() || new TextEncoder().encode(text).length > byteLimit) {
      return showError("Text must be non-blank and within the accepted limit");
    }
    const result = await post("/v1/summarize", { text }, "Summarizing…");
    if (result && typeof result.content === "string" && typeof result.node_id === "string") {
      renderResult(document.querySelector("#summarize-result"), result.content, result.node_id);
    } else if (result) showError("Request failed");
  });

  function addLabel(value = "") {
    const row = document.createElement("div");
    row.className = "label-row";
    const input = document.createElement("input");
    input.className = "classify-label";
    input.type = "text";
    input.value = value;
    input.setAttribute("aria-label", "Classification label");
    const remove = document.createElement("button");
    remove.type = "button";
    remove.textContent = "Remove label";
    remove.addEventListener("click", () => row.remove());
    row.append(input, remove);
    document.querySelector("#label-inputs").append(row);
  }

  addLabel();
  addLabel();
  document.querySelector("#add-label").addEventListener("click", () => addLabel());

  document.querySelector("#classify-file").addEventListener("change", async (event) => {
    const [file] = event.target.files;
    if (!file) return;
    try {
      const text = new TextDecoder("utf-8", { fatal: true }).decode(await file.arrayBuffer());
      document.querySelector("#classify-text").value = text;
    } catch (_) {
      showError("Selected file is not valid UTF-8 text");
    }
  });

  document.querySelector("#classify-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const text = document.querySelector("#classify-text").value;
    const labels = Array.from(document.querySelectorAll(".classify-label"), (input) => input.value);
    if (!text.trim() || new TextEncoder().encode(text).length > byteLimit || labels.length < 2) {
      return showError("Text and at least two labels are required");
    }
    const result = await post("/v1/classify", { text, labels }, "Classifying…");
    if (result && typeof result.selected_label === "string" && typeof result.node_id === "string") {
      renderResult(document.querySelector("#classify-result"), result.selected_label, result.node_id);
    } else if (result) showError("Request failed");
  });

  document.querySelectorAll('[role="tab"]').forEach((tab) => {
    tab.addEventListener("click", () => {
      document.querySelectorAll('[role="tab"]').forEach((other) => {
        const selected = other === tab;
        other.setAttribute("aria-selected", String(selected));
        document.querySelector(`#${other.getAttribute("aria-controls")}`).hidden = !selected;
      });
    });
  });
})();
