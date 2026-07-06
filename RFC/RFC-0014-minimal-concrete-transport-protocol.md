# RFC-0014: Minimal Concrete Transport Protocol

Status: Draft

Date: 2026-07-06

Author: frian

## Summary

Home AI Cluster should use a single boring HTTP request as the first concrete
remote transport protocol.

The request may carry a normalized cluster request from the orchestrator to a
selected manually and statically declared remote node address over a local
network, and receive one of:

- a normalized cluster result;
- a normalized transport failure;
- a normalized runtime failure.

This RFC builds on RFC-0012 and RFC-0013.

It chooses the first concrete transport protocol needed after the minimal remote
transport boundary.

It does not implement remote execution.

It does not define authentication, TLS, retries, fallback, discovery,
registration, daemon lifecycle, health probing, runtime supervision, streaming,
or a general public node API.

## Problem

Home AI Cluster is moving toward the first meaningful proof:

```text
One endpoint. Two machines. One routed request.
```

The project is currently in Phase 2 and is intentionally still:

- single-process;
- local;
- static;
- non-distributed.

RFC-0012 defines the remote membership boundary:

```text
Only manually and statically declared remote nodes may be considered.
```

RFC-0013 defines the minimal remote transport boundary:

```text
A normalized cluster request may cross to a selected declared remote node
boundary and return a normalized cluster result or normalized failure.
```

RFC-0013 deliberately does not choose a concrete protocol, endpoint,
authentication model, daemon lifecycle, discovery, registration, retries,
fallback, health probing, runtime supervision, or remote execution
implementation.

The next architectural decision is narrower:

```text
What is the first concrete protocol shape allowed to satisfy that boundary?
```

Without this decision, future implementation could accidentally choose a
protocol by convenience, hide transport assumptions in code, expose a broader
node API than needed, or let runtime-specific request formats leak across the
cluster boundary.

The project needs a boring concrete transport choice before implementation work
starts, while still refusing to decide remote execution behavior too early.

## Goals

This RFC should:

- choose the first concrete remote transport protocol;
- keep the transport local-network oriented;
- build directly on RFC-0012 and RFC-0013;
- allow contact only with a manually and statically declared remote node
  address;
- ensure unknown or undeclared machines are never contacted;
- define one minimal internal transport endpoint;
- keep the endpoint narrow and cluster-internal;
- carry normalized cluster objects, not runtime-specific payloads;
- keep runtime-specific details behind adapters;
- return either a normalized cluster result, normalized transport failure, or
  normalized runtime failure;
- avoid introducing remote execution implementation;
- avoid introducing discovery, registration, health probing, retries, fallback,
  load balancing, streaming, authentication, TLS, or daemon lifecycle.

## Non-goals

This RFC does not define:

- remote execution implementation;
- full node public API;
- discovery;
- registration;
- health API;
- model inventory;
- runtime probing;
- runtime supervision or auto-start;
- daemon or process lifecycle;
- dynamic configuration or config file format;
- authentication;
- TLS;
- retry policy;
- fallback policy;
- load balancing;
- streaming;
- OpenAI-compatible API;
- dashboard;
- Docker;
- database;
- prompt or response logging by default;
- runtime-specific request formats in core;
- treating node id as address, credential, or cryptographic identity.

Future work in any of those areas requires a separate RFC.

## Proposal

Home AI Cluster should use HTTP as the first concrete protocol for the minimal
remote transport boundary defined by RFC-0013.

The first transport should be a single HTTP request over a local network from
the orchestrator to a manually and statically declared remote node address.

The request must carry a normalized cluster request.

The response must carry one of:

- a normalized cluster result;
- a normalized transport failure;
- a normalized runtime failure.

The transport must not carry runtime-specific payloads as core transport
semantics.

Runtime-specific details remain behind runtime adapters.

### Endpoint

The first internal transport endpoint should be:

```text
POST /internal/cluster/request
```

This endpoint is the minimal endpoint used to carry a normalized cluster request
to a selected declared remote node.

It is a cluster-internal transport endpoint.

It is not a general public node API.

It is not an OpenAI-compatible API.

It is not a runtime API.

It is not a discovery, registration, health, inventory, probing, or management
API.

### Minimal flow

The minimal conceptual flow is:

```text
user request
  -> orchestrator endpoint
  -> normalized cluster request
  -> routing decision
  -> selected manually declared remote node
  -> declared remote node address
  -> HTTP POST /internal/cluster/request
  -> remote node boundary
  -> normalized cluster result or normalized failure
  -> user response
```

This flow is conceptual only.

It does not imply that remote execution exists in production code today.

It does not define how a remote process is started, supervised, configured,
authenticated, encrypted, probed, retried, or upgraded.

### Declared remote node requirement

The orchestrator may use this HTTP transport only for a remote node that has
already been manually and statically declared as an allowed cluster member.

The remote node declaration must include or refer to the remote address needed
by the transport, once later representation work defines where that address is
stored.

The address is transport metadata for a declared node.

It is not node identity.

It is not proof of trust.

It is not discovery.

It is not registration.

Unknown or undeclared machines must never be contacted by this transport.

The transport must not scan, probe, infer, discover, or register machines.

Reachability must not become trust.

### Local-network orientation

This transport is local-network oriented.

It is intended for manually declared machines on a local personal network.

It does not define cloud transport.

It does not define hosted control planes.

It does not allow request contents to be sent outside the manually declared
local cluster boundary.

Future work may define different trust or transport boundaries for non-local
networks, but that is outside this RFC.

### Normalized cluster objects

The HTTP request body must represent a normalized cluster request.

The HTTP response body must represent a normalized cluster result or normalized
failure.

The concrete schema for those normalized objects is not defined by this RFC.

This RFC only decides that the HTTP transport carries cluster-facing normalized
objects, not runtime-specific request and response formats.

The core must not treat Ollama-shaped, llama.cpp-shaped, vLLM-shaped,
MLX-shaped, or other runtime-specific payloads as the transport contract.

Runtime-specific request formats, runtime-specific response formats, runtime
endpoint URLs, runtime failures, model names, and runtime availability remain
behind adapters.

### Failure boundary

The HTTP transport must normalize failures into one of the failure categories
defined by the remote transport boundary:

- normalized transport failure;
- normalized runtime failure.

A transport failure describes failure to carry the normalized request or
response across the HTTP transport boundary.

A runtime failure describes a runtime-side failure after the request has crossed
the remote node boundary and reached runtime adapter behavior.

Failure normalization must not introduce retry or fallback policy.

This RFC does not define status-code mapping, timeout policy, user-facing error
mapping, retry behavior, fallback behavior, or load balancing.

### What the endpoint does not define

The endpoint:

```text
POST /internal/cluster/request
```

does not define:

- a full node public API;
- discovery;
- registration;
- health API;
- model inventory;
- runtime probing;
- daemon lifecycle;
- authentication;
- TLS;
- retry;
- fallback;
- load balancing;
- streaming;
- OpenAI-compatible API.

Each of those requires a separate decision if the project later needs it.

## Rationale

HTTP is boring.

That is the main reason to choose it first.

It is inspectable, familiar, easy to test with `curl`, and easy to reason about
in small local deployments.

It also fits the existing Python, FastAPI, and httpx stack already used by the
project.

Choosing HTTP keeps the first concrete transport understandable without adding a
special protocol, code generator, persistent connection model, shell execution
surface, or discovery mechanism.

The proposal keeps the project aligned with RFC-0012. A remote node must already
be manually and statically declared before the orchestrator may contact it.
Unknown and undeclared machines remain outside the cluster.

The proposal keeps the project aligned with RFC-0013. The HTTP endpoint carries
normalized cluster objects across the minimal remote transport boundary and
returns a normalized result or failure.

The proposal preserves engine independence. The transport contract is not an
Ollama API, llama.cpp API, vLLM API, MLX API, or any other runtime API.
Runtime-specific details remain behind adapters.

The proposal also preserves local-first and privacy-first defaults. It does not
introduce cloud routing, hosted control planes, discovery scans, telemetry,
prompt logging, or response logging.

## Alternatives considered

### Keep transport abstract for longer

The project could keep RFC-0013's transport boundary abstract for another step.

That would avoid choosing too early, but it would leave the first implementation
to choose a protocol implicitly.

Because protocol shape affects endpoints, failure boundaries, testing, and
future compatibility, the project should make the concrete first choice in an
RFC before implementation.

### Use raw TCP

The project could define a small custom protocol over raw TCP.

That would avoid HTTP overhead and could be very small.

It is rejected for the first transport because it would require more custom
framing, debugging, testing, and operational knowledge than HTTP.

Raw TCP is also less inspectable with common tools.

### Use gRPC

The project could use gRPC for typed request and response contracts.

That may become useful later if the transport surface becomes larger or more
structured.

It is rejected for the first transport because it introduces more tooling,
generation, protocol assumptions, and operational complexity than the current
minimal boundary needs.

### Use WebSocket

The project could use WebSocket for long-lived bidirectional communication.

That may become useful later for streaming, events, or interactive sessions.

It is rejected for the first transport because this RFC does not define
streaming, subscriptions, health events, or bidirectional control.

A single request and response is enough for the first concrete transport
decision.

### Use SSH

The project could use SSH as the remote transport.

SSH is familiar to technical users and already solves some authentication and
encryption concerns.

It is rejected for the first transport because it would couple cluster request
transport to shell access, command execution shape, account setup, process
lifecycle, and host administration concerns.

Those are broader than the minimal cluster transport boundary.

### Start with discovery or registration

The project could define discovery or registration before choosing a concrete
request transport.

That is rejected because RFC-0012 already defines manual static declaration as
the current trust boundary.

Discovery and registration introduce identity, trust, lifecycle, filtering, and
dynamic-state questions before the project needs them.

Unknown or undeclared machines must not be contacted.

## Trade-offs

HTTP is not the smallest possible wire protocol.

That overhead is acceptable because the first proof values clarity,
inspectability, and boring operation over protocol minimalism.

HTTP is widely understood, but it can also imply a broader API surface than the
project wants. This RFC limits that risk by defining one internal transport
endpoint only.

Choosing HTTP before authentication or TLS is a deliberate narrowing of scope,
not a claim that security is solved. Later work must define the trust and
security model before any production-oriented remote execution behavior is
implemented.

The endpoint path may become a compatibility point. That is acceptable because
the path is narrow, internal, and directly tied to the minimal transport
boundary.

This RFC still does not make the system distributed by itself. That is
intentional. It chooses the protocol shape needed before implementation, but
does not implement the remote node, remote process, or execution behavior.

## Impact

This RFC affects future Phase 3 architecture and implementation review.

It does not require production code changes.

It does not require tests.

It does not change current single-process behavior.

It does not implement HTTP transport.

It does not modify runtime behavior.

It does not change node health, static node availability, runtime availability,
routing behavior, or runtime adapter boundaries.

If accepted, future work that introduces the first remote transport should use:

```text
POST /internal/cluster/request
```

over HTTP to carry normalized cluster objects between the orchestrator and a
selected manually and statically declared remote node address.

Future work that introduces authentication, TLS, endpoint schemas, timeout
policy, status-code mapping, daemon lifecycle, remote execution implementation,
discovery, registration, health probing, runtime probing, runtime supervision,
retries, fallback, load balancing, streaming, or a public node API must be
proposed separately.

## Open questions

- What exact normalized cluster request schema should cross this endpoint?
- What exact normalized cluster result and failure schemas should cross this
  endpoint?
- Where will the declared remote node address be represented?
- What minimal authentication or trust model is required before implementation?
- Is TLS needed for the first local-network implementation, or is another local
  trust boundary acceptable?
- What timeout and status-code mapping should be used?
- What process shape will receive this endpoint on a remote node?
- What is the smallest implementation that proves one endpoint, two machines,
  one routed request?

## Decision

Pending.
