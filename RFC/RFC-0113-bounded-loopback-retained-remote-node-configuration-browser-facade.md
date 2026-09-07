# RFC-0113: Bounded Loopback Retained Remote-Node Configuration Browser Facade

Status: Draft

Date: 2026-09-07

Author: frian

## Summary

This RFC proposes one bounded extension to RFC-0112's native-loopback browser
configuration facade. The browser may become a second facade over the
caller-owned retained remote-node declarations already owned by `hac config
node` in RFC-0094:

```text
native loopback browser
        |
        +-- retained local facade -------> hac config local authority
        |
        +-- retained remote-node facade -> hac config node authority

receiver application
        X-- no configuration facade
```

The extension is local caller configuration, not configuration or
administration of a remote machine. It reads and mutates only retained static
remote topology for future ordinary invocations, using the same validation and
semantic operations as `hac config node`. It adds no observation, probing,
discovery, live reconfiguration, dashboard, control plane, CORS, or general
authentication.

## Context

RFC-0058 accepts explicit, operator-declared allowed capabilities for static
remote declarations. RFC-0059 keeps routing capabilities caller-local and
static. RFC-0094 accepts one HAC-managed retained configuration with separate
`config local` and `config node` semantic domains: the former owns local
runtime composition and caller-local capability restrictions; the latter owns
caller-side retained static remote topology.

RFC-0109 closes the receiver application to its two accepted HAC-to-HAC
routes. RFC-0111 makes that receiver authority an explicit, separate listener
while retaining the ordinary native application on loopback. RFC-0112 accepts
a native-loopback browser facade over only the retained `config local` domain,
explicitly excluding `config node` and remote topology.

That exclusion leaves an ordinary operator split: the browser can manage
retained local configuration, while the CLI remains the only facade for
caller-owned retained remote-node declarations. This RFC considers only whether
the existing bounded browser may also facade the already accepted `hac config
node` authority.

## Problem

A caller may retain its static declarations of remote nodes through `hac
config node`, but must return to the CLI to inspect or correct them. Extending
the browser must not reinterpret those declarations as remote-machine truth or
authority. In particular, it must preserve the distinction:

```text
configure the caller's retained declaration of a remote node
!=
configure the remote node
```

The latter remains outside Home AI Cluster's accepted architecture.

## Goals

- Add a native-loopback browser facade over the existing `hac config node`
  semantic authority.
- Represent only caller-owned retained remote-node declarations and their
  retained order.
- Preserve the CLI's add, update, and removal meanings and its validation.
- Keep retained topology for future ordinary invocations distinct from the
  currently running process and its composition.
- Reuse RFC-0112's bounded native-browser request-authority boundary and
  RFC-0109/RFC-0111 receiver isolation.
- Preserve static, caller-declared capability ownership and existing routing
  order without observation or network activity.

## Non-goals

This RFC does not authorize configuring a remote machine's runtime; remote
runtime or model information; receiver host/port configuration or receiver
administration; remote execution limits or availability; capacity, slots,
workers, hardware, or GPU facts; credentials; TLS; CORS; or a general
authentication framework.

It does not add connection testing, HTTP probing, online/offline indicators,
health or status observation, capability validation against a remote, runtime,
node, DNS, or interface discovery. It does not add live topology
reconfiguration, current-process topology mutation, `LocalAppComposition`
reconstruction, retained multi-binding changes, `--runtime-config`
inspection/editing, external-information configuration, or Chat
external-information fallback configuration.

It does not add whole-topology replacement, PATCH/merge semantics, bulk
mutation, a rename operation, a reorder UI, priorities, weights, scheduling,
load balancing, a generic configuration API/framework, dashboard, cluster
monitoring surface, or cluster control plane. It authorizes no implementation
in this RFC PR.

## Proposal

### One additional bounded semantic domain

RFC-0112 remains valid for the retained-local domain. This RFC narrows only
its remote-topology exclusion: the same bounded browser configuration facade
may additionally read and mutate the existing `hac config node` domain. All
other RFC-0112 exclusions remain in force.

The browser is a second facade, not a new configuration owner:

```text
hac config node ----\
                    -> one retained remote-node semantic authority
browser facade -----/
```

Later implementation may extract the smallest reusable internal operation
needed to share CLI and browser semantics. It must preserve existing meanings
and must not use that refactor to introduce a generic configuration framework,
repository/persistence abstraction, precedence rule, topology schema, or new
mutation semantics. Transport-specific HTTP schemas and exact endpoint names
remain implementation details.

### Ownership and retained facts

The browser represents caller-owned retained remote-node declarations: the
caller-side static topology and eligibility facts that RFC-0094 already
assigns to `config node`. It does not represent another machine.

Each declaration exposes only these already accepted retained facts:

- `node_id`;
- configured explicit HTTP `base_url`; and
- caller-declared allowed capabilities.

`node_id` is a caller-local declaration identifier, not remotely attested
identity. `base_url` is configured data, not a value this facade contacts or
verifies. Allowed capabilities are caller-declared routing eligibility facts,
not remote advertisement, discovery, observation, runtime truth, or health
truth.

### Read semantics and inert values

Read authority exposes exactly the retained remote-node declarations and their
actual retained order. It reads retained configuration only. It must perform no
runtime or process observation, DNS or network probing, HTTP contact with a
configured base URL, health/status lookup, or capability discovery.

The values are inert configuration data. Displaying a retained node ID,
configured URL, or allowed capability must not interpret, resolve, probe,
fetch, navigate to, or otherwise activate that value. The browser must not
silently sort declarations: retained declaration order is displayed as
retained.

### Mutation semantics

The browser uses exactly the semantic operations already owned by `hac config
node`; it does not replace the topology as a whole.

For an add, when a supplied `node_id` is absent, the browser creates one valid
retained declaration and appends it to the end of retained declaration order.

For an update, when the supplied `node_id` already exists, the browser replaces
that declaration and preserves its current position. The existing `node_id` is
the identity of the declaration being edited; it is immutable during an edit.
Only the configured base URL and caller-declared allowed capabilities may
change. The first facade introduces no rename semantics. An operator may use
the existing remove-plus-add expression, with its existing ordering
consequences, when a different identifier is needed.

For removal, the browser removes exactly one declaration identified by
`node_id`. Removing a declaration that is not retained fails visibly, with the
same meaning as the CLI.

Each mutation preserves every other retained declaration, their order, and
every unrelated retained configuration domain. Invalid input must not persist a
partial change. Existing validation for node IDs, remote base URLs, and the
closed capability vocabulary and allowed-capability declarations remains
authoritative.

The retained ordering consequences are therefore exactly:

```text
[A, B, C] + add D -> [A, B, C, D]
update B          -> [A, B', C]
remove B          -> [A, C]
```

The browser receives no reorder authority. Drag-and-drop, move controls,
implicit sorting, priority fields, weights, and scheduling semantics are not
accepted.

### Retained state is not current process state

The browser represents retained static remote topology for **future ordinary
invocations**. Saving a declaration changes neither the already constructed
`LocalAppComposition` nor the current process's static routing topology. It
does not reconstruct routing or composition, reload or restart HAC, alter
receiver authority, contact the configured node, or test connectivity.

Consequently, the current process may continue using topology different from
the newly retained future-launch topology. This is intentional retained-state
semantics under RFC-0094, not accidental stale state:

```text
retained node change
        |
        v
future ordinary invocation

current running process -------- unchanged
```

### Request-authority and receiver boundary

The remote-node facade exists only on the ordinary native application at HAC's
accepted effective loopback authority. It is structurally absent from the
RFC-0109 receiver application.

Persistent mutation uses RFC-0112's bounded native-browser authority: an
accepted native Host authority, an exact same-origin `Origin`, and a bounded
JSON/non-simple request. Configuration requests must be addressed to HAC's
accepted effective native authority; client-controlled Host and Origin values
must not validate one another. No cross-origin CORS authority is granted.

This remains protection against unrelated Web origins, not authentication
against arbitrary local processes or local users able to forge loopback HTTP
headers. Login, accounts, sessions, OAuth, tokens, TLS, and general
authentication remain separate decisions. Malicious mutation of a retained
configured URL could affect a future ordinary invocation, which is why the
same bounded same-origin mutation boundary applies to this additional domain.

## Privacy and security

Retained remote-node declarations are local HAC-managed state and may contain
private LAN values. The page may show their bounded retained facts because the
operator explicitly opened the local facade, but this does not authorize
broader disclosure or logging. Reads, validation, add, update, and removal
must not contact a configured node. Local-first and privacy-first defaults,
including the existing request-origin boundary, remain unchanged.

## Compatibility

The browser facade is additive and optional. Existing `hac config node`, `hac
config local`, and `hac config show` remain fully supported, as do retained
storage semantics, ordinary startup consumption, explicit topology/declaration
override rules, and existing routing behavior. RFC-0058/RFC-0059 capability
semantics, RFC-0109 receiver route isolation, RFC-0111 receiver activation,
and RFC-0112 retained-local browser behavior remain unchanged.

## Rationale

The established native loopback browser is the smallest useful second facade
for already accepted caller-local configuration. Sharing `config node`
semantics avoids a second topology mutation model and keeps validation and
ordering truthful. The narrow scope preserves the architectural difference
between a caller declaring where it may route and administering a remote
machine. Reusing RFC-0112's request boundary addresses the specific
unrelated-Web-origin threat without prematurely creating a broader local
identity system.

## Alternatives considered

### Keep `config node` CLI-only

This remains simple and functional, but leaves an unnecessary split ordinary
configuration experience after RFC-0112.

### Whole-topology browser replacement

Rejected. It would create a second mutation model instead of reusing the
accepted `hac config node` semantic operations, and would risk hidden merge or
ordering behavior.

### Generic retained-configuration browser API

Rejected as premature. The demonstrated need is one additional bounded domain,
not a general API or configuration framework.

### Browser connection test or health view

Rejected because it turns retained configuration into runtime/network
observation and would activate configured values.

### Remote administration

Rejected because caller-owned declarations do not grant authority over the
remote machine.

### Reorder UI

Rejected because no new ordering mutation is necessary for the first useful
facade, and retained declaration order already has accepted routing meaning.

### Rename operation

Rejected because existing `config node` semantics do not own it. Remove plus
add remains explicit and preserves its accepted ordering consequences.

## Trade-offs and consequences

The facade intentionally reports retained declarations rather than connection
or runtime truth. It can therefore be useful without answering whether a
configured endpoint is reachable or suitable at this moment. The absence of a
rename or reorder operation keeps the mutation contract small, while remove
plus add remains available through the established semantics. A browser page
can become stale after a CLI mutation; this RFC introduces no revision,
compare-and-swap, merge, or distributed-coordination system.

## Implementation boundary

After acceptance, a later implementation may add one native-loopback retained
remote-node browser view; bounded retained read, add, update, and removal
surfaces; the stated Host/Origin/non-simple request checks; minimal shared CLI
and browser semantic-authority reuse; focused frontend/backend and receiver
route-isolation tests; and operator documentation. It must not implement
anything outside this RFC's non-goals. This Draft RFC authorizes no
implementation.

## Proof expectations

A later implementation must prove at minimum that:

1. the facade exists only on native loopback authority and never on the
   RFC-0109 receiver application;
2. read returns retained declarations only, in retained order, with no runtime,
   node, or network observation;
3. displaying a retained configured base URL causes no resolution, request,
   probe, health check, navigation, or capability discovery;
4. add appends exactly one declaration and preserves prior declarations, their
   order, and every unrelated retained domain;
5. update changes only the selected declaration and preserves its position;
6. an update cannot rename `node_id`;
7. remove deletes exactly the identified declaration and missing-declaration
   removal fails visibly;
8. browser and CLI share authoritative node ID, base URL, and allowed
   capability validation, and invalid mutation persists no partial state;
9. retained node mutation does not change current-process routing or
   composition, while a future ordinary invocation consumes changed retained
   topology under RFC-0094;
10. accepted Host authority is required for configuration disclosure/mutation
    as applicable, and mutation requires exact same-origin Origin; absent,
    `null`, or foreign Origin cannot mutate state;
11. no CORS authority is introduced and RFC-0109 receiver route isolation
    remains exact; and
12. no probing, health/status, discovery, runtime/model/capacity observation,
    scheduling, reorder semantics, dashboard, or control-plane behavior
    appears, while existing CLI and RFC-0112 browser behavior remain
    compatible.

## Open questions

None remain within this proposed boundary. General local authentication, a
stale-state product problem requiring coordination, or any remote-management,
observation, or topology-model change requires a separate RFC.

## Decision

Proposed: Home AI Cluster should extend RFC-0112's native-loopback browser
facade to the already accepted caller-owned retained `hac config node` domain.
The browser would read and mutate only retained remote-node declarations for
future ordinary invocations, with existing add/update/remove and ordering
semantics, shared validation, inert configured values, native-only
same-origin mutation authority, and exact receiver isolation.

It would not configure or observe remote machines, activate configured URLs,
change the running process, create a whole-topology or generic configuration
API, or add a dashboard, control plane, CORS, TLS, or authentication framework.
