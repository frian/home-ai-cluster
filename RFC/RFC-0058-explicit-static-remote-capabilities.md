# RFC-0058: Explicit static remote capabilities

Status: Draft

Date: 2026-07-28

Author: frian

## Summary

This RFC proposes bounded, operator-declared capability sets for ordinary static
remote nodes. The accepted explicit names are chat and summarize. An omitted
capability field retains the existing implicit chat plus summarize behavior.

The proposal applies equivalently to multi-remote TOML, legacy flat
single-remote TOML, and the existing single-remote inline path. It preserves
local-first routing, remote declaration order, and bounded pre-request fallback.
It does not configure the local node, probe remotes, expand status, or add
scheduling.

## Context

The completed heterogeneous static capabilities investigation recorded Outcome
C: node descriptions and routing already support capability eligibility, while
ordinary static declarations cannot express different remote capability sets.

RFC-0004 makes capabilities part of a node description. RFC-0016 defines
declared-remote eligibility using caller-owned declarations, static availability,
and declared capability membership. RFC-0040 makes remote declaration order the
only remote priority rule. RFC-0051 establishes summarize as the second
executable capability alongside chat.

The present ordinary construction path assigns both capabilities to every
declared remote after parsing only a node ID and base URL. Consequently, an
operator cannot declare a chat-only or summarize-only remote although the router
can filter either description.

## Problem

A static declaration says which remote nodes the caller may consider, but it
cannot state which accepted capabilities the caller is allowed to route to each
one. That prevents an ordinary operator-facing heterogeneous remote proof.

Deriving this information from remote health, a remote application, adapters,
models, or hardware would replace operator-owned static data with observation
and broaden the system beyond its deterministic declaration boundary.

## Goals

This RFC proposes to:

* allow each ordinary static remote declaration to state a bounded capability
  set;
* preserve declarations that omit capability data;
* preserve equivalent one-remote inline and TOML semantics;
* keep capabilities static, operator-owned, local to declaration validation, and
  network-free;
* preserve existing routing, ordering, fallback, and public status contracts;
  and
* reject invalid capability configuration before process startup.

## Non-goals

This RFC does not introduce:

* local-node capability configuration or a new local composition surface;
* runtime capability probing, adapter/model-derived declarations, discovery, or
  automatic capability updates;
* scheduling, scoring, weights, configurable priorities, round-robin, load
  balancing, fastest-node selection, hardware/model-aware routing, or a generic
  policy engine;
* retries or fallback redesign;
* status-result expansion, health-aware routing, persistence, a database,
  Docker, Kubernetes, a dashboard, runtime management, or model inventory;
* arbitrary capability names or a generic capability configuration framework;
  or
* implementation, tests, a proof, a roadmap phase, or Phase 19 in this RFC PR.

## Decision

### Capability ownership

A declared remote capability set states only which capabilities the caller is
allowed to route to that explicitly declared remote node. It is static,
operator-owned declaration data.

It is not runtime probing or runtime-discovered truth; a guarantee that a remote
application, adapter, or runtime implements a capability; a health or
reachability assertion; dynamic state; or mutable status information. Existing
request execution and status observation retain their established boundaries.

The fixed ordinary local node retains its existing composition-owned capability
behavior. This RFC deliberately creates no local configuration surface. A
topology that also requires heterogeneous local capabilities requires a separate
decision.

### Capability vocabulary and set rules

The closed explicit vocabulary contains exactly:

    chat
    summarize

An explicit list must contain at least one string. Every item must be in that
vocabulary, and duplicate items are invalid. Unknown names, non-string items,
an empty list, and duplicates fail local declaration parsing or preflight
preparation before ordinary startup and before network activity.

Capability-list order has no routing, fallback, or priority meaning. Membership
controls eligibility only. Remote-node declaration order remains the only remote
priority rule.

### TOML declaration contract

An entry in the existing ordered remote collection may include capabilities:

    [[remote_nodes]]
    node_id = "chat-node"
    base_url = "http://example.invalid:8000"
    capabilities = ["chat"]

    [[remote_nodes]]
    node_id = "summary-node"
    base_url = "http://example.invalid:8001"
    capabilities = ["summarize"]

Each entry otherwise retains its node_id and base_url contract. Unknown keys
continue to fail. Omitting capabilities constructs the compatibility default
chat plus summarize; it never triggers runtime discovery.

The legacy flat single-remote TOML form remains supported and gains the
corresponding optional remote_capabilities field:

    remote_node_id = "single-remote"
    remote_base_url = "http://example.invalid:8000"
    remote_capabilities = ["chat"]

Omission has the same compatibility default. This avoids contradictory
single-remote TOML contracts and preserves one-remote equivalence.

### Inline declaration contract

The existing exactly-one-remote inline form gains repeatable
--remote-capability NAME options:

    --remote-node-id single-remote
    --remote-base-url http://example.invalid:8000
    --remote-capability chat
    --remote-capability summarize

No remote-capability option uses the compatibility default. One or more options
construct exactly the supplied set after closed-vocabulary, non-empty, and
duplicate validation. Declaration mode and all inline topology options,
including remote-capability, remain mutually exclusive.

This repeated spelling matches existing repeated CLI-value practice without a
comma-separated mini-language. Equivalent one-remote TOML and inline inputs must
construct equivalent IDs, normalized base URLs, and capability sets.

### Backward compatibility

Existing valid inline, flat TOML, and multi-remote TOML declarations without
explicit capability data continue to declare chat and summarize. This is a
compatibility rule, not runtime discovery.

No declaration form, accepted capability, local-first behavior, remote ordering
rule, or status field is removed. Explicit capability sets are additive and
opt-in.

### Routing consequences

This RFC changes declaration representation, not routing policy. The accepted
sequence remains:

1. filter candidates by requested capability;
2. preserve local-first selection among eligible candidates;
3. preserve declaration order among eligible remotes;
4. preserve bounded traversal only for the accepted pre-request
   connection-unavailable condition; and
5. preserve stopping behavior for every other failure.

A chat-only remote is ineligible for summarize and a summarize-only remote is
ineligible for chat. This does not select a fastest, healthiest, strongest, or
otherwise optimal node. No scheduler or direct node selector is introduced.

### Preflight consequences

Static preflight validates declaration-owned capability data locally and without
network access as part of preparing coherent static declarations. Its existing
per-node capability representation reports the constructed declared list. It
does not contact a remote, probe a runtime, verify adapter implementation, or
turn declaration coherence into runtime availability.

### Status consequences

The public status result remains unchanged. It continues to report declaration
coherence, application reachability, and runtime observation through its
accepted fields; it does not report capability lists. A later heterogeneous proof
may use validated declaration input, preflight output, request attribution, and
existing structured failures. Status expansion needs a separate decision.

### Failure behavior

Malformed explicit capability data is a local declaration validation failure. It
fails before application construction, endpoint binding, or remote network
activity through the established safe declaration/preflight failure boundaries.
It must not expose a remote URL, declaration contents, raw parser details, or
runtime information.

After valid declaration construction, existing request failures remain
authoritative. No eligible capability uses the existing structured
capability-related failure; an eligible candidate's runtime or transport failure
remains an execution-time outcome. This RFC creates no public failure category.

## Rationale

The proposal makes the caller's allowed remote routing surface explicit while
retaining the existing simple default. A closed two-name vocabulary is truthful
to the current executable surface and avoids a plugin-shaped framework.

Optional fields preserve compatibility. Rejecting bad or duplicate values is
more transparent than silent normalization. Capability-list order is explicitly
meaningless so it cannot become a second priority system; remote declaration
order stays the only priority rule.

Keeping fixed local composition and status unchanged respects their accepted
boundaries and keeps this decision narrow.

## Alternatives considered

### Keep implicit capabilities on every remote

Rejected because it cannot express heterogeneous remote eligibility.

### Probe the remote application

Rejected because it introduces network observation and dynamic state into a
static operator-owned declaration.

### Derive capabilities from runtime adapters or models

Rejected because remote eligibility is declaration-backed, while adapters and
models are runtime details.

### Add capabilities only to TOML

Rejected because it would make equivalent one-remote TOML and inline declarations
inconsistent.

### Make capabilities mandatory immediately

Rejected because it breaks established declarations without need.

### Accept arbitrary capability strings

Rejected because arbitrary names imply an extension vocabulary or registry
without an accepted executable contract.

### Normalize duplicates silently

Rejected because duplicate declaration data is an operator error and rejection
is deterministic and visible.

### Add capabilities to status now

Rejected because status intentionally separates declaration coherence from
application and runtime observation.

### Configure local-node capabilities in this RFC

Rejected because local capabilities are composition-owned and would add a
separate authority and operator-interface decision.

### Introduce priorities, weights, or scheduling

Rejected because RFC-0040 already makes remote declaration order the only
remote priority rule. Capability membership filters eligibility; it does not
optimize a target.

## Consequences

If accepted, an operator can declare a remote as chat-only, summarize-only, or
capable of both operations without probing it. Existing declarations remain
valid and retain their behavior.

A later implementation is bounded to declaration parsing and validation, remote
construction, inline/TOML equivalence, preflight representation or validation,
focused tests, documentation, and a later ordinary heterogeneous proof. The
router does not need redesign because it already consumes declared capability
sets.

## Security and privacy

Capabilities are static low-sensitivity declaration facts, but declarations
continue to contain private endpoint data. Existing privacy rules remain:
public errors, request history, routing explanations, status output, proof
records, and ordinary logs must not expose remote URLs, private addresses,
credentials, prompts, responses, raw parser errors, or runtime-private errors.

Validation is local and read-only. It performs no DNS resolution, remote
connection, runtime probe, state mutation, file rewrite, cache, telemetry, or
project-owned persistence.

## Implementation boundary

A later implementation may affect only the ordinary static declaration parser
and validators, static remote construction, corresponding inline parsing,
preflight preparation or representation as needed, focused tests, and accurate
operator documentation. It must preserve routing, fallback, transport, status,
runtime, and local composition boundaries.

This RFC does not prescribe an implementation sequence or authorize
implementation in this PR.

## Proof expectations

After separate implementation, focused evidence and one later ordinary
heterogeneous proof should demonstrate:

* one chat-only remote and one summarize-only remote;
* chat excludes the summarize-only remote;
* summarize excludes the chat-only remote;
* local-first applies only among eligible candidates;
* declaration order remains deterministic when multiple remotes are eligible;
* no eligible node produces the existing structured capability-related failure;
* preflight represents declared remote capability sets;
* status remains unchanged; and
* no scheduler, topology selector, or runtime probing is introduced.

Retained proof material must use placeholders only and must not retain private
environment data, prompts, responses, private URLs, or machine identifiers.

## Open questions

None within this remote-declaration scope.

A future question remains whether fixed local-node capability ownership needs an
explicit configuration contract. This RFC neither answers nor blocks that
question.

## Decision

Pending.
