# RFC-0152: Native Active Routable Capability Projection

Status: Accepted

Date: 2026-10-08

Author: frian

## Summary

Home AI Cluster should expose RFC-0144's existing capability-only projection
through one explicit, read-only native loopback operation on the already-running
ordinary HAC process.

The operation answers only:

> Which accepted semantic capabilities does this running originating HAC
> process currently have on its ordinary routing surface before
> request-specific constraints?

It returns stable accepted capability names and nothing else. It is derived
from the active process's existing routing eligibility seam; it neither
reconstructs configuration nor probes, executes, selects, reserves, or
predicts. This proposal adds a native carrier for existing truth, not a new
capability-discovery, health, readiness, or routing architecture.

## Problem

An independent native thin client can use the ordinary native Chat contract,
but it has no accepted native contract for learning the active caller's
capability surface. It must not approximate that answer by reading retained
Configuration, inspecting node or binding declarations, calling adapters or
runtimes, inspecting health/status, or inferring facts from previous results.
Those sources either answer a different question or would create a second
orchestrator outside HAC.

The existing browser-only carrier at `GET /caller-routable-capabilities` is
not a native client contract. RFC-0144 deliberately confined that first public
carrier to the native loopback browser application. An independent native
client needs the same HAC-owned semantic truth through the ordinary native
loopback authority, without widening the browser route or treating browser
facades as generic APIs.

## Goals

This proposal should:

- expose one finite, read-only, capability-only native projection from the
  running ordinary process;
- reuse RFC-0144's active-composition eligibility semantics and its existing
  authoritative core projection seam;
- keep HAC, rather than a native client, responsible for routability;
- provide a useful successful empty set when the active composition has no
  ordinary routing-surface capability;
- expose no request content, topology, runtime, model, health, availability,
  execution, or configuration detail; and
- preserve local-first, privacy-first, capability-centered, and
  engine-independent boundaries.

## Non-goals

This RFC does not define or authorize capability discovery, a registry service,
runtime/model inventory, health/readiness/status reporting, remote probing,
remote capability verification, execution-permission inspection, concurrency
inspection, selection controls, routing explanation, fallback simulation,
request execution, configuration inspection or mutation, polling, caching,
subscriptions, events, monitoring, lifecycle control, a generic
introspection/client framework, an OpenAI-compatible capability listing,
trusted-LAN or receiver access, or any Desktop implementation or presentation
behavior.

## Existing architecture and authoritative seams

RFC-0144 defines *caller routable capabilities*: accepted capabilities for
which the currently running caller has at least one existing ordinary
routing-eligible local or declared-remote candidate, before additional
request-specific constraints. Its implementation's
`project_caller_routable_capabilities` iterates the accepted vocabulary and
uses `local_routing_decision_for_capability` plus
`declared_remote_declarations_for_capability`. It therefore reuses the same
active composition and local eligibility relationships that ordinary routing
uses instead of implementing a parallel approximation.

The serving process owns the relevant active in-memory composition. RFC-0147
establishes the same carrier-authority pattern for active static routing
explanation: the ordinary loopback process exposes a bounded projection of its
own composition, while core routing seams retain routing ownership. Its native
diagnostic routes are explicitly named under `/diagnostics/`; this proposal
follows that native convention rather than using `/v1/capabilities`, which
could misleadingly imply an OpenAI-compatible inventory API.

RFC-0144's browser carrier is a browser-specific projection over reusable,
authoritative core semantics. It is neither a new source of truth nor itself
the native contract proposed here. RFC-0146 through RFC-0150 expose richer
active-routing and actual-request explanations, but those surfaces answer
constraint-specific or execution-specific questions and must not be used to
reconstruct this set.

## Proposed semantics

### Configured, declared, routable, and executable now

These are distinct facts:

| Term | Meaning in this RFC |
| --- | --- |
| Configured | Retained operator intent for future HAC invocations. It is not active-process truth. |
| Declared | A capability recorded on a node, binding, adapter, or active remote declaration. A declaration alone is not enough. |
| Routable | The active process has at least one existing ordinary local or declared-remote routing-eligible path for an accepted capability, before request-specific constraints. |
| Executable now | A separate request-time question. This projection makes no claim that a later request will obtain permission, reach a remote, invoke a runtime, or succeed. |

For each accepted capability, inclusion is exactly the RFC-0144 union:

```text
existing locally eligible candidate
OR
existing statically eligible declared-remote candidate
```

Local inclusion preserves existing active `NodeRegistry` availability and
capability matching, explicit local binding ownership where composed, and
caller-local routing permission. Adapter support by itself does not include a
capability. A declared remote includes a capability when the active caller's
declaration is eligible under existing static remote semantics. A remote-only
capability is therefore included.

Declared-remote order and local-first precedence remain authoritative for a
later ordinary request, but do not affect set membership: local and remote
paths for the same capability produce one name, and remote-only eligibility
also produces that name. The operation selects neither candidate.

`local_only` and other future request-specific constraints are not inputs to
this operation. A capability may be listed while a later constrained request
cannot use an otherwise eligible remote. RFC-0144's ordinary routing-surface
meaning remains the complete definition of the set.

### Health, reachability, permission, and races

Construction performs no runtime, remote, health, status, availability, or
model probe. Static node availability already used by existing routing remains
an input, but is not live health or readiness. Remote reachability and current
runtime health do not change membership. Process-local execution limits,
temporary execution permission, active execution count, remote permission
refusal, runtime failure, and transport failure are request-time facts and do
not change membership.

The response is a finite snapshot of the active process's existing composed
routing surface while it is constructed. It is not a subscription, lease,
reservation, readiness promise, reachability guarantee, or guarantee that a
later request will execute. Active composition may differ between this response
and a later request, and request-time conditions may independently change. The
later ordinary request and its accepted routing/execution path remain
authoritative.

## Native operation and response contract

The already-running ordinary HAC loopback process should provide:

```text
GET /diagnostics/caller-routable-capabilities
```

This route is native HAC diagnostics, not an ordinary business route and not
an OpenAI-compatible surface. It belongs only to the fixed existing ordinary
native loopback authority (currently RFC-0090's `127.0.0.1:25042`). It is
absent from receiver, trusted-LAN browser, compatibility/OpenAI, remote
transport, and any separately bound authority. This RFC neither changes that
authority nor grants a client host, port, URL, proxy, redirect, or target
choice.

The `/diagnostics/` path does not itself enforce that authority. The carrier
must be attached through application composition owned by the ordinary
originating native loopback process. A shared router or factory may be reused
only if the resulting route is absent from receiver, trusted-LAN browser,
compatibility/OpenAI, remote transport, and other separately bound application
authorities.

The operation accepts no body, query parameters, constraints, request content,
or selection input. It has no side effect and starts no background work.

On success it returns HTTP `200` with exactly:

```json
{"capabilities":["chat","summarize","code"]}
```

`capabilities` is an array of distinct accepted semantic capability names.
Membership and uniqueness are contractual; array order has no semantic meaning
and clients must not depend on it. An implementation may emit a deterministic
order, but no particular vocabulary iteration order is part of this native
contract. The array may be empty. It must not expose local-versus-remote
provenance, counts, priority, explanation, or any other fact.

If the active process cannot truthfully construct the projection from its
active composition, it fails closed with HTTP `503` and a fixed safe detail.
It must not guess from retained Configuration, defaults, adapters, browser
state, or input files. A malformed internal projection is likewise an ordinary
safe server failure, with no raw exception, internal object, or private detail
disclosed. Client connection, timeout, redirect, and response-validation
failure remain client-owned transport failures. This RFC introduces no larger
error taxonomy.

## Privacy, trust, and engine independence

The response must not reveal prompts, responses, source text, workspace or
file data, credentials, configuration values, model names, runtime names,
adapter names or instances, bindings, node IDs, machine names, remote
addresses or URLs, topology, health reasons, transport errors, execution-limit
values, active execution counts, routing priority, or execution history.

Only project-owned semantic capability names cross the boundary. No request
content is supplied or transmitted, and construction performs no network or
runtime activity. The operation consequently adds no external-data authority
and remains independent of concrete runtimes and models.

## Relationship to existing architecture

Retained Configuration remains future-invocation operator state under
RFC-0094 and successors; it is not read to answer this request. RFC-0144's
browser carrier remains browser-only and unchanged. This RFC adds a parallel
native carrier of the same core semantic projection; it does not turn browser
routes into a generic client API.

RFC-0146 through RFC-0148's active static-routing explanation accepts a
capability plus `local_only` and exposes candidate facts. RFC-0149 and
RFC-0150 explain one actually executed request, including request-time
lifecycle facts. Those operations are deliberately richer and do not replace
this zero-input set projection. This operation does not select a candidate,
reserve it, consume execution permission, mutate fallback state, or execute a
request.

An independent native thin client, including a future Desktop feature, may
consume this response only as HAC-owned presentation input. It must not import
`home_ai_cluster`, read Configuration or topology, call runtimes, infer hidden
facts from the response, reproduce routing, or treat membership as health or
an execution guarantee. This RFC specifies no Desktop UI, refresh, cache,
polling, navigation, or packaging behavior.

## Alternatives considered

| Alternative | Assessment |
| --- | --- |
| Client reconstructs capabilities from Configuration, declarations, or status | Rejected: it answers different questions and creates a second routing interpretation. |
| Reuse the browser route as the native contract | Rejected: RFC-0144 intentionally confines that carrier to browser authority. |
| Use `/v1/capabilities` | Rejected: it implies a generic or OpenAI-compatible inventory surface rather than a bounded HAC diagnostic projection. |
| Require a capability and `local_only` per query | Rejected: RFC-0146/0147 already provide a richer constraint-specific explanation; it is not the requested set projection. |
| Probe runtimes/remotes or expose health | Rejected: routability is not readiness or execution success and probing expands authority. |
| Generic discovery/introspection service | Rejected: one existing projector and one explicit route meet the need without framework architecture. |

## Trade-offs and compatibility

The contract gives an independent client a small amount of active-process
truth, but deliberately cannot promise immediate execution. Consumers must
handle an empty set, safe failure, and a later request that fails or differs.
The benefit is that clients stay capability-centered without learning topology
or duplicating routing.

This proposal is additive. It does not change RFC-0144 semantics, ordinary
request routes/results, routing, fallback, health/status, execution policy,
retained Configuration, browser behavior, receiver/trusted-LAN authority,
OpenAI compatibility, or Desktop. Once accepted and implemented, only this
route and its closed response/failure behavior become a native compatibility
contract.

## Falsifiable proof requirements

A future implementation must demonstrate at least:

1. The response is built by the already-running ordinary process from its
   active composition, not retained Configuration, another process, or client
   reconstruction.
2. A locally eligible capability is included; adapter support without the
   applicable active local eligibility path is not enough; caller-local
   restriction is respected.
3. An active static-cluster remote-only eligible capability is included, while
   neither remote reachability nor a remote probe is required.
4. Local plus remote eligibility yields one capability name; an absent path
   yields no name; a valid constructed active composition with no eligible
   capability paths returns a successful empty set through the real projector
   and native carrier. This proof does not require an existing production
   launcher to create that composition.
5. Membership is capability-centered and engine-independent, with no model,
   runtime, adapter, node, topology, configuration, health, or execution data
   in a valid response.
6. Construction makes no runtime call, remote/network probe, synthetic
   request, routing selection, fallback mutation, reservation, or execution
   permission attempt or consumption.
7. A subsequent ordinary request independently evaluates constraints,
   selection, execution permission, fallback, and failure; membership alone
   neither predicts nor guarantees that result.
8. Projection failure is safe and fail-closed; it does not cause a client to
   infer capability absence or trigger a replacement probe.
9. The route exists only on ordinary native loopback authority. Tests verify
   its actual absence from receiver, trusted-LAN, compatibility/OpenAI, remote
   transport, and other separately bound application compositions.
10. A small independent non-HAC HTTP client can consume and validate the
    closed response without importing `home_ai_cluster` or inspecting HAC
    Configuration/topology; a Desktop implementation is not required.

If implementation needs to alter RFC-0144 membership semantics, accepted
routing/fallback/execution behavior, native authority, or introduce a generic
introspection abstraction, it must return to architecture before proceeding.

## Impact

If accepted, implementation may add one small native carrier that calls the
existing RFC-0144 projector using the ordinary process's active composition,
with focused route and boundary tests. No implementation is authorized by this
Draft. No production code, tests, Desktop code, dependencies, or configuration
change is part of this RFC draft.

## Open questions

The proposal intentionally leaves no unresolved semantic question about the
set's meaning: it reuses RFC-0144. Co-architect review should confirm the
proposed native route spelling and whether this narrowly additive carrier is
the desired next client contract. Private helper placement and exact fixed safe
error wording remain implementation details.

## Decision

Accepted.
