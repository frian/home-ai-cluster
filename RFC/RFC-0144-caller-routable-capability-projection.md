# RFC-0144: Caller Routable Capability Projection

Status: Accepted

Date: 2026-09-26

Author: frian

## Summary

Home AI Cluster should define one bounded capability-only projection answering:

> Which accepted capabilities are present on this currently running caller's
> ordinary routing surface before additional request-specific constraints?

The projection is derived from the caller's already composed in-memory routing and execution eligibility. It does not reconstruct routing from retained configuration, execute or simulate requests, probe runtimes or remote nodes, inspect health, or introduce a second routing policy.

The first consumer is the ordinary/native loopback browser. It may use this projection to avoid presenting a capability operation as currently usable when the serving caller has no routing-eligible local or declared-remote candidate for that capability.

The projection exposes capability names only. It does not expose nodes, topology, bindings, adapters, runtimes, models, addresses, health, routing priority, or selection explanations.

## Context

HAC is capability-centered. Accepted capability names describe bounded semantic requirements, while existing routing architecture determines which local or declared-remote candidates are eligible for a request requiring one of those capabilities.

Several distinct truths already exist and must remain distinct:

    adapter execution support
        !=
    local binding ownership
        !=
    caller-local routing permission
        !=
    declared-remote capability eligibility
        !=
    caller ordinary routing surface
        !=
    guaranteed eligibility for every constrained request
        !=
    runtime or remote health

RFC-0108 defines local binding capabilities as process-local execution ownership. The local execution-capable set is the union of valid local binding capability sets. `RuntimeAdapter.capabilities()` remains adapter execution truth and must not independently grant routing ownership when explicit bindings exist.

RFC-0059 separately defines caller-local static capabilities as caller-side routing permission. A static-cluster caller may therefore expose only a subset of the capabilities owned by its local execution composition without changing that execution composition.

Declared remote nodes remain caller-owned capability-only static routing declarations. Their capability claims are not runtime discovery, health observation, model inspection, or remote verification.

Existing routing already combines these truths for an actual request. Local routing requires a locally eligible node and matching execution ownership. Declared-remote routing considers remote declarations eligible by requested capability. Existing candidate composition and selection then apply the accepted routing rules.

The loopback browser currently has fixed capability views. Historically this was deliberate: RFC-0062 made the browser a small same-origin client of existing native capability routes rather than a routing or operator-inspection layer. Later capability and composition work expanded HAC beyond that original fixed proof, but no accepted architecture currently lets the browser ask which capabilities the serving caller can route.

The retained Configuration browser facade is not that authority. RFC-0132 explicitly represents retained future/operator state rather than the composition of the currently serving process. Retained state may differ from the active process and must not be reinterpreted by the browser as current routing truth.

## Problem

The browser can present an operation for a capability even when the current caller has no eligible routing path for that capability.

Attempting the operation remains safe because existing routing and failure behavior are authoritative, but the browser has no capability-centered way to represent the caller's current routing surface before a request is made.

The browser must not solve this by independently interpreting:

- retained local configuration;
- retained local capability settings;
- retained remote-node declarations;
- runtime configuration;
- adapter capability methods;
- local bindings;
- current browser configuration forms; or
- combinations of those facts.

Doing so would create a second routing interpretation outside the routing architecture and could diverge from the caller composition actually serving requests.

The browser also must not probe runtimes or remote nodes merely to decide whether to present an operation. Routability and current execution success are different facts.

## Goals

This RFC should:

- define one capability-only projection of the currently running caller's routing eligibility;
- derive that projection from the already composed caller routing and execution truths;
- preserve existing local binding, caller-local permission, declared-remote eligibility, routing-order, and failure semantics;
- perform no request execution, runtime call, remote transport, health check, discovery, or retained-state reconstruction;
- let the ordinary/native loopback browser consume the projection without owning routing logic; and
- remain engine-independent and capability-centered.

## Non-goals

This RFC does not define or authorize:

- a status API;
- health or readiness reporting;
- runtime, model, adapter, or binding inspection;
- topology inspection;
- node listing or node selection;
- remote-node probing or capability verification;
- runtime or model discovery;
- retained-configuration introspection as current process truth;
- routing explanations;
- routing priority exposure;
- scheduling, scoring, preference, load balancing, or routing-policy changes;
- capability negotiation;
- dynamic capability discovery;
- automatic refresh, polling, monitoring, or background work;
- a dashboard or control plane;
- receiver administration;
- trusted-LAN browser authority; or
- a generic introspection framework.

It also does not change capability admission, request contracts, result contracts, local execution ownership, caller-local permission, remote declaration semantics, fallback, failure behavior, or the closed accepted capability vocabulary.

## Decision

### One caller-routability projection

HAC may project the set of accepted capabilities for which the currently
running caller has at least one routing-eligible candidate in its already
composed ordinary routing surface, before additional request-specific
constraints narrow candidate eligibility.

Conceptually:

    caller routable capabilities
        =
    capabilities with an eligible local candidate
        UNION
    capabilities with an eligible declared-remote candidate

This is a projection of existing eligibility, not a new source of eligibility.

The projection does not choose a candidate and has no effect on subsequent routing. An actual request continues through the existing routing and orchestration path, which remains authoritative.

### Local eligibility

A capability is locally represented only when the active caller composition has
an existing local routing candidate for that capability. The projection must
preserve the current local candidate-eligibility relationships:

    active routing NodeRegistry eligibility
    AND
    the applicable existing local adapter-selection path

NodeRegistry eligibility includes the local node's declared capability and its
existing static `availability == "available"` condition. Static availability is
therefore existing routing truth. It is not a live health or readiness
observation, and this projection must not probe to create one.

Where explicit local capability bindings are composed, the applicable path is:

    eligible routing node
    AND
    bound adapter for the capability

Adapter execution support alone remains insufficient. A capability that an
adapter could execute but that no binding owns must not become locally present
through this projection.

Where explicit bindings are not composed, the existing legacy/unbound path
remains authoritative:

    eligible routing node
    AND
    existing node/adapter matching semantics

This preserves current compatibility; it does not define new adapter-selection
behavior or promote the legacy path into a future architecture.

Process-local execution ownership and RFC-0059 caller-local routing permission
remain relevant existing truths. In particular, a locally execution-owned
capability excluded by caller-local routing permission must not be projected
from the local candidate. They are not, by themselves, a replacement for the
existing local routing candidate eligibility represented by the active caller
composition.

The projection must therefore use the already composed caller-side routing
state rather than re-reading configuration inputs that may have produced it.

### Declared-remote eligibility

A capability is remotely present on the ordinary routing surface when at least
one remote declaration in the caller's active routing composition declares that
capability eligible under the existing static remote semantics.

Remote declaration order remains authoritative for actual routing and fallback
but has no meaning in this set projection.

The projection does not contact a declared remote node. It does not verify that
the remote process is running, healthy, reachable, or still capable of
fulfilling the declaration.

A request-specific constraint such as `local_only` may exclude an otherwise
eligible declared-remote candidate for that particular request. This does not
make the projection false: it represents the ordinary routing surface and does
not pre-evaluate every possible request constraint. Actual request-time routing
remains authoritative.

### Routability is not execution availability

Projected membership means only:

> The current caller has an existing ordinary routing-surface path for this
> capability.

The relevant truths remain distinct:

    caller ordinary routing surface
        !=
    guaranteed eligibility for every constrained request
        !=
    execution success

It does not mean:

> A request using this capability would currently succeed.

For example, a capability declared by an eligible remote node remains on the
ordinary routing surface even if that remote process is currently unavailable.
The existing request path determines the resulting transport or execution
failure if a request is later attempted.

Existing static `availability` remains a routing input. This projection does
not convert it, or static `health` fields used inside existing node
representations, into live observations.

No network activity or runtime activity is permitted when constructing the projection.

### No synthetic requests

The projection must not be implemented by constructing synthetic capability requests and submitting them through request routing or orchestration.

Different accepted capabilities may own different request contracts, validation, constraints, or execution behavior. Caller routability is a property of the already composed eligibility state and should not depend on inventing otherwise meaningless request payloads merely to ask whether a capability has a candidate.

Implementation should instead project capability membership directly from the
same authoritative active-composition relationships used by routing, rather
than implementing a simplified parallel approximation.

This projection logic must remain small and must not become a parallel general-purpose router.

### Capability vocabulary

The projection contains only accepted project-owned capability names.

It does not create capability names, infer capabilities from runtime or model properties, expose arbitrary adapter capability strings as public routing facts, or create an extensible capability registry.

Capability admission remains governed by the existing accepted architecture.

### Browser consumption

The ordinary/native loopback browser may consume this projection to determine whether a capability operation should be presented as currently usable by the serving caller.

The browser must not independently reconstruct, supplement, or override the returned set.

In particular, browser JavaScript must not derive routability from retained Configuration responses or from knowledge of runtimes, bindings, nodes, adapters, models, or remote declarations.

The projection does not authorize the browser to select a node or influence routing. Submission of an enabled operation remains an ordinary capability request through the existing native path.

Exact UI presentation is an implementation detail. Hiding, disabling, or otherwise clearly marking an unavailable capability operation is permitted provided the browser does not imply health or guaranteed success.

### Projection shape

The browser-facing representation is capability-only.

Conceptually:

    {
      "capabilities": [
        "chat",
        "summarize",
        "code"
      ]
    }

Exact route spelling, JSON field spelling, ordering, and browser presentation remain implementation details unless they acquire semantic significance.

The representation must not expose:

    node_id
    local-versus-remote provenance
    remote declaration count
    remote declaration order
    adapter
    adapter instance
    binding
    runtime
    model
    endpoint or base URL
    health
    readiness
    routing reason
    routing priority
    execution limit

A later need for any such fact requires separate architectural evaluation.

### Application and authority boundary

The first browser-facing projection belongs only to the ordinary/native loopback browser application.

It does not become a receiver endpoint, trusted-LAN browser endpoint, compatibility endpoint, remote inspection protocol, or general public status surface.

It follows the existing loopback-browser application-composition boundary rather than widening browser authority.

The projection is read-only and has no persistent effect.

### Relationship to retained Configuration

This projection and retained Configuration answer different questions:

    retained Configuration
        -> what future HAC invocations are configured to use

    caller routability projection
        -> what this currently running caller can route

The caller-routability projection must not load retained configuration in order to reconstruct the current process.

A retained configuration mutation remains future-invocation-only unless another accepted decision says otherwise. It therefore need not change the routability projection of the currently serving process.

Conversely, the active caller may have been constructed from explicit invocation or declaration inputs that differ from retained state. The active composed caller remains authoritative for this projection.

## Failure semantics

If the serving application cannot truthfully construct its caller-routability projection from its active composition, the projection must fail closed rather than guess from retained state, adapter support, defaults, or browser assumptions.

Failure of the projection does not change capability request semantics. Existing native capability routes remain authoritative and may still be called directly.

The browser must not interpret projection failure as proof that every capability is routable.

No new public execution-failure taxonomy is introduced.

## Privacy and security

The projection contains only accepted capability names already used as cluster-facing semantic routing facts.

It exposes no prompt, response, source text, file content, credentials, runtime configuration, model identity, adapter identity, node address, remote address, retained configuration, private topology, health observation, or execution history.

Constructing it performs no network access, runtime call, plugin access, filesystem discovery, model inspection, or remote probe.

The projection therefore adds no authority to send user content outside the existing request path.

## Compatibility

Existing CLI, native HTTP, receiver, compatibility, retained Configuration, routing, fallback, execution, and failure behavior remain unchanged.

Applications that do not include the loopback browser surface gain no browser projection endpoint from this RFC.

Existing capability requests remain valid regardless of whether a browser has consumed the projection.

The projection is advisory only to browser presentation. Existing request-time routing remains authoritative.

## Implementation constraints

The first implementation should remain deliberately small.

It should:

1. add one core/read-only capability projection over the active caller composition;
2. expose that projection only through the ordinary/native loopback browser boundary;
3. update the fixed browser presentation to consume it;
4. add focused tests proving local, restricted-local, remote-only, mixed, and absent-capability cases; and
5. preserve all existing request routing and failure tests unchanged.

The implementation must not introduce a generic introspection service, new registry architecture, polling, caching, background refresh, runtime probes, remote probes, or retained-state reconstruction.

Special-case browser logic for individual runtimes or models is not acceptable. Image Generation and other accepted capabilities must follow the same capability-centered projection rule when their existing composition makes them routing-eligible.

## Acceptance proof

The implementation proof must establish at least:

1. a capability with an existing locally eligible candidate in the active caller composition is projected;
2. a capability supported by an adapter but absent from the applicable active local candidate-eligibility path is not made locally present by adapter support alone;
3. a locally execution-owned capability excluded by caller-local routing permission is not projected from the local candidate;
4. a capability absent locally but present in an active declared remote is projected;
5. a capability present in neither eligible local composition nor active remote declarations is absent;
6. local and remote eligibility for the same capability produces one capability membership, not topology information;
7. remote projection performs no network request and remains independent of current remote reachability;
8. retained configuration is not read to reconstruct active routability;
9. projection construction performs no runtime execution or synthetic capability request;
10. the browser consumes the projection without making routing decisions;
11. receiver, trusted-LAN, and compatibility application boundaries do not gain the browser projection; and
12. ordinary capability request routing and failure semantics remain unchanged.

## Rationale

The browser needs one small piece of current-process truth to remain capability-centered as HAC composition becomes richer.

Exposing retained configuration would answer the wrong question. Exposing adapters, bindings, nodes, runtimes, models, or health would widen the browser into an operator-inspection surface. Probing capabilities would confuse routability with availability. Reimplementing routing in JavaScript would create a second routing policy.

A capability-only projection is the smallest boundary that lets the browser answer its actual question while preserving routing ownership inside HAC:

    browser asks what is routable
    HAC answers with capability names
    browser presents those operations
    actual requests still let HAC route

This keeps the browser a client of HAC rather than a participant in routing.
