# RFC-0015: Static Remote Declaration Source Boundary

Status: Accepted

Date: 2026-07-07

Author: frian

## Summary

Home AI Cluster should keep static remote node declarations caller-provided,
explicit, and in-memory for the next implementation step.

A caller may construct a `RemoteNodeDeclarationRegistry` directly and pass it to
an explicit opt-in orchestration seam.

This RFC does not introduce a configuration file, environment-variable loading,
discovery, registration, persistence, daemon-owned state, or active remote
execution.

The goal is to make the next step possible without accidentally choosing a full
configuration system too early.

## Problem

Home AI Cluster now has the following explicit opt-in remote-preparation pieces:

```text
orchestrate_request_with_declared_http_remote()
  -> HttpRemoteTransport
  -> POST /internal/cluster/request
```

The path is implemented, tested in-process, and documented, but it still needs a
source for declared remote nodes before a later implementation can move toward a
real two-machine proof.

RFC-0012 already decides that remote nodes must be manually and statically
declared.

RFC-0014 already decides that the first concrete transport uses HTTP and may
only contact manually and statically declared remote node addresses.

The next architectural question is narrower:

```text
Where may static remote declarations come from for the next step?
```

If the project does not answer this first, implementation work may accidentally
introduce a configuration file, environment-variable contract, discovery
mechanism, daemon-owned registry, or implicit trust boundary before the project
is ready for those decisions.

## Goals

This RFC should:

- define the allowed source of static remote declarations for the next step;
- keep declarations explicit and caller-owned;
- keep declarations in memory;
- allow tests and future opt-in wiring to construct `RemoteNodeDeclaration`
  values directly;
- avoid introducing a configuration format too early;
- avoid introducing config loading;
- avoid introducing discovery or registration;
- preserve the rule that unknown or undeclared machines must never be contacted;
- keep `/v1/chat` local-only unless a future RFC changes that boundary.

## Non-goals

This RFC does not define:

- a configuration file format;
- config loading;
- environment-variable loading;
- CLI flags;
- persistent storage;
- database-backed declarations;
- discovery;
- registration;
- health probing;
- reachability probing;
- trust establishment;
- authentication;
- TLS;
- retries;
- fallback;
- daemon lifecycle;
- runtime supervision;
- remote node public API;
- active remote execution in `/v1/chat`;
- OpenAI-compatible API behavior.

Future work in any of those areas requires a separate RFC.

## Proposal

For the next implementation step, static remote declarations may only come from
explicit caller-owned code.

The allowed source shape is:

```text
caller code
  -> RemoteNodeDeclaration values
  -> RemoteNodeDeclarationRegistry
  -> explicit opt-in orchestration seam
```

The caller may construct a `RemoteNodeDeclarationRegistry` directly and pass it
to an explicit helper such as `orchestrate_request_with_declared_remote()` or
`orchestrate_request_with_declared_http_remote()`.

The registry remains in-memory.

The registry is not loaded automatically.

The registry is not global process state.

The registry is not daemon-owned state.

The registry is not discovered from the network.

The registry is not persisted.

The registry is not populated from a config file, environment variables, a
database, a dashboard, or a remote service.

A remote declaration remains permission to consider a known remote node address
for an explicit opt-in path only.

A remote declaration is not proof of trust.

A remote declaration is not discovery.

A remote declaration is not registration.

A remote declaration is not reachability proof.

Unknown or undeclared machines must never be contacted.

This RFC allows future implementation work to add a small helper that returns a
static in-memory `RemoteNodeDeclarationRegistry`, but only when the declarations
are still explicit in code and not loaded from an external source.

## Rationale

The project is intentionally moving in small steps.

The next useful step is to make declared remote nodes expressible in code, not
to invent a complete configuration system.

Caller-provided in-memory declarations are boring, inspectable, and easy to test.
They keep the trust boundary visible at the call site and avoid hiding remote
addresses behind implicit loading behavior.

This preserves local-first and privacy-first defaults because nothing contacts a
machine unless the caller explicitly provides a declaration and chooses an
explicit opt-in orchestration seam.

It preserves engine independence because declarations describe cluster-facing
node and transport metadata, not runtime-specific details.

It also keeps the architecture aligned with RFC-0012, RFC-0013, and RFC-0014:
remote behavior is only allowed for manually and statically declared nodes, over
a normalized transport boundary, using the minimal internal HTTP endpoint.

## Alternatives considered

### Add a config file now

The project could define a file such as `remote_nodes.toml`, YAML, or JSON.

That is rejected for now because a file format becomes a compatibility surface
and starts broader configuration design before the project needs it.

The project has not yet decided config location, validation rules, secrets,
profiles, override behavior, reload behavior, or user-facing ergonomics.

### Use environment variables

The project could encode remote node addresses in environment variables.

That is rejected for now because it would still define an implicit loading
contract, naming scheme, precedence model, and operational behavior.

Environment variables are also awkward for structured node declarations.

### Add discovery or registration

The project could let nodes discover or register themselves.

That is rejected because it violates the current static remote declaration
boundary and introduces identity, trust, lifecycle, filtering, and dynamic-state
questions too early.

### Add a daemon-owned registry

The project could make a long-running process own the remote declaration
registry.

That is rejected for now because daemon lifecycle is explicitly out of scope.
The current project shape remains single-process, local, static, and
non-distributed.

### Keep the source undefined

The project could continue using remote declarations in tests without deciding
where they may come from.

That is rejected because the next implementation step risks choosing a source by
accident. A small RFC keeps the boundary explicit without over-designing it.

## Trade-offs

Caller-provided in-memory declarations are not ergonomic for users.

That is acceptable because this RFC is not defining user-facing configuration.
It defines a narrow architectural source boundary for the next implementation
step.

This approach may require another RFC later for a real configuration source.

That is intentional. A future config RFC can make better decisions once the
first explicit remote proof has clarified what configuration actually needs to
represent.

This approach keeps implementation simple but manual.

That manual nature is useful now because it makes remote contact explicit,
reviewable, and hard to trigger accidentally.

## Impact

This RFC affects future Phase 2 and Phase 3 implementation review.

If accepted, future work may add small helpers that construct static in-memory
remote declaration registries from explicit code.

Future work must not introduce config files, config loading, environment
loading, discovery, registration, persistence, daemon-owned registry state, or
active `/v1/chat` remote execution under this RFC.

This RFC does not require production code changes by itself.

It does not require tests by itself.

It does not change current runtime behavior.

It does not make the system distributed.

## Open questions

- What future RFC should define the first user-facing or developer-facing
  configuration source?
- Should a later config source live in a project file, user-local file, CLI flag,
  or another mechanism?
- What security boundary is required before remote execution becomes active
  beyond explicit tests or local development proofs?

## Decision

Accepted.

For the next implementation step, static remote declarations may only come from
explicit caller-owned code and remain in memory.

Callers may construct `RemoteNodeDeclaration` values directly, place them in a
`RemoteNodeDeclarationRegistry`, and pass that registry into explicit opt-in
orchestration seams.

This decision does not introduce configuration files, configuration loading,
environment-variable loading, discovery, registration, persistence,
daemon-owned registry state, or active `/v1/chat` remote execution.
