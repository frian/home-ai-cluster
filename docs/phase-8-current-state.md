# Phase 8 Current State

Status: Draft

This document describes the current implementation and operator state after Phase 8.

It is descriptive, not architectural.

It records what currently exists so future changes can be reviewed against the accepted RFCs and the verified operator workflow.

## Accepted RFC references

This current state should be read against the accepted RFC set, especially:

- `RFC/RFC-0036-static-operator-preflight.md`;
- `RFC/RFC-0037-canonical-operator-workflow.md`;
- `RFC/RFC-0038-ordinary-static-multi-node-mode.md`.

The canonical operator documents are:

- `docs/operator-workflow.md`;
- `docs/phase-8-canonical-operator-workflow-proof.md`;
- `docs/phase-8-ordinary-static-multi-node-proof.md`.

## Current system shape

Home AI Cluster currently provides a static, local-first cluster architecture with:

- one native cluster chat endpoint;
- explicit node and adapter registries;
- capability-based routing;
- normalized runtime adapter results;
- routing explanations and request history without prompt logging by default;
- a read-only health command;
- a read-only static operator preflight;
- one ordinary explicit static multi-node process;
- one explicit static two-machine proof process;
- an optional compatibility endpoint kept separate from the native endpoint.

The ordinary local flow is:

```text
operator request
  -> native cluster endpoint
  -> orchestrator
  -> capability-based router
  -> declared local node
  -> runtime adapter
  -> external runtime
  -> normalized cluster result
```

The explicit two-machine proof flow is:

```text
operator request on the calling machine
  -> static proof process
  -> declared remote node
  -> receiving machine native endpoint
  -> receiving machine runtime adapter
  -> receiving machine external runtime
  -> normalized cluster result with remote attribution
```

The ordinary static multi-node flow is:

```text
operator request on the calling machine
  -> ordinary static multi-node process
  -> local candidate first
  -> accepted narrow fallback to one declared remote candidate when eligible
  -> normalized cluster result with cluster-owned attribution
```

## Canonical operator workflow

The shortest supported operator workflow is documented in:

```text
docs/operator-workflow.md
```

It defines exactly three modes:

1. ordinary local-only operation;
2. ordinary explicit static multi-node operation;
3. explicit historical two-machine proof operation.

The documented sequence covers preparation, preflight, health, startup, request execution, shutdown, recovery, process ownership, port ownership, and privacy boundaries.

## Current operator commands

The current operator-facing commands include:

```text
home-ai-cluster-preflight
home-ai-cluster-health
home-ai-cluster-static-cluster
home-ai-cluster-static-proof
```

The ordinary application is started directly with the existing ASGI server command documented in the canonical workflow.

External runtimes remain operator-owned and are prepared, started, stopped, and configured outside Home AI Cluster.

## Preflight boundary

`home-ai-cluster-preflight` performs static inspection only.

It currently validates one rule:

> Every adapter declared by a configured node resolves in the inspected adapter registry.

For local-only invocation, it inspects the local declaration. When both explicit
remote arguments are supplied, it also projects one declared remote node and
checks both nodes' adapter names against the same inspected adapter registry.
Neither mode does network or runtime observation.

It does not:

- contact a runtime;
- inspect runtime health;
- test a network path;
- test a supplied remote URL or LAN path;
- validate remote execution;
- start or stop any process;
- mutate configuration;
- repair any condition.

## Health boundary

`home-ai-cluster-health` observes the configured local runtime adapters through the existing health boundary.

It is distinct from preflight:

- preflight answers whether inspected static cluster facts are coherent;
- health answers whether the configured runtime adapter can currently be observed as available.

Health remains read-only and does not supervise, repair, retry, or restart runtimes.

## Verified operation

The Phase 8 operator proof has been completed and retained in:

```text
docs/phase-8-canonical-operator-workflow-proof.md
```

The verified facts are:

- the ordinary local-only path was followed without consulting source code;
- preflight ran before health and their distinct meanings were understood;
- one real request completed through the native local endpoint;
- two real machines used the same repository revision;
- the receiving endpoint was reached over one trusted LAN;
- one real request was routed through the static proof process;
- the routed result carried cluster-owned remote node attribution;
- the calling proof process was stopped before the receiving application;
- the retained record respected the documented privacy boundary.

No prompt, generated response, private address, machine name, hardware detail, local filesystem path, credential, raw exception, or personal detail is retained as proof evidence.

## Current operating modes

### Ordinary local-only operation

This is the normal supported mode.

The application, node registry, adapter registry, runtime adapter, and external runtime operate on one machine through loopback interfaces by default.

### Ordinary explicit static multi-node operation

This supported mode uses one calling-machine local node and one
operator-declared remote node. The declaration remains process-local, routing is
local-first with only the accepted narrow fallback, and all runtime and remote
process lifecycle remains operator-owned.

RFC-0038 repository implementation is complete. Real ordinary two-machine
operator verification remains pending in:

```text
docs/phase-8-ordinary-static-multi-node-proof.md
```

### Explicit two-machine proof operation

This remains a deliberate proof-only mode.

It requires:

- two manually prepared machines;
- the same repository revision on both machines;
- a trusted LAN;
- an explicitly supplied receiving endpoint;
- manual process startup and shutdown;
- temporary network exposure only when required;
- explicit removal of temporary firewall exposure when created.

The proof process does not turn the cluster into an automatically managed distributed system.

The historical proof remains retained until ordinary static multi-node operator
verification succeeds.

## Current lifecycle boundary

Home AI Cluster does not own the lifecycle of external runtimes or remote application processes.

Current operation remains manual:

- operators start required external runtimes;
- operators run preflight and health;
- operators start application processes;
- operators provide any explicit remote endpoint required by the selected mode;
- operators stop processes in the documented order;
- operators remove temporary network exposure when applicable.

There is no supervisor, daemon installation, remote control protocol, automatic recovery, or service manager integration.

## Current configuration boundary

The cluster still uses explicit static configuration and in-memory registries.

There is no:

- automatic node discovery;
- automatic model discovery;
- dynamic registration protocol;
- distributed configuration service;
- database-backed registry;
- new operator configuration format introduced by Phase 8.

## Current privacy boundary

The project remains local-first and privacy-first.

Current documentation and proof records do not retain:

- real prompts or generated responses;
- private LAN addresses;
- credentials or authorization values;
- real filesystem paths;
- machine names or hardware inventories;
- raw runtime exceptions;
- personal account details or secrets.

Request history remains metadata-oriented and does not log prompt contents by default.

## Deliberately not included

The current system does not include:

- automatic process supervision;
- remote process control;
- automatic node discovery;
- automatic model discovery;
- automatic retries or repair;
- production distributed operation;
- a dashboard;
- a local web UI;
- Docker or Kubernetes;
- a database;
- authentication;
- streaming;
- a generic runbook framework;
- a new configuration format.

## Pending ordinary-mode verification

The ordinary static multi-node repository implementation does not itself prove a
real two-machine run. The pending scaffold requires operator verification of
local-first behavior, the accepted narrow fallback, remote attribution,
loopback binding, privacy boundaries, and manual shutdown order before any
ordinary-mode success claim is made.
