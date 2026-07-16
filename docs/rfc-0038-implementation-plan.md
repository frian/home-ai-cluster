# RFC-0038 Implementation Plan

Status: Draft

Date: 2026-07-16

## Purpose

This document defines the smallest implementation sequence for accepted
RFC-0038.

It does not introduce architectural decisions beyond RFC-0038. It identifies
which existing proof components can be reused, which assumptions must remain
proof-only, and how implementation should be split into focused pull requests.

## Current reusable components

The existing two-machine proof already provides several implementation pieces
that are valid outside the proof when their contracts are preserved:

- `RemoteNodeDeclaration` for one explicit remote node;
- `HttpRemoteTransport` for repository-owned HTTP transport;
- the remote declaration registry;
- routing-candidate composition across local and remote declarations;
- normalized remote request execution;
- cluster-owned node attribution;
- existing transport and remote-response failure normalization;
- ordinary local node and runtime-adapter registry construction;
- the native `/v1/chat` endpoint;
- existing routing explanation and request-history privacy boundaries.

These components should be reused without changing their accepted public
contracts.

## Proof-only assumptions that must not become ordinary behavior

The current static proof path also contains assumptions that belong only to the
proof:

- the fixed remote node ID `declared-remote`;
- proof-specific process and symbol names;
- positional remote-address invocation;
- `DECLARED_REMOTE_ONLY` candidate selection;
- proof-specific application-state names;
- error names and messages that describe a proof rather than an ordinary mode.

The ordinary static multi-node mode must not merely rename the proof command
while retaining these assumptions.

## Target ordinary shape

The accepted ordinary process should construct:

1. the existing local node;
2. the existing local runtime adapter;
3. one operator-declared remote node;
4. one repository-owned HTTP remote transport;
5. the existing router and accepted candidate-selection policy;
6. the existing native endpoint on loopback port `8000` by default.

The process should receive only:

```text
--remote-node-id <remote-node-id>
--remote-base-url <remote-base-url>
```

The local-only application remains unchanged and default.

## Implementation sequence

### PR 1 — Extract proof-neutral static remote composition

Create the smallest internal seam that can represent one local registry plus one
remote declaration without encoding proof selection policy.

This slice should:

- introduce proof-neutral internal naming for reusable wiring;
- preserve the existing proof command and behavior;
- keep candidate selection explicit at the caller;
- add focused tests proving no behavior change in the proof path.

It should not add the new operator command yet.

### PR 2 — Add ordinary static multi-node process

Add:

```text
home-ai-cluster-static-cluster
```

This slice should:

- validate the remote node ID and base URL before startup;
- construct one local and one remote declaration;
- use the existing normal routing and fallback policy;
- bind to loopback port `8000` by default;
- keep the remote URL process-local and non-persistent;
- expose the existing native `/v1/chat` endpoint;
- preserve the proof command unchanged.

### PR 3 — Add process-specific static preflight support

Allow the ordinary static multi-node process registries to be inspected with the
same RFC-0036 rule:

> Every adapter declared by a configured node resolves in the inspected adapter
> registry.

This slice must remain static only. It must not contact the remote endpoint,
resolve LAN reachability, inspect runtime health, or validate request execution.

No new distributed-health contract is introduced.

### PR 4 — Documentation and retained proof scaffold

Update the canonical operator workflow to describe three separate modes:

1. ordinary local-only operation;
2. ordinary explicit static multi-node operation;
3. explicit historical two-machine proof operation.

Add a privacy-safe proof scaffold for RFC-0038, but leave operator verification
pending until the real two-machine run is performed.

## Required tests

Implementation should include focused coverage for:

- valid remote node ID and base URL parsing;
- empty or duplicate remote node IDs;
- invalid or relative remote URLs;
- deterministic local-then-remote declaration order;
- unchanged local-only behavior;
- unchanged proof-only behavior;
- ordinary local selection when the local path is usable;
- existing fallback to the remote node when the local path is unavailable;
- remote node attribution;
- normalized remote transport and response failures;
- absence of the remote base URL from public errors and retained history;
- static preflight coherence without network access.

## Explicit implementation boundaries

The implementation must not add:

- a configuration file;
- environment-variable topology;
- more than one remote node;
- discovery or registration;
- direct node targeting;
- routing weights or priorities;
- a new scheduler;
- new retry behavior;
- background remote health polling;
- process supervision or remote control;
- authentication or internet-facing operation;
- a database, dashboard, Docker, or Kubernetes.

## Completion boundary

RFC-0038 implementation is complete only after:

- all focused repository checks pass;
- the ordinary local-only mode remains unchanged;
- the ordinary static multi-node mode is documented;
- one real local-plus-remote request is reproduced through existing fallback;
- remote attribution and normalized failure behavior are observed;
- a privacy-safe proof is retained without prompts, generated responses, private
  addresses, endpoint URLs, machine details, paths, credentials, or raw
  exceptions.
