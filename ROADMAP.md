# Roadmap

Status: Draft

This roadmap describes the intended direction of Home AI Cluster.

It is not a release plan.

It is not a promise.

It is a way to keep the project aligned with its foundations while avoiding premature implementation.

The roadmap should remain small, readable, and easy to revise.

---

## Guiding milestone

The first meaningful proof of Home AI Cluster is:

> One endpoint. Two machines. One routed request.

This proves the core idea without pretending to solve the whole problem.

It shows that multiple personal machines can behave as one AI system.

---

## Phase 0 — Foundations

Goal:

Clarify the project before writing code.

Expected outcomes:

* founding questions;
* working answers;
* project foundations;
* project vision;
* RFC process;
* roadmap;
* non-goals;
* shared vocabulary.

Success means:

> The project can be explained clearly before it is implemented.

---

## Phase 1 — Single-machine orchestrator

Goal:

Create the smallest possible orchestrator on one machine.

The orchestrator should expose one API endpoint and route a request to a local runtime through a simple adapter.

Expected outcomes:

* one orchestrator process;
* one local runtime adapter;
* one chat request;
* one response;
* no distributed behavior yet.

This phase proves the shape of the system without adding network complexity.

---

## Phase 2 — Agent and node model

Goal:

Define what a node is.

A node should be represented by an explicit cluster-facing description,
including availability, supported capabilities, declared adapter names, and
basic health.

Expected outcomes:

* static local node announcement;
* node identity;
* node health;
* capability announcement;
* static in-memory node and adapter registries.

This phase starts by keeping the implementation single-process, local, static,
and non-distributed. It does not introduce an agent process, node discovery, or
a registration protocol yet.

This phase prepares the project to prove that machines can describe what they
can do.

---

## Phase 3 — Two machines

Goal:

Connect at least two machines.

The orchestrator should be able to see more than one node and route a request to one of them.

Expected outcomes:

* two running nodes;
* one orchestrator;
* one unified endpoint;
* one routed request;
* visible explanation of which node handled the request.

This is the first real proof of Home AI Cluster.

---

## Phase 4 — Capability-based routing

Goal:

Route requests based on capabilities rather than machine names, model names, or runtime names.

Expected outcomes:

* simple capability model;
* request constraints;
* node matching;
* fallback when a node is unavailable;
* basic explanation of routing decisions.

The cluster should ask:

> What does this request need?

not:

> Which machine should run this?

---

## Phase 5 — Runtime adapters

Goal:

Keep the core independent from specific AI engines.

Runtime-specific behavior should live behind adapters.

Expected outcomes:

* at least two runtime adapters;
* a minimal adapter interface;
* clear separation between core orchestration and runtime details.

The core should reason about capabilities, requests, constraints, results, health, and availability.

It should not be designed around one engine.

---

## Phase 6 — OpenAI-compatible access

Goal:

Allow existing tools to use Home AI Cluster without special integration.

Expected outcomes:

* OpenAI-compatible chat endpoint;
* simple configuration;
* local developer tools can point to the cluster instead of one machine.

The user should keep using familiar tools.

The cluster should decide where work runs.

---

## Phase 7 — Observability and trust

Goal:

Make automatic decisions understandable.

Expected outcomes:

* request history without prompt logging by default;
* routing explanation;
* node status;
* health view;
* failure visibility;
* clear privacy boundaries.

The system should not be magical.

It should be transparent.

---

## Phase 8 — Operable local cluster

Goal:

Make the existing static local cluster understandable and repeatable as an ordinary operator workflow.

Expected outcomes:

* one documented canonical operator workflow;
* static validation of configured cluster facts;
* one read-only operator preflight;
* one repeatable two-machine runbook;
* clear local-only and distributed-proof operation;
* recovery guidance;
* proof that the founding milestone can be reproduced from documented steps.

This phase should improve operation of the existing static architecture without introducing process supervision, remote process control, automatic discovery, containers, a dashboard, or a new configuration format.

Success means:

> One operator can reproduce the existing two-machine milestone without reconstructing the procedure from repository knowledge.

---

## Phase 9 — Repeatable static cluster declaration

Goal:

Make the verified ordinary static multi-node mode convenient to start repeatedly
without changing its static architecture.

Expected outcomes:

* one explicit local cluster declaration;
* one ordinary startup command;
* static validation before startup;
* no secret values in the retained declaration;
* no discovery, supervision, or remote process control;
* no automatic network observation while loading the declaration.

This phase should reduce repeated command-line reconstruction while preserving
operator ownership, explicit topology, local-first routing, and the accepted
narrow fallback.

The declaration format, location, precedence rules, validation behavior, and CLI
relationship are architectural decisions and must be defined by an accepted RFC
before implementation.

Success means:

> One operator can restart the same explicit static cluster without rebuilding
> its declaration by hand.

---

## Phase 10 — Multiple explicit static remote nodes

Goal:

Extend the verified static cluster shape beyond one explicitly declared remote
node while preserving explicit topology and operator control.

Expected outcomes:

* more than one remote node can be represented in one explicit static cluster declaration;
* all declared nodes remain statically validated before startup;
* routing continues to operate on capabilities rather than direct machine targeting;
* node attribution and routing explanation remain cluster-owned and understandable;
* no discovery, supervision, remote process control, or automatic topology mutation;
* no secrets or runtime credentials in the retained declaration;
* one repeatable real multi-machine operator proof.

This phase should test whether the accepted architecture scales from one local
plus one remote node to a small explicitly declared home cluster without turning
Home AI Cluster into a scheduler, service manager, or dynamic discovery system.

The declaration structure, supported node count, ordering semantics, duplicate
handling, validation rules, candidate selection, failure behavior, fallback
boundaries, CLI compatibility, and migration from RFC-0039 are architectural
decisions and must be defined by an accepted RFC before implementation.

Success means:

> One operator can declare and reproduce a small static cluster with multiple
> remote nodes while the user still addresses one capability-centered endpoint.

---

## Phase 11 — Explicit static cluster status

Goal:

Let an operator explicitly inspect the current runtime and network status of the
small declared static cluster before sending an ordinary request.

Expected outcomes:

* one read-only, operator-invoked cluster status operation;
* a clear distinction between static declaration coherence and observed runtime
  or network status;
* status for the fixed local node and each explicitly declared remote node;
* bounded execution with understandable, privacy-safe results;
* no prompt or generated-response logging;
* no background polling, discovery, supervision, remote process control, or
  automatic topology mutation;
* no routing, lifecycle, or declaration changes caused by status inspection.

This phase should reduce manual use of unrelated network and process tools while
keeping observation explicit, finite, and operator-owned. It should not turn
Home AI Cluster into a monitoring service, health-aware scheduler, or dynamic
cluster manager.

The observation target, status vocabulary, remote protocol, timeout behavior,
sequential or parallel execution, privacy boundary, CLI or endpoint shape, and
relationship to existing local health and static preflight behavior are
architectural decisions and must be defined by an accepted RFC before
implementation.

Success means:

> One operator can explicitly inspect the declared static cluster and understand
> which observations are static facts and which come from a bounded live check.

---

## Phase 12 — Heterogeneous runtime cluster proof

Goal:

Demonstrate that the ordinary static cluster can operate across nodes using
different runtime engines without changing the cluster-facing architecture.

Expected outcomes:

* at least two nodes in one explicitly declared static cluster use different
  runtime engines;
* one ordinary capability-centered request succeeds through the heterogeneous
  cluster;
* cluster-facing request, result, routing, attribution, and status concepts
  remain engine-independent;
* runtime-specific behavior remains confined to runtime adapters on the
  executing nodes;
* no runtime name, adapter name, or model name becomes a request-level routing
  selector;
* one retained privacy-safe real operator proof;
* no discovery, automatic runtime selection, model inventory, runtime lifecycle
  management, or new generic adapter abstraction.

This phase should connect the already-proven second runtime adapter boundary with
the already-proven ordinary static multi-node cluster. It should test whether
different runtime engines can participate in one cluster without making engine
identity part of the cluster-facing domain.

The concrete topology, runtime placement, proof path, required wiring changes,
compatibility expectations, and whether any architecture change is needed must
be investigated before implementation. Any new architectural decision requires
an accepted RFC.

A two-machine proof is sufficient if it exercises two different runtime engines.
A larger topology must not be required unless investigation shows that it is
necessary.

Success means:

> One ordinary request can execute through a statically declared cluster whose
> nodes use different runtime engines without changing the cluster-facing
> architecture.

---

## Later possibilities

These ideas may become useful later, but they are not required for the first proof:

* dashboard;
* automatic node discovery;
* automatic model discovery;
* model download helpers;
* scheduling policies;
* multi-model workflows;
* embeddings;
* vision;
* tool calling;
* local web UI;
* plugins;
* cluster-aware developer tools;
* optional cloud nodes;
* more advanced distributed inference experiments.

These ideas belong later unless they directly help prove the core abstraction.

---

## Roadmap rule

Every phase must preserve the core idea:

> Many machines. One AI.

If a phase does not make that idea clearer, simpler, or more useful, it should be postponed.
