# RFC-0004: Minimal node model

Status: Draft

Date: 2026-07-02

Author: frian

## Summary

Home AI Cluster should define a minimal node model before introducing real multi-machine behavior.

A node represents a machine or process that can provide AI work to the cluster.

The node model should describe what the cluster needs to know in order to route requests by capability, while avoiding unnecessary system inspection, distributed behavior, discovery, persistence, or configuration complexity.

For the next implementation steps, a node may still be static and local.

The important decision is conceptual:

> The code may still be fake in distribution, but it should not be fake in architecture.

## Problem

Home AI Cluster already has a minimal Phase 1 flow:

```text
HTTP request
  -> API layer
  -> core request
  -> router
  -> runtime adapter
  -> runtime result
  -> normalized response
```

The project also already has a runtime adapter boundary.

However, the node concept is still mostly implicit.

RFC-0001 defines nodes as one of the core concepts of the system, and the roadmap points toward a future proof of:

```text
One endpoint. Two machines. One routed request.
```

Before the project can introduce real agents, registration, discovery, or node-to-orchestrator communication, it needs a small shared definition of what a node is.

Without a minimal node model, future code may accidentally confuse:

* a node with a machine name;
* a node with a runtime;
* a node with an adapter;
* a node with a model;
* a node with a network service;
* a node with a full system inventory.

That would make the project harder to keep capability-centered, privacy-first, and engine-independent.

## Goals

This RFC should define the smallest useful node model for Home AI Cluster.

It should:

* define what a node represents;
* define the minimal information a node may expose;
* preserve capability-based routing;
* keep runtime-specific details behind adapters;
* support a single-machine Phase 1 implementation;
* prepare for a later two-machine proof;
* avoid premature distributed-system complexity;
* avoid unnecessary system inspection;
* preserve local-first and privacy-first defaults.

## Non-goals

This RFC does not define:

* an agent process;
* a node network protocol;
* automatic node discovery;
* node registration;
* heartbeats;
* health-based routing;
* fallback behavior;
* distributed execution;
* a dashboard;
* persistence;
* authentication or authorization;
* a configuration file format;
* environment variable configuration;
* model download or placement;
* detailed hardware inventory;
* telemetry;
* prompt or response logging.

Those decisions can come later.

This RFC only defines the minimal node description that early code should be allowed to use.

## Proposal

Home AI Cluster should define a node as:

> A node is a cluster-visible description of a machine or process that can provide one or more AI capabilities through one or more runtime adapters.

For now, a node description should be static and small.

It should contain only information needed for early routing and explanation.

A minimal node description should include:

* `id`;
* `name`;
* `availability`;
* `health`;
* `capabilities`;
* `adapters`;
* `models`.

The exact Python model names may be decided during implementation, but the concepts should remain visible.

### Node identity

A node should have a stable `id` inside the current cluster context.

For Phase 1, the local node may use an id such as:

```text
local
```

The id is not a global identity system.

It is not a cryptographic identity.

It is not a discovery name.

It is only the identifier the orchestrator can use in routing decisions and results.

A node should also have a human-readable `name`.

For Phase 1, this may be simple, such as:

```text
Local node
```

The name is for humans.

The id is for stable references inside the cluster.

### Availability

A node should expose whether it is currently considered available for routing.

For early versions, availability should be simple.

Possible values may include:

* `available`;
* `unavailable`;
* `unknown`.

This RFC does not define health-based routing.

It only allows the system to represent whether a node should be considered usable.

### Health

A node should expose minimal health information.

Health should remain boring and small.

For Phase 1, health may be derived from the runtime adapter health already available.

The model should not require continuous monitoring, background polling, heartbeats, persistence, or system telemetry.

A node health value may describe:

* whether the node appears healthy;
* whether its required local adapter is reachable;
* a short reason when it is not healthy.

The health model should not include prompt contents or response contents.

### Capabilities

A node should expose the capabilities it can provide.

Capabilities remain the core abstraction of Home AI Cluster.

Examples include:

* `chat`;
* `embeddings`;
* `vision`;
* `code`.

For Phase 1, `chat` may be the only supported capability.

The node model should not require a final capability ontology.

It should only allow the router to ask:

> Which available node can satisfy this requested capability?

### Adapters

A node should expose the runtime adapters it can use.

For Phase 1, the local node may expose only:

```text
ollama
```

The node model should not expose Ollama-specific request formats, options, endpoints, or response shapes.

Those remain behind the runtime adapter interface.

The node may say:

> I can provide chat through the Ollama adapter.

The core should not need to know how Ollama provides that chat capability.

### Models

A node may expose available models when that information is useful for transparency or future routing.

For Phase 1, this may be a small list such as:

```text
llama3.2
```

However, models must remain implementation details.

The router should not become model-centered.

A model list should help explain or inspect what a node can provide, but it should not replace capabilities as the primary routing concept.

### Privacy boundaries

A node description should not expose more than the orchestrator needs.

It should not include:

* user files;
* environment variables;
* process lists;
* prompt contents;
* response contents;
* full hardware inventory;
* detailed operating system telemetry;
* network scans;
* account information.

The safest default remains:

> Do not collect what is not needed.

The node model should describe what the node can do, not everything the node is.

### Phase 1 local node

The current Phase 1 implementation may continue to run on one machine.

It may define one static local node.

That is acceptable.

The important point is that the local node should be represented using the same conceptual shape that can later support more nodes.

A possible Phase 1 node description could be:

```json
{
  "id": "local",
  "name": "Local node",
  "availability": "available",
  "health": "healthy",
  "capabilities": ["chat"],
  "adapters": ["ollama"],
  "models": ["llama3.2"]
}
```

This example is illustrative.

It is not a final protocol.

### Relationship to routing

Routing should remain capability-centered.

A simple router may use the node model like this:

1. start from the requested capability;
2. find available nodes;
3. filter nodes by capability;
4. choose the first matching node;
5. call the selected adapter;
6. return a normalized result.

This RFC does not require changing the current router.

It only defines the node information that later routing code should be able to use.

### Relationship to adapters

Runtime adapters remain responsible for runtime-specific behavior.

A node description may mention that an adapter exists, but it should not absorb adapter responsibilities.

The node does not translate requests.

The adapter translates requests.

The node does not define runtime API shapes.

The adapter hides runtime API shapes.

The node announces what is available to the cluster.

The adapter performs work against a runtime.

## Rationale

This proposal supports the project foundations.

It keeps the project capability-centered by making capabilities part of the node description without making models, runtimes, or machines the primary abstraction.

It supports engine independence by keeping runtime details behind adapters.

It supports local-first operation because a single static local node is enough for Phase 1.

It supports privacy-first defaults because the node description is intentionally small and does not require system inspection or telemetry.

It supports boring solutions first because it avoids discovery, agents, protocols, dashboards, databases, and distributed behavior.

It supports the roadmap because the project needs a node concept before the later two-machine proof.

The main design rule is:

> Name the seam before crossing it.

A node model gives the project a seam for future multi-machine work without forcing that work into the current implementation.

## Alternatives considered

### Keep the node concept implicit

This would avoid adding a new model too early.

It is rejected because the project already speaks about nodes in its architecture and roadmap.

If the concept remains implicit, future changes may define it accidentally through code instead of deliberately through architecture.

### Treat a runtime adapter as a node

This would be simple for Phase 1 because there is currently one Ollama adapter.

It is rejected because it would confuse runtime concerns with cluster topology.

A node may have multiple adapters later.

An adapter is how Home AI Cluster talks to a runtime.

A node is what the cluster can route work to.

### Treat a model as a node

This is rejected because Home AI Cluster should not be model-centered.

Models are replaceable implementation details.

Capabilities remain the primary routing abstraction.

### Define a full agent protocol now

This would move faster toward Phase 2.

It is rejected for this RFC because protocol design would introduce networking, registration, trust, failure handling, and security questions too early.

The project should first define what a node is before defining how an agent announces one.

### Define detailed hardware inventory now

This would make future routing more powerful.

It is rejected because it would add privacy and complexity costs before they are justified.

Early routing does not need detailed hardware telemetry.

The node should describe what it can do, not expose everything about the machine.

## Trade-offs

This RFC introduces one more explicit concept before it is fully used.

That adds some structure.

The risk is premature abstraction.

The risk is acceptable because the node concept already exists in the project foundations and roadmap, and because this RFC keeps the model intentionally small.

The proposal makes future multi-machine work easier to discuss.

It makes Phase 1 slightly more structured than a direct adapter registry.

That structure is acceptable only if implementation remains boring:

* one local node is enough;
* static data is enough;
* no discovery is required;
* no agent is required;
* no network protocol is required;
* no persistence is required.

## Impact

This RFC affects future implementation work around:

* node descriptions;
* adapter registries;
* routing decisions;
* routing explanations;
* future agent responsibilities;
* future node registration;
* future two-machine routing.

It does not require changing the public API immediately.

It does not require changing the current Ollama adapter immediately.

It may later guide a small implementation PR that introduces a static local node description.

## Open questions

The following questions remain open:

* Should `availability` and `health` be separate models or one simple status?
* Should adapter capabilities live on the node, the adapter, or both?
* Should model names be included in the default API response?
* Should model information be optional in the node description?
* When should hardware information become useful enough to expose?
* What is the smallest future agent responsibility around node announcement?
* When should node ids become stable across restarts?

These questions should not block this RFC.

They should guide later RFCs and implementation discussion.

## Decision

Pending.
