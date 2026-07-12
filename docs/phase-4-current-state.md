# Phase 4 Current State

Status: Draft

This document describes the current Phase 4 implementation state after merged
PRs #142 and #143. It is descriptive, not a new architectural decision.
Accepted RFCs remain the source of architectural decisions.

## Status

Phase 4 has begun. Accepted RFC-0025 is implemented in an explicit internal
composition seam, and accepted RFC-0026 is implemented as a dedicated
proof-only automatic-routing process by PR #147.

Phase 4 is not complete. A real two-machine RFC-0025/RFC-0026 proof succeeded
on 2026-07-12; it returned HTTP 200 from Ollama model `llama3.2` with
`node_id=declared-remote`.

The evidence-based [Phase 4 Completion Assessment](phase-4-completion-assessment.md)
records why the demonstrated proof does not yet satisfy every current roadmap
outcome.

Accepted RFC-0027 is implemented by the explicit
`home-ai-cluster-explain-routing` command. It reports an explanation without
candidate execution; ordinary `/v1/chat` remains unchanged, and fallback
remains postponed.

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

The following RFC-0025 implementation is now present on `main`:

- automatic candidate selection;
- deterministic internal explanation facts;
- explicit automatic orchestration;
- preservation of the no-selectable-candidate explanation;
- reuse of selected-candidate execution; and
- caller-owned declared-remote `node_id` attribution.

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

## Explicitly postponed

- fallback;
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
- ordinary `/v1/chat` activation; and

## Next architectural question

The next Phase 4 architectural question remains undecided and requires an RFC
before implementation.

## Accepted RFC references

- [RFC-0022: Explicit Static Proof Process Entrypoint](../RFC/RFC-0022-explicit-static-proof-process-entrypoint.md)
- [RFC-0024: Phase 3 Closeout and Phase 4 Entry](../RFC/RFC-0024-phase-3-closeout-and-phase-4-entry.md)
- [RFC-0025: Minimal Capability-Based Candidate Selection](../RFC/RFC-0025-minimal-capability-based-candidate-selection.md)
- [RFC-0027: Minimal Operator-Facing Routing Explanation](../RFC/RFC-0027-minimal-operator-facing-routing-explanation.md)
