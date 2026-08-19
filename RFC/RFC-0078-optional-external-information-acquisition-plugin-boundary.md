# RFC-0078: Optional External-Information Acquisition Plugin Boundary

Status: Accepted

Date: 2026-08-19

Author: frian

## Summary

This RFC proposes one optional, explicitly selected, separately installed
Python acquisition-plugin boundary for one operator-requested external
information operation. The operation is a distinct `hac external-information`
one-shot caller edge, not ordinary HAC server startup or request handling. Its
caller process discovers and lazy-loads the selected plugin, invokes it once,
constructs fresh RFC-0077 evidence/request values from its bounded candidate
data, and then calls the existing `POST /v1/chat/sources` boundary. Only that
validated source-grounded request begins existing ordinary `capability=chat`
routing.

The proposed flow is deliberately closed:

```text
explicit operator external-information request and query
        ↓
one `hac external-information` caller process
        ↓
one explicitly selected optional acquisition plugin
        ↓
bounded candidate title/url/content values
        ↓
fresh RFC-0077 SourceEvidence[] and SourceGroundedChatRequest
        ↓
POST /v1/chat/sources
        ↓
ordinary capability=chat routing
```

This is an acquisition boundary, not a HAC capability, provider interface, or
general plugin system. It selects no provider and authorizes no production
implementation in this acceptance change. With zero installed acquisition
plugins, HAC startup, ordinary Chat, RFC-0077 supplied-source Chat, routing,
adapters, and history remain unchanged and no plugin module is imported.

## Problem

RFC-0077 accepts a bounded, provider-neutral evidence seam but intentionally
leaves acquisition outside HAC. The completed optional-external-integration
investigation found that a future explicit acquisition exception can remain
small only if provider HTTP behavior, credentials, configuration, and parsing
stay outside core, while an installed integration does not become an automatic
network authority.

Without a narrow boundary, a provider-specific core import or caller-selected
module path would either couple HAC to a provider or give HAC a durable
arbitrary-import configuration surface. A generic framework would prematurely
solve unrelated extension categories. HAC instead needs one inspectable,
operator-owned packaging seam for this one pre-RFC-0077 acquisition category.

RFC-0064 remains Rejected. In particular, this RFC does not revive arbitrary
public URL acquisition: a provenance URL returned as RFC-0077 evidence never
grants HAC authority to resolve, fetch, follow, render, or otherwise act on it.

## Goals

This RFC proposes to:

- keep acquisition before RFC-0077 validation and ordinary Chat routing;
- make acquisition an explicit, separate, finite `hac external-information`
  one-shot caller edge to an already running HAC server;
- use one category-specific Python entry-point group for separately installed
  acquisition distributions;
- require one caller/operator-selected exact plugin name and one invocation per
  external-information operation;
- keep the core contract limited to an explicit query and ordered candidate
  source evidence;
- revalidate every successful plugin result against the complete RFC-0077
  source-evidence contract before routing; and
- preserve zero-plugin and ordinary-HAC behavior exactly.

## Non-goals

This RFC does not introduce or authorize:

- a generic plugin framework, `PluginManager`, generic plugin hierarchy,
  `SourceProvider`, generic plugin registry, lifecycle API, health subsystem,
  configuration system, filesystem scanning, repository scanning, or arbitrary
  module-import configuration;
- a `web`, `search`, `browse`, `retrieve`, or `research` capability, node, or
  routing rule;
- a FastAPI acquisition endpoint, acquisition-plugin startup hook, plugin use
  in ordinary request handling, or any change to ordinary `hac chat` behavior;
- automatic provider selection, ranking, preference policy, arbitration,
  fallback, retry through another provider, or any operation without exact
  caller/operator selection;
- a provider, provider SDK, provider dependency, provider configuration,
  credential scheme, endpoint, cost policy, or service lifecycle;
- arbitrary public URL fetch, result-URL following, redirect following, page
  fetching, a browser, crawler, scraper, model-directed acquisition, or
  repeated research loops;
- plugin influence over capability selection, candidate collection, routing,
  node selection, topology, fallback, runtime-adapter selection, request
  history, or results;
- a database, daemon, Docker, Kubernetes, worker, thread-based timeout runner,
  subprocess, IPC, container, or plugin sandbox/isolation architecture; or
- a revision to RFC-0077 or reopening RFC-0064.

## Proposal

### One narrowly discovered category

The sole entry-point group is:

```text
home_ai_cluster.external_information_acquisition.v1
```

It is intentionally named for external-information acquisition rather than for
plugins in general, source providers, or an executable capability. The `.v1`
suffix belongs to this one closed category; it does not establish a general
plugin-versioning scheme or permission to add groups for other categories.

A plugin is a separately installed Python distribution that publishes one named
entry point in this group. The `hac external-information` caller edge uses
`importlib.metadata.entry_points()` only to inspect this group and locate the
one exact name selected for its explicit operation. Entry-point metadata
discovery must not import a plugin. HAC does not scan the filesystem, a
checkout, a `plugins/` directory, or arbitrary configured import strings.

The selected name is a caller-edge value, not a provider recommendation or a
core configuration preference. It must be a non-blank exact entry-point name
of at most 64 UTF-8 bytes. A name is usable only when exactly one matching entry
point exists in the group. Installation means only that a distribution is
available for explicit selection; it neither authorizes network access nor
changes startup or ordinary HAC behavior.

Discovery occurs only within an explicit external-information operation, after
the caller has selected its exact plugin name. HAC startup and ordinary Chat do
not inspect this group and never import a plugin merely because one is
installed.

### Explicit operation and callable contract

The operator invokes exactly this new finite caller action:

```text
hac external-information --plugin NAME --query QUERY --question QUESTION
```

It is an explicit non-interactive one-shot client, following the existing HAC
one-shot request convention: it performs one finite operation against an
already running server and exits. It is not a new executable capability. The
only HAC request it sends is the existing `POST /v1/chat/sources` body after
successful acquisition validation; it does not add an acquisition route or
alter ordinary `hac chat` input, output, startup, or request handling.

One operation has three caller-supplied values: `NAME`, the exact selected
entry-point name; `QUERY`, the exact operator-requested acquisition query; and
`QUESTION`, the RFC-0077 operator question. `QUESTION` is not supplied to the
plugin; it remains the later source-grounded question. `QUERY` is the only
plugin input. It must be non-blank and no more than 4,096 UTF-8 bytes, a
caller-owned finite contract bound. There is no plugin context object in the
first contract: the caller passes no provider, routing, remote, topology,
credential, or configuration context to the selected acquisition callable.

The loaded entry point must be an asynchronous callable with this conceptual
contract:

```text
async acquire(query: str) -> list[dict[str, str]]
```

The return representation is deliberately built-in Python data, not an import
from `home_ai_cluster.core.models` or another HAC package API. The caller
accepts only a concrete `list` of one through five concrete `dict` values. Each
dictionary has exactly these three string keys and no others:

```text
title
url
content
```

It does not consume a generator, stream, callback, iterator, object, or
provider-specific result representation. The caller invokes the selected
callable exactly once, constructs fresh RFC-0077 `SourceEvidence` values from
those dictionaries, and then constructs and fully validates a fresh
`SourceGroundedChatRequest(question=QUESTION, sources=sources)`. Complete
RFC-0077 validation includes the closed field set, individual title/URL/content
bounds, source count, aggregate evidence bound, and canonical projection bound.
Only after that succeeds does the caller send the existing
`POST /v1/chat/sources` body. No candidate may reach that endpoint, candidate
collection, remote transport, or a runtime adapter before validation succeeds.

The existing HAC orchestration and transport surfaces are asynchronous. The
callable is therefore asynchronous as well, avoiding an adapter, executor, or
parallel execution framework solely for this boundary. A plugin must not
receive a `ClusterRequest`, routing candidates, runtime adapters, remote
clients, or a source-grounded execution result. Its result contains only
ordered candidate title/URL/content dictionaries: no provider score, rank,
request ID, raw response, credential, endpoint, configuration, or
provider-specific field may cross the caller/core contract.

### Compatibility and lazy loading

The versioned entry-point group is the sole compatibility mechanism. The `v1`
in `home_ai_cluster.external_information_acquisition.v1` identifies the exact
callable and three-field return contract defined here. There is no additional
plugin API-version attribute: that would duplicate the same compatibility fact
without improving compatibility or safety.

A selected entry point in this group is compatible only if lazy loading yields
the asynchronous callable defined above. A different incompatible contract
requires a later RFC and a different explicitly named entry-point group; HAC
must not negotiate, range-match, guess, adapt, or discover multiple groups at
runtime. A selected incompatible plugin fails that operation before routing and
HAC does not try another installed plugin.

### Ownership and trust boundary

The separate caller edge may only inspect this one group, locate the exact
selected name, lazy-load it for the explicit operation, check compatibility,
invoke the narrow callable once, construct and validate fresh RFC-0077 values,
send the accepted source-grounded body to the existing endpoint, and normalize
an acquisition-boundary failure. The ordinary HAC server process must not
discover, import, configure, or invoke acquisition plugins merely because they
are installed. HAC owns no provider HTTP client, request format, response
parser, credential, endpoint, provider configuration, provider health, or
provider retry behavior.

The selected plugin owns its provider/service request, request formatting,
response parsing, finite provider-specific connection/read/request limits, and
normalization to candidate title/URL/content dictionaries. The caller/core
contract passes no credential or provider configuration to the plugin.
Configuration and credentials are entirely operator-owned plugin state. A
concrete provider plugin must define its own explicit configuration and
credential mechanism before that provider is implemented; RFC-0078 creates no
generic HAC plugin configuration or secrets system. Such values must never
enter `SourceEvidence`,
`SourceGroundedChatRequest`, `ClusterRequest`, routing, remote transport,
runtime adapters, source-grounded results, default history, logs, metrics,
traces, or retained proof material.

A plugin is trusted Python code explicitly installed by the operator. Package
installation is the trust decision; this mechanism is not a sandbox. HAC does
not add containers, subprocesses, daemons, IPC, generic workers, or fake
isolation guarantees. Network disclosure occurs only because the operator
explicitly invokes this operation and selects the plugin that owns that
provider/service connection.

### Bounds and failure behavior

The caller edge enforces the 4,096-byte non-blank query bound, exactly one
selected name, exactly one invocation, the closed concrete list/dictionary
return representation, and the complete RFC-0077 evidence envelope. Those are
caller/plugin-contract boundaries it can
actually enforce. It does not claim an end-to-end deadline for arbitrary
in-process Python and must not add threads, workers, subprocesses, or a generic
timeout executor to imply that it can forcibly interrupt a plugin.

Each plugin instead owns finite provider-specific transport, connect, read, and
request limits for its one explicit acquisition call. The core does not expose
or standardize those provider-specific values in this first boundary. Oversized
or invalid returned evidence is rejected by complete RFC-0077 revalidation,
regardless of any plugin-local limits.

The following conditions are all one privacy-safe
`external-information-acquisition-failed` operation failure before ordinary
routing:

- selected entry point is missing or duplicated;
- selected plugin is incompatible;
- selected plugin fails to load or import;
- plugin configuration is unavailable or invalid;
- the acquisition call fails;
- an unexpected plugin runtime exception occurs; or
- the return is not a concrete bounded candidate list or fails RFC-0077
  validation.

The caller-visible result is the fixed bounded failure code only. It must not
reveal credentials, configuration, query, endpoint, provider identity, raw
response, import detail, stack trace, or private topology. Such a failure must
not prevent HAC startup, create a `ClusterRequest`, enter candidate collection
or routing, invoke a runtime adapter, silently continue as ordinary Chat
without sources, or select another plugin.

### Zero-plugin invariant

When zero acquisition plugins are installed, a future implementation must prove
all of the following:

- ordinary HAC startup is unchanged;
- the ordinary HAC server process does not discover, import, configure, or
  invoke a plugin;
- ordinary Chat is unchanged;
- RFC-0077 source-grounded Chat remains usable when sources enter through its
  existing accepted boundary;
- routing, adapters, and history are unchanged;
- no external-information acquisition occurs; and
- no plugin module is imported merely because HAC starts.

The same ordinary-server rule applies when plugins are installed but no
`hac external-information` operation selects one. Availability for selection is
not permission for use.

## Rationale

Python entry-point metadata is the smallest credible packaging seam: it is
standard-library discovery of separately installed distributions and does not
require a core provider dependency or repository scanning. Restricting it to
one exact group prevents the metadata mechanism from becoming an implicit
general extension architecture.

Running acquisition in a distinct one-shot client process makes its location
and network authority visible. It prevents the ordinary server from gaining an
installed-plugin startup or request-handling responsibility, and it reuses the
already accepted source-grounded endpoint rather than creating a second server
surface. Exact caller selection preserves the project rule that the user
defines the network boundary. It is intentionally less convenient than provider
ranking or fallback, but makes every provider/service choice visible and
prevents a failed operation from changing its disclosure destination.
Revalidation preserves RFC-0077 as the single authority for evidence bounds and
keeps acquisition out of routing and adapters.

The 4,096-byte query and eager-list return are deliberately modest bounds that
the caller edge can enforce without interpreting provider data. Provider
network behavior cannot be safely bounded by a generic in-process timeout
mechanism, so that responsibility remains honestly with the trusted selected
plugin.

## Alternatives considered

### Generic plugin registry or `PluginManager`

Rejected. It would define provider lifecycle, registry, configuration, health,
and future extension rules before evidence exists that a second plugin category
needs them.

### Generic `SourceProvider` abstraction

Rejected. This first boundary has one input and one closed output. A provider
abstraction would expose provider concepts through core and invite selection,
ranking, health, and fallback policy.

### Filesystem scanning or explicit module imports

Rejected. They make a checkout or arbitrary import path part of HAC's durable
configuration and code-loading authority. Separately installed distribution
metadata is narrower and more inspectable.

### Synchronous callable

Rejected. HAC's request orchestration and transport are already asynchronous.
A synchronous plugin would need executor ownership or block the existing async
path; neither improves this one-call contract.

### Core-owned provider HTTP timeout

Rejected. No small in-process core mechanism can reliably interrupt arbitrary
trusted Python. A generic timeout runner would add misleading machinery while
still leaving provider-specific transport ownership unresolved.

### Provider selection, fallback, or retries

Rejected. They would make an installed distribution an automatic disclosure
destination and would require preference, failure, cost, and trust policy.

## Trade-offs

This decision adds entry-point metadata and one explicit caller command where a
hard-coded provider import would be smaller for one service. Those costs are
justified only because they keep provider code and dependencies out of the
ordinary HAC server while preserving a truthful zero-plugin state.

The small contract intentionally excludes streaming, rich provider output,
automatic recovery, and a core deadline. Operators and plugin authors retain
provider-specific responsibility for finite network behavior and credentials.
If that is insufficient for another category, it is evidence for a separate
RFC, not a reason to generalize this one.

## Impact and implementation boundary

If accepted, a later implementation may add only the `hac external-information`
one-shot caller edge needed to perform the stated discovery, selection, lazy
load, compatibility check, single async call, safe failure normalization,
fresh RFC-0077 reconstruction/validation, and existing
`POST /v1/chat/sources` call. It may use `importlib.metadata.entry_points()`
and no new core dependency is required for discovery.

It must not change ordinary Chat, RFC-0077 supplied-source input, capabilities,
routing, candidate selection, fallback, runtime adapters, topology, remote
transport semantics, default history, or URL authority. It must not add an
acquisition FastAPI route, plugin activity in ordinary server startup/request
handling, a provider client in HAC server core, provider selection, plugin
configuration or secrets framework, generic plugin machinery, external network
behavior at server startup, or production provider implementation in HAC core.

## Proof expectations

A future implementation must provide focused proof that:

1. zero installed plugins preserve all ordinary behavior;
2. discovery reads metadata without importing an unselected plugin;
3. exactly one selected compatible plugin is loaded by one explicit
   `hac external-information` operation, while the ordinary server imports none;
4. missing, duplicate, incompatible, import-failing, configuration-failing,
   runtime-failing, and invalid-output cases fail before routing;
5. successful built-in three-field output is reconstructed and revalidated
   against RFC-0077 before the caller sends `POST /v1/chat/sources`;
6. invalid or oversized evidence cannot reach routing;
7. plugin configuration and credentials do not enter cluster request, result,
   routing, or history domains;
8. a selected plugin cannot change node, runtime, or capability selection
   through the acquisition contract;
9. source URLs remain provenance only and do not grant HAC arbitrary fetch
   authority; and
10. no provider fallback or automatic selection occurs.

Proof material must omit private questions, queries, source content and URLs,
generated content, credentials, configuration, provider payloads, endpoints,
private topology, model/runtime identities, and raw logs.

## Open questions

This RFC leaves these implementation-critical choices outside the HAC core
boundary:

- Before a concrete provider plugin is proposed, that distribution must state
  its own explicit configuration and credential mechanism, provider/service
  disclosure boundary, finite transport limits, and provider-specific safe
  failure handling.
- The new one-shot command must reuse the existing native-client endpoint,
  timeout, exit-status, and result-presentation conventions. If those existing
  conventions cannot express the command's explicit inputs and safe result
  handling, that difference needs review before implementation rather than a
  hidden server behavior.

Provider selection is intentionally outside RFC-0078 and is not an open
question for this boundary. These provider-specific prerequisites remain for a
later concrete provider-plugin decision.

## Decision

Accepted.

HAC accepts exactly one optional, explicitly selected, separately installed
external-information acquisition-plugin boundary at the one-shot
`hac external-information` caller edge. The caller edge performs one explicit
plugin acquisition invocation, constructs and validates fresh RFC-0077 evidence
and source-grounded request values, then calls the existing
`POST /v1/chat/sources` boundary before ordinary `capability=chat` routing.

The zero-plugin invariant remains mandatory: ordinary HAC startup, ordinary
Chat, RFC-0077 supplied-source Chat, routing, adapters, and history are
unchanged; the ordinary server does not discover, import, configure, invoke, or
gain network authority through acquisition plugins. One operation selects one
exact plugin name and invokes it once. The versioned
`home_ai_cluster.external_information_acquisition.v1` entry-point group remains
the sole compatibility mechanism. A plugin returns only the closed built-in
`title`/`url`/`content` candidate dictionaries; the caller constructs fresh
RFC-0077 values and completes validation before the source-grounded POST.

Provider configuration, credentials, and finite provider-specific network
behavior remain plugin/operator-owned. This decision retains no provider
selection, no automatic selection or fallback, no new HAC capability, no
generic plugin framework, and no ordinary-server plugin discovery, import, or
network authority. Acceptance adds no production implementation and does not
resolve the provider-specific prerequisites recorded above.
