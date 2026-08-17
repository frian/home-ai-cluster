# Phase 5 Current State

Status: Complete

This document records the completed Phase 5 roadmap state. It is descriptive,
not a new architectural decision. Accepted RFCs remain the source of the
project's architecture.

## Goal and starting state

The [roadmap](../ROADMAP.md) defines Phase 5's goal as keeping the core
independent from specific AI engines by placing runtime-specific behavior
behind adapters. Its expected outcomes are:

* at least two runtime adapters;
* a minimal adapter interface; and
* clear separation between core orchestration and runtime details.

Before Phase 5, the project had the minimal `RuntimeAdapter` boundary and one
concrete `OllamaAdapter`. The boundary had not yet been exercised by a second
runtime with different HTTP paths, payloads, responses, health behavior, model
behavior, and failure details. Phase 5 therefore needed a small proof of the
boundary, not a runtime catalogue or new routing policy.

## Accepted boundaries

[RFC-0003](../RFC/RFC-0003-runtime-adapter-interface.md) defines the minimal
cluster-owned adapter shape:

```text
name
health() -> AdapterHealth
capabilities() -> list[Capability]
chat(ClusterRequest) -> RuntimeResult
```

[RFC-0007](../RFC/RFC-0007-runtime-availability-boundary.md) keeps runtime
availability translation at adapter call time without retries, fallback,
preflight checks, health-based routing, or lifecycle management.

[RFC-0023](../RFC/RFC-0023-result-node-attribution.md) keeps `node_id`
cluster-owned: adapters return `RuntimeResult`, while selected execution creates
the attributed `ClusterResult`.

[RFC-0028](../RFC/RFC-0028-minimal-pre-execution-candidate-fallback.md)
established the existing narrow pre-transmission connection-unavailability
signal for its proof-only fallback composition. Phase 5 reuses that
cluster-owned error only where its semantics match; it does not add fallback or
activate that proof-only composition for ordinary requests.

[RFC-0029](../RFC/RFC-0029-phase-4-closeout-and-phase-5-entry.md) required an
accepted Phase 5 design before implementation. [RFC-0030](../RFC/RFC-0030-second-runtime-adapter-proof.md)
then selected `llama-server` as the smallest second-runtime proof and explicitly
rejected plugin loading, discovery, generic compatibility adapters, automatic
selection, and public API changes for this increment.

## Implemented adapter boundary

The repository now has two concrete chat-only implementations of
`RuntimeAdapter`:

* `OllamaAdapter`, which owns Ollama's base URL, configured model, `/api/version`
  health check, `/api/chat` payload and response extraction; and
* `LlamaServerAdapter`, which owns llama-server's base URL, configured model,
  `/health` check, private `/v1/chat/completions` payload and response
  extraction.

The llama-server compatibility-shaped HTTP interface remains private to its
adapter. The core does not expose it as an internal or public protocol.

The boundary remains cluster-owned for normalized `ClusterRequest`,
`RuntimeResult`, `Capability`, `AdapterHealth`, error categories, routing,
public API behavior, and node attribution. In particular, adapters never set
`node_id`.

Adapters remain responsible for runtime-specific URLs, model configuration and
runtime model behavior, HTTP request and response shapes, descriptive health
requests, and translating runtime failures. A connection failure before request
transmission uses the existing
`RuntimeConnectionUnavailableBeforeRequestError` where its narrow semantics
match; other adapter failures use `RuntimeAdapterUnavailableError`.

## Real-local proof

The proof recorded in
[Phase 5 Evidence — Runtime Adapter Proof](evidence/phase-5-runtime-adapter-proof.md)
explicitly constructed both adapters and sent the same small cluster-owned chat
request through the shared `RuntimeAdapter` shape.

On the observed local Linux host, Ollama 0.30.8 served `llama3.2:latest` and
llama-server 8681 served an explicitly loaded local GGUF model on loopback as
`phase-5-gemma`. Both adapters produced normalized result summaries with only
adapter identity, model attribution, and a content length; neither result had
node attribution.

After the operator stopped the explicit llama-server process, the same adapter
returned `RuntimeConnectionUnavailableBeforeRequestError`. The proof output did
not expose an `httpx`, llama.cpp, GGUF, or compatibility-protocol exception.

The ordinary unit suite remains live-runtime-free. When it was executed, the
real proof was explicitly opt-in; runtimes and models were started, stopped, and
managed by the operator, not application code. Its historical runner has since
been removed after proof completion.

No `/v1/chat` API or public protocol, routing behavior, node-attribution rule,
or `RuntimeAdapter` member changed for the proof.

## Roadmap assessment

| Expected outcome | Assessment | Evidence |
| --- | --- | --- |
| At least two runtime adapters | Complete | `OllamaAdapter` and `LlamaServerAdapter` are concrete implementations, each declaring the existing `chat` capability. |
| Minimal adapter interface | Complete | Both adapters implement RFC-0003's unchanged four-member `RuntimeAdapter` protocol. |
| Clear separation between core orchestration and runtime details | Complete | RFC-0030's real-local proof exercises distinct runtime HTTP and response behavior while the shared cluster-owned models, errors, routing, public API, and node-attribution boundary remain unchanged. |

**Phase 5 is complete** according to the roadmap's stated outcomes. RFC-0030's
smallest shared-runtime proof is also complete. This conclusion does not claim
that multi-runtime evolution is complete forever or that all future runtimes
will fit the current boundary without an RFC.

## Remaining non-goals

Phase 5 did not add automatic runtime selection, runtime discovery, plugin
loading, configuration-driven registration, model discovery, retry or fallback
policy, scoring, lifecycle management, runtime installation or model download
automation, a generic OpenAI-compatible adapter, an OpenAI-compatible cluster
endpoint, streaming, a database, a dashboard, Docker, or Kubernetes.

The ordinary `/v1/chat` path remains unchanged. Existing proof-only routing and
fallback seams do not become a general multi-runtime routing system because two
adapters now exist.

## Phase 6 boundary

Phase 6 has **not** started in this PR. This document does not create a Phase 6
RFC or propose an implementation.

Before any Phase 6 implementation, architectural discussion and likely a new
RFC are required for:

* the exact OpenAI-compatible surface;
* translation between compatibility requests and cluster-owned models;
* streaming scope;
* model-name semantics;
* configuration ownership and format;
* interaction with the existing `/v1/chat` endpoint;
* error compatibility; and
* privacy and logging behavior.

Those questions remain deliberately unanswered here.

## References

* [Roadmap](../ROADMAP.md)
* [RFC-0003: Runtime Adapter Interface](../RFC/RFC-0003-runtime-adapter-interface.md)
* [RFC-0007: Runtime Availability Boundary](../RFC/RFC-0007-runtime-availability-boundary.md)
* [RFC-0023: Result Node Attribution](../RFC/RFC-0023-result-node-attribution.md)
* [RFC-0028: Minimal Pre-Execution Candidate Fallback](../RFC/RFC-0028-minimal-pre-execution-candidate-fallback.md)
* [RFC-0029: Phase 4 Closeout and Phase 5 Entry](../RFC/RFC-0029-phase-4-closeout-and-phase-5-entry.md)
* [RFC-0030: Second Runtime Adapter Proof](../RFC/RFC-0030-second-runtime-adapter-proof.md)
* [Phase 5 Second Runtime Investigation](phase-5-second-runtime-investigation.md)
* [Phase 5 Runtime Adapter Proof](evidence/phase-5-runtime-adapter-proof.md)
