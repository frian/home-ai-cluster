# RFC-0064: Bounded Public URL Summarization

Status: Draft

Date: 2026-08-04

Author: frian

## Summary

This RFC proposes one explicit, caller-local hac summarize --url URL source. It
is a fourth mutually exclusive source for the existing native summarize command,
alongside --text, --file, and standard input. The command would retrieve one
public HTTP URL before constructing the existing bounded SummarizeRequest. The
existing capability-based routing then selects a local or explicitly declared
remote summarize execution candidate.

The selected runtime node receives only normalized bounded source text. It does
not receive the URL and does not access the Internet. This is input acquisition,
not a runtime capability, retrieval framework, or browser feature.

This Draft proposes an architectural boundary only. It authorizes no
implementation until accepted.

## Problem

An operator can already retrieve material outside Home AI Cluster and submit
text through --text, --file, or stdin. That safe workflow requires manual
copying. A project-owned fetch would add outbound network authority, untrusted
content, destination privacy, SSRF, resource, and attribution concerns.

Passing a URL to a runtime adapter or selected remote would make routing alter
network identity and reachable resources, and turn declared remotes into
implicit Internet gateways. This cannot be a prompt shape or implementation
convenience.

## Goals

This RFC proposes to:

* add one opt-in --url source to the existing native summarize command;
* keep retrieval caller-local and before normalized request routing;
* accept one explicit public HTTP or HTTPS URL only;
* establish public-destination, privacy, finite-resource, and safe-failure
  boundaries before inference;
* accept strict UTF-8 text/plain only for the first increment;
* preserve the existing 65,536 UTF-8-byte normalized summarize source limit;
* preserve summarize capability eligibility, local-first routing, remote
  transport, adapters, and cluster attribution; and
* present the normalized requested URL in the native command result layer
  without adding it to ClusterResult or the internal remote envelope.

## Non-goals

This RFC does not add:

* web-research, generic retrieval, a generic fetch command, Chat or Classify
  URL input, or a generic source abstraction;
* search providers, queries, multiple sources, crawling, indexing, embeddings,
  vector storage, caching, persistence, history, retries, polling, scheduling,
  or background work;
* model-directed URL selection, tool calling, autonomous browsing, JavaScript,
  a rendering engine, or external subresource retrieval;
* remote-node retrieval, node Internet permissions, or capability declaration
  changes;
* cookies, authentication, browser sessions, arbitrary request headers, or
  proxy configuration;
* HTML, PDF, image, binary, or document parsing;
* citations, evidence offsets, canonical URL discovery, titles, authors,
  publication dates, freshness guarantees, archived content, or multi-source
  attribution;
* a native endpoint, compatibility API, browser implementation, browser
  exposure change, dashboard, or operator-console expansion; or
* changes to existing --text, --file, or stdin behavior.

## Proposal

### Invocation and source ownership

hac summarize gains one --url URL option in the existing mutually exclusive
source group:

    --text TEXT | --file PATH | --url URL | stdin

Exactly one source is selected. As today, repeated values for one explicit
source and combinations of explicit sources are invalid. An explicit source
ignores stdin, and stdin is used only when no explicit source is present.
--url is opt-in and does not affect an invocation without it.

The caller-side native command acquires the URL, not the summarize endpoint, a
runtime adapter, the router, or a remote receiver:

    one explicit URL
      -> caller-local validation and bounded retrieval
      -> deterministic bounded text source
      -> existing SummarizeRequest(text=...)
      -> existing summarize routing
      -> local or declared-remote execution

The existing public endpoint continues to receive only its normalized text body.
The closed internal summarize envelope continues to contain only normalized text
and constraints. A selected remote receives neither URL nor retrieval metadata.

Retrieval is input acquisition rather than a runtime capability. Routing remains
based solely on summarize. Caller-local acquisition keeps fetched text identical
before routing, prevents route selection from changing the egress identity or
reachable resources, and prevents declared remotes from becoming hidden web
gateways. URL validation, HTTP behavior, and text handling do not belong in
runtime adapters.

### URL syntax boundary

One explicit absolute URL is required. The only accepted schemes are HTTP and
HTTPS. Validation rejects relative URLs, missing hosts, malformed or ambiguous
authorities, username/password user information, fragments, and every other
scheme, including file, ftp, data, and javascript.

Fragments are rejected rather than silently removed: they do not identify bytes
sent to an HTTP server, and silently changing the operator's input would obscure
the boundary. No domain allowlist, retained URL configuration, URL alias, or
operator-supplied header is introduced.

The request uses no credentials. Cookies, Authorization forwarding,
username/password URL credentials, client certificates, browser-session reuse,
ambient application credentials, .netrc or equivalent credential discovery, and
authenticated pages are forbidden. Any HTTP-required or fixed minimal ordinary
headers are client-owned implementation details and must carry no identity or
credentials. Arbitrary caller headers are not accepted. Automatic
proxy-environment inheritance is forbidden; proxy use needs a future RFC.

### Public-destination policy

URL parsing alone is not a safety decision. Before a connection, a literal IP
address or every address resolved for a hostname must be an ordinary public
Internet destination. The policy applies to IPv4 and IPv6 and rejects loopback,
private, link-local, multicast, unspecified, reserved, and every other
non-public special-purpose range.

For a hostname with multiple answers, one forbidden candidate makes the
destination forbidden. Resolved addresses are never included in ordinary
operator failures. A validation success is insufficient if the later connection
can use another address. The implementation must validate the connected peer
where the client/platform exposes it, or use a mechanism that preserves this
invariant:

> A validated hostname must not cause Home AI Cluster to connect to a
> non-public destination.

This covers DNS rebinding and resolution changes between validation and
connection. The RFC does not select a DNS-pinning or transport algorithm;
focused implementation evidence must show how the chosen client preserves this
invariant on supported platforms.

### Redirect, time, and resource boundaries

The first version does not follow redirects. A 3xx response is a normalized
redirect-refused retrieval failure. Every redirect would create a new destination
requiring independent parsing, resolution, connected-peer validation, privacy
review, time limits, and resource accounting. Redirect support is deferred to a
future RFC.

Retrieval owns separate finite bounds for DNS and connection work where
practically enforceable, response-header wait, body reading, and total retrieval
duration. It also owns independent limits for encoded/wire bytes,
decoded/decompressed bytes, extracted UTF-8 text, and the existing normalized
summarize source. The latter remains at most 65,536 UTF-8 bytes.

The native inference-client timeout is not a retrieval timeout and does not
govern these bounds. Content-Length is advisory only: it can be absent, false,
or describe encoded content. Reads must be bounded while streaming, and
compressed content must not expand past the decoded-byte bound.

The repository establishes the 65,536-byte source limit but supplies no
evidence for safe numeric DNS, transport, decompression, or total-retrieval
limits. This Draft proposes independently owned finite bounds, but leaves their
initial numeric values pending one narrow non-user-facing HTTP-client/library
spike before acceptance. The spike must not add a dependency or establish
user-facing behavior.

### Media type, decoding, and extraction

This Draft selects Option A: text/plain only. It is the smallest useful initial
boundary supported by the current dependency set: no HTML parser or rendering
dependency is present, while the project already has an HTTP client for bounded
native and remote calls. Accepted text/plain content is decoded as strict UTF-8,
with no character-set guessing.

The first increment has no HTML extraction. text/html, binary and document
formats, and unsupported media types fail safely. This avoids claiming that
arbitrary pages can become reliable article text and avoids choosing an HTML
parser, boilerplate policy, or browser engine without evidence.

A later HTML RFC would have to distinguish raw response bytes, decoded text, and
extracted text; exclude scripts and styles; define treatment of navigation and
boilerplate; retain finite limits at each stage; and make no browser-equivalence
claim. It must not execute JavaScript, CSS, or external subresource requests.

Retrieved text is untrusted operator-selected input. It can include misleading
instructions, prompt injection, hidden or boilerplate text, adversarial
repetition, and false claims. Bounded extraction does not solve prompt
injection. The normalized summarize request gives the runtime text to summarize,
not authority to alter project instructions, configuration, tools, or network
actions.

### Source presentation and failures

The normalized requested URL is caller-owned metadata. For a successful --url
invocation, the native command result layer presents it alongside the ordinary
summarize result and cluster-owned execution attribution. The URL is not added
to ClusterResult, the native endpoint, runtime-adapter calls, or the internal
remote envelope. Existing result fields remain unchanged; URL-specific human
and JSON presentation is an opt-in native-command contract.

This identifies the requested input only. It is not a verified citation, quoted
evidence, source offset, extracted-document identity, canonical URL, or
factual-grounding guarantee.

Retrieval failures are distinct from existing summarize routing and inference
failures. The command must use stable, privacy-safe categories for invalid URL,
forbidden destination, name-resolution failure, connection failure, retrieval
timeout, redirect refused, non-success HTTP status, unsupported media type,
response too large, decoded content too large, invalid text encoding, extraction
failure, blank extracted text, and extracted text above the summarize bound.
Existing summarize failures retain their current ownership after a normalized
request is made.

No ordinary failure may expose raw exceptions, resolved addresses, private
topology, response bodies, credentials, authorization values, or arbitrary
remote error detail.

### Privacy and retention

Retrieval occurs only for an explicit --url invocation; it is never automatic or
model-directed. The contacted destination can observe ordinary network metadata,
including the caller's public network address. The requested URL and fetched
content can be sensitive.

The increment adds no default retention of URLs, responses, extracted text,
prompts, or summaries. It adds no history, cache, telemetry, retry, polling,
background work, persistence, cookie jar, or browser state. Existing prompt and
response logging defaults remain unchanged.

### Browser and compatibility boundary

This RFC authorizes no browser work. The native operator contract must be
accepted, implemented, and proven before a separate decision considers whether
the loopback browser client should expose it. RFC-0062 and RFC-0063 remain
unchanged. The OpenAI-compatible surface remains chat-only.

## Rationale

summarize --url is the smallest useful project-owned retrieval increment. It
reuses one bounded capability and result shape, gives immediate operator value,
and makes outbound authority explicit in one command. It does not build a
generic retrieval abstraction or allow a model to choose, follow, or combine
URLs.

Keeping acquisition caller-local means a routing decision determines only where
bounded summarization executes. It does not silently alter Internet egress,
source visibility, or network trust. The same normalized source follows the
accepted local-first and declared-remote rules with existing final attribution.

Plain text only favors a small, inspectable security and dependency surface over
broad web compatibility. Operator-owned retrieval outside the cluster remains
available for every other format.

## Alternatives considered

### Keep retrieval outside Home AI Cluster

This is the current safe baseline and remains supported. It creates no project
network authority, but requires manual copying.

### Generic URL-to-text command

A generic fetch command would establish a reusable retrieval architecture before
one bounded use is proven. It also adds output, file, retention, and reuse
questions unnecessary for URL summarization.

### URL input directly to Chat

Chat has no bounded source-plus-question request contract. URL input would hide
retrieved content in a prompt or require a different request/result decision.

### Retrieve on the selected execution node

This would make routing alter network behavior, give remotes implicit Internet
authority, and risk turning declared nodes into web gateways. It is rejected.

### Web research, search integration, or multiple-source synthesis

These add query privacy, provider ownership, credentials, ranking, citations,
source selection, partial failures, and multi-source resource policies. They are
broader than one explicit URL.

### General tool calling or autonomous browsing

Model-directed actions require a tool protocol, authority and stopping model,
action history, and resource accounting. They are outside this proposal.

### Start with the loopback browser client

The browser must not define network or retrieval architecture. A browser change
is deferred until the native contract is accepted and proven separately.

## Trade-offs

This proposal makes one public plain-text URL convenient to summarize while
preserving runtime and routing seams. It deliberately excludes most ordinary
web pages needing HTML or authentication, and requires careful SSRF, DNS,
peer-validation, timeout, and size-bound implementation evidence.

The URL-specific command presentation gives provenance without changing the core
result model. It does not supply citations or prove a summary correct.

## Impact

If accepted, implementation would change the native summarize command and add a
caller-local retrieval component with focused controlled-transport tests. The
summarize endpoint, SummarizeRequest, capability vocabulary, routing, runtime
adapters, and remote transport remain unchanged. A remote execution still
receives only normalized text and returns existing cluster attribution.

Future evidence must test exactly-one source selection; URL scheme, authority,
credentials, and fragment validation; public/private IPv4/IPv6; hostnames with
a forbidden answer; connected-peer validation where supported; redirect refusal;
proxy and ambient-credential isolation; finite timeouts; streamed encoded and
decoded limits; media types; strict decoding; blank or over-limit text; no URL
in remote transport; unchanged existing source paths; and privacy-safe failures.
Tests use controlled local or fake transports, never the public Internet.

One later live proof may use a harmless public source. Retained proof evidence
must not include private URLs or hostnames, private addresses, raw fetched text,
prompts, generated summaries, credentials, or private topology.

## Open questions

* What concrete DNS, connection, header, body, total-duration, encoded-byte,
  decoded-byte, and decompression limits does a focused HTTP-client spike
  support safely without a new dependency?
* Which supported-client mechanism establishes connected-peer validation or an
  equivalent DNS-rebinding-safe invariant on every supported platform?
* What exact fixed minimal ordinary request headers are necessary, if any, and
  how can they be shown not to carry credentials or operator identity?
* What exact opt-in native-command formatting should present source_url in
  default, verbose, and JSON modes while preserving existing non-URL output?
* After this proof, is an HTML extension justified, and if so what deterministic
  extraction and resource contract merits a separate RFC?

## Decision

Pending.
