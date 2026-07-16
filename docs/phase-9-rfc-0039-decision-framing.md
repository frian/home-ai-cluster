# Phase 9 RFC-0039 Decision Framing

Status: Draft

## Purpose

Frame the architectural decisions that RFC-0039 must make before Home AI Cluster
introduces a repeatable static cluster declaration.

This document is an investigation aid. It does not choose a declaration format,
configuration path, precedence rule, parser, schema, or implementation.

## Current accepted boundary

RFC-0038 accepts one ordinary static multi-node mode with:

- the existing local node;
- exactly one explicitly declared remote node;
- `remote_node_id` and `remote_base_url` supplied through narrow CLI arguments;
- local-first routing and the accepted narrow fallback;
- loopback-only exposure on the calling machine;
- operator-owned runtime and remote application lifecycle;
- no persistence of the remote base URL;
- no discovery, supervision, remote process control, database, or generic
  configuration abstraction.

Phase 9 does not reopen those boundaries. It asks how the same accepted static
cluster can be restarted without reconstructing its declaration by hand.

## Problem to solve

The verified ordinary static multi-node mode is usable, but repeated operation
requires the operator to rebuild the same startup arguments each time.

The smallest Phase 9 problem is therefore:

> How should one explicit, local, privacy-safe static cluster declaration be
> retained and supplied to the ordinary startup path without changing the
> accepted topology or authority boundaries?

## Required RFC decisions

RFC-0039 must make explicit decisions in the following areas.

### 1. Declaration source

Decide what operator-controlled source supplies the retained declaration.

The RFC must compare at least:

- one explicitly named local file;
- environment variables;
- a shell wrapper or command alias;
- continued CLI-only operation.

It must not assume automatic file discovery or a generic configuration search
path without separately justifying them.

### 2. Declaration scope

Decide whether the first retained declaration describes only the accepted
ordinary static topology or introduces a broader configuration domain.

The narrow default to evaluate is:

- existing local node remains repository-defined;
- zero or one explicit remote node;
- no arbitrary node list;
- no routing-policy configuration;
- no runtime lifecycle configuration.

### 3. Minimal retained facts

Decide the smallest facts that must be retained.

At minimum, RFC-0038 currently requires:

- `remote_node_id`;
- `remote_base_url`.

The RFC must decide whether any additional fact is truly required, rather than
adding fields for possible future use.

### 4. CLI relationship and precedence

Decide how the retained declaration relates to existing CLI arguments.

The RFC must define whether CLI values:

- remain an independent invocation mode;
- override declaration values;
- are rejected when a declaration is supplied;
- or are reduced to one explicit declaration-path argument.

Any precedence rule must be simple, visible, and deterministic.

### 5. Validation boundary

Decide which validation occurs before startup.

The RFC must preserve the accepted static preflight boundary:

- parsing and structural validation may occur locally;
- node IDs and adapter references may be checked statically;
- the remote URL must not appear in public normalized errors;
- loading the declaration must not contact the remote endpoint;
- no DNS, LAN, runtime, model, or remote health observation occurs while loading.

### 6. Privacy and retention

Decide how a retained remote base URL is handled without weakening the project’s
privacy boundary.

The RFC must address:

- whether the declaration is intended to be committed to the repository;
- whether example files use placeholders only;
- file permission guidance, if relevant;
- exclusion from request history and proof records;
- redaction from public errors and logs;
- prohibition of credentials and authorization values in the declaration.

### 7. Compatibility and migration

Decide how the new path coexists with the accepted RFC-0038 command contract.

The RFC must state:

- whether existing CLI startup remains supported;
- whether the ordinary command name changes;
- whether local-only startup remains unchanged and default;
- whether the historical proof command remains separate;
- what, if anything, is deprecated.

## Required non-goals

RFC-0039 must not introduce:

- automatic node or model discovery;
- arbitrary numbers of remote nodes;
- dynamic registration or membership;
- process supervision or remote process control;
- automatic runtime startup, shutdown, repair, or retries;
- routing-policy configuration;
- load balancing or scheduling policy;
- a distributed configuration service;
- a database;
- secrets, credentials, or authorization values in the declaration;
- internet-facing operation;
- a dashboard or web UI;
- Docker or Kubernetes;
- live reload or background configuration watching;
- a generic configuration framework for unrelated future features.

## Evaluation criteria

A proposal should be preferred when it:

1. solves repeated command reconstruction;
2. keeps topology explicit and operator-owned;
3. preserves local-only operation as the shortest default path;
4. preserves RFC-0038 routing, adapter, lifecycle, and privacy boundaries;
5. introduces the fewest new concepts and precedence rules;
6. can be explained and validated without network observation;
7. avoids turning one narrow declaration into a generic configuration system.

## Questions RFC-0039 should answer

1. What exact operator action selects the retained declaration?
2. What exact data is allowed in the first declaration?
3. Is the declaration explicitly named or automatically discovered?
4. Can CLI topology arguments and a declaration be used together?
5. If both are allowed, which source wins and why?
6. What failures stop startup before the application binds its endpoint?
7. How are private endpoint values kept out of errors, logs, history, and proof?
8. Does the existing `home-ai-cluster-static-cluster` command remain unchanged?
9. Does this increment need a schema version, and what concrete problem would it
   solve now?
10. What future extensions are deliberately made impossible or deferred?

## Completion condition

This framing is complete when RFC-0039 can make one narrow decision that enables:

> One operator can restart the same explicit static cluster without rebuilding
> its declaration by hand.

The RFC must remain narrow enough that implementation does not require discovery,
supervision, a database, or a generic configuration subsystem.
