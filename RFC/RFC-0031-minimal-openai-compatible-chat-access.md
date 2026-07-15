# RFC-0031: Minimal OpenAI-Compatible Chat Access

Status: Accepted

Date: 2026-07-15

Author: frian

## Summary

Home AI Cluster should add one narrow, non-streaming public-edge compatibility
endpoint:

```text
POST /v1/chat/completions
```

The endpoint should accept a deliberately small OpenAI chat-completions subset,
translate it into the existing cluster-owned `ClusterRequest` for the `chat`
capability, and return one compatibility-shaped response from the normalized
`ClusterResult`.

This is an access adapter for existing local tools. It is not the internal
cluster protocol, a runtime adapter protocol, a direct runtime proxy, a
replacement for `/v1/chat`, or a commitment to full OpenAI API compatibility.

The first proof is loopback-only, accepts no real authentication, has no
streaming, model discovery, runtime model selection, generation controls, tools,
or token accounting. It keeps routing, adapters, error normalization, and node
attribution cluster-owned.

## Problem

Phase 6 of the roadmap aims to let local developer tools use Home AI Cluster
without special integration. Many such tools can target an OpenAI-compatible
chat-completions URL with a custom base URL. The current `/v1/chat` endpoint is
cluster-native: it requires a capability and returns a `ClusterResult` with
cluster attribution.

Replacing that endpoint, exposing a runtime endpoint, or making an
OpenAI-shaped protocol the core architecture would violate the project's
capability-centered and engine-independent boundaries. Conversely, broad
compatibility would invite unsupported generation, tool, streaming, model, and
authentication semantics that the existing cluster models do not own.

The project needs the smallest explicit compatibility decision that enables one
useful local chat proof without hiding architectural choices inside an endpoint
implementation.

## Goals

This RFC should:

* define one additional public-edge compatibility endpoint for ordinary
  non-streaming chat requests;
* preserve the existing `/v1/chat` contract and the current cluster-owned
  request, routing, adapter, result, and node-attribution flow;
* define a fixed endpoint-identifier meaning for the compatibility `model`
  request field without making it a routing or runtime-model selector;
* define a small, truthful response envelope and error envelope;
* support an official OpenAI Python client configured with a loopback custom
  base URL and a raw HTTP client;
* preserve local-first, privacy-first, capability-centered, and
  engine-independent defaults; and
* state the minimum later implementation proof without starting implementation.

## Non-goals

This RFC does not define or authorize:

* full OpenAI API compatibility or compatibility with every OpenAI client;
* streaming, SSE, buffered pseudo-streaming, or streaming fallback;
* tools, function calling, tool calls, tool results, or tool choice;
* multimodal messages or non-string message content;
* embeddings, the Responses API, Completions API, Assistants API, or any other
  OpenAI-shaped endpoint;
* `GET /v1/models`, model discovery, model aliases, a model registry, or
  configuration-driven model mapping;
* concrete model, adapter, node, or runtime selection by a request;
* generation parameters, multiple choices, token accounting, or token usage;
* real authentication, authorization, token storage, non-loopback binding, LAN
  access, or remote-client access;
* a configuration framework;
* public routing explanations or custom OpenAI response fields for adapter or
  node attribution;
* changes to runtime adapters, the current cluster request/result models, or
  the existing `/v1/chat` endpoint; or
* direct proxying to Ollama, llama-server, or another runtime.

## Proposal

### Compatibility boundary

Add `POST /v1/chat/completions` as a public-edge translation. The endpoint
accepts one defined compatibility request, validates it before execution, then
creates the existing cluster-owned request:

```text
compatibility request
  -> strict compatibility validation
  -> ClusterRequest(messages, Capability(name="chat"), default constraints)
  -> existing orchestration and routing
  -> ClusterResult with cluster-owned node attribution
  -> compatibility response
```

The route must not call a runtime directly, duplicate routing, bypass
`ClusterRequest`, bypass node attribution, or expose a runtime response object.
It is a second public edge over the same orchestration path. The current
`POST /v1/chat` request and response shapes remain unchanged.

### First-proof request contract

The smallest successful request is:

```json
{
  "model": "home-ai-cluster",
  "messages": [
    {
      "role": "user",
      "content": "Hello"
    }
  ],
  "stream": false
}
```

The compatibility request accepts only:

* `model`, a required string equal to `home-ai-cluster`;
* `messages`, a non-empty sequence of messages with non-empty plain string
  content and a `system`, `user`, or `assistant` role;
* optional `stream`, omitted or exactly `false`; and
* optional `n`, omitted or exactly `1`, representing the one answer the proof
  can return.

All accepted messages translate unchanged to the existing `ChatMessage` model.
The endpoint creates `ClusterRequest` with `Capability(name="chat")` and the
existing default constraints. It does not add a request-level model, runtime,
adapter, node, or concrete-model selector to `ClusterRequest`.

`model` is an endpoint identifier only. The accepted value `home-ai-cluster`
means “send this request to the Home AI Cluster compatibility endpoint.” It
does not identify, select, prefer, constrain, or promise a concrete runtime
model, adapter, node, or route. Capability routing continues to use only the
cluster-owned `chat` capability and existing constraints.

The endpoint rejects all other request fields. In particular, it rejects:

* `stream: true`;
* `temperature`, `top_p`, `max_tokens`, and `stop`;
* an `n` value other than `1`;
* `tools`, `tool_choice`, and `response_format`;
* `user`;
* `developer` and `tool` message roles;
* multimodal or otherwise non-string message content; and
* tool calls and tool-result messages.

Unknown fields are rejected. `user` is also rejected: the first proof does not
need it, and accepting then discarding a caller-supplied identity-like value
would broaden the privacy and identity boundary without benefit. No accepted
field is identity, authorization, routing input, or loggable metadata beyond
the request required to execute it.

### First-proof response contract

On success, the endpoint returns one non-streaming compatibility response:

```json
{
  "id": "chatcmpl-...",
  "object": "chat.completion",
  "created": 0,
  "model": "...",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "..."
      },
      "finish_reason": null
    }
  ]
}
```

The fields have the following cluster-owned meanings:

| Field | Meaning |
| --- | --- |
| `id` | A newly generated opaque cluster compatibility-completion identifier. It is not a runtime identifier and carries no prompt or topology information. |
| `object` | The fixed compatibility value `chat.completion`. |
| `created` | The Unix timestamp generated by the cluster when it creates the compatibility response; it is not a runtime timestamp. |
| `model` | The actual normalized `ClusterResult.model` when it is a non-empty string. If it is unavailable, the fixed value `home-ai-cluster` means only the cluster compatibility endpoint produced the response; it does not claim a concrete model executed it. The field is always a string. |
| `choices` | Exactly one choice. |
| `choices[0].index` | The fixed value `0`. |
| `choices[0].message.role` | The fixed value `assistant`. |
| `choices[0].message.content` | The actual normalized `ClusterResult.content`. |
| `choices[0].finish_reason` | The fixed value `null`, meaning Home AI Cluster does not currently know or preserve the runtime generation finish reason. |
| `usage` | Omitted. The current cluster result has no token accounting, so the endpoint must not fabricate it. |

The `null` value deliberately makes no claim about why runtime generation
ended. It is not a redefinition of an OpenAI finish reason. A future RFC may
decide whether runtime finish semantics warrant a new cluster-owned result
field.

Adapter and node attribution remain present in `ClusterResult` and owned by the
existing execution path, but the compatibility response adds no adapter, node,
routing, or other custom OpenAI-shaped fields. This preserves the public
routing-explanation boundary.

### Loopback and placeholder bearer behavior

The first proof server must bind only to loopback. The compatibility endpoint
accepts either no `Authorization` header or a syntactically valid
`Authorization: Bearer <placeholder>` header. If present, the bearer value is
ignored solely so clients that always send an API key can make a loopback proof
request. Any other authorization scheme or malformed bearer header is rejected
as an invalid request.

The placeholder is not authentication, authorization, identity, access
control, or a security boundary. It must not be logged, persisted, forwarded to
a runtime, or used for routing. This RFC does not support non-loopback exposure
under this behavior. Real authentication, token storage, LAN access, remote
clients, and any binding beyond loopback require a separate RFC.

### Compatibility error envelope

The compatibility route owns one small public error envelope:

```json
{
  "error": {
    "message": "Runtime adapter unavailable",
    "type": "server_error",
    "param": null,
    "code": null
  }
}
```

`message` is a stable, factual cluster message. `type` is limited to
`invalid_request_error` for request validation and `server_error` for failures
after a valid request reaches the cluster. `param` names a relevant top-level
field when doing so is safe, otherwise it is `null`; `code` is `null` in the
first proof. The route must not reproduce a larger provider-specific error
taxonomy.

| Situation | HTTP status | `type` | `param` | Public message |
| --- | --- | --- | --- | --- |
| Malformed JSON or missing/invalid required request value | 400 | `invalid_request_error` | Relevant field when safe, otherwise `null` | `Invalid chat completion request` |
| Unsupported field, field value, message role, or message content | 400 | `invalid_request_error` | Relevant field when safe, otherwise `null` | `Unsupported chat completion request value` |
| `stream: true` | 400 | `invalid_request_error` | `stream` | `Streaming is not supported` |
| Unsupported endpoint identifier | 400 | `invalid_request_error` | `model` | `Unsupported model identifier` |
| No matching chat capability or routing candidate | 503 | `server_error` | `null` | `No available chat capability` |
| Runtime adapter unavailable | 503 | `server_error` | `null` | `Runtime adapter unavailable` |
| Unexpected internal failure | 500 | `server_error` | `null` | `Internal server error` |

The compatibility layer may translate the existing project exceptions, but it
must preserve their non-leaking boundary: no raw adapter exceptions, runtime
URLs, runtime payloads, node internals, prompt content, or response content in
public errors or default logs.

### Explicit exclusions

`stream: true` fails with the compatibility error envelope. It must not start a
runtime stream, buffer a result to imitate streaming, or emit SSE. Streaming
requires a separate RFC because it changes adapter interfaces, result lifecycle,
SSE framing, cancellation, disconnect handling, partial failures, and retry or
fallback semantics after output has begun.

`GET /v1/models` is excluded. The first proof's representative clients can
send a chat-completions request directly, while the cluster has no accepted
model catalogue. Listing concrete runtime models, adapters, capabilities, or
aliases would create model-ownership and discovery architecture outside this
increment.

## First implementation proof

A later implementation PR satisfies this RFC only if it demonstrates all of
the following:

1. Existing `/v1/chat` tests remain unchanged and pass.
2. A valid non-streaming compatibility request reaches the existing
   cluster-orchestration flow through `ClusterRequest` and `Capability(name="chat")`.
3. The normal routing and cluster-owned node-attribution path is used.
4. The compatibility route calls no runtime directly and duplicates no routing
   logic.
5. One official OpenAI Python client request succeeds against a loopback custom
   base URL using a placeholder bearer token.
6. One raw HTTP request succeeds against loopback without an authorization
   header.
7. The official OpenAI Python client successfully parses the selected
   `finish_reason: null` representation.
8. `stream: true` and every unsupported field/value fail explicitly with the
   compatibility error envelope.
9. Runtime unavailability translates without runtime-specific leakage.
10. Prompts, responses, and authorization headers are not logged by default.
11. Ordinary automated tests require no live runtime.
12. A separate, opt-in local proof may use one already supported local runtime.

## Rationale

The proposal follows the evidence in
[Phase 6 OpenAI-Compatible Access Investigation](../docs/phase-6-openai-compatibility-investigation.md).
That investigation found that the official OpenAI Python SDK can use a custom
base URL and a minimal `model`/`messages` chat-completions request, and that a
raw HTTP client needs no model-listing endpoint or authentication. It also
found that the current cluster owns messages, capability routing, adapter
normalization, result attribution, and privacy/error boundaries.

Using a fixed endpoint identifier avoids turning a compatibility field into a
model-routing mechanism. Returning actual normalized model attribution when it
is available preserves honesty; the fixed fallback tells the truth about the
endpoint without inventing a concrete model.

On 2026-07-15, a disposable loopback HTTP server returned minimal successful
chat-completion responses to the official OpenAI Python SDK 2.45.0, configured
with a custom loopback base URL and placeholder API key. The SDK parsed both
`"finish_reason": null` and an omitted `finish_reason` as `None`. This RFC
selects the explicit `null` representation because it truthfully communicates
that Home AI Cluster has not preserved the runtime generation finish reason.

The compatibility route remains small and boring: one endpoint, text chat,
one answer, and strict rejection. That is enough to make the Phase 6 roadmap
goal concrete without making runtime-specific behavior or OpenAI protocol
details part of the core. It preserves RFC-0003's adapter boundary,
RFC-0005's public explanation boundary, RFC-0007's normalized availability
boundary, RFC-0023's cluster-owned node attribution, and RFC-0030's decision
that a compatibility-shaped runtime interface stays private to its adapter.

## Alternatives considered

### Make `/v1/chat` OpenAI-compatible

Rejected. It would replace the cluster-native API with a different public
contract, create a breaking change, and blur the distinction between a
compatibility edge and the cluster protocol.

### Proxy directly to an OpenAI-compatible runtime endpoint

Rejected. A direct proxy would bypass cluster request normalization, capability
routing, node attribution, error translation, and engine independence. It
would also make a particular runtime protocol shape the public architecture.

### Implement broad compatibility immediately

Rejected. Current models cannot represent streaming, tools, structured output,
generation controls, token accounting, multimodal content, or model discovery.
Accepting those fields would either silently ignore user intent or make false
claims about behavior.

### Use request `model` to select a concrete runtime model

Rejected for the first proof. Model selection remains adapter-owned and is not
portable across current runtimes. Routing by a request model field would also
displace capability routing as the central abstraction.

### Add model aliases now

Rejected. Aliases require configuration, ownership, validation, discoverability,
and explainability decisions. They are not necessary for a fixed endpoint
identifier proof.

### Include streaming now

Rejected. Current adapter and result boundaries are final-result-only.
Streaming requires new lifecycle and failure semantics, not a route option.

### Require authentication immediately

Rejected for the loopback-only proof. Real authentication needs token storage,
configuration, deployment, and access-boundary decisions. A placeholder bearer
value is tolerated only for client compatibility and provides no security.

### Expose no OpenAI-compatible endpoint

Rejected. That would leave the Phase 6 roadmap goal unmet: existing local tools
would still need a custom Home AI Cluster integration rather than a familiar
chat-completions access surface.

## Trade-offs

This compatibility subset is intentionally narrow. Clients that require
streaming, tools, message roles beyond the accepted text subset, generation
controls, model discovery, concrete model selection, token usage, or real
authentication will not work with the first proof. Strict rejection reduces
convenience compared with permissive proxies.

The response is also intentionally less complete than a broad OpenAI response:
there is one choice and no usage; `finish_reason` is explicitly `null` because
runtime provenance is unavailable; and the endpoint identifier may appear as
the model fallback when actual normalized model attribution is unavailable.

Those limits are acceptable because preserving cluster-owned routing,
attribution, privacy, and engine independence is more important than
maximizing superficial compatibility. Later expansion may be valuable, but it
must be justified by evidence and a new RFC rather than inferred from this
small access proof.

## Impact

If accepted, this RFC authorizes a later small implementation PR to add the
specified compatibility edge and its tests. That implementation may add
edge-specific request/response/error models and route handling, but it must not
change the cluster-owned core models, adapter interface, routing policy,
existing `/v1/chat`, or runtime-specific boundaries described here.

The RFC does not itself change code, dependencies, API behavior, runtime
configuration, or deployment behavior. It does not make the endpoint active
until a later implementation has been reviewed and merged.

## Open questions

The following questions do not block the fixed first proof and require later
evidence and, where architectural, a separate RFC:

* user-defined model aliases and any configuration format;
* real authentication, authorization, LAN access, and remote-client exposure;
* streaming, cancellation, and partial-result semantics;
* token usage/accounting and finish-reason provenance;
* generation controls, multiple choices, tools, structured output, and broader
  message roles or content;
* a model-listing endpoint or model discovery; and
* a separate public cluster-native routing explanation surface.

## Decision

Accepted.

Home AI Cluster will add the minimal, loopback-only, non-streaming
`POST /v1/chat/completions` compatibility endpoint under the exact scope and
constraints defined by this RFC. It is a public-edge translation into the
existing cluster-owned chat flow; `POST /v1/chat` remains unchanged.

`model: "home-ai-cluster"` is an endpoint identifier, not a model, adapter,
node, or routing selector. Only the strict plain-text, single-choice,
non-streaming subset is accepted. `finish_reason` is `null` because the cluster
does not currently preserve runtime finish provenance.

Streaming, model listing, concrete model selection, real authentication,
non-loopback access, tools, generation controls, and broader compatibility
remain outside this decision.
