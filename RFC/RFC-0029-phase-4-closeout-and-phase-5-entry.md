# RFC-0029: Phase 4 Closeout and Phase 5 Entry

Status: Accepted

Date: 2026-07-13

Author: frian

## Summary

Phase 4 has completed the current roadmap checkpoint for capability-based
routing. This RFC proposes to formally close that checkpoint and establish a
controlled entry boundary before Phase 5 runtime-adapter work begins.

Phase 4 demonstrated a simple capability-based routing shape, including one
narrow proof-only fallback condition. It did not make the ordinary application
a general remote-routing or resilient execution system.

This RFC does not select a second runtime, design a second adapter, or
authorize Phase 5 implementation. A separate accepted RFC must make those
decisions first.

## Problem

The Phase 4 roadmap outcomes are now demonstrated through accepted RFCs,
focused tests, and real two-machine proofs. Without an explicit closeout, the
project risks treating the current Ollama adapter and its protocol as a final
multi-runtime design, or beginning a second adapter by copying runtime-specific
assumptions into the core.

That would undermine engine independence, capability-centered routing, and the
project preference for architecture before implementation. It could also turn a
small second-adapter proof into a generic plugin system, configuration design,
or model-routing effort before those decisions are accepted.

## Goals

This RFC should:

* formally close Phase 4 as the demonstrated capability-based routing
  checkpoint;
* state precisely what Phase 4 demonstrated and what it did not establish;
* preserve ordinary local-only application behavior;
* establish that Phase 5 implementation requires a separate accepted RFC;
* require that RFC to define the smallest useful second-runtime proof; and
* preserve local-first, privacy-first, engine-independent, capability-centered
  boundaries.

## Non-goals

This RFC does not:

* select the second runtime;
* add code, modify the adapter protocol, or modify Ollama behavior;
* activate multiple adapters in ordinary application wiring;
* define model discovery, automatic model selection, adapter scoring, adapter
  fallback, plugin loading, or entry-point discovery;
* define a configuration format, database, Docker or Kubernetes setup,
  dashboard, or OpenAI-compatible API; or
* begin Phase 5 implementation.

## Current Phase 4 State

Phase 4 is complete according to the current roadmap and accepted RFCs. The
demonstrated outcomes are:

* a simple exact-name `Capability(name)` model;
* request constraints, including `local_only` as a hard privacy boundary;
* local adapter-backed and declared-remote declaration-backed candidate
  matching;
* deterministic automatic selection with fixed local precedence;
* exactly-once selected execution;
* an operator-facing routing explanation that performs no execution;
* one narrow proof-only local-to-declared-remote fallback condition;
* real two-machine automatic-routing and fallback proofs; and
* authoritative caller-owned `declared-remote` node attribution.

The real-machine proofs directly observed successful HTTP results and
normalized caller-owned node attribution. The direct remote readiness checks
additionally observed receiver-side Ollama execution. The narrow
pre-transmission connection classification and exact-attempt-count guarantees
are established by the implemented adapter and orchestration boundaries and
their focused automated tests.

All remote-capable behavior remains proof-only and explicitly activated.
Ordinary `/v1/chat` remains local-only: it does not automatically activate
remote routing or fallback.

## What Phase 4 Does Not Establish

Phase 4 does not establish:

* general node availability or health-aware routing;
* general fallback, retry, timeout fallback, HTTP-error fallback, or arbitrary
  failure recovery;
* high availability, fault tolerance, or general resilience;
* dynamic discovery or registration;
* persistent configuration;
* verified remote identity, untrusted-node security, or production
  observability;
* ordinary application automatic remote routing; or
* a complete distributed system.

In particular, RFC-0028 permits only candidate/runtime endpoint connection
unavailability before request transmission in its dedicated proof-only path.
It must not be broadened into a claim that a node is down or that ordinary
traffic automatically fails over.

## Proposal

This RFC proposes that:

1. Phase 4 is formally closed as the demonstrated capability-based routing
   checkpoint.
2. The existing proof-only routing and fallback paths remain explicit and do
   not change ordinary application behavior.
3. Phase 5 is not started by this RFC.
4. No Phase 5 implementation begins until a separate RFC is accepted.
5. That RFC must select one concrete second runtime and define the smallest
   implementation and proof needed to validate the existing engine-independent
   abstraction.

## Phase 5 Entry Boundary

The roadmap defines Phase 5 as:

```text
Goal:
Keep the core independent from specific AI engines.

Expected outcomes:
- at least two runtime adapters;
- a minimal adapter interface;
- clear separation between core orchestration and runtime details.
```

The current protocol and Ollama adapter are evidence and implementation input,
not a declaration that the current protocol is the final Phase 5 interface.
Before any Phase 5 implementation begins, the first Phase 5 RFC must answer at
least:

1. Which concrete second runtime is proposed, and why is it the smallest useful
   proof?
2. Is the second runtime already available locally, or does adopting it add
   installation or operational complexity?
3. Which single capability will both adapters prove first?
4. What exact request and result semantics must both adapters implement?
5. Which current adapter protocol members are truly cluster-owned and
   engine-independent?
6. Which existing Ollama-specific assumptions must not leak into the core?
7. Which runtime-specific errors are translated at the adapter boundary?
8. Which errors remain visible without normalization?
9. Does adapter health remain descriptive, and is it comparable across
   runtimes?
10. How is model selection handled without making model names part of core
    routing?
11. How will tests prove that the core does not branch on runtime type or name?
12. How will a real local proof demonstrate interchangeable execution through
    two adapters?
13. Does ordinary `/v1/chat` change?
14. What remains explicitly postponed?

The selected second adapter must prove the existing abstraction rather than
trigger a broad plugin framework or runtime ecosystem design.

## Rationale

Closing Phase 4 preserves the value of a small, demonstrated routing
checkpoint. It makes the project’s current limits explicit rather than inviting
unplanned resilience, availability, or remote-routing features.

Requiring a Phase 5 RFC preserves engine independence without assuming that
one adapter’s implementation details are already universal. It supports a
boring proof: two explicit runtime adapters, one shared capability, one clear
adapter boundary, and evidence that the core does not depend on a runtime brand.

This follows local-first and privacy-first principles because it adds no cloud
dependency, telemetry, prompt logging, or automatic remote movement. It also
preserves the rule that agents implement accepted decisions but do not make
architectural decisions themselves.

## Alternatives considered

### Begin implementing a second adapter immediately

Rejected. Selecting a runtime and deciding shared semantics, error boundaries,
and proof requirements are architectural decisions that require an accepted
RFC.

### Declare the existing adapter protocol final without review

Rejected. A protocol used by only Ollama has not yet demonstrated that its
members are engine-independent or sufficient for a second runtime.

### Build a generic plugin system first

Rejected. Plugin loading, entry-point discovery, and lifecycle management are
premature abstractions. Two explicit adapters are enough to test the boundary.

### Refactor Ollama into a broad abstraction before a second implementation exists

Rejected. This would generalize from one runtime without evidence and could
hide runtime-specific assumptions rather than expose them for review.

### Postpone Phase 4 closeout and continue adding routing features

Rejected. The current roadmap outcomes are demonstrated. Continuing would blur
the completed routing checkpoint with later availability or resilience work.

### Choose the most feature-rich runtime rather than the smallest useful proof

Rejected. A feature-rich choice may add operational complexity and scope beyond
what is needed to demonstrate a second adapter.

## Trade-offs

This RFC intentionally delays Phase 5 implementation. It requires another
review cycle before code can be written and leaves the current adapter protocol
open to revision.

That cost is acceptable because it prevents a second runtime from silently
shaping the core. The boundary keeps the next increment small, reviewable, and
reversible while protecting the project from premature plugin, configuration,
or model-routing infrastructure.

## Impact

If accepted, this RFC formally records Phase 4 completion and requires a
separate accepted Phase 5 design RFC before implementation. It changes no
runtime behavior, public HTTP contract, routing policy, adapter interface,
proof process, or configuration.

## Open questions

The Phase 5 entry questions above remain open until a separate RFC proposes a
concrete second runtime and the smallest shared adapter proof.

## Decision

Accepted.

Phase 4 is formally closed as the demonstrated capability-based routing
checkpoint.

The existing automatic-routing, routing-explanation, and narrow fallback
behaviors remain explicit proof-only mechanisms. Ordinary `/v1/chat` remains
local-only and does not automatically activate remote routing or fallback.

Phase 5 is not started by this decision. No Phase 5 implementation may begin
until a separate RFC is accepted that selects one concrete second runtime and
defines the smallest shared adapter implementation and proof needed to test the
engine-independent boundary.

This decision does not select a second runtime, declare the current adapter
protocol final, authorize adapter implementation, or introduce plugin loading,
model discovery, adapter scoring, configuration infrastructure, or broader
runtime abstraction.
