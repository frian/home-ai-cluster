# Phase 6 OpenAI-Compatible Access Investigation

Status: Investigation only

Date: 2026-07-15

## Purpose and scope

This document gathers evidence for a later Phase 6 architectural decision. It
does not define that decision, start Phase 6 implementation, or change a public
API.

The question is deliberately narrow: what is the smallest OpenAI-compatible
surface that lets existing local tools submit ordinary chat requests while
keeping Home AI Cluster's request normalization, capability routing, adapter
boundary, attribution, privacy defaults, and error boundary cluster-owned?

The likely candidate is `POST /v1/chat/completions`. Its path and JSON naming
would be a compatibility translation at the public edge, not a replacement for
the cluster's architecture. This investigation does not assume full OpenAI API
compatibility.

## Current Home AI Cluster boundary

### Current public and core shapes

`POST /v1/chat` currently accepts:

```json
{
  "messages": [{"role": "user", "content": "Hello"}],
  "capability": "chat"
}
```

`messages` must be non-empty. Each message has a non-empty string `content`
and one of the roles `system`, `user`, or `assistant`. `capability` is a
non-empty string. A successful response is the normalized `ClusterResult`:

```json
{
  "content": "...",
  "adapter": "ollama",
  "model": "llama3.2",
  "node_id": "local"
}
```

`model` may be `null`. The normal response deliberately omits routing reason,
node description, health, and other routing metadata. The internal
`POST /internal/cluster/request` instead accepts the normalized
`ClusterRequest` shape, including `capability: {"name": "chat"}` and optional
constraints.

The present cluster-owned objects are:

| Object | Current responsibility |
| --- | --- |
| `ClusterRequest` | Normalized messages, requested `Capability`, and `RequestConstraints`; it defaults to `local_only=true`. |
| `Capability` | The routing input. It is explicitly not a model, adapter, or node name. |
| `RuntimeAdapter` | Runtime-specific translation behind `name`, `health()`, `capabilities()`, and `chat(ClusterRequest) -> RuntimeResult`. |
| `RuntimeResult` | Adapter-normalized content, adapter identity, and optional runtime model attribution. |
| `RoutingDecision` | Internal selected node, adapter, capability, and reason. |
| `ClusterResult` | Cluster-normalized content, adapter/model attribution, and mandatory cluster-owned `node_id`. |

The router selects the first available node declaring the requested capability
and a matching registered adapter. The normal application starts without proof
wiring, so `/v1/chat` uses the static local registry. Separate explicit proof
paths can exercise declared remote routing; they are not a general default
routing policy.

Node attribution is added by selected execution, not by an adapter. The two
current adapters own their runtime URLs, configured model identity, HTTP
payloads, response extraction, and runtime-specific failures. In particular,
the llama-server adapter's private use of `/v1/chat/completions` is not a
cluster public protocol.

These remain cluster-owned after any compatibility translation:

* `ClusterRequest`, `Capability`, request constraints, and validation;
* routing and all node-selection semantics;
* `RuntimeResult`, `ClusterResult`, adapter attribution, and node attribution;
* the boundary that hides runtime payloads, response objects, URLs, and raw
  adapter exceptions; and
* default privacy and data-movement boundaries.

This follows [RFC-0001](../RFC/RFC-0001-minimal-system-shape.md),
[RFC-0003](../RFC/RFC-0003-runtime-adapter-interface.md),
[RFC-0005](../RFC/RFC-0005-routing-explanation-boundary.md),
[RFC-0007](../RFC/RFC-0007-runtime-availability-boundary.md),
[RFC-0023](../RFC/RFC-0023-result-node-attribution.md), and
[RFC-0030](../RFC/RFC-0030-second-runtime-adapter-proof.md).

### Errors, locality, and logging

The current route translates `RuntimeAdapterUnavailableError` to HTTP 503 with
only `{"detail":"Runtime adapter unavailable"}`. It translates a missing
capability or matching adapter to HTTP 404 with a capability-only detail. Tests
verify that runtime names, URLs, and connection details are not exposed. Body
validation is FastAPI/Pydantic validation and currently uses its `detail`
envelope.

The application factory itself does not bind a listening socket. The repository
proof entry points explicitly bind Uvicorn to `127.0.0.1`; no production binding
or authentication configuration exists yet. Core and adapter source has no
application logging setup and does not log prompts or responses. The Phase 5
proof intentionally reports summaries rather than prompt or generated content.
An eventual server deployment must still avoid debug middleware, body-logging
proxies, and access-log configurations that record sensitive headers.

## Candidate minimum request shape

The smallest useful non-streaming compatibility request is:

```json
{
  "model": "client-selected-label",
  "messages": [{"role": "user", "content": "Hello"}],
  "stream": false
}
```

The official Python SDK's chat-completions method requires `model` and
`messages`; `stream` is optional and defaults to non-streaming. Its method
surface also shows that many optional generation and tool parameters can be
sent by callers. See the [official method source](https://github.com/openai/openai-python/blob/main/src/openai/resources/chat/completions/completions.py)
and [official SDK example](https://github.com/openai/openai-python).

`messages` needs an explicit edge translation and validation policy. The
cluster currently permits only three text roles, while compatibility clients
may send `developer`, `tool`, multimodal content parts, tool calls, or other
message fields. A first proof should not quietly discard those semantics.

| Field | Evidence and current boundary | First-proof classification |
| --- | --- | --- |
| `model` | Required by the official SDK call. The current core has no request-level model field; configured adapter models remain adapter-owned. | Required syntactically; semantic interpretation requires an RFC decision. |
| `messages` | Required by the official SDK call and convertible only for the current plain-text `system`/`user`/`assistant` subset. | Required for the proof; unsupported roles/content forms must be rejected truthfully. |
| `stream: false` or absent | Both current adapters explicitly request non-streaming generation and return one final `RuntimeResult`. | Required behavioral mode for the proof. |
| `stream: true` | Requires a different protocol and result lifecycle; see below. | Safely rejectable for the proof. |
| `temperature`, `top_p`, `max_tokens`, `stop` | No cluster request fields or accepted cross-runtime semantics exist. Silently ignoring them could claim a generation control was honored. | Safely rejectable. |
| `n` | Current result represents one result only. | Safely rejectable. |
| `tools`, `tool_choice` | Would require tool message roles, tool-call results, output representation, execution ownership, and routing/privacy decisions. | Requires a later architectural decision. |
| `response_format` | Structured-output validation and runtime portability are not represented in current cluster models. | Requires a later architectural decision. |
| `user` | It is caller-supplied metadata, not an authenticated identity. It can be discarded without affecting current execution, but must not be logged by default. | Safely ignorable if a future compatibility DTO explicitly permits it. |
| Unknown extra fields | The official SDK permits `extra_body`; accepting arbitrary data would create accidental semantics and logging risks. | Safely rejectable. |

This table does not authorize a schema. It records why a later RFC should
prefer explicit acceptance/rejection over inheriting a large provider surface.

## Candidate minimum response shape

For a successful non-streaming text response, common clients expect the
chat-completions envelope rather than the cluster result envelope:

```json
{
  "id": "chatcmpl-local-...",
  "object": "chat.completion",
  "created": 0,
  "model": "...",
  "choices": [
    {
      "index": 0,
      "message": {"role": "assistant", "content": "..."},
      "finish_reason": "..."
    }
  ]
}
```

The official Python response type declares `id`, `object`, `created`, `model`,
one or more choices, a choice `index`, `message`, and `finish_reason`; its
`usage` field is optional. The SDK's normal example reads
`choices[0].message.content`. See the [response type](https://github.com/openai/openai-python/blob/main/src/openai/types/chat/chat_completion.py)
and [SDK example](https://github.com/openai/openai-python).

| Response field | Evidence-based treatment |
| --- | --- |
| `id` | A newly generated opaque compatibility request/completion identifier is honest synthetic metadata. It must not imply that a runtime supplied it. Whether it should correlate with cluster request identity is an RFC question. |
| `object` | Fixed compatibility metadata, `chat.completion`. |
| `created` | A cluster-side Unix timestamp is honest compatibility metadata if documented as creation of the compatibility response, not a runtime timestamp. |
| `choices[0].index` | Fixed `0` is honest for a first proof that accepts only one choice. |
| `choices[0].message.role` | Fixed `assistant` for a normalized successful chat result. |
| `choices[0].message.content` | Must be the actual `ClusterResult.content`. |
| `model` | Must not merely echo an arbitrary request label if a different configured runtime model executed. `ClusterResult.model` is the only current candidate attribution, but it can be null and model-name semantics are unresolved. A response guarantee needs an RFC decision. |
| `choices[0].finish_reason` | The normalized result does not preserve why generation ended. Returning `stop` unconditionally would be an unsupported claim. This cannot be produced honestly yet without a defined translation or richer result boundary. |
| `usage` | Current normalized results contain no token counts. Omit it where client tolerance permits; do not fabricate counts. |

Adapter and node attribution are real cluster facts, but standard
chat-completions fields do not carry them. They must not be leaked through
ad-hoc fields in the first compatibility response: RFC-0005 keeps public
routing metadata out of ordinary results. A later RFC may decide whether a
separate cluster-native explanation surface is appropriate.

## Model-name semantic options

The compatibility `model` field is required by common clients, but it must not
silently become the core routing abstraction. The current model has no
`ClusterRequest.model`, model catalogue, or configuration-driven registration;
nodes intentionally do not list models.

| Option | Fit and consequence |
| --- | --- |
| Ignore it as a compatibility label | Small transport translation, but surprising if the response indicates a different runtime model. It requires clear documentation and a response-model rule. |
| Map it to a capability | Keeps routing capability-centered only if an explicit, user-visible mapping exists. It changes capability semantics and needs an RFC. |
| Map it to an adapter | Exposes runtime identity as a caller control and bypasses capability-first routing. It changes routing semantics and needs an RFC. |
| Map it to a runtime model | Violates the current adapter-owned model-selection boundary unless model ownership, portability, and availability are designed explicitly. Needs an RFC and likely new configuration/model metadata. |
| Map it to a user-defined cluster alias | Could protect engine independence and user expectations, but creates alias ownership, validation, configuration, and explainability architecture. Needs an RFC. |
| Restrict it in the first proof | Most honest initial posture: require a syntactic string but support only one documented label or label policy. The exact restriction still needs the later RFC. |

RFC-0030 is especially direct: a request-level model field was intentionally
not added because model selection is adapter-owned and is not consistent across
runtimes. The observed llama-server process could execute an unknown request
model against its configured loaded model. Therefore an endpoint cannot claim
that accepting a model string selects a runtime model without a new project
decision.

## Authentication observations

The official Python client accepts a custom `base_url`, but its normal client
construction requires an API key or another credential source. Its
chat-completions operations are declared with bearer authentication. The
[client source](https://github.com/openai/openai-python/blob/main/src/openai/_client.py)
and [chat method source](https://github.com/openai/openai-python/blob/main/src/openai/resources/chat/completions/completions.py)
show both facts. The SDK also documents custom base URLs.

A raw HTTP client can send no `Authorization` header. Consequently the smallest
local-only proof could accept both no header and `Authorization: Bearer` with a
placeholder value, then ignore that value. That accommodates SDKs without
pretending a placeholder protects a non-loopback service. It should never log
the value.

Requiring a configured local token is a different security/configuration
decision. It may be necessary before any non-loopback exposure, but no current
binding, authentication, token storage, or configuration architecture exists.
The later RFC should decide the loopback binding guarantee, accepted-header
behavior, token handling, and rejection behavior together; this investigation
does not implement any of them.

## Error-envelope observations

OpenAI-compatible clients commonly consume HTTP status and an error object;
the SDK maps 400, 401, 403, 404, 422, 429, and server failures to typed errors.
It does not make raw runtime errors a compatibility requirement. See the
[official SDK error documentation](https://github.com/openai/openai-python).

An OpenAI-style envelope normally has this broad shape:

```json
{
  "error": {
    "message": "Human-readable cluster error",
    "type": "...",
    "param": null,
    "code": null
  }
}
```

| Situation | Current behavior | Compatibility implication |
| --- | --- | --- |
| Invalid body | FastAPI/Pydantic 422 `detail` validation response. | A compatibility mapper could use an `invalid_request_error`-style envelope, but field naming/exposure needs an RFC. |
| Unsupported fields or `stream: true` | No current compatibility schema. | Reject with a stable cluster-owned client error; do not silently ignore generation semantics. |
| No matching capability/node/adapter | HTTP 404 capability-only detail. | Preserve factual cluster explanation; exact status/type mapping is an RFC question. |
| Runtime unavailable | HTTP 503 generic detail. | Preserve the generic cluster-owned unavailable message; do not expose runtime URLs, exception classes, or payloads. |
| Internal failure | Not a defined compatibility mapping. | Must be generic and non-leaking; error taxonomy requires an RFC. |

Compatibility must translate at the public boundary, not allow an adapter or
runtime error object to escape it. Existing runtime failures already normalize
to project exceptions; that remains the right direction.

## Streaming boundary

Accepting `stream: true` would be a separate feature, not a Boolean branch.
The official Python SDK exposes a distinct stream return type; its documentation
uses server-sent events (SSE). A compatible endpoint would need to produce
incremental chat-completion chunk envelopes, set the SSE media type, send a
terminal `data: [DONE]`, and handle flush ordering, client disconnects, and
cancellation.

The current adapter protocol returns one final `RuntimeResult`; `ClusterResult`
has no stream lifecycle, chunk identifier, delta, finish reason, cancellation,
or partial-error representation. Both present adapters explicitly request
non-streaming runtime responses. Runtimes may offer their own streaming APIs,
but translating those safely would require adapter changes plus a cluster-owned
stream/result/error boundary. It also raises routing questions: after streaming
starts, a retry or fallback cannot be invisible to the caller.

Streaming can therefore be deferred from the first proof. Rejecting
`stream: true` explicitly is more honest than buffering a response while
claiming it streamed.

## Model-listing observations

The official SDK's direct chat-completions example sends a model string and
does not first call a model-listing endpoint. LiteLLM's documented proxy example
does the same with a custom base URL and placeholder key; it is useful evidence
that direct chat requests are sufficient for a representative generic
OpenAI-compatible client. See the [LiteLLM README](https://github.com/BerriAI/litellm).

No `/v1/models` endpoint exists in the repository. The node model intentionally
has no model list, current adapters own configured model identities, and there
is no cluster alias catalogue. `GET /v1/models` is therefore not necessary for
the smallest proof and cannot honestly promise a portable cluster model
catalogue today. A later RFC would need to decide whether it lists concrete
runtime models, adapters, capabilities, aliases, or no models.

## Representative client evidence

| Client | Endpoint and minimum request | Response/use | Streaming, models, auth, base URL |
| --- | --- | --- | --- |
| Official OpenAI Python SDK | Calls `/chat/completions` relative to configured `base_url`; `model` and `messages` are required. | The documented normal access is `choices[0].message.content`; the typed response includes the envelope fields discussed above. | Streaming is optional and separate. The direct example does not list models first. Normal construction uses an API key and bearer auth; custom base URLs are supported. |
| Raw HTTP client | Can send exactly the candidate JSON to `POST /v1/chat/completions`. | Needs only HTTP success/error handling and the desired JSON fields. | Streaming and model listing are optional to this client. It can omit authentication entirely. |
| LiteLLM proxy / generic OpenAI-compatible client | Its documented proxy example constructs `openai.OpenAI(api_key="anything", base_url="http://…")` then calls `chat.completions.create(model=…, messages=…)`. | It uses the standard OpenAI client response surface. | The example demonstrates a placeholder key and custom base URL; it does not require a preliminary models call. |

These are intentionally a small sample, not a market survey. They show that
chat-completions plus a custom base URL is a useful first compatibility target,
while they do not establish a need for the Responses API, tools, streaming, or
model discovery.

## Privacy and logging considerations

Compatibility introduces new inputs that current `/v1/chat` does not accept:
the `Authorization` header, client-chosen model label, `user`, tool schemas,
and arbitrary optional metadata. Some can contain identifiers or secrets even
when the message body is private.

The compatibility edge should preserve these defaults:

* no prompt, completion, authorization-header, or `user` logging by default;
* no persistence, telemetry, cloud account, or external request forwarding;
* no runtime-specific payload/response or raw exception leakage into core logs
  or public errors; and
* loopback-only deployment assumptions made explicit before implementation.

Rejecting unsupported fields reduces accidental retention and avoids implying
that sensitive tool or structured-output data has a supported handling path.
Any opt-in diagnostics need a separately designed redaction and retention
boundary.

## Compatibility levels considered

| Level | Scope | Status in this investigation |
| --- | --- | --- |
| 0 — current cluster API | `/v1/chat` and normalized cluster result. | Implemented; not changed. |
| 1 — first useful proof | `POST /v1/chat/completions`, plain-text chat messages, required model label, non-streaming only, one response choice, no fabricated usage, explicit rejection of unsupported semantics. | Promising direction; requires an RFC before implementation. |
| 2 — selective client convenience | Carefully specified optional generation controls, model aliases, a model-listing decision, and a stable error/auth policy. | Later architectural work. |
| 3 — broad OpenAI surface | Streaming, tools, structured output, multimodal messages, multiple choices, Responses API, and a broad model catalogue. | Explicitly out of the first proof. |

## Unresolved architectural questions

1. What `model` means at the cluster edge, and whether a model label may
   constrain routing without making models the routing abstraction.
2. Whether a compatibility request introduces a separate edge DTO only, or
   requires any change to `ClusterRequest` and constraints.
3. Which plain-text roles translate, including the treatment of `developer`
   and tool-related messages.
4. Whether and how actual runtime model attribution is exposed in the required
   response `model` field when it is unavailable or differs from a request
   label.
5. Whether finish reasons should be preserved through a new result boundary or
   have an explicitly limited compatibility meaning.
6. The authentication and loopback-binding policy, including ignored
   placeholder bearer tokens versus a configured local token.
7. The stable compatibility error taxonomy, status mappings, and validation
   error disclosure policy.
8. Configuration and ownership for aliases, tokens, binding, or any future
   model catalogue.
9. Whether a later separate cluster-native attribution/explanation surface is
   needed without overloading OpenAI-compatible responses.
10. The streaming adapter/core/cancellation boundary.

## Non-binding recommendation for a later RFC

The strongest small direction is a Level 1, non-streaming
`POST /v1/chat/completions` compatibility edge. It should translate only a
plain-text chat subset into the unchanged cluster-owned request and return a
single compatibility envelope from the unchanged cluster-owned result. It
should accept no claimed generation controls, tools, structured output, model
catalogue, or streaming.

Before implementation, the RFC should explicitly decide model-label semantics,
the response `model` and `finish_reason` truthfulness rules, error envelope,
authentication/loopback policy, validation behavior, and the exact set of
rejected fields. If resolving any of those requires changes to request/result
models, routing, model ownership, error categories, privacy boundaries, or
configuration, that RFC—not this investigation—must make the decision.

## Sources and repository evidence

Repository evidence inspected on 2026-07-15:

* `src/home_ai_cluster/api/routes.py`, `main.py`, and `api/wiring.py`;
* `core/models.py`, `router.py`, `orchestrator.py`, `executor.py`, and
  `registry.py`;
* `adapters/base.py`, `ollama.py`, and `llama_server.py`;
* API, core-model, adapter, routing, and application tests;
* [Phase 5 Current State](phase-5-current-state.md); and
* accepted RFCs governing the minimal system, runtime adapter, node, routing,
  availability, node attribution, Phase 4/5 boundary, and second adapter
  proof.

External primary-source evidence:

* [OpenAI Python SDK README](https://github.com/openai/openai-python);
* [OpenAI Python chat-completions method source](https://github.com/openai/openai-python/blob/main/src/openai/resources/chat/completions/completions.py);
* [OpenAI Python chat-completion response type](https://github.com/openai/openai-python/blob/main/src/openai/types/chat/chat_completion.py);
* [OpenAI Python client source](https://github.com/openai/openai-python/blob/main/src/openai/_client.py); and
* [LiteLLM repository README](https://github.com/BerriAI/litellm).

No production code, API, dependency, live runtime, or external application was
changed or installed for this investigation.
