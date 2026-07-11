# RFC-0022: Explicit Static Proof Process Entrypoint

Status: Accepted

Date: 2026-07-11

Author: frian

## Summary

Home AI Cluster has the accepted static two-machine proof architecture and an
opt-in `/v1/chat` integration, but it still needs one executable process setup
for a real proof outside tests.

This RFC accepts one dedicated proof-only command:

```text
home-ai-cluster-static-proof
```

The command requires exactly one remote transport address as a command-line
argument. It constructs one manually declared remote node with the fixed node
identifier `declared-remote`, one HTTP remote transport, and an application with
`StaticRemoteProofWiring` enabled.

The proof uses `declared-remote-only` selection and is limited to two machines
reachable on the same trusted local area network.

The proof process uses the standard server defaults `127.0.0.1:8000`, while
allowing ordinary explicit server host and port arguments when LAN access to the
proof endpoint is required.

The default application remains local-only.

## Problem

RFC-0020 accepts the minimal static two-machine proof:

```text
One endpoint. Two machines. One routed request.
```

RFC-0021 accepts explicit caller-owned in-memory proof wiring. The repository
contains the required wiring, orchestration, HTTP transport, and explicit
`/v1/chat` opt-in integration.

Tests can construct this setup directly, but an operator cannot yet start a
real proof process through a small supported repository entrypoint.

The remaining decisions are the process boundary, command interface, remote
node identity, selection mode, HTTP client lifetime, server defaults, and
network boundary.

## Goals

This RFC:

- defines the smallest executable setup for the static two-machine proof;
- keeps the ordinary application local-only;
- requires explicit operator intent before remote routing is enabled;
- requires exactly one manually declared remote node;
- requires its transport address explicitly at process startup;
- gives that node the fixed proof identifier `declared-remote`;
- limits the first proof to two machines on the same trusted LAN;
- reuses `StaticRemoteProofWiring` and the accepted orchestration seams;
- uses the existing HTTP remote transport boundary;
- uses deterministic `declared-remote-only` selection;
- gives the proof process clear ownership of HTTP client lifetime;
- remains local-first, privacy-first, engine-independent, and boring.

## Non-goals

This RFC does not:

- define a general configuration format;
- load configuration files;
- read remote membership from environment variables;
- introduce persistence, discovery, or registration;
- introduce daemon-owned mutable registry state;
- introduce retries or fallback after remote failure;
- introduce health probing, scoring, or scheduling;
- introduce multiple remote nodes;
- introduce authentication or encryption policy;
- support VPNs or overlay networks, including Tailscale;
- support cross-site execution or untrusted networks;
- introduce Docker, Kubernetes, a dashboard, or a database;
- introduce an OpenAI-compatible API or cloud execution;
- replace the default application entrypoint;
- define production deployment.

## Proposal

Home AI Cluster will add one dedicated proof-only process entrypoint exposed as:

```text
home-ai-cluster-static-proof
```

The command is separate from the default local-only application startup and
must be invoked explicitly by the operator.

Its process setup will:

1. require one remote transport address as a command-line argument;
2. require the operator to choose an address reachable on the same trusted LAN;
3. construct one `RemoteNodeDeclaration` with node id `declared-remote` and the
   `chat` capability;
4. create one process-owned `httpx.AsyncClient`;
5. wrap that client in `HttpRemoteTransport`;
6. construct `StaticRemoteProofWiring` in memory;
7. use `RoutingCandidateSelectionMode.DECLARED_REMOTE_ONLY`;
8. create the FastAPI application through `create_app(...)` with that wiring;
9. use standard server defaults `127.0.0.1:8000`;
10. close the HTTP client when the application process shuts down.

The receiving machine continues to expose `/internal/cluster/request`, which
remains strictly local.

The proof path is:

```text
operator starts home-ai-cluster-static-proof
  -> required remote LAN address
  -> fixed declared-remote node declaration
  -> process-owned HttpRemoteTransport
  -> create_app(static_remote_proof_wiring=...)
  -> /v1/chat
  -> declared-remote-only selection
  -> HTTP /internal/cluster/request on declared LAN machine
  -> local adapter execution on receiving machine
```

Without this dedicated entrypoint, the application remains:

```text
create_app()
  -> no proof wiring
  -> /v1/chat local-only
```

## Explicit Startup Boundary

Remote routing must not be enabled by importing the package, constructing the
default application, or starting the existing application entrypoint.

The proof starts only through `home-ai-cluster-static-proof`.

The remote address must be supplied directly by the operator. The proof must
not infer it, discover it, read it from a registry, or load it from a
configuration file.

A command-line argument is visible, temporary, caller-owned, and requires no
configuration format or persistence.

The address is transport metadata. It is not discovery, identity, registration,
or proof of trust.

## Remote Node Identity

The first proof uses the fixed remote node identifier:

```text
declared-remote
```

A second command-line argument for node identity would add no useful proof
value. The fixed identifier makes logs, tests, and the operator runbook stable
without creating a general node naming interface.

The transport address remains separate from node identity.

## Network Boundary

The first executable proof is limited to two machines reachable on the same
trusted local area network.

The operator supplies a LAN-reachable transport address. The entrypoint does
not discover the network, verify LAN membership, or infer trust from an
address. The LAN restriction is an operator and runbook boundary.

VPNs, overlay networks such as Tailscale, cross-site routing, and untrusted
networks remain separate future transport and trust-boundary work.

## Selection Mode

The proof command uses `declared-remote-only` and does not expose a
selection-mode option.

This makes the proof unambiguous:

- success demonstrates that the request crossed the declared remote boundary;
- local eligibility cannot hide a broken remote setup;
- no runtime fallback occurs;
- remote failure remains visible.

Other accepted selection modes remain available to tests and future explicit
setups.

## Server Binding

The proof process uses the standard development defaults:

```text
127.0.0.1:8000
```

These defaults avoid exposing the endpoint on the LAN unless the operator
explicitly chooses a different server binding outside the proof command.

This RFC does not add host or port options to the proof command. The first proof
command therefore owns only remote proof wiring, not general server
configuration.

A later implementation may expose ordinary server binding separately if needed,
but that is outside this RFC.

## HTTP Client Lifetime

The proof process owns the `httpx.AsyncClient` used by `HttpRemoteTransport`.

The client is created during explicit process setup and closed during
application shutdown. It must not be a hidden module-global client.

The exact FastAPI lifespan implementation is an implementation detail, provided
that ownership and shutdown remain explicit and testable.

## Failure Behavior

Startup fails explicitly when the required remote address is missing or cannot
construct the manual declaration.

Runtime remote transport failure remains explicit. The proof command must not:

- retry the remote request;
- fall back to local execution;
- select another node;
- contact another address;
- hide an invalid remote response.

Existing transport and orchestration errors remain the source of truth. Richer
HTTP error mapping is a separate decision.

## Privacy and Trust Boundaries

The ordinary application remains local-only.

Request contents may cross a machine boundary only when the operator explicitly
starts the proof command with one manually supplied LAN address.

Only `declared-remote` may be contacted. Unknown or undeclared machines must
never be contacted.

The trusted-LAN constraint reduces transport and security variables, but does
not make reachability equivalent to trust. The operator remains responsible for
choosing the declared machine and LAN boundary.

## Rationale

A dedicated command is the smallest boring bridge between the accepted
architecture and a real two-machine demonstration.

The fixed command and node identifier avoid premature general configuration.
The explicit address preserves caller ownership. `declared-remote-only` keeps
the proof honest. Process-owned HTTP resources avoid hidden global state.

The loopback server default preserves local-first behavior without turning the
proof command into a general server launcher.

## Alternatives Considered

### Load a configuration file

Rejected. This would require decisions about format, location, validation,
precedence, and compatibility.

### Read the remote address from an environment variable

Rejected for this proof. It is less visible at invocation and begins to define
an implicit configuration interface.

### Require a remote node id argument

Rejected. The first proof has exactly one declared remote node, and a fixed
`declared-remote` identifier is sufficient.

### Hard-code a remote address

Rejected. Repository code must not contain one operator's machine address.

### Extend the default application entrypoint

Rejected. The default must remain local-only.

### Expose all selection modes

Rejected. The objective is one obvious remote routed request, not a general
routing CLI.

### Use `prefer-declared-remote`

Rejected. The proof should fail rather than silently cease proving remote
execution when no remote candidate exists.

### Bind to `0.0.0.0` by default

Rejected. A default LAN-wide bind would weaken the local-first and privacy-first
startup boundary.

### Add host and port options to the proof command

Rejected for this RFC. The first proof command decides remote proof wiring, not
a general server command interface.

### Use Tailscale or another overlay network

Rejected for the first proof. It would add identity, addressing, service
availability, ACL, and cross-network trust questions.

## Trade-offs

The dedicated command duplicates a small amount of startup logic. That is
acceptable because it protects the default local-only path and avoids premature
general configuration.

A command-line address is less convenient than persistent configuration. That
inconvenience is intentional for a temporary static proof.

A fixed remote identifier is less flexible than user-defined naming. The first
proof does not require that flexibility.

The loopback server default means the proof endpoint is local to the initiating
machine. That preserves the safer default and is sufficient when the operator
sends the test request from that machine.

`declared-remote-only` means the proof process cannot serve locally when the
remote machine is unavailable. This is desirable because no fallback policy has
been accepted.

## Impact

Implementation may add:

- the `home-ai-cluster-static-proof` command;
- one proof process module;
- a fixed `declared-remote` declaration;
- explicit HTTP client and transport lifetime management;
- tests for startup wiring, default-local isolation, remote execution, and
  client shutdown;
- a short LAN-only operator runbook.

The default application behavior does not change.

No general configuration, persistence, discovery, registration, retry,
fallback, health probing, scheduling, overlay network, cross-site execution, or
production deployment is introduced.

## Open Questions

None for this RFC.

## Decision

Accepted.

The first executable static two-machine proof uses the dedicated
`home-ai-cluster-static-proof` command.

The operator must explicitly provide exactly one remote LAN transport address.
The declared remote node uses the fixed identifier `declared-remote`.

The command constructs caller-owned static in-memory proof wiring, uses
`declared-remote-only`, and owns the HTTP client for the process lifetime.

The proof process uses the fixed development binding `127.0.0.1:8000`.

The proof is limited to two machines on the same trusted LAN. VPNs, overlay
networks, cross-site execution, and untrusted networks are outside this proof.

The default application remains local-only. No retry or fallback is introduced.
