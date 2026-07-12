# Phase 4 Current State

Status: Draft

This document describes the current Phase 4 implementation state after merged
PRs #142 and #143. It is descriptive, not a new architectural decision.
Accepted RFCs remain the source of architectural decisions.

## Status

Phase 4 has begun. Accepted RFC-0025 is implemented in an explicit internal
composition seam.

Phase 4 is not complete. No real two-machine proof of the RFC-0025 automatic
capability-selection behavior has yet been recorded.

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

## What has not been proved yet

No real two-machine proof of RFC-0025 automatic capability selection has yet
been recorded.

The implementation is covered by in-memory tests, but no operator-facing or
proof-process invocation has been decided or implemented.

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
- public routing explanation.

## Next architectural question

> What is the smallest explicit operator-owned way to invoke and prove
> RFC-0025 automatic capability routing without changing ordinary `/v1/chat`?

Answering this question requires a new RFC before implementation. This document
does not propose a final interface, configuration format, endpoint, command, or
process design.

## Accepted RFC references

- [RFC-0022: Explicit Static Proof Process Entrypoint](../RFC/RFC-0022-explicit-static-proof-process-entrypoint.md)
- [RFC-0024: Phase 3 Closeout and Phase 4 Entry](../RFC/RFC-0024-phase-3-closeout-and-phase-4-entry.md)
- [RFC-0025: Minimal Capability-Based Candidate Selection](../RFC/RFC-0025-minimal-capability-based-candidate-selection.md)
