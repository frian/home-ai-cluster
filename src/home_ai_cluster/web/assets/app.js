(() => {
  const byteLimit = 65536;
  const pdfByteLimit = 8388608;
  // PDF.js 6.2.108: matched vendored main/worker assets.
  const pdfjsMainUrl = "/assets/pdfjs-6.2.108/pdf.min.mjs";
  const pdfjsWorkerUrl = "/assets/pdfjs-6.2.108/pdf.worker.min.mjs";
  const messages = [];
  const codeMessages = [];
  const assistantAttribution = new WeakMap();
  let requestActive = false;
  const themeKey = "home-ai-cluster.theme";
  const themeSelect = document.querySelector("#theme-select");
  const root = document.documentElement;
  const error = document.querySelector("#request-error");
  const status = document.querySelector("#request-status");

  function useSystemTheme() {
    root.removeAttribute("data-theme");
    themeSelect.value = "system";
  }

  function initializeThemePreference() {
    let theme;
    try {
      theme = localStorage.getItem(themeKey);
    } catch (_) {
      useSystemTheme();
      return;
    }
    if (theme === "light" || theme === "dark") {
      root.setAttribute("data-theme", theme);
      themeSelect.value = theme;
      return;
    }
    useSystemTheme();
    if (theme !== null) {
      try {
        localStorage.removeItem(themeKey);
      } catch (_) {
        // Invalid storage remains unavailable; System is still safe.
      }
    }
  }

  themeSelect.addEventListener("change", () => {
    const theme = themeSelect.value;
    if (theme === "light" || theme === "dark") {
      try {
        localStorage.setItem(themeKey, theme);
      } catch (_) {
        useSystemTheme();
        return;
      }
      root.setAttribute("data-theme", theme);
      return;
    }
    try {
      localStorage.removeItem(themeKey);
    } catch (_) {
      useSystemTheme();
      return;
    }
    useSystemTheme();
  });

  initializeThemePreference();

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
    document.querySelector("#chat-result-region").hidden = messages.length === 0;
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
    container.scrollTop = container.scrollHeight;
  }

  function rollbackPendingMessage(pendingMessage) {
    const pendingIndex = messages.indexOf(pendingMessage);
    if (pendingIndex !== -1) messages.splice(pendingIndex, 1);
    renderChat();
  }

  function renderCode() {
    const container = document.querySelector("#code-conversation");
    document.querySelector("#code-result-region").hidden = codeMessages.length === 0;
    container.replaceChildren();
    codeMessages.forEach((message) => {
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
    container.scrollTop = container.scrollHeight;
  }

  function rollbackPendingCodeMessage(pendingMessage) {
    const pendingIndex = codeMessages.indexOf(pendingMessage);
    if (pendingIndex !== -1) codeMessages.splice(pendingIndex, 1);
    renderCode();
  }

  function renderResult(container, content, nodeId) {
    container.closest(".result-section").hidden = false;
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
    input.value = "";
    const request = post(
      "/v1/chat",
      { capability: "chat", messages },
      "Generating response…",
    );
    status.scrollIntoView({ block: "nearest" });
    const result = await request;
    if (result && typeof result.content === "string" && typeof result.node_id === "string") {
      const assistantMessage = { role: "assistant", content: result.content };
      assistantAttribution.set(assistantMessage, result.node_id);
      messages.push(assistantMessage);
      renderChat();
    } else {
      rollbackPendingMessage(pendingMessage);
      if (input.value === "") input.value = pendingMessage.content;
      if (result) showError("Request failed");
    }
  });

  document.querySelector("#code-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const input = document.querySelector("#code-text");
    const pendingMessage = { role: "user", content: input.value };
    const candidateMessages = [...codeMessages, pendingMessage];
    const candidateBytes = candidateMessages.reduce(
      (total, message) => total + new TextEncoder().encode(message.content).length,
      0,
    );
    if (!input.value.trim() || candidateBytes > byteLimit) {
      return showError("Code conversation must be non-blank and within the accepted limit");
    }
    codeMessages.push(pendingMessage);
    renderCode();
    input.value = "";
    const request = post(
      "/v1/chat",
      { capability: "code", messages: codeMessages },
      "Generating code…",
    );
    status.scrollIntoView({ block: "nearest" });
    const result = await request;
    if (result && typeof result.content === "string" && typeof result.node_id === "string") {
      const assistantMessage = { role: "assistant", content: result.content };
      assistantAttribution.set(assistantMessage, result.node_id);
      codeMessages.push(assistantMessage);
      renderCode();
    } else {
      rollbackPendingCodeMessage(pendingMessage);
      if (input.value === "") input.value = pendingMessage.content;
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

  function extractedPdfText(items) {
    return items.map((item) => item.str + (item.hasEOL ? "\n" : " ")).join("");
  }

  async function readPdfText(file) {
    const pdfjs = await import(pdfjsMainUrl);
    pdfjs.GlobalWorkerOptions.workerSrc = pdfjsWorkerUrl;
    let loadingTask;
    try {
      const bytes = new Uint8Array(await file.arrayBuffer());
      loadingTask = pdfjs.getDocument({ data: bytes });
      const documentProxy = await loadingTask.promise;
      const pages = [];
      for (let number = 1; number <= documentProxy.numPages; number += 1) {
        const page = await documentProxy.getPage(number);
        const content = await page.getTextContent();
        pages.push(extractedPdfText(content.items));
      }
      return pages.join("\n\n");
    } catch (exception) {
      if (exception instanceof pdfjs.PasswordException) throw "password-protected";
      throw "unreadable";
    } finally {
      if (loadingTask) {
        try {
          await loadingTask.destroy();
        } catch (_) {
          // A teardown failure must not turn successfully extracted text unreadable.
        }
      }
    }
  }

  document.querySelector("#summarize-pdf").addEventListener("change", async (event) => {
    const [file] = event.target.files;
    if (!file) return;
    event.target.value = "";
    clearError();
    if (file.size > pdfByteLimit) {
      return showError("Selected PDF must be at most 8 MiB");
    }
    try {
      const text = await readPdfText(file);
      if (!text.trim()) return showError("Selected PDF contains no extractable text");
      const input = document.querySelector("#summarize-text");
      input.value = text;
      if (new TextEncoder().encode(text).length > byteLimit) {
        showError("Text must be non-blank and within the accepted limit");
      }
    } catch (failure) {
      if (failure === "password-protected") {
        showError("Selected PDF is password-protected");
      } else {
        showError("Selected PDF could not be read");
      }
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

  function updateLabelAccessibleNames() {
    document.querySelectorAll(".label-row").forEach((row, index) => {
      const labelNumber = index + 1;
      row.querySelector(".classify-label").setAttribute(
        "aria-label",
        `Classification label ${labelNumber}`,
      );
      row.querySelector("button").setAttribute(
        "aria-label",
        `Remove classification label ${labelNumber}`,
      );
    });
  }

  function addLabel(value = "") {
    const row = document.createElement("div");
    row.className = "label-row";
    const input = document.createElement("input");
    input.className = "classify-label";
    input.type = "text";
    input.value = value;
    const remove = document.createElement("button");
    remove.type = "button";
    remove.textContent = "Remove label";
    remove.addEventListener("click", () => {
      row.remove();
      updateLabelAccessibleNames();
    });
    row.append(input, remove);
    document.querySelector("#label-inputs").append(row);
    updateLabelAccessibleNames();
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

  const tabs = Array.from(document.querySelectorAll('[role="tab"]'));

  function activateTab(tab, focus = false) {
    tabs.forEach((other) => {
      const selected = other === tab;
      other.setAttribute("aria-selected", String(selected));
      other.tabIndex = selected ? 0 : -1;
      document.querySelector(`#${other.getAttribute("aria-controls")}`).hidden = !selected;
    });
    if (focus) tab.focus();
  }

  tabs.forEach((tab, index) => {
    tab.addEventListener("click", () => activateTab(tab));
    tab.addEventListener("keydown", (event) => {
      let nextIndex;
      if (event.key === "ArrowRight") nextIndex = (index + 1) % tabs.length;
      if (event.key === "ArrowLeft") nextIndex = (index - 1 + tabs.length) % tabs.length;
      if (event.key === "Home") nextIndex = 0;
      if (event.key === "End") nextIndex = tabs.length - 1;
      if (nextIndex === undefined) return;
      event.preventDefault();
      activateTab(tabs[nextIndex], true);
    });
  });
})();
