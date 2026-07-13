# Phase 4 Current State

Status: Draft

This document describes the current Phase 4 implementation state. It is
descriptive, not a new architectural decision.
Accepted RFCs remain the source of architectural decisions.

## Status

Phase 4 is complete according to the current roadmap and accepted RFCs.
RFC-0025 automatic capability selection, RFC-0026's real two-machine automatic
proof, RFC-0027's no-execution routing explanation, and RFC-0028's narrowly
defined fallback are implemented and demonstrated.

The real RFC-0028 proof succeeded on 2026-07-13. It returned HTTP 200 from
Ollama model `llama3.2` with `node_id=declared-remote` after the dedicated
proof-only local runtime endpoint could not establish a connection before
request transmission.

The evidence-based [Phase 4 Completion Assessment](phase-4-completion-assessment.md)
records the narrow completion conclusion and its limits.

## Accepted decision

RFC-0025 defines a small, cluster-owned automatic capability-selection policy:

- candidates match only by exact `Capability(name)` matching;
- discovery, selectability, selection, and execution are separate steps;
- the sole selectable candidate wins;
- when both are selectable, local wins through fixed precedence;
- `local_only=true` excludes declared-remote selection, contact, and
  execution;
- no selectable candidate fails before execution;
- selected execution occurs exactly once, with no retry or fallback; and
- health remains descriptive and does not influence routing.

## Implemented seams

The following capability-routing implementation is now present on `main`:

- automatic candidate selection;
- deterministic internal explanation facts;
- explicit automatic orchestration;
- preservation of the no-selectable-candidate explanation;
- reuse of selected-candidate execution; and
- caller-owned declared-remote `node_id` attribution.

RFC-0028 additionally provides:

- one cluster-owned pre-execution connection-unavailability signal;
- one narrow Ollama adapter translation for that signal;
- one proof-only local-to-declared-remote fallback seam; and
- one explicit two-machine fallback proof process.

The merged implementation PRs are:

- PR #142 — automatic candidate selection;
- PR #143 — automatic orchestration.

## Current execution shape

```text
explicit caller-owned composition
  -> discover local and declared-remote candidates
  -> apply request constraints
  -> select one candidate or fail before execution
  -> execute the selected candidate exactly once
```

## What remains unchanged

- Ordinary application wiring remains local-only.
- Ordinary `/v1/chat` does not invoke declared-remote discovery.
- Ordinary `/v1/chat` does not invoke automatic selection.
- Ordinary `/v1/chat` does not invoke remote transport.
- RFC-0022’s caller-directed proof path remains unchanged.
- A declaration, address, or transport instance alone does not activate remote
  routing.

## Recorded automatic-routing proof

PR #147 added the dedicated proof-only automatic-routing process. Its real
two-machine execution is recorded in
[Automatic Routing Two-Machine Proof Result](automatic-routing-two-machine-proof-result.md).
Ordinary `/v1/chat` remains local-only, RFC-0022 remains unchanged, and no
general routing or configuration surface was introduced.

## Recorded fallback proof

The dedicated RFC-0028 fallback proof process demonstrated the accepted local
to declared-remote fallback condition on two real machines. Its observed
result, including the direct readiness check and the dedicated proof-only
fallback path, is recorded in
[RFC-0028 Two-Machine Fallback Proof Result](rfc-0028-two-machine-fallback-proof-result.md).
It does not establish general node availability or ordinary application
fallback.

## Explicitly outside the demonstrated fallback condition

- retry;
- health-aware routing;
- scoring;
- scheduling;
- load balancing;
- discovery;
- registration;
- persistence;
- configuration design;
- authentication and trust;
- richer capability modeling;
- ordinary `/v1/chat` activation.

The demonstrated fallback is only candidate/runtime endpoint connection
unavailability before request transmission. It does not define general node
availability, timeout or HTTP-error fallback, retry, high availability, or
ordinary application fallback.

## Accepted RFC references

- [RFC-0022: Explicit Static Proof Process Entrypoint](../RFC/RFC-0022-explicit-static-proof-process-entrypoint.md)
- [RFC-0024: Phase 3 Closeout and Phase 4 Entry](../RFC/RFC-0024-phase-3-closeout-and-phase-4-entry.md)
- [RFC-0025: Minimal Capability-Based Candidate Selection](../RFC/RFC-0025-minimal-capability-based-candidate-selection.md)
- [RFC-0027: Minimal Operator-Facing Routing Explanation](../RFC/RFC-0027-minimal-operator-facing-routing-explanation.md)
- [RFC-0028: Minimal Pre-Execution Candidate Fallback](../RFC/RFC-0028-minimal-pre-execution-candidate-fallback.md)
- [RFC-0028 Two-Machine Fallback Proof Result](rfc-0028-two-machine-fallback-proof-result.md)
