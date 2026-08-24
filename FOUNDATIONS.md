# Foundations

Status: Current

Home AI Cluster is built on a small set of ideas that should remain stable even as models, runtimes, hardware, and implementations change.

This document defines the foundations of the project.

It is not a specification.

It is not a roadmap.

It is the memory of why the project exists.

---

## Core idea

Home AI Cluster turns multiple personal computers into one local AI system.

Many machines.

One AI.

---

## Motto

> The user talks to the cluster, never to a machine.

The user should not have to select a machine, runtime, or model for an ordinary
request.

Within operator-owned topology and explicit process-local composition, routing
should make deterministic capability-centered choices.

The user should simply ask.

---

## Why it exists

Modern developers and hobbyists often own several computers.

A desktop.

A laptop.

A mini PC.

A NAS.

A Raspberry Pi.

An old workstation.

Each machine has resources.

Each machine can run something.

But local AI tools usually treat these machines as isolated systems.

Home AI Cluster exists to make these machines work together as one personal AI infrastructure.

---

## First user

The first user is a technical individual who already uses or wants to use local AI.

They may be a developer, a Linux user, a self-hosting enthusiast, or a privacy-conscious hobbyist.

They do not need an enterprise platform.

They need a simple way to make several personal machines behave like one AI system.

Home AI Cluster should eventually become accessible to more people, but it should begin with users who understand local tools and value control.

---

## Core abstraction

The core abstraction is the capability.

Not the machine.

Not the model.

Not the runtime.

Machines are physical resources.

Models are replaceable.

Runtimes are adapters.

Capabilities describe what the cluster can do for the user.

The cluster should not ask first:

> Which model should run this?

It should ask:

> What does this request need?

Then it should use explicitly declared capability eligibility and deterministic
selection within operator-owned boundaries. Local candidates have fixed
precedence; declared remotes retain operator-declared order. The cluster does
not rank models, runtimes, load, latency, capacity, or live health.

---

## Local first

Home AI Cluster must work without requiring an external service.

No account should be required.

No cloud service should be required.

No internet connection should be required for normal operation once the necessary software and models are installed.

Cloud execution may exist later, but only as an explicit option.

Local first is not a marketing phrase.

It is an architectural constraint.

---

## Privacy by default

Privacy must shape the architecture from the beginning.

Prompts should not be logged by default.

Responses should not be logged by default.

Request contents should not leave the local cluster unless the user explicitly allows it.

The system should make privacy boundaries visible and understandable.

The safest default is:

> Do not collect what is not needed.

---

## Engine independence

Home AI Cluster must not depend on any specific AI engine.

It may support Ollama.

It may support llama.cpp.

It may support vLLM.

It may support MLX.

It should support future runtimes without redesigning the project.

The core should speak in terms of capabilities, requests, constraints, results, health, and availability.

Runtime-specific details belong in adapters.

Today’s favorite runtime may not be tomorrow’s best option.

Home AI Cluster should survive that.

---

## User control

The cluster may automate decisions only inside boundaries chosen by the user.

The user should explicitly control which machines participate, network and
privacy boundaries, explicit process-local runtime and model composition,
whether optional external providers are allowed, whether prompts may be logged,
and whether requests may leave the local network. Cluster-facing requests and
routing remain independent of runtime and model names.

The cluster may recommend.

The cluster may explain.

The cluster may choose among allowed options.

But it must not silently expand its own authority.

Trust is more important than convenience.

---

## Simplicity

The project should prefer boring, understandable solutions.

A simple design that works is better than an elegant design nobody can operate.

Every architectural decision must make the system simpler for its users, even if it makes it harder for its developers.

Complexity is acceptable only when it makes the user experience simpler, safer, or more reliable.

Complexity must justify itself.

---

## Non-negotiables

These ideas should remain true over time:

* Multiple personal machines can behave like one AI.
* The user talks to the cluster, never to a machine.
* The project remains local-first.
* Privacy remains the default.
* Engines remain replaceable.
* Capabilities matter more than brand names.
* The architecture remains understandable.
* The project serves personal users before infrastructure teams.
* The project refuses unnecessary complexity.
* The project is not a cloud platform.

---

## First proof

The founding proof of Home AI Cluster was achieved without distributed LLM
execution.

Its deliberately simple shape was:

> One endpoint. Two machines. One routed request.

It proved the core idea without pretending to solve the whole problem.

Everything else can come later.
