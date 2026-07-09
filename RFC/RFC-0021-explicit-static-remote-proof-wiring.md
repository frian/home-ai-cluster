# RFC-0021: Explicit Static Remote Proof Wiring

Status: Draft

Date: 2026-07-09

Author: frian

## Summary

This RFC proposes the smallest implementation wiring for the RFC-0020 Phase 3
proof:

```text
One endpoint. Two machines. One routed request.
```

RFC-0020 allows `/v1/chat` to route to one manually declared remote node only
when remote routing is explicitly enabled by caller-owned setup or
configuration.

This RFC proposes an explicit caller-owned process wiring mode for that proof.
The wiring may assemble, in memory, the local registries, one manually declared
remote node, an explicit `RemoteTransport`, candidate discovery and
composition, explicit candidate selection, and selected candidate
orchestration.

Without that explicit setup, `/v1/chat` remains local-only.

This RFC does not implement anything.

## Problem

Phase 2 prepared the explicit opt-in seams needed for declared remote
eligibility, candidate discovery, candidate composition, candidate selection,
selected candidate orchestration, and execution boundaries.

RFC-0020 accepts the first Phase 3 proof as a minimal static two-machine proof,
and allows `/v1/chat` to be the endpoint for that proof when remote routing is
explicitly enabled.

The next architectural question is narrower than production configuration or
dynamic membership:

```text
How may /v1/chat be wired for the first proof without introducing premature
infrastructure?
```

Without a small wiring decision, the first proof could accidentally introduce a
configuration format, persistence, dynamic discovery, registration,
daemon-owned registry state, fallback, health probing, scheduling, or implicit
remote behavior.

## Goals

This RFC should:

- define the smallest wiring shape for the RFC-0020 proof;
- keep the proof setup caller-owned;
- keep the proof setup static and in memory;
- allow `/v1/chat` to use proof wiring only when explicitly enabled;
- keep `/v1/chat` local-only without that explicit setup;
- reuse the prepared Phase 2 seams;
- avoid introducing a new routing policy;
- keep the remote node manually declared;
- require an explicit `RemoteTransport`;
- keep request movement across the remote boundary explicit;
- preserve local-first and privacy-first defaults.

## Non-goals

This RFC does not:

- implement code;
- introduce config file loading;
- introduce persistence;
- introduce dynamic discovery;
- introduce registration;
- introduce daemon-owned registry state;
- introduce retries;
- introduce fallback after remote failure;
- introduce health probing;
- introduce scoring or scheduling;
- introduce Docker or Kubernetes;
- introduce a dashboard;
- introduce a database;
- introduce an OpenAI-compatible API;
- introduce cloud execution;
- contact unknown or undeclared machines;
- make remote routing default behavior;
- make remote execution default behavior;
- decide a long-term configuration format;
- decide dynamic node membership;
- decide production deployment.

## Proposal

Home AI Cluster should define an explicit static remote proof wiring mode for
the first Phase 3 proof.

The wiring is caller-owned. It may be constructed by tests or by an explicit
application factory or process entrypoint. It is not global discovery, not
registration, not persistence, and not daemon-owned state.

When enabled, the proof wiring may assemble, in memory:

- a local node registry;
- a local adapter registry;
- one manually declared remote node;
- a remote declaration registry containing that one declared remote node;
- an explicit `RemoteTransport` for that declared remote node;
- explicit routing candidate discovery and composition;
- an explicit candidate selection mode;
- selected candidate orchestration.

When not enabled, `/v1/chat` remains on the existing local-only path:

```text
/v1/chat
  -> active orchestrate_request(...)
  -> route_request(...)
  -> local adapter execution
```

This is wiring, not a new routing policy. The proof wiring chooses an explicit
candidate selection mode as part of caller-owned setup. It does not introduce
scoring, scheduling, fallback, retries, or health-aware routing.

## Minimal Wiring Shape

The minimal proof wiring shape is:

```text
explicit process setup
  -> local node registry
  -> local adapter registry
  -> one manually declared remote node
  -> explicit RemoteTransport
  -> /v1/chat handler
  -> candidate discovery and composition
  -> explicit candidate selection mode
  -> selected candidate orchestration
  -> local execution boundary or declared remote execution boundary
```

The setup remains static and in memory for the first proof.

The remote node is manually declared. The declaration is the trust and
membership boundary. The transport address is transport metadata, not node
identity, not discovery, not registration, and not proof of trust.

The `RemoteTransport` is provided explicitly by the setup. Request contents may
cross the remote boundary only when the selected candidate is the declared
remote candidate and the caller-owned setup provided the transport.

The setup may be assembled in tests to prove the behavior. It may also be
assembled by an explicit application factory or process entrypoint. This RFC
does not decide the final shape of that factory or entrypoint.

## /v1/chat Integration Boundary

`/v1/chat` may use the static remote proof wiring only when explicitly enabled
by process setup.

Without that setup, `/v1/chat` must remain local-only and continue to use the
existing active orchestration path.

When proof wiring is enabled, `/v1/chat` may:

1. normalize the incoming request;
2. use caller-owned local and remote setup;
3. compose local and declared remote candidates;
4. select a candidate using the explicit proof selection mode;
5. execute the selected candidate through selected candidate orchestration;
6. return the normalized result or explicit failure.

This integration must remain visible in code. A reviewer should be able to see
where remote routing was enabled, which manually declared node was allowed, and
which transport was provided.

This RFC does not require `/v1/chat` to use proof wiring by default. It does
not make remote routing implicit.

## Privacy and Trust Boundaries

The proof wiring remains local-first and privacy-first.

Unknown or undeclared machines must never be contacted.

The setup may contact only the manually declared remote node for which the
caller-owned setup provided an explicit `RemoteTransport`.

Request contents may cross the remote boundary only because:

1. remote proof wiring was explicitly enabled;
2. the remote node was manually declared;
3. the remote transport was explicitly provided;
4. the selected candidate was the declared remote candidate.

Reachability is not trust. A transport address is not cluster membership.

Cloud execution is not part of this wiring.

## Failure Behavior

Failure remains explicit.

If the selected candidate is remote and the remote transport fails, the
declared remote node cannot execute the request, the response is invalid, or
another remote execution failure occurs, the request should fail through the
explicit failure path chosen by implementation.

No fallback occurs after selected remote failure.

No retry occurs after selected remote failure.

The proof wiring must not silently try another candidate, another remote node,
another transport, another adapter, or another endpoint.

Fallback, retries, timeout policy, and richer error mapping remain separate
decisions.

## Rationale

The project needs the first Phase 3 proof to become real without becoming
larger than the proof requires.

An explicit caller-owned wiring mode keeps the proof small:

- it uses the existing `/v1/chat` endpoint allowed by RFC-0020;
- it reuses the Phase 2 preparation seams;
- it keeps remote membership manual and visible;
- it keeps request movement behind explicit `RemoteTransport`;
- it avoids dynamic discovery, registration, persistence, fallback, health
  probing, scoring, and scheduling.

This preserves the core idea:

```text
The user talks to the cluster, never to a machine.
```

It also preserves the trust boundary. The cluster does not contact unknown
machines. The proof does not infer trust from reachability or addresses.

## Alternatives Considered

### Add config file loading first

This is rejected for this RFC. Config loading may become useful, but the first
proof can be wired explicitly in memory. A long-term configuration format is a
separate decision.

### Add dynamic discovery first

This is rejected. Dynamic discovery is not required for the first static
two-machine proof and would introduce a separate trust and membership problem.

### Add registration first

This is rejected. Registration changes node ownership, lifecycle, and trust.
The first proof can use one manually declared remote node.

### Use daemon-owned registry state

This is rejected. Daemon-owned registry state would introduce lifecycle and
ownership decisions beyond the first proof.

### Keep `/v1/chat` local-only and use only a separate endpoint

This is rejected for the first proof direction accepted by RFC-0020. The proof
is one endpoint, two machines, one routed request. `/v1/chat` may be that
endpoint when explicitly enabled.

### Add fallback after remote failure

This is rejected. Fallback would introduce routing policy beyond wiring and
would make the first proof harder to explain.

### Add health probing, scoring, or scheduling

This is rejected. The first proof needs explicit static wiring, not a scheduler
or health-aware router.

## Trade-offs

Explicit in-memory wiring is less convenient than config files or discovery,
but it keeps the first proof understandable and reviewable.

Allowing `/v1/chat` to use proof wiring touches the active public endpoint, but
only when explicitly enabled by caller-owned setup. Without that setup,
`/v1/chat` remains local-only.

Not adding fallback means remote failures are visible. That is less polished,
but it keeps the first remote proof honest.

This RFC may require a later implementation to introduce a small application
factory or process entrypoint seam. That seam should remain explicit and should
not become a hidden configuration system.

## Impact

If accepted, this RFC would affect future implementation of the RFC-0020 proof.

It would allow a future implementation to add explicit static process wiring
that lets `/v1/chat` route to one manually declared remote node when enabled by
caller-owned setup.

It would not require code changes by itself.

It would not activate remote routing by default.

It would not activate remote execution by default.

It would not decide config loading, persistence, dynamic discovery,
registration, daemon-owned registry state, retries, fallback, health probing,
scoring, scheduling, Docker, Kubernetes, dashboard, database,
OpenAI-compatible API, cloud execution, or production deployment.

## Open Questions

- Should the first implementation expose the proof wiring through a new
  application factory argument or a separate explicit process entrypoint?
- Which explicit candidate selection mode should the first proof use?
- Should the first proof prefer local when both candidates exist, or use a
  declared-remote-only setup to make the remote proof obvious?
- What exact error mapping should `/v1/chat` use for remote transport failure?
- What minimal routing explanation should be returned or logged without
  logging prompt or response contents?

## Decision

Pending.
