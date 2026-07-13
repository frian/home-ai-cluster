# Phase 5 Second Runtime Investigation

Status: Investigation

Date: 2026-07-13

This document is descriptive and investigative. It is not an RFC, makes no
architectural decision, and does not select or recommend a second runtime.

## Purpose

This investigation defines the evidence needed before RFC-0030 can select one
concrete second runtime and define the smallest shared adapter proof. It does
not answer candidate-specific questions before evidence is gathered.

## Current adapter boundary

The current `RuntimeAdapter` protocol has exactly these members:

* a stable internal `name` property returning `str`;
* synchronous `health() -> AdapterHealth` for descriptive adapter availability;
* synchronous `capabilities() -> list[Capability]`; and
* asynchronous `chat(request: ClusterRequest) -> RuntimeResult`.

The cluster-owned models crossing that boundary are currently:

| Model | Actual fields and semantics |
| --- | --- |
| `ClusterRequest` | `messages: list[ChatMessage]`, `capability: Capability`, and `constraints: RequestConstraints`. `ChatMessage` has a constrained `role` (`system`, `user`, or `assistant`) and non-empty `content`. `RequestConstraints` has `local_only` (default `true`), `prefer_fast_response` (default `false`), and optional positive `min_context_size`. |
| `RuntimeResult` | Non-empty `content`, non-empty `adapter`, and optional `model`. It contains no `node_id`; cluster execution boundaries own node attribution. |
| `Capability` | Non-empty `name`. Matching currently uses this exact name. |
| `AdapterHealth` | `available: bool` and optional `reason: str`. Current health is descriptive rather than a routing decision or cross-runtime comparison. |

These facts describe the current implementation. They are not a declaration
that every current member, synchrony choice, or semantic is final for Phase 5.

## Current Ollama-specific implementation facts

`OllamaAdapter` currently uses the default base URL
`http://localhost:11434` and a configured model default of `llama3.2`. It uses
`httpx` for transport.

Its synchronous health implementation sends `GET /api/version`, calls
`raise_for_status()`, and returns `AdapterHealth(available=False, reason=...)`
for `httpx.HTTPError`; otherwise it returns available health.

Its asynchronous chat implementation:

* converts normalized messages to dictionaries with `role` and `content`;
* sends non-streaming `POST /api/chat` with configured `model`, converted
  `messages`, and `stream: false`;
* calls `raise_for_status()`;
* extracts response content from `message.content`; and
* constructs `RuntimeResult(content=..., adapter="ollama", model=...)`.

For chat failures, it translates only `httpx.ConnectError` to the narrow
cluster-owned `RuntimeConnectionUnavailableBeforeRequestError`. Other
`httpx.HTTPError` failures translate to the broader cluster-owned
`RuntimeAdapterUnavailableError`. The adapter does not assign node
attribution.

The base URL, model default, HTTP client, endpoint paths, message JSON shape,
non-streaming flag, response extraction, and HTTPX exception types are current
Ollama implementation facts. They are not requirements of the protocol or a
final multi-runtime contract.

## Questions the second runtime must test

Candidate-specific evidence must answer:

1. Can the current normalized `ClusterRequest` be used without adding
   runtime-specific fields?
2. Can it return the current `RuntimeResult` without leaking runtime-specific
   response objects?
3. Is `name` sufficient as a stable cluster-facing adapter identifier?
4. Is `capabilities()` genuinely runtime-independent?
5. Can `health()` retain the same descriptive semantics?
6. Is synchronous health appropriate for the second runtime?
7. Is the current chat-only protocol sufficient for the first Phase 5 proof?
8. Can model selection remain adapter-owned?
9. Can the core remain unaware of runtime type, executable, API shape, and
   model format?
10. Which runtime failures can map to existing cluster-owned exceptions?
11. Does the RFC-0028 narrow pre-transmission signal apply meaningfully to the
    second runtime?
12. Which failures must remain broad `RuntimeAdapterUnavailableError`
    conditions?
13. Can the second adapter be instantiated explicitly without plugin loading or
    dynamic discovery?
14. Can tests run without requiring the real runtime for the ordinary unit
    suite?
15. What real local proof would demonstrate execution through both adapters?

## Candidate evaluation criteria

Each candidate will be evaluated with a small evidence-backed rubric:

* local-first operation and no required cloud service or account;
* privacy characteristics and Linux support;
* installation complexity and ability to run on the project’s available
  hardware;
* stable programmatic interface and simple non-streaming chat support;
* explicit model configuration and message-role compatibility;
* health or readiness mechanism and error behavior;
* testability without a live runtime and dependency impact on the Python
  project;
* whether it exercises a genuinely different runtime boundary;
* operational steps required for a real proof;
* risk of indirectly introducing an OpenAI-compatible API into project
  architecture;
* risk of premature plugin or configuration infrastructure;
* maintenance burden; and
* suitability for one small reversible increment.

Popularity, benchmark quality, model quality, UI polish, and feature count are
not primary selection criteria.

## Candidate evidence table

| Candidate | Interface type | Local/account requirements | Installation facts | Chat API facts | Health mechanism | Error-boundary implications | Dependency impact | Proof complexity | Unresolved questions |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| llama.cpp server | To verify | To verify | To verify | To verify | To verify | To verify | To verify | To verify | To verify |
| LM Studio local server | To verify | To verify | To verify | To verify | To verify | To verify | To verify | To verify | To verify |
| Direct in-process Python runtime category | To verify | To verify | To verify | To verify | To verify | To verify | To verify | To verify | To verify |

## Evidence requirements

Every future candidate-specific fact must have at least one of:

* official runtime documentation;
* direct command output from André’s machine;
* direct source-code inspection; or
* a small disposable local experiment.

Community articles, marketing pages, and memory alone are insufficient for an
architectural selection.

## Explicit non-goals

This investigation must not:

* select the second runtime or draft RFC-0030’s decision;
* modify `RuntimeAdapter`, refactor `OllamaAdapter`, add dependencies, install
  runtimes, or add source code or tests;
* introduce plugin loading, runtime discovery, model discovery, configuration
  infrastructure, adapter fallback, or scoring;
* change `/v1/chat` or add an OpenAI-compatible endpoint; or
* change any accepted RFC.

## Next step

Gather official and directly observed evidence for the three candidate categories,
then use that evidence to draft RFC-0030.
