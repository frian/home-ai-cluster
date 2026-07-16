# Next Phase Direction Investigation

Status: Investigation

Date: 2026-07-16

## Purpose

This document investigates the smallest useful direction after completion of
Phase 8.

It does not define a new phase, introduce an architectural decision, authorize
implementation, or change the supported operating modes.

Any architectural change identified here still requires a separate RFC before
implementation.

## Current position

The founding milestone has now been reproduced from the canonical operator
workflow:

> One endpoint. Two machines. One routed request.

The current system provides:

- ordinary local-only operation;
- explicit static two-machine proof operation;
- capability-based routing;
- explicit static node and adapter registries;
- runtime adapters kept behind cluster-facing boundaries;
- static operator preflight;
- runtime health observation;
- routing explanations and privacy-bounded request history;
- a canonical operator workflow;
- a verified privacy-safe operator proof.

The current state is described in:

```text
docs/phase-8-current-state.md
```

## Operational evidence

The verified operator run demonstrated that the architecture works across two
real machines on a trusted LAN.

It also exposed the remaining friction:

- both machines must be prepared manually;
- both machines must use the same repository revision;
- the receiving application must be started manually;
- the receiving endpoint must be supplied explicitly;
- the calling machine uses a proof-specific process;
- shutdown order remains manual;
- temporary network exposure remains operator-managed;
- the two-machine path is still proof-only rather than an ordinary supported
  cluster mode.

This friction is evidence for investigation, not evidence that automation or
discovery is required next.

## Core question

> What is the smallest next increment that makes multiple static nodes more
> useful in ordinary operation without introducing discovery, supervision,
> remote process control, or premature configuration machinery?

## Evaluation criteria

A useful next increment should:

- preserve local-first and privacy-first operation;
- remain engine-independent and capability-centered;
- build on the accepted static architecture;
- make the cluster abstraction more ordinary rather than more theatrical;
- reduce proof-specific behavior where justified;
- keep external runtime ownership explicit;
- avoid automatic discovery and lifecycle ownership;
- remain understandable to one operator;
- be testable without requiring production distributed infrastructure;
- keep the change narrow enough for one RFC and one focused implementation.

## Candidate directions

### Candidate A — Ordinary static multi-node configuration

Investigate whether an operator should be able to declare more than one static
node through an ordinary supported configuration path and start one normal
cluster process that routes to those declared nodes.

Potential value:

- converts the two-machine topology from proof-only wiring into ordinary static
  operation;
- preserves explicit operator knowledge of each node;
- keeps routing capability-centered;
- avoids discovery;
- moves closer to the user talking to the cluster rather than to a machine.

Architectural questions:

- where static node declarations belong;
- whether the current in-memory registry construction can consume operator
  configuration without a new generic configuration subsystem;
- how remote node endpoints are represented;
- which facts remain local declarations versus observed runtime facts;
- how preflight handles ordinary remote declarations;
- whether one process can route to both local and remote nodes through existing
  abstractions;
- how node identity and attribution remain cluster-owned;
- what failure behavior applies when a declared remote node is unavailable.

Risks:

- introducing a configuration format before its required fields are understood;
- accidentally combining declaration, discovery, health, and lifecycle;
- turning static addresses into hidden infrastructure assumptions;
- broadening preflight without a clear contract.

### Candidate B — Generalize the proof-specific process

Investigate whether the existing static proof process can become an ordinary
supported static-cluster process with minimal changes.

Potential value:

- reuses a path already proven across two machines;
- may reduce the amount of new implementation;
- keeps topology explicit;
- could remove the special status of the proof command.

Architectural questions:

- whether the proof process has the right ownership and naming for ordinary use;
- whether its hard-coded declarations are acceptable outside a proof;
- how multiple nodes would be represented;
- whether it should remain a separate process from the ordinary application;
- whether promoting it would preserve or distort existing boundaries.

Risks:

- legitimizing proof scaffolding as permanent architecture;
- retaining hard-coded topology under a more general name;
- creating two competing ordinary application shapes;
- solving naming rather than operator usefulness.

### Candidate C — Limited lifecycle assistance

Investigate narrowly whether documentation-level or command-level assistance for
starting known local processes would remove meaningful friction without taking
ownership of remote machines or external runtimes.

Potential value:

- reduces repetitive manual steps;
- may improve ordinary local operation;
- can remain local-only.

Architectural questions:

- which processes Home AI Cluster would own;
- whether already-running detection is required;
- how logs, ports, errors, and shutdown are handled;
- whether the external runtime remains entirely operator-owned;
- whether the value applies to multi-node operation or only convenience.

Risks:

- drifting into supervision;
- introducing operating-system-specific behavior;
- hiding process boundaries that are currently explicit;
- solving lifecycle before ordinary static multi-node operation exists.

### Candidate D — Distributed-aware preflight

Investigate whether preflight should validate explicitly declared remote-node
facts before a request is attempted.

Potential value:

- may classify configuration mistakes earlier;
- could make an ordinary static multi-node mode easier to operate.

Architectural questions:

- whether remote endpoint syntax is a static fact;
- whether network reachability belongs to preflight or another surface;
- which checks are static and which are observations;
- how partial failure is represented;
- whether this is useful before ordinary remote declarations exist.

Risks:

- collapsing static validation into runtime or network health;
- contradicting RFC-0036;
- creating distributed checks before defining ordinary distributed
  configuration;
- adding a surface without a stable owning model.

### Candidate E — Discovery or automatic registration

Deferred.

The current evidence does not require automatic discovery.

Discovery would introduce identity, trust, freshness, conflict, expiry, network
scope, and security questions before ordinary static multi-node operation has
been established.

### Candidate F — Process supervision or remote control

Deferred.

The current evidence does not justify Home AI Cluster owning remote process or
runtime lifecycle.

### Candidate G — Dashboard or web UI

Rejected for the next increment.

A dashboard would visualize current limitations rather than remove the smallest
architectural gap.

## Comparison

The candidates are not equally independent.

Distributed-aware preflight depends on first knowing what an ordinary remote
node declaration is.

Lifecycle assistance does not by itself make multiple nodes an ordinary cluster.

Discovery and supervision solve much larger problems than the verified evidence
requires.

The central unresolved boundary is therefore not automation. It is whether the
existing explicit static two-machine architecture should become an ordinary
supported multi-node operating mode.

## Leading investigation direction

The strongest candidate for a later RFC is:

> Define the smallest ordinary static multi-node operating mode that reuses the
> existing node, adapter, routing, health, and attribution boundaries while
> keeping node declaration explicit and lifecycle external.

This is an investigation conclusion, not an accepted decision.

## Questions a later RFC would need to decide

A focused RFC would need to decide only:

- whether ordinary static multi-node operation becomes supported;
- the minimum declared facts for a remote node;
- where those declarations are supplied;
- how existing registries are constructed from them;
- whether one ordinary process can route across local and remote nodes;
- how local and remote adapter execution remain separated;
- how preflight and health boundaries apply;
- how remote failure and node attribution are exposed;
- which existing proof-only command remains, changes, or is retired;
- the privacy and trusted-network boundary;
- the smallest reproducible proof.

## Explicit non-goals for the next increment

The next increment should not add:

- automatic node discovery;
- automatic model discovery;
- dynamic registration;
- process supervision;
- remote process control;
- service installation;
- automatic repair or retries;
- a distributed configuration service;
- a database;
- a dashboard or web UI;
- Docker or Kubernetes;
- internet-facing operation;
- authentication unless separately justified by the chosen network boundary;
- a generic plugin or orchestration framework;
- a broad configuration abstraction.

## Evidence required before implementation

Before proposing implementation, the project should be able to describe:

1. one ordinary operator scenario involving one local and one explicit remote
   node;
2. the exact declared facts required for both nodes;
3. the process and network ownership boundaries;
4. how one request is matched and routed by capability;
5. how unavailable remote nodes are represented without hidden retries;
6. how preflight differs from health and request-time failure;
7. how privacy-sensitive endpoint values are excluded from retained evidence;
8. why the proposal is smaller than discovery, supervision, or a new generic
   configuration system.

## Recommended sequence

1. Review and merge this investigation.
2. Decide whether ordinary static multi-node operation is the next project
   direction.
3. If yes, draft one narrow RFC for that operating mode.
4. Review and merge the RFC proposal.
5. Accept the RFC separately.
6. Implement only the accepted minimum.
7. Reproduce one ordinary local-plus-remote request from documented steps.
8. Reassess lifecycle, distributed preflight, and discovery only after that
   evidence exists.

## Conclusion

The founding distributed proof now works and is reproducible.

The boring next architectural question is not how to automate the cluster. It is
whether the proven explicit static topology should become an ordinary supported
multi-node mode.

That question should be answered before discovery, supervision, remote control,
a dashboard, or a broader configuration system is introduced.
