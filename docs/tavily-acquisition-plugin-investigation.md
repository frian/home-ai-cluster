# Tavily acquisition-plugin investigation

Status: Investigation only

Date: 2026-08-30

## Question

Can a separately installed Tavily acquisition plugin satisfy RFC-0078 unchanged,
using one explicit operator-selected acquisition operation, without adding
provider concepts, credentials, configuration, or network authority to HAC
core?

This is a documentation-only investigation. It implements no plugin, creates no
plugin repository, adds no dependency, and makes no architectural decision.
RFC-0078 remains the governing acquisition boundary.

## Outcome

**Outcome A — Tavily has a sufficiently small, concrete, evidence-backed shape
to merit a dedicated Tavily provider RFC under unchanged RFC-0078.**

This is a recommendation to consider that RFC, not provider selection,
acceptance, or implementation. Tavily's current Search API can receive the one
RFC-0078 query in one direct HTTPS request and return a ranked `results` list
whose useful entries already have `title`, `url`, and `content`. An independently
installed plugin can discard everything else, return at most five fresh built-in
three-field dictionaries, and leave RFC-0078 reconstruction plus complete
RFC-0077 validation as the sole HAC evidence authority.

The smallest credible shape is:

```text
hac external-information --plugin tavily --query QUERY --question QUESTION
  -> one selected, separately installed Tavily plugin
  -> one bounded POST to https://api.tavily.com/search
  -> JSON results[] only; bounded title/url/content normalization
  -> RFC-0078 reconstruction and complete RFC-0077 validation
  -> existing POST /v1/chat/sources
  -> unchanged ordinary capability=chat routing
```

The explicit query and API key reach Tavily. That is an operator-selected public
provider disclosure boundary, not a claim that a search result, provider rank,
or generated snippet is true, current, safe, or authoritative. Result URLs
remain provenance strings only: neither the plugin nor HAC may follow, resolve,
fetch, render, crawl, or otherwise act on them.

## Accepted boundary versus provider decision

RFC-0078 already fixes the caller edge, exact versioned entry-point group, one
explicit selected plugin, one asynchronous callable accepting only `query`, one
invocation, a concrete built-in `list[dict[str, str]]` containing exactly
`title`, `url`, and `content`, and complete fresh RFC-0077 reconstruction
before the existing source-grounded endpoint. It also fixes the zero-plugin
invariant, privacy-safe pre-routing failure, no fallback, and no ordinary-server
plugin authority. This investigation does not revisit those decisions.

RFC-0077 already fixes the downstream envelope: one through five ordered
sources; nonblank title, URL, and content; title at most 512 UTF-8 bytes, URL
at most 2,048, content at most 1,024, and all source fields together at most
20,480. It preserves supplied order without scoring, sorting, deduplication, or
repair. [RFC-0077](../RFC/RFC-0077-bounded-source-grounded-chat.md)

The provider-specific question is therefore narrow: can one separate Tavily
package make one bounded request to one fixed provider endpoint and normalize
the response into that existing closed representation? Current official
documentation supports that shape.

## Current Tavily facts

### Search endpoint, method, authentication, and direct HTTP

Tavily documents its API base URL as `https://api.tavily.com`, and its Search
endpoint as `POST /search`; its own cURL example is a direct JSON POST to
`https://api.tavily.com/search`. All endpoints use an API key in the required
`Authorization: Bearer <Tavily API key>` header. [Tavily API
introduction](https://docs.tavily.com/documentation/api-reference/introduction),
[Tavily Search API](https://docs.tavily.com/documentation/api-reference/endpoint/search)

The Search API's only required body field is a string `query`. A minimal first
plugin request can use just that required field plus fixed explicit bounding
choices, rather than exposing Tavily's optional topic, dates, domains, language,
country, safe-search, exact-match, or automatic-parameter controls through HAC.
[Tavily Search API](https://docs.tavily.com/documentation/api-reference/endpoint/search)

An SDK is not necessary: the official documentation supplies a complete direct
HTTP cURL request alongside its SDK examples. A future separate plugin can own
one compatible asynchronous HTTP client; it does not need `tavily-python`, the
Tavily CLI, or any Tavily dependency in HAC core.

### Results and result-count controls

The successful Search response is a JSON object with a ranked `results` array.
Each result documents `title`, `url`, and `content`; `content` is the
query-related content Tavily derives from the scraped URL. Score, raw content,
favicon, images, ID, response time, usage, request ID, and the echoed query are
provider data, not RFC-0078 candidate fields. [Tavily Search
API](https://docs.tavily.com/documentation/api-reference/endpoint/search),
[Tavily Python SDK result reference](https://docs.tavily.com/sdk/python/reference)

`max_results` currently defaults to 5 and has a documented range from 0 through
20. A later RFC can fix it to exactly 5, matching RFC-0077's maximum rather than
requesting extra provider results that the plugin would discard. `chunks_per_source`
currently defaults to 3 and ranges from 1 through 3; each chunk is documented as
at most 500 characters. The smallest first shape should fix
`chunks_per_source=1`, reducing provider-returned content before RFC-0078 and
RFC-0077 validation. It cannot guarantee RFC-0077's 1,024 UTF-8-byte `content`
limit because Tavily documents characters, not UTF-8 bytes. Complete RFC-0077
validation therefore remains authoritative, and the plugin must never truncate
or repair oversized content. This is a provider response-size control, not a
substitute for RFC-0077 byte validation or the plugin's raw response envelope.
[Tavily Search API](https://docs.tavily.com/documentation/api-reference/endpoint/search)

### Features excluded from the first shape

The later provider RFC should require `include_answer=false`,
`include_raw_content=false`, `include_images=false`, and
`include_image_descriptions=false`, and should not request usage, favicon, or
project/session/human tracking headers. Tavily describes `include_answer` as an
LLM-generated answer and `include_raw_content` as cleaned/parsed page content;
neither is needed for the accepted evidence contract. [Tavily Search
API](https://docs.tavily.com/documentation/api-reference/endpoint/search)

It should fix `auto_parameters=false` and an explicit `search_depth` rather
than let the provider choose a deeper request from query intent. Tavily says
automatic parameters can choose `advanced`, whereas explicit `basic` avoids
that choice. The first shape also excludes all other Tavily APIs: Extract,
Crawl, Map, and Research. Those APIs would add URL input, page extraction,
site navigation, asynchronous/multi-step work, or provider-generated research
beyond one acquisition call. [Tavily API
introduction](https://docs.tavily.com/documentation/api-reference/introduction),
[Tavily Search API](https://docs.tavily.com/documentation/api-reference/endpoint/search)

The first RFC should choose `search_depth=basic`: it is the documented default
and a balanced relevance/latency option. Tavily currently describes basic search
as one API credit per request; this is operational context only, not a durable
HAC cost guarantee or a reason to add core cost policy. [Tavily Search
API](https://docs.tavily.com/documentation/api-reference/endpoint/search),
[Tavily Credits & Pricing](https://docs.tavily.com/documentation/api-credits)

## Smallest provider-owned operation

### Package identity and exact destination

The later RFC can select one independently versioned distribution and existing
RFC-0078 entry-point identity:

```text
repository:         frian/home-ai-cluster-plugin-tavily
distribution:       home-ai-cluster-plugin-tavily
entry-point group:  home_ai_cluster.external_information_acquisition.v1
entry-point name:   tavily
```

It would expose only the accepted conceptual callable:

```python
async def acquire(query: str) -> list[dict[str, str]]
```

One invocation makes exactly one HTTPS request to the one literal destination:

```text
POST https://api.tavily.com/search
Content-Type: application/json
Authorization: Bearer <plugin-owned Tavily API key>

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
```

The query is passed unchanged. There is no query rewriting, model-generated
query, optional Tavily parameter surface, retry, pagination, second provider
request, fallback provider, project ID, session ID, human ID, cookie/session
workflow, result-URL request, Extract, Crawl, Map, or Research operation.

The exact literal HTTPS origin means an implementation must verify ordinary TLS
for `api.tavily.com`; it must not accept an endpoint/base-URL override, hostname
alias, insecure TLS mode, custom CA behavior, or environment proxy. It must
disable redirect following and environment/client configuration inheritance
(`follow_redirects=False` and `trust_env=False`, or exact equivalents), so a
redirect or `HTTP_PROXY`/`HTTPS_PROXY` setting cannot change the disclosed
destination. Redirect responses are a safe acquisition failure, never a second
request.

### Finite transport and response envelope

RFC-0078 correctly leaves transport values to the selected plugin. Tavily's API
documentation establishes the endpoint and request shape but not a HAC-suitable
response-byte ceiling or finite end-to-end deadline. A later Tavily RFC must
therefore select explicit finite values, including a total one-operation
deadline; connect, read, write, and pool timeouts; a connection limit; and a
decoded response-body maximum enforced while streaming before JSON parsing.
`Content-Length` may be an early rejection only, never the enforcement method.

The SearXNG provider RFC demonstrates a comparable bounded policy (30-second
total, 2/20/5/2-second component timeouts, 1 MiB decoded response) but those
numbers are not automatically Tavily's values. A Tavily RFC must independently
justify its chosen values and focused transport proof; copying them would be a
provider-specific decision, not a core contract.

### Deterministic normalization

The provider's ranked order is output only, not truth, authority, freshness,
or a HAC ranking policy. The plugin should implement only this deterministic
algorithm:

1. Accept only a successful HTTP response within the decoded byte bound, valid
   JSON, a top-level object, and a concrete `results` list.
2. Inspect the received list once in provider order. Ignore each non-mapping
   entry and each entry whose `title`, `url`, or `content` is not a nonblank
   string.
3. For each usable entry, copy exactly those values into a new ordinary built-in
   dictionary. Do not copy score, raw content, ID, dates, images, favicon, query,
   answer, usage, response time, request ID, or any other provider value.
4. Preserve surviving order and stop after five candidates. Do not score,
   rerank, sort, deduplicate, enrich, verify, truncate, or repair values.
5. If none survive, fail acquisition. Otherwise return the closed list and let
   the RFC-0078 caller construct fresh values and apply all RFC-0077 validation.

Skipping malformed provider entries is not a relaxation of RFC-0077: a selected
candidate that later violates any RFC-0077 limit causes the entire operation to
fail before routing. The plugin must not trim any field to make it fit.

## Credential and disclosure analysis

Tavily documents Bearer API-key authentication and recommends environment
variables or a secure secrets manager rather than hardcoding keys. Its separate
CLI also documents three broader credential paths: a key stored in
`~/.tavily/config.json`, browser OAuth tokens under `~/.mcp-auth/`, or
`TAVILY_API_KEY`; the CLI automatically adds a session identifier. [Tavily API
key management](https://docs.tavily.com/documentation/best-practices/api-key-management),
[Tavily CLI](https://docs.tavily.com/documentation/tavily-cli)

The narrowest credible first-plugin choice is to require one nonblank
`TAVILY_API_KEY` environment variable at explicit acquisition invocation, read
only by the Tavily plugin and used only to form the one Authorization header.
An operator may arrange that variable through their own operating-system secret
or secrets-manager mechanism; HAC does not discover, parse, retain, or
configure it. The plugin should not inherit the Tavily CLI's config file, OAuth
token store, CLI session tracking, project ID, session ID, human ID, or a second
credential/configuration fallback. An inline CLI key is incompatible with
RFC-0078's closed caller inputs and would expose the secret in shell history.

Missing, blank, malformed, or rejected credentials are plugin/acquisition
failures. The query and API key must never enter HAC evidence, source-grounded
request, routing, history, logs, metrics, traces, results, errors, remote
transport, runtime adapters, or retained proof. The only caller-visible
pre-routing failure remains RFC-0078's bounded
`external-information-acquisition-failed`; it must not disclose the query, key,
provider endpoint, HTTP status/body, request ID, exception, or configuration
detail. The plugin itself must add no default logging, cache, telemetry, raw
response store, or persistence.

## Provider-specific decisions for a later RFC

A dedicated Tavily RFC would need to decide all of the following, without
altering RFC-0077 or RFC-0078:

1. The separate package identity above, including the exact existing entry-point
   group and `tavily` name.
2. The one literal `https://api.tavily.com/search` destination, ordinary TLS
   verification, no endpoint override, no redirects, and disabled ambient proxy
   or client-environment inheritance.
3. The exact one-request JSON body: unchanged query, fixed `basic` depth,
   `max_results=5`, `chunks_per_source=1`, fixed false feature flags, and no
   provider tracking headers or other search controls. The RFC must retain
   complete RFC-0077 validation because Tavily's one-chunk character maximum is
   not a UTF-8-byte guarantee, and must prohibit truncation or repair.
4. Explicit finite total/connect/read/write/pool timeouts, connection limits,
   and incrementally enforced decoded response-size maximum; no retry,
   pagination, fallback, or subsequent provider API call.
5. The plugin-only `TAVILY_API_KEY` environment-variable mechanism, including
   nonblank validation and no CLI-file/OAuth/project/session/human-ID fallback;
   no HAC configuration or generic secrets system.
6. The exact JSON-success rule and deterministic skip/copy/stop-after-five
   normalization, including zero usable candidates as failure and no
   truncation, scoring, sorting, deduplication, enrichment, dates, or provider
   metadata.
7. The privacy-safe failure rule and focused post-acceptance tests: exactly one
   destination/request, TLS and redirects/proxies, finite limits, no result-URL
   traffic, no sensitive retention, safe failures, and unchanged RFC-0078
   zero-plugin/ordinary-server behavior.

These are provider-package decisions only. They do not authorize generic HAC
configuration, secrets, provider selection, cost policy, lifecycle management,
network fallback, a new capability, a server endpoint, automatic Chat
acquisition, or retained configuration investigation.

## Sources consulted

Provider claims were checked against current official Tavily documentation on
2026-08-30:

- [API introduction](https://docs.tavily.com/documentation/api-reference/introduction)
- [Search API](https://docs.tavily.com/documentation/api-reference/endpoint/search)
- [Credits & Pricing](https://docs.tavily.com/documentation/api-credits)
- [API key management](https://docs.tavily.com/documentation/best-practices/api-key-management)
- [Tavily CLI](https://docs.tavily.com/documentation/tavily-cli)
- [Python SDK result reference](https://docs.tavily.com/sdk/python/reference)
