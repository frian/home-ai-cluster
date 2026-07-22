# RFC-0051: Bounded Text Summarization

Status: Draft

Date: 2026-07-22

Author: frian

## Summary

This RFC proposes `summarize` as the first second executable capability: produce
one concise plain-text summary of one supplied non-empty source text. It adds a
dedicated normalized `SummarizeRequest`, a native `POST /v1/summarize` endpoint,
an explicit `summarize` adapter operation, and a closed internal transport form
for exactly chat and summarize requests.

The proposal preserves capability-based eligibility, local-first ordering,
bounded pre-transmission fallback, normalized failures, and caller-owned final
node attribution. It does not add document ingestion, files, prompts supplied
by callers, generic capability payloads, an OpenAI-compatible summarization
edge, or lifecycle behavior.

## Problem

The accepted system is capability-centered in candidate eligibility but has only
one executable, chat-shaped capability. `ClusterRequest`, `/v1/chat`, adapter
execution, and the internal remote request path all currently represent chat.
Merely declaring another capability or asking a chat model to summarize a user
message would not prove a distinct cluster capability.

The project needs one small, engine-independent second capability that exercises
the existing eligibility and declared-remote seams without conflating text with
documents or building a general capability framework.

## Goals

This RFC proposes to:

* define exactly one new capability named `summarize`;
* make its source text and plain-text result a distinct normalized contract;
* retain current routing authority and result attribution;
* support the same bounded semantics through both current runtime adapter
  families and declared remote execution; and
* establish a narrow proof sequence before a two-machine proof.

## Non-goals

This RFC does not add:

* document upload, file paths, standard input, PDF, OCR, MIME types, binary
  transport, document retention, document indexing, document question answering,
  RAG, embeddings, or vector storage;
* sessions, streaming, tool execution, structured summaries, configurable
  length, style, language, tone, or caller-supplied prompts;
* generic request payloads, generic capability plugins, smarter routing,
  scheduling, discovery, lifecycle management, or model installation;
* a dashboard, broad OpenAI-compatible support, a database, Docker, or
  Kubernetes; or
* a root `home-ai-cluster summarize` command in this increment.

## Proposal

### Capability and semantic boundary

The sole new capability name is exactly `summarize`. `summarization` is not an
alias and no alternate capability names are accepted.

`summarize` means: **produce one concise plain-text summary of one supplied
non-empty source text.** The supplied text is content to summarize, never an
instruction-bearing chat message.

The first contract has one source text and one summary result. It has no
conversation, roles, message list, caller-supplied system prompt, question,
requested tone, style, language, or length, structured output, files, metadata,
persistence, session, or streaming. The result is plain text only.

### Normalized request and validation

The core gains a dedicated request type, conceptually:

```python
class SummarizeRequest(BaseModel):
    capability: Literal["summarize"] = "summarize"
    text: str
```

The repository-consistent implementation may add the existing request
constraints as a separately owned field when it is needed for local-versus-
declared-remote selection. It must not add fields to `ClusterRequest`, use a
generic payload map, or permit optional combinations of `messages` and `text`.
The closed request family is exactly `ClusterRequest | SummarizeRequest`.

The public endpoint determines the capability; callers submit only:

```json
{"text":"source text"}
```

`text` must be a JSON string. Its UTF-8 encoding must contain at most 65,536
bytes. Whitespace is preserved as source content, but a value whose
`text.strip()` is empty is invalid. The byte bound and blank check occur before
routing, adapter construction, remote transport, or network activity. This is a
deterministic engine-independent payload bound, not a model-token estimate or a
runtime context-window query.

The native `/v1/chat` DTO currently uses Pydantic's default policy: unmodelled
top-level fields are ignored. `/v1/summarize` follows that same public policy:
extra top-level fields are ignored, never normalized, forwarded, recorded, or
used. Thus its accepted semantic body contains only `text`.

Malformed JSON, missing or non-string `text`, blank text, and text above the
65,536-byte bound return HTTP 422 with exactly:

```json
{"detail":"Invalid summarize request"}
```

They do not expose validation internals and do not invoke adapters or remote
nodes. The uniform public error avoids making the rejected source text part of a
stable response contract.

### Internal orchestration and result

The implementation uses one small, closed internal request boundary implemented
only by `ClusterRequest` and `SummarizeRequest`. It exposes each request's
capability to the existing capability-based candidate discovery and selection
internals, then dispatches local execution to the explicit operation belonging
to that request type. It is not an open request envelope, a generic payload
object, or a plugin framework: it has two named variants and two named adapter
operations.

Existing eligibility remains authoritative. A summarize request is eligible
only when the node declares `summarize` and its declared adapter advertises
`summarize`; it must never route to a chat-only node. Existing local-first
ordering applies among eligible candidates. Existing bounded fallback applies
only among eligible candidates and only for the already accepted pre-request
connection failure. No model preference, scheduler, or capability-specific
routing policy is added.

`ClusterResult` remains unchanged. Its `content`, `adapter`, `model`, and
`node_id` fields are sufficient: the endpoint and normalized request already
identify the capability. A summary may have empty `content`, because the
existing normalized textual result contract permits empty runtime content; an
empty result is still a completed textual result rather than a new capability
failure. No result capability field or tagged result union is introduced.

### Native and compatibility endpoints

`POST /v1/chat` remains chat-only and unchanged. This RFC adds native
`POST /v1/summarize`, returning the existing `ClusterResult` JSON shape on a
successful request:

```json
{
  "content":"summary",
  "adapter":"adapter-name",
  "model":"model-name-or-null",
  "node_id":"selected-node"
}
```

No OpenAI-compatible summarization endpoint is added; the accepted
OpenAI-compatible edge remains chat-only.

If no local or declared remote candidate is eligible for `summarize`, the
existing no-selectable-candidate path applies. The native endpoint returns HTTP
404 with exactly `{"detail":"No adapter provides capability: summarize"}`.
The existing generic distinction for an available node whose declared adapter
does not provide the capability remains internal candidate evidence, but it
does not alter this public result. Runtime request failures retain the existing
HTTP 503 `{"detail":"Runtime adapter unavailable"}` behavior. Invalid runtime
responses and invalid remote results retain their existing normalized adapter or
remote transport failure handling; neither may return runtime-private details.

### Adapter contract and mapping

`RuntimeAdapter` gains one explicit operation, conceptually:

```python
async def summarize(request: SummarizeRequest) -> RuntimeResult:
    ...
```

An adapter advertises `Capability(name="summarize")` only when it implements
that operation. The execution boundary selects `summarize` only after the
adapter declaration and requested capability match, so an unsupported adapter
is never invoked as though it supported summarization.

Both current adapter families, Ollama and llama-server, implement this bounded
operation. The normalized request remains engine-independent. Each adapter owns
the runtime-specific request mapping and uses a fixed adapter-owned instruction
that directs the runtime to produce a concise summary of the supplied source
text. That mapping must treat the source as quoted content to summarize, must
not create caller-visible conversation history, and must admit no caller-
controlled role or system prompt. Byte-identical prompts across engines are not
required.

Both current runtime families may use their existing chat-completions-style
transport internally to carry the adapter-owned request. That is a runtime
transport detail, not an assertion that normalized `summarize` is chat or that
either runtime has a native summarization API. Runtime-specific model fields
remain in adapters, never in `SummarizeRequest`.

### Closed remote transport

The internal request route remains the dedicated internal cluster boundary, but
its request representation becomes a closed tagged union for exactly two
variants:

```text
kind: "chat"       with a normalized ClusterRequest
kind: "summarize"  with a normalized SummarizeRequest
```

The concrete representation may use two explicit typed models and a
discriminated union. It must validate the tag and its matching typed body before
local execution. It must not send summarize text as fake chat messages, reuse
`/v1/chat`, or introduce a generic `payload` field. The caller-side transport
selects the tag from the closed normalized request type; the receiving node
uses the matching local operation.

Declared remote ownership remains unchanged. Source text may cross the network
only to an explicitly declared trusted-LAN node selected by existing capability
eligibility. The caller overwrites any receiver-provided node identity with its
declared remote `node_id`; remote response validation remains required before
that attribution. This RFC adds no discovery, authentication, or network-trust
authority.

### Privacy and request history

RFC-0035 remains authoritative. Source text is request content and summary text
is result content: neither may enter bounded request history. History may
record only already accepted metadata; this RFC requires no additional history
field. There is no prompt or generated-summary logging, telemetry, temporary
file, hidden cache, retained text, persistence, or document metadata.

### CLI

The first implementation has no CLI surface. It exposes only the native
endpoint and the bounded internal proof path. In particular it adds no root
subcommand and does not modify RFC-0050's accepted seven-command namespace.

This avoids enlarging the first request, transport, adapter, and proof decision
with a new operator input contract. A later RFC may consider a finite
`home-ai-cluster summarize --text "..."` command only after a concrete operator
workflow warrants it; it would need explicit text-only input, no stdin,
positionals, files, `--file`, sessions, or automatic service startup.

## Rationale

`summarize` is the smallest credible second executable capability. It has a
first-class source-text contract distinct from conversation, plain-text results
that fit the existing normalized result shape, and a useful path toward later
local document-text workflows without deciding document ingestion. It makes the
existing capability declarations operationally meaningful while retaining
boring local-first routing and explicit static remote ownership.

The closed two-variant boundary is smaller and more truthful than optional
fields on `ClusterRequest` or a general payload envelope. It resolves the
current chat-shaped execution seam without predicting arbitrary future
capabilities. The fixed 64 KiB UTF-8 limit provides a simple, deterministic
resource and privacy boundary without claiming to understand any runtime's
context window.

## Alternatives considered

* **No second capability.** Safest for scope, but leaves the stated first-user
  need and the executable capability proof unresolved.
* **Summarization as chat prompting.** Rejected: it makes source text a chat
  message and proves only a prompt convention, not a new capability.
* **Optional `text` on `ClusterRequest`.** Rejected: chat and summary fields
  create invalid combinations and obscure ownership.
* **Generic capability payload envelope or generic adapter `execute`.**
  Rejected: both introduce a framework and plugin-shaped abstraction for only
  two known request meanings.
* **Separate `SummarizeRequest`.** Selected: it expresses the distinct source
  text semantics directly and keeps the family closed.
* **Dedicated `/v1/summarize`.** Selected: it leaves `/v1/chat` honest and
  avoids a premature general `/v1/requests` endpoint.
* **Reuse `/v1/chat` or add a general `/v1/requests`.** Rejected: the first is
  semantically false and the second broadens the public protocol unnecessarily.
* **One-adapter-only implementation.** Rejected: it would not demonstrate the
  required engine-independent adapter boundary across current families.
* **Caller-configurable prompt.** Rejected: it changes capability meaning and
  permits hidden role or policy input.
* **Include the CLI immediately.** Rejected for this increment: endpoint,
  transport, and runtime proof are sufficient and preserve RFC-0050's finite
  root namespace. CLI is deferred.
* **Document upload, embeddings, or RAG first.** Rejected: each adds separate
  ingestion, binary, storage, retrieval, metadata, or persistence decisions.

## Consequences

Positive consequences:

* this is the first executable proof that capability-centered architecture is
  more than a label;
* declared capability routing becomes operationally meaningful for a second
  request meaning;
* source text remains engine-independent and future local document-text work
  has a narrow textual predecessor; and
* no persistence, multimodal transport, or document authority is added.

Costs:

* a new durable request contract and native endpoint;
* one adapter protocol operation and two runtime mappings to maintain;
* a closed internal transport extension; and
* broader local, remote, validation, and privacy proof obligations.

## Proof obligations and implementation boundary

Implementation is authorized only after this RFC is accepted, and only through
these bounded steps:

1. add the normalized request and its validation tests;
2. add explicit Ollama and llama-server summarize mappings with transport fakes;
3. add local orchestration and the native endpoint;
4. prove capability eligibility, chat-only exclusion, no eligible node, and
   local execution;
5. add the closed internal remote transport support and validate remote results;
6. prove remote-only summarize execution and final caller-owned node
   attribution; and
7. run a retained two-machine proof with one chat-only node and one
   summarize-capable node, then perform Phase 18 closeout documentation.

The two-machine proof must show selection solely due to capability eligibility,
no engine-specific field in the normalized request, and no source or summary
content in history. Unit and integration evidence precede that physical proof.
No unrelated refactoring, document ingestion, CLI work, lifecycle behavior, or
roadmap edit is authorized by the implementation sequence.

## Phase classification

This RFC creates formal **Phase 18**. Unlike the completed standalone
post-roadmap refinements, it jointly extends the durable normalized request,
adapter protocol, native endpoint, internal transport, and multi-capability
proof contract. Its architectural goal is one bounded second executable
capability whose local and declared-remote execution proves that eligibility is
capability-based rather than chat-labelled.

This RFC does not modify `ROADMAP.md`. Roadmap integration is a separate
documentation pull request after RFC acceptance.

## Open questions

The architectural and public contracts are selected. Implementation may decide
only the exact fixed adapter-owned wording and escaping strategy for each
runtime request, provided it satisfies the mapping policy above and adds focused
tests. It may also choose the concrete Pydantic discriminated-union syntax for
the already selected two-variant internal transport. Neither question may
broaden the request family, prompt authority, endpoint set, or failure contract.

## Decision

Pending.
