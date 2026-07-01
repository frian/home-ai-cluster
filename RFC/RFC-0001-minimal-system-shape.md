# RFC-0001: Minimal system shape

Status: Accepted

Date: 2026-06-27

Author: frian

## Summary

Home AI Cluster should start with the smallest system shape that can grow toward the first proof:

> One endpoint. Two machines. One routed request.

The first implementation should be a single-machine orchestrator, but it should already use the language of the future cluster.

Even when there is only one local runtime, the system should already speak in terms of requests, capabilities, nodes, adapters, routing decisions, and results.

This prevents the first implementation from becoming only a wrapper around one runtime.

## Problem

Home AI Cluster exists to make multiple personal computers behave like one local AI system.

The project is not an LLM, not an inference engine, not a model format, and not a cloud platform.

Its core value is orchestration.

However, the first code will probably run on one machine and talk to one runtime.

That creates a risk.

If the first implementation is shaped around the first runtime, the architecture may become runtime-centered.

If the first implementation is shaped around the first machine, the architecture may become machine-centered.

If the first implementation is shaped around the first model, the architecture may become model-centered.

All three outcomes would conflict with the foundations of the project.

The first implementation must therefore be small, but not conceptually wrong.

## Goals

This RFC defines the minimal conceptual shape of Home AI Cluster before implementation begins.

It should:

* define the first components;
* define the first responsibilities;
* keep the project capability-centered;
* keep runtime-specific details behind adapters;
* allow a single-machine prototype without blocking the two-machine proof;
* preserve local-first and privacy-first defaults;
* avoid premature distributed-system complexity.

## Non-goals

This RFC does not define:

* a final network protocol;
* a final public API;
* automatic node discovery;
* a dashboard;
* model download or model placement;
* distributed model execution;
* scheduling policies;
* authentication or authorization;
* a final configuration format;
* a final capability ontology;
* production deployment.

Those decisions can come later.

The purpose of this RFC is to define the smallest stable shape that early code should respect.

## Proposal

Home AI Cluster should begin with five core concepts:

1. request;
2. capability;
3. node;
4. runtime adapter;
5. routing decision.

The first implementation may run entirely on one machine, but it should still use these concepts internally.

### Request

A request is what the user sends to the cluster.

At first, the only supported request type should be a simple chat request.

A request should contain only what is needed to process it.

A minimal request may include:

* request type;
* prompt or messages;
* requested capability;
* optional constraints;
* optional metadata that does not expose private content unnecessarily.

Examples of requested capabilities:

* `chat`;
* `code`;
* `summarization`.

Examples of constraints:

* local execution only;
* prefer fast response;
* require a specific minimum context size.

The request format does not need to be final.

It only needs to be explicit enough for routing decisions to exist.

### Capability

A capability describes what the cluster can do for the user.

A capability is not a model name.

A capability is not a runtime name.

A capability is not a machine name.

For the first implementation, capabilities should remain simple strings or simple structured values.

Examples:

* `chat`;
* `code`;
* `embeddings`;
* `vision`;
* `local-only`;
* `fast-response`;
* `large-context`.

The early capability model should be boring and easy to inspect.

It should not try to become a taxonomy of all AI tasks.

The goal is only to let the orchestrator ask:

> What does this request need?

and then find an available node that can satisfy it.

### Node

A node represents a machine or process that can handle AI work for the cluster.

In the first implementation, there may be only one node: the local machine.

Even so, that local machine should be represented as a node.

A minimal node description may include:

* node id;
* human-readable name;
* availability;
* health status;
* supported capabilities;
* available runtime adapters;
* available models;
* basic memory information;
* optional basic hardware information.

The node description should expose what the cluster needs to make routing decisions.

It should not expose unnecessary system details.

It should not inspect user files.

It should not collect more data than needed.

### Runtime adapter

A runtime adapter translates between Home AI Cluster and a specific AI runtime.

The orchestrator should not know runtime-specific details unless they are part of a stable adapter interface.

An adapter should be responsible for:

* reporting the capabilities it can provide;
* reporting available models when needed;
* accepting a normalized request;
* calling the underlying runtime;
* returning a normalized result;
* reporting basic health or availability.

The first adapter may be for Ollama.

But the core architecture must not become Ollama-shaped.

A future adapter for llama.cpp, vLLM, MLX, or another runtime should be possible without changing the core concepts.

### Routing decision

A routing decision records how the orchestrator chose where to send a request.

At first, routing can be extremely simple.

For example:

1. find nodes that are available;
2. filter nodes by requested capability;
3. choose the first matching node;
4. call its adapter;
5. return the result.

Even this simple decision should be represented explicitly.

A minimal routing decision may include:

* selected node id;
* selected adapter;
* selected capability;
* reason;
* fallback information, if any;
* failure reason, if no node can handle the request.

The user does not need to choose the node manually.

But the system should be able to explain which node handled the request and why.

### Result

A result is the normalized response returned by the cluster.

A minimal result may include:

* response content;
* request id;
* selected node id;
* selected adapter;
* routing explanation;
* error information, if applicable.

Prompts and responses should not be logged by default.

Routing metadata may be kept when useful, but it should not require storing private request contents.

## Minimal first flow

The first implementation should support this flow:

```text
user request
  -> orchestrator endpoint
  -> normalized request
  -> routing decision
  -> selected node
  -> selected runtime adapter
  -> runtime response
  -> normalized result
  -> user response
```

For Phase 1, the selected node may always be the local node.

That is acceptable.

The important point is that the code already has a place for routing.

The first implementation proves the shape of the system.

The later two-machine version proves the idea of the project.

## First implementation constraint

The first implementation should be allowed to be fake in distribution, but not fake in architecture.

This means:

* it may have only one local node;
* it may have only one adapter;
* it may have only one request type;
* it may use static configuration;
* it may use a simple in-memory registry;
* it may use a naive routing algorithm.

But it should not:

* call a runtime directly from the public endpoint without an adapter;
* hard-code a model as if it were the core abstraction;
* hard-code a machine name as if routing did not exist;
* log prompts by default;
* require a cloud service;
* require a dashboard;
* require distributed networking before the architecture is clear.

## Rationale

This proposal supports the existing project principles.

It keeps user simplicity above developer convenience by preserving one endpoint and hiding per-machine decisions from the default user flow.

It keeps the project local-first because the first implementation can run entirely on local machines without accounts or cloud services.

It keeps privacy by default because routing metadata can exist without logging prompt contents.

It keeps capabilities above brand names because routing begins from what the request needs, not from which model or machine happens to exist first.

It keeps engine independence because runtime details are isolated behind adapters.

It keeps automatic behavior explainable because routing decisions are explicit objects rather than invisible side effects.

It keeps the first step small enough to build.

## Alternatives considered

### Start as a direct Ollama wrapper

This would be the fastest way to get a response from a local model.

It is rejected as the core shape because it would make the first architecture runtime-centered.

Ollama may be the first adapter, but it should not define the project.

### Start with two-machine networking immediately

This would feel closer to the final proof.

It is rejected as the first step because networking, discovery, trust, and failure handling would add complexity before the internal shape is stable.

The project should first prove that request normalization, adapter boundaries, and routing decisions exist.

### Start with a dashboard

This would make the project visible early.

It is rejected as the first step because a dashboard should reveal the system, not define it.

The first important work is orchestration, not interface design.

### Start with a full protocol specification

This would make the project feel serious.

It is rejected as the first step because it would likely create premature abstractions.

The first protocol should emerge from the minimal working flow.

## Trade-offs

This proposal adds some structure before the first code exists.

That makes the first implementation slightly slower than a direct runtime wrapper.

The extra structure is acceptable because it protects the core project idea.

The risk is over-abstraction.

To reduce that risk, the first implementation should keep every concept minimal and inspectable.

No component should be generalized before there is a real need.

The rule is:

> Name the seams early, but keep them simple.

## Impact

This RFC affects the first implementation of Home AI Cluster.

It also affects future RFCs about:

* agent responsibilities;
* node registration;
* capability modeling;
* runtime adapter interfaces;
* routing policy;
* OpenAI-compatible access;
* observability and trust.

It does not require changing the existing vision, foundations, principles, roadmap, or non-goals.

It gives the first code a shape that matches those documents.

## Open questions

The following questions remain open:

* What language should the first implementation use?
* What should the first endpoint path be?
* Should the first public API be custom or OpenAI-compatible?
* How should static node configuration be represented?
* What is the smallest useful adapter interface?
* What capability names should be supported first?
* How much routing metadata should be returned to the user by default?
* When should node discovery become necessary?

These questions should not block the RFC.

They should guide the first implementation discussion.

## Decision

Home AI Cluster starts with a minimal architecture made of request, capability, node, runtime adapter, routing decision, and result.
