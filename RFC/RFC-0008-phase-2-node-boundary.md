# RFC-0008: Phase 2 Node Boundary

Status: Draft

Date: 2026-07-04

Author: frian

## Summary

This RFC defines the node boundary for Home AI Cluster after Phase 1.

Phase 1 introduced a static local node as an internal routing concept.

This RFC clarifies what a node boundary means before Home AI Cluster introduces real distributed behavior.

The goal is to keep the architecture honest while still allowing the implementation to remain local and simple.

In other words:

```text
Fake in distribution, but not fake in architecture.
```

## Problem

Home AI Cluster currently runs as a single local process.

Inside that process, requests already move through distinct conceptual boundaries:

```text
API request
  -> orchestrator
  -> router
  -> static local node
  -> runtime adapter
  -> normalized result
```

The static local node is not a real distributed node.

It does not have its own process, network endpoint, lifecycle, registry protocol, discovery mechanism, or runtime supervision.

That is intentional for Phase 1.

However, before moving further, Home AI Cluster needs to make the node boundary explicit so future changes do not blur the distinction between:

- the cluster-facing orchestration layer;
- node descriptions;
- runtime adapters;
- machine-specific execution details;
- future remote node behavior.

Without an explicit node boundary, future work could accidentally make the orchestrator depend on local runtime details, machine names, Ollama behavior, or implementation shortcuts that would make later distribution harder.

## Goals

This RFC aims to:

- define what a node boundary means conceptually;
- preserve the existing Phase 1 implementation shape;
- avoid introducing real distributed behavior too early;
- keep routing capability-centered;
- keep runtime-specific details behind runtime adapters;
- make future node-related changes easier to review;
- clarify what is allowed before real multi-machine support exists.

## Non-goals

This RFC does not introduce:

- real distributed nodes;
- node discovery;
- node registration;
- node-to-node communication;
- a node daemon;
- a node HTTP API;
- remote execution;
- fallback;
- retries;
- health polling;
- runtime supervision;
- runtime auto-start;
- persistent node storage;
- dashboard or UI;
- Docker;
- Kubernetes;
- API compatibility layers;
- distributed model execution.

Those features require separate RFCs if they are introduced later.

## Decision

Home AI Cluster will treat a node as an explicit architectural boundary, even while Phase 2 may still run in a single local process.

A node is the cluster-visible boundary around one execution environment.

For now, a node remains represented by a static description.

The orchestrator and router may use declared capabilities, availability, and adapter names for the current minimal routing behavior.

Node health remains descriptive state and must not drive routing unless a later RFC allows it.

They must not depend on runtime-specific details hidden behind adapters.

A runtime adapter remains responsible for speaking to a concrete runtime such as Ollama.

A node boundary must not imply that the node is already remote, independently running, discoverable, supervised, or reachable over the network.

## Minimal node boundary

A node boundary separates these concerns.

### Cluster-facing concerns

The cluster may know:

- node identity;
- node display name;
- node availability state;
- node health description;
- declared capabilities;
- declared adapter names.

### Runtime-facing concerns

Runtime-specific details remain behind adapters, including:

- runtime endpoint URLs;
- model names;
- runtime-specific errors;
- runtime-specific request formats;
- runtime availability checks;
- runtime process state.

### Out-of-scope concerns

The node boundary does not yet include:

- network address;
- process management;
- runtime supervision;
- discovery metadata;
- persistent configuration;
- scheduling policy;
- load information;
- cost information;
- performance metrics.

## Current implementation expectation

The current implementation may continue to use one static local node in one process.

That is acceptable.

The important boundary is architectural, not operational.

The implementation may remain:

```text
single process
  -> static local node description
  -> local runtime adapter
```

The implementation must not pretend to provide:

```text
remote node process
node discovery
node registration
node health polling
runtime supervision
fallback routing
```

## Routing implications

Routing remains capability-centered.

The router may continue using the current minimal selection behavior, such as:

- requested capability;
- static node availability;
- node adapter list;
- adapter capabilities.

Current registration order may remain an implementation detail, but this RFC does not define a long-term scheduling policy.

The router must not start doing the following as a consequence of this RFC:

- filtering by node health;
- probing adapter health before selection;
- retrying on another node;
- falling back to another adapter;
- starting runtimes;
- polling nodes;
- contacting remote machines.

Those behaviors require separate RFCs.

## API implications

This RFC does not change the public API.

The `/v1/chat` endpoint remains a custom Home AI Cluster endpoint.

The public API does not expose node details, routing explanations, runtime internals, or health metadata by default.

Any future public node, routing, or explanation surface requires a separate RFC.

## Privacy implications

The node boundary must preserve the privacy-first default.

The cluster must not log prompts or responses by default.

Node descriptions must not require exposing machine-specific private information.

Runtime-specific failures must remain normalized before reaching public API responses.

Future node metadata must be reviewed carefully before it becomes public, persistent, or transmitted over a network.

## Engine independence implications

The node boundary must not be shaped around Ollama.

Ollama remains one runtime adapter.

The node model must remain independent of any specific engine, model naming scheme, endpoint format, or runtime lifecycle.

## Consequences

This RFC makes the node boundary explicit without implementing distribution.

This allows future work to improve the architecture in small steps while keeping the system local-first and simple.

It also creates a review point for future proposals that may add:

- remote nodes;
- node discovery;
- node registration;
- node APIs;
- runtime supervision;
- health polling;
- fallback routing.

Those proposals must explain how they respect this boundary.

## Alternatives considered

### Keep the node boundary implicit

This would avoid adding another RFC.

However, the project is now close to the point where future work may naturally want to introduce node behavior.

Leaving the boundary implicit increases the risk of accidental coupling between orchestration, nodes, and runtime adapters.

### Introduce real remote nodes now

This would move too quickly.

The current project principles prefer boring solutions first and architecture before implementation.

Real remote nodes would introduce networking, failure modes, configuration, security, and lifecycle questions that are not needed yet.

### Add a node HTTP API now

This would be premature.

A node API may be useful later, but this RFC only defines the architectural boundary.

The transport mechanism should be decided separately.

### Add discovery now

Discovery is explicitly out of scope.

A static local node description remains enough for the next step.

## Compatibility with accepted RFCs

This RFC builds on:

- RFC-0001: Minimal system shape;
- RFC-0002: Phase 1 implementation stack;
- RFC-0003: Runtime adapter interface;
- RFC-0004: Minimal node model;
- RFC-0005: Routing explanation boundary;
- RFC-0006: Node health boundary;
- RFC-0007: Runtime availability boundary.

It does not replace or contradict those RFCs.

## Open questions

- Should Phase 2 introduce a separate in-process `NodeClient` or equivalent boundary object?
- Should node descriptions remain fully static during Phase 2?
- Should a future RFC define a node protocol before any remote implementation exists?
- What is the smallest useful implementation step after this boundary is accepted?
- When should a node become something more than a static description?

## Acceptance criteria

This RFC is accepted when the project agrees that:

- node is an explicit architectural boundary;
- the current implementation may remain single-process and local;
- real distribution is still out of scope;
- runtime-specific details remain behind adapters;
- future node behavior requires explicit RFCs.
