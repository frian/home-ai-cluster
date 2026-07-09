# RFC-0020: Minimal Static Two-Machine Proof

Status: Accepted

Date: 2026-07-09

Author: frian

## Summary

This RFC proposes the smallest acceptable Phase 3 proof for:

```text
One endpoint. Two machines. One routed request.
```

The proof should remain static, explicit, and boring. It should use one
manually declared remote node and an explicit `RemoteTransport`.

For the first Phase 3 proof, `/v1/chat` may route to one manually declared
remote node only when remote routing is explicitly enabled by caller-owned
setup or configuration. Remote routing and remote execution must not become
implicit default behavior.

This RFC does not implement anything.

## Problem

RFC-0019 closes Phase 2 as a prepared architecture checkpoint, not active
distributed behavior. It also requires a separate accepted RFC before Phase 3
introduces real two-machine active behavior.

The project now has a prepared opt-in chain:

```text
declared remote eligibility
  -> declared remote routing candidate discovery
  -> candidate composition beside local routing candidates
  -> explicit opt-in candidate selection
  -> explicit opt-in selected candidate orchestration
  -> existing execution boundaries
```

The active path remains:

```text
/v1/chat
  -> active orchestrate_request(...)
  -> route_request(...)
  -> local adapter execution
```

The next question is not how to build a production cluster. The next question
is smaller:

```text
What is the smallest real two-machine proof that preserves explicit trust,
privacy, and local-first defaults?
```

Without a narrow RFC, Phase 3 could accidentally introduce dynamic discovery,
registration, persistence, fallback, scheduling, or implicit remote execution
while trying to prove only one endpoint, two machines, and one routed request.

## Goals

This RFC should:

- define the smallest acceptable Phase 3 two-machine proof;
- keep the proof static and explicit;
- use one manually declared remote node;
- require an explicit remote transport boundary;
- decide whether `/v1/chat` may be the one endpoint for the first proof;
- preserve local-first and privacy-first defaults;
- ensure request contents cross a remote boundary only when setup explicitly
  allows the declared remote node;
- ensure unknown or undeclared nodes are never contacted;
- keep the goal focused on one visible routed request;
- avoid production-cluster assumptions.

## Non-goals

This RFC does not:

- implement code;
- decide dynamic discovery;
- decide registration;
- decide persistence;
- introduce daemon-owned registry state;
- introduce retries;
- introduce fallback after remote failure;
- introduce health probing;
- introduce scoring or scheduling;
- introduce Docker or Kubernetes;
- introduce a dashboard;
- introduce a database;
- introduce an OpenAI-compatible API;
- introduce automatic trust of unknown machines;
- make cloud execution part of the proof;
- make remote execution implicit or magic;
- define a production cluster.

## Proposal

Home AI Cluster should define the first Phase 3 proof as a minimal static
two-machine proof.

The proof should have:

- one orchestrator process exposing `/v1/chat`;
- one local node that remains available to the orchestrator;
- one manually declared remote node;
- one explicit `RemoteTransport` for the declared remote node;
- one request routed through the cluster to either the local node or the
  manually declared remote node;
- one visible explanation of which node handled the request.

For the first proof, `/v1/chat` may be the one endpoint.

`/v1/chat` may route to the manually declared remote node only when the process
has been explicitly set up to allow that remote node. The setup must be
caller-owned and explicit. It must not discover, register, persist, or infer
remote nodes.

The first proof should remain static:

- no dynamic discovery;
- no registration;
- no persistence;
- no daemon-owned registry state;
- no retries;
- no fallback;
- no health probing;
- no scoring;
- no scheduling.

Remote routing should be active only inside this explicitly enabled proof
setup. It should not become an implicit default merely because a remote
transport or declaration exists.

## Minimal Static Proof Shape

The proof shape is:

```text
client
  -> /v1/chat
  -> normalized ClusterRequest
  -> explicit static local and remote setup
  -> candidate preparation
  -> explicit selection policy for the proof
  -> selected candidate orchestration
  -> local adapter or explicit RemoteTransport
  -> normalized ClusterResult
```

The remote side is manually declared. The declaration is the trust and
membership boundary for the proof. A transport address is transport metadata,
not node identity, discovery, registration, or proof of trust.

The allowed remote transport is explicit. Request contents may cross the remote
transport boundary only because the setup explicitly allows that declared node
and provides the remote transport.

Unknown or undeclared machines must never be contacted.

The proof should route one request visibly. It does not need to solve general
fleet management, placement, scheduling, fallback, health probing, persistence,
or dynamic membership.

## /v1/chat Behavior

For the first Phase 3 proof, `/v1/chat` may become the one endpoint that can
route to the manually declared remote node.

That behavior should be enabled only by explicit caller-owned setup or
configuration. Without that explicit setup, `/v1/chat` should remain local-only.

The proof should not add a second public user-facing endpoint only to avoid
touching `/v1/chat`. The project goal is one endpoint, two machines, one routed
request. If accepted, this RFC allows `/v1/chat` to be that endpoint for the
first proof.

This does not mean:

- remote routing is enabled by default;
- every `/v1/chat` request may leave the local machine;
- unknown nodes may be contacted;
- dynamic discovery is active;
- remote execution is implicit.

The active behavior should remain explainable: a reviewer should be able to
see what setup enabled remote routing and which declared node was allowed.

## Privacy and Trust Boundaries

The proof remains local-first and privacy-first.

Request contents may cross the remote boundary only when all of the following
are true:

1. the remote node is manually declared;
2. the setup explicitly allows remote routing for the proof;
3. an explicit `RemoteTransport` is provided for that declared node;
4. the selected candidate is the declared remote candidate.

The proof must not use reachability as trust. A reachable machine is not
automatically a cluster node.

The proof must not use transport address as node identity. Node identity and
cluster-facing metadata remain part of the manually declared node description.

Unknown or undeclared machines must never be contacted for discovery,
probing, routing, execution, registration, or fallback.

Cloud execution is not part of this proof.

## Failure Behavior

The first proof should fail explicitly.

If the declared remote node cannot be reached, the transport fails, the remote
side returns an invalid result, or remote execution fails, the request should
return a clear failure through the active error path chosen by the
implementation RFC.

No fallback should occur after remote failure.

No retry should occur after remote failure.

The system should not silently try:

- a local candidate after selected remote failure;
- another remote node;
- another transport;
- another adapter;
- another endpoint.

Fallback, retry, timeout policy, and richer user-facing error mapping remain
separate decisions.

## Rationale

The project's first meaningful proof is:

```text
One endpoint. Two machines. One routed request.
```

The smallest way to prove that is not dynamic discovery, registration,
scheduling, or a dashboard. It is a static setup that allows one declared
remote node to handle one routed request through an explicit remote transport.

Using `/v1/chat` as the endpoint keeps the proof aligned with the user's model:
the user talks to the cluster, not to a machine. However, this must not weaken
privacy defaults. `/v1/chat` may route remotely only when remote routing is
explicitly enabled for the proof.

Manual declaration keeps trust visible. Explicit transport keeps request
movement visible. No fallback keeps the proof easy to reason about.

This gives Phase 3 a concrete target without pretending to solve production
distributed orchestration.

## Alternatives Considered

### Keep `/v1/chat` local-only and use only a separate proof helper

This would avoid changing the public active endpoint, but it would not fully
prove the roadmap goal of one endpoint, two machines, one routed request.

The helper may still be useful for tests or setup, but the first Phase 3 proof
should allow `/v1/chat` to be the endpoint when explicitly configured.

### Add dynamic discovery first

This is rejected. Dynamic discovery is a separate architectural decision. It
is not required for the smallest two-machine proof.

### Add registration first

This is rejected. Registration changes membership and trust boundaries. The
first proof can use manual static declaration.

### Add persistence or config loading first

This is rejected for this RFC. A later implementation RFC may decide the
smallest explicit setup mechanism, but this RFC does not require persistence or
file-based configuration.

### Add fallback after remote failure

This is rejected. Fallback is a routing and execution policy decision. It
would make the first proof harder to review and explain.

### Add scoring or scheduling

This is rejected. The first proof needs one visible routed request, not a
general scheduler.

### Make cloud execution part of the proof

This is rejected. The first Phase 3 proof should remain local-first and
personal-machine focused.

## Trade-offs

Allowing `/v1/chat` to route to a declared remote node makes the first proof
more meaningful, but it also touches the active public path. That is why this
RFC requires explicit setup and keeps remote behavior disabled by default.

Keeping the proof static avoids premature infrastructure, but it means the
first proof does not demonstrate discovery, registration, persistence, or
automatic membership. That is acceptable because those are separate decisions.

Disallowing fallback makes failures more visible. It may be less convenient,
but it keeps the first remote proof honest and easy to debug.

## Impact

If accepted, this RFC would affect future Phase 3 implementation work.

It would allow a future implementation RFC or PR to make `/v1/chat` route to
one manually declared remote node when remote routing is explicitly enabled by
caller-owned setup or configuration.

It would not require code changes by itself.

It would not activate remote routing by default.

It would not activate remote execution by default.

It would not decide dynamic discovery, registration, persistence,
daemon-owned registry state, retries, fallback, health probing, scoring,
scheduling, Docker, Kubernetes, dashboard, database, or OpenAI-compatible API.

## Open Questions

- What is the smallest explicit setup mechanism for enabling the proof without
  introducing premature config loading or persistence?
- Should the first implementation use an in-memory wiring helper, a test-only
  setup, or a minimal explicit process setup?
- What exact user-facing error should `/v1/chat` return when the selected
  declared remote node fails?
- What routing explanation shape should show which node handled the first
  routed remote request?
- Should the first proof allow local and remote candidates side by side, or
  should it use a declared-remote-only setup to make the proof narrower?

## Decision

Accepted.

The first Phase 3 proof is:

```text
One endpoint. Two machines. One routed request.
```

For that proof, `/v1/chat` may route to one manually declared remote node only
when remote routing is explicitly enabled by caller-owned setup or
configuration.

The proof remains static, explicit, local-first, and privacy-first.

Remote routing and remote execution are not enabled by default.

Unknown or undeclared machines must never be contacted.

This decision does not introduce dynamic discovery, registration, persistence,
daemon-owned registry state, retries, fallback, health probing, scoring,
scheduling, Docker, Kubernetes, dashboard, database, OpenAI-compatible API,
cloud execution, or implicit remote behavior.
