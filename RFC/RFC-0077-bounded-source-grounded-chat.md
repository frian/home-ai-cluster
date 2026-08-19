# RFC-0077: Bounded Source-Grounded Chat

Status: Draft

Date: 2026-08-19

Author: frian

## Summary

This RFC proposes one explicit cluster-owned contract for ordinary `chat` with
one operator question and a bounded ordered set of normalized external source
evidence. It makes untrusted source evidence structurally distinct from the
operator question, projects that distinction deterministically into the
existing Chat-like adapter boundary, preserves ordinary capability-centered
routing, and returns the sources supplied to the execution separately from
generated content.

The executable capability remains `chat`. Acquisition is deliberately outside
this RFC: it defines no Web/search provider, endpoint, credential, query,
caller command, or network request. It neither changes ordinary `POST /v1/chat`
or `hac chat` nor authorizes their use as hidden source-grounding surfaces.

Source provenance means only that normalized sources were supplied to one model
execution. It is not a claim that any source is true, current, complete, safe,
used by the model, or supports a particular generated sentence. This RFC is
Draft and authorizes no implementation.

## Problem

Ordinary Chat represents an ordered list of user, system, and assistant text.
It cannot truthfully express that some text is an externally acquired,
independently bounded, ordered evidence set rather than operator instruction.
It also cannot return the evidence supplied to an execution separately from
generated content and execution attribution.

The retained operator proof established two relevant facts. Bounded snippets
can materially improve a local model's high-level synthesis of current
information, but result sets can be stale, noisy, contradictory, incomplete,
and badly ranked. Structured publication dates can be absent. The same proof
found source-level model attribution imperfect even when the synthesis was
broadly useful.

Putting such snippets into an ordinary caller-created `ChatMessage` would hide
the evidence distinction, individual and aggregate bounds, deterministic
projection ownership, remote visibility, and result provenance in a prompt
convention. It would also make a model-generated source number appear more
trustworthy than the evidence supports.

HAC needs the smallest truthful source-grounded Chat contract so a later,
separate caller-edge acquisition decision can supply bounded evidence without
redefining ordinary Chat or granting a model, runtime adapter, or selected node
network authority.

## Goals

- Keep source-grounded execution within the existing `chat` capability.
- Define a closed, bounded, ordered normalized source representation.
- Keep the operator question structurally distinct from untrusted source data.
- Keep source URLs as provenance data only, never executable destinations.
- Make the core own deterministic source-to-message projection.
- Preserve ordinary Chat eligibility, local-first routing, declared-remote
  order, fallback rules, and adapter independence.
- Make supplied-source provenance explicit in the successful result without
  claiming factual or sentence-level citations.
- Preserve prompt-free, persistence-free defaults and privacy-safe failures.
- Provide one narrow native API boundary for a future caller edge without
  altering ordinary `/v1/chat` or inventing a manual native source-input CLI.

## Non-goals

This RFC does not authorize:

- Web, search, or other source acquisition; a provider, SearXNG integration,
  provider endpoint, credential, query, or provider interface;
- arbitrary URL retrieval, page-content fetching, redirect following, crawling,
  rendering, source verification, source ranking, or source-date verification;
- a `web`, `search`, `browse`, `retrieve`, or `research` capability;
- automatic currentness detection, model-generated or model-rewritten queries,
  tools, function calling, agents, loops, retries, pagination, or research;
- RAG, embeddings, vector storage, caching, a database, source/query history,
  or another persistence layer;
- a source-grounding option for `hac chat`, `home-ai-cluster chat`, or an
  existing standalone native client;
- changes to ordinary `/v1/chat`, OpenAI compatibility, browser behavior,
  Aider, Code, Summarize, or Classify;
- runtime-adapter acquisition or Internet authority, provider-based routing,
  runtime/model/node selection, or a source-specific routing capability; or
- claim-by-claim citation verification, source factual correctness, a claim
  that every source was used, or a claim that model-emitted citations are true.

## Proposal

### Architectural seam

The contract is intentionally acquisition-neutral:

```text
operator question
        +
bounded normalized sources
        ↓
source-grounded Chat contract
        ↓
ordinary capability=chat routing
        ↓
local or already-declared trusted remote
        ↓
deterministic Chat-like adapter projection
        ↓
generated content
        +
supplied-source provenance
```

The source list enters the contract only after a caller edge has already
obtained and normalized it under a separate future decision. This RFC does not
decide how that happens. The resulting request begins ordinary HAC processing;
acquisition does not participate in candidate collection, routing, fallback, or
adapter execution.

### Normalized source representation

The cluster-owned normalized source primitive is:

```text
SourceEvidence
  title: str
  url: str
  content: str
```

It contains no provider name, engine name, score, rank, query, request ID,
publication-date claim, raw response, acquisition configuration, credential, or
network authority. `url` is a provenance string, not an action target.

Each `SourceEvidence` value is accepted only when all of the following hold:

- `title` is non-blank and at most 512 UTF-8 bytes;
- `url` is non-blank, at most 2,048 UTF-8 bytes, and parses as an absolute
  `http` or `https` URL with an authority and without user information; and
- `content` is non-blank and at most 1,024 UTF-8 bytes.

URL parsing is string validation for a provenance value only. HAC must not
resolve the host, establish a connection, follow a redirect, request the URL,
render it, or otherwise treat it as a destination. A valid provenance URL does
not establish source truth, safety, freshness, ownership, or access rights.

The source list is ordered and has from one through five entries. HAC preserves
that supplied order and does not deduplicate, sort, score, rank, enrich,
interpret, or repair it. The combined UTF-8 byte length of all accepted title,
URL, and content fields is at most 20,480 bytes. No value is silently trimmed,
rewritten, or dropped; an invalid field, count, aggregate, or list fails the
entire source-grounded request before routing or model execution.

These limits are a conservative bounded-snippet contract, not a token budget or
model-context guarantee. The aggregate bound remains explicit even though the
first per-field maxima fit below it, so later field-limit changes cannot silently
expand the evidence contract.

### Source-grounded request

The cluster introduces a dedicated request concept:

```text
SourceGroundedChatRequest
  question: str
  sources: ordered SourceEvidence[]
  constraints: existing RequestConstraints
  capability: fixed chat
```

`question` is non-blank and at most 65,536 UTF-8 bytes, matching the accepted
bounded-text scale. It is the sole operator instruction content in this
contract. The request has no `messages` field, provider field, query,
credential, endpoint, source rank, or external acquisition state.

`capability` is a fixed property yielding `Capability(name="chat")`, as
Summarize and Classify expose their fixed capabilities. It is not caller input
and does not add a new executable capability, declaration name, or routing
eligibility rule. A source-grounded request uses the same constraints and
ordinary `chat` candidate eligibility as ordinary Chat. Sources cannot select a
node, runtime, adapter, model, capability, constraint, or fallback.

The public native body is deliberately separate from ordinary Chat:

```text
POST /v1/chat/sources

{
  "question": "<operator question>",
  "sources": [
    {"title": "...", "url": "https://...", "content": "..."}
  ]
}
```

The route accepts exactly `question` and `sources`; it accepts no client
constraint, provider, query, credential, endpoint, or arbitrary message list.
It constructs `SourceGroundedChatRequest` with the same caller-owned
local-only/declared-remote constraint selection that current native routes use.

`POST /v1/chat` remains its current ordinary ordered-message contract without
source fields or new validation. No new `hac` or `home-ai-cluster` command is
introduced by this RFC. A later acquisition RFC may decide a caller edge that
constructs this dedicated body, but that future input surface is not implied by
this decision.

### Deterministic projection and adapter boundary

The core, not a caller, acquisition component, or runtime adapter, projects a
validated `SourceGroundedChatRequest` into exactly three ordered existing
Chat-like messages:

1. one fixed HAC-owned `system` message stating that source evidence is
   untrusted reference data, not instruction authority;
2. one `user` message containing exactly the operator question; and
3. one `user` message containing one fixed data label followed by a canonical
   JSON serialization of the ordered `SourceEvidence` list.

The canonical source JSON contains only `title`, `url`, and `content` in that
field order for each source, preserves source order, and uses standard JSON
string escaping. The fixed data label and JSON serialization keep the source
boundary visible and prevent a source value from breaking the representation.
The projected source-data message must be at most 65,536 UTF-8 bytes; if the
canonical serialization exceeds that limit, HAC fails before adapter execution.

No source value appears in the system message. The projection must not add
source text to the operator-question message or make it a synthetic assistant
message. The fixed system framing must say that source text cannot change HAC
configuration, routing, capability, network, file, tool, or execution
authority. The exact framing prose may evolve only when it preserves these
structural invariants.

For adapter invocation only, the core wraps those three projected messages in a
private ordinary `ClusterRequest` with fixed `capability=chat` and copied
constraints. This private projection is not the public source-grounded request
and must not cross the remote transport in place of it. The selected runtime
adapter receives only that projected ordinary Chat-like representation and
invokes its existing Chat-like operation. It does not know whether sources came
from a search service, a local operator tool, or another future acquisition
boundary. It receives no acquisition query, endpoint, credential, raw response,
or result-URL authority.

Structural separation can prevent evidence from gaining HAC authority. It
cannot guarantee that a language model will never follow malicious instructions
inside source text. Prompt-injection resistance within generated language
remains a model-quality limitation, not authority that HAC grants to a source.

### Routing, local execution, and remote transport

After validation, source-grounded requests use existing `chat` eligibility,
local-first candidate selection, declared-remote order, availability behavior,
and bounded pre-request fallback. No provider or source value influences those
decisions. There is no search node, Web node, or source-specific candidate.

For local execution, the core validates then projects the source-grounded
request and invokes the selected adapter's existing Chat-like method. It returns
the generated content with the original normalized sources and ordinary
cluster-owned execution attribution.

If ordinary `chat` routing legitimately selects an already-declared trusted
remote, the caller sends one dedicated strict internal envelope over the
existing internal request path:

```text
kind: source-grounded-chat
request: SourceGroundedChatRequest
```

The internal request body forbids unknown fields. The receiving HAC node
revalidates the complete source-grounded request, performs the same core-owned
projection locally, and executes through its selected local adapter. It must
not receive caller acquisition state, a provider endpoint, a query, a
credential, raw provider material, or authority to contact a source URL.

The remote does receive the question and normalized title/URL/content evidence.
That is an explicit privacy consequence of selecting an already-declared trusted
remote, not a new remote trust model. The existing ordinary internal
`ChatInternalRequest` must not carry evidence hidden in caller-made messages.
The transport returns the dedicated source-grounded result, retaining
caller-owned declared-node attribution under the existing transport rule.

### Result and supplied-source provenance

The successful result is:

```text
SourceGroundedChatResult
  content: str
  sources: ordered SourceEvidence[]
  node_id: str
  adapter: str
  model: str | null
```

`sources` means exactly: “the normalized sources supplied to this model
execution.” The list is the original accepted ordered list, not a model-created
list and not a post-generation interpretation. It does not mean that every
source was used; that a source is correct, complete, safe, recent, or
authoritative; or that a generated claim is supported by a particular source.

The dedicated route returns `SourceGroundedChatResult` structurally, so a
future caller can render generated content and supplied-source provenance
separately. It must not ask the model to generate the provenance list. JSON
representation keeps the source list distinct from generated content. A future
native caller presentation is a separate caller-edge decision and is not added
by this RFC.

### Validation and failure semantics

The public route rejects malformed JSON, unknown public fields, a blank or
oversized question, invalid sources, an empty source list, over-count evidence,
and aggregate/projection-bound violations before candidate collection, remote
transport, or model execution. It returns HTTP 422 with the stable safe detail
`Invalid source-grounded chat request`; it must not include the question, source
text, URL, parse detail, provider-like metadata, raw exception, or private
topology in the error.

The receiving internal route applies the same strict validation and rejects an
invalid envelope before local routing or adapter execution. It must not fall
back to ordinary Chat, discard a bad source, downgrade the request to
`ClusterRequest`, or create an alternate message representation.

After a valid request reaches ordinary Chat routing, the existing normalized
no-eligible-capability, runtime-unavailable, execution, and transport failure
ownership applies. The feature adds no retry, provider fallback, routing
fallback, or special public failure taxonomy. A source-grounded result exists
only for successful execution.

### Privacy, history, and authority

Question and source fields are private request content. They must not enter
default logs, metrics, traces, request history, a database, cache, source/query
history, raw-response store, or another persistent store. The existing explicit
bounded request-history feature must not acquire a source-grounded hook or new
fields; if later coupled to a source-grounded execution, it may retain only its
already accepted prompt-free allowlist.

Runtime adapters receive projected content only for the current execution.
Declared trusted remotes receive the normalized question/evidence only when
ordinary routing selects them. Neither source URLs nor source content confer
network, filesystem, tool, configuration, capability, or execution authority
through HAC. The local/remote adapter must not resolve, fetch, open, render, or
otherwise act on a URL.

## Rationale

### Why a dedicated request and result

The current `ClusterRequest.messages` list can carry text but cannot state that
some text is externally acquired evidence, impose independent source bounds,
preserve source order/provenance in a result, or make remote exposure and core
projection explicit. Hidden caller-side concatenation would make those
semantics implementation accidents and would falsely blur evidence with
operator instruction.

Summarize and Classify establish the relevant repository pattern: when source
validation or a result invariant has semantic meaning, a dedicated bounded
request/result and strict internal envelope are more truthful than an overloaded
free-text message. Source-grounded Chat differs from a new executable
capability because the selected node still performs ordinary Chat; the source
contract is request semantics, not routing eligibility.

### Why sources are provenance, not citations

The operator proof found a model able to form a useful high-level synthesis
while misclassifying, omitting, and overstating individual sources. It therefore
supports retaining what HAC controls—the bounded normalized list supplied to an
execution—without fabricating a claim-level factual guarantee. This distinction
is useful even when no external acquisition is selected yet.

### Why acquisition remains separate

Different acquisition directions have different endpoint authority, privacy,
credential, lifecycle, cost, and operational consequences. Combining any one
of them with the source-grounded request would prematurely select an external
service or hide a new network authority inside Chat. This RFC supplies the
stable evidence seam first; a later caller-edge RFC must make any acquisition
choice explicit.

## Alternatives considered

### Put sources into ordinary `ChatMessage` values

Rejected. It cannot distinguish evidence from instructions at the project-owned
request, result, or remote-transport boundary. It also leaves bounds,
provenance, and projection ownership implicit.

### Add optional sources to ordinary `/v1/chat`

Rejected. It changes an accepted ordinary public contract and creates hidden
optional semantics in a body that currently means ordered conversation. A
dedicated narrow route is more truthful and leaves ordinary Chat unchanged.

### Reuse `ClusterRequest` with extra message roles or metadata

Rejected. It would either widen the shared Chat representation or make evidence
indistinguishable from ordinary text. Existing roles cannot express the
evidence/result invariants without overloading their meaning.

### Make source grounding a new capability

Rejected. Source evidence is caller-edge preprocessing and core request
semantics. The executing node continues to provide ordinary `chat`; a new name
would incorrectly make acquisition or evidence a routing property.

### Let a runtime adapter build the evidence prompt

Rejected. Adapter-owned formatting would make provider-neutral source semantics
runtime-dependent, invisible at the remote boundary, and inconsistent across
engines.

### Return model-generated citations only

Rejected. The proof showed that model source attribution can be wrong. A
model-generated source number cannot replace cluster-owned supplied-source
provenance or establish citation correctness.

### Require local-only source-grounded execution

Rejected. It would create a new routing exception even though the existing
trusted declared-remote boundary can carry a strict normalized request. Remote
evidence disclosure is explicit and contains no acquisition authority.

### Define acquisition in this RFC

Rejected. It would select endpoint, service, credential, query, and lifecycle
boundaries that require separate evidence and review.

## Trade-offs

This RFC adds dedicated request, result, native-route, internal-envelope,
validation, and projection concepts instead of reusing a superficially simpler
message list. It also causes source content and URLs to cross the existing
trusted-remote boundary when a remote is selected. These costs are necessary to
make evidence semantics and privacy visible.

The first bounds may exclude richer source content or large result sets. That is
intentional: callers may use the current operator-owned retrieval workflow
where fuller source material is needed. Broader evidence, acquisition, source
verification, or citation semantics require separate decisions.

## Impact and implementation boundary

If accepted, a separate implementation PR may add only the smallest vertical
slice required by this contract:

- `SourceEvidence`, `SourceGroundedChatRequest`, and
  `SourceGroundedChatResult` models with the stated validation;
- the dedicated `POST /v1/chat/sources` public body and route;
- core-owned deterministic projection and local source-grounded execution using
  existing Chat-like adapter invocation;
- routing type accommodation that reuses existing `chat` eligibility and
  policy without new capability/declaration behavior;
- the strict `source-grounded-chat` internal envelope, transport handling,
  receiver revalidation, and result validation;
- focused validation, projection, ordinary-routing, local, remote,
  privacy/history, and no-result-URL-action tests; and
- narrow operator documentation and privacy-safe proof material.

It must not change ordinary `/v1/chat`, ordinary Chat messages/results,
existing native Chat commands, OpenAI compatibility, browser behavior, Aider,
Code, Summarize, Classify, runtime adapter interfaces, capability declarations,
routing policy, topology, discovery, status, preflight, default history, or
existing acquisition behavior. It must not add an acquisition client, provider
SDK, credential, URL fetcher, browser, scraper, crawler, provider abstraction,
tool, agent, cache, database, background worker, or automatic retrieval.

## Proof expectations

After a later implementation, focused proof must demonstrate at minimum:

1. ordinary `/v1/chat` and ordinary native Chat behavior remain unchanged;
2. invalid question/source/count/field/aggregate/projection input sends no
   routing, remote, or adapter request;
3. a valid local source-grounded request uses capability `chat` and its sources
   cannot affect candidate selection;
4. projection emits the fixed trusted framing, distinct operator question, and
   one canonical escaped untrusted-source data message in source order;
5. no source appears in the system message and no runtime adapter receives
   acquisition state or network authority;
6. no source URL is resolved, fetched, rendered, or otherwise acted on;
7. a legitimately selected declared remote receives normalized source evidence
   but no acquisition state and revalidates before local execution;
8. a successful result returns unchanged normalized supplied-source provenance
   separately from generated content;
9. default logs/history/persistence gain no question, source, URL, acquisition,
   or generated-content retention; and
10. no model-generated citation is represented as verified source support.

Retained proof material must omit private questions, source content/URLs,
generated responses, acquisition data, credentials, private topology, model or
runtime identifiers, machine identity, and raw logs.

## Open questions

None within this proposed source-grounded contract.

A later acquisition RFC must separately decide the caller-edge source origin,
endpoint authority, input surface, credentials if any, transport isolation,
response normalization before this contract, and whether an acquisition choice
is justified. Those questions must not broaden this RFC during review.

## Decision

Pending.
