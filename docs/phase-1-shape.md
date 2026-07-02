# Current Phase 1 shape

Home AI Cluster is currently an early Phase 1 prototype.

Phase 1 runs as a single local process.

Requests go through one static local node and one Ollama runtime adapter.

The static local node is an internal routing concept.

It does not introduce:

* distributed behavior;
* node discovery;
* node registration;
* a node network protocol;
* model information in the node model;
* a public API change.

The public `/v1/chat` response shape remains unchanged.

This keeps the implementation aligned with the project rule:

> fake in distribution, but not fake in architecture.
