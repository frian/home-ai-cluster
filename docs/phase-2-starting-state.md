# Phase 2 Starting State

Status: Draft

This document describes the Phase 2 starting state after acceptance of the
Phase 2 node boundary.

It is descriptive, not normative.

It records what currently exists so future changes can be reviewed against the
accepted RFCs without treating this document as a new architecture decision.

## Accepted RFC references

This starting state should be read against:

- `RFC/RFC-0001-minimal-system-shape.md`;
- `RFC/RFC-0002-phase-1-implementation-stack.md`;
- `RFC/RFC-0004-minimal-node-model.md`;
- `RFC/RFC-0006-node-health-boundary.md`;
- `RFC/RFC-0007-runtime-availability-boundary.md`;
- `RFC/RFC-0008-phase-2-node-boundary.md`.

## Current shape

Phase 2 starts from a single-process implementation.

There is still one static local node. The implementation has not introduced a
remote node process, a node transport, or independent node lifecycle behavior.

The current flow remains:

```text
API request
  -> core orchestrator
  -> router
  -> static local node
  -> runtime adapter
  -> normalized cluster result
```

The node boundary is now explicit through static helpers. Those helpers make
the boundary visible in code without changing the operational shape of the
system.

## Current node boundary

The static node description remains the cluster-visible representation of the
local execution environment.

The `NodeRegistry` filters nodes by availability and requested capability only.
Node health is not part of routing selection.

The router uses adapter names declared by the selected node. It then selects a
registered runtime adapter with a matching name and requested capability.

Node health remains descriptive state. It can describe the node, but it does
not drive routing, fallback, retries, polling, supervision, or adapter
selection.

Runtime details remain behind runtime adapters. The core node boundary does not
depend on runtime endpoint URLs, runtime request formats, runtime process
state, model files, or runtime-specific failures.

## Deliberately not included

Phase 2 currently does not include:

- remote nodes;
- a node HTTP API;
- node discovery;
- a registration protocol;
- a node daemon;
- fallback;
- retries;
- health polling;
- runtime supervision;
- a database;
- a dashboard;
- Docker;
- an API compatibility layer.

Those remain outside the current implementation unless a future accepted RFC
defines their boundary.
