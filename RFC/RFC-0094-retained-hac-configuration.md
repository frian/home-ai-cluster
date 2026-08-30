# RFC-0094: Retained HAC Configuration

Status: Draft

Date: 2026-08-30

Author: frian

## Summary

Home AI Cluster should add one ordinary retained-configuration surface beneath
the existing `hac` / `home-ai-cluster` facade:

```text
hac config local
hac config node
hac config show
```

It retains two already accepted, distinct operator-owned domains: this
machine's local runtime composition and the caller-side static remote topology.
Retained state is a local HAC-managed baseline for ordinary later invocations;
explicitly supplied compatible CLI values are temporary overrides. It neither
creates a general configuration framework nor changes runtime, routing, remote
ownership, or network authority.

`hac config show` reports retained state only. It is local and read-only, and
does not observe a runtime or cluster.

## Context

RFC-0042, RFC-0071, RFC-0073, and RFC-0074 establish the closed local runtime
composition facts for `ollama` and `llama-server`. RFC-0039, RFC-0040,
RFC-0058, and RFC-0059 establish caller-owned, static remote topology and
capability declarations. RFC-0050 establishes `hac` as the ordinary operator
facade.

Those decisions make the ordinary product usable, but repeated operation still
requires reconstructing stable choices at launch. The 0.8 direction identifies
this as a candidate product problem; that non-binding direction does not itself
authorize a configuration design.

## Problem

An operator who has already selected a local runtime composition and static
remote topology should be able to retain those choices, inspect them, and use
HAC again without repeating every value. Existing explicitly selected
`--runtime-config PATH` and `--declaration PATH` files do not supply that
ordinary HAC-managed experience: each remains an explicit, self-contained
source selected for one invocation.

Without a bounded retained baseline, ordinary repeated use remains fragile and
pushes durable private LAN/runtime facts into shell history or ad hoc wrappers.

## Goals

- Provide one ordinary `hac config` concept for retained HAC state.
- Retain only accepted local runtime-composition and caller-side static-topology
  facts.
- Make retained state a local baseline, optional for ordinary operation.
- Define explicit CLI values as temporary, suppliedness-aware overrides.
- Keep inspection distinct from preflight, health, and status.
- Preserve the closed existing runtime, topology, capability, validation, and
  ownership boundaries.

## Non-goals

This RFC does not add a general configuration framework, profiles, includes,
inheritance, import/export, named environments, arbitrary sections, providers,
plugins, environment-variable precedence, remote synchronization, database,
dashboard, Docker, or Kubernetes.

It does not add credentials, generic secret storage, external-information
authority or retained plugin preference, Chat fallback, research loops,
runtime/node/capability discovery, model inventory, health observation during
resolution, installation, lifecycle management, dynamic topology, capacity,
`can_accept_work`, scheduling, load balancing, weights/priorities, or
vLLM-specific architecture.

## Decision / Proposal

### One ordinary retained-configuration surface

The root facade gains exactly these semantic surfaces:

- `hac config local` owns mutation of retained local runtime composition for
  this machine.
- `hac config node` owns mutation of caller-side retained static remote-node
  declarations.
- `hac config show` owns local, read-only inspection of the retained state HAC
  would normally use for later ordinary invocations.

Equivalent long-form `home-ai-cluster config ...` behavior follows the
accepted facade relationship. This RFC does not add other general configuration
commands.

Retained configuration is HAC-managed. An implementation may use a local
persisted representation, but a manually edited general HAC config file is not
the ordinary product interface. The exact local storage path and byte format
remain implementation details: the architecture requires durable, local,
operator-correctable state, not a file-format contract.

### Ownership boundaries

The two retained domains remain deliberately separate:

```text
config local
  -> local runtime composition for this executing machine

config node
  -> caller-owned declarations of remote topology and eligibility
```

`config local` must not configure a remote runtime. `config node` must not be
treated as local runtime configuration plus an IP address. A remote machine
continues to configure its own runtime locally; its caller declares only static
facts needed for capability-centered routing.

Capability-centered routing, local-first selection, accepted remote declaration
order, request/result contracts, status/health ownership, and external runtime
lifecycle ownership remain unchanged.

### Retained local runtime domain

`hac config local` may retain only the existing closed local runtime-composition
facts. Initially these are:

- for Ollama: selected runtime, an explicitly configured model when present,
  and the accepted thinking-disable choice;
- for llama-server: selected runtime, the accepted loopback HTTP base URL, and
  model identifier.

It adds no runtime discovery, model inventory, hardware/capacity facts,
installation, supervision, arbitrary runtime options, or generic provider
configuration. The same existing runtime-specific validation remains
authoritative.

### Retained static topology domain

`hac config node` may retain one or more caller-owned static remote-node
declarations. Each contains only already accepted topology facts:

- node ID;
- explicit HTTP base URL/address under existing URL rules; and
- explicitly allowed capabilities.

It must not contain remote runtime or model facts, hardware, slots/capacity,
runtime health, discovered capabilities, credentials, or scheduling
weights/priorities. Declaration order remains the only remote ordering semantic.

### Inspection semantics

`hac config show` displays the retained configuration HAC would normally use;
it does not compute current runtime or cluster truth. It is local and read-only:

```text
hac config show  -> what is retained
hac preflight    -> whether static declaration/configuration is locally coherent
hac health       -> runtime observation
hac status       -> cluster observation
```

It must not contact a local runtime or remote node, perform probes or health
checks, discover capabilities, resolve runtime/model truth, or mutate retained
state.

### Effective invocation and override semantics

When applicable retained state exists, ordinary invocations may consume it as a
baseline. Its absence preserves current compatible ordinary behavior, including
zero-argument Ollama composition; retained configuration is never mandatory.

Only values explicitly supplied by the operator on that invocation override
compatible retained values, and only for that invocation. Parser defaults are
not explicit overrides. An override does not mutate retained state or silently
rewrite persistence. Suppliedness is therefore a semantic contract, even if its
implementation is local argument-parsing detail.

Within one retained runtime domain, an explicitly supplied compatible field may
replace the retained field temporarily. For example, retained Ollama
`model-A` plus `hac local --ollama-model model-B` has effective model `model-B`
for that invocation; retained state remains `model-A`.

### Runtime-domain replacement

An explicit selection of a runtime different from the retained runtime replaces
the effective runtime-composition domain. It must not merge incompatible
runtime-specific fields across runtimes. Thus retained Ollama model and
thinking-disable values do not carry to an invocation explicitly selecting
`llama-server`; existing llama-server validation, including required facts,
remains authoritative. Missing values are not invented.

### Topology-domain replacement

An explicitly selected existing complete topology source replaces retained
topology for that invocation. This applies to `--declaration PATH` and the
existing complete bounded inline static-topology form. Retained node collections
must not merge with an explicit declaration, and individual remote facts or
capability patches must not merge across topology modes. Existing
declaration-versus-inline mutual exclusion remains authoritative.

### RFC-0074 interaction

`--runtime-config PATH` remains RFC-0074's explicitly selected,
self-contained runtime-composition source. Selecting it temporarily bypasses
the retained local-runtime baseline for that invocation. It does not merge with
retained local runtime state or equivalent explicit runtime CLI values, and
RFC-0074's supplied-argument mutual exclusion remains intact.

This is intentionally not a general source ladder such as defaults < retained
< file < environment < CLI. The bounded normal path is retained local baseline
plus explicitly supplied compatible runtime CLI values; `--runtime-config` is
the separate explicit alternative.

### Validation and failure behavior

Malformed or semantically invalid retained state must fail locally and visibly
before affected ordinary startup. HAC must not silently fall back to a different
runtime or topology, probe the network to repair state, rewrite it, discard it,
or infer missing values. Existing runtime and topology validation remains the
source of truth for effective values.

Resolution and validation of retained state must not perform runtime/model/node
discovery, DNS/network observation, health checks, or lifecycle actions.

## Compatibility

Unless retained state is deliberately present and applicable, this RFC preserves
current ordinary behavior: no-retained-configuration operation, zero-argument
Ollama, explicit local runtime CLI forms, `--runtime-config PATH`, explicit
static declaration, complete inline static topology, runtime-specific
validation, declaration/inline mutual exclusion, capability vocabulary and
eligibility, and no network activity during configuration resolution.

The root `hac` command with no subcommand remains help/discovery behavior, never
an implicit process launcher.

## Privacy and security

Retained configuration remains on the operator's local machine: it has no
telemetry or external synchronization. It may contain local model identifiers
and private/LAN base URLs, but never prompts, responses, request history,
acquired external-information content, or credentials under this RFC.

Normal errors and logs must not unnecessarily reveal retained topology or
runtime facts. `hac config show` is an explicitly requested operator inspection
and may display facts necessary to understand retained configuration. This does
not authorize broader logging of those values.

## Rationale

This is the smallest durable shape that removes repeated ordinary operator
friction while preserving established domain ownership. A HAC-managed retained
baseline makes ordinary use natural; explicit temporary CLI values preserve
one-off control without hidden persistent mutation. Domain replacement avoids
an unsafe generic merge policy, and keeping RFC-0074 self-contained preserves
its intentionally simple contract.

## Alternatives considered

### Continue explicit paths and CLI values only

Rejected. They remain supported, but do not provide the desired ordinary
configure-once, inspect, and later-use product behavior.

### One general editable HAC configuration file

Rejected. It would promote storage mechanics into the product interface and
collapse separate local-runtime and caller-topology ownership domains.

### A universal precedence hierarchy

Rejected. It introduces a configuration framework and difficult mixed-source
semantics beyond this bounded need.

### Merge retained topology with explicit topology input

Rejected. Complete topology replacement is clearer than merging collections,
capabilities, and source-specific facts.

### Observe runtimes or nodes in `config show`

Rejected. Retained-state inspection must not be confused with health or status.

## Trade-offs / consequences

The proposal adds durable local state, a new local failure surface, and a
suppliedness requirement for relevant CLI parsing. It deliberately leaves some
one-off operations explicit and rejects broad flexibility. Those costs are
acceptable because they produce a clear ordinary operator experience without
new network authority, dynamic behavior, or a general configuration system.

## Implementation boundary

No implementation is authorized by this Draft RFC. If accepted, work may add a
small HAC-managed local persistence boundary, the three specified facade
surfaces, suppliedness preservation for relevant runtime/topology inputs,
effective-domain construction, focused tests, and operator documentation.

It must not add persistence for requests/results, a generic configuration
framework, changed routing/request/status contracts, network probing during
resolution, external-information behavior, credentials, discovery, lifecycle,
or scheduling.

## Proof expectations

Later implementation must prove that:

1. absent retained state preserves current compatible behavior, including
   zero-argument Ollama;
2. retained local composition and retained static topology are separately owned
   and consumed as a baseline when applicable;
3. only explicitly supplied compatible CLI values override retained values, and
   never mutate them;
4. explicit runtime switching replaces the runtime domain rather than carrying
   incompatible fields across;
5. explicit declaration and complete inline topology replace retained topology
   rather than merge it;
6. `--runtime-config` bypasses retained local runtime state and retains its
   RFC-0074 mutual exclusion;
7. invalid retained state fails locally without fallback, rewrite, or network
   activity; and
8. `config show` is read-only retained-state inspection with no runtime/node
   observation.

Proof must also show unchanged capability/routing contracts and no unnecessary
exposure of private retained facts.

## Open questions

- What exact user-facing mutation/removal spelling makes retained nodes and
  local state operator-correctable? This RFC requires correctability/removal
  as a semantic property but does not invent durable syntax absent an accepted
  naming decision. It must be resolved before implementation.
- Does implementation need a canonical platform-standard storage location and
  a concrete format, or can those safely remain internal? If a public contract
  is necessary, it requires explicit review of its location, migration, and
  privacy implications before implementation.

## Decision

Draft. RFC-0094 proposes one HAC-managed retained configuration surface with
`config local`, `config node`, and `config show`; separate retained local runtime
and caller-side static topology domains; retained state as an optional baseline;
explicit compatible CLI values as temporary overrides; runtime/topology domain
replacement; and RFC-0074 as a self-contained alternative local runtime source.

It authorizes no implementation unless accepted and the listed necessary open
questions are resolved.
