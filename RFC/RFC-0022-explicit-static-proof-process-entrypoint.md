# RFC-0022: Explicit Static Proof Process Entrypoint

Status: Draft

Date: 2026-07-11

Author: frian

## Summary

Home AI Cluster now has the accepted static two-machine proof architecture and
an opt-in `/v1/chat` integration, but no executable process setup constructs the
HTTP proof wiring outside tests.

This RFC proposes one dedicated proof-only process entrypoint.

The entrypoint requires the operator to provide exactly one remote transport
address explicitly on the command line. It constructs one manually declared
remote node, one HTTP remote transport, and an application with
`StaticRemoteProofWiring` enabled.

The proof entrypoint uses `declared-remote-only` selection so a request sent to
its `/v1/chat` endpoint visibly crosses the declared remote boundary.

The default application remains local-only.

This RFC does not introduce a general configuration system.

## Problem

RFC-0020 accepts the minimal static two-machine proof:

```text
One endpoint. Two machines. One routed request.
```

RFC-0021 accepts explicit caller-owned in-memory proof wiring. The repository
now contains the required wiring, orchestration, HTTP transport, and explicit
`/v1/chat` opt-in integration.

However, the ordinary application still starts with no proof wiring:

```text
create_app()
  -> no StaticRemoteProofWiring
  -> /v1/chat remains local-only
```

Tests can construct proof wiring directly, but an operator cannot yet start a
real proof process through a small supported repository entrypoint.

Choosing how the process receives the remote address, who owns the HTTP client,
and which candidate selection mode demonstrates the proof are architectural
setup decisions. They should be explicit before implementation.

## Goals

This RFC should:

- define the smallest executable process setup for the static two-machine proof;
- keep the ordinary application local-only;
- require explicit operator intent before remote routing is enabled;
- require exactly one manually declared remote node;
- require the remote transport address explicitly at process startup;
- reuse `StaticRemoteProofWiring` and the accepted orchestration seams;
- use the existing HTTP remote transport boundary;
- make the remote proof obvious and deterministic;
- give the proof process clear ownership of HTTP client lifetime;
- remain local-first, privacy-first, engine-independent, and boring.

## Non-goals

This RFC does not:

- define a general configuration format;
- load configuration files;
- read remote membership from environment variables;
- introduce persistence;
- introduce dynamic discovery;
- introduce registration;
- introduce daemon-owned mutable registry state;
- introduce retries;
- introduce fallback after remote failure;
- introduce health probing;
- introduce scoring or scheduling;
- introduce multiple remote nodes;
- introduce authentication or encryption policy;
- introduce Docker or Kubernetes;
- introduce a dashboard;
- introduce a database;
- introduce an OpenAI-compatible API;
- introduce cloud execution;
- replace the default application entrypoint;
- define production deployment.

## Proposal

Home AI Cluster should add one dedicated proof-only process entrypoint.

The entrypoint is separate from the default local-only application startup. It
must be invoked explicitly by the operator.

Its process setup should:

1. require one remote transport address as a command-line argument;
2. construct one manual `RemoteNodeDeclaration` for the `chat` capability;
3. create one process-owned `httpx.AsyncClient`;
4. wrap that client in `HttpRemoteTransport`;
5. construct `StaticRemoteProofWiring` in memory;
6. use `RoutingCandidateSelectionMode.DECLARED_REMOTE_ONLY`;
7. create the FastAPI application through `create_app(...)` with that wiring;
8. close the HTTP client when the application process shuts down.

The proof entrypoint should expose the same `/v1/chat` endpoint as the default
application. The receiving machine continues to expose
`/internal/cluster/request`, which remains strictly local.

The resulting proof path is:

```text
operator starts explicit proof entrypoint
  -> required remote address argument
  -> one manual remote declaration
  -> process-owned HttpRemoteTransport
  -> create_app(static_remote_proof_wiring=...)
  -> /v1/chat
  -> declared-remote-only selection
  -> HTTP /internal/cluster/request on declared machine
  -> local adapter execution on receiving machine
```

Without this dedicated entrypoint, the existing application remains:

```text
create_app()
  -> no proof wiring
  -> /v1/chat local-only
```

## Explicit Startup Boundary

Remote routing must not be enabled by importing the package, constructing the
default application, or starting the existing application entrypoint.

The proof process starts only through an explicit proof command.

The remote address must be supplied directly by the operator at startup. The
first proof should not infer it, discover it, read it from a registry, or load it
from a configuration file.

A command-line argument is chosen because it is visible, temporary, caller-owned,
and requires no configuration format or persistence.

The address is transport metadata. It is not discovery, identity, registration,
or proof of trust.

## Selection Mode

The first executable proof should use `declared-remote-only`.

This makes the proof unambiguous:

- a successful response demonstrates that the request crossed the declared
  remote boundary;
- local eligibility cannot hide a broken remote setup;
- no runtime fallback occurs;
- remote failure remains visible.

Other accepted selection modes remain available to tests and future explicit
setups, but this proof entrypoint should not expose a selection-mode option.
Doing so would add unnecessary surface area to the first proof.

## HTTP Client Lifetime

The proof process owns the `httpx.AsyncClient` used by `HttpRemoteTransport`.

The client should be created as part of explicit application process setup and
closed during application shutdown.

It must not be a hidden module-global client.

The exact FastAPI lifespan implementation is an implementation detail, provided
that ownership and shutdown remain explicit and testable.

## Failure Behavior

Startup should fail explicitly when the required remote address is missing or
invalid for constructing the manual declaration.

Runtime remote transport failure remains explicit.

The proof entrypoint must not:

- retry the remote request;
- fall back to local execution;
- select another node;
- contact another address;
- hide an invalid remote response.

Existing explicit transport and orchestration errors remain the source of truth.
Any HTTP response mapping beyond the current behavior is a separate decision.

## Privacy and Trust Boundaries

The ordinary application remains local-only.

Request contents may cross a machine boundary only when the operator explicitly
starts the proof entrypoint with one manually supplied remote address.

Only the manually declared remote node may be contacted.

Unknown or undeclared machines must never be contacted.

This proof does not claim that reachability establishes trust. The operator is
responsible for choosing the declared machine and network boundary used for the
proof.

## Rationale

A dedicated command-line proof entrypoint is the smallest boring bridge between
the accepted architecture and a real two-machine demonstration.

It avoids committing the project to a configuration file, environment-variable
schema, service manager integration, deployment system, or discovery protocol.

Using `declared-remote-only` keeps the proof honest. Success means remote
execution worked. Failure remains visible instead of being masked by local
fallback.

Explicit process ownership of the HTTP client avoids hidden global resources and
makes shutdown behavior understandable.

## Alternatives Considered

### Load a configuration file

Rejected for the first proof. This would require decisions about format,
location, validation, precedence, and compatibility.

### Read the remote address from an environment variable

Rejected for this proof entrypoint. It is less visible at invocation and begins
to define an implicit configuration interface. Environment-based configuration
may be reconsidered separately.

### Hard-code a remote address in the repository

Rejected. Repository code must not contain one operator's machine address, and a
hard-coded address weakens the explicit caller-owned boundary.

### Extend the default application entrypoint

Rejected. The default must remain local-only. Remote proof behavior should be
visibly separate and explicitly invoked.

### Expose all selection modes as command-line options

Rejected for the first proof. The objective is to demonstrate one remote routed
request, not to create a general routing CLI.

### Use `prefer-declared-remote`

Rejected for this proof entrypoint. Although deterministic selection prefers the
remote candidate, it can select local when no remote candidate exists. The first
proof should fail rather than silently cease proving remote execution.

### Let callers provide an already-created HTTP client

Useful for tests and library-level composition, but insufficient as the complete
process decision. A supported process entrypoint still needs explicit lifetime
ownership.

## Trade-offs

A dedicated proof command duplicates a small amount of process startup logic.
That duplication is acceptable because it protects the default local-only path
and avoids premature general configuration.

A command-line remote address is less convenient than persistent configuration.
That inconvenience is intentional for a temporary static proof.

Using `declared-remote-only` means the proof process cannot serve locally when
the remote machine is unavailable. This is desirable because the proof should
remain honest and no fallback policy has been accepted.

This entrypoint is not production deployment. It is a deliberately narrow bridge
to validate the architecture on two real machines.

## Impact

If accepted, implementation may add:

- one dedicated proof process module or command;
- explicit construction of one manual remote declaration;
- explicit HTTP client and transport lifetime management;
- tests for startup wiring, default-local isolation, selected remote execution,
  and client shutdown;
- a short operator runbook for the two-machine proof.

The default application behavior does not change.

No configuration file, persistence, discovery, registration, retry, fallback,
health probing, scoring, scheduling, dashboard, database, container platform, or
cloud execution is introduced.

## Open Questions

- What exact command name should expose the proof entrypoint?
- Should the proof entrypoint use a fixed remote node identifier such as
  `declared-remote`, or require a second explicit command-line argument?
- Should host and port for the proof process itself remain standard server
  arguments or use fixed development defaults?
- Should the first operator runbook use LAN addresses only, or also document a
  private overlay network example?

## Decision

Pending.
