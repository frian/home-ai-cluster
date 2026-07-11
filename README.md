# Home AI Cluster

Local-first orchestration for personal AI runtimes.

Status: early Phase 2 prototype.

For project context, read:

* `VISION.md`
* `FOUNDATIONS.md`
* `ROADMAP.md`
* `RFC/`
* `docs/phase-2-current-state.md`
* `docs/phase-1-current-state.md`

## Current Phase 2 shape

Phase 2 currently runs as a single local process.

Requests go through one static local node and one Ollama runtime adapter.

The static local node announcement is explicit in wiring code, and node
availability is static declared routing eligibility. Node health remains
descriptive, and runtime availability remains adapter-call-time behavior.

For the detailed current Phase 2 state, see
`docs/phase-2-current-state.md`.

For the earlier Phase 1 state, see `docs/phase-1-current-state.md`.

## Run locally

This is an early Phase 2 prototype.

Prerequisites:

* Python 3.13
* `uv`
* Ollama installed and running locally
* the default Ollama model used by the adapter, currently `llama3.2`

Install dependencies:

```sh
uv sync
```

Run the FastAPI app:

```sh
uv run uvicorn home_ai_cluster.main:app --reload
```

Send a chat request:

```sh
curl -s http://127.0.0.1:8000/v1/chat \
  -H 'content-type: application/json' \
  -d '{
    "messages": [{"role": "user", "content": "Hello"}],
    "capability": "chat"
  }'
```

Example response shape:

```json
{
  "content": "...",
  "adapter": "ollama",
  "model": "llama3.2"
}
```

If Ollama is not running, `/v1/chat` returns HTTP 503:

```json
{
  "detail": "Runtime adapter unavailable"
}
```

Start Ollama and make sure the `llama3.2` model is available.

## Run the static two-machine proof

For the explicit RFC-0022 LAN-only proof, follow
`docs/static-two-machine-proof.md`.
