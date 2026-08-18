# RFC-0076: Bounded Tavily-Assisted Chat

Status: Draft

Date: 2026-08-18

Author: frian

## Summary

This RFC proposes one explicit, caller-local Tavily Search acquisition before
one ordinary `chat` execution. An operator supplies both one Chat question and
one separate external query. The native caller makes exactly one fixed HTTPS
request to `POST https://api.tavily.com/search`, normalizes at most five
untrusted title/URL/content entries, then sends one source-grounded Chat request
through ordinary existing Chat eligibility and routing.

The executable capability remains `chat`. Tavily is not a runtime, node, or
capability. The model, runtime adapter, and selected execution node receive no
Tavily credential and have no provider or result-URL network authority. A
successful result returns generated content plus the normalized sources supplied
to that execution. This is provenance, not a claim of sentence-level factual
citation.

The proposal is an explicit opt-in exception to local-only processing. Ordinary
`hac chat` remains unchanged and usable without Tavily, an account, an API key,
or Internet access. This RFC is Draft and authorizes no implementation.

## Problem

Local Chat models have finite training knowledge. For current events and other
changing public facts—software versions, prices, rules, schedules, products,
or recently changed information—ordinary HAC Chat has no project-owned way to
obtain fresh evidence.

The current operator-owned workflow remains valid:

```text
operator retrieval
  -> local text/file/stdin or ordinary Chat input
  -> HAC
```

It does not provide a small explicit path that preserves source provenance
through Chat. The preceding fixed-provider investigation found that a fixed
provider is materially different from an arbitrary URL: HAC sends a query to
one project-selected destination rather than accepting a caller-selected network
destination. It also found that ordinary `ClusterRequest.messages` and
`ClusterResult` cannot truthfully represent acquired evidence and its
provenance as a project-owned contract.

RFC-0064 remains Rejected. HAC must not solve Chat freshness by fetching an
arbitrary public URL or by following URLs returned from a search result.

## Goals

- Add one explicit, finite, caller-local external-information path for ordinary
  Chat.
- Keep ordinary Chat local-first and unchanged when no external query is given.
- Select Tavily Search as one concrete first provider without a provider
  interface or abstraction.
- Send only an explicit operator-supplied query to Tavily, never infer, rewrite,
  or generate that query from the Chat question.
- Keep provider credentials, HTTP, acquisition, and result URL handling outside
  the runtime adapter and selected execution node.
- Normalize a small ordered evidence set before ordinary `chat` routing.
- Establish explicit source-grounded request, result, provenance, remote
  transport, deterministic message-projection, privacy, and failure semantics.
- Keep all network operations explicit and finite: one provider call, no
  retries, pagination, follow-up searches, or URL fetches.

## Non-goals

This RFC does not authorize:

- arbitrary URL retrieval, including fetching URLs returned by Tavily;
- Tavily Extract, Crawl, Map, Research, logs, usage, or any other Tavily
  endpoint;
- Exa or another provider, provider auto-selection, a second provider, or a
  provider abstraction/interface;
- a provider SDK dependency; implementation uses the existing HTTPX stack
  directly if this RFC is later accepted;
- automatic currentness detection, automatic retrieval, model-generated or
  model-rewritten queries, tool/function calling, or autonomous agents;
- retries, pagination, search loops, multi-step research, background work, or
  a fallback to ordinary stale Chat after assisted acquisition fails;
- a `web`, `browse`, `search`, `retrieve`, or `research` capability;
- RAG, embeddings, vector storage, caching, databases, persistence, query or
  source history, browser integration, OpenAI compatibility changes, Aider,
  Code, Summarize, or Classify changes;
- runtime-adapter or selected-node provider Internet authority, provider-based
  routing, model selection, runtime selection, or topology changes;
- sentence-level citation correctness, source factual correctness, or a claim
  that every supplied source was used; or
- secret storage, `.env` loading, a credential manager, TOML secret fields, or
  a generic credential abstraction.

## Proposal

### One explicit caller-edge surface

Both existing native command names gain the same optional assisted form:

```text
hac chat --external-query QUERY --message MESSAGE
home-ai-cluster chat --external-query QUERY --message MESSAGE
```

The existing positional-message spelling remains supported in the ordinary
form. For the assisted form, `--message MESSAGE` is required so the separate
operator question and external query remain visible and unambiguous. Positional
message plus `--external-query`, repeated `--message`, repeated
`--external-query`, missing either value, or blank values are invalid local
input. The existing `--timeout-seconds`, `--verbose`, and `--json` choices
retain their ordinary meanings after successful acquisition.

The presence of `--external-query` is the explicit privacy opt-in. HAC sends
only that value to Tavily. It must not send the Chat message unless the
operator has supplied exactly the same text as the external query. HAC does not
derive, summarize, expand, rewrite, rank, or otherwise transform the operator
query before sending it.

An assisted invocation follows this closed sequence:

```text
one explicit question + one explicit external query
  -> one caller-local Tavily Search request
  -> bounded source normalization
  -> one source-grounded ordinary Chat request
  -> generated content + supplied-source provenance
```

Normal `hac chat` without `--external-query` creates the same ordinary
`ClusterRequest`, sends the same `POST /v1/chat`, and has no provider contact or
new input bound. This RFC does not alter ordinary Chat behavior.

### Fixed provider and caller-local credential

The first and only provider is Tavily Search at this fixed endpoint:

```text
POST https://api.tavily.com/search
```

The operator cannot configure a different endpoint, base URL, provider,
request-header set, or provider request option. The endpoint is a fixed
project-owned authority boundary, not an arbitrary caller-selected destination.

The caller edge reads exactly one credential from the process environment:

```text
HAC_TAVILY_API_KEY
```

It is sent only as Tavily's documented `Authorization: Bearer` credential. The
key must not appear in a CLI argument, runtime composition TOML, declaration,
`ClusterRequest`, source-grounded request or result, remote envelope, runtime
adapter call, output, history, log, exception, or temporary file. HAC does not
load `.env` files. A missing or blank key fails before any Tavily or HAC model
request.

Tavily documents the fixed API base URL, `/search` endpoint, API-key
authentication, and bearer-header form in its [API introduction](https://docs.tavily.com/documentation/api-reference/introduction).
No Tavily SDK is added or required.

### One closed Tavily Search request

One assisted invocation makes at most one Tavily request. The caller uses this
closed JSON request shape:

```text
query: <explicit operator query>
search_depth: "advanced"
chunks_per_source: 1
max_results: 5
include_answer: false
include_raw_content: false
include_images: false
auto_parameters: false
include_favicon: false
include_usage: false
```

The caller sends no session, human, project, cookie, proxy, tracking, or other
optional provider header. It does not request an answer, raw page content,
images, favicons, usage, extraction, crawl, map, research, streaming, or a
provider-generated follow-up. Tavily documents that `include_answer` controls a
provider LLM answer, `include_raw_content` controls cleaned extracted page
content, `max_results` affects response size, and advanced search can return a
bounded number of short content chunks per source. [Tavily Search API](https://docs.tavily.com/documentation/api-reference/endpoint/search)

This selects raw result entries as the first information primitive. A Tavily
answer would outsource synthesis as well as acquisition and would become a
second answer authority. It is not an acceptable fallback.

The caller owns Tavily HTTP and creates a fresh isolated HTTPX client for this
one request. It uses the fixed HTTPS URL, `follow_redirects=False`,
`trust_env=False`, no proxy configuration, no pre-existing cookies, no ambient
authentication, no client certificate, a fixed `Accept-Encoding: identity`
header, and only the required content-type and explicit Tavily Authorization
headers. It must reject any non-identity `Content-Encoding` before reading the
body.

This repeats the conservative HTTPX isolation and identity-content evidence
recorded for RFC-0064. The endpoint is fixed, so this is not a claim that
hostname prevalidation solves arbitrary URL retrieval. No runtime adapter,
router, remote transport, or selected node may construct a Tavily client or
contact Tavily.

The provider call has a 5-second connect inactivity timeout and a 5-second read
inactivity timeout. These are separate from the existing 120-second omitted
native HAC inference timeout, which begins only after source-grounded request
construction. The client reads raw identity-encoded bytes and rejects the
provider response when the 131,073rd byte is observed; it retains and parses at
most 131,072 bytes. `Content-Length` is advisory only.

There is no retry, pagination, second provider call, result-URL fetch,
provider-generated-answer fallback, or fallback to ordinary Chat. If Tavily
acquisition fails, the operator's explicit assisted invocation fails and makes
zero HAC model requests.

### Normalized external source boundary

The caller accepts only a successful Tavily JSON object whose `results` value is
an ordered array of one through five entries. Each entry must contain exactly
the usable string values required for this boundary:

```text
title
url
content
```

Unknown Tavily response fields are ignored only after the expected result shape
is validated. The normalizer preserves result order and does not sort, score,
deduplicate, enrich, fetch, or interpret the entries. It retains none of
Tavily's score, request ID, response time, usage, favicon, images, raw content,
answer, provider configuration, or account data.

An accepted source entry has all of these properties:

- title is non-blank and at most 512 UTF-8 bytes;
- URL is a non-blank absolute `http` or `https` URL without user information,
  at most 2,048 UTF-8 bytes; and
- content is non-blank and at most 1,024 UTF-8 bytes.

The normalized source list has at most five entries and the sum of every title,
URL, and content UTF-8 byte length is at most 20,480 bytes. The provider query
is non-blank and at most 1,024 UTF-8 bytes. The assisted Chat question is
non-blank and at most 65,536 UTF-8 bytes, matching the accepted bounded textual
request scale. Values are never truncated or silently repaired.

The independent aggregate bound remains required even though the first
per-entry maxima fit beneath it. It keeps the total evidence contract visible if
a later decision changes a field limit. The 20,480-byte evidence maximum is
well below the existing 65,536-byte bounded-text scale and is conservative for
five single Tavily advanced chunks; HAC still enforces its own limit rather
than trusting provider behavior.

A result URL is source provenance text only. HAC must never resolve, open,
validate for connection, request, render, redirect to, or otherwise use it as
a network destination. It does not restore the arbitrary-URL authority rejected
by RFC-0064.

All source values are untrusted external data. A malformed provider JSON body,
missing or wrong-type expected structure, zero entries, excessive result count,
invalid source value, or any per-field or aggregate limit violation fails the
assisted invocation before Chat routing or model execution.

### Source-grounded ordinary Chat request and result

This RFC introduces one dedicated normalized request concept:

```text
SourceGroundedChatRequest
  question: str
  sources: ordered ExternalSource[]
  constraints: existing RequestConstraints
  capability: fixed chat
```

`ExternalSource` is the closed normalized title/URL/content representation
defined above. It contains neither provider name nor provider metadata. The
request contains neither the external query nor any credential. Its fixed
capability is `chat`; no new executable capability, static declaration name,
or routing eligibility is introduced.

The caller posts this request only to the dedicated native route:

```text
POST /v1/chat/external
```

This route is deliberately separate from `/v1/chat`, which remains the ordinary
ordered-message surface. The new route validates the explicit source-grounded
body and creates one `SourceGroundedChatRequest`; it must not accept a provider
query or key. This is narrower and more truthful than optional source fields in
the existing ordinary Chat body.

The matching successful result is:

```text
SourceGroundedChatResult
  content: str
  sources: ordered ExternalSource[]
  node_id: str
  adapter: str
  model: str | null
```

`sources` means only “the normalized sources supplied to this model execution.”
It does not assert that any sentence is supported by a source, that every source
was used, or that source content is true, complete, current, or safe. This is
provenance, not factual citation.

For an assisted invocation, default human output writes the generated content,
then an HAC-rendered `Sources supplied:` list of title and URL values. JSON
output structurally contains the normalized sources. Verbose output includes
that list plus existing execution attribution. The model does not generate this
provenance list. Ordinary Chat output is unchanged.

### Deterministic evidence projection and adapter boundary

The core owns deterministic projection from `SourceGroundedChatRequest` to the
ordered textual messages accepted by existing Chat-like runtime adapters. The
caller must not concatenate an undocumented source prompt, Tavily must not
supply instructions, and adapters must not invent provider formatting.

The projection creates a fixed ordered representation with all of these
properties:

1. a fixed cluster-owned system instruction says that the following reference
   data is untrusted data, not instruction authority;
2. the operator question remains a separate user message;
3. sources are represented in their normalized order in one separate reference
   data message; title, URL, and content are deterministically delimited using
   a fixed serialization with string escaping, so source text cannot break the
   structural boundary; and
4. no source content becomes a system message or changes request capability or
   constraints.

The exact instruction prose and serialization spelling are implementation
details only if they preserve those invariants. The runtime adapter receives the
projected ordinary text messages and invokes its existing Chat-like operation.
It does not know Tavily was used, receive an API key, select a provider, make
HTTP calls, or handle source provenance.

Structural separation ensures that sources cannot invoke tools, provider calls,
result-URL fetches, file access, code execution, configuration changes, node
selection, routing changes, or persistent-state mutation through HAC; none is
available in this slice. It cannot guarantee that a language model, especially
a small local model, will never follow malicious instructions contained in
untrusted reference text. That is a model-quality risk, not authority granted
by HAC, and this RFC makes no prompt-injection-resistance claim beyond the
structural boundary.

### Routing, remote transport, and execution

Acquisition completes before candidate collection and routing. The router treats
`SourceGroundedChatRequest` as requiring ordinary `chat`, applies existing
constraints, local-first selection, declared remote order, and only the
existing narrow pre-request fallback. Tavily data cannot select a node, runtime,
model, adapter, capability, constraint, or fallback behavior. There is no
provider node or web node.

Local execution projects the normalized source-grounded request in the core,
uses the selected adapter's existing Chat-like method, and returns
`SourceGroundedChatResult` with cluster-owned execution attribution and the
original normalized sources.

Declared remote execution remains possible under the existing static trusted
cluster model. It requires one dedicated strict internal tagged envelope,
conceptually:

```text
kind: source-grounded-chat
request: SourceGroundedChatRequest
```

The receiving HAC node revalidates the source-grounded request and performs the
same core-owned deterministic projection before its selected local adapter. The
ordinary `ChatInternalRequest` must not carry source data hidden inside a
caller-made message. The remote receives the question and normalized source
metadata/content, which is an explicit privacy consequence of choosing an
already-declared trusted remote. It receives neither the Tavily query,
credential, request details, raw response, nor provider HTTP authority.

Remote result attribution remains caller-owned declared-node attribution under
the existing transport rule, while the returned normalized sources remain the
ones supplied to the execution. Routing, topology, capability declarations,
status, preflight, discovery, and compatibility defaults otherwise remain
unchanged.

### Privacy, retention, and request history

Tavily-assisted Chat is an explicit external-processing exception. Ordinary
Chat remains fully usable without Tavily, a Tavily account, `HAC_TAVILY_API_KEY`,
or Internet access. The external provider supplies information only; inference
remains under existing local or explicitly declared trusted-remote HAC routing.
HAC does not become cloud-first.

Tavily can learn the explicit query, ordinary network/request metadata, and
the account/API-key association. Tavily's current privacy policy states that it
collects query data to retrieve content, may use portions of query data to
improve future responses unless a contract says otherwise, retains information
under its stated retention terms, and may share query data with third-party
search-index providers in limited situations. Operators must not put personal
information into a query unless they accept that disclosure; they must not
assume queries are local, confidential, or zero-retention. [Tavily Privacy
Policy](https://www.tavily.com/privacy). Tavily also documents credit-based
usage and that an advanced search costs two API credits. [Tavily Credits &
Pricing](https://docs.tavily.com/documentation/api-credits)

HAC adds no database, cache, search/query/source history, raw-response store,
or provider log. It must not log a query, question, source title/URL/content,
provider response, credential, or model result by default. If the existing
bounded request-history accounting hook is applied to this new request, it may
retain only its existing prompt-free fields—status, requested capability,
selected candidate family, outcome rule, and failure status. It must not add an
assisted flag, query, source, URL, credential, provider, raw response, or
content field. No source data is persisted solely to render the one in-process
result.

### Fail-closed behavior

The caller completes all assisted input and credential checks before creating a
Tavily client. It constructs no source-grounded request, native HTTP client, or
model request on a failed acquisition.

The invocation fails closed with privacy-safe output and no Chat/model request
when any of the following occurs:

- missing/blank Tavily key, invalid query, or invalid question;
- Tavily connection or timeout failure;
- redirect, non-success status, non-identity content encoding, or response body
  above the byte bound;
- malformed provider JSON or invalid expected result structure;
- zero usable sources or any normalized field/count/aggregate bound failure; or
- failure to construct or send the source-grounded HAC request.

Invalid caller input retains the ordinary `error: invalid request input` and
exit status 2. A missing key reports only `error: external information not
configured`. All other acquisition failures report only `error: external
information unavailable`; they expose no raw exception, provider response,
query, source text, URL, credential, resolved address, account data, or private
topology. After successful acquisition, existing native no-capability,
runtime-unavailable, timeout, status, and invalid-cluster-response ownership
applies to the one source-grounded Chat request without retry or fallback.

## Rationale

### Why one concrete Tavily provider

Tavily offers one documented fixed `/search` endpoint with API-key
authentication and explicit request controls that disable provider-generated
answers, raw content, images, automatic parameter selection, and usage fields.
Advanced search with one chunk per source and at most five results gives a small
useful evidence shape. Its documented raw result fields include title, URL, and
content, which map directly to the minimal provenance/evidence representation.

Choosing one concrete provider is smaller and more auditable than designing a
provider interface before a second implemented provider need exists. Tavily is
not selected because it is universally best; it is selected because its fixed
closed Search request supports this narrow proof. Replacing it remains a later
architectural decision, not an anticipated abstraction.

### Why a dedicated source-grounded contract

Current Chat messages can encode source text but cannot state which text is
operator instruction versus acquired evidence, independently bound sources,
their provenance, remote visibility, or result presentation. Caller-side prompt
concatenation would hide those decisions in one native command and make them
adapter/model dependent. A dedicated request, result, and closed remote
envelope keep the semantics cluster-owned while preserving the existing `chat`
capability and Chat-like adapters.

### Why this remains local-first

The default has not changed: a normal Chat request never contacts Tavily.
Assisted Chat is one visible operator choice with one disclosed external query.
It keeps model inference in HAC and only permits a provider to supply bounded
external source text. This is smaller than turning a model into a browsing actor
or making a cloud inference provider required.

## Alternatives considered

### Keep operator-owned retrieval only

Rejected for this proposal. It remains supported and safest by default, but it
does not offer the stated explicit freshness path or preserve acquired-source
provenance through Chat.

### Arbitrary public URL retrieval

Rejected. RFC-0064 remains Rejected because the documented high-level HTTPX
hostname path could not establish the required connected-public-peer invariant;
its literal-IP/text-only narrowing also lacked ordinary value. Following Tavily
result URLs would recreate that rejected arbitrary-destination authority.

### Hidden prompt concatenation into `ChatMessage`

Rejected. It loses independent source semantics, bounds, provenance, remote
transport truthfulness, and deterministic cluster ownership merely to reuse an
existing text field.

### Preprocessing-only evidence document

Rejected. It mostly recreates operator-owned retrieval with an extra provider
step and does not establish which evidence reached a Chat result.

### Exa as the first concrete provider

Not selected for the first proposal. Exa is a credible fixed-provider direction,
not a claim of inferior quality. Tavily is selected here because its documented
single `/search` request directly supports disabled generated-answer/raw-content
options and a short advanced-chunk shape. A second provider would require a
later architectural decision rather than a generic compatibility layer.

### Generic provider abstraction

Rejected. One concrete provider is the only proposed need. An abstraction would
add configuration, lifecycle, result, credential, and compatibility policy
before evidence justifies it.

### Provider-generated answer

Rejected. It delegates answer synthesis in addition to acquisition, obscures
the evidence supplied to local Chat, and weakens the point of local inference.

### Automatic or model-directed retrieval

Rejected. Deciding freshness, generating a query, repeatedly searching, or
calling tools would require a separate authority, stopping, and action-history
architecture. This RFC retains one explicit operator action only.

### New `search` or `web` capability

Rejected. Acquisition is caller-local preprocessing. The node still performs
ordinary Chat, so introducing a retrieval capability would falsely give runtime
eligibility and routing a provider/network meaning.

### Local-only source-grounded execution

Rejected. It would add a new routing exception even though the existing trusted
static remote boundary can carry a dedicated normalized request. The remote
privacy consequence is explicit, and the remote receives no provider authority.

## Trade-offs

This proposal introduces one concrete third-party dependency at the operational
level: a Tavily account and API key, query disclosure, network availability,
provider lifecycle, and credit costs. It also introduces a new explicit request,
result, internal envelope, source validation, and projection contract.

Those costs are deliberate. They keep external authority at one caller edge,
make privacy visible, avoid arbitrary destination access and hidden prompting,
preserve ordinary capability routing, and refuse provider frameworks, tools,
retrieval loops, caching, and persistent state.

## Impact and implementation boundary

If accepted, a separate implementation PR may add only the smallest vertical
slice necessary for this decision:

- the assisted native Chat option and direct HTTPX Tavily client;
- the fixed request, isolation, bounds, normalization, and safe failures;
- source-grounded public request/result models and `/v1/chat/external` route;
- core projection, local execution, strict remote envelope, receiver
  revalidation, and existing-Chat routing reuse;
- source-aware native output and focused tests; and
- privacy-safe proof material.

It must leave ordinary Chat, existing `/v1/chat`, OpenAI compatibility, browser
Chat, Aider, Code, Summarize, Classify, adapter APIs, capability declarations,
routing policy, topology, discovery, status, preflight, and default history
semantics unchanged. It must not add a provider SDK, second provider, generic
abstraction, cache, database, background worker, tool, browser, or agent.

The implementation proof must demonstrate: ordinary Chat unchanged and makes no
provider call; missing key and every acquisition failure make no HAC model
request; one successful invocation makes exactly one fixed Tavily call and one
source-grounded Chat execution; result URLs are never fetched; credentials do
not cross any internal boundary; source bounds and validation are enforced;
local-first and declared-remote Chat routing are unchanged; a selected remote
receives normalized evidence but no provider authority; output separates
provenance from generated content; and no query, source, key, or raw response
is added to retained history or default logs.

## Open questions

- Can a simple supported mechanism establish a strict total Tavily-acquisition
  deadline in addition to the fixed 5-second connect/read inactivity limits?
  Current HTTPX evidence establishes the latter but not a strict total deadline.
  Until focused implementation evidence exists, no total-duration guarantee is
  made or implemented.

## Decision

Pending.
