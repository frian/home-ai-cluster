# RFC-0011: Minimal Agent Shape

Status: Draft

Date: 2026-07-05

Author: frian

## Summary

This RFC defines the minimal Phase 2 meaning of "agent" before Home AI Cluster
introduces any agent abstraction, process, protocol, lifecycle, or new source of
truth in code.

For Phase 2, an agent is the minimal local boundary responsible for representing
one execution environment to the cluster through an explicit static node
announcement.

It is not yet a daemon, protocol endpoint, discovery participant, runtime
supervisor, or configuration system.

This RFC does not require a separate agent object in code. Phase 2 may continue
using the current explicit in-process static local node declaration.

## Problem

Home AI Cluster's roadmap names Phase 2 as the agent and node model phase.
Accepted Phase 2 RFCs have already defined the node model, the node boundary,
the static local node announcement, node health, runtime availability, and
static node availability.

Those decisions intentionally keep the implementation:

- single-process;
- local;
- static;
- non-distributed.

They also explicitly avoid an agent process, node discovery, registration,
node HTTP API, runtime probing, runtime supervision, health polling, fallback,
and configuration files.

However, the word "agent" still needs a small architectural meaning before
implementation work introduces an agent abstraction or related boundary.

Without a minimal definition, future code could accidentally make "agent" mean:

- a daemon;
- a node HTTP server;
- a discovery client;
- a registration participant;
- a runtime supervisor;
- a configuration loader;
- a source of runtime-derived node metadata.

Those are separate architectural decisions.

The project needs a boring boundary that says what an agent means in Phase 2
without expanding the current system's authority or behavior.

## Goals

This RFC should:

- define the minimal Phase 2 meaning of "agent";
- keep the current implementation single-process, local, static, and
  non-distributed;
- preserve the existing static local node announcement source of truth;
- keep node descriptions cluster-facing;
- keep runtime-specific behavior behind runtime adapters;
- prevent runtime adapters from owning node identity or node metadata;
- keep routing behavior unchanged;
- keep node health descriptive only;
- keep static node availability as routing eligibility only;
- keep runtime availability as adapter-call-time behavior;
- make future agent-related implementation easier to review.

## Non-goals

This RFC does not introduce:

- distributed behavior;
- discovery;
- registration;
- a node HTTP API;
- a daemon or process lifecycle;
- runtime probing;
- runtime supervision or auto-start;
- health polling;
- fallback or retries;
- a config file format;
- model inventory;
- model placement or download automation;
- public API changes;
- prompt or response logging;
- adapter-owned node metadata.

Future work in any of those areas requires a separate RFC.

This RFC also does not require adding a concrete `Agent` class, interface,
module, process, or service in the current implementation.

## Proposal

For Phase 2, Home AI Cluster should define an agent as:

> The minimal local boundary responsible for representing one execution
> environment to the cluster through an explicit static node announcement.

This definition is intentionally small.

It separates three concepts:

- a node is the cluster-visible description;
- a runtime adapter talks to a concrete runtime;
- an agent is the future-facing local owner of the node announcement boundary.

The agent boundary says:

```text
This execution environment is represented to the cluster by this static node
announcement.
```

It does not say:

```text
This execution environment has a daemon.
This node is reachable over HTTP.
This node was discovered.
This node registered itself.
This runtime is live right now.
This runtime should be started or supervised.
This node metadata came from a config file.
```

### Relationship to nodes

A node remains the cluster-visible description of an execution environment.

The node description contains the cluster-facing metadata already defined by
accepted RFCs:

- node identity;
- display name;
- static availability;
- descriptive health;
- declared capabilities;
- declared adapter names.

The node description is what the orchestrator and router may reason about.

The agent is not a replacement for the node description. It is the local
ownership boundary that may later become responsible for producing or serving
that description, once later RFCs define how that should happen.

For Phase 2, the node announcement remains static and explicit.

### Relationship to runtime adapters

A runtime adapter talks to a runtime.

Runtime adapters remain responsible for runtime-specific behavior, including:

- runtime endpoint URLs;
- runtime request formats;
- runtime-specific failures;
- runtime availability at adapter call time;
- model names needed to execute a request.

Runtime adapters must not own node identity or node metadata.

An adapter may expose its own name, capabilities, health, and execution methods
through the runtime adapter boundary. That does not make the adapter the owner
of the node announcement.

The node announcement declares which adapter names the cluster is allowed to
consider for a node. The adapter implements the runtime-specific behavior needed
to satisfy a request.

Those remain separate responsibilities.

### Current source of truth

The current Phase 2 source of truth remains the explicit in-process static local
node declaration.

This RFC does not move that source of truth into:

- runtime adapters;
- live runtime probing;
- machine inspection;
- discovery;
- registration;
- a daemon;
- a config file.

Phase 2 may continue without a separate agent object in code.

If implementation later adds an in-process object named `Agent`, or a similar
boundary, it must preserve the decisions in this RFC unless another accepted RFC
changes them.

Such an object would be allowed only to make the local ownership boundary more
explicit. It must not introduce process lifecycle, transport, discovery,
registration, runtime probing, runtime supervision, configuration loading, or
routing changes by implication.

### Routing behavior

Routing behavior remains unchanged.

The router may continue to use the current minimal behavior:

- match the requested capability;
- consider static node availability;
- use declared adapter names;
- select a matching registered adapter.

This RFC does not introduce new routing policy, scheduling, scoring, retries, or
fallback.

Node health remains descriptive only and does not drive routing.

Static node availability remains routing eligibility only.

Runtime availability remains adapter-call-time behavior.

### Privacy and local-first boundaries

The minimal agent shape must preserve the project's local-first and
privacy-first defaults.

The agent boundary must not require prompt logging, response logging, model
inventory, process inspection, environment inspection, user file inspection, or
network scans.

The safest default remains:

> Do not collect what is not needed.

For Phase 2, the agent boundary should only explain ownership of the static node
announcement. It should not cause the system to collect more information.

## Rationale

This RFC keeps the architecture honest without making the implementation more
dynamic than it is.

The project already has a static node description, a runtime adapter boundary,
and static routing behavior. Defining an agent as the future-facing owner of the
node announcement boundary gives the roadmap term "agent" a concrete meaning
without introducing a daemon, protocol, lifecycle, discovery, or supervision.

This preserves the Phase 2 rule:

```text
single process
  -> static local node announcement
  -> local runtime adapter
```

It also protects engine independence. Runtime adapters continue to talk to
runtimes, but they do not decide who the node is or what metadata the cluster is
allowed to see.

The boundary remains capability-centered. The cluster still reasons about
declared capabilities and adapter names, not runtime brand names, model
inventory, machine inspection, or live runtime state.

The proposal is deliberately boring. It names a responsibility before the code
needs to grow an abstraction for it.

## Alternatives considered

### Do not define agent yet

The project could continue with only node and adapter concepts.

That would keep the current implementation simple, but it leaves the roadmap's
agent language undefined. Future implementation could then introduce an agent
object, process, or protocol as an implementation detail rather than an
architectural decision.

### Define an agent as a daemon now

An agent could mean an independently running process on each machine.

That may become useful later, but it would introduce lifecycle, supervision,
transport, security, configuration, and failure-mode questions before the
project needs them.

### Define an agent as a node HTTP API now

An agent could mean an HTTP endpoint that serves node metadata or accepts work.

That would prematurely decide transport and protocol boundaries. Phase 2 does
not need a node HTTP API.

### Let runtime adapters own node announcements

Adapters could build or expose the node announcement.

That would blur node identity, runtime behavior, adapter capabilities, and live
runtime state. It would also make the core more likely to inherit
runtime-specific assumptions.

### Define file-based agent configuration now

A config file may eventually become the right way for users to declare local
nodes or agent behavior.

Defining that format now would create compatibility and user-facing semantics
before they are needed. The current explicit in-process declaration remains
enough for Phase 2.

## Trade-offs

This RFC gives "agent" a clear Phase 2 meaning without adding new behavior.

It makes future agent-related work easier to review because proposals can be
checked against a small boundary:

- does this only make local node announcement ownership clearer?
- or does it introduce process, protocol, discovery, lifecycle, supervision,
  configuration, or routing behavior?

The trade-off is that the definition may feel almost too small. It does not
make the system more capable by itself.

That is acceptable because Phase 2 is still preparing the architecture for the
later two-machine proof. The goal is to prevent hidden architecture, not to
simulate distribution.

## Impact

This RFC affects Phase 2 architecture vocabulary and future implementation
review.

It does not require code changes.

It does not require public API changes.

It does not change routing behavior.

It does not change node health, static node availability, or runtime
availability semantics.

It does not change the current source of truth for the static local node
announcement.

Future implementation may continue without a separate agent object in code. If
future work introduces one, it should preserve this boundary or first propose a
separate RFC that changes it.

## Open questions

- When should the project introduce a concrete in-process agent object, if ever?
- What is the smallest useful agent behavior before the first two-machine
  proof?
- Should a future remote agent protocol be designed before or alongside the
  first two-machine implementation?
- When should the source of truth move from in-process declaration to a
  user-controlled configuration format?
- How should future agent behavior preserve local-first and privacy-first
  defaults when node metadata becomes network-visible?

## Decision

Pending.
