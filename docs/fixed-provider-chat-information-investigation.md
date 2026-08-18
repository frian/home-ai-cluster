# Fixed-Provider Chat Information Investigation

Status: Complete

## Question

> What is the smallest truthful architecture by which one explicit Chat request
> could use a bounded set of current external facts from one fixed provider,
> while keeping acquisition caller-local, preserving ordinary capability
> routing, retaining source provenance, and giving neither the model nor runtime
> adapter Internet authority?

This is a documentation-only investigation. It does not authorize an
implementation, an RFC, a provider selection, a dependency, a capability,
network access, automatic retrieval, a tool framework, or a change to current
runtime, routing, request, or result behavior.

## Outcome

**Outcome B — the evidence is sufficient to justify drafting one narrowly
scoped RFC for explicit fixed-provider-assisted Chat.**

The evidence does not authorize implementation. It establishes two facts that a
future RFC, rather than a hidden prompt convention, must decide together:

1. a fixed authenticated information-provider endpoint can return one bounded
   set of result metadata and snippets for one explicit query without HAC
   following arbitrary result URLs; and
2. current Chat cannot truthfully distinguish acquired evidence from ordinary
   message text or return that evidence's provenance separately from generated
   content and execution attribution.

The smallest RFC question is approximately:

> Should Home AI Cluster support one explicit caller-local fixed-provider
> information acquisition followed by one bounded source-grounded ordinary Chat
> request, with no model/network authority, no result-URL fetching, and no
> automatic retrieval?

It must remain a single vertical boundary, not a generic provider abstraction
or a `web`, `search`, `browse`, `research`, or `retrieve` capability.

## Scope and non-goals

This investigation considers two linked boundaries only:

1. **Acquisition:** one explicit, caller-local request to one
   project/operator-selected provider endpoint; and
2. **Chat evidence:** one normalized bounded set of provider results supplied
   to ordinary `chat`, with source provenance available outside generated text.

It does not design invocation syntax, select a provider, select byte limits,
add an endpoint, define a schema, or decide provider configuration or secret
storage. It does not permit provider result URLs to be fetched by HAC, a model,
a runtime adapter, or a selected execution node.

The following remain out of scope: automatic currentness detection,
model-generated queries, provider-query rewriting, tool/function calling,
retries, pagination, follow-up searches, search loops, background work,
crawling, browser execution, caches, databases, persistence, RAG, and agents.

## Current main baseline

This investigation reviewed GitHub `main` at commit
`8e26cd3d34cea8421316a0797732396260524c78`.

### Current Chat contract

`chat` is an existing executable capability. The native `hac chat` command
accepts exactly one non-blank operator message and constructs exactly one user
`ChatMessage`; its native body carries that one message and `capability: chat`.

`ClusterRequest` contains an ordered non-empty list of `ChatMessage` values, a
capability, and constraints. Chat has no dedicated external-source field,
source count or evidence-byte limit, or source provenance contract. The
only aggregate message byte limit is the separate accepted `code` rule; it
does not apply to ordinary Chat.

The public `/v1/chat` route reconstructs `ClusterRequest` from ordered
messages and the requested capability. `ClusterResult` contains generated
content plus adapter, optional model, and `node_id` execution metadata; it
contains no source metadata or citation field. The native default, verbose, and
JSON output project those fields only.

Summarize and Classify have dedicated bounded source-text request types. Their
existence does not make arbitrary extra Chat messages a truthful source-grounded
contract. In particular, Classify's dedicated request/result and closed remote
envelope show that a semantic field requiring validation and a structural result
invariant needs an explicit cluster-owned boundary rather than prompt text by
analogy.

### Execution, routing, and transport

The current adapters execute normalized requests against their configured local
runtime endpoints. They do not receive provider credentials, perform search,
or fetch arbitrary Internet material. Static routing remains capability-centered
and local-first; it selects an existing `chat` candidate and must not select an
Internet egress node.

For declared remote Chat execution, the closed `ChatInternalRequest` envelope
serializes the normalized `ClusterRequest` to the selected remote HAC node. If
a future source-grounded request crosses that boundary, the remote node would
receive the question and normalized evidence—including source URLs and
snippets—not provider credentials or acquisition mechanics. That privacy and
transport consequence needs an explicit RFC decision.

### Existing external-information boundary

RFC-0064 is Rejected. Its arbitrary caller-selected public URL design could not
prove that hostname validation controlled the actual connected public peer while
preserving ordinary hostname, HTTPS certificate, and SNI semantics. The
literal-public-IP/text-only narrowing was also rejected as too limited for
ordinary value. Arbitrary public-URL retrieval remains blocked.

The merged post-RFC-0064 investigation records a fixed-provider boundary as a
technically credible future candidate. That Outcome C did not authorize this
investigation, an RFC, or implementation. It did establish the important
distinction: a fixed provider accepts a query at a project/operator-selected
destination, rather than letting a caller select HAC's network destination.

## Part A — fixed-provider acquisition evidence

### The bounded acquisition shape

The smallest credible direction is:

```text
explicit operator action and explicit provider query
  -> one caller-local request to one fixed provider endpoint
  -> one bounded structured provider response
  -> locally normalized evidence
  -> one ordinary Chat execution
```

The provider may itself index, rank, or obtain public information. HAC's only
network request in this shape is to the fixed provider endpoint. Returned URLs
are provenance data, not network instructions:

```text
provider search response             -> accepted
HAC follows a returned result URL    -> forbidden
```

This materially reduces the specific caller-controlled-destination and
connected-peer problem that blocked RFC-0064. It does not remove the need for a
fixed endpoint/credential policy, finite HTTP and response bounds, explicit
privacy consent, or validation of untrusted provider output.

### Representative official API evidence

Two current APIs are sufficient to show the architectural facts; neither is a
recommendation or a candidate selection.

| Representative API | Boundary-relevant documented facts | Consequence for a future RFC |
| --- | --- | --- |
| [Tavily Search](https://docs.tavily.com/documentation/api-reference/endpoint/search) | A `POST /search` request needs a bearer API key and a required query. Its response has ranked results with title, URL, content, and score; its result-count option affects response size. It can optionally return provider-generated answers and raw content, and documents usage credits. | Credentials, response/result bounds, cost handling, and an explicit choice of raw results rather than a provider answer are architectural concerns. |
| [Exa Search](https://exa.ai/docs/reference/search) | A `POST /search` request needs an API key and a required query. It documents a configurable 1–100 result count and result title, URL, published date, author, text/highlights. It also exposes synthesized output and cost fields. | A bounded result count and provenance fields are practical, but the future contract must reject provider-specific rich fields it does not need and avoid outsourcing answer synthesis. |

Both examples use one fixed API endpoint and authenticate the caller. Their
responses can include source URLs and text-like snippets without requiring HAC
to connect to those URLs. Their richer options also demonstrate why a first
increment needs a deliberately closed request and result subset.

### Raw results are smaller than provider-generated answers

Provider-returned search results/snippets and a provider-generated answer are
different products:

- **Raw bounded results** keep current-information acquisition separate from
  local Chat reasoning. HAC can normalize only a finite ordered subset of
  title, URL, and snippet/content.
- **A provider-generated answer** asks the provider to synthesize or reason as
  well as acquire information. It can obscure what was actually supplied to
  local Chat, adds a second answer authority, and weakens the local-first value
  of using local inference.

The smaller future candidate should therefore evaluate raw bounded results.
This does not claim that snippets are factually correct, complete, fresh, or
free of ranking bias.

### Privacy, authority, and credentials

Fixed-provider acquisition is an **explicit privacy exception** to ordinary
local-only Chat. A provider can learn at least the submitted query, ordinary
request and network metadata, and account/API-key identity where authentication
is used. Usage accounting can also associate requests with an account.

Two query choices have materially different disclosure boundaries:

```text
full original Chat message       -> provider
explicit operator search query   -> provider
```

Sending the full message is simpler but may disclose unrelated instructions,
personal context, or private data. A separately supplied operator query makes
the disclosure visible and may be narrower, at the cost of an extra operator
step. No model may generate, rewrite, or choose the provider query in this
direction. A future RFC must select the explicit query boundary rather than
silently treating a Chat message as provider input.

Credentials must remain caller-local acquisition configuration. They must not
enter `ClusterRequest`, remote transport, runtime adapter calls, results,
ordinary logs, or default history. This investigation makes no secret-storage
or provider-configuration decision.

### Required finite envelope

The provider's result-count controls do not make the HAC boundary finite by
themselves. A future RFC must independently bound, before Chat routing:

- exactly one provider request per explicit operator action;
- a finite provider result count;
- title, URL/provenance, and text bytes for each accepted result;
- aggregate normalized evidence bytes;
- provider response bytes while reading;
- provider connect and read inactivity timeouts; and
- a total request lifetime only if a concrete enforceable mechanism is shown.

The first proof should exclude retries, pagination, provider follow-up calls,
result-URL fetches, and loops. It should also request only the provider fields
the normalized evidence requires. Content returned by the provider remains
untrusted even if it names a known public URL.

## Part B — Chat evidence and result boundary

### Candidate 1: caller-side prompt concatenation

Putting source labels, URLs, and snippets into ordinary `ClusterRequest.messages`
would reuse a representation that can encode the text, but it does not create a
truthful contract. It leaves source/evidence distinction, formatting ownership,
individual and aggregate bounds, source count, remote visibility, and result
provenance unspecified. It also makes prompt injection look like ordinary
operator text, lets acquired source data disappear from the result, and makes
tests depend on an implicit prompt convention and model behavior.

This candidate is not a defensible first project-owned boundary merely because
the existing message list can carry arbitrary strings.

### Candidate 2: explicit source-grounded Chat request

An explicit source-grounded request is the truthful future direction. It would
remain executable `chat`: external acquisition is caller-local preprocessing,
not a new runtime capability. Conceptually, a future request would contain a
question and a finite ordered collection of normalized evidence entries with
optional title, source URL, and content. This investigation does not propose a
field name or schema.

Such a contract would let an RFC decide all of the following explicitly:

- a finite source count, individual field limits, and aggregate evidence limit;
- the minimally useful provenance fields and their strict validation;
- deterministic, cluster-owned conversion of question and untrusted evidence
  into runtime-specific ordered chat messages;
- receiver validation and the precise closed internal envelope if a declared
  remote executes Chat;
- whether remote execution is allowed to receive source metadata and content,
  while never receiving provider credentials or acquisition authority; and
- a result that presents generated content and the normalized supplied-source
  metadata separately.

The runtime adapter need not know that evidence came from the Internet. It can
receive the cluster-owned ordinary messages after the core's deterministic
projection. That is different from hiding the projection in a caller: the
request and result preserve the evidence semantics at the core/transport
boundary, while provider selection, HTTP, and credentials remain outside the
adapter.

This is a new request/result and transport question, but not a new executable
capability. It is justified because the evidence semantics, bounds, provenance,
and remote trust boundary cannot be represented by current ordinary Chat text
without losing their meaning.

### Candidate 3: preprocessing-only evidence document

A caller-local component could create a text document and require the operator
to feed it into ordinary Chat manually. That preserves the current no-provenance
Chat contract, but largely recreates today’s operator-owned retrieval workflow
with an additional provider step. It does not reliably show which evidence was
actually supplied to a resulting answer, and it does not solve the hidden
prompt-construction issue if HAC assembles the document itself.

It is useful as an operator-owned workflow outside HAC, but not sufficient as a
project-owned fixed-provider-assisted Chat contract.

### Provenance is not factual citation

The smallest truthful result can structurally retain provenance:

```text
generated content
+ the normalized external sources supplied to this Chat execution
```

This says only that the listed sources were supplied to the model. It does not
claim that a sentence in generated content is supported by a particular URL,
that the provider snippet is correct, or that the model used every source.
Sentence-level factual citations require model cooperation and validation not
established here. Source/query/evidence persistence, history, and caching are
not required and must remain disabled by default.

### Untrusted evidence and prompt injection

Provider result text may contain instructions such as “ignore previous
instructions,” requests to reveal secrets, or links to contact. The source is
not a principal and has no authority.

An explicit source-grounded contract can structurally guarantee that evidence:

- cannot cause a second provider call or a result-URL request;
- cannot invoke a tool, change configuration, access files, execute code, or
  mutate persistent state, because none is exposed by the first boundary;
- cannot select a node, change the `chat` capability, alter constraints, or
  affect routing; and
- cannot disclose credentials, which remain outside normalized evidence and
  remote/runtime messages.

It cannot guarantee that a particular model, especially a small local model,
will not follow malicious text in its generated answer. Deterministic source
separation and a cluster-owned message projection make the boundary inspectable
and testable, but prompt-injection resistance within language generation remains
a model-quality risk. The RFC must not promise otherwise.

## Routing and local-first interpretation

The following separation is defensible:

```text
external information acquisition  -> caller-local preprocessing
ordinary Chat                     -> existing capability-centered execution
```

Acquisition completes before candidate collection and routing. The selected
node receives only the accepted normalized source-grounded request, if a future
RFC permits remote execution; it neither sees provider credentials nor performs
provider HTTP. Route selection therefore cannot change the Internet egress
identity or expose different provider-reachable resources.

This remains compatible with local-first principles only as an explicit opt-in:
ordinary Chat continues to operate without an account, provider, or Internet
connection; no request leaves the local machine unless the operator asks for
external information; ordinary inference stays local or follows existing
explicit trusted-remote routing; and the provider supplies information, not
inference. Any future RFC must make this exception visible and must preserve the
default local-only path.

## RFC boundary and open decisions

The evidence supports drafting an RFC, not deciding it here. That RFC must at
minimum decide:

- one explicit caller-local action and whether the provider query is separately
  operator-supplied;
- one fixed provider endpoint and credential/configuration ownership, without a
  generic provider layer;
- raw bounded result entries rather than provider-generated answers;
- exactly one provider call, no retries/pagination/follow-up searches, and no
  result-URL fetching;
- independent network, response, result-field, source-count, and aggregate
  evidence bounds;
- the exact source-grounded Chat request, result provenance, public surface,
  internal remote envelope, and receiver validation;
- deterministic untrusted-evidence message projection, remote visibility, and
  privacy-safe failure behavior; and
- no default retention of query, result, evidence, prompt, or response.

It must not add a provider recommendation, a general provider interface,
automatic retrieval, model-directed action, a new retrieval capability, runtime
adapter Internet access, routing changes, citation-correctness claims, or a
browser/crawler/agent system.

## Decision

**Outcome B — draft the narrowly scoped RFC before any implementation.**

Fixed-provider acquisition is materially safer than arbitrary public-URL
fetching with respect to HAC's destination authority, and real APIs establish
that one authenticated query can return a finite result set with provenance
fields. The current Chat contract, however, has no truthful way to carry those
sources or return their provenance. An explicit source-grounded ordinary Chat
contract is therefore the smallest candidate worth deciding in an RFC.

Until such an RFC is accepted and separately implemented, operator-owned
retrieval followed by existing local text/file/stdin or ordinary Chat input
remains the supported workflow. RFC-0064 remains Rejected and arbitrary
public-URL retrieval remains blocked.
