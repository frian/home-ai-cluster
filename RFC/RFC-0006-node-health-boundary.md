# RFC-0006: Node Health Boundary

Status: Accepted

Date: 2026-07-02

Author: frian

## Summary

Home AI Cluster may describe node health internally, but Phase 1 must not turn health into active orchestration policy.

For Phase 1, node health is static descriptive state. Runtime availability is still handled at adapter call time.

No health polling, heartbeat, fallback, monitoring, discovery, or health-based routing is introduced by this RFC.

## Problem

Home AI Cluster now has a minimal node model and a runtime adapter boundary.

The current code can represent node health and adapter availability, and runtime failures can be reported as unavailable adapters.

Without a clear boundary, future changes may blur several different ideas:

* whether a node exists in the registry;
* whether a node is available for routing;
* whether a runtime adapter is reachable right now;
* whether the cluster should actively poll health;
* whether failed requests should trigger fallback;
* whether health should influence routing policy.

These are related, but they are not the same architectural decision.

If we do nothing, small implementation changes may accidentally introduce monitoring, retries, fallback, discovery, or health-based routing before those behaviors have been designed.

## Goals

* Define what node health means in Phase 1.
* Keep node health descriptive and internal for now.
* Keep runtime failures handled at adapter call time.
* Avoid introducing active health orchestration too early.
* Preserve the minimal static local node architecture.
* Make future health-related decisions explicit RFC topics.

## Non-goals

This RFC does not define:

* health polling;
* heartbeats;
* node agents;
* network discovery;
* registration;
* monitoring;
* telemetry;
* dashboards;
* persistence;
* retries;
* fallback policy;
* health-based routing;
* load balancing;
* scoring;
* scheduling;
* node lifecycle management;
* runtime process supervision.

## Proposal

For Phase 1, node health is internal descriptive state attached to a known node.

The static local node may report minimal health such as:

* `healthy: true`;
* optional `reason` when health is not healthy or not known.

Node health does not actively drive routing policy yet.

Routing continues to use the current minimal behavior:

* select from known available nodes;
* match the requested capability;
* select the first matching adapter declared by the node;
* call the selected runtime adapter.

Runtime availability remains an adapter concern at call time.

If the selected runtime adapter cannot reach its runtime, the request fails through the existing runtime-unavailable path.

This RFC does not introduce preflight health checks, background checks, polling, heartbeat state, retries, fallback, or alternative node selection.

Any future change that makes health influence routing, fallback, monitoring, discovery, or node lifecycle requires a separate RFC.

## Rationale

This keeps Phase 1 aligned with the current project goal:

> fake in distribution, but not fake in architecture.

The architecture can already represent a node and its health without pretending to operate a real distributed system.

Keeping health descriptive avoids premature orchestration complexity while preserving a clear place for future health semantics.

It also keeps the implementation local-first and privacy-first. Health state should not become telemetry, persistent monitoring, or hidden logging.

## Alternatives considered

### Health-based routing now

The router could skip unhealthy nodes or prefer healthier ones.

This is too early. It would introduce routing policy before the project has multiple real nodes or a health update mechanism.

### Adapter preflight checks before every request

The orchestrator could check adapter health before calling it.

This adds extra runtime behavior and may still race with the actual request. It also starts to blur adapter availability, node health, and routing policy.

### Background health polling

The cluster could periodically poll runtimes and nodes.

This would introduce scheduling, monitoring, state freshness, and failure semantics too early for Phase 1.

### Fallback on runtime failure

If one adapter fails, the cluster could try another.

Fallback is a routing policy decision and may affect user expectations, privacy, reproducibility, and latency. It needs a separate RFC.

### No health field at all

Removing health would avoid confusion, but the minimal node model already includes health as useful descriptive state.

Keeping it static and internal is simpler than removing it and reintroducing it later.

## Trade-offs

This RFC makes the current system simpler and safer by avoiding premature orchestration behavior.

It also means Phase 1 may route to a node whose runtime fails at call time.

That trade-off is acceptable because the current architecture has one static local node and one runtime adapter. The existing runtime-unavailable response is enough for this phase.

## Impact

This RFC affects node and routing architecture.

It does not require a public API change.

It does not require code changes by itself.

Future work involving active health checks, health-based routing, fallback, monitoring, discovery, or node lifecycle management must reference this RFC and define a new boundary.

## Open questions

* What health states are needed once there are real remote nodes?
* Should adapter health and node health remain separate concepts long term?
* Should health freshness be represented explicitly later?
* Should a user be able to ask why a node is unavailable without exposing private topology by default?
* What is the smallest useful health behavior for the first two-machine proof?

## Decision

Accepted.

For Phase 1, node health is internal descriptive state.

Runtime availability remains handled at adapter call time.

Node health does not drive routing, fallback, polling, monitoring, discovery, or runtime supervision.

Any future active health behavior requires a separate RFC.
