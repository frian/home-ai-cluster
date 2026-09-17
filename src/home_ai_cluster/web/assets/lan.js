const result = document.querySelector("#result");
async function submit(path, body) {
  const response = await fetch(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  if (!response.ok) throw new Error("Request failed");
  return response;
}
for (const form of document.querySelectorAll("form")) form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const [text, labels] = form.querySelectorAll("textarea, input");
  try {
    if (form.dataset.capability) {
      const response = await submit("/v1/chat", { capability: form.dataset.capability, messages: [{ role: "user", content: text.value }] });
      result.textContent = (await response.json()).content;
    } else if (form.dataset.path === "/v1/classify") {
      result.textContent = (await (await submit(form.dataset.path, { text: text.value, labels: labels.value.split(",").map((label) => label.trim()).filter(Boolean) })).json()).label;
    } else if (form.dataset.path === "/v1/image-generation") {
      const response = await submit(form.dataset.path, { instruction: text.value });
      const image = document.querySelector("#generated-image"); image.src = URL.createObjectURL(await response.blob()); image.hidden = false;
    } else result.textContent = (await (await submit(form.dataset.path, { text: text.value })).json()).content;
  } catch (_) { result.textContent = "Request failed"; }
});
