# RFC-0030: Second Runtime Adapter Proof

Status: Accepted

Date: 2026-07-15

Author: frian

## Summary

Select `llama-server` as the concrete second runtime for the first Phase 5 multi-runtime adapter proof.

The proof will add one explicit `llama-server` adapter behind the existing cluster-owned `RuntimeAdapter` boundary, keep Ollama unchanged, and demonstrate one real local chat request through each adapter.

The proof must remain small, local-only, explicitly wired, and reversible. It must not introduce runtime discovery, plugin loading, automatic fallback, scoring, new public API shapes, or an OpenAI-compatible cluster endpoint.

## Problem

Home AI Cluster currently has one concrete runtime adapter: `OllamaAdapter`.

The existing adapter boundary is intended to be engine-independent, but one implementation cannot prove that the core is truly independent of Ollama-specific transport, endpoints, payloads, response objects, model behavior, and failures.

Phase 5 therefore needs one concrete second runtime and one smallest shared proof.

If the project does nothing, the current architecture may remain only theoretically multi-runtime. Ollama-specific assumptions could continue to look like generic cluster concepts because no second implementation exercises the boundary.

The second runtime must be chosen deliberately. The investigation considered:

* `llama-server`;
* LM Studio local server; and
* a Python in-process runtime using Transformers, PyTorch, and SmolLM2.

The evidence is recorded under `docs/evidence/` and in `docs/phase-5-second-runtime-investigation.md`.

## Goals

This RFC should:

* select one concrete second runtime for the first Phase 5 implementation;
* define the smallest shared adapter proof;
* preserve the existing cluster-owned request and result models unless implementation evidence proves a minimal change is necessary;
* keep model selection and runtime-specific configuration adapter-owned;
* keep the core unaware of executable names, HTTP paths, payload shapes, model formats, and runtime response objects;
* retain explicit construction and wiring;
* define the minimum real local validation required before the proof is complete; and
* leave later runtime discovery, routing policy, and broader lifecycle management for separate decisions.

## Non-goals

This RFC does not:

* define a general plugin system;
* add automatic runtime discovery;
* add model discovery;
* add dynamic configuration infrastructure;
* define automatic fallback or retry policy;
* compare model quality or performance;
* distribute one inference across machines;
* change the public `/v1/chat` API;
* add an OpenAI-compatible cluster API;
* make LM Studio or Transformers unsupported forever;
* rewrite the project in Go or Rust;
* manage runtime installation or model downloads from the cluster;
* start Docker, Kubernetes, a database, or a dashboard; or
* change node discovery or distributed execution.

## Proposal

### Selected runtime

Use `llama-server` as the second runtime for the first Phase 5 adapter proof.

The runtime will run as a separate local process bound explicitly to loopback. The adapter will communicate with it over HTTP.

The proof should use the runtime's documented non-streaming chat-completions interface only as an adapter-private integration detail. The cluster must not expose or adopt that compatibility interface as its own public protocol.

### Adapter shape

Add one concrete adapter implementing the existing `RuntimeAdapter` protocol:

```text
name
health() -> AdapterHealth
capabilities() -> list[Capability]
chat(request: ClusterRequest) -> RuntimeResult
```

The exact class name is an implementation detail, but `LlamaCppAdapter` or `LlamaServerAdapter` would be clear and unsurprising.

The adapter must:

* own its base URL and configured model identity;
* translate cluster-owned messages into the runtime request shape;
* request non-streaming generation;
* extract assistant text without leaking runtime response objects;
* return a cluster-owned `RuntimeResult`;
* use a stable adapter name distinct from `ollama`;
* report descriptive availability through `AdapterHealth`; and
* translate runtime failures into existing cluster-owned exceptions where their semantics genuinely match.

### Model selection

Model loading and selection remain adapter-owned.

The core must not assume that a request-level model name selects execution consistently across runtimes.

The local `llama-server` investigation showed that, in the tested single-model mode, an unknown request model value did not prevent execution of the already loaded model. The adapter must therefore treat the process configuration as authoritative and must not expose that runtime-specific behavior to the core.

The proof does not add a model field to `ClusterRequest`.

### Health

`health()` remains descriptive.

For `llama-server`, health should test the actual HTTP execution boundary used by the adapter rather than infer readiness from process existence.

The initial implementation may use the runtime's observed `/health` endpoint if the implementation confirms stable behavior for the selected packaged version.

Health must not become routing policy, runtime ranking, or cross-runtime scoring.

### Error translation

A connection failure before an HTTP request can be transmitted may map to the existing `RuntimeConnectionUnavailableBeforeRequestError`, matching the narrow semantics established for the Ollama adapter.

Other transport, HTTP status, malformed response, model-loading, and runtime execution failures should map to `RuntimeAdapterUnavailableError` unless an already accepted cluster-owned exception matches exactly.

The adapter must not leak `httpx`, llama.cpp, OpenAI-compatible, or GGUF-specific exceptions through the cluster boundary.

This RFC does not introduce new shared exception categories solely to preserve every runtime-specific distinction.

### Capabilities

The first adapter proof remains chat-only.

The `llama-server` adapter should declare the same existing chat capability required by the current proof. It must not add speculative capabilities based on runtime feature count.

### Wiring

Instantiate both adapters explicitly in composition or wiring code.

Do not introduce:

* entry points;
* reflection;
* module scanning;
* plugin registries;
* dynamic imports;
* runtime factories; or
* configuration-driven discovery.

The implementation should make the two concrete adapters visible and understandable in ordinary code.

### Smallest shared proof

The proof is complete when all of the following are demonstrated:

1. The ordinary unit test suite runs without requiring Ollama or `llama-server` to be installed or active.
2. The existing Ollama path still succeeds through the shared cluster boundary.
3. A real local `llama-server` process can be started explicitly on loopback with one explicit local model.
4. One real non-streaming chat request succeeds through the new adapter and returns a normal `RuntimeResult`.
5. The returned result contains cluster-owned content, adapter identity, and optional model attribution only.
6. Stopping `llama-server` produces the expected cluster-owned unavailable failure rather than leaking transport details.
7. No public endpoint, request schema, response schema, node attribution rule, or routing policy changes are required for the proof.

The two real runtime executions may initially be invoked through separate explicit test wiring or a narrow proof script. This RFC does not require automatic runtime selection in the public API.

## Rationale

### Why `llama-server`

`llama-server` is the smallest reversible increment that still proves a second concrete runtime implementation.

It supports the project principles:

* **local-first:** the tested server runs locally on loopback with a local model;
* **privacy-first:** no cloud account or remote inference service is required for execution;
* **engine-independent:** the core must support both Ollama and llama.cpp-specific behavior without learning either API;
* **capability-centered:** the shared proof remains based on the chat capability rather than runtime brands;
* **boring solutions first:** it reuses the existing HTTP client dependency and an explicit process boundary;
* **architecture before implementation:** the adapter decision and proof boundary are recorded before code; and
* **fake in distribution, but not fake in architecture:** both runtimes can remain on one machine while exercising two real adapter implementations and two real execution processes.

Compared with the other candidates, it introduces the least new project-level machinery:

* no PyTorch or Transformers dependency in the orchestrator;
* no model object held in the orchestrator process;
* no LM Studio daemon/server/model lifecycle stack;
* no account or desktop application requirement;
* no plugin system;
* no new public protocol; and
* no commitment to Python as the only viable future implementation language.

### Why the compatibility endpoint is acceptable internally

The llama.cpp server interface resembles an OpenAI chat-completions API.

Using that endpoint privately inside one adapter does not mean Home AI Cluster adopts OpenAI compatibility as an architectural boundary.

The adapter owns:

* endpoint paths;
* request and response shapes;
* model-name behavior;
* transport details; and
* runtime errors.

The cluster continues to expose its existing local `/v1/chat` contract and cluster-owned models.

This distinction must remain explicit in code and documentation.

### Why not LM Studio for the first proof

LM Studio was locally proven to work, but the investigated native API adds more operational layers:

```text
llmster daemon
HTTP server
loaded model
```

Daemon availability did not imply HTTP server availability.

The tested native `/api/v1/chat` interface also rejected direct role-based assistant history, while the current `ClusterRequest` supports `system`, `user`, and `assistant` messages.

An adapter could instead use LM Studio's compatibility endpoint or stored conversation mechanism, but either choice adds avoidable questions for the first proof:

* compatibility-interface influence;
* runtime-owned conversation state;
* explicit storage controls;
* more lifecycle states; and
* a larger operational dependency.

LM Studio remains a valid future candidate after the shared boundary has been proven with a smaller increment.

### Why not Transformers in-process for the first proof

The Transformers experiment proved that the current protocol can represent a non-HTTP runtime. That is valuable architectural evidence.

However, selecting it for the first implementation would add substantial coupling and dependency weight:

* PyTorch and Transformers become project dependencies;
* model memory shares the orchestrator process;
* runtime crashes or memory pressure affect the orchestrator directly;
* installation and wheel compatibility become part of the application environment;
* exceptions require library-specific interpretation; and
* future implementation-language independence becomes harder.

It also accepts unexpected message roles at the template layer, which confirms that the adapter or cluster must own validation rather than relying on the runtime.

This candidate is useful for testing the conceptual boundary, but it is not the smallest boring implementation increment.

## Alternatives considered

### Select LM Studio local server

Advantages:

* explicit model identifiers;
* useful local CLI lifecycle controls;
* native local REST API;
* successful local execution; and
* clear rejection of unknown models.

Not selected because the first proof would inherit more lifecycle and interface complexity than necessary.

### Select Transformers in-process

Advantages:

* genuinely different non-HTTP boundary;
* direct support for tested role history;
* strict offline execution after acquisition;
* simple content normalization; and
* no runtime server process.

Not selected because it couples the orchestrator to a large Python inference stack and shares failure and memory boundaries with the core process.

### Keep Ollama as the only adapter

Not selected because it cannot demonstrate that the adapter boundary is genuinely runtime-independent.

### Implement more than one new adapter

Not selected because Phase 5 needs one smallest proof, not a runtime catalogue.

### Introduce a generic OpenAI-compatible adapter

Not selected because protocol similarity is not sufficient proof of shared runtime semantics. Model selection, health, lifecycle, failure behavior, and response details differ across runtimes.

A generic compatibility abstraction would be premature and could accidentally make OpenAI compatibility the project's architecture.

### Introduce a plugin system before the second adapter

Not selected because explicit wiring is sufficient for two adapters and easier to understand, test, and reverse.

## Trade-offs

This proposal makes it easier to:

* prove the current adapter boundary with a second real runtime;
* isolate runtime-specific HTTP details;
* reuse the existing transport dependency;
* keep the orchestrator process independent from model execution memory;
* preserve future implementation-language freedom; and
* complete Phase 5 in small reviewable increments.

It makes it harder to:

* demonstrate a non-HTTP adapter in production code immediately;
* exercise in-process lifecycle and exception semantics;
* use LM Studio's richer management features; and
* claim broad runtime support after only two HTTP-backed adapters.

The selected runtime also carries a compatibility-interface risk. That risk is acceptable only because the interface remains private to one adapter and the cluster API remains unchanged.

The proof requires an externally managed local process and model file. This is acceptable because runtime installation and lifecycle automation are outside the current scope.

## Impact

### Architecture

The project gains a second concrete implementation of `RuntimeAdapter`.

The core should remain unchanged unless implementation reveals a minimal, evidence-backed incompatibility. Any architectural change beyond this RFC's decision requires either an amendment while Draft or a separate RFC.

### Source code

Future implementation work is expected to add:

* one concrete adapter module;
* adapter-specific tests using mocked or injected HTTP behavior;
* explicit composition or proof wiring; and
* a small real-local proof procedure or result document.

### Dependencies

No new Python dependency is expected if the adapter reuses `httpx`.

`llama-server` and its model remain external local runtime prerequisites for the real proof, not Python project dependencies.

### Public API

No change.

`/v1/chat` remains the cluster-owned local endpoint and must not become OpenAI-compatible.

### Users

No immediate user-facing change is required for the adapter implementation proof.

### Future compatibility

The proof should make later adapters easier by clarifying which behaviors belong to the core and which belong to concrete runtimes.

It does not promise that every runtime can fit the current protocol without future RFCs.

## Open questions

The following implementation details remain open and do not block the architectural selection:

* the final concrete adapter class name;
* the exact internal default base URL and whether tests always inject it;
* the exact configured model attribution returned in `RuntimeResult`;
* whether health uses `/health` directly or another minimal verified readiness request;
* the smallest explicit proof wiring that avoids changing public routing behavior;
* whether the real proof uses the already investigated Gemma GGUF or another comparably small local model; and
* the exact follow-up documentation filename for the successful shared proof.

The following require a new RFC if proposed later:

* automatic adapter selection;
* runtime fallback;
* dynamic discovery;
* configuration-driven runtime registration;
* shared lifecycle management;
* a generic OpenAI-compatible adapter;
* runtime-owned conversation state; and
* changes to the public API.

## Decision

Accepted.

Home AI Cluster will use `llama-server` as the concrete second runtime for
the first Phase 5 multi-runtime adapter proof, under the scope and constraints
defined by this RFC.
