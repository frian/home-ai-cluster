# RFC-0009: Static Local Node Announcement Boundary

Status: Draft

Date: 2026-07-04

Author: frian

## Summary

This RFC defines the ownership and source of truth for the Phase 2 static local
node announcement.

RFC-0008 makes the node boundary explicit while keeping the implementation
single-process and local. This RFC proposes that the Phase 2 local node
announcement is an explicit local declaration constructed in-process by wiring
code for now.

The announcement describes cluster-facing node metadata only. It is not
discovered dynamically, derived from live runtime probing, owned by runtime
adapters, or loaded from a file-based configuration format yet.

## Problem

Home AI Cluster now has an explicit static node boundary, but the project still
needs to decide where the local node description comes from.

Without a clear source of truth, future changes could accidentally treat the
static local node as:

- runtime adapter metadata;
- live runtime inventory;
- discovered machine state;
- implicit orchestration wiring;
- a configuration format;
- a future registration protocol.

Those are different architectural decisions.

The Phase 2 implementation should remain boring and local, but it should not
hide ownership of the node announcement inside incidental code. The project
needs a small boundary that says what counts as a node announcement, who owns
it, and what information it may contain.

## Goals

This RFC should:

- define what counts as a node announcement in Phase 2;
- define the source of truth for the static local node description;
- clarify whether capabilities and adapter names are declared or derived;
- keep runtime-specific details behind runtime adapters;
- preserve local-first and privacy-first defaults;
- avoid introducing dynamic node behavior;
- leave file-based configuration as a possible future option without defining
  it now;
- keep routing behavior unchanged.

## Non-goals

This RFC does not introduce:

- remote nodes;
- a node HTTP API;
- discovery;
- a registration protocol;
- a daemon or agent process;
- fallback;
- retries;
- health polling;
- runtime supervision;
- a database or persistence layer;
- a dashboard;
- Docker;
- an API compatibility layer;
- health-based routing;
- model inventory;
- model placement automation;
- runtime-specific details in core.

It also does not define a file-based configuration format.

Future file-based configuration, discovery, remote registration, or
adapter-derived inventory require separate RFCs.

## Proposal

In Phase 2, the static local node announcement should be an explicit local
declaration.

A node announcement is the cluster-facing declaration that a known execution
environment exists and may be considered by the orchestrator and router. For
Phase 2, that execution environment is still the single local process.

The static local node announcement may be constructed in-process by wiring code
for now.

It should not be discovered dynamically.

It should not be derived from live runtime probing.

It should not be owned by runtime adapters.

It should declare only cluster-facing metadata:

- node id;
- display name;
- availability;
- descriptive health;
- declared capabilities;
- declared adapter names.

Capabilities and adapter names are declared manually as part of the static local
announcement. They are not inferred from runtime adapter health checks, runtime
model lists, runtime endpoints, process inspection, or network discovery.

The static local node announcement says:

```text
This local node is allowed to provide these cluster capabilities through these
declared adapter names.
```

It does not say:

```text
This runtime is live right now.
These models are installed.
This machine was discovered.
This node is reachable over the network.
This process should be supervised.
```

Runtime adapters remain responsible for runtime-specific behavior, including
runtime endpoint URLs, runtime request formats, runtime-specific failures,
runtime availability at call time, and any runtime model naming needed to
execute a request.

Model inventory remains out of scope for the node announcement. The static
local node may declare a capability such as `chat`, but it does not enumerate
models, model files, model placement, model download state, or model-specific
routing metadata.

This RFC does not change routing behavior. The router may continue using the
current minimal behavior allowed by RFC-0008:

- match the requested capability;
- consider static node availability;
- use declared adapter names;
- select a matching registered adapter.

Node health remains descriptive and does not drive routing.

## Rationale

An explicit local declaration keeps Phase 2 honest without making the system
dynamic too early.

It preserves the boundary from RFC-0008:

```text
single process
  -> static local node description
  -> local runtime adapter
```

Manual declaration is intentionally boring. It avoids hidden runtime probing,
system inspection, model inventory, discovery, registration, and supervision.
It also keeps the node boundary engine-independent because the node does not
need to understand Ollama or any other runtime.

Keeping the declaration out of runtime adapters protects adapter boundaries.
Adapters know how to speak to runtimes. They should not own the cluster-visible
identity of the node or decide which node metadata the cluster is allowed to
see.

Keeping file-based configuration out of this RFC avoids deciding a user-facing
configuration format before the project needs one. A later RFC may introduce
file-based local node declarations if that becomes the smallest useful next
step.

## Alternatives considered

### Keep the source of truth implicit

The current code can continue constructing a static local node without naming
that behavior.

This is simple in the short term, but it makes future changes harder to review.
Without an explicit boundary, runtime probing, adapter-derived metadata, or
configuration decisions could appear as implementation details instead of
architecture.

### Let runtime adapters own node announcements

Adapters could announce which node capabilities they provide.

This would couple cluster-visible node identity to runtime-specific adapter
behavior. It would make the core more likely to inherit runtime assumptions and
would blur the distinction between a node, an adapter, and a runtime.

### Derive the announcement from live runtime probing

The system could ask local runtimes what they support and build the node
announcement from the answer.

This would introduce dynamic runtime inventory, availability checks, and
possibly model inspection. Those behaviors are outside Phase 2 and would make
the node dynamic before the project has accepted discovery, polling, or
inventory boundaries.

### Define file-based configuration now

A configuration file may eventually be the right source for local node
declarations.

Defining that format now would introduce compatibility and user-facing
configuration questions before they are necessary. This RFC leaves file-based
configuration as a future option.

### Introduce registration or discovery

Registration and discovery may become important for later phases.

They are explicitly out of scope here. This RFC defines a local declaration,
not a protocol for finding or registering nodes.

## Trade-offs

This proposal makes the Phase 2 source of truth clear and reviewable.

It keeps the implementation local, static, and easy to understand.

It also means the static announcement may not reflect live runtime state. That
is acceptable because RFC-0007 keeps runtime availability at adapter call time,
and RFC-0008 keeps node health descriptive.

Manual declarations may feel repetitive because an adapter also exposes its
capabilities. That repetition is acceptable for now because the node
announcement and adapter implementation answer different questions:

- the node announcement declares what the cluster is allowed to consider;
- the adapter declares what the runtime adapter can execute.

The proposal deliberately postpones file-based configuration, runtime-derived
inventory, and remote node behavior. That keeps Phase 2 small, but it means
later RFCs must define those boundaries before implementation.

## Impact

This RFC affects Phase 2 node ownership and source-of-truth boundaries.

It does not require a public API change.

It does not change routing behavior.

It does not make the node remote.

It does not make the node dynamic.

If accepted, future implementation work may make the static local declaration
more explicit in code while preserving the same behavior. Such work should not
introduce file-based configuration, discovery, registration, runtime probing, or
adapter-owned node metadata without a separate accepted RFC.

## Open questions

- When should the project introduce file-based local node configuration?
- Should future local configuration support multiple declared local nodes, or
  only one local node?
- How should future adapter-derived inventory be represented without making
  runtime details part of the core node model?
- What is the smallest useful boundary before Phase 3 introduces two machines?

## Decision

Pending.
