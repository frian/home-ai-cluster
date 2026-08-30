# RFC-0093: Bounded Tavily Acquisition Plugin

Status: Draft

Date: 2026-08-30

Author: frian

## Summary

This RFC proposes one concrete Tavily provider decision under accepted RFC-0078.
A separately installed, separately versioned Tavily package may be selected only
by the explicit external-information caller edge. It makes one bounded HTTPS
search request, returns only an ordered concrete list of `title`/`url`/`content`
candidates, and leaves fresh complete RFC-0077 validation to the existing caller
before ordinary source-grounded Chat routing.

The proposal does not revise RFC-0077 or RFC-0078, and does not implement the
plugin in this RFC. An installed package does not grant ordinary Chat or HAC
startup automatic network authority.

## Problem

RFC-0078 accepts one small, provider-neutral acquisition seam but deliberately
selects no provider destination, credential mechanism, request shape, transport
policy, or response-normalization rule. The completed
[Tavily acquisition-plugin investigation](../docs/tavily-acquisition-plugin-investigation.md)
reached Outcome A: Tavily can satisfy that seam unchanged and merits one
dedicated provider RFC.

Without a fixed provider contract, an implementation could silently add endpoint
overrides, ambient proxy or certificate behavior, credential fallbacks, provider
request options, retries, URL following, result shaping, or retained
configuration. Those choices would turn one explicit provider package into a
configuration and network-authority surface. This RFC selects the smallest
inspectable Tavily operation while preserving RFC-0077 evidence validation and
RFC-0078 caller ownership.

RFC-0064 remains Rejected. A URL returned by Tavily remains provenance data
only; it grants neither the plugin nor HAC authority to resolve, fetch, follow,
render, or otherwise act on it.

## Goals

This RFC proposes to:

- select one separately installed Tavily package identity under RFC-0078;
- select one fixed public HTTPS destination and one plugin-owned API-key
  mechanism;
- define exactly one bounded provider request and one finite transport policy;
- retain only ordered `title`, `url`, and `content` candidate data through the
  plugin boundary;
- preserve fresh complete RFC-0077 validation before ordinary routing;
- preserve zero-plugin, startup, ordinary Chat, routing, adapter, and history
  behavior; and
- define focused later implementation proof without claiming it exists now.

## Non-goals

This RFC does not revise RFC-0077 or RFC-0078. It does not authorize:

- an implementation in this PR, Tavily dependencies in HAC core, or package
  publication;
- a generic provider, plugin, configuration, credential, or secrets framework;
- provider selection, preference, health, fallback, or automatic
  external-information fallback for ordinary Chat;
- retained provider configuration, a HAC secrets store, cost/account management,
  or runtime/service lifecycle management;
- arbitrary external URL retrieval, a browser, crawler, Extract, Crawl, Map,
  Research, result-URL fetching, retries, or multi-step acquisition;
- a Web/search/browse/retrieve/research capability, endpoint, node, routing
  rule, adapter operation, or server-side acquisition; or
- a change to RFC-0077 source limits.

Whether RFC-0077's 1,024 UTF-8-byte source-content limit is ideal may be
separately investigated if real provider proof shows repeated useful-source
rejection. This RFC does not change that limit.

## Proposal

### Unchanged acquisition boundary

RFC-0093 is a provider-specific decision under RFC-0078; it does not amend
RFC-0077 or RFC-0078. The conceptual callable remains exactly:

~~~python
async def acquire(query: str) -> list[dict[str, str]]
~~~

Each returned dictionary has exactly `title`, `url`, and `content` string
fields. The caller still constructs fresh values and performs complete fresh
RFC-0077 validation before its existing `POST /v1/chat/sources` request. No
candidate reaches ordinary routing before that validation succeeds.

This introduces no HAC capability, provider abstraction, plugin framework,
configuration framework, secrets framework, routing concept, fallback policy,
or ordinary Chat behavior.

### Package identity and explicit selection

The future package identity is fixed as follows:

~~~text
repository:         frian/home-ai-cluster-plugin-tavily
distribution:       home-ai-cluster-plugin-tavily
entry-point group:  home_ai_cluster.external_information_acquisition.v1
entry-point name:   tavily
~~~

The package is separately installed and separately versioned. It exposes only
the existing RFC-0078 callable and returns built-in data rather than HAC models.
Installation makes the package available for exact explicit selection only. It
does not import Tavily at HAC startup, perform network activity, or grant
automatic network authority.

### Fixed destination and connection boundary

One invocation may request exactly this provider destination:

~~~text
https://api.tavily.com/search
~~~

The request uses HTTPS with ordinary TLS verification enabled. There is no
endpoint or base-URL override, insecure TLS mode, custom CA mechanism, hostname
alias, or provider connection configuration. Redirect following is disabled. A
redirect is an acquisition failure and must never become a second request.

The provider client must set `trust_env=False`, or use an exact equivalent, so
ambient `HTTP_PROXY`, `HTTPS_PROXY`, `ALL_PROXY`, certificate environment
configuration, and other client-environment settings cannot silently alter the
provider connection.

### Credential ownership

The sole first-version credential mechanism is a nonblank `TAVILY_API_KEY`. The
selected Tavily plugin reads it directly from the `hac external-information`
caller process environment when its `acquire` callable is invoked. HAC core does
not read, parse, pass, retain, configure, or otherwise handle the key. This
introduces no separate plugin process, subprocess, sandbox, IPC, or isolation
mechanism. The only use of the key is constructing:

~~~text
Authorization: Bearer <key>
~~~

There is no inline CLI key, Tavily CLI config-file fallback, OAuth-token
fallback, project/session/human identifier, or generic HAC secrets or
configuration system. Missing, blank, malformed, rejected, or otherwise
unusable credentials normalize to the existing RFC-0078 caller-visible
acquisition failure.

### Exact one-request shape

One plugin invocation makes exactly one HTTP POST to the fixed destination with
the Authorization header above and this JSON body:

~~~json
{
  "query": "<exact RFC-0078 operator query>",
  "search_depth": "basic",
  "max_results": 5,
  "chunks_per_source": 1,
  "include_answer": false,
  "include_raw_content": false,
  "include_images": false,
  "include_image_descriptions": false,
  "auto_parameters": false
}
~~~

The query passes unchanged. The package adds no query rewriting,
model-generated query, topic/date/domain/language/country control, safe-search
or exact-match setting, arbitrary Tavily parameter, retry, pagination, fallback,
another provider request, result-URL request, Extract, Crawl, Map, Research,
provider-generated answer, or raw page content.

`chunks_per_source=1` reduces provider-returned content before RFC-0078 and
RFC-0077 validation. Tavily documents a character bound, not a UTF-8-byte bound,
so it does not guarantee RFC-0077's 1,024 UTF-8-byte `content` bound. The
package must never truncate or repair returned content to fit; RFC-0077
validation remains authoritative.

### Provider transport bounds

The plugin operation has these fixed bounds:

~~~text
total operation deadline:                    30 seconds
connect timeout:                              5 seconds
read timeout:                                20 seconds
write timeout:                                5 seconds
pool timeout:                                 2 seconds
maximum decoded response body:                1 MiB
maximum simultaneous provider connections:   1
retries:                                      0
redirects:                                    disabled
~~~

The 30-second total bound is deliberately consistent with Tavily's current
official direct-HTTP example. The component values are HAC's provider-specific
conservative bounds for one remote HTTPS operation; they are not Tavily service
guarantees. The decoded one-MiB envelope is a transport-safety bound only and
does not enlarge RFC-0077 evidence limits.

The implementation must enforce the response limit incrementally before JSON
parsing. `Content-Length` may permit early rejection, but must not be the
enforcement mechanism. The total deadline applies in addition to component
timeouts, and the operation has no persistent cross-operation session.

### Response acceptance and deterministic normalization

Success requires HTTP 200, a response within the decoded one-MiB bound, valid
JSON, a top-level JSON object, and `results` as a concrete list. The package
inspects `results` once in received provider order.

For each entry, it ignores non-mapping entries and requires nonblank string
`title`, `url`, and `content` fields. For a usable entry it copies exactly those
three values into a fresh built-in dictionary and copies no other provider
field. It stops after five usable candidates.

The package must not score, rerank, sort, deduplicate, enrich, verify,
truncate, repair, or interpret provider order as authority, truth, freshness,
or citation correctness. If no usable candidate remains, acquisition fails.
Otherwise it returns the concrete list for RFC-0078 to reconstruct and fully
validate under RFC-0077. An RFC-0077-invalid selected candidate fails the
complete operation before ordinary routing.

The following provider data must not cross the plugin boundary: Tavily score,
answer, raw content, images, favicon, echoed query, response time, usage,
request ID, provider tracking identifiers, dates, and all other
provider-specific metadata. Result URLs remain provenance strings only and
grant no network authority.

### Failure, privacy, and ordinary-HAC invariants

All plugin and provider failures normalize through RFC-0078 to:

~~~text
error: external-information-acquisition-failed
~~~

This includes missing or invalid credentials; DNS, TLS, connect, read, write,
pool, and other transport failures; total-deadline expiry; redirects; non-200
statuses including authentication, rate-limit, usage-limit, and provider errors;
oversized responses; invalid JSON or response structure; zero usable candidates;
and unexpected plugin exceptions.

The ordinary caller-visible failure must not expose the query, API key,
Authorization header, endpoint detail, HTTP status or body, request ID,
provider response, source content, stack trace, private topology, or
configuration detail. The package adds no default logs, history, telemetry,
cache, raw-response persistence, or other retained provider state.

RFC-0078's zero-plugin and ordinary-HAC invariants remain exact: HAC server
startup and ordinary Chat do not discover, import, or invoke Tavily; installation
alone performs no network access; only explicit
`hac external-information --plugin tavily ...` selection authorizes the one
provider request; and routing, capabilities, runtime adapters, remote transport
semantics, history, and ordinary HAC behavior remain unchanged.

## Rationale

Tavily is materially different from RFC-0079's SearXNG provider. SearXNG uses
an operator-owned local service, a fixed loopback first hop, no credential at
that hop, and operator-owned service lifecycle. Tavily uses an external public
HTTPS service and a provider account/API credential, with no local service
lifecycle.

The important architectural proof is that these materially different providers
both fit the unchanged RFC-0078 acquisition seam and deliver the same closed
candidate representation to HAC. This is the 0.7 “interchangeable” proof
identified in the [release direction](../docs/release-direction-to-1.0.md). It
does not generalize a two-provider result into a broad plugin or provider
framework.

## Alternatives considered

### Keep only SearXNG

Retaining only the local-service option would avoid external credentials, but
would not test whether the accepted acquisition seam remains independent of
operator-owned local service lifecycle. Tavily provides that bounded second
integration without changing cluster-facing concepts.

### Add Tavily behavior to HAC core

Core ownership would couple HAC to a provider dependency, credential, and
network destination. A separately installed package keeps the provider request,
credential handling, and parsing on the RFC-0078 side of the boundary.

### Permit configurable endpoint, credentials, or request options

Those surfaces appear convenient but make the fixed authority and privacy
boundary ambiguous. One destination, one credential mechanism, and one request
shape remain reviewable and finite.

### Accept provider answers, raw content, or URL retrieval

Those options exceed the bounded title/URL/content candidate contract and would
add unneeded data, network authority, or multi-step behavior. RFC-0077
validation of the small candidate representation is the intended seam.

## Trade-offs

Tavily requires an operator-held API key and sends the explicit query to a
public provider. This is less local than an operator-run SearXNG service and can
be subject to provider availability and usage limits. The explicit caller edge,
fixed destination, plugin-owned credential, one-request bound, and safe failure
contract keep that disclosure visible rather than making it ordinary Chat
behavior.

Fixed parameters and no retries can reject work that a broader integration might
recover or refine. That is an intentional first-version constraint: it keeps
authority, cost exposure, latency, and data handling finite. Provider snippets
can still fail RFC-0077 byte or aggregate validation; the package must not make
them fit by altering evidence.

## Impact

If accepted, this RFC authorizes a later separately installed Tavily plugin
implementation only. HAC core gains no dependency, provider import, API key,
configuration, endpoint, capability, route, routing behavior, or automatic
network access. RFC-0077 and RFC-0078 remain unchanged. Later implementation
must provide focused proof of:

- the exact entry-point identity and no Tavily import or network activity during
  ordinary HAC startup;
- exactly one provider request per explicit invocation, to the fixed destination
  with the exact body and a plugin-only API-key read;
- TLS verification, disabled redirects, and disabled environment proxy or
  configuration inheritance;
- finite component and total timeouts, one-connection maximum, and incremental
  response-byte enforcement;
- deterministic normalization with no result-URL request;
- safe failure normalization without credential or query leakage;
- complete RFC-0078/RFC-0077 validation before routing and zero-plugin
  invariants; and
- one privacy-safe live proof using an operator-provided Tavily account and key,
  without placing a real key, private query, or raw provider response in the
  repository.

## Open questions

No open question blocks this Draft. Real implementation proof may show that
useful candidates repeatedly exceed RFC-0077's content bound; that would justify
a separate investigation, not a silent adjustment here. Provider pricing,
account policy, availability, and future Tavily features remain outside HAC's
first provider contract.

## Decision

Pending.
