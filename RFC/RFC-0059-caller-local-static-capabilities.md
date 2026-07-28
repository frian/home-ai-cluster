# RFC-0059: Caller-local static capabilities

Status: Draft

Date: 2026-07-28

Author: frian

## Summary

This RFC proposes a bounded, caller-local capability declaration for ordinary
`hac static-cluster` processes. It lets an operator restrict the fixed local
routing candidate to `chat`, `summarize`, or both, while preserving the
compatibility default of both capabilities.

The declaration means only which capabilities the caller-side static-cluster
router may consider locally. It does not change adapter implementation, runtime
health, endpoint registration, `hac local` receiver composition, or
caller-owned remote declarations. Existing eligibility, local-first routing,
remote declaration order, bounded fallback, status, and failure contracts
remain unchanged.

## Context

RFC-0058 established explicit bounded capabilities for ordinary static remote
declarations. The retained heterogeneous proof showed that remote declarations
filter eligibility, but a healthy fixed local node still declares both `chat`
and `summarize`; it therefore wins locally for both before a remote is
considered.

The local capability ownership investigation recorded Outcome C: current local
capabilities are fixed composition-owned declarations, and no ordinary
operator-facing path can restrict them. The smallest demonstrated need is:

```text
caller local: chat
declared remote: summarize
```

Under that topology, chat should remain local while summarize excludes the
healthy caller-local candidate and reaches an eligible remote through existing
routing. This RFC decides that caller-local declaration boundary without making
receiver behavior or cross-node capability agreement configurable.

## Problem

Today an ordinary static-cluster caller cannot express that its fixed local
routing candidate is allowed to provide only one accepted capability. As a
result, explicit remote specialization is normally observable only after the
accepted local pre-request connection-unavailable condition.

Deriving a local set from adapter methods or runtime health would conflate
cluster routing permission with runtime implementation and observation. Changing
the router or adding a selector would solve a different problem: existing
eligibility filtering already excludes a local node that does not declare the
requested capability before local-first selection occurs.

## Goals

This RFC proposes to:

- let an ordinary static-cluster caller declare a bounded local routing
  capability set;
- provide equivalent inline and TOML declaration surfaces;
- reuse the closed `chat` and `summarize` vocabulary and set semantics from
  RFC-0058;
- preserve omission as `chat` plus `summarize`;
- apply the same caller-local declaration to static preflight;
- preserve local-first among eligible candidates, remote order, and bounded
  pre-request fallback;
- keep `hac local` and receiver-side execution composition unchanged; and
- preserve current status and public failure contracts.

## Non-goals

This RFC does not introduce:

- configuration for `hac local`;
- receiver-side local capability restriction;
- capability negotiation, cross-node validation, or remote capability probing;
- adapter enablement or disablement, runtime discovery, or runtime health
  changes;
- direct node selection, remote preference, priorities, weights, scheduling,
  load balancing, or fastest-node selection;
- model- or hardware-aware routing;
- arbitrary capability names, a plugin registry, or a generic topology schema;
- local IDs, local addresses, local adapters, or runtime settings in a topology
  declaration;
- status expansion, persistence, a database, Docker, Kubernetes, or a
  dashboard;
- implementation, tests, retained proof, roadmap work, or Phase 19 in this RFC
  PR.

## Decision

### Ownership and scope

An ordinary `hac static-cluster` process may declare the capabilities its
fixed local routing candidate is allowed to provide. This is static,
operator-owned, caller-local routing permission.

It is not an assertion of which operations a local adapter implements, which
operations a runtime currently provides, runtime health or reachability, an
endpoint exposure setting, receiver capability advertisement, or remote
verification.

The scope is intentionally asymmetric:

```text
hac static-cluster local capability restriction
  -> caller-side routing permission

hac local receiver
  -> unchanged local execution composition
```

An ordinary receiver continues to use its existing local composition and
capabilities. A caller's remote declaration remains caller-owned and is not
validated against a receiver-local declaration. This RFC creates no dynamic
negotiation or cross-machine agreement contract.

### Capability vocabulary and set rules

The local declaration vocabulary is exactly:

```text
chat
summarize
```

An explicit set must contain at least one string, contain only those names, and
contain no duplicate. Empty sets, non-string values, unknown names, and
duplicates fail local declaration or preflight preparation before application
construction and before network activity.

Capability-list order has no eligibility, routing, fallback, or priority
meaning. It must not be sorted merely for convenience. Remote declaration order
remains the only remote priority rule.

Omission preserves the compatibility default:

```text
chat + summarize
```

Implementations should reuse RFC-0058's accepted vocabulary and validation
semantics rather than create a second capability-validation policy.

### Inline static-cluster syntax

The exactly-one-remote inline form gains repeatable local capability input:

```text
hac static-cluster \
  --remote-node-id <NODE_ID> \
  --remote-base-url <BASE_URL> \
  --local-capability chat \
  --remote-capability summarize
```

`--local-capability NAME` belongs only to inline static-cluster topology mode.
It may be repeated once per requested local capability. It requires the
existing complete inline remote identity pair and is mutually exclusive with
`--declaration`.

With no `--local-capability` option, the caller-local declaration remains
`chat` plus `summarize`. With one or more options, it contains exactly the
validated supplied set in supplied order.

### TOML static declaration syntax

Both accepted TOML shapes gain one optional root field:

```toml
local_capabilities = ["chat"]

[[remote_nodes]]
node_id = "summary-remote"
base_url = "http://example.invalid:8000"
capabilities = ["summarize"]
```

The legacy flat one-remote shape uses the same optional root field:

```toml
remote_node_id = "summary-remote"
remote_base_url = "http://example.invalid:8000"
remote_capabilities = ["summarize"]
local_capabilities = ["chat"]
```

`local_capabilities` contains only caller-local routing capability data. It
does not introduce a `[local_node]` table, local identity, address, adapter,
runtime setting, or general topology object. It is valid in either otherwise
valid flat or ordered declaration shape and follows the same set rules above.
Its omission preserves the compatibility default.

Declaration mode cannot be combined with inline local or remote topology
arguments. In particular, `--local-capability` must not override or merge with
`local_capabilities`.

### Construction semantics

The selected set changes only the fixed local `NodeDescription` constructed
for the calling static-cluster process. The local adapter remains registered
with its existing implementation and capability methods. Runtime configuration,
health, endpoint registration, native request shapes, remote transport, and
receiver application construction remain unchanged.

The caller process still exposes its existing chat and summarize endpoints.
Their normal routing path uses the restricted caller-local description; an
endpoint is not removed merely because its local candidate is ineligible.

### Routing and failure consequences

No router policy changes are authorized. Existing behavior remains:

1. filter candidates by declared requested capability;
2. apply local-first only among eligible candidates;
3. preserve remote declaration order among eligible remotes;
4. preserve bounded traversal only for the accepted pre-request
   connection-unavailable condition; and
5. preserve stopping behavior for every other failure.

For example, with local `["chat"]` and one remote `["summarize"]`:

```text
chat:
  local is eligible
  local-first selects local

summarize:
  local is ineligible
  the eligible summarize remote is selected directly
  no local summarize runtime attempt is made
```

This is capability eligibility, not remote preference or scheduling.

When neither the restricted local candidate nor any declared remote supports a
request, the existing structured no-selectable/no-capability outcome remains
authoritative. No public failure category is added. This differs from an
eligible local runtime failure, an eligible remote transport failure, and a
local declaration validation failure.

### Preflight and status

The static preflight path that evaluates the same caller topology accepts and
validates local capability input using the same rules:

- inline preflight accepts repeatable `--local-capability NAME` only with its
  complete inline static topology;
- declaration preflight reads optional root `local_capabilities`; and
- omission retains both capabilities.

Preflight projects the constructed restricted local list in its existing node
representation. It remains local, read-only, deterministic, and network-free;
it does not probe a runtime or remote node. The standalone local-only preflight
mode gains no local-capability option.

Public status remains unchanged and does not expose local capability lists. A
future status capability field requires a separate decision.

### Compatibility

Existing static-cluster inline invocations, flat TOML declarations, ordered
TOML declarations, and static preflight invocations that omit local capability
data retain local `chat` plus `summarize` behavior. Existing `hac local`
behavior is unchanged.

## Rationale

The decision gives operators a small explicit boundary for healthy-operation
capability distribution without making them select a machine. The router still
chooses automatically inside the declared eligibility boundary; local-first
remains intact whenever local is eligible.

Caller-local scope is deliberately smaller than changing every ordinary local
composition. It meets the demonstrated static-caller need while avoiding a
receiver-policy change, a cross-machine mismatch protocol, and dynamic
capability negotiation. Reusing RFC-0058's two-name vocabulary and validation
keeps the new contract closed and understandable.

One optional root field fits both established TOML shapes because it describes
only the fixed caller-local routing candidate. It avoids introducing a generic
local-node table or duplicate identity and runtime configuration domains.

## Alternatives considered

### Keep the local node permanently broad

Rejected. It prevents healthy-operation specialization and makes explicit remote
capabilities primarily useful through fallback.

### Configure every `hac local` composition

Rejected for this RFC. It changes inbound receiver behavior and broadens local
capability ownership beyond the demonstrated caller-routing need.

### Add a generic `[local_node]` declaration table

Rejected. It implies a general topology schema and invites unnecessary local
identity, address, adapter, and runtime fields.

### Derive the local set from adapters

Rejected. Adapter implementation and caller routing permission answer different
questions. Derivation would also make the operator boundary depend on
runtime-specific implementation behavior.

### Probe the runtime

Rejected. Runtime probing introduces dynamic observation into static
eligibility and confuses declaration with reachability.

### Add direct node selection or remote preference

Rejected. Existing capability filtering plus local-first already produces the
required result without allowing a caller to target a node.

### Allow an empty local set

Rejected. The current node model requires at least one capability, and a
remote-only caller mode would be a separate architectural decision.

### Add status capability reporting

Rejected as unrelated to the routing need. The existing status contract remains
valid without exposing declaration capability lists.

## Consequences

If accepted, an implementation may add only the bounded static-cluster and
corresponding preflight declaration parsing, shared validation reuse,
caller-local node construction, focused tests, and accurate operator
documentation.

It must not alter routing policy, adapters, runtime configuration, endpoint
registration, receiver composition, status, remote capability ownership,
transport, or fallback behavior. It must not extend the local-only `hac local`
configuration surface.

## Security and privacy

Local capability names are low-sensitivity static declaration data. Validation
is local and must not resolve names, contact a runtime or remote, mutate state,
or retain configuration outside existing process lifetime.

The feature must not expose or retain remote URLs, addresses, credentials,
runtime details, prompts, responses, filesystem paths, model inventory,
hardware details, raw exceptions, or environment data through errors, status,
history, logs, or retained proof material.

## Implementation boundary

A later implementation may affect only:

- static-cluster inline argument parsing and caller-local construction;
- static declaration parsing for optional root `local_capabilities`;
- static preflight parsing, validation, and local projection for the same
  caller topology;
- focused construction, validation, routing-eligibility, and preflight tests;
- operator documentation and one later retained ordinary proof.

It must use the existing router and public status result unchanged. It must not
add a local option to `hac local`, change receiving applications, or introduce
cross-node capability validation.

## Proof expectations

After implementation, one later ordinary real process-and-HTTP proof should
demonstrate:

- a healthy caller-local runtime with caller-local capabilities restricted to
  `chat`;
- one declared summarize-only remote;
- local chat selection;
- summarize exclusion of the healthy local candidate and successful remote
  execution with no local summarize attempt;
- unchanged local-first, remote order, and failure boundaries;
- no selector, scheduler, probing, or fallback trigger;
- preflight projection of the restricted local list; and
- existing structured no-eligible-capability behavior when neither local nor
  remote declares the request capability.

Retained evidence must use placeholders and exclude private topology, prompts,
source content, generated responses, logs, credentials, and environment data.

## Open questions

None within the caller-local static-cluster scope.

A separate future question is whether ordinary `hac local` receiver processes
ever need an explicit local capability restriction. This RFC neither answers
nor authorizes that question.

## Decision

Pending.
