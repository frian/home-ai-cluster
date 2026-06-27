# AGENTS.md

Status: Draft

This document defines how AI coding agents should work in the Home AI Cluster repository.

Agents may help implement the project.

They may suggest code, write code, refactor, add tests, and point out inconsistencies.

But agents must not silently make architectural decisions.

Architecture belongs to the project.

---

## Purpose

Home AI Cluster is a local-first, privacy-first, engine-independent orchestration layer for personal AI infrastructure.

The project is built around one core idea:

> Many machines. One AI.

The user talks to the cluster, never to a machine.

Agents working in this repository must preserve that idea.

---

## Required reading

Before making meaningful changes, agents should read:

* `VISION.md`
* `FOUNDATIONS.md`
* `PRINCIPLES.md`
* `NON_GOALS.md`
* `ROADMAP.md`
* `CONTRIBUTING.md`
* `RFC/README.md`
* accepted RFCs relevant to the change

Agents should not rely only on local code context.

The repository documents why the project exists, what it refuses to become, and how decisions are made.

Those documents are part of the working context.

---

## Decision rules

Agents may implement decisions.

Agents must not own decisions.

If a change affects architecture, the agent should stop and ask whether an RFC is needed.

A change probably needs an RFC if it affects:

* core orchestration;
* node behavior;
* capability modeling;
* routing behavior;
* runtime adapter boundaries;
* request or response formats;
* privacy boundaries;
* configuration format;
* long-term compatibility.

Small implementation details do not require RFCs.

Architectural decisions do.

When in doubt, ask.

---

## Coding rules

Agents should prefer small, understandable changes.

A good change should be easy to review, easy to test, and easy to revert.

Agents should not introduce unnecessary abstraction.

Agents should not add infrastructure before it is needed.

Agents should not optimize for cleverness.

The preferred approach is:

1. implement the smallest useful version;
2. keep the architecture visible;
3. add tests around behavior and boundaries;
4. leave future expansion possible without pretending to solve it now.

---

## Runtime independence

Home AI Cluster must not become shaped around one runtime.

Ollama may be the first adapter.

It must remain an adapter.

Agents must not put runtime-specific assumptions into the core unless an RFC explicitly allows it.

The core should speak in terms of:

* requests;
* capabilities;
* nodes;
* routing decisions;
* adapters;
* results;
* health;
* availability.

Runtime-specific details belong behind adapter boundaries.

---

## Privacy rules

Privacy is a design constraint.

Agents must not add prompt logging by default.

Agents must not add response logging by default.

Agents must not send request contents outside the local cluster unless explicitly allowed by project decisions.

Agents should avoid collecting data that is not needed.

The safest default is:

> Do not collect what is not needed.

---

## Git and pull requests

Agents should work through small branches and pull requests.

Branch names should describe intent.

Examples:

```text
rfc-0003-runtime-adapter-interface
docs-agents
bootstrap-python-project
feature-static-node-registry
fix-routing-explanation
```

Commit messages should describe the change clearly.

Examples:

```text
Add agent contribution guidelines
Bootstrap Python project
Add static node registry
Add Ollama runtime adapter
Fix routing explanation
```

Avoid vague messages such as:

```text
changes
misc
work
temp
fixes
```

---

## What agents must not do

Agents must not:

* silently change project architecture;
* bypass RFCs for architectural decisions;
* turn runtime-specific behavior into core behavior;
* add cloud dependencies by default;
* add prompt or response logging by default;
* add dashboards, databases, queues, or distributed infrastructure before they are needed;
* make the project harder for personal users in order to satisfy imagined enterprise needs;
* hide important decisions inside code.

If a change feels like a major decision, it probably is.

Stop and ask.

---

## Review expectations

Agent-generated changes should be reviewed like any other contribution.

A reviewer should be able to answer:

* What changed?
* Why was it needed?
* Which project decision does it implement?
* Does it respect the RFCs?
* Does it preserve local-first and privacy-first defaults?
* Does it keep the core independent from specific runtimes?
* Is the change smaller than it could be?

If those questions are hard to answer, the change is probably too large or too implicit.

---

## Final rule

Agents are collaborators, not decision makers.

They help the project move faster only when they preserve the project’s memory, boundaries, and principles.

The goal is not to generate code quickly.

The goal is to help build Home AI Cluster without losing why it exists.
