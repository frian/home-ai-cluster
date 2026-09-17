const result = document.querySelector("#result");
const conversations = { chat: [], code: [] };
let capabilityRequestActive = false;
let currentImageUrl = null;

async function submit(path, body) {
  if (capabilityRequestActive) return null;
  capabilityRequestActive = true;
  try {
    const response = await fetch(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    if (!response.ok) {
      const detail = await response.json().catch(() => ({}));
      throw new Error(typeof detail.detail === "string" ? detail.detail : "Request failed");
    }
    return response;
  } finally { capabilityRequestActive = false; }
}
for (const form of document.querySelectorAll("form")) form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const [text, labels] = form.querySelectorAll("textarea, input");
  if (capabilityRequestActive) return;
  try {
    if (form.dataset.capability) {
      const capability = form.dataset.capability;
      const response = await submit("/v1/chat", { capability, messages: [...conversations[capability], { role: "user", content: text.value }] });
      if (!response) return;
      const answer = await response.json();
      conversations[capability].push({ role: "user", content: text.value }, { role: "assistant", content: answer.content });
      result.textContent = answer.content;
    } else if (form.dataset.path === "/v1/classify") {
      const response = await submit(form.dataset.path, { text: text.value, labels: labels.value.split(",").map((label) => label.trim()).filter(Boolean) });
      if (response) result.textContent = (await response.json()).label;
    } else if (form.dataset.path === "/v1/image-generation") {
      const response = await submit(form.dataset.path, { instruction: text.value });
      if (!response) return;
      const image = document.querySelector("#generated-image");
      if (currentImageUrl) URL.revokeObjectURL(currentImageUrl);
      currentImageUrl = URL.createObjectURL(await response.blob()); image.src = currentImageUrl; image.hidden = false;
    } else {
      const response = await submit(form.dataset.path, { text: text.value });
      if (response) result.textContent = (await response.json()).content;
    }
  } catch (error) { result.textContent = error.message; }
});
