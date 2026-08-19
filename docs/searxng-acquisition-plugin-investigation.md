# SearXNG Acquisition Plugin Investigation

Status: Complete

Date: 2026-08-19

## Question

Can an operator-owned private SearXNG service support one small concrete
RFC-0078 external-information acquisition plugin, without giving HAC core or
ordinary servers new provider, service, URL-fetching, or lifecycle authority?

This is a documentation-only investigation. It implements no plugin, creates no
plugin repository, adds no dependency or network authority, and accepts no
architectural decision. RFC-0078 remains the governing acquisition boundary.

## Outcome

**Outcome C — SearXNG has a sufficiently small, concrete, evidence-backed
provider-specific contract to justify a dedicated RFC as the first RFC-0078
production plugin.**

This is a recommendation to consider a dedicated SearXNG RFC, not selection or
implementation. That RFC must make the provider-specific decisions listed below
before a separately versioned plugin is built. It must not reopen RFC-0077 or
RFC-0078, and it must not turn one provider into a generic plugin or service
framework.

The smallest credible shape is:

```text
hac external-information --plugin searxng --query QUERY --question QUESTION
  -> one selected, separately installed SearXNG plugin
  -> one bounded POST form request to one closed, operator-owned SearXNG /search endpoint
  -> JSON results[] only; bounded title/url/content normalization
  -> RFC-0078 reconstruction and complete RFC-0077 validation
  -> existing POST /v1/chat/sources
  -> unchanged ordinary capability=chat routing
```

The service is already running and operator-owned. HAC core and its ordinary
server do not discover, import, configure, start, stop, supervise, or contact
SearXNG. The selected plugin alone owns its one provider request. Result URLs
are returned provenance strings only; neither the plugin nor HAC follows,
resolves, fetches, renders, or otherwise treats them as destinations.

## Accepted boundary versus provider decision

RFC-0078 already fixes the caller edge, exact versioned entry-point group, one
explicit selected plugin, one asynchronous callable accepting only `query`, one
invocation, a concrete built-in `list[dict[str, str]]` containing exactly
`title`, `url`, and `content`, and complete fresh RFC-0077 reconstruction
before the existing source-grounded endpoint. It also fixes the zero-plugin
invariant, privacy-safe pre-routing failure, no fallback, and no ordinary-server
plugin authority. This investigation does not revisit any of those decisions.

RFC-0077 already fixes the downstream source envelope: one through five ordered
sources; nonblank title, URL, and content; title at most 512 UTF-8 bytes, URL at
most 2,048, content at most 1,024, and all source fields together at most
20,480. Source URLs are validated as provenance strings and are never network
instructions. Supplied order is not an authority, truth, freshness, or citation
guarantee. [RFC-0077](../RFC/RFC-0077-bounded-source-grounded-chat.md)

The remaining decision is provider-specific: whether a separately installed
SearXNG distribution may make one bounded call to one operator-owned service and
normalize the response into that already accepted closed representation.

## Current SearXNG facts

### Search API, method, and redirects

SearXNG documents both GET and POST at `/` and `/search`: GET uses query
parameters and POST uses `application/x-www-form-urlencoded` form data. `q`
is required and is passed to configured external search services. JSON requires
`format=json` and the operator must enable `json` in SearXNG's
`search.formats`; otherwise the API returns HTTP 403. [SearXNG Search
API](https://docs.searxng.org/dev/search_api.html)

The plugin should use only POST `/search`, never `/`. Current SearXNG source
redirects a query at `/` to `/search`; using the latter avoids that
service-local redirect. Its search handler can also redirect an external bang
before it emits JSON. SearXNG documents `!!` query syntax as an automatic
redirect to a result or an external search page. A first plugin therefore cannot
follow redirects and must reject query forms SearXNG would interpret as `!!`.
The future RFC must decide whether to reject all SearXNG query-language modifiers
or name the narrow allowed subset. [SearXNG WebApp
source](https://github.com/searxng/searxng/blob/master/searx/webapp.py),
[SearXNG search syntax](https://docs.searxng.org/user/search-syntax.html)

The candidate's request shape is intentionally closed:

```text
POST <closed base endpoint>/search
Content-Type: application/x-www-form-urlencoded
form: q=<exact operator query>, format=json
```

The future RFC should decide whether `categories=general` is also fixed. It
must not expose engines, pages, language, safe-search, arbitrary parameters, or
time range as HAC CLI/configuration fields. Those are SearXNG service/operator
choices, not RFC-0078 caller-core data.

### JSON results and normalization inputs

Current SearXNG serializes JSON as a top-level object whose `results` value is
the result container's ordered main-result list. `answers`, `infoboxes`,
suggestions, corrections, and `unresponsive_engines` are separate top-level
values. The plugin should inspect only `results` and ignore every other field.
[SearXNG JSON serialization
source](https://github.com/searxng/searxng/blob/master/searx/webutils.py)

`results` entries are rich provider-owned objects. The base result type permits
a null URL and defaults title/content to empty strings; main and legacy results
can carry template, engine, image/media, date, score, category, and other
metadata. Thus no SearXNG field is safe to assume present, non-null, nonblank,
or useful merely because it occurs in `results`. [SearXNG result-type
source](https://github.com/searxng/searxng/blob/master/searx/result_types/_base.py)

SearXNG itself merges duplicate main results and orders the result container,
choosing longer title/content values while merging and calculating score. That
is SearXNG provider behavior, not authority or truth. The plugin should preserve
the received `results` order only; it must not score, sort, rerank, enrich, or
introduce a second duplicate-URL policy. [SearXNG result-container
source](https://github.com/searxng/searxng/blob/master/searx/results.py)

### Freshness

`time_range` has day, month, and year values but SearXNG documents it as
applying only to engines that support time-range search. `publishedDate` is an
optional result field and can be null; it is a provider value, not a verified
publication record. The retained private-instance proof observed useful current
snippets while `publishedDate` was generally null and a one-day range still
returned generic results. Neither result order, `time_range`, nor
`publishedDate` can be a freshness or authority guarantee. [SearXNG Search
API](https://docs.searxng.org/dev/search_api.html), [SearXNG result-type
source](https://github.com/searxng/searxng/blob/master/searx/result_types/_base.py),
[retained SearXNG proof](operator-controlled-web-discovery-proof.md)

The recommended first RFC excludes `time_range` and `publishedDate`
entirely. It returns only RFC-0078's three fields. Adding fixed freshness
behavior would be a separate provider-policy decision, not an implementation
default.

## Private-service and disclosure boundary

SearXNG's default source settings bind its direct web application to
`127.0.0.1:8888`; documented server settings expose `bind_address` and port.
This supports private loopback operation. A SearXNG `secret_key` is used for
SearXNG cryptographic purposes, not documented as a narrow search-API
credential. The documented limiter is bot/rate-limit protection and requires
Valkey; `public_instance` features are explicitly not needed for local usage.
[SearXNG default settings](https://github.com/searxng/searxng/blob/master/searx/settings.yml),
[SearXNG server settings](https://docs.searxng.org/admin/settings/settings_server.html),
[SearXNG limiter](https://docs.searxng.org/admin/searx.limiter)

The supportable privacy statement is:

```text
HAC caller -> selected private SearXNG service
SearXNG    -> the external search engines configured by its operator
```

The query reaches the selected SearXNG service. Its API says it passes `q` to
external search services; configured engines can receive the query and observe
SearXNG's network identity or configured proxy. A private SearXNG service is
private only at the first hop: it is not a claim that the query stays local or
that upstream providers do not observe it. The plugin must add no retention of
query, endpoint, raw response, engine data, or credentials, and its
caller-visible acquisition failure remains exactly RFC-0078's
`error: external-information-acquisition-failed`.

The official search API/settings documents identify no dedicated search-API
authentication setting suitable for this narrow contract. Loopback needs no
additional network authentication when the machine boundary is the trust
boundary. Private-LAN deployment would need a separately decided operator
trust/authentication mechanism, such as an operator-owned reverse proxy; it is
not a HAC credential system and must not be inherited from environment variables.
SearXNG documents reverse-proxy deployments as operationally distinct from its
direct listener. [SearXNG nginx deployment](https://docs.searxng.org/admin/installation-nginx.html)

## Endpoint configuration options

| Option | Usefulness and privacy | Destination and transport conclusion |
| --- | --- | --- |
| A. Fixed `http://127.0.0.1:8888` | Smallest first service trust boundary; matches current SearXNG defaults; no hostname resolution, LAN exposure, or API credential. | Credible smallest first option. The RFC must explicitly fix literal loopback, port, `/search`, plain HTTP scope, disabled redirects, and disabled environment proxies. |
| B. Explicit operator-configured loopback URL/port | Supports a nondefault port or local reverse proxy without allowing a remote destination. | Credible only if configuration accepts a closed loopback URL shape, validates literal loopback rather than hostname, fixes the path, prohibits user info/query/fragment and redirects, and decides whether local HTTPS is supported. More configuration than A. |
| C. Explicit trusted private-LAN endpoint | Useful when SearXNG deliberately runs on another trusted personal machine. | Materially broader: hostname resolution/rebinding, private-address policy, TLS name/certificate handling, reverse-proxy authentication, proxy behavior, and operator trust need a specific accepted policy. It cannot be an arbitrary URL. |

An arbitrary public SearXNG URL is not credible for the first plugin. It would
reintroduce an operator-configured public destination and the hostname/
destination-validation problem behind rejected RFC-0064, while adding unknown
service logging, JSON availability, engine configuration, and public-instance
trust. The special fixed provider-service destination is distinguishable from a
returned result URL; the latter remains forbidden as a network target.

The recommendation is **A for the first RFC**. B and C should remain outside
that RFC unless reviewers deliberately want their extra trust/configuration
surface. This is a recommendation, not an accepted endpoint decision.

## Recommended plugin-owned operation

The future distribution can remain separately versioned and installed:

```text
repository:    frian/home-ai-cluster-plugin-searxng
distribution:  home-ai-cluster-plugin-searxng
entry point:   home_ai_cluster.external_information_acquisition.v1
name:          searxng
```

It owns its compatible HTTP client rather than adding a dependency to HAC core.
It exposes one RFC-0078 asynchronous callable and no HAC server entry point.
Installing it only makes `searxng` available for exact explicit selection; it
grants no startup, ordinary-chat, or automatic network authority.

For exactly one call, the plugin should use a fresh async HTTP client with all
of these fixed behaviors:

- one POST form request to the closed `/search` endpoint, with only the RFC-
  selected form fields;
- `follow_redirects=False`, so a root, external-bang, reverse-proxy, or service
  redirect fails locally rather than becoming another request;
- `trust_env=False`, so proxy environment variables do not silently change the
  disclosed destination;
- no cookie jar, browser state, pagination, retry, engine fallback, query
  rewriting, result-URL request, or second SearXNG call;
- explicit finite connect/read/write/pool timeout and connection limits;
- response streaming with a response-byte envelope before JSON parse; content
  length is only an early rejection aid, not the enforcement mechanism;
- successful status plus JSON-only parsing; and
- internal normalization of service, transport, status, redirect, size, JSON,
  structure, and zero-candidate failures to the one RFC-0078 safe error.

SearXNG owns its own finite upstream-engine timeout configuration, together
with engine-specific timeouts, proxy settings, and retries. Those values are
independently operator/service-owned and may vary; they neither determine nor
may be conflated with the plugin's caller-to-SearXNG timeout or retry policy.
Current official documentation illustrates that point rather than a stable
contract: the outgoing-settings reference shows `request_timeout: 2.0`, while
the step-by-step installation example shows `request_timeout: 3.0`. HAC must
not surface or standardize either value. [SearXNG outgoing
settings](https://docs.searxng.org/admin/settings/settings_outgoing.html),
[SearXNG step-by-step installation](https://docs.searxng.org/admin/installation-searxng.html)

RFC-0077 derives the plugin's candidate cap and all candidate-field bounds; it
does **not** derive a raw HTTP byte cap or connect/read/write/pool numbers. The
future provider RFC must justify and select finite values as provider-specific
architectural choices, not infer them from a model-context limit or from
SearXNG's upstream-engine settings. It can accept a finite streaming envelope
and no retry now; those are enforceable provider behaviors, unlike a generic
core timeout executor. Controlled-transport tests and a privacy-safe live proof
are post-acceptance implementation obligations that demonstrate the selected
values and boundaries, not a prerequisite additional investigation before RFC
work.

## Candidate normalization and failures

The recommended deterministic algorithm is deliberately small:

1. Require a JSON object whose `results` value is a concrete list.
2. Inspect that received order once. Ignore every non-mapping item and every
   item whose `title`, `url`, or `content` is not a string with nonblank
   content.
3. Copy only those three values into fresh built-in dictionaries. Do not copy
   engine, score, template, date, answer, infobox, correction, image, media,
   rank, raw response, or any other provider field.
4. Preserve the surviving SearXNG order, do not perform a second deduplication
   pass, and stop after five candidates.
5. If no usable candidate remains, fail acquisition. Otherwise return the list
   and let the RFC-0078 caller perform fresh complete RFC-0077 validation.

The plugin does not silently trim title, URL, or content to fit RFC-0077. It may
skip malformed/unusable provider entries while searching for up to five
candidates, but the returned closed list still fails at the caller if any
selected value violates RFC-0077. This preserves HAC's accepted final
pre-routing evidence validation.

Internal failure classes include unavailable service, connect/read/write/pool
timeout, transport failure, any redirect status, any non-success status
(including JSON-disabled 403), response-envelope breach, invalid JSON,
non-object/non-list structure, malformed entries, and zero usable candidates.
They must never reveal query, endpoint, engine name, raw response, snippets,
credentials, stack trace, or private topology to the HAC caller.

## Lifecycle and configuration

The plugin assumes an already-running operator-owned SearXNG service. It has no
installation, startup, shutdown, upgrade, engine-configuration, repair,
supervision, health-polling, or service-manager responsibility. SearXNG's own
service configuration remains separate from plugin configuration. Partial
upstream-engine failure is normal operational state, not a reason for HAC to
own another service lifecycle.

For recommended fixed-loopback option A, the smallest plugin configuration is no
endpoint configuration and no credential. The operator configures SearXNG itself
to listen at the selected loopback endpoint and enable JSON. If a later RFC
selects B or C, it must name one provider-specific explicit configuration
mechanism and secret-handling rules. Credentials/configuration must not enter HAC
requests, evidence, history, logs, metrics, traces, results, errors, or retained
proof material. This is not permission for a generic HAC configuration/secrets
system.

## RFC-worthy decision surface

Only the following provider-specific choices need a dedicated RFC before
implementation:

1. Select endpoint option A, B, or C. The recommendation is A, a fixed literal
   loopback endpoint, and the RFC must say whether it is the only first-version
   destination.
2. Select exact closed POST `/search` form fields, including whether
   `categories=general` is fixed, and policy for SearXNG query-language
   modifiers. It must reject external-bang redirects.
3. Require the operator-owned prerequisite: JSON enabled, service already
   running, configured engines explicitly accepted by the operator, and no HAC
   lifecycle ownership.
4. Justify and select finite plugin-to-SearXNG connect/read/write/pool and
   streaming response-byte limits. Keep them separate from SearXNG engine
   timeouts and the later HAC-server HTTP timeout; controlled-transport tests
   and live proof are post-acceptance implementation obligations.
5. Select endpoint authentication/trust. The recommendation is no credential for
   fixed loopback; private-LAN support requires explicit operator-owned TLS/auth
   policy, never generic HAC secrets.
6. Accept the narrow response rule: JSON `results` only, no answer/infobox/date/
   engine metadata, deterministic skip-and-stop normalization, no plugin-side
   duplicate policy, and zero usable candidates as safe failure.
7. Specify post-acceptance focused package tests and privacy-safe live proof:
   exact one POST, disabled redirects/proxy environment, no result-URL traffic,
   the accepted finite limits, safe failures, no retained sensitive data, and
   unchanged zero-plugin/ordinary-server behavior.

These are choices for one SearXNG package. They do not authorize provider
selection, a plugin manager, provider fallback, generic configuration, a new
capability, a server endpoint, ordinary-server discovery, or public-URL
retrieval.

## Sources consulted

Technical claims were checked against current official SearXNG documentation and
source on 2026-08-19:

- [Search API](https://docs.searxng.org/dev/search_api.html)
- [search syntax](https://docs.searxng.org/user/search-syntax.html)
- [server settings](https://docs.searxng.org/admin/settings/settings_server.html)
- [limiter documentation](https://docs.searxng.org/admin/searx.limiter)
- [outgoing settings](https://docs.searxng.org/admin/settings/settings_outgoing.html)
- [step-by-step installation](https://docs.searxng.org/admin/installation-searxng.html)
- [default settings source](https://github.com/searxng/searxng/blob/master/searx/settings.yml)
- [WebApp source](https://github.com/searxng/searxng/blob/master/searx/webapp.py)
- [JSON serialization source](https://github.com/searxng/searxng/blob/master/searx/webutils.py)
- [result-type source](https://github.com/searxng/searxng/blob/master/searx/result_types/_base.py)
- [result-container source](https://github.com/searxng/searxng/blob/master/searx/results.py)

The previous HAC SearXNG proof remains empirical evidence of usefulness and
limits, not a provider contract or reliability guarantee.
