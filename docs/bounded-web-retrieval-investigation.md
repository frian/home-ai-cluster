# Bounded Web Retrieval Investigation

Status: Complete

## Question

> What is the smallest truthful way Home AI Cluster could retrieve public web
> content for one explicit request without making Internet access implicit or
> turning the project into a browser, search engine, tool platform, or agent
> framework?

This is a documentation-only investigation. It records evidence and recommends a
future RFC boundary. It does not authorize implementation, add a capability,
change an endpoint, permit network access, or modify the accepted loopback web
client.

## Current Baseline

Home AI Cluster currently executes three cluster-owned capabilities:

- `chat` through `ClusterRequest`;
- `summarize` through one bounded source text;
- `classify` through one bounded source text and an ordered caller-supplied label
  set.

The existing runtime and remote boundaries execute normalized requests. They do
not retrieve source material, discover URLs, search the web, browse pages, or
run tools. `summarize` and `classify` bound source text to 65,536 UTF-8 bytes
before execution. The current loopback browser client calls only the existing
same-origin native routes and adds no generic proxy or upload path.

The accepted privacy default remains that request contents do not leave the
local cluster unless explicitly allowed. Current ordinary runtime execution may
cross an explicitly declared trusted-LAN boundary, but it does not contact
arbitrary Internet destinations on behalf of a request.

Relevant current boundaries include:

- [`models.py`](../src/home_ai_cluster/core/models.py);
- [RFC-0051](../RFC/RFC-0051-bounded-text-summarization.md);
- [RFC-0061](../RFC/RFC-0061-bounded-text-classification.md);
- [RFC-0062](../RFC/RFC-0062-minimal-loopback-web-client.md);
- [RFC-0063](../RFC/RFC-0063-classify-local-text-file-input.md);
- [the retained loopback web client proof](loopback-web-client-proof.md).

The retained browser proof explicitly excludes web research, tools, arbitrary
static-file serving, background requests, and LAN browser access. That exclusion
is descriptive of the current system, not evidence that a future retrieval
feature is justified.

## Why Retrieval Is Architecturally Different

Retrieval is not only another prompt shape.

A retrieval operation would give Home AI Cluster a new authority:

```text
operator request
  -> project-owned outbound network access
  -> untrusted remote response
  -> bounded local representation
  -> existing or new executable capability
```

That authority affects:

- privacy, because the destination can observe the caller's network request;
- security, because a supplied URL can target loopback, private LAN services,
  link-local services, or other non-public resources;
- resource ownership, because downloads can be large, slow, compressed, or
  indefinitely streamed;
- truthfulness, because HTML extraction and source attribution are not model
  execution concerns;
- failure semantics, because DNS, connection, redirect, status, media type,
  decoding, and size failures occur before inference;
- topology, because retrieval on the caller and retrieval on a selected remote
  expose different network identities and trust boundaries.

These are architectural decisions. They cannot be introduced as a small browser
button or hidden adapter helper.

## External Security Evidence

Python's URL parsing documentation warns that `urlsplit()` and related functions
do not perform validation and that callers must defensively verify parsed
components before using them for security-sensitive operations:

- <https://docs.python.org/3/library/urllib.parse.html#url-parsing-security>

OWASP describes server-side request forgery as the risk created when an
application fetches a user-controlled destination. Its prevention guidance
specifically warns about URL parser ambiguity, redirects, DNS pinning or
rebinding, and access to internal resources:

- <https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html>
- <https://owasp.org/www-community/attacks/Server_Side_Request_Forgery>

Python's `ipaddress` module exposes classifications such as loopback, private,
link-local, multicast, and unspecified addresses, but those classifications are
only part of a complete network policy. A hostname can resolve to more than one
address, and redirect targets require the same validation as the original
request:

- <https://docs.python.org/3/library/ipaddress.html>

This evidence supports one conclusion: accepting an arbitrary URL and passing it
directly to the existing HTTP client would not be a small implementation detail.

## Candidate A — Operator-Owned Retrieval

The operator retrieves content outside Home AI Cluster and supplies bounded text
through an existing input path.

Examples include:

```text
curl or browser
  -> operator review
  -> pasted text or local UTF-8 file
  -> summarize, classify, or chat
```

### Advantages

- no new Home AI Cluster network authority;
- no SSRF boundary;
- no redirect, DNS, media-type, or HTML-extraction contract;
- the operator can inspect and edit the source before submission;
- existing bounded text paths remain usable;
- no RFC or implementation is required to continue this workflow.

### Limitations

- manual copying remains necessary;
- provenance is not carried through the request;
- Chat has no dedicated bounded source-text request shape;
- the operator must choose what content to retain and remove.

This is the current safe baseline. It is not an implementation proposal.

## Candidate B — One Explicit Public URL Retrieval

Home AI Cluster would accept exactly one operator-supplied public `http` or
`https` URL for one explicit invocation. The retrieval would complete before
model execution and would produce one bounded plain-text source plus minimal
source attribution.

An approximate conceptual flow is:

```text
explicit operator URL
  -> local validation
  -> one bounded public HTTP retrieval
  -> bounded text extraction
  -> one normalized execution request
  -> result with minimal source attribution
```

This is the smallest credible project-owned retrieval shape, but it still
requires an RFC.

### Decisions a Future RFC Must Own

#### Invocation boundary

The RFC must decide whether retrieval belongs to:

- a new one-shot operator command;
- a new native endpoint;
- a new capability-specific request;
- or an explicit preprocessing command that outputs text without invoking a
  model.

Adding it first to the loopback browser client would be backwards. The browser
must not define the architecture.

#### Network ownership

The RFC must choose where retrieval occurs.

Caller-local retrieval is the narrowest and most understandable first boundary.
Retrieval on the selected execution node would make route selection change the
network identity, reachable resources, privacy exposure, and observed source.
Remote retrieval should therefore remain excluded from the first proof.

#### Destination policy

The first boundary would need at least:

- only explicit `http` and `https` schemes;
- no credentials or user information in URLs;
- no loopback, private, link-local, multicast, unspecified, or otherwise
  non-public resolved address;
- validation of every resolved address before connection;
- no automatic proxy inheritance unless explicitly decided;
- no authorization headers, cookies, client certificates, or ambient browser
  session state;
- no access to local files or non-HTTP schemes.

A hostname allowlist would be safer than arbitrary public URLs but would make the
first feature useful only for preconfigured domains and introduce a retained
configuration contract. The investigation does not recommend that broader
configuration step now.

#### Redirect policy

Automatic redirects create a second destination decision and can bypass an
initial validation. The smallest first rule is therefore:

> Do not follow redirects.

A future RFC may instead allow a very small redirect count only if every target
is parsed, resolved, and validated independently before connection. That is more
complex and is not required for a first useful proof.

#### Download bounds

The operation needs independent finite bounds for:

- connection and response time;
- maximum response bytes after transfer decoding;
- maximum redirect count, preferably zero initially;
- accepted media types;
- accepted text encoding;
- extracted text size.

A `Content-Length` header cannot be the only size control because it may be
missing, incorrect, or describe encoded rather than decoded content. The client
would need to stop reading when the accepted byte bound is exceeded.

The existing 65,536-byte source bound is useful evidence but does not directly
settle the download bound. HTML and extraction overhead may require a larger
transport limit before producing a 65,536-byte normalized source.

#### Content handling

The first proof should not claim general web-page understanding.

The smallest honest accepted types are likely:

- `text/plain` decoded as strict UTF-8;
- optionally `text/html` only if one deterministic, dependency-conscious text
  extraction rule is accepted.

HTML extraction is not equivalent to rendering. It does not execute JavaScript,
apply CSS, wait for dynamic content, authenticate, accept consent banners, or
reproduce a human browser view. Adding a headless browser would be a different
and much larger architecture.

The current investigation does not select an HTML parser or extraction
algorithm. That implementation-specific evidence should be gathered before an
RFC commits to HTML support. A text/plain-only first proof is smaller but may be
too limited for ordinary web pages.

#### Source attribution

The minimum useful attribution is probably the normalized requested URL returned
alongside the result. That is still a new result or presentation contract.

The first proof should not promise:

- factual citations;
- sentence-to-source mappings;
- quoted evidence offsets;
- search-result ranking;
- canonical URL discovery;
- page titles or authors;
- archived copies;
- freshness guarantees.

One URL proves provenance of the retrieved input, not correctness of the model's
answer.

#### Privacy and retention

The operation should be explicit and disabled by default. Documentation must
state that the destination learns at least the caller's network address and
ordinary HTTP request metadata.

The first proof should add no:

- retrieval history;
- cache;
- cookies;
- persistent content store;
- browser storage;
- automatic reuse;
- prompt or response logging;
- retained raw response.

Ordinary safe errors must not expose private addresses, DNS answers, raw response
content, authorization values, or transport exceptions.

### Assessment

Candidate B is useful and can remain bounded, local-first, and understandable.
It is nevertheless a new network, privacy, security, input, attribution, and
failure contract. It requires an accepted RFC before implementation.

## Candidate C — Search and Multi-Source Retrieval

This candidate accepts a query, contacts a search provider, selects results,
retrieves multiple pages, combines sources, and asks a runtime to answer.

It immediately creates decisions about:

- search provider and API ownership;
- credentials and external services;
- query privacy;
- result ranking;
- number of sources;
- duplicate and conflicting sources;
- per-source and total limits;
- citations and attribution;
- partial failures;
- retries and rate limits;
- provider-independent abstractions;
- local versus remote retrieval placement.

This is not the next small increment. It would also violate the preference to
avoid provider abstractions before one concrete bounded retrieval path exists.

## Candidate D — General Tool Calling or Autonomous Browsing

This candidate lets a model choose URLs, issue repeated requests, follow links,
run tools, or decide when enough information has been collected.

It requires a tool protocol, authority model, execution loop, stopping policy,
resource accounting, untrusted-content handling, prompt-injection policy,
partial-result semantics, and auditable action history. It would make the model
an actor with network authority rather than keep the operator as the explicit
authority owner.

This is far outside the current architecture and should not be disguised as web
retrieval.

## Comparison

| Property | Operator-owned retrieval | One explicit URL | Search and multiple sources | Autonomous browsing |
| --- | --- | --- | --- | --- |
| Project-owned Internet access | No | Yes, once | Yes, multiple destinations | Yes, model-directed |
| New RFC required | No | Yes | Yes, broad | Yes, broad |
| New provider dependency | No | No | Likely | Not necessarily |
| SSRF boundary | No | Yes | Yes | Yes |
| New attribution contract | No | Minimal | Multi-source | Action and source history |
| New persistence required | No | No | No, but tempting | Usually becomes tempting |
| Operator authority remains explicit | Yes | Yes | Partly | No |
| Smallest credible next proof | Current baseline | Yes | No | No |

## Capability or Input Source

Web retrieval should not initially be modeled as a runtime capability.

A capability describes executable work a node can perform through a runtime
adapter. Retrieval is a caller-local input acquisition operation with a
separate network and security boundary. Calling it `web-research` would combine
source acquisition, search, synthesis, and model behavior into one vague
capability.

The first architectural question should instead be:

> Can one explicit caller-local retrieval operation produce one bounded source
> for an existing or narrowly defined execution request?

This preserves engine independence and prevents runtime adapters from owning URL
validation, HTTP behavior, extraction, or source attribution.

The exact downstream operation remains unresolved. Feeding retrieved text into
ordinary `chat` would require a bounded source-plus-question request contract or
would reduce retrieval to hidden prompt construction. Feeding it into
`summarize` is structurally smaller but proves only URL summarization, not web
research. The future RFC must select one truthful purpose rather than create a
generic retrieval-to-any-capability framework.

## Decision

**Outcome C — A narrow RFC is justified before implementation.**

The smallest credible project-owned increment is one explicit caller-local
retrieval of one public URL with finite network and content bounds, no automatic
redirects, no ambient credentials, no persistence, and no remote retrieval.

However, this investigation does not recommend implementing a generic
`web-research` capability or adding a web field to the current Chat page. The
future RFC must first decide the exact purpose and request boundary. The most
credible options are:

1. one bounded URL-to-text preprocessing operation with no model execution; or
2. one bounded URL summarization operation that feeds accepted extracted text
   into the existing `summarize` capability.

Option 2 provides clearer immediate user value and reuses an accepted bounded
source-text result contract, but it still adds URL attribution and retrieval
failure semantics. Option 1 keeps retrieval and inference maximally separate but
may be too low-level for ordinary users.

A general question-answer or Chat research flow should remain deferred until the
project has a first proven retrieval boundary and a separately accepted bounded
source-grounded request contract.

## Proposed RFC Boundary

The following is investigation guidance only, not an accepted contract.

A future RFC should decide:

- one explicit caller-local invocation surface;
- exactly one supplied `http` or `https` URL;
- whether the first purpose is URL-to-text or URL summarization;
- no remote-node retrieval;
- no search provider or query input;
- no model-directed URL selection;
- a closed public-destination policy with DNS and IP validation;
- zero redirects initially, or independently validated bounded redirects;
- finite connection, response, raw-byte, decoded-byte, and extracted-text
  bounds;
- accepted media types and strict decoding rules;
- the smallest deterministic text extraction behavior;
- minimal requested-URL attribution;
- stable privacy-safe failure categories;
- no cookies, ambient credentials, authorization forwarding, proxy magic,
  cache, history, persistence, polling, retries, or background work;
- focused tests using local controlled transports without contacting the public
  Internet;
- one explicit privacy-safe live proof against a harmless public source;
- no client-web implementation until the native/operator contract is accepted
  and proven.

## Required Follow-up

Draft and review a new RFC before implementation.

Before that RFC is finalized, perform one narrow implementation-spike or
library investigation only if needed to answer these unresolved facts:

- whether strict UTF-8 `text/plain` alone is useful enough for the first proof;
- the smallest acceptable standard-library or existing-dependency HTML text
  extraction path;
- how the selected HTTP client exposes peer-address, redirect, streaming-size,
  decoding, and proxy controls without adding a new dependency;
- which finite byte limits are practical while preserving the existing 65,536
  UTF-8-byte normalized source bound.

The spike must not be merged as user-facing behavior and must not establish
architecture by implementation.

## Deferred Work

This investigation does not authorize:

- a `web-research` capability;
- web search;
- search-provider integration;
- multiple-source synthesis;
- citations or evidence offsets;
- automatic redirects;
- arbitrary URL proxying;
- LAN, loopback, link-local, or private-resource retrieval;
- remote-node retrieval;
- JavaScript execution;
- headless browsing;
- cookies or authenticated sessions;
- tool calling;
- model-directed actions;
- agent loops;
- crawling;
- indexing;
- embeddings;
- vector storage;
- caching;
- persistence;
- history;
- retries;
- background polling;
- scheduling;
- dashboard or operator-console expansion;
- Docker or Kubernetes;
- compatibility API expansion;
- changes to existing Chat, Summarize, Classify, internal transport, routing,
  static capability declarations, runtime adapters, or loopback exposure.
