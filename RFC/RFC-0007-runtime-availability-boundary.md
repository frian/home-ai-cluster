# RFC-0007: Runtime Availability Boundary

Status: Draft

Date: 2026-07-02

Author: frian

## Summary

Home AI Cluster runtime availability is detected at runtime adapter call time in Phase 1.

When a selected runtime adapter cannot reach or use its runtime, the adapter normalizes that failure as a runtime-unavailable error.

The public API may map that normalized error to an unavailable response, but Phase 1 does not introduce retries, fallback, preflight checks, circuit breakers, runtime supervision, or health-based routing.

## Problem

Home AI Cluster separates public API handling, core routing, and runtime adapters.

The first real runtime adapter is Ollama. Ollama may be stopped, unreachable, misconfigured, or otherwise unable to answer a request.

The project already needs a boring way to handle that failure without coupling the public API to Ollama details.

At the same time, runtime availability can easily expand into larger orchestration behavior:

* preflight checks before routing;
* retries;
* fallback to another adapter;
* circuit breakers;
* background health checks;
* runtime supervision;
* automatic runtime startup;
* model download or runtime management.

Those are separate architectural decisions.

If we do nothing, adapter failure handling may grow into orchestration policy without an explicit RFC.

## Goals

* Define the Phase 1 boundary for runtime availability.
* Keep runtime-specific failures inside runtime adapters.
* Normalize unavailable runtime failures before they reach the public API layer.
* Keep the public API independent from a specific runtime such as Ollama.
* Avoid retries, fallback, preflight checks, and runtime supervision for now.
* Keep future active availability behavior behind explicit RFCs.

## Non-goals

This RFC does not define:

* retries;
* fallback policy;
* adapter selection based on runtime health;
* circuit breakers;
* preflight checks;
* background health polling;
* runtime supervision;
* automatic runtime startup;
* automatic model download;
* runtime installation;
* runtime configuration discovery;
* persistent error history;
* telemetry;
* dashboards;
* distributed runtime management.

## Proposal

For Phase 1, runtime availability is checked only when the selected runtime adapter is called.

A runtime adapter is responsible for translating runtime-specific connection or availability failures into a normalized runtime-unavailable error.

The core and API layers should not expose runtime-specific implementation details such as Ollama connection errors.

The public `/v1/chat` endpoint may map the normalized runtime-unavailable error to HTTP 503.

This RFC does not require the cluster to check runtime availability before routing.

This RFC does not allow the router to change selection based on live runtime availability.

This RFC does not introduce fallback to another adapter when the selected adapter fails.

This RFC does not introduce runtime process supervision or automatic recovery.

Any future change that adds retries, fallback, circuit breakers, preflight checks, runtime supervision, automatic startup, or health-based adapter selection requires a separate RFC.

## Rationale

This keeps the Phase 1 behavior simple and explicit.

Runtime adapters own runtime-specific details. The public API sees only normalized project-level failures.

This preserves engine independence: the API does not need to know whether the failed runtime was Ollama or something else.

It also preserves boring solutions first. A failed local runtime results in a clear unavailable response instead of hidden retry or fallback behavior.

## Alternatives considered

### Preflight runtime health checks

The orchestrator could check adapter health before making a request.

This adds complexity and can still race with the actual request. It also starts turning availability into routing policy.

### Retry failed runtime calls

Retries may help transient failures, but they also affect latency, user expectations, and failure semantics.

Retry behavior should be decided separately.

### Fallback to another adapter

Fallback may be useful later, especially with multiple runtimes.

For Phase 1, fallback would be premature because there is one local runtime adapter and no accepted fallback policy.

### Surface runtime-specific errors directly

The API could return raw Ollama or HTTP client errors.

This would leak implementation details and weaken engine independence.

### Supervise runtime processes

The cluster could start or restart runtimes automatically.

That would introduce lifecycle management and runtime ownership, which are outside Phase 1.

## Trade-offs

This RFC makes runtime failure handling simple and predictable.

It also means the cluster fails the request when the selected runtime is unavailable, instead of trying to recover automatically.

That trade-off is acceptable for Phase 1 because the goal is a minimal local vertical slice, not runtime orchestration.

## Impact

This RFC affects runtime adapter and API error boundaries.

It does not require a public API shape change.

It does not require code changes by itself.

Future work that changes runtime availability behavior must reference this RFC and define the new boundary explicitly.

## Open questions

* Should future runtime errors distinguish unavailable runtime, invalid runtime response, timeout, and unsupported model?
* Should retry behavior be allowed for idempotent requests later?
* How should fallback interact with privacy, reproducibility, and user intent?
* Should runtime availability ever be visible to users by default?
* What is the smallest useful availability behavior for the first two-machine proof?

## Decision

Pending.
