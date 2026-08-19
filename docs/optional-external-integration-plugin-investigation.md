# Optional External Integration Plugin Investigation

Status: Complete

## Question

> What is the smallest credible architecture that lets optional external
> integration code be installed separately from Home AI Cluster (HAC),
> discovered by HAC, and invoked through a narrow stable contract while HAC
> remains fully functional without it?

This is a documentation-only investigation. It does not authorize an RFC,
implementation, plug-in system, provider, dependency, entry point,
configuration, production code, network access, or change to runtime, routing,
request, result, history, or ordinary Chat behavior.

## Outcome

**Outcome B — one narrow external-information acquisition plug-in boundary is
credible enough for a future RFC.**

The credible boundary is not a universal plug-in API. It is one optional,
operator-installed Python distribution category that performs explicit
external-information acquisition before the accepted RFC-0077
source-grounded-Chat contract:

```text
explicit operator external-information request and query
        ↓
one explicitly selected optional acquisition plug-in
        ↓
bounded normalized SourceEvidence[]
        ↓
RFC-0077 source-grounded Chat
        ↓
ordinary capability=chat routing
```

Python package entry points are the recommended future discovery mechanism.
They are standard-library metadata, make separately installed distributions
visible without repository-directory scanning, and allow HAC to defer import
until an explicit request selects one known plug-in name. The recommendation is
for one category-specific entry-point group and one acquisition callable, not a
`PluginManager`, a general plug-in hierarchy, or a `SourceProvider` framework.

This outcome does not authorize implementation. Operator-owned browser,
command, or helper retrieval followed by existing HAC input remains the
supported workflow. RFC-0064 remains Rejected, arbitrary public-URL retrieval
remains blocked, and RFC-0077 remains the accepted provider-neutral
source-grounded execution boundary whose acquisition decision is still outside
that RFC.

## Scope and governing boundaries

This investigation considers only a future caller-edge integration category:
one explicit external-information acquisition whose successful output feeds
RFC-0077. It does not examine runtime adapters, generic extensions, or an
arbitrary code-loading framework.

RFC-0077 is governing for the downstream boundary:

- execution remains `capability=chat`;
- the operator question and normalized untrusted source evidence remain
  structurally distinct;
- core projection remains system framing, source evidence, then the final
  operator question;
- supplied-source provenance remains separate from generated content and is
  not source truth or claim-level citation correctness; and
- acquisition, credentials, provider state, raw responses, and network
  authority remain outside runtime adapters, routing, and the RFC-0077 source
  representation.

The retained external-information investigations establish that a
project/operator-selected destination is materially different from the
caller-controlled destination rejected by RFC-0064. They also establish that
fixed-provider and independently operated private-SearXNG acquisition have
different privacy, credential, cost, lifecycle, endpoint, and operational
trade-offs. The closed Tavily-specific Draft RFC-0076 / PR #471 is
non-governing historical evidence only; it neither selects Tavily nor defines
this investigation's contract.

This investigation does not authorize:

- Tavily, SearXNG, another provider, provider recommendation, provider SDK, or
  HAC-owned service installation/lifecycle;
- an arbitrary URL, result-URL, page fetch, redirect, crawler, browser, or
  scraping surface;
- a `web`, `search`, `browse`, `retrieve`, or `research` capability;
- automatic, model-directed, model-rewritten, repeated, fallback, or
  background acquisition;
- a generic provider, credential, endpoint, plug-in, or service abstraction;
- plug-in-driven changes to node selection, routing, capability declarations,
  runtime adapter selection, topology, history, persistence, or results; or
- process isolation, sandboxing, containers, IPC, daemon supervision, or a
  plug-in security boundary.

## Current repository facts

Current `main` for this investigation is
`583f88e9225bb6541ce5c9a13c8931aa3fbdc9ba`.

The core package already requires Python `>=3.13,<3.15` and lists HTTPX as a
direct dependency. It has one core distribution built by Hatchling and no
plug-in metadata, plug-in directory, dynamic-import configuration, or entry
point discovery today. Existing HTTP calls belong to fixed native, runtime, and
declared-remote boundaries; they do not create an external-information client.

RFC-0077 intentionally accepts normalized `SourceEvidence` only after
acquisition. Its source representation excludes provider names, scores, ranks,
queries, request IDs, credentials, raw responses, acquisition configuration,
and network authority. Its core, routing, transport, and adapters must not
resolve or fetch source URLs. A future acquisition plug-in must therefore end
before source-grounded routing begins.

## Candidate mechanisms

### 1. Separately installed distributions discovered through Python entry points

**Recommended future mechanism.** A future core implementation could use
`importlib.metadata.entry_points()` from the Python standard library to inspect
one category-specific group, for example a group reserved for RFC-0077
external-information acquisition. Each separately installable distribution
would expose one named acquisition factory/callable in that group.

Entry-point discovery needs no new HAC runtime dependency. It reports package
metadata rather than importing a distribution merely because it is installed.
HAC can therefore keep ordinary startup and ordinary local behavior free of
plug-in imports. Only a future explicit external-information operation may
select one exact entry-point name and load it.

This is smaller than a registry because the Python packaging installer already
owns distribution installation, uninstallation, and metadata visibility. HAC
only needs bounded lookup, one selected load, and one category-specific call.
It must not enumerate an installed plug-in list as an authorization list,
auto-select a provider, or treat metadata discovery as permission to make a
network request.

### 2. Separately packaged projects kept under a repository `plugins/` area

**Compatible source layout, not a discovery mechanism.** A future monorepo
could keep independent source projects such as `plugins/tavily/` and
`plugins/searxng/`, each with its own distribution metadata, dependencies,
tests, release version, and optional installation command. Editable installation
for development and ordinary package installation for users would then expose
the same entry points as an externally hosted package.

This layout does not make source part of the HAC core distribution and must not
cause HAC to scan the checkout. It adds release and compatibility discipline:
each plug-in needs a declared compatible HAC API range, its own dependency
constraints, and a policy for a core/plug-in mismatch. A shared repository can
be convenient, but it does not remove separate-version ownership.

### 3. Explicit module/import configuration

**Not recommended for the first boundary.** An operator could configure one
module path or callable import string. This has superficially little machinery,
but it creates a durable HAC configuration surface for arbitrary import
authority, import-path validation, precedence, error behavior, and local
packaging assumptions. It also makes independently installed distribution
identity and compatibility less visible.

For a private one-off deployment, an explicit import may be smaller than
metadata lookup. For a project-owned optional boundary, standard distribution
metadata is the more boring and inspectable choice. A future RFC should not add
both mechanisms initially.

### 4. Hard-coded optional imports

**Baseline only; rejected.** `try: import tavily` or `try: import searxng`
would be small code for one integration, but it names a provider in core,
couples core releases to provider packages, makes absence and version errors
core behavior, and must grow a new conditional branch for every provider. It
does not serve an independently installable boundary and is less honest than
one narrow metadata contract.

### Repository-directory scanning

**Rejected.** Scanning `plugins/` or an arbitrary local directory conflates a
source checkout with an installed product, creates path and import-precedence
rules, and silently expands code-discovery authority. It provides no packaging
compatibility metadata and adds no value over entry points for separately
installed distributions.

## Smallest credible future contract

The first contract should be limited to one category: explicit acquisition that
returns RFC-0077-compatible source evidence. It should not introduce generic
plug-in lifecycle, discovery, health, configuration, capability, routing, or
extension objects.

Conceptually, one selected plug-in callable receives only:

```text
one explicit operator query
one caller-edge operation context required by the future RFC
```

and returns either:

```text
one ordered bounded SourceEvidence[] value
or one normalized acquisition failure
```

The future RFC must decide the exact callable signature, sync/async ownership,
and error type. It should require the plug-in output to be validated by the
core against RFC-0077 before any source-grounded request enters routing. The
plug-in must not receive a `ClusterRequest`, routing candidate, adapter,
remote-client, or source-grounded result. The core contract must not mention a
provider name, provider request/response shape, credential, endpoint, result
rank, score, or raw response.

The selected plug-in's package owns its own provider adaptation: request
formatting, provider response parsing, transport client use, and conversion to
the closed source fields. It may use in-process trusted operator-installed
Python code. This is not a sandbox guarantee; package installation itself is a
trust decision by the operator.

### Explicit selection and absence

Installation means only **available for explicit selection**. It does not
authorize external network use, change ordinary Chat, add a capability, or
cause discovery/import at startup. A future external-information caller edge
must require an explicit operator action plus an explicit selection of one
installed, configured plug-in. The first RFC need not solve ranking, fallback,
preference, or arbitration when Tavily and SearXNG are both installed.

For the first boundary, selection should be exact and caller-owned: one named
plug-in for one operation. A missing entry point, a duplicate name, an import
failure, an incompatible plug-in, or missing plug-in configuration is an
external-information operation failure before HAC source-grounded routing. It
must not prevent core startup, change ordinary local behavior, leak import or
credential details, silently choose another plug-in, fall back to unassisted
Chat, or retry with another provider.

### Failure, timeout, and privacy containment

The plug-in executes before candidate collection. A failure therefore produces
no `ClusterRequest`, no source-grounded transport envelope, no routing attempt,
and no runtime-adapter call. A future caller edge needs a stable, privacy-safe
acquisition failure separate from ordinary Chat failures; it must not expose
the query, credential, endpoint, provider metadata, raw response, exception,
or private topology.

An in-process trusted callable cannot be safely forcibly stopped by a small
generic core mechanism. The first boundary should not add threads, workers,
process isolation, or a general timeout runner to pretend otherwise. Each
plug-in must use finite transport/connect/read limits appropriate to its one
explicit request; a future RFC may add an end-to-end acquisition deadline only
after identifying an enforceable caller-edge mechanism. Plug-in load and
runtime exceptions must be contained to that explicit operation.

Credentials and provider configuration remain plug-in-owned caller-edge state.
They must not enter `SourceEvidence`, `SourceGroundedChatRequest`,
`ClusterRequest`, routing, remote transport, adapters, source-grounded results,
default history, logs, metrics, traces, or retained proof material. The future
RFC must decide a specific operator configuration/credential boundary without
making a generic HAC secret/configuration system.

### Provider examples without core coupling

A Tavily distribution can plausibly add **zero new HAC-core dependencies**:
HTTPX is already in the core environment, and the distribution can either
declare a compatible HTTPX requirement itself or use the resolved compatible
version. Its API key, request shape, usage/cost handling, response parsing, and
timeouts remain its package's responsibility, not HAC's. This is a packaging
possibility, not a provider recommendation.

A SearXNG distribution can likewise remain outside core. Its plug-in owns only
one explicitly selected request to an operator's independently running service
and conversion of its response to bounded source values. SearXNG installation,
engine selection, JSON enablement, updates, availability, upstream engine
blocks, and service lifecycle remain operator-owned costs. HAC must not install,
configure, start, supervise, or otherwise manage that service.

## Core versus plug-in responsibility

| Concern | Future core boundary | Future selected plug-in boundary |
| --- | --- | --- |
| Availability | Read one entry-point group; recognize one explicitly selected installed name. | Provide distribution metadata and a compatible callable. |
| Authorization | Require explicit caller-edge operation and exact plug-in selection; no automatic use. | Perform no work until invoked. |
| Acquisition | Validate returned `SourceEvidence` before RFC-0077 routing; own safe normalized failure at the HAC edge. | Provider/service request, response parsing, bounded local normalization, and provider-specific finite transport behavior. |
| Configuration and credentials | Never place them in core request/routing/adapter/history/result domains. | Operator-owned package configuration and credential handling, to be specified per future acquisition RFC. |
| Routing and execution | Use RFC-0077 and ordinary `chat` routing unchanged after accepted evidence exists. | No node, runtime, adapter, capability, constraint, topology, or fallback influence. |
| Provenance | Return only RFC-0077 supplied-source provenance. | Do not claim source truth, freshness, rank reliability, or citation correctness. |

## Smallest RFC-worthy decision surface

Outcome B supports one future RFC question:

> Should HAC add one optional, explicitly selected, separately installed
> external-information acquisition plug-in entry point that can make one
> operator-requested acquisition call and return bounded RFC-0077 source
> evidence before ordinary `chat` routing?

That RFC must decide only:

1. the one entry-point group, name rules, core/plug-in compatibility version,
   and lazy-load behavior;
2. the explicit caller-edge action, plugin-name selection, and absence/load/
   incompatibility/runtime-failure presentation;
3. the narrow acquisition callable request/result/error contract and RFC-0077
   revalidation point;
4. one enforceable finite request/response/result/timeout envelope for the
   selected first integration;
5. the operator-owned configuration and credential boundary; and
6. focused proof that zero plug-ins preserve startup and all ordinary HAC
   behavior, while an explicit selected plug-in cannot affect routing, adapters,
   history, or URL authority.

It must not define a generic plug-in interface, registry, manager, lifecycle,
configuration system, provider selection policy, provider fallback, capability,
or security sandbox. A second or third materially different plug-in category
would be evidence required before considering any generalization.

## Trade-offs and unresolved questions

Entry points add distribution metadata and a compatibility policy, while a
hard-coded import avoids those mechanics. The metadata cost is justified only
because it keeps provider-specific code and dependencies out of core and keeps
zero-plug-in behavior honest. Separate packages also make individual provider
failure and release cadence explicit; they do not make a provider's operational
or privacy cost disappear.

The remaining questions are intentionally narrow and must be answered by a
future RFC for one concrete first integration:

- Which first operator problem is worth an explicit external-information
  exception rather than the existing operator-owned retrieval workflow?
- Which exact plug-in name, core/plug-in version policy, and caller-edge
  selection syntax are small enough to support?
- Which provider/service-specific request, response, timeout, and result bounds
  are enforceable without adding generic machinery?
- Where does that plug-in's operator-owned configuration and credential live,
  and how is explicit consent to disclose its query made visible?
- Does the first implementation need only one selected plug-in, with any
  multi-installed selection left entirely explicit and manual?

## Decision

**Outcome B — investigate one narrow entry-point-discovered,
external-information acquisition plug-in in a future RFC; do not implement it
now.**

Python package entry points are the smallest credible mechanism because they
use standard-library metadata and preserve separately installable provider code
without checkout scanning or core provider imports. The boundary remains
credible only when it is confined to explicit caller-edge acquisition feeding
RFC-0077, with provider-specific authority and credentials outside core and
ordinary HAC fully functional with zero plug-ins.

No provider is selected. No generic plug-in framework is justified. Ordinary
operator-owned retrieval remains the supported current workflow.
