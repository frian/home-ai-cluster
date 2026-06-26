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

A node should be able to announce basic information about itself, including availability, supported capabilities, available runtimes, and basic health.

Expected outcomes:

* minimal agent process;
* node identity;
* node health;
* capability announcement;
* basic registration with the orchestrator.

This phase proves that machines can describe what they can do.

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
