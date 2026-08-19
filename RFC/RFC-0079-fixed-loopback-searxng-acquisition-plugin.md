# RFC-0079: Fixed-Loopback SearXNG Acquisition Plugin

Status: Accepted

Date: 2026-08-19

Author: frian

## Summary

This RFC proposes the first concrete provider integration under accepted
RFC-0078: one separately installed SearXNG acquisition plugin selected only by
the explicit one-shot hac external-information caller edge.

The first version is intentionally fixed and local. The plugin makes exactly one
bounded form POST to exactly:

~~~text
http://127.0.0.1:8888/search
~~~

It receives the exact RFC-0078 query, returns only an ordered concrete built-in
list of title/URL/content dictionaries, and leaves fresh RFC-0077 reconstruction
and complete validation to the existing caller boundary. The ordinary HAC server
does not discover, import, configure, invoke, or gain network authority through
this plugin.

The provider/service path is explicit:

~~~text
HAC caller
  -> private loopback SearXNG
  -> operator-configured external search engines
~~~

A private SearXNG first hop does not mean that the explicit query remains local.
RFC-0079 acceptance authorizes only a later separately installed plugin
implementation, while this PR itself contains no plugin implementation,
repository, dependency, lifecycle machinery, or new HAC capability.

## Problem

RFC-0078 deliberately accepts a small provider-neutral acquisition boundary but
selects no provider, endpoint, provider request, configuration, or provider
limits. The completed SearXNG investigation found that a private SearXNG service
can supply bounded untrusted title/URL/snippet candidates, but that provider
requires a concrete decision before any separately installed distribution is
implemented.

Without a fixed first contract, an implementation could silently choose among
configurable loopback/LAN/public endpoints, proxy inheritance, redirects,
credentials, query modifiers, retries, raw response limits, and result
normalization policy. That would make a supposedly small first plugin a hidden
configuration and network-authority system.

RFC-0064 remains rejected. A SearXNG result URL is provenance data only; it
never gives the plugin, HAC caller, ordinary server, router, remote node, or
runtime adapter authority to connect to it.

## Evidence basis

The completed [SearXNG acquisition-plugin investigation](../docs/searxng-acquisition-plugin-investigation.md)
established the narrow provider facts used here: SearXNG documents form POST at
its search API with required query and JSON format; its default source settings
use literal 127.0.0.1:8888; and JSON exposes ordered main results separately
from provider metadata. It also records why time ranges, publication dates, and
provider ordering are not freshness, truth, or authority guarantees. The
[retained operator proof](../docs/operator-controlled-web-discovery-proof.md)
demonstrates limited snippet usefulness and its limits without authorizing an
integration.

This RFC selects the fixed provider choices left open by that investigation. It
does not treat one prior service observation as a reliability guarantee, and it
does not alter the source/evidence or installed-plugin boundaries accepted in
[RFC-0077](RFC-0077-bounded-source-grounded-chat.md) and
[RFC-0078](RFC-0078-optional-external-information-acquisition-plugin-boundary.md).

## Goals

This RFC proposes to:

- select exactly one first provider package identity under RFC-0078;
- keep its service destination literal, loopback-only, DNS-free,
  credential-free, and configuration-free;
- define one exact provider request and one bounded one-operation transport
  policy;
- retain only SearXNG results title/URL/content data under deterministic
  normalization;
- preserve RFC-0078 as the sole plugin/caller compatibility boundary and
  RFC-0077 as the authoritative evidence validation boundary;
- make upstream disclosure and operator-owned SearXNG lifecycle visible;
- preserve zero-plugin, ordinary-server, ordinary Chat, routing, adapter, and
  result behavior; and
- name focused post-acceptance implementation tests and live proof without
  claiming any exists now.

## Non-goals

This RFC does not reopen or revise RFC-0077 or RFC-0078. It does not introduce
or authorize:

- a plugin implementation, plugin repository, package publication, dependency,
  provider SDK in HAC core, or change to HAC production source;
- installation, startup, shutdown, upgrade, configuration, engine selection,
  repair, supervision, health polling, or service management for SearXNG;
- configurable SearXNG endpoints or ports, hostname destinations, private-LAN
  destinations, public SearXNG instances, HTTPS/TLS, authentication credentials,
  endpoint environment-variable overrides, or generic endpoint configuration;
- a generic plugin/provider/configuration/credentials/secrets framework,
  PluginManager, provider selection, provider fallback, or provider health;
- categories, engines, page number, language, safe-search, time range, or
  arbitrary SearXNG request parameters;
- plugin query parsing, query rewriting, model-directed queries, repeated
  research loops, retries, pagination, a second SearXNG request, browser state,
  cookies, or result URL requests;
- a web, search, browse, retrieve, or research capability, endpoint, node,
  routing policy, adapter operation, or server-side acquisition;
- result ranking, authority/freshness inference, date interpretation, source
  verification, citation correctness, RAG, cache, database, persistence,
  telemetry, history, tools, agents, Docker, Kubernetes, or dashboard; or
- ordinary HAC-server discovery, import, configuration, invocation, or network
  authority for acquisition plugins.

## Proposal

### Provider and package identity

The future plugin is one separately installed Python distribution:

~~~text
repository:         frian/home-ai-cluster-plugin-searxng
distribution:       home-ai-cluster-plugin-searxng
entry-point group:  home_ai_cluster.external_information_acquisition.v1
entry-point name:   searxng
~~~

It exposes the existing RFC-0078 conceptual callable only:

~~~python
async def acquire(query: str) -> list[dict[str, str]]
~~~

The distribution is separately versioned and installed. It must not import HAC
models merely to construct its return value. Its entry point remains available
only for exact explicit selection through RFC-0078; installation does not alter
ordinary HAC startup, ordinary request handling, or network authority.

### Service ownership and disclosure

The plugin assumes that an operator has independently installed, configured, and
already started SearXNG. The operator enables JSON output and accepts/configures
the external search engines SearXNG uses.

HAC core, the ordinary HAC server, and the plugin do not install, start, stop,
upgrade, configure engines for, repair, supervise, health-poll, or otherwise
manage SearXNG. They do not own its engine timeouts, retries, proxy behavior, or
service lifecycle.

The chosen plugin is trusted Python installed by the operator under RFC-0078.
The separate package, not HAC core, owns one provider request and provider
response parsing. The explicit query reaches loopback SearXNG, which may then
forward it to its operator-configured external engines. This is an explicit
provider disclosure boundary, not a claim that a private first hop keeps the
query local.

### Fixed destination

The sole first-version provider destination is the literal IPv4 loopback URL:

~~~text
http://127.0.0.1:8888/search
~~~

There is no hostname or DNS resolution, configurable base URL/port, private-LAN
or public endpoint, TLS configuration, API authentication, generic endpoint
configuration, or environment-variable endpoint override. Plain HTTP is limited
to this literal loopback destination.

An operator who wants this plugin configures their independently operated
SearXNG service to expose its JSON search API there. An occupied local port is
an intentional first-version incompatibility, not permission to add a port
override as an implementation convenience.

### Exact request and one operation

One RFC-0078 plugin invocation makes exactly one provider HTTP request:

~~~text
POST http://127.0.0.1:8888/search
Content-Type: application/x-www-form-urlencoded

q=<exact RFC-0078 operator query>
format=json
~~~

Those are exactly the provider form fields. The plugin adds no category, engine,
page, language, safe-search, time-range, arbitrary SearXNG parameter, or
provider configuration value. It passes the exact RFC-0078 query unchanged and
performs no generic SearXNG query-language parsing or rewriting. Bangs, engine
selectors, language modifiers, and other operator-entered syntax are neither
rewritten nor interpreted by the plugin.

The client does not follow redirects. A redirect-producing external bang or any
other redirect response is therefore an acquisition failure; it cannot produce
another request or change the destination.

### Plugin-owned transport policy

The plugin uses one fresh finite asynchronous HTTP client operation with these
fixed bounds:

~~~text
total plugin-to-SearXNG operation deadline: 30 seconds
connect timeout:                             2 seconds
read timeout:                               20 seconds
write timeout:                               5 seconds
pool timeout:                                2 seconds
decoded response body maximum:               1 MiB
~~~

The implementation must enforce the 30-second total operation deadline in
addition to component HTTP timeouts. It reads response content incrementally so
the decoded one-MiB limit is enforced before JSON parsing; Content-Length may
provide an early rejection but is never the enforcement mechanism.

The client must disable redirect following and environment proxy/configuration
inheritance (follow_redirects=False and trust_env=False, or equivalent). It
makes exactly one provider request, uses no retry, pagination, second request,
result URL request, cookie/session workflow, automatic provider fallback, or
automatic engine fallback. A fresh one-operation client may use one connection
only and introduces no persistent cross-operation session or browser state.

These values belong only to the plugin-to-local-SearXNG operation. They do not
configure, infer, replace, or mirror SearXNG's own upstream-engine timeouts.
SearXNG owns finite upstream-engine timeout configuration independently; its
operator/service-owned values may vary and must not determine the plugin limits.

### Response acceptance and normalization

A successful provider response is only one that is:

- HTTP 200;
- within the decoded one-MiB body limit;
- valid JSON;
- a top-level JSON object; and
- an object containing results as a list.

The plugin ignores every other top-level SearXNG value, including answers,
infoboxes, suggestions, corrections, unresponsive-engine metadata, scores,
dates, engine identities, media/image fields, and any other provider-specific
metadata.

It inspects results once in received order. For each item, it ignores a
non-object item and otherwise requires nonblank string title, url, and content
values. For every usable item, it copies exactly those three values into a fresh
built-in dictionary. It preserves surviving SearXNG order and stops after five
usable candidates.

The plugin must not score, rerank, sort, deduplicate, enrich, fetch a URL, use
publishedDate, infer authority/freshness, trim/truncate fields to satisfy
RFC-0077, or copy any provider-specific field. SearXNG output order is provider
output order only; it is not truth, authority, freshness, or citation
correctness.

If no usable candidate remains, acquisition fails. Otherwise the plugin returns
the concrete built-in list. RFC-0078 then constructs fresh SourceEvidence and
SourceGroundedChatRequest values and completes authoritative RFC-0077
validation. The plugin neither duplicates nor replaces that validation. A
selected candidate that violates RFC-0077 therefore fails at the RFC-0078
acquisition boundary rather than being silently modified.

### Failure, privacy, and URL authority

Plugin-internal failures include at least:

- unavailable service;
- connect, read, write, or pool timeout;
- total operation deadline exceeded;
- transport error;
- redirect response;
- non-200 response, including JSON-disabled 403;
- decoded response body over one MiB;
- invalid JSON;
- invalid top-level structure;
- missing or non-list results; and
- zero usable candidates.

RFC-0078 remains the sole caller-visible acquisition failure contract:

~~~text
error: external-information-acquisition-failed
~~~

No ordinary failure reveals the query, raw provider response, result content,
engine identities, stack trace, credentials, private topology, or service
internals. The documented fixed endpoint does not license exposing runtime
endpoint details. The plugin adds no default logs, history, cache, telemetry,
persistence, or raw response retention.

Returned result URLs remain provenance strings only. Neither the plugin nor HAC
resolves, validates as a network destination, follows, fetches, renders,
previews, or otherwise acts on one.

## Rationale

A literal 127.0.0.1:8888/search destination is the smallest credible first
provider boundary. It is local, DNS-free, credential-free, and requires no HAC
endpoint configuration. That makes the outbound destination visible and avoids
the hostname/address validation, private topology, TLS, authentication, and
configuration issues of remote endpoints. It also does not revive arbitrary
public URL acquisition rejected by RFC-0064.

One POST form body keeps the operation aligned with SearXNG documented Search
API while putting the explicit query in the request body rather than the request
URL. The closed two-field shape prevents a first plugin from becoming a generic
SearXNG client. Passing the operator query unchanged preserves RFC-0078 exact
query contract; refusing redirects rather than rewriting query syntax ensures a
redirect cannot create a second destination request.

The finite client bounds are deliberately provider-owned rather than core-owned.
Loopback connection setup should be fast, so two seconds is sufficient for the
connection/pool phase. The submitted form body is very small, so five seconds
for write is conservative. SearXNG may legitimately wait for its independently
configured upstream engines, so a twenty-second read allowance and thirty-second
total deadline give finite headroom without leaving acquisition open-ended.
These are not SearXNG upstream-engine values.

One MiB of decoded response is intentionally much larger than RFC-0077 final
20,480-byte aggregate evidence envelope, allowing a rich SearXNG JSON response
to contain ignored provider metadata while preventing that metadata from making
one operation unbounded. Incremental decoded-byte enforcement preserves the
bound even when Content-Length is absent or inaccurate.

The return is intentionally only RFC-0078 three-field representation. SearXNG
scores, engines, dates, and result types would add provider semantics to HAC
core boundary without being necessary for bounded source-grounded Chat.
RFC-0077 revalidation remains final evidence authority before the existing
source-grounded POST and ordinary chat routing.

## Alternatives considered

### Fixed literal loopback endpoint

Selected. Fixed 127.0.0.1:8888 removes hostname/DNS, remote trust, credentials,
TLS, and endpoint-configuration design from the first provider increment. It is
directly compatible with an operator-owned local service.

### Configurable loopback endpoint or port

Deferred. It would introduce a plugin configuration source, precedence,
validation, failure, and environment-override policy. A future demonstrated
need may justify a separate RFC, but it must not be predesigned into the first
implementation.

### Private-LAN SearXNG

Deferred. It introduces private topology, hostname/DNS and address policy, TLS
name/certificate validation, authentication, reverse-proxy, and trust decisions
that are not needed for the local first increment.

### Arbitrary or public SearXNG instance

Rejected for the first boundary. It would add unknown instance logging, service
configuration, JSON availability, public trust, and a user-configured public
destination. It is not a meaningful privacy improvement over other public
provider choices and reintroduces RFC-0064-related destination concerns.

### Direct proprietary search provider

Not selected. This RFC decides only the first operator-owned SearXNG plugin and
does not establish provider competition, a generic provider abstraction, or
preference policy.

### Operator-owned manual retrieval

Remains supported. An operator may acquire information independently and use the
existing accepted source-grounded boundary. This RFC adds no requirement to run
SearXNG or install a plugin for ordinary HAC use.

## Trade-offs

The fixed endpoint is less convenient for an operator whose loopback port 8888
is occupied or whose SearXNG service runs on another machine. That inconvenience
is accepted deliberately: the first contract is literal, local,
credential-free, DNS-free, configuration-free, and easy to reason about.

The one-MiB provider response limit may reject an otherwise parseable rich
response, and fixed timeouts may reject a slow local service. Those outcomes are
preferable to unbounded provider work in the first plugin. The operator-owned
manual retrieval workflow remains available when the bounded provider shape is
not suitable.

A separate distribution adds packaging and release work, but it keeps SearXNG
code and any dependencies out of HAC core and retains RFC-0078 zero-plugin
ordinary-HAC behavior.

## Impact

If accepted, this RFC authorizes only a later separately installed
home-ai-cluster-plugin-searxng implementation under existing
home_ai_cluster.external_information_acquisition.v1 group and searxng entry
point. It may implement fixed provider behavior above and focused tests.

HAC core architecture, ordinary HAC-server startup/request handling, ordinary
Chat, RFC-0077 supplied-source Chat, capability vocabulary, routing, adapters,
remote transport semantics, history, and result models remain unchanged.
RFC-0078 remains governing category-specific acquisition boundary and RFC-0077
remains evidence/source-grounded Chat boundary.

Ordinary HAC remains fully functional with no SearXNG service and no plugin
installed. Acceptance authorizes the later separate plugin implementation
described by RFC-0079, while this acceptance PR itself adds no production code,
dependency, plugin repository, or runtime/network authority to HAC core.

## Proof obligations after acceptance

Acceptance must authorize implementation but does not claim implementation or
proof completion. A future implementation must retain focused tests for:

1. exact entry-point group/name metadata and existing RFC-0078 async callable
   contract;
2. exactly one POST to literal fixed path with exactly q and format=json form
   fields, preserving exact query;
3. disabled redirects and environment proxies;
4. no retry, pagination, second request, browser/session state, or result URL
   traffic;
5. component timeout configuration and total thirty-second deadline;
6. incremental decoded one-MiB response enforcement independent of
   Content-Length;
7. exact HTTP-200, JSON, top-level-object, and results-list acceptance;
8. deterministic candidate normalization, stop-after-five behavior, closed
   three-field return, and safe zero-usable-candidate failure;
9. safe provider failure normalization without retained sensitive data; and
10. unchanged RFC-0078 zero-plugin and ordinary-server behavior.

A privacy-safe live proof must later demonstrate one real separately installed
plugin against an already running private loopback SearXNG service, then existing
RFC-0078 to RFC-0077 to POST /v1/chat/sources to ordinary chat path. It must not
retain private queries, URLs, result content, raw responses, credentials, service
configuration, machine identity, or private topology. This is post-acceptance
implementation evidence, not established by RFC acceptance itself.

## Open questions

The proposal intentionally leaves no configurable first-version variant.
The following are deferred rather than implementation choices:

- configurable loopback endpoint/port;
- hostname, private-LAN, public-instance, HTTPS/TLS, and authentication
  destinations;
- any future non-pass-through SearXNG query-modifier policy;
- categories, engines, page, language, safe-search, and freshness parameters;
- provider configuration/credentials and generic HAC configuration;
- source ranking, date/freshness semantics, duplicate policy, and result URL
  retrieval; and
- provider lifecycle, selection, fallback, or generic plugin expansion.

Each would require a future focused RFC if evidence demonstrates a need.

## Decision

Accepted.

HAC accepts one separately installed `home-ai-cluster-plugin-searxng`
distribution, exposed through the RFC-0078
`home_ai_cluster.external_information_acquisition.v1` entry-point group under
the exact name `searxng`. One explicit acquisition invocation makes exactly one
form POST to `http://127.0.0.1:8888/search`, with only the exact operator query
as `q` and `format=json`.

The plugin owns a 30-second total operation deadline, 2-second connect timeout,
20-second read timeout, 5-second write timeout, 2-second pool timeout, and a
1 MiB decoded-response maximum. Redirects and environment proxy/configuration
inheritance are disabled. It makes no retry, pagination, second provider
request, or result-URL fetch. It accepts JSON `results` only and deterministically
preserves surviving provider order into at most five built-in `title`/`url`/
`content` dictionaries, without scoring, reranking, deduplication, enrichment,
freshness inference, or truncation. RFC-0078 reconstruction and complete
RFC-0077 validation remain authoritative.

SearXNG remains independently installed, configured, already running, and
operator-owned; HAC core, the ordinary server, and the plugin do not own its
lifecycle. Configurable endpoints/ports, LAN or public destinations, TLS or
authentication, provider configuration, query-policy expansion, URL retrieval,
provider selection/fallback, and generic plugin expansion remain outside this
decision.

Acceptance authorizes a later separately installed plugin implementation and
its focused tests and proof. It adds no production implementation or
runtime/network authority to HAC core.
