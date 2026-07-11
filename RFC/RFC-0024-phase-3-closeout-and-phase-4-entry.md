# RFC-0024: Phase 3 Closeout and Phase 4 Entry

Status: Accepted

Date: 2026-07-11

Author: frian

## Summary

Phase 3 has achieved the guiding milestone:

> One endpoint. Two machines. One routed request.

The proof is deliberately static, manual, explicit, and limited to two
machines on a trusted LAN. This RFC proposes formally closing Phase 3 as the
first real two-machine proof checkpoint and establishing a controlled boundary
before Phase 4 work begins.

Closing this checkpoint does not make Home AI Cluster production-ready,
dynamically distributed, secure against untrusted nodes, or ready for automatic
routing.

## Problem

The Phase 3 proof criteria have been demonstrated, but without an explicit
closeout the project may continue adding concerns to the proof indefinitely.
That would blur a successful static proof with production clustering, make
manual declarations look like discovery, and make proof wiring look like
ordinary application behavior.

It would also risk introducing Phase 4 routing policy, fallback, health
probing, scoring, or scheduling without a prior architectural decision.

## Goals

This RFC should:

- formally record that the Phase 3 proof criteria were demonstrated;
- define exactly what Phase 3 proved and did not prove;
- preserve the ordinary application's local-only default;
- preserve the explicit static proof as a proof mechanism, not a production
  operating mode;
- establish that Phase 4 work requires a separate accepted RFC;
- identify the minimum questions that the first Phase 4 RFC must answer; and
- prevent Phase 4 implementation from beginning implicitly.

## Non-goals

This RFC does not:

- change code or `/v1/chat`;
- activate remote routing in the ordinary application;
- make static proof wiring the default application behavior;
- define a final capability model or automatic capability-based routing;
- define fallback, retry, health probing, scoring, or scheduling;
- define dynamic discovery, registration, persistence, or a configuration file
  format;
- define node authentication, encryption, or verified remote identity;
- define production deployment, Docker, Kubernetes, a database, or a dashboard;
- introduce an OpenAI-compatible API; or
- begin Phase 4 implementation.

## Current Phase 3 State

The demonstrated path is:

```text
Ubuntu caller
  -> explicit static proof process
  -> one local user-facing endpoint
  -> explicit declared-remote-only selection
  -> caller-owned declared remote node
  -> LAN HTTP transport
  -> Windows internal cluster endpoint
  -> remote local execution boundary
  -> Ollama adapter
  -> llama3.2
  -> normalized successful cluster result
  -> authoritative node attribution as declared-remote
  -> user response
```

The observed proof used an Ubuntu portable caller and a Windows 11 Pro Dell
OptiPlex receiver. The proof used receiver address `192.168.0.55`, Ollama, and
the configured model `llama3.2`. A cold-model request completed in
approximately ten seconds with `200 OK` and `node_id: declared-remote`.

The receiver IP address is transport metadata, not authoritative node identity.
For declared remote execution, attribution comes from the caller-owned declared
node id.

## Phase 3 Closeout Criteria

Phase 3 is complete when all of the following are true:

- two real machines participate;
- one user-facing endpoint accepts the request;
- the remote machine is manually and explicitly declared;
- unknown or undeclared machines are not contacted;
- candidate discovery and selection remain separate;
- the selected candidate is explicit;
- the selected declared remote candidate executes through the accepted remote
  transport boundary;
- the remote machine executes through its local adapter boundary;
- a normalized result returns to the caller;
- the result includes authoritative selected-node attribution;
- the ordinary application remains local-only by default;
- the proof requires explicit activation;
- no retry or fallback occurs after selected execution failure;
- request contents cross the network only because the operator explicitly
  activated and configured the proof; and
- cold local runtime startup does not fail because of an accidental HTTP client
  timeout.

These criteria have been demonstrated.

## What Phase 3 Does Not Establish

Phase 3 does not establish:

- dynamic node discovery or registration;
- verified machine identity, trust between untrusted machines, authentication,
  or application-level encryption;
- persistent node declarations or production configuration;
- automatic selection between local and remote candidates or a
  capability-based routing policy;
- health-aware routing, fallback, retry, scoring, or scheduling;
- multiple active remote nodes or high availability;
- production observability or production readiness; or
- a complete distributed system.

## Proposal

This RFC proposes that:

1. Phase 3 is formally closed as the first real two-machine proof checkpoint.
2. The guiding milestone has been demonstrated.
3. The existing static proof remains an explicit proof path.
4. The ordinary application remains local-only by default.
5. Phase 4 is not started by this RFC.
6. Any Phase 4 implementation requires a separate accepted RFC.

## Phase 4 Entry Boundary

The roadmap defines Phase 4 as capability-based routing. This RFC does not
design that behavior.

Before Phase 4 implementation begins, its first RFC must answer at least:

- What exact routing behavior is being activated?
- Does the ordinary `/v1/chat` path change?
- Which existing capability representation is sufficient, and what is missing?
- How are local and declared remote candidates matched against requested
  capabilities?
- Is selection still explicitly configured, or does the cluster choose
  automatically?
- What happens when no candidate matches?
- Is fallback still out of scope?
- Is health descriptive only, or does it affect routing?
- How is accidental remote execution prevented?
- What routing explanation is returned or recorded?
- Which parts remain static and manually configured?
- What behavior is deliberately postponed?

Fallback, retry, health-aware routing, scoring, scheduling, discovery, and
registration require explicit decisions and must not enter Phase 4 implicitly.

## Rationale

This closeout follows architecture-before-implementation and RFC-before-
architectural-decision principles. It preserves local-first and privacy-first
defaults because remote request movement remains explicit and operator-owned.

It preserves engine independence by treating Ollama as the runtime used in the
proof, not as the core architecture. It also keeps the project
capability-centered without silently defining a capability-routing policy.

Closing Phase 3 now keeps the successful proof small and reviewable. It
prevents a deliberately boring proof from growing into an accidental production
architecture.

## Alternatives considered

### Keep Phase 3 open and continue improving the proof

Rejected. The proof criteria have been demonstrated. Further work would blur
Phase 3 with later concerns.

### Treat the proof as the ordinary application architecture

Rejected. The proof wiring is intentionally explicit, static, and
operator-controlled.

### Begin capability-based routing immediately

Rejected. It introduces routing policy and user-visible behavior that require
a separate RFC.

### Add fallback or health-aware routing before closing Phase 3

Rejected. Those are Phase 4-or-later policy decisions and are not required for
the first two-machine proof.

### Require authentication or production hardening before closing Phase 3

Rejected as a closeout requirement. Those remain important future decisions,
but the trusted-LAN static proof did not claim production security.

## Trade-offs

Closing Phase 3 leaves a deliberately limited proof: manual setup, static
declaration, a trusted-LAN assumption, an explicit process entrypoint, and no
automatic routing.

This is acceptable because Phase 3 proves the architecture's two-machine path,
not production operation. The limitation keeps later routing, trust, and
operational decisions visible instead of making them accidental consequences of
the proof.

## Impact

If accepted, this RFC changes project phase status and records the first guiding
milestone as achieved. It requires no implementation changes and does not
activate Phase 4 behavior.

Future capability-routing implementation must be covered by a new accepted RFC.
Acceptance may later justify a small roadmap or current-state update, but this
RFC does not rewrite roadmap semantics.

## Open questions

- What is the smallest useful automatic capability-based routing behavior?
- Should Phase 4 first activate automatic choice only between one local and one
  declared remote candidate?
- What failure behavior should be visible when no capability match exists?
- Should health remain descriptive in the first Phase 4 increment?
- What minimal routing explanation should accompany a result?

## Decision

Accepted.

Phase 3 is formally closed as the first real static two-machine proof
checkpoint.

The guiding milestone has been demonstrated:

> One endpoint. Two machines. One routed request.

The existing static proof remains an explicit, manually configured proof path.
The ordinary application remains local-only by default.

Phase 4 is not started by this decision. Any Phase 4 implementation, including
capability-based routing behavior, requires a separate accepted RFC before
implementation begins.

This decision does not introduce automatic routing, fallback, retry,
health-aware routing, scoring, scheduling, discovery, registration,
persistence, authentication, verified remote identity, or production
deployment.
