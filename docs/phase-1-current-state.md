# Phase 1 Current State

Status: Draft

This document describes the current Phase 1 implementation state.

It is descriptive, not architectural.

It records what currently exists so future changes can be reviewed against the accepted RFCs.

## Current shape

Home AI Cluster currently exposes a custom `POST /v1/chat` endpoint.

The implementation uses:

- FastAPI;
- Python 3.13;
- Pydantic;
- httpx;
- uv;
- pytest;
- ruff;
- Ollama as the first runtime adapter.

The current flow is:

```text
API request
  -> core orchestrator
  -> router
  -> static local node
  -> Ollama runtime adapter
  -> normalized cluster result
```

## Current behavior

When Ollama is available, `/v1/chat` returns a normalized `ClusterResult`.

When the runtime adapter is unavailable, `/v1/chat` returns HTTP 503 with a generic public error:

```json
{
  "detail": "Runtime adapter unavailable"
}
```

When no node supports the requested capability, `/v1/chat` returns HTTP 404 with a generic public error.

## Current boundaries

Routing explanations are internal in Phase 1.

Node health is descriptive state only and does not drive routing.

Runtime availability is detected at runtime adapter call time.

Runtime-specific failure details are normalized by adapters and are not exposed through the public API.

## Deliberately not included

Phase 1 currently does not include:

- real distributed nodes;
- node discovery;
- fallback;
- retries;
- health polling;
- runtime supervision;
- prompt or response logging by default;
- database;
- dashboard;
- authentication;
- streaming;
- Docker;
- OpenAI-compatible API.
