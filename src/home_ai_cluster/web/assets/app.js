(() => {
  const byteLimit = 65536;
  const pdfByteLimit = 8388608;
  // PDF.js 6.2.108: matched vendored main/worker assets.
  const pdfjsMainUrl = "/assets/pdfjs-6.2.108/pdf.min.mjs";
  const pdfjsWorkerUrl = "/assets/pdfjs-6.2.108/pdf.worker.min.mjs";
  const messages = [];
  const codeMessages = [];
  const assistantAttribution = new WeakMap();
  const assistantSources = new WeakMap();
  const themeKey = "home-ai-cluster.theme";
  const themeSelect = document.querySelector("#theme-select");
  const root = document.documentElement;
  const requestContexts = {
    chat: createRequestContext("#chat-form", "#chat-error", "#chat-status"),
    externalInformation: createRequestContext("#external-information-form", "#external-information-error", "#external-information-status"),
    summarize: createRequestContext("#summarize-form", "#summarize-error", "#summarize-status"),
    classify: createRequestContext("#classify-form", "#classify-error", "#classify-status"),
    code: createRequestContext("#code-form", "#code-error", "#code-status"),
    imageGeneration: createRequestContext("#image-generation-form", "#image-generation-error", "#image-generation-status"),
    configuration: createRequestContext("#configuration-form", "#configuration-error", "#configuration-status"),
    imageGenerationConfiguration: createRequestContext("#image-generation-configuration-form", "#image-generation-configuration-error", "#image-generation-configuration-status"),
    remoteNodes: createRequestContext("#remote-node-form", "#remote-node-error", "#remote-node-status"),
    externalInformationConfiguration: createRequestContext("#external-information-configuration-form", "#external-information-configuration-error", "#external-information-configuration-status"),
    chatExternalInformationConfiguration: createRequestContext("#chat-external-information-configuration-form", "#chat-external-information-configuration-error", "#chat-external-information-configuration-status"),
  };
  const capabilityRequestContexts = [
    requestContexts.chat,
    requestContexts.externalInformation,
    requestContexts.summarize,
    requestContexts.classify,
    requestContexts.code,
    requestContexts.imageGeneration,
  ];
  let capabilityRequestActive = false;

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
  document.querySelector("#chat-external-information").checked = false;
  let retainedPluginPresentationGeneration = 0;

  function setChatExternalInformationPluginState(plugin, resetAuthorization = false) {
    const checkbox = document.querySelector("#chat-external-information");
    const state = document.querySelector("#chat-external-information-plugin-state");
    if (typeof plugin === "string" && plugin.trim()) {
      checkbox.disabled = false;
      if (resetAuthorization) checkbox.checked = false;
      state.textContent = `Retained External Information plugin: ${plugin}`;
      return;
    }
    checkbox.checked = false;
    checkbox.disabled = true;
    state.textContent = plugin === null
      ? "No External Information plugin configured."
      : "External Information plugin configuration unavailable.";
  }

  function publishPassiveChatExternalInformationPluginState(plugin, generation) {
    if (generation !== retainedPluginPresentationGeneration) return;
    setChatExternalInformationPluginState(plugin);
  }

  async function loadChatExternalInformationPluginState() {
    const generation = retainedPluginPresentationGeneration;
    try {
      const response = await fetch("/retained-external-information-configuration");
      if (!response.ok) return publishPassiveChatExternalInformationPluginState(undefined, generation);
      const body = await response.json();
      if (!Object.hasOwn(body, "plugin")) return publishPassiveChatExternalInformationPluginState(undefined, generation);
      publishPassiveChatExternalInformationPluginState(body.plugin, generation);
    } catch (_) {
      publishPassiveChatExternalInformationPluginState(undefined, generation);
    }
  }

  void loadChatExternalInformationPluginState();

  function setRequestActive(context, active, message = "") {
    context.active = active;
    context.status.dataset.active = String(active);
    context.status.textContent = active ? message : "";
    if (capabilityRequestContexts.includes(context)) {
      capabilityRequestActive = active;
      capabilityRequestContexts.forEach((capabilityContext) => {
        capabilityContext.submit.disabled = active;
      });
    } else {
      context.submit.disabled = active;
    }
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
    if (capabilityRequestActive || context.active) return null;
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
  const imageGenerationConfigurationForm = document.querySelector("#image-generation-configuration-form");
  const imageGenerationConfigurationBaseUrl = document.querySelector("#image-generation-configuration-base-url");
  const externalInformationConfigurationForm = document.querySelector("#external-information-configuration-form");
  const externalInformationConfigurationPlugin = document.querySelector("#external-information-configuration-plugin");
  const chatExternalInformationConfigurationForm = document.querySelector("#chat-external-information-configuration-form");
  const chatExternalInformationConfigurationAuthorized = document.querySelector("#chat-external-information-configuration-authorized");
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

  function clearConfigurationLocalForm() {
    document.querySelector("#configuration-form").reset();
    configurationRuntime.value = "";
    document.querySelector("#configuration-ollama-model").value = "";
    document.querySelector("#configuration-ollama-disable-thinking").checked = false;
    document.querySelector("#configuration-llama-server-base-url").value = "";
    document.querySelector("#configuration-llama-server-model").value = "";
    document.querySelector("#configuration-vllm-base-url").value = "";
    document.querySelector("#configuration-vllm-model").value = "";
    document.querySelector("#configuration-temperature").value = "";
    configurationCapabilitiesAbsent.checked = true;
    document.querySelectorAll("#configuration-capabilities input").forEach((input) => {
      input.checked = false;
    });
    document.querySelector("#configuration-execution-limit").value = "";
    updateConfigurationRuntimeFields();
    updateConfigurationCapabilities();
  }

  function setConfigurationLocal(local) {
    document.querySelector("#configuration-absence").textContent = local === null
      ? "No retained local configuration exists. Enter one complete configuration to retain it."
      : "Editing retained local configuration for future HAC launches.";
    if (local === null) {
      clearConfigurationLocalForm();
      return;
    }
    configurationRuntime.value = local.runtime;
    document.querySelector("#configuration-ollama-model").value = local.ollama_model || "";
    document.querySelector("#configuration-ollama-disable-thinking").checked = local.ollama_disable_thinking;
    document.querySelector("#configuration-llama-server-base-url").value = local.llama_server_base_url || "";
    document.querySelector("#configuration-llama-server-model").value = local.llama_server_model || "";
    document.querySelector("#configuration-vllm-base-url").value = local.vllm_base_url || "";
    document.querySelector("#configuration-vllm-model").value = local.vllm_model || "";
    document.querySelector("#configuration-temperature").value = local.temperature === null ? "" : String(local.temperature);
    configurationCapabilitiesAbsent.checked = local.local_capabilities === null;
    document.querySelectorAll("#configuration-capabilities input").forEach((input) => {
      input.checked = local.local_capabilities !== null && local.local_capabilities.includes(input.value);
    });
    document.querySelector("#configuration-execution-limit").value = local.execution_limit === null ? "" : String(local.execution_limit);
    updateConfigurationRuntimeFields();
    updateConfigurationCapabilities();
  }

  function setImageGenerationConfiguration(imageGeneration) {
    document.querySelector("#image-generation-configuration-absence").textContent = imageGeneration === null
      ? "No retained Image Generation configuration exists."
      : "Editing retained stable-diffusion.cpp configuration for future HAC launches.";
    imageGenerationConfigurationBaseUrl.value = imageGeneration === null ? "" : imageGeneration.base_url;
  }

  function setExternalInformationConfiguration(plugin, resetAuthorization = false) {
    document.querySelector("#external-information-configuration-absence").textContent = plugin === null
      ? "No retained external-information plugin choice exists."
      : "Editing retained external-information plugin choice for accepted external-information flows.";
    externalInformationConfigurationPlugin.value = plugin || "";
    setChatExternalInformationPluginState(plugin, resetAuthorization);
  }

  function setChatExternalInformationConfiguration(authorized) {
    chatExternalInformationConfigurationAuthorized.checked = authorized;
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
    const retainedPluginGeneration = retainedPluginPresentationGeneration;
    setRequestActive(context, true, "Loading retained configuration…");
    clearError(context);
    try {
      const [localResponse, imageGenerationResponse, externalInformationResponse, chatExternalInformationResponse] = await Promise.all([
        fetch("/retained-local-configuration"),
        fetch("/retained-image-generation-configuration"),
        fetch("/retained-external-information-configuration"),
        fetch("/retained-chat-external-information-configuration"),
        loadRemoteNodes(),
      ]);
      if (!localResponse.ok) return showError(context, await safeFailure(localResponse));
      if (!imageGenerationResponse.ok) return showError(context, await safeFailure(imageGenerationResponse));
      if (!externalInformationResponse.ok) {
        publishPassiveChatExternalInformationPluginState(undefined, retainedPluginGeneration);
        return showError(context, await safeFailure(externalInformationResponse));
      }
      if (!chatExternalInformationResponse.ok) return showError(context, await safeFailure(chatExternalInformationResponse));
      const responseBody = await localResponse.json();
      if (!Object.hasOwn(responseBody, "local")) return showError(context, "Request failed");
      const imageGenerationBody = await imageGenerationResponse.json();
      let externalInformationBody;
      try {
        externalInformationBody = await externalInformationResponse.json();
      } catch (_) {
        publishPassiveChatExternalInformationPluginState(undefined, retainedPluginGeneration);
        return showError(context, "Request failed");
      }
      const chatExternalInformationBody = await chatExternalInformationResponse.json();
      if (!Object.hasOwn(imageGenerationBody, "image_generation") || typeof chatExternalInformationBody.authorized !== "boolean") return showError(context, "Request failed");
      setConfigurationLocal(responseBody.local);
      setImageGenerationConfiguration(imageGenerationBody.image_generation);
      if (!externalInformationBody || !Object.hasOwn(externalInformationBody, "plugin")) {
        publishPassiveChatExternalInformationPluginState(undefined, retainedPluginGeneration);
        return showError(context, "Request failed");
      }
      if (retainedPluginGeneration === retainedPluginPresentationGeneration) {
        setExternalInformationConfiguration(externalInformationBody.plugin);
      }
      setChatExternalInformationConfiguration(chatExternalInformationBody.authorized);
      configurationLoaded = true;
    } catch (_) {
      showError(context, "Request failed");
    } finally {
      setRequestActive(context, false);
    }
  }

  configurationRuntime.addEventListener("change", () => {
    document.querySelector("#configuration-temperature").value = "";
    updateConfigurationRuntimeFields();
  });
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
      temperature: document.querySelector("#configuration-temperature").value === "" ? null : Number(document.querySelector("#configuration-temperature").value),
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

  document.querySelector("#configuration-local-reset").addEventListener("click", async () => {
    const context = requestContexts.configuration;
    if (context.active) return;
    setRequestActive(context, true, "Removing retained local configuration…");
    clearError(context);
    try {
      const response = await fetch("/retained-local-configuration", { method: "DELETE" });
      if (!response.ok) return showError(context, await safeFailure(response));
      setConfigurationLocal(null);
      context.status.textContent = "Retained local configuration removed for future HAC launches.";
    } catch (_) {
      showError(context, "Request failed");
    } finally {
      setRequestActive(context, false);
    }
  });

  imageGenerationConfigurationForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const context = requestContexts.imageGenerationConfiguration;
    if (context.active) return;
    setRequestActive(context, true, "Saving Image Generation configuration…");
    clearError(context);
    try {
      const response = await fetch("/retained-image-generation-configuration", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ base_url: imageGenerationConfigurationBaseUrl.value }),
      });
      if (!response.ok) return showError(context, await safeFailure(response));
      const body = await response.json();
      setImageGenerationConfiguration(body.image_generation);
      context.status.textContent = "Image Generation configuration saved for future HAC launches.";
    } catch (_) {
      showError(context, "Request failed");
    } finally {
      setRequestActive(context, false);
    }
  });

  document.querySelector("#image-generation-configuration-clear").addEventListener("click", async () => {
    const context = requestContexts.imageGenerationConfiguration;
    if (context.active) return;
    setRequestActive(context, true, "Clearing Image Generation configuration…");
    clearError(context);
    try {
      const response = await fetch("/retained-image-generation-configuration", { method: "DELETE" });
      if (!response.ok) return showError(context, await safeFailure(response));
      setImageGenerationConfiguration(null);
      context.status.textContent = "Image Generation configuration cleared for future HAC launches.";
    } catch (_) {
      showError(context, "Request failed");
    } finally {
      setRequestActive(context, false);
    }
  });

  externalInformationConfigurationForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const context = requestContexts.externalInformationConfiguration;
    if (context.active) return;
    setRequestActive(context, true, "Saving plugin choice…");
    clearError(context);
    try {
      const response = await fetch("/retained-external-information-configuration", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ plugin: externalInformationConfigurationPlugin.value }),
      });
      if (!response.ok) return showError(context, await safeFailure(response));
      const body = await response.json();
      retainedPluginPresentationGeneration += 1;
      setExternalInformationConfiguration(body.plugin, true);
      context.status.textContent = "Plugin choice saved as retained external-information configuration.";
    } catch (_) {
      showError(context, "Request failed");
    } finally {
      setRequestActive(context, false);
    }
  });

  document.querySelector("#external-information-configuration-clear").addEventListener("click", async () => {
    const context = requestContexts.externalInformationConfiguration;
    if (context.active) return;
    setRequestActive(context, true, "Clearing plugin choice…");
    clearError(context);
    try {
      const response = await fetch("/retained-external-information-configuration", { method: "DELETE" });
      if (!response.ok) return showError(context, await safeFailure(response));
      retainedPluginPresentationGeneration += 1;
      setExternalInformationConfiguration(null, true);
      context.status.textContent = "Plugin choice cleared from retained external-information configuration.";
    } catch (_) {
      showError(context, "Request failed");
    } finally {
      setRequestActive(context, false);
    }
  });

  chatExternalInformationConfigurationForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const context = requestContexts.chatExternalInformationConfiguration;
    if (context.active) return;
    setRequestActive(context, true, "Saving Chat authorization…");
    clearError(context);
    try {
      const response = await fetch("/retained-chat-external-information-configuration", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ authorized: chatExternalInformationConfigurationAuthorized.checked }),
      });
      if (!response.ok) return showError(context, await safeFailure(response));
      const body = await response.json();
      setChatExternalInformationConfiguration(body.authorized);
      context.status.textContent = "Chat authorization saved for future eligible native one-shot Chat.";
    } catch (_) {
      showError(context, "Request failed");
    } finally {
      setRequestActive(context, false);
    }
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
    const status = document.querySelector("#chat-status");
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
      const sources = assistantSources.get(message);
      if (sources) {
        const heading = document.createElement("div");
        heading.className = "attribution";
        heading.textContent = "Supplied sources";
        entry.append(heading);
        sources.forEach((source) => {
          const item = document.createElement("div");
          item.className = "attribution";
          item.textContent = `${source.title}\nURL provenance: ${source.url}\n${source.content}`;
          entry.append(item);
        });
      }
      container.append(entry);
    });
    container.append(status);
    container.scrollTop = container.scrollHeight;
  }

  function rollbackPendingMessage(pendingMessage) {
    const pendingIndex = messages.indexOf(pendingMessage);
    if (pendingIndex !== -1) messages.splice(pendingIndex, 1);
    renderChat();
  }

  function renderCode() {
    const container = document.querySelector("#code-conversation");
    const status = document.querySelector("#code-status");
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
    container.append(status);
    container.scrollTop = container.scrollHeight;
  }

  function rollbackPendingCodeMessage(pendingMessage) {
    const pendingIndex = codeMessages.indexOf(pendingMessage);
    if (pendingIndex !== -1) codeMessages.splice(pendingIndex, 1);
    renderCode();
  }

  function renderWorkspaceActivity(activity) {
    const container = document.querySelector("#workspace-activity");
    container.replaceChildren();
    if (!Array.isArray(activity)) return;
    activity.forEach((entry) => {
      if (!entry || typeof entry.operation !== "string" || typeof entry.path !== "string" || typeof entry.outcome !== "string") return;
      const line = document.createElement("p");
      line.textContent = `${entry.operation} ${entry.path}: ${entry.outcome}`;
      container.append(line);
    });
  }

  const workspaceEnabled = document.querySelector("#workspace-enabled");
  const workspaceOptions = document.querySelector("#workspace-options");
  const workspaceRoot = document.querySelector("#workspace-root");
  let fixedWorkspace = null;
  workspaceEnabled.addEventListener("change", () => {
    workspaceOptions.hidden = !workspaceEnabled.checked;
    if (fixedWorkspace) {
      workspaceRoot.value = fixedWorkspace.root;
      workspaceRoot.readOnly = true;
      document.querySelectorAll("#workspace-grants input").forEach((input) => {
        input.checked = fixedWorkspace.grants.includes(input.value);
        input.disabled = true;
      });
    }
  });

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

  function renderExternalInformationSources(sources) {
    const container = document.querySelector("#external-information-sources");
    container.replaceChildren();
    sources.forEach((source) => {
      const item = document.createElement("article");
      const title = document.createElement("h4");
      const url = document.createElement("p");
      const content = document.createElement("p");
      title.textContent = source.title;
      url.textContent = `URL provenance: ${source.url}`;
      content.textContent = source.content;
      item.append(title, url, content);
      container.append(item);
    });
  }

  let currentImageUrl = null;

  async function postImageGeneration(context, body) {
    if (capabilityRequestActive || context.active) return;
    setRequestActive(context, true, "Generating image…");
    clearError(context);
    try {
      const response = await fetch("/v1/image-generation", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!response.ok) {
        showError(context, await safeFailure(response));
        return;
      }
      const imageUrl = URL.createObjectURL(await response.blob());
      if (currentImageUrl) URL.revokeObjectURL(currentImageUrl);
      currentImageUrl = imageUrl;
      document.querySelector("#generated-image").src = currentImageUrl;
      document.querySelector("#image-generation-result-region").hidden = false;
    } catch (_) {
      showError(context, "Request failed");
    } finally {
      setRequestActive(context, false);
    }
  }

  document.querySelector("#image-generation-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const context = requestContexts.imageGeneration;
    if (capabilityRequestActive) return;
    const instruction = document.querySelector("#image-generation-instruction").value;
    if (!instruction.trim()) return showError(context, "Instruction is required");
    const width = document.querySelector("#image-generation-width").value;
    const height = document.querySelector("#image-generation-height").value;
    if ((width === "") !== (height === "")) {
      return showError(context, "Width and height are required together");
    }
    const body = { instruction };
    if (width !== "") {
      if (!/^\d+$/.test(width) || !/^\d+$/.test(height)) {
        return showError(context, "Width and height must be whole pixels");
      }
      const numericWidth = Number(width);
      const numericHeight = Number(height);
      if (numericWidth < 64 || numericWidth > 2048 || numericHeight < 64 || numericHeight > 2048) {
        return showError(context, "Width and height must be between 64 and 2048");
      }
      body.width = numericWidth;
      body.height = numericHeight;
    }
    await postImageGeneration(context, body);
  });

  document.querySelector("#external-information-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const context = requestContexts.externalInformation;
    const result = await post(context, "/external-information", {
      plugin: document.querySelector("#external-information-plugin").value,
      query: document.querySelector("#external-information-query").value,
      question: document.querySelector("#external-information-question").value,
    }, "Acquiring supplied sources…");
    if (!result || typeof result.content !== "string" || !Array.isArray(result.sources)) return;
    const region = document.querySelector("#external-information-result-region");
    region.hidden = false;
    renderResult(document.querySelector("#external-information-result"), result.content, result.node_id);
    renderExternalInformationSources(result.sources);
  });

  document.querySelector("#chat-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const context = requestContexts.chat;
    if (capabilityRequestActive) return;
    const input = document.querySelector("#chat-message");
    if (!input.value.trim()) return showError(context, "Message is required");
    const pendingMessage = { role: "user", content: input.value };
    messages.push(pendingMessage);
    renderChat();
    input.value = "";
    const automaticExternalInformation = document.querySelector("#chat-external-information").checked;
    const request = automaticExternalInformation
      ? post(context, "/chat-external-information", { messages }, "Generating response…")
      : post(context, "/v1/chat", { capability: "chat", messages }, "Generating response…");
    context.status.scrollIntoView({ block: "nearest" });
    const result = await request;
    const chatResult = automaticExternalInformation && result ? result.result : result;
    if (chatResult && typeof chatResult.content === "string" && typeof chatResult.node_id === "string") {
      const assistantMessage = { role: "assistant", content: chatResult.content };
      assistantAttribution.set(assistantMessage, chatResult.node_id);
      if (automaticExternalInformation && result.branch === "source-grounded" && Array.isArray(chatResult.sources)) {
        assistantSources.set(assistantMessage, chatResult.sources);
      }
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
    if (capabilityRequestActive) return;
    renderWorkspaceActivity(null);
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
    const grants = [...document.querySelectorAll("#workspace-grants input:checked")].map((input) => input.value);
    if (workspaceEnabled.checked && (!workspaceRoot.value || grants.length === 0)) {
      return showError(context, "Workspace access requires an explicit root and grant");
    }
    if (fixedWorkspace && workspaceEnabled.checked && (workspaceRoot.value !== fixedWorkspace.root || grants.join(",") !== fixedWorkspace.grants.join(","))) {
      return showError(context, "Reload the page before changing workspace access");
    }
    codeMessages.push(pendingMessage);
    renderCode();
    input.value = "";
    const request = workspaceEnabled.checked
      ? post(context, "/workspace-code", { root: workspaceRoot.value, grants, history: codeMessages.slice(0, -1), instruction: pendingMessage.content }, "Generating code…")
      : post(context, "/v1/chat", { capability: "code", messages: codeMessages }, "Generating code…");
    context.status.scrollIntoView({ block: "nearest" });
    const result = await request;
    if (workspaceEnabled.checked && result) renderWorkspaceActivity(result.activity);
    if (result && typeof result.content === "string" && typeof result.node_id === "string") {
      const assistantMessage = { role: "assistant", content: result.content };
      assistantAttribution.set(assistantMessage, result.node_id);
      codeMessages.push(assistantMessage);
      if (workspaceEnabled.checked && !fixedWorkspace) {
        fixedWorkspace = { root: workspaceRoot.value, grants };
        workspaceRoot.readOnly = true;
        document.querySelectorAll("#workspace-grants input").forEach((input) => { input.disabled = true; });
      }
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
    if (capabilityRequestActive) return;
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
    if (capabilityRequestActive) return;
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
