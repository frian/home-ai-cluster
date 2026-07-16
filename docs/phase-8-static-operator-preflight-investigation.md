# Phase 8 Static Operator Preflight Investigation

Status: Investigation

Date: 2026-07-16

## Purpose

This document investigates the smallest plausible first increment of Phase 8:
one read-only operator preflight for the existing static local cluster.

It does not define a command contract, create an RFC, authorize implementation,
or introduce a new configuration format.

Any architectural decision still requires a separate RFC.

## Phase 8 boundary

Phase 8 aims to make the existing static local cluster understandable and
repeatable as an ordinary operator workflow.

The first increment should improve operator understanding without taking
ownership of external processes or adding distributed infrastructure.

It must remain:

- local-first;
- privacy-first;
- engine-independent;
- capability-centered;
- static and explicit;
- read-only;
- single-process;
- non-distributed by default.

## Current repository facts

The repository already has two ordinary static registry factories in
`home_ai_cluster.api.wiring`:

- `create_static_local_node_registry()`;
- `create_static_runtime_adapter_registry()`.

These factories are already used by the local health snapshot command and are
the narrowest repository-owned source of ordinary configured node and adapter
facts.

The repository also has `home-ai-cluster-health`, implemented in
`home_ai_cluster.local_health_snapshot`.

That command combines two distinct kinds of information:

1. static declared node facts;
2. direct runtime adapter health observations.

For every adapter declared by a node, the health command resolves the adapter in
the local registry and calls `adapter.health()` when the adapter exists.

This means the health command is not a static preflight. It intentionally
performs runtime observation.

## Static facts already available

Without network access or runtime probing, the existing registries can expose:

- configured node ids and names;
- declared node availability metadata;
- declared node health metadata;
- declared capabilities;
- declared adapter names;
- registered adapter names;
- whether a declared adapter name resolves in the adapter registry.

These facts are sufficient to detect at least one useful configuration
inconsistency:

> a node declares an adapter name that is absent from the inspected adapter
> registry.

This is already represented as `missing` by the health snapshot, but detecting
it does not require calling any runtime.

## What is not statically knowable

A static preflight cannot truthfully determine:

- whether an external runtime process is running;
- whether a runtime URL is reachable;
- whether a remote machine is reachable;
- whether a model is currently loaded or available;
- whether a request would execute successfully;
- whether a node is currently routable;
- whether credentials or transport configuration are valid;
- whether a later runtime call will fail.

Those are runtime or network observations and belong outside a static preflight.

## Relationship with health

The preflight and health surfaces should remain distinct.

A static preflight would answer:

> Are the repository-owned static declarations internally coherent?

The existing health command answers:

> What do the ordinary static declarations say, and what did each declared
> adapter report during this invocation?

The preflight must not call `adapter.health()` indirectly or reuse a projection
that does so.

The boring implementation seam would be to inspect the same registries while
performing only registry and declaration checks.

## Operating mode question

The roadmap distinguishes local-only operation from distributed-proof
operation.

The ordinary registry factories currently represent the ordinary local default.
Distributed behavior has remained explicit and proof-only through separate proof
paths and settings.

The first preflight should not silently activate or discover distributed
configuration.

A later RFC must decide whether the first contract:

1. validates only the ordinary local static registries; or
2. accepts one explicit proof-mode input that constructs the already-existing
   distributed proof registries without changing their opt-in nature.

The first option is smaller and safer.

The second option may be justified only if the repository already has one clear,
non-mutating proof configuration seam that can be reused without defining a new
configuration system.

## Candidate validation rules

A later RFC could consider a deliberately small set of rules:

- at least one node declaration exists;
- every declared node adapter name resolves in the inspected adapter registry;
- every declared capability name is non-empty;
- every node id is non-empty and unique;
- every registered adapter name is non-empty and unique;
- the reported operating mode is explicit and derived from the selected static
  registry construction path.

This list is investigative, not accepted.

Rules should be limited to invariants already implied by existing models and
registries. The project should not invent a new configuration policy merely to
make the command appear more comprehensive.

## Candidate output shape

A useful first output could remain one compact JSON object on stdout with:

- one overall status;
- one explicit operating mode;
- a prompt-free summary of configured node families, capabilities, and adapter
  names;
- a bounded list of static inconsistencies using safe stable reasons.

The output should not expose:

- runtime URLs;
- authorization values;
- prompts or responses;
- model contents;
- filesystem paths;
- private machine details;
- raw exceptions.

The exact fields, statuses, ordering, and exit behavior are architectural
contract decisions and therefore belong in a later RFC.

## Failure boundary

The preflight should distinguish between:

- a successfully constructed report containing static inconsistencies; and
- inability to construct the report at all.

A configuration inconsistency should likely be represented as report data and
produce a non-zero operator result, but the exact contract remains undecided.

Unexpected construction failures should remain safe CLI errors without leaking
raw exception details.

## Reuse boundary

The first implementation should prefer direct reuse of:

- existing node and adapter registry types;
- existing ordinary static registry factories;
- existing node, capability, and adapter names;
- existing compact JSON CLI conventions;
- existing safe-error conventions.

It should not create:

- a generic validation framework;
- a generic diagnostics abstraction;
- a configuration loader abstraction;
- a health/preflight superclass;
- a plugin system;
- a retained status model.

Name the smallest operator seam and keep it local.

## Explicit non-goals

The first preflight must not become:

- a runtime health probe;
- a network probe;
- node discovery;
- model discovery;
- process detection;
- process startup or shutdown;
- service supervision;
- remote process control;
- configuration mutation;
- installation or deployment tooling;
- a daemon;
- an HTTP endpoint;
- a dashboard;
- a database;
- a replacement for `home-ai-cluster-health`.

## Main finding

The repository already has a suitable static source boundary: the ordinary node
and adapter registry factories.

The existing health command proves that these registries can be projected for an
operator, but it is not itself the right preflight seam because it deliberately
calls runtime adapter health methods.

The smallest justified Phase 8 architectural question is therefore:

> Should Home AI Cluster add one explicit read-only CLI command that validates
> the internal coherence of the ordinary static node and adapter registries
> without runtime or network observation?

## Recommended first RFC scope

A first Phase 8 RFC should decide only:

- whether the command exists;
- whether the first contract is local-only;
- the exact static validation rules;
- the JSON projection;
- stable safe reasons;
- stdout, stderr, and exit-code behavior;
- privacy exclusions;
- proof requirements.

It should explicitly defer distributed-proof input unless one existing seam can
be reused without a new configuration contract.

## Proof candidate

A later implementation proof could use injected in-memory registries to show:

1. one coherent ordinary local configuration succeeds;
2. one node declaring a missing adapter produces a static inconsistency;
3. no adapter `health()` or `chat()` method is called;
4. output contains no runtime URL, prompt, response, raw exception, or private
   machine detail;
5. the ordinary application and health command remain unchanged.

A separate live-runtime proof should not be required for a purely static
contract.

## Recommended sequence

1. Review and merge this investigation.
2. Draft a narrow RFC for a local-only static operator preflight.
3. Review and merge the RFC proposal.
4. Accept the RFC separately.
5. Let an implementation agent implement only the accepted contract.
6. Record a static proof and reassess the next Phase 8 operator gap.

## Conclusion

The first Phase 8 increment should remain smaller than health observation and
much smaller than lifecycle automation.

One read-only local static preflight can add real operator value by exposing
whether the repository-owned node and adapter declarations are internally
coherent before any request or runtime probe occurs.

The repository already contains the required facts and seams. What remains is a
small operator contract, which must be decided by RFC before implementation.
