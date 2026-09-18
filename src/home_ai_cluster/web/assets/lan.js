const result = document.querySelector("#result");
const conversations = { chat: [], code: [] };
let capabilityRequestActive = false;
let currentImageUrl = null;
function addLabel(value = "") {
  const input = document.createElement("input"); input.className = "classify-label"; input.value = value;
  const remove = document.createElement("button"); remove.type = "button"; remove.textContent = "Remove label";
  remove.addEventListener("click", () => input.parentElement.remove());
  const row = document.createElement("div"); row.append(input, remove); document.querySelector("#label-inputs").append(row);
}
document.querySelector("#add-label").addEventListener("click", () => addLabel());

async function submit(path, body) {
  const response = await fetch(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  if (!response.ok) {
    const detail = await response.json().catch(() => ({}));
    throw new Error(typeof detail.detail === "string" ? detail.detail : "Request failed");
  }
  return response;
}
for (const form of document.querySelectorAll("form")) form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const [text] = form.querySelectorAll("textarea");
  if (capabilityRequestActive) return;
  capabilityRequestActive = true;
  try {
    if (form.dataset.capability) {
      const capability = form.dataset.capability;
      const response = await submit("/v1/chat", { capability, messages: [...conversations[capability], { role: "user", content: text.value }] });
      const answer = await response.json();
      conversations[capability].push({ role: "user", content: text.value }, { role: "assistant", content: answer.content });
      result.textContent = answer.content;
    } else if (form.dataset.path === "/v1/classify") {
      const labels = Array.from(document.querySelectorAll(".classify-label"), (input) => input.value);
      const response = await submit(form.dataset.path, { text: text.value, labels });
      result.textContent = (await response.json()).selected_label;
    } else if (form.dataset.path === "/v1/image-generation") {
      const width = document.querySelector("#image-generation-width").value;
      const height = document.querySelector("#image-generation-height").value;
      if ((width === "") !== (height === "")) throw new Error("Width and height are required together");
      const body = { instruction: text.value };
      if (width !== "") {
        if (!/^\d+$/.test(width) || !/^\d+$/.test(height)) throw new Error("Width and height must be whole pixels");
        const numericWidth = Number(width), numericHeight = Number(height);
        if (numericWidth < 64 || numericWidth > 2048 || numericHeight < 64 || numericHeight > 2048) throw new Error("Width and height must be between 64 and 2048");
        body.width = numericWidth; body.height = numericHeight;
      }
      const response = await submit(form.dataset.path, body);
      const image = document.querySelector("#generated-image");
      if (currentImageUrl) URL.revokeObjectURL(currentImageUrl);
      currentImageUrl = URL.createObjectURL(await response.blob()); image.src = currentImageUrl; image.hidden = false;
    } else {
      const response = await submit(form.dataset.path, { text: text.value });
      result.textContent = (await response.json()).content;
    }
  } catch (error) { result.textContent = error.message; }
  finally { capabilityRequestActive = false; }
});
