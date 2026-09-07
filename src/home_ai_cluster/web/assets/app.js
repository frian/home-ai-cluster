(() => {
  const byteLimit = 65536;
  const pdfByteLimit = 8388608;
  // PDF.js 6.2.108: matched vendored main/worker assets.
  const pdfjsMainUrl = "/assets/pdfjs-6.2.108/pdf.min.mjs";
  const pdfjsWorkerUrl = "/assets/pdfjs-6.2.108/pdf.worker.min.mjs";
  const messages = [];
  const codeMessages = [];
  const assistantAttribution = new WeakMap();
  const themeKey = "home-ai-cluster.theme";
  const themeSelect = document.querySelector("#theme-select");
  const root = document.documentElement;
  const requestContexts = {
    chat: createRequestContext("#chat-form", "#chat-error", "#chat-status"),
    summarize: createRequestContext("#summarize-form", "#summarize-error", "#summarize-status"),
    classify: createRequestContext("#classify-form", "#classify-error", "#classify-status"),
    code: createRequestContext("#code-form", "#code-error", "#code-status"),
    configuration: createRequestContext("#configuration-form", "#configuration-error", "#configuration-status"),
    remoteNodes: createRequestContext("#remote-node-form", "#remote-node-error", "#remote-node-status"),
  };

  function createRequestContext(formSelector, errorSelector, statusSelector) {
    const form = document.querySelector(formSelector);
    return {
      active: false,
      form,
      submit: form.querySelector("[data-submit]"),
      error: document.querySelector(errorSelector),
      status: document.querySelector(statusSelector),
    };
  }

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

  function setRequestActive(context, active, message = "") {
    context.active = active;
    context.status.dataset.active = String(active);
    context.status.textContent = active ? message : "";
    context.submit.disabled = active;
  }

  function clearError(context) { context.error.textContent = ""; }

  function showError(context, message) { context.error.textContent = message; }

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

  async function post(context, path, body, activeMessage) {
    if (context.active) return null;
    setRequestActive(context, true, activeMessage);
    clearError(context);
    try {
      const response = await fetch(path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!response.ok) {
        showError(context, await safeFailure(response));
        return null;
      }
      try {
        return await response.json();
      } catch (_) {
        showError(context, "Request failed");
        return null;
      }
    } catch (_) {
      showError(context, "Request failed");
      return null;
    } finally {
      setRequestActive(context, false);
    }
  }

  const configurationRuntime = document.querySelector("#configuration-runtime");
  const configurationCapabilitiesAbsent = document.querySelector("#configuration-capabilities-absent");
  const remoteNodeForm = document.querySelector("#remote-node-form");
  const remoteNodeId = document.querySelector("#remote-node-id");
  const remoteNodeBaseUrl = document.querySelector("#remote-node-base-url");
  const remoteNodeCancel = document.querySelector("#remote-node-cancel");
  const remoteNodesList = document.querySelector("#remote-nodes-list");
  let configurationLoaded = false;
  let editingRemoteNodeId = null;

  function updateConfigurationRuntimeFields() {
    document.querySelectorAll("[data-runtime]").forEach((fieldset) => {
      fieldset.hidden = fieldset.dataset.runtime !== configurationRuntime.value;
    });
  }

  function updateConfigurationCapabilities() {
    const disabled = configurationCapabilitiesAbsent.checked;
    document.querySelectorAll("#configuration-capabilities input").forEach((input) => {
      input.disabled = disabled;
    });
  }

  function setConfigurationLocal(local) {
    document.querySelector("#configuration-absence").textContent = local === null
      ? "No retained local configuration exists. Enter one complete configuration to retain it."
      : "Editing retained local configuration for future HAC launches.";
    if (local === null) return;
    configurationRuntime.value = local.runtime;
    document.querySelector("#configuration-ollama-model").value = local.ollama_model || "";
    document.querySelector("#configuration-ollama-disable-thinking").checked = local.ollama_disable_thinking;
    document.querySelector("#configuration-llama-server-base-url").value = local.llama_server_base_url || "";
    document.querySelector("#configuration-llama-server-model").value = local.llama_server_model || "";
    document.querySelector("#configuration-vllm-base-url").value = local.vllm_base_url || "";
    document.querySelector("#configuration-vllm-model").value = local.vllm_model || "";
    configurationCapabilitiesAbsent.checked = local.local_capabilities === null;
    document.querySelectorAll("#configuration-capabilities input").forEach((input) => {
      input.checked = local.local_capabilities !== null && local.local_capabilities.includes(input.value);
    });
    document.querySelector("#configuration-execution-limit").value = local.execution_limit === null ? "" : String(local.execution_limit);
    updateConfigurationRuntimeFields();
    updateConfigurationCapabilities();
  }

  function resetRemoteNodeForm() {
    editingRemoteNodeId = null;
    remoteNodeForm.reset();
    remoteNodeId.readOnly = false;
    remoteNodeId.value = "";
    document.querySelector("#remote-node-form-heading").textContent = "Add remote node";
    remoteNodeCancel.hidden = true;
    document.querySelectorAll("#remote-node-capabilities input").forEach((input) => {
      input.checked = input.value === "chat" || input.value === "summarize";
    });
  }

  function setRemoteNodes(nodes) {
    remoteNodesList.replaceChildren();
    if (nodes.length === 0) {
      const absent = document.createElement("p");
      absent.textContent = "No retained remote nodes.";
      remoteNodesList.append(absent);
      return;
    }
    nodes.forEach((node) => {
      const entry = document.createElement("article");
      entry.className = "remote-node";
      const name = document.createElement("h4");
      name.textContent = node.node_id;
      const baseUrl = document.createElement("p");
      baseUrl.textContent = `Configured base URL: ${node.base_url}`;
      const capabilities = document.createElement("p");
      capabilities.textContent = `Caller-declared allowed capabilities: ${node.capabilities.join(", ")}`;
      const actions = document.createElement("div");
      actions.className = "remote-node-actions";
      const edit = document.createElement("button");
      edit.type = "button";
      edit.textContent = "Edit";
      edit.addEventListener("click", () => {
        editingRemoteNodeId = node.node_id;
        remoteNodeId.value = node.node_id;
        remoteNodeId.readOnly = true;
        remoteNodeBaseUrl.value = node.base_url;
        document.querySelectorAll("#remote-node-capabilities input").forEach((input) => {
          input.checked = node.capabilities.includes(input.value);
        });
        document.querySelector("#remote-node-form-heading").textContent = "Edit remote node";
        remoteNodeCancel.hidden = false;
      });
      const remove = document.createElement("button");
      remove.type = "button";
      remove.textContent = "Remove";
      remove.addEventListener("click", () => removeRemoteNode(node.node_id));
      actions.append(edit, remove);
      entry.append(name, baseUrl, capabilities, actions);
      remoteNodesList.append(entry);
    });
  }

  async function loadRemoteNodes() {
    const response = await fetch("/retained-remote-nodes");
    if (!response.ok) throw new Error("request failed");
    const body = await response.json();
    if (!Array.isArray(body.remote_nodes)) throw new Error("request failed");
    setRemoteNodes(body.remote_nodes);
  }

  async function loadConfiguration() {
    if (configurationLoaded) return;
    const context = requestContexts.configuration;
    setRequestActive(context, true, "Loading retained configuration…");
    clearError(context);
    try {
      const [localResponse] = await Promise.all([
        fetch("/retained-local-configuration"),
        loadRemoteNodes(),
      ]);
      if (!localResponse.ok) return showError(context, await safeFailure(localResponse));
      const responseBody = await localResponse.json();
      if (!Object.hasOwn(responseBody, "local")) return showError(context, "Request failed");
      setConfigurationLocal(responseBody.local);
      configurationLoaded = true;
    } catch (_) {
      showError(context, "Request failed");
    } finally {
      setRequestActive(context, false);
    }
  }

  configurationRuntime.addEventListener("change", updateConfigurationRuntimeFields);
  configurationCapabilitiesAbsent.addEventListener("change", updateConfigurationCapabilities);
  remoteNodeCancel.addEventListener("click", resetRemoteNodeForm);
  updateConfigurationRuntimeFields();
  updateConfigurationCapabilities();
  resetRemoteNodeForm();

  document.querySelector("#configuration-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const context = requestContexts.configuration;
    if (context.active) return;
    const limit = document.querySelector("#configuration-execution-limit").value;
    const local = {
      runtime: configurationRuntime.value,
      ollama_model: document.querySelector("#configuration-ollama-model").value || null,
      ollama_disable_thinking: document.querySelector("#configuration-ollama-disable-thinking").checked,
      llama_server_base_url: document.querySelector("#configuration-llama-server-base-url").value || null,
      llama_server_model: document.querySelector("#configuration-llama-server-model").value || null,
      vllm_base_url: document.querySelector("#configuration-vllm-base-url").value || null,
      vllm_model: document.querySelector("#configuration-vllm-model").value || null,
      local_capabilities: configurationCapabilitiesAbsent.checked ? null : Array.from(document.querySelectorAll("#configuration-capabilities input:checked"), (input) => input.value),
      execution_limit: limit === "" ? null : Number(limit),
    };
    setRequestActive(context, true, "Saving retained configuration…");
    clearError(context);
    let saved = false;
    try {
      const response = await fetch("/retained-local-configuration", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(local),
      });
      if (!response.ok) return showError(context, await safeFailure(response));
      const responseBody = await response.json();
      setConfigurationLocal(responseBody.local);
      configurationLoaded = true;
      saved = true;
    } catch (_) {
      showError(context, "Request failed");
    } finally {
      setRequestActive(context, false);
    }
    if (saved) context.status.textContent = "Retained configuration saved for future HAC launches.";
  });

  remoteNodeForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const context = requestContexts.remoteNodes;
    if (context.active) return;
    const nodeId = editingRemoteNodeId || remoteNodeId.value;
    const body = {
      base_url: remoteNodeBaseUrl.value,
      capabilities: Array.from(document.querySelectorAll("#remote-node-capabilities input:checked"), (input) => input.value),
    };
    setRequestActive(context, true, "Saving retained remote node…");
    clearError(context);
    let saved = false;
    try {
      const response = await fetch(`/retained-remote-nodes/${encodeURIComponent(nodeId)}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!response.ok) return showError(context, await safeFailure(response));
      await loadRemoteNodes();
      resetRemoteNodeForm();
      saved = true;
    } catch (_) {
      showError(context, "Request failed");
    } finally {
      setRequestActive(context, false);
    }
    if (saved) context.status.textContent = "Retained remote node saved for future HAC launches.";
  });

  async function removeRemoteNode(nodeId) {
    if (!window.confirm(`Remove retained remote node "${nodeId}"?\n\nThis affects future HAC launches. The currently running process is not reconfigured.`)) return;
    const context = requestContexts.remoteNodes;
    if (context.active) return;
    setRequestActive(context, true, "Removing retained remote node…");
    clearError(context);
    let removed = false;
    try {
      const response = await fetch(`/retained-remote-nodes/${encodeURIComponent(nodeId)}`, {
        method: "DELETE",
      });
      if (!response.ok) return showError(context, await safeFailure(response));
      await loadRemoteNodes();
      if (editingRemoteNodeId === nodeId) resetRemoteNodeForm();
      removed = true;
    } catch (_) {
      showError(context, "Request failed");
    } finally {
      setRequestActive(context, false);
    }
    if (removed) context.status.textContent = "Retained remote node removed for future HAC launches.";
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
    const context = requestContexts.chat;
    if (context.active) return;
    const input = document.querySelector("#chat-message");
    if (!input.value.trim()) return showError(context, "Message is required");
    const pendingMessage = { role: "user", content: input.value };
    messages.push(pendingMessage);
    renderChat();
    input.value = "";
    const request = post(
      context,
      "/v1/chat",
      { capability: "chat", messages },
      "Generating response…",
    );
    context.status.scrollIntoView({ block: "nearest" });
    const result = await request;
    if (result && typeof result.content === "string" && typeof result.node_id === "string") {
      const assistantMessage = { role: "assistant", content: result.content };
      assistantAttribution.set(assistantMessage, result.node_id);
      messages.push(assistantMessage);
      renderChat();
    } else {
      rollbackPendingMessage(pendingMessage);
      if (input.value === "") input.value = pendingMessage.content;
      if (result) showError(context, "Request failed");
    }
  });

  document.querySelector("#code-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const context = requestContexts.code;
    if (context.active) return;
    const input = document.querySelector("#code-text");
    const pendingMessage = { role: "user", content: input.value };
    const candidateMessages = [...codeMessages, pendingMessage];
    const candidateBytes = candidateMessages.reduce(
      (total, message) => total + new TextEncoder().encode(message.content).length,
      0,
    );
    if (!input.value.trim() || candidateBytes > byteLimit) {
      return showError(context, "Code conversation must be non-blank and within the accepted limit");
    }
    codeMessages.push(pendingMessage);
    renderCode();
    input.value = "";
    const request = post(
      context,
      "/v1/chat",
      { capability: "code", messages: codeMessages },
      "Generating code…",
    );
    context.status.scrollIntoView({ block: "nearest" });
    const result = await request;
    if (result && typeof result.content === "string" && typeof result.node_id === "string") {
      const assistantMessage = { role: "assistant", content: result.content };
      assistantAttribution.set(assistantMessage, result.node_id);
      codeMessages.push(assistantMessage);
      renderCode();
    } else {
      rollbackPendingCodeMessage(pendingMessage);
      if (input.value === "") input.value = pendingMessage.content;
      if (result) showError(context, "Request failed");
    }
  });

  document.querySelector("#summarize-file").addEventListener("change", async (event) => {
    const [file] = event.target.files;
    if (!file) return;
    try {
      const text = new TextDecoder("utf-8", { fatal: true }).decode(await file.arrayBuffer());
      document.querySelector("#summarize-text").value = text;
    } catch (_) {
      showError(requestContexts.summarize, "Selected file is not valid UTF-8 text");
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
    clearError(requestContexts.summarize);
    if (file.size > pdfByteLimit) {
      return showError(requestContexts.summarize, "Selected PDF must be at most 8 MiB");
    }
    try {
      const text = await readPdfText(file);
      if (!text.trim()) return showError(requestContexts.summarize, "Selected PDF contains no extractable text");
      const input = document.querySelector("#summarize-text");
      input.value = text;
      if (new TextEncoder().encode(text).length > byteLimit) {
        showError(requestContexts.summarize, "Text must be non-blank and within the accepted limit");
      }
    } catch (failure) {
      if (failure === "password-protected") {
        showError(requestContexts.summarize, "Selected PDF is password-protected");
      } else {
        showError(requestContexts.summarize, "Selected PDF could not be read");
      }
    }
  });

  document.querySelector("#summarize-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const context = requestContexts.summarize;
    if (context.active) return;
    const text = document.querySelector("#summarize-text").value;
    if (!text.trim() || new TextEncoder().encode(text).length > byteLimit) {
      return showError(context, "Text must be non-blank and within the accepted limit");
    }
    const result = await post(context, "/v1/summarize", { text }, "Summarizing…");
    if (result && typeof result.content === "string" && typeof result.node_id === "string") {
      renderResult(document.querySelector("#summarize-result"), result.content, result.node_id);
    } else if (result) showError(context, "Request failed");
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
      showError(requestContexts.classify, "Selected file is not valid UTF-8 text");
    }
  });

  document.querySelector("#classify-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const context = requestContexts.classify;
    if (context.active) return;
    const text = document.querySelector("#classify-text").value;
    const labels = Array.from(document.querySelectorAll(".classify-label"), (input) => input.value);
    if (!text.trim() || new TextEncoder().encode(text).length > byteLimit || labels.length < 2) {
      return showError(context, "Text and at least two labels are required");
    }
    const result = await post(context, "/v1/classify", { text, labels }, "Classifying…");
    if (result && typeof result.selected_label === "string" && typeof result.node_id === "string") {
      renderResult(document.querySelector("#classify-result"), result.selected_label, result.node_id);
    } else if (result) showError(context, "Request failed");
  });

  const tabs = Array.from(document.querySelectorAll('[role="tab"]'));

  function activateTab(tab, focus = false) {
    tabs.forEach((other) => {
      const selected = other === tab;
      other.setAttribute("aria-selected", String(selected));
      other.tabIndex = selected ? 0 : -1;
      document.querySelector(`#${other.getAttribute("aria-controls")}`).hidden = !selected;
    });
    if (tab.id === "configuration-tab") loadConfiguration();
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
