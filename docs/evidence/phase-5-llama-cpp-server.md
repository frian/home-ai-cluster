# Phase 5 Evidence — llama.cpp Server

Status: Investigation

Date: 2026-07-13

This document records candidate-specific evidence for the Phase 5 second runtime
investigation. It is descriptive only. It does not select a runtime, change the
adapter contract, or make an architectural decision.

## Candidate

`llama.cpp` `llama-server`.

## Investigation boundary

This record examines whether `llama-server` can support the smallest useful
second-adapter proof while preserving the current cluster-owned request, result,
capability, health, and error boundaries.

No Home AI Cluster implementation change is proposed here.

## Official sources

* `llama.cpp` main README:
  <https://github.com/ggml-org/llama.cpp/blob/master/README.md>
* `llama-server` README:
  <https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md>

The source revision used for the final comparison should be recorded before
RFC-0030 is drafted.

## Installation

Official documentation lists several installation paths:

* package managers including Homebrew, Nix, Winget, and conda-forge;
* downloadable pre-built release binaries;
* building from source; and
* Docker images.

For Home AI Cluster investigation, Docker is not required and should not be the
first proof path.

Linux installation on André's machine has not yet been directly verified.

Evidence type: official documentation.

## Execution model

`llama-server` is a separate native C/C++ process exposing an HTTP server.

The documented default bind address is `127.0.0.1` and the documented default
port is `8080`.

A model can be selected explicitly with `-m, --model FNAME`. The main README
shows the minimal local form:

```text
llama-server -m model.gguf --port 8080
```

The server can also download a model from Hugging Face, but a local GGUF file is
the preferable proof input because it keeps model acquisition outside the proof
and preserves a clearly local execution path.

Evidence type: official documentation.

## Programmatic interface

`llama-server` exposes HTTP REST endpoints.

The documented chat endpoint is:

```text
POST /v1/chat/completions
```

It is described as OpenAI-compatible. The documentation also states that it
does not make a strong claim of full OpenAI API specification compatibility.

This is a runtime interface fact. It does not imply that Home AI Cluster should
adopt an OpenAI-compatible internal or public contract.

Evidence type: official documentation.

## Chat request shape

The documented chat endpoint accepts a JSON body containing a `messages` array.
Examples use message objects with `role` and `content` fields, including
`system` and `user` roles.

The endpoint supports synchronous and streaming operation. A Phase 5 proof can
therefore request non-streaming operation explicitly.

The exact minimum request body, including whether an arbitrary model field is
ignored, validated, or used as a router key in single-model mode, still requires
direct verification.

Evidence type: official documentation.

## Chat response shape

The endpoint returns an OpenAI-style chat completion response. The normalized
assistant text appears under a choice message rather than in the same response
shape used by Ollama.

A future adapter would therefore need to own response extraction and return only
cluster-owned `RuntimeResult` data.

The exact response produced by the selected local build and proof model has not
yet been directly observed.

Evidence type: official documentation plus an architectural implication to be
tested.

## Model selection

A single server instance can load a model explicitly from a local GGUF path with
`--model`.

The server also documents a router mode in which requests are routed by the
request body's `model` field. Router mode is not required for the smallest Phase
5 proof and would add unnecessary runtime-side selection behavior.

The smallest proof should therefore investigate one explicitly started server
with one explicitly loaded local model.

Evidence type: official documentation.

## Message role handling

Official examples show `system` and `user` messages. The endpoint uses a model
chat template, and the documentation states that models with a supported chat
template work optimally. ChatML is used as a default when no supported template
is available.

Compatibility with the complete current Home AI Cluster role set — `system`,
`user`, and `assistant` — must be verified with the chosen model and local
server build.

Evidence type: official documentation.

## Health or readiness

The server documents:

```text
GET /health
```

`/v1/health` is also documented as working.

Documented responses include:

* HTTP `503` with an `unavailable_error` while the model is loading; and
* HTTP `200` with `{"status": "ok"}` when the model is loaded and the server is
  ready.

This can support descriptive adapter health without requiring the core to know
llama.cpp-specific readiness states.

The behavior when no process is listening remains a transport-level connection
failure and must be directly observed through the eventual adapter transport.

Evidence type: official documentation.

## Error behavior

The server documents structured HTTP error bodies with an `error` object that
can include `code`, `message`, and `type`.

Examples include:

* HTTP `503` / `unavailable_error` during model loading;
* HTTP `501` / `not_supported_error` for a disabled endpoint; and
* HTTP `400` / `invalid_request_error` for invalid input.

These are HTTP responses after a connection is established. They must not be
confused with the narrow pre-transmission connection signal defined by RFC-0028.

Direct evidence is still required for:

* no listener on the configured address;
* missing model file at server startup;
* unknown or incompatible model identifier in a request;
* malformed chat input; and
* model or template failures during execution.

Evidence type: official documentation.

## Testability

A future HTTP adapter could be unit-tested with a fake or mock HTTP transport in
the same general manner as the Ollama adapter, without requiring a real
`llama-server` in the ordinary unit suite.

This is an investigation hypothesis, not yet an accepted implementation
decision.

A real proof would still require one local `llama-server` process and one small
compatible GGUF model.

## Python dependency impact

Because `llama-server` exposes HTTP, a minimal adapter could plausibly reuse the
project's existing `httpx` dependency.

No Python binding appears necessary for the smallest server-based proof.

This is an investigation finding only. Dependency impact must be confirmed
against the eventual proposed adapter implementation in RFC-0030.

## Direct observations

None yet.

The following must be collected from André's Linux machine before this candidate
can be considered fully investigated:

1. installed `llama-server` version and build information;
2. installation method used;
3. exact startup command with a local GGUF model;
4. successful `GET /health` while ready;
5. successful non-streaming chat request and raw response;
6. behavior before any server is listening;
7. behavior while the model is loading, if reproducible;
8. malformed request behavior;
9. missing or invalid model behavior; and
10. shutdown behavior.

## Candidate pressure on the current adapter boundary

Current official evidence suggests:

* `ClusterRequest.messages` can probably be translated without adding
  llama.cpp-specific fields;
* `RuntimeResult` can probably remain unchanged because response extraction can
  stay inside the adapter;
* model selection can remain adapter-owned for a one-server, one-model proof;
* `health()` can probably retain descriptive semantics using `/health`;
* the core does not need to know the executable, model format, endpoint shape,
  or response schema;
* HTTP response failures should map to broad adapter-unavailable behavior unless
  a narrower cluster-owned semantic is explicitly justified; and
* failure to establish the connection before request transmission may be able to
  use the existing narrow connection-unavailable signal.

All statements in this section are hypotheses to be tested, not decisions.

## OpenAI-compatible API risk

The primary chat interface is explicitly OpenAI-compatible.

The architectural risk is not using that runtime endpoint. The risk would be
allowing its schema, terminology, model semantics, or error categories to become
the Home AI Cluster adapter contract or core architecture.

A safe proof would:

* construct the runtime-specific HTTP body only inside the adapter;
* extract only normalized cluster-owned result fields;
* keep `ClusterRequest` and `RuntimeResult` independent of OpenAI types;
* avoid adding the OpenAI Python client dependency; and
* avoid adding an OpenAI-compatible Home AI Cluster endpoint.

Whether this containment is sufficient must be decided later by RFC-0030.

## Unknowns

* Exact Linux installation path preferred for the proof.
* Exact local GGUF model to reuse or acquire.
* Exact behavior of all three current message roles with that model.
* Exact non-streaming response shape for the chosen build.
* Whether synchronous `health()` remains appropriate in implementation.
* Exact exception translation using the existing HTTP client.
* Whether the model field should be sent in single-model mode.
* Maintenance implications of the server REST API changelog.

## Evidence summary

Official documentation establishes that `llama-server` is a local native HTTP
runtime with explicit local model loading, a synchronous-capable chat endpoint,
and a readiness endpoint.

It appears capable of exercising a second HTTP runtime boundary without adding a
new Python runtime dependency. It also carries a clear OpenAI-compatibility risk
that must remain contained at the adapter boundary.

The candidate is not yet proven on André's machine and is not selected.