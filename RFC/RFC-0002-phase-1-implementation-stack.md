# RFC-0002: Phase 1 implementation stack

Status: Draft

Date: 2026-06-27

Author: frian

## Summary

Phase 1 of Home AI Cluster should use a small Python stack to prove the first implementation shape.

The selected stack is:

* Python for the implementation language;
* FastAPI for the HTTP API;
* Pydantic for request and response models;
* httpx for outbound HTTP calls;
* uv for project, dependency, and Python version management;
* pytest for tests;
* ruff for linting and formatting;
* Ollama as the first runtime adapter.

These are Phase 1 choices.

They are not permanent project identity.

Home AI Cluster should remain engine-independent and should not become defined by Python, FastAPI, or Ollama.

## Problem

The project now has a minimal conceptual shape:

* request;
* capability;
* node;
* runtime adapter;
* routing decision;
* result.

The next step is to choose a Phase 1 implementation stack that can express this shape clearly.

The risk is choosing technology for the wrong reason.

A language or framework may be powerful, fashionable, or efficient, while still being wrong for the first proof.

Phase 1 does not need maximum performance.

Phase 1 does not need distributed networking.

Phase 1 does not need a dashboard.

Phase 1 needs a small implementation that makes the architecture understandable, testable, and easy to change.

The first implementation should prove this flow:

```text
request -> capability -> routing decision -> adapter -> result
```

The stack should support that flow without adding unnecessary ceremony.

## Goals

This RFC should decide the Phase 1 implementation stack.

It should:

* choose the implementation language;
* choose the HTTP framework;
* choose dependency and project tooling;
* choose the first runtime adapter target;
* define what is deliberately not included in Phase 1;
* keep implementation choices aligned with the project foundations;
* avoid turning temporary Phase 1 choices into permanent architectural constraints.

## Non-goals

This RFC does not define:

* the final public API;
* an OpenAI-compatible endpoint;
* the final runtime adapter interface;
* the final capability model;
* network discovery;
* multi-node communication;
* a dashboard;
* Docker packaging;
* deployment strategy;
* authentication;
* persistent storage;
* production observability.

Those decisions belong later.

## Proposal

Phase 1 should use Python with FastAPI.

The first implementation should expose a small custom HTTP API, use Pydantic models for request and result objects, keep orchestration logic outside the web layer, and talk to Ollama only through a runtime adapter.

The system should start with:

* one process;
* one local static node;
* one runtime adapter;
* one chat capability;
* one naive routing decision;
* one normalized result.

The implementation is single-machine, but the code should already use cluster concepts.

### Language: Python

Python should be the Phase 1 language.

Python is a good fit for the first implementation because Home AI Cluster starts as orchestration logic, not low-level performance engineering.

The first code should be easy to read, easy to test, and easy to reshape.

Python also fits the early development context of the project: it is practical for local tooling, HTTP APIs, adapters, and AI-related workflows.

This does not mean the project can never include other languages.

It only means Python is the right language for Phase 1.

### Python version

Phase 1 should target Python 3.13.

The repository should include:

```text
.python-version
```

with:

```text
3.13
```

The project metadata should require:

```text
>=3.13,<3.15
```

This gives the project a modern Python baseline without depending on the newest system Python available on one machine.

### HTTP API: FastAPI

FastAPI should be used for the Phase 1 HTTP API.

FastAPI is appropriate because it keeps the HTTP layer small and explicit, works naturally with typed request and response models, and provides automatic API documentation during development.

The web layer should remain thin.

It should translate HTTP requests into core request objects, call the orchestrator, and return normalized results.

It should not contain routing logic.

It should not know Ollama-specific details.

### Data modeling: Pydantic

Pydantic should be used for request, result, node, capability, and routing decision models.

The first models should stay small.

They should describe the architecture without pretending to be the final protocol.

Initial model candidates:

* `ClusterRequest`;
* `ChatMessage`;
* `RequestConstraints`;
* `Capability`;
* `NodeDescription`;
* `RoutingDecision`;
* `ClusterResult`.

These names may change during implementation, but the concepts should remain visible.

### HTTP client: httpx

httpx should be used for outbound HTTP calls from runtime adapters.

The first Ollama adapter can use httpx to call the local Ollama API.

The adapter should hide Ollama-specific request and response details from the core.

### Project tooling: uv

uv should be used for Phase 1 project and dependency management.

The repository should include a `pyproject.toml`.

uv should manage the virtual environment, dependencies, lockfile, and Python version selection.

This keeps local development simple and repeatable.

### Tests: pytest

pytest should be used for tests.

The first tests should focus on architecture seams rather than model output quality.

Useful early tests:

* the router selects the local node for a chat capability;
* the router rejects a request when no capability matches;
* the Ollama adapter is called only through the adapter interface;
* the HTTP endpoint returns routing metadata;
* prompts are not logged by default.

### Linting and formatting: ruff

ruff should be used for linting and formatting.

The goal is not to create a complex quality system.

The goal is to keep the first code consistent without adding many tools.

### First runtime adapter: Ollama

Ollama should be the first runtime adapter.

It is a practical first target because it is already a common local AI runtime and exposes a simple local HTTP API.

However, Ollama must remain an adapter, not the architecture.

The repository should avoid names like:

```text
core/ollama.py
```

and prefer names like:

```text
adapters/ollama.py
```

The core should speak in terms of capabilities, requests, nodes, routing decisions, and results.

The adapter should translate those concepts into Ollama-specific calls.

## Proposed repository structure

Phase 1 should start with this approximate structure:

```text
home-ai-cluster/
├── pyproject.toml
├── .python-version
├── README.md
├── src/
│   └── home_ai_cluster/
│       ├── __init__.py
│       ├── main.py
│       ├── api/
│       │   ├── __init__.py
│       │   └── routes.py
│       ├── core/
│       │   ├── __init__.py
│       │   ├── models.py
│       │   ├── registry.py
│       │   └── router.py
│       └── adapters/
│           ├── __init__.py
│           ├── base.py
│           └── ollama.py
└── tests/
    ├── test_router.py
    └── test_ollama_adapter.py
```

This structure is not final.

It is only a starting shape.

The important separation is:

* `api/` handles HTTP;
* `core/` handles orchestration concepts;
* `adapters/` handles runtime-specific behavior;
* `tests/` protects routing and adapter boundaries.

## First endpoint

Phase 1 should start with a custom endpoint:

```http
POST /v1/chat
```

The request should be small and cluster-oriented.

Example:

```json
{
  "messages": [
    {
      "role": "user",
      "content": "Hello"
    }
  ],
  "capability": "chat",
  "constraints": {
    "local_only": true
  }
}
```

The response should include both content and routing metadata.

Example:

```json
{
  "content": "Hello!",
  "routing": {
    "selected_node": "local",
    "selected_adapter": "ollama",
    "selected_capability": "chat",
    "reason": "Only available local node with chat capability"
  }
}
```

This endpoint is intentionally not OpenAI-compatible.

OpenAI-compatible access is useful later, but it should not define the first internal architecture.

The first endpoint should make the project concepts visible.

## Phase 1 exclusions

Phase 1 should deliberately exclude:

* Docker;
* dashboard;
* database;
* persistent storage;
* network discovery;
* authentication;
* OpenAI-compatible endpoint;
* streaming responses;
* real multi-node routing;
* complex configuration;
* automatic model downloads;
* automatic updates;
* cloud providers.

These exclusions are not rejections forever.

They are postponements.

The first goal is to prove the shape of the orchestrator.

## Minimal success criteria

Phase 1 succeeds when a developer can run the project locally and send a request like this:

```text
curl Home AI Cluster
```

and the system:

1. receives the request through one endpoint;
2. normalizes it into a core request;
3. selects the local node through a routing decision;
4. calls Ollama through the adapter;
5. returns the model response;
6. includes a simple routing explanation.

The expected proof is:

```text
One endpoint. One local node. One adapter. One routed request.
```

This prepares the project for the later proof:

```text
One endpoint. Two machines. One routed request.
```

## Rationale

Python keeps the first implementation readable and easy to change.

FastAPI gives the project a small HTTP layer without requiring a full application framework.

Pydantic makes the project concepts explicit as typed models.

httpx is enough for runtime adapter HTTP calls.

uv keeps local setup and dependency management simple.

pytest keeps architectural seams testable.

ruff keeps code style boring and consistent.

Ollama is the most practical first adapter target, while still staying behind an adapter boundary.

Together, these choices support the project principles:

* user simplicity over developer convenience;
* local first;
* privacy by default;
* capabilities over brand names;
* engine independence;
* transparency over magic;
* boring solutions first;
* small steps.

## Alternatives considered

### Go

Go would be a strong choice for a future long-running local agent or small distributed binary.

It is rejected for Phase 1 because the first goal is conceptual clarity and fast iteration, not deployment simplicity or static binaries.

Go may become relevant later for agents or packaging.

### Rust

Rust would provide safety and performance.

It is rejected for Phase 1 because it would add too much implementation weight before the architecture is proven.

Rust may become relevant later for performance-sensitive components.

### TypeScript

TypeScript would be a reasonable choice for API and tooling work.

It is rejected for Phase 1 because the project begins closer to local AI orchestration and Python AI tooling than to a web application.

TypeScript may become relevant later for a dashboard or developer tools.

### OpenAI-compatible API first

An OpenAI-compatible API would make existing tools easier to connect.

It is rejected for Phase 1 because it could force the project to model itself around another API too early.

Compatibility should come after the internal concepts are clear.

### Docker first

Docker could make setup reproducible.

It is rejected for Phase 1 because local development should remain simple and direct.

Docker may come later when packaging matters more than architectural discovery.

## Trade-offs

Python may not be the fastest runtime.

That is acceptable because Phase 1 is not performance-critical.

FastAPI may not be the final public API layer.

That is acceptable because Phase 1 needs a clear local HTTP entrypoint.

Ollama may influence the first adapter shape.

That risk is acceptable only if the adapter boundary is respected.

The most important trade-off is this:

> Phase 1 optimizes for architectural clarity, not finality.

## Impact

This RFC affects the first implementation commit.

It should guide creation of:

* `pyproject.toml`;
* `.python-version`;
* `src/home_ai_cluster/`;
* `api/`;
* `core/`;
* `adapters/`;
* `tests/`.

It also affects future RFCs about runtime adapter interfaces, OpenAI-compatible access, node discovery, and observability.

## Open questions

The following questions remain open:

* Should the first custom endpoint be exactly `/v1/chat`?
* Should `capability` be a string, enum, or structured object in Phase 1?
* Should routing metadata always be returned, or only when explicitly requested?
* Should the first config be hard-coded, TOML, YAML, or environment-based?
* Should Ollama model selection be explicit in config or inferred from capabilities?
* Should streaming be introduced in Phase 2 or later?

These questions should be answered during the first implementation work.

They do not block the Phase 1 stack decision.

## Decision

Pending.
