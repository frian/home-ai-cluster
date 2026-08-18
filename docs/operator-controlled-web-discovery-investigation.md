# Operator-Controlled Web Discovery Investigation

Status: Complete

## Question

> Is there a small, useful, operator-controlled boundary that can turn one
> explicit search query into a bounded set of current Web result snippets for
> Home AI Cluster Chat without requiring a proprietary search API account,
> giving runtimes Internet authority, fetching arbitrary result URLs,
> embedding unsupported search-engine scraping inside HAC, or introducing a
> large new search subsystem?

This is a documentation-only investigation. It authorizes no implementation,
RFC, dependency, configuration, service installation, search endpoint, network
access, capability, or change to runtime, routing, request, result, or history
behavior.

## Outcome

**Outcome B — an operator-owned, already-running private SearXNG service is
credible enough to justify a future narrowly scoped RFC, provided HAC does not
own SearXNG's installation, lifecycle, updates, or engine configuration.**

This is not a finding that self-hosting is free of outside dependencies. SearXNG
is a metasearch service: it sends the explicit query to the external engines an
operator has configured. It removes the need for HAC to hold one dedicated
proprietary search-API account, but it does not remove dependence on upstream
search services, their availability, their rules, or their result quality.

The credible future shape is deliberately narrower than a general search
integration:

```text
explicit operator question + explicit operator query
  -> operator-owned already-running private SearXNG service
  -> one bounded JSON result set
  -> HAC-normalized title / URL / snippet evidence
  -> source-grounded ordinary Chat
  -> local or already-declared trusted-remote inference
```

The future RFC would still need to decide the endpoint trust scope, exact
closed request shape, independent HTTP/result bounds, failure behavior, and the
source-grounded Chat contract. This investigation neither chooses loopback over
a private-LAN endpoint nor permits arbitrary configured URLs. It does not
authorize a provider or search-service abstraction.

Operator-owned browser, command, or helper retrieval remains the current
supported workflow until such an RFC is accepted and separately implemented.
RFC-0064 remains Rejected; HAC must not fetch a result URL or other arbitrary
public URL.

## Scope and non-goals

The concrete need is **current-information discovery**, not arbitrary page
retrieval, autonomous browsing, or general Web research. The investigation
keeps two problems distinct:

```text
discovery
  explicit query -> bounded result metadata/snippets

source-grounded Chat
  bounded evidence -> ordinary Chat execution + supplied-source provenance
```

Discovery is the subject here. The prior fixed-provider investigation remains
useful evidence that hidden prompt concatenation is not a truthful evidence
contract, but its Tavily-specific proposal is not an accepted project decision.

This investigation does not authorize:

- following, fetching, rendering, validating for connection, or otherwise
  using a returned result URL as a destination;
- a `search`, `web`, `browse`, `retrieve`, or `research` capability;
- model-generated, model-rewritten, automatic, or repeated queries;
- runtime-adapter or selected-node Internet authority;
- a browser, crawler, search index, RAG, cache, database, persistence, tool
  framework, agent system, Docker/Compose, or service supervision;
- installing, configuring, starting, stopping, updating, or operating SearXNG,
  YaCy, Whoogle, or another service; or
- a generic provider, search-service, credential, or endpoint abstraction.

## Current main baseline

This investigation reviewed GitHub `main` at
`218c4f91135f2e024c2b3a8516676e841dc9b2aa`.

### Existing Chat and caller boundary

The installed native `hac chat` / `home-ai-cluster chat` surface accepts one
ordinary operator message and sends it to the fixed loopback `POST /v1/chat`
endpoint. It constructs a `ClusterRequest` containing ordered `ChatMessage`
values, the existing `chat` capability, and constraints. The public endpoint
returns `ClusterResult` with content and execution attribution only.

There is currently no external-query field, source list, source byte bound,
source provenance result, or discovery behavior in the native command,
`ClusterRequest`, `ClusterResult`, or `/v1/chat`. The existing direct native
client has a finite per-invocation HTTPX timeout; it is not a discovery client.

The closed remote transport currently carries only ordinary ordered-message
Chat, Summarize, or Classify request variants. A future source-grounded Chat
request would need its own truthful closed transport envelope rather than
smuggling snippets into an ordinary caller-owned message. The existing
prompt-free request history allowlist retains only status and routing-account
fields, not request or result content. Any future discovery path must preserve
that privacy boundary.

### Governing boundaries

RFC-0064 was rejected because the existing high-level HTTP path could not
establish the required hostname-to-connected-public-peer invariant for an
arbitrary caller-selected URL. Its literal-IP-only narrowing was not useful
enough. A search-result URL is therefore provenance data only, never an HAC
network instruction.

The current fixed-provider investigation establishes a narrower architectural
fact: caller-local acquisition from one selected destination is materially
different from arbitrary caller-selected URL retrieval. It also establishes
that acquired evidence needs an explicit cluster-owned contract rather than
hidden prompt formatting. It does not select Tavily, SearXNG, or any other
service for the project.

## Evaluation criteria

Any credible future discovery direction must preserve all of the following:

- one explicit operator query; no model-selected destination or query;
- discovery completed at the caller edge before ordinary `chat` routing;
- no runtime adapter, model, or selected node provider/search HTTP authority;
- no result-URL fetching, no retries, pagination, search loop, or fallback to
  stale ordinary Chat after an explicitly assisted attempt fails;
- no new executable capability or node selected for Internet egress;
- independent request, response-byte, result-count, field, aggregate-evidence,
  timeout, validation, and privacy-safe failure limits;
- ordinary Chat fully usable without a search account, service, or Internet
  connection; and
- no HAC retention of query, result, raw response, source URL, or credential by
  default.

## Candidate 1 — private SearXNG

### What SearXNG provides

SearXNG is a self-hostable metasearch engine, not its own comprehensive Web
index. Its documented Search API accepts `GET` or `POST` at `/` or `/search`;
the required `q` value is passed to external search services. JSON output is
available only when the operator enables the `json` format in `settings.yml`.
The same documentation warns that many public instances disable non-HTML
formats. [SearXNG Search API](https://docs.searxng.org/dev/search_api.html)

Its main result representation contains a title, a URL, and `content` described
as an extract or description; it can also carry `publishedDate` where an engine
provides it. This is sufficient in principle for a future bounded
title/URL/snippet evidence shape without fetching a result URL. It is not full
article content, a factual guarantee, or proof that every engine produces a
published date. [SearXNG main result type](https://docs.searxng.org/dev/result_types/main/mainresult.html)

The API exposes an optional `time_range` of day, month, or year only for engines
that support it. It is therefore not a universal currentness guarantee and
would need an explicit future decision rather than becoming implicit query
rewriting. [SearXNG Search API](https://docs.searxng.org/dev/search_api.html)

### Privacy and upstream dependence

For a private instance, the operator controls the instance code, logging
settings, and local configuration. SearXNG documents that it omits cookies to
external search engines and creates a random browser profile per request, but
the upstream engine sees the IP address of the SearXNG instance (or its
configured proxy/Tor exit), not a promise that the query never leaves the
operator's environment. [Why use a private instance?](https://docs.searxng.org/own-instance.html)

The relevant distinction is:

```text
operator -> private SearXNG       local/private operator trust boundary
SearXNG  -> configured engines    external search-service boundary
```

Thus a private SearXNG service can avoid a dedicated HAC-to-proprietary-search
API contract and API key. It cannot claim independence from external search
engines, their blocks/CAPTCHAs, changes, ranking, terms, or their observation
of the forwarded query and the instance's network identity.

### Operation and lifecycle

SearXNG can run directly with a loopback `bind_address`, and its documented
direct web-app check uses `127.0.0.1:8888`. Its server settings default
`limiter` and `public_instance` to false; Valkey is required for the limiter,
not for a small local instance with that feature disabled. A reverse proxy is
deployment guidance for exposed instances, not a prerequisite for a direct
single-user loopback service. [SearXNG server settings](https://docs.searxng.org/admin/settings/settings_server.html)

That does not make the service operationally free. The non-container reference
installation creates a system user, installs OS packages and Python build
dependencies, clones SearXNG, creates a virtual environment, installs its
dependencies, and describes a uWSGI service. SearXNG's installation guidance
recommends either its container path or installation script for ordinary
installs and says operators should stay current with migrations. [Step-by-step
installation](https://docs.searxng.org/admin/installation-searxng.html),
[installation overview](https://docs.searxng.org/admin/installation), and
[uWSGI service setup](https://docs.searxng.org/admin/installation-uwsgi.html)

Engine configuration is also real continuing work. SearXNG's own settings
record suspension periods for access-denied, CAPTCHA, rate-limit, and
Cloudflare/Google CAPTCHA conditions. This is evidence that engine failures and
upstream countermeasures are normal operational concerns, not exceptional
conditions HAC can hide. [SearXNG search settings](https://docs.searxng.org/admin/settings/settings_search.html)

### Ownership alternatives

| Boundary | Assessment |
| --- | --- |
| HAC installs, starts, stops, updates, or configures SearXNG | Not credible for the first boundary. It turns HAC into a service manager and makes it responsible for a Python service, engines, updates, and recovery. |
| Operator independently runs a private SearXNG service; HAC may later use one explicit trusted endpoint | Credible enough for a future RFC. The service remains an optional operator prerequisite, analogous in ownership to an operator-selected local runtime rather than an HAC subsystem. |
| HAC selects a public SearXNG endpoint at request time | Rejected. This restores third-party endpoint selection and makes privacy, availability, and destination authority unbounded. |

The second row is the Outcome B candidate, not a current workflow. It requires
an operator who accepts the operational maintenance burden. A permanently
maintained search service can still be worse for some operators than explicit
external search or manual retrieval; self-hosting is not automatically the
boring solution.

### Endpoint trust remains an RFC question

The SearXNG service endpoint is unlike Tavily's fixed project-owned URL. A
future RFC must define who configures it, how it is represented, and the
acceptable destination scope. This investigation identifies, but does not
select, these possibilities:

| Scope | Investigation finding |
| --- | --- |
| Fixed loopback endpoint | Smallest apparent trust surface; directly supported by SearXNG's bind settings. It still needs a closed configuration and HTTP/failure contract. |
| Explicitly configured private-LAN endpoint | Potentially useful where an operator runs SearXNG on a different trusted machine, but it needs explicit transport-address validation, trust, credential, redirect, and privacy evidence. |
| Arbitrary URL | Not credible. It would reintroduce caller-controlled destination authority addressed by RFC-0064 and is not a SearXNG feature worth special-casing. |

Neither a local endpoint nor a JSON response is automatically safe. A future
boundary must treat the service's title, URL, snippet, and optional date as
untrusted data; disable ambient proxy authority where supported; choose redirect
and credential policy explicitly; and independently bound the response before
Chat routing. A local service may still return attacker-controlled URLs and
content. HAC must never follow those URLs.

### Are snippets useful enough?

Yes, for the constrained question. A bounded set of result extracts plus title
and provenance URL can give a local model current leads, names, dates, and
short factual context. It cannot make claims that require complete source text,
the full context of a page, or reliable citation. The appropriate response to a
weak snippet is a safe failure or an operator's existing manual retrieval
workflow—not automatic result-page fetching.

The future evidence contract would need to reject missing/invalid snippets or
otherwise explicitly decide whether an entry with no extract is useful. It must
apply its own byte/count/aggregate limits regardless of SearXNG engine settings
or locality.

## Candidate 2 — public SearXNG instance

Rejected. A public SearXNG endpoint removes neither third-party trust nor
service lifecycle risk; it transfers those concerns to an unknown administrator.
SearXNG states that public-instance users must trust the administrator and
cannot know whether requests are logged, aggregated, or sent to a third party.
It also describes abuse-driven CAPTCHAs and IP bans that can reduce results.
[SearXNG private-instance guidance](https://docs.searxng.org/own-instance.html)

JSON may be disabled, endpoint and engine configuration vary per administrator,
and a public service can rate-limit or disappear. Permitting an operator or
model to enter an arbitrary public SearXNG URL would additionally recreate the
destination problem RFC-0064 rejected. This candidate is neither a
non-proprietary privacy solution nor a stable project-owned boundary.

## Candidate 3 — direct search-engine Web-interface access

Rejected. The relevant issue is durable HAC ownership, not whether a one-off
parser works today. SearXNG's own DuckDuckGo engine documentation shows that
the no-JavaScript HTML/Lite paths are Web form surfaces, not a stable HAC API:
the implementation handles request-specific `vqd` values and detects CAPTCHA
responses. Its documentation also notes malformed DuckDuckGo result links that
should be ignored. [SearXNG DuckDuckGo engine](https://docs.searxng.org/dev/engines/online/duckduckgo.html)

Copying such engine behavior would make HAC a permanent provider-specific
scraper responsible for changing HTML/form/token/anti-bot behavior. A search
API provider itself distinguishes sanctioned structured access from brittle,
often-disallowed parsing of rendered result pages. [Brave's API explanation](https://brave.com/search/api/glossary/web-search-api/)

No documented, supported machine-consumption contract was found for the named
ordinary HTML surfaces that would justify making them HAC protocol. The project
must not copy SearXNG engine implementations or use undocumented scraping as a
shortcut.

## Candidate 4 — Whoogle

Rejected with minimal further investigation. The official repository announced
on 24 July 2026 that Whoogle no longer returns results because Google ended the
JavaScript-free access it depended on, and that active development, releases,
fixes, reviews, and support have ended. [Whoogle project status](https://github.com/benbusby/whoogle-search)

This is direct historical evidence of the exact brittle maintenance dependency
that makes direct search-result HTML scraping unsuitable for HAC.

## Candidate 5 — YaCy or a self-hosted search index

Rejected for this need. YaCy's official project describes a full search-engine
application with a server-hosted search index, a production crawler, and a
scheduler to keep the index fresh; it also supports peer-to-peer index exchange.
It requires Java 17 or later and a build/run or container lifecycle, although it
has HTTP XML/JSON interfaces. [YaCy search server](https://github.com/yacy/yacy_search_server)

That answers a different problem: owning an index and its crawl freshness.
Useful current-Web coverage would require crawl/index/storage/service decisions
far beyond a single explicit discovery call. Its API does not make its crawler,
index, Java, storage, and lifecycle burden a small fit for HAC's need.

## Candidate 6 — keep discovery outside HAC

Retained as the supported baseline. An operator can use a browser, command, or
private helper, then provide bounded text to existing Chat. It has more manual
work and does not preserve project-owned acquired-source provenance, but it
avoids a new endpoint, service trust, configuration, and evidence contract.

It remains smaller for operators unwilling to run and maintain SearXNG. Outcome
B is a future RFC candidate, not a reason to remove or disparage this workflow.

## Dependency and trust comparison

| Candidate | Code dependency in HAC | Service dependency | Account/API key | External search dependency | Operational maintenance | Privacy/trust boundary |
| --- | --- | --- | --- | --- | --- | --- |
| Operator-owned private SearXNG, already running | None now; a future RFC could use existing HTTPX directly | Optional operator-operated SearXNG | No dedicated HAC search API key required | Yes: configured engines receive the query | Operator owns install, engine choice, updates, service health, and engine blocks | Operator trusts their service; upstream engines see query and instance/proxy IP; returned data remains untrusted |
| HAC-owned SearXNG | Would add a client plus service-management responsibility | HAC-managed SearXNG | No dedicated API key necessarily | Yes | HAC would inherit all service/engine lifecycle | HAC becomes responsible for another networked service; out of scope |
| Public SearXNG | A client only | Third-party public service | Usually no project API key, but no meaningful privacy gain | Yes | Instance administrator and public availability | Trust unknown administrator plus upstream engines; logging cannot be ruled out |
| Direct HTML search scraping | Provider-specific parser/maintenance | None | Usually no API key | Yes, directly | Continuous anti-bot/HTML/token maintenance | Query goes directly to engines; HAC owns brittle scraper behavior |
| Whoogle | Client plus abandoned service integration | Self-hosted service | No dedicated API key necessarily | Google HTML access | Unsupported/ended project | Same scraping fragility plus abandoned lifecycle |
| YaCy | Client plus a large integration decision | Java/index/crawler service | No dedicated API key necessarily | Either own crawl/index or peer network | Crawl/index/storage/scheduler/updates | Much broader local and network authority |
| Operator-owned manual retrieval | None | Operator chooses tools | Operator chooses | Operator chooses | Operator-owned outside HAC | No new HAC external boundary |

## Authority, routing, and privacy constraints for any future RFC

The only candidate worth further RFC work has these ownership domains:

| Domain | Permitted responsibility |
| --- | --- |
| Operator/native caller edge | Explicit opt-in; separate query; optional trusted SearXNG endpoint prerequisite; one discovery request; response validation and normalization. |
| HAC core/routing | Source-grounded request semantics, bounds, deterministic projection, ordinary `chat` routing, and provenance/result semantics. |
| Runtime adapter/model | Receives only the cluster-owned text projection; no SearXNG endpoint, credential, query authority, result-URL authority, or tools. |
| SearXNG | External discovery service outside the HAC inference trust boundary; receives the explicit query and returns untrusted result data. |
| Upstream engines | Receive forwarded query from SearXNG and observe its instance/proxy network identity. |
| Declared remote HAC node | May receive normalized question/evidence only if ordinary trusted remote Chat is separately allowed; never SearXNG endpoint authority, configuration, or credential. |

Acquisition must complete before candidate collection and routing. It cannot
select a node, runtime, model, adapter, capability, constraint, or fallback.
Ordinary Chat remains local-first and unchanged when the operator does not make
the explicit assisted request. If a future source-grounded result lists sources,
the list means only “sources supplied to this model execution,” not factual or
sentence-level citation correctness.

## What a future RFC must prove and decide

Outcome B supports one *future* narrow RFC question, approximately:

> Should HAC support one explicit caller-local query to one independently
> operated private SearXNG endpoint, followed by bounded normalized snippets and
> source-grounded ordinary Chat, without result-URL fetching or SearXNG
> lifecycle ownership?

Before such an RFC could be accepted, focused evidence must make the following
concrete:

1. The endpoint scope: fixed loopback, explicitly declared private-LAN address,
   or another closed operator configuration boundary. Arbitrary URLs are out.
2. The exact one-request JSON-capable Search API contract and operator
   prerequisite that JSON output is enabled.
3. No destination redirect, ambient proxy, cookie, or credential policy can be
   inferred from SearXNG's browser-oriented defaults; the RFC must state it.
4. One finite request body, response body, result count, per-field, aggregate
   evidence, and timeout contract, with privacy-safe fail-closed behavior.
5. The minimum accepted normalized fields—at most title, URL, snippet, and only
   an optional date if its semantics can be validated—without engine/config
   metadata becoming HAC semantics.
6. The explicit source-grounded Chat request/result, deterministic untrusted
   evidence projection, remote envelope, source output, and prompt-free history
   boundary.
7. A focused operational proof that an independently operated single-user
   instance can supply useful bounded snippets under the selected engine
   configuration, including expected engine failure behavior, without HAC
   installing or supervising it.

It must not turn the first service into a provider abstraction, add provider
selection, allow result-page retrieval, or reframe discovery as a routable
capability. It must not turn SearXNG's own engine configuration into HAC
configuration.

## Consequence for Draft RFC-0076

Draft PR #471 is non-governing and remains unmodified by this investigation.
Its Tavily-specific acquisition direction assumes the proprietary account,
credential, cost, and provider-lifecycle trade-off that the operator has now
rejected. It should therefore not proceed toward acceptance unchanged.

If the project later acts on this investigation, it should replace the
Tavily-specific acquisition question with one concrete operator-controlled
SearXNG boundary, or first split the source-grounded Chat contract from the
discovery choice if review finds that separation necessary. The source-grounded
evidence/provenance insight remains applicable; it is not a reason to accept
or implement Draft RFC-0076.

## Sources consulted

All technical claims below use primary project or official sources current on
2026-08-18:

- [SearXNG Search API](https://docs.searxng.org/dev/search_api.html)
- [SearXNG main result type](https://docs.searxng.org/dev/result_types/main/mainresult.html)
- [SearXNG private-instance and privacy guidance](https://docs.searxng.org/own-instance.html)
- [SearXNG server settings](https://docs.searxng.org/admin/settings/settings_server.html)
- [SearXNG limiter documentation](https://docs.searxng.org/admin/searx.limiter)
- [SearXNG installation overview](https://docs.searxng.org/admin/installation)
- [SearXNG step-by-step installation](https://docs.searxng.org/admin/installation-searxng.html)
- [SearXNG uWSGI setup](https://docs.searxng.org/admin/installation-uwsgi.html)
- [SearXNG search settings](https://docs.searxng.org/admin/settings/settings_search.html)
- [SearXNG DuckDuckGo engine](https://docs.searxng.org/dev/engines/online/duckduckgo.html)
- [Whoogle official repository/status](https://github.com/benbusby/whoogle-search)
- [YaCy official search-server repository](https://github.com/yacy/yacy_search_server)
- [Brave's official API/scraping distinction](https://brave.com/search/api/glossary/web-search-api/)
