# RFC-0003: Runtime adapter interface

Status: Draft

Date: 2026-06-30

Author: frian

## Summary

Home AI Cluster should define a minimal runtime adapter interface before implementing the first Ollama adapter.

A runtime adapter translates between Home AI Cluster core concepts and a specific AI runtime.

The core should not know how Ollama, llama.cpp, vLLM, MLX, or any future runtime expects requests, models, options, or responses.

For Phase 1, the adapter interface should stay small:

* report basic health;
* report supported capabilities;
* accept a normalized chat request;
* return a normalized result.

The first implementation may only support Ollama and one chat capability, but the boundary must already be clear.

## Problem

Home AI Cluster must remain engine-independent.

RFC-0001 defines runtime adapters as one of the core concepts of the system.

RFC-0002 selects Ollama as the first runtime target for Phase 1, but also states that Ollama must not shape the core architecture.

Without a minimal adapter interface, the first implementation could accidentally become an Ollama wrapper.

That would make the public endpoint, routing logic, request models, and result models depend on Ollama-specific behavior too early.

The project needs a small boundary between:

* core orchestration;
* routing decisions;
* runtime-specific execution.

## Goals

This RFC should:

* define what a runtime adapter is responsible for;
* define what the core may expect from an adapter;
* keep runtime-specific details outside the core;
* support the first Ollama implementation;
* preserve the possibility of future adapters;
* avoid over-designing a final plugin system.

## Non-goals

This RFC does not define:

* a final plugin system;
* dynamic adapter loading;
* adapter discovery;
* streaming responses;
* multi-modal requests;
* embeddings;
* tool calling;
* model download behavior;
* model placement;
* advanced scheduling;
* authentication;
* remote runtime protocols;
* a final configuration format.

Those can be decided later.

## Proposal

A runtime adapter should be a small boundary object used by the orchestrator to execute a normalized request through a specific runtime.

For Phase 1, the adapter interface should provide four responsibilities:

1. identify itself;
2. report health;
3. report supported capabilities;
4. execute a chat request.

A possible first interface:

```python
from typing import Protocol

from home_ai_cluster.core.models import (
    AdapterHealth,
    Capability,
    ClusterRequest,
    ClusterResult,
)


class RuntimeAdapter(Protocol):
    @property
    def name(self) -> str:
        ...

    def health(self) -> AdapterHealth:
        ...

    def capabilities(self) -> list[Capability]:
        ...

    async def chat(self, request: ClusterRequest) -> ClusterResult:
        ...
```

The exact Python names may change during implementation, but the architectural boundary should remain.

### Adapter identity

Each adapter should have a stable internal name.

Examples:

```text
ollama
llama-cpp
mlx
vllm
```

The adapter name is used for routing metadata and explanations.

It is not a user-facing brand promise.

### Health

An adapter should be able to report basic availability.

For Phase 1, health can be minimal:

```python
class AdapterHealth(BaseModel):
    available: bool
    reason: str | None = None
```

This is enough for the router to avoid an unavailable adapter and explain failures.

### Capabilities

An adapter should report the capabilities it can currently provide.

For Phase 1, this may be as simple as:

```python
Capability(name="chat")
```

The capability model should remain intentionally small.

The first adapter does not need to expose a rich taxonomy of model features.

### Chat execution

The adapter should accept a normalized cluster request and return a normalized cluster result.

The core should pass Home AI Cluster objects to the adapter.

The adapter should translate those objects into runtime-specific calls.

For Ollama, this means the adapter may know about:

* Ollama endpoint paths;
* Ollama request JSON;
* Ollama response JSON;
* Ollama model names;
* Ollama connection errors.

The core should not know those details.

For Phase 1, the adapter interface should expose a `chat()` method rather than a generic `execute()` method.

`chat` is generic enough in the AI ecosystem to describe the first supported capability, while still being explicit and understandable.

A more generic `execute()` method may become useful later if several capability types share the same execution shape.

Phase 1 should not pretend that such a unified execution model already exists.

### Normalized result

The adapter should return a result shaped for Home AI Cluster, not for the runtime.

A minimal result may include:

```python
class ClusterResult(BaseModel):
    content: str
    adapter: str
    model: str | None = None
```

Routing metadata may be added by the orchestrator rather than the adapter.

The adapter should report what happened inside the runtime boundary.

The orchestrator should report why that adapter was selected.

## Phase 1 behavior

In Phase 1:

* there is one local node;
* there is one Ollama adapter;
* there is one `chat` capability;
* routing is naive;
* the adapter interface is explicit;
* the public endpoint does not call Ollama directly.

The expected flow is:

```text
HTTP request
  -> API layer
  -> ClusterRequest
  -> router
  -> RuntimeAdapter
  -> Ollama
  -> ClusterResult
  -> HTTP response
```

## Constraints

The first implementation should not:

* import Ollama-specific code from the API layer;
* put routing logic inside the Ollama adapter;
* expose Ollama request or response shapes as core models;
* make model names the primary routing abstraction;
* log prompts or responses by default;
* require more adapter methods than Phase 1 needs.

## Rationale

This proposal supports the project foundations.

It keeps Home AI Cluster engine-independent by making runtime behavior replaceable.

It keeps the core capability-centered by requiring adapters to report capabilities rather than forcing the core to reason directly about model names.

It keeps the first implementation boring because the interface is small and explicit.

It keeps architecture-before-implementation because the adapter boundary is decided before the Ollama adapter is written.

It also follows the Phase 1 principle:

> fake in distribution, but not fake in architecture.

There may be only one adapter at first, but the code should not pretend runtime boundaries do not exist.

## Alternatives considered

### Call Ollama directly from the endpoint

This would be the fastest implementation.

It is rejected because it would make the API layer runtime-specific and weaken the architecture from the first commit.

### Define a full plugin interface now

This would make future adapters feel planned.

It is rejected because it would introduce complexity before the project has even one working adapter.

Phase 1 needs a boundary, not a plugin framework.

### Make model selection the adapter interface

The core could call something like `run_model(model_name, prompt)`.

This is rejected because it makes model names too central.

Home AI Cluster should route by capabilities and constraints, not by model names first.

### Mirror the OpenAI API internally

The adapter interface could be shaped around OpenAI-compatible chat requests.

This is rejected for now because OpenAI-compatible access is a later compatibility layer, not the core architecture.

## Trade-offs

This interface adds structure before it is strictly needed for one local Ollama call.

That makes the first implementation slightly more verbose.

The cost is acceptable because it protects the project from becoming runtime-centered.

The main risk is over-abstracting too early.

To reduce that risk, the interface only includes what Phase 1 needs.

Future capabilities should be added when there is an actual implementation need.

## Impact

This RFC affects:

* `src/home_ai_cluster/adapters/base.py`;
* the first Ollama adapter;
* core request and result models;
* routing tests;
* endpoint implementation.

It should also guide future RFCs about:

* capability modeling;
* adapter configuration;
* streaming;
* embeddings;
* tool calling;
* OpenAI-compatible access;
* multi-node runtime selection.

## Open questions

The following questions remain open:

* Should `health()` be synchronous or asynchronous?
* Should adapter capabilities be static or discovered from the runtime?
* Should model names appear in core models, adapter metadata, or configuration only?
* Should adapter errors have a shared error type?
* Should routing metadata include adapter health information?
* Should streaming require a separate adapter method later?

These questions should not block the first adapter interface.

## Decision

Pending.
