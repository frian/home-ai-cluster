const conversations = { chat: [], code: [] };
let capabilityRequestActive = false;
let currentImageUrl = null;
const tabs = Array.from(document.querySelectorAll('[role="tab"]'));
const themeKey = "home-ai-cluster.theme";
const themeSelect = document.querySelector("#theme-select");
const root = document.documentElement;

function useSystemTheme() { root.removeAttribute("data-theme"); themeSelect.value = "system"; }
function initializeThemePreference() {
  let theme;
  try { theme = localStorage.getItem(themeKey); } catch (_) { useSystemTheme(); return; }
  if (theme === "light" || theme === "dark") { root.setAttribute("data-theme", theme); themeSelect.value = theme; return; }
  useSystemTheme();
  if (theme !== null) { try { localStorage.removeItem(themeKey); } catch (_) { /* System remains safe. */ } }
}
themeSelect.addEventListener("change", () => {
  const theme = themeSelect.value;
  if (theme === "light" || theme === "dark") {
    try { localStorage.setItem(themeKey, theme); } catch (_) { useSystemTheme(); return; }
    root.setAttribute("data-theme", theme); return;
  }
  try { localStorage.removeItem(themeKey); } catch (_) { useSystemTheme(); return; }
  useSystemTheme();
});
initializeThemePreference();

function selectTab(tab, focus = false) {
  tabs.forEach((candidate) => {
    const selected = candidate === tab;
    candidate.setAttribute("aria-selected", String(selected));
    candidate.tabIndex = selected ? 0 : -1;
    document.querySelector(`#${candidate.getAttribute("aria-controls")}`).hidden = !selected;
  });
  if (focus) tab.focus();
}
tabs.forEach((tab, index) => {
  tab.addEventListener("click", () => selectTab(tab));
  tab.addEventListener("keydown", (event) => {
    let next = null;
    if (event.key === "ArrowRight") next = tabs[(index + 1) % tabs.length];
    if (event.key === "ArrowLeft") next = tabs[(index - 1 + tabs.length) % tabs.length];
    if (event.key === "Home") next = tabs[0];
    if (event.key === "End") next = tabs[tabs.length - 1];
    if (next) { event.preventDefault(); selectTab(next, true); }
  });
});

function addLabel(value = "") {
  const row = document.createElement("div"); row.className = "label-row";
  const input = document.createElement("input"); input.className = "classify-label"; input.required = true; input.value = value;
  const remove = document.createElement("button"); remove.type = "button"; remove.textContent = "Remove label";
  remove.addEventListener("click", () => row.remove()); row.append(input, remove);
  document.querySelector("#label-inputs").append(row);
}
document.querySelector("#add-label").addEventListener("click", () => addLabel());
document.querySelectorAll("#label-inputs button").forEach((button) => button.addEventListener("click", () => button.parentElement.remove()));

function contextFor(form) {
  const key = form.dataset.capability || form.dataset.path.slice(4).replaceAll("/", "-");
  return { error: document.querySelector(`#${key}-error`), status: document.querySelector(`#${key}-status`), result: document.querySelector(`#${key}-result-region`) };
}
function setActive(context, active, message = "") {
  if (active) capabilityRequestActive = true;
  else capabilityRequestActive = false;
  document.querySelectorAll("[data-submit]").forEach((button) => { button.disabled = active; });
  context.status.dataset.active = String(active);
  context.status.textContent = message;
}
function showError(context, message) { context.error.textContent = message; }
async function submit(path, body) {
  const response = await fetch(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  if (!response.ok) { const detail = await response.json().catch(() => ({})); throw new Error(typeof detail.detail === "string" ? detail.detail : "Request failed"); }
  return response;
}
function renderConversation(capability) {
  const container = document.querySelector(`#${capability}-conversation`); container.replaceChildren();
  document.querySelector(`#${capability}-result-region`).hidden = conversations[capability].length === 0;
  conversations[capability].forEach((message) => {
    const card = document.createElement("article"); card.className = `message message-${message.role}`;
    const role = document.createElement("span"); role.className = "message-role"; role.textContent = message.role === "user" ? "You" : "Home AI Cluster";
    const content = document.createElement("div"); content.textContent = message.content; card.append(role, content); container.append(card);
  });
}

for (const form of document.querySelectorAll("form")) form.addEventListener("submit", async (event) => {
  event.preventDefault(); if (capabilityRequestActive) return;
  const context = contextFor(form); const text = form.querySelector("textarea");
  const activity = { chat: "Generating response…", code: "Generating code…", "/v1/image-generation": "Generating image…", "/v1/summarize": "Summarizing…", "/v1/classify": "Classifying…" };
  setActive(context, true, activity[form.dataset.capability || form.dataset.path]); showError(context, "");
  let pendingCapability = null;
  try {
    if (form.dataset.capability) {
      const capability = form.dataset.capability; pendingCapability = capability;
      conversations[capability].push({ role: "user", content: text.value }); renderConversation(capability);
      const response = await submit("/v1/chat", { capability, messages: conversations[capability] });
      const answer = await response.json(); conversations[capability].push({ role: "assistant", content: answer.content }); renderConversation(capability); text.value = "";
    } else if (form.dataset.path === "/v1/classify") {
      const labels = Array.from(document.querySelectorAll(".classify-label"), (input) => input.value);
      const response = await submit(form.dataset.path, { text: text.value, labels });
      document.querySelector("#classify-result").textContent = (await response.json()).selected_label; context.result.hidden = false;
    } else if (form.dataset.path === "/v1/image-generation") {
      const width = document.querySelector("#image-generation-width").value; const height = document.querySelector("#image-generation-height").value;
      if ((width === "") !== (height === "")) throw new Error("Width and height are required together");
      const body = { instruction: text.value };
      if (width !== "") {
        if (!/^\d+$/.test(width) || !/^\d+$/.test(height)) throw new Error("Width and height must be whole pixels");
        const numericWidth = Number(width), numericHeight = Number(height);
        if (numericWidth < 64 || numericWidth > 2048 || numericHeight < 64 || numericHeight > 2048) throw new Error("Width and height must be between 64 and 2048");
        body.width = numericWidth; body.height = numericHeight;
      }
      const response = await submit(form.dataset.path, body); const image = document.querySelector("#generated-image");
      if (currentImageUrl) URL.revokeObjectURL(currentImageUrl);
      currentImageUrl = URL.createObjectURL(await response.blob()); image.src = currentImageUrl; context.result.hidden = false;
    } else {
      const response = await submit(form.dataset.path, { text: text.value });
      document.querySelector("#summarize-result").textContent = (await response.json()).content; context.result.hidden = false;
    }
  } catch (error) {
    if (pendingCapability) { conversations[pendingCapability].pop(); renderConversation(pendingCapability); }
    showError(context, error.message);
  } finally { setActive(context, false); }
});
