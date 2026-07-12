# RFC-0026: Explicit Automatic Routing Proof Process

Status: Draft

Date: 2026-07-12

Author: frian

## Summary

This RFC proposes the smallest explicit real two-machine proof of the accepted
RFC-0025 automatic capability-routing policy. It adds one proof-only command:

```text
home-ai-cluster-automatic-proof
```

The command is separate from the ordinary local-only application and from
`home-ai-cluster-static-proof`, the accepted RFC-0022 caller-directed proof
path. The operator supplies exactly one remote transport address. The process
then composes, in memory, one nonmatching local side and one matching manually
declared remote candidate, with `local_only=false` only for this proof request.

The proof remains limited to two machines on the same trusted LAN. It proves
that the cluster-owned RFC-0025 policy selects the declared remote candidate as
the sole selectable exact `Capability("chat")` match, then executes it once.

## Problem

RFC-0025 is implemented in an explicit internal composition seam, but no real
two-machine proof of its automatic capability-selection behavior has been
recorded. The existing RFC-0022 proof demonstrates caller-directed
`declared-remote-only` selection; it cannot demonstrate that RFC-0025 chose a
remote candidate automatically because it was the sole selectable match.

The next proof must make remote movement explicit without changing ordinary
`/v1/chat`, creating a public remote-permission surface, or turning the static
proof into a general routing command.

## Goals

- Define one explicit, proof-only command for an RFC-0025 real-machine proof.
- Require one operator-supplied HTTP transport address for one manually
  declared remote node.
- Prove automatic selection of that node as the sole selectable `chat`
  candidate.
- Reuse the accepted automatic orchestration and selected-candidate execution
  seams.
- Preserve authoritative caller-owned `ClusterResult.node_id` attribution as
  `declared-remote`.
- Preserve ordinary local-only application behavior and the RFC-0022 proof
  path.
- Keep transport, declaration, request permission, and resource ownership
  explicit and process-owned.

## Non-goals

This RFC does not introduce:

- a change to ordinary `/v1/chat` or the ordinary application entrypoint;
- a change to RFC-0022 or `home-ai-cluster-static-proof`;
- caller-directed selection modes or general selection-mode options;
- arbitrary capability or node-identity command-line options;
- multiple local or remote candidates;
- fallback, retry, health-aware routing, health probing, scoring, scheduling,
  or load balancing;
- dynamic discovery, registration, persistence, configuration files,
  environment-variable configuration, or a database;
- authentication, HTTPS or TLS policy, encryption policy, trust protocols, VPN
  or overlay-network support, or cross-site or untrusted-network execution;
- Docker, Kubernetes, dashboards, public routing explanations, or production
  deployment; or
- prompt logging, a new result wrapper, or a changed internal endpoint
  contract.

## Proposal

### Dedicated process

Provide the proof-only command:

```text
home-ai-cluster-automatic-proof REMOTE_ADDRESS
```

`REMOTE_ADDRESS` is required and is exactly one absolute HTTP remote transport
address. The trusted-LAN proof is HTTP-only and does not introduce TLS
certificate or encryption-policy variables. The address identifies transport
metadata for the one manually declared remote node; it is not node identity,
discovery, registration, or trust by reachability. Missing or invalid input
fails explicitly before the proof process starts.

The process binds only to `127.0.0.1:8000`, matching the accepted static proof.
Only one proof process needs to run at a time. It is limited to two manually
prepared machines reachable on the same trusted LAN.

### Static proof composition

The dedicated process constructs the following explicitly and in memory:

- local node and adapter registries that produce no matching local `chat`
  candidate for the proof request, preferably empty registries;
- exactly one manually declared remote node, with id `declared-remote` and
  exact `Capability("chat")`;
- one remote-declaration registry containing that node;
- the one operator-supplied remote transport address;
- one process-owned `httpx.AsyncClient`;
- one `HttpRemoteTransport` using that client; and
- the accepted RFC-0025 automatic orchestration seam.

The process must not introduce a general way to choose local or remote
capabilities. Fixed `chat` and `declared-remote` are sufficient for this proof.

The existing RFC-0022 static-proof wiring cannot be reused unchanged because
it requires a caller-directed selection mode. The current ordinary `/v1/chat`
request construction also retains the default `local_only=true`. An
implementation of this RFC therefore needs a separate proof-only composition
that invokes automatic orchestration and constructs its proof request with the
constraint below. This is a narrow proof seam, not a change to either existing
path.

### Request permission and HTTP entrypoint

The proof process may expose the existing `/v1/chat` route through its
proof-only application composition, following RFC-0022. For every proof
request, it explicitly constructs `local_only=false`.

This request-level permission is allowed only because the operator deliberately
started `home-ai-cluster-automatic-proof`. Ordinary requests still default to
`local_only=true`; ordinary `/v1/chat` remains local-only; and ordinary
application startup does not enable remote routing. A remote declaration,
address, or transport alone does not override `local_only`.

Do not add a general HTTP field, header, query parameter, environment variable,
or configuration option for changing `local_only`. The proof-only `/v1/chat`
is available only inside the dedicated process and does not change the ordinary
HTTP contract.

### Normative proof path

The successful proof path is:

```text
operator starts home-ai-cluster-automatic-proof
  -> required remote LAN address
  -> fixed declared-remote node with Capability("chat")
  -> explicit request permission local_only=false
  -> proof-only /v1/chat
  -> discover no matching local candidate
  -> discover one matching declared-remote candidate
  -> RFC-0025 automatic selection
  -> select declared remote as sole selectable candidate
  -> HTTP /internal/cluster/request on receiving machine
  -> local runtime adapter executes there
  -> normalized ClusterResult.node_id = declared-remote
```

The unchanged ordinary path is:

```text
ordinary application startup
  -> no automatic proof wiring
  -> /v1/chat remains local-only
```

The proof must not use `DECLARED_REMOTE_ONLY`, `PREFER_DECLARED_REMOTE`,
`PREFER_LOCAL`, or any other caller-directed selection mode. Success proves
that the cluster-owned RFC-0025 automatic policy selected the remote candidate
because it was the sole selectable capability match.

### Receiving machine and explanation boundary

The receiving machine continues to expose `/internal/cluster/request` as the
accepted internal local-execution boundary. Its contract does not change.

RFC-0025 explanation facts remain internal. Visible proof evidence may consist
only of a successful HTTP response, required `ClusterResult.node_id`
attribution, operator-observed two-machine execution, and a recorded proof
result document after the run. This RFC adds no public routing explanation,
logging requirement, persistence, prompt logging, or result wrapper.

### Failure and resource ownership

The proof fails explicitly if its remote address is missing or invalid, no
candidate is selectable, transport fails, remote execution fails, or the
remote response is invalid. It must not retry, fall back to local, select
another node, contact another address, dynamically alter declarations, or hide
failure behind a local response.

The proof process owns the manual declaration, proof request constraint, HTTP
client, remote transport, automatic-proof wiring, and their startup and
shutdown. The HTTP client must not become module-global state. The precise
lifespan implementation remains an implementation detail.

## Rationale

This is the smallest operator-owned invocation that proves RFC-0025 without
changing normal request movement. An empty or otherwise nonmatching local side
ensures the accepted local-precedence rule does not mask automatic remote
selection. One static declaration and one transport keep trust and request
movement visible. `local_only=false` remains narrowly coupled to deliberate
proof-process startup, preserving the safe ordinary default.

## Alternatives considered

### Reuse `home-ai-cluster-static-proof` with a selection-mode flag

Rejected. It would create a general routing CLI and blur caller-directed and
cluster-owned proof authority.

### Change ordinary `/v1/chat`

Rejected. Normal request movement must remain local-only.

### Keep a matching local `chat` candidate

Rejected. RFC-0025 would correctly select local, so the run would not prove
automatic remote selection.

### Use `DECLARED_REMOTE_ONLY`

Rejected. It would repeat RFC-0022 rather than prove RFC-0025.

### Add a new public proof endpoint

Rejected. The established proof-process `/v1/chat` pattern is sufficient and
does not require a new public endpoint.

### Pass `local_only` through ordinary HTTP requests

Rejected. It would begin defining a general public remote-permission interface.

### Load configuration files or environment variables

Rejected. That is premature configuration design.

### Expose capability or node-id CLI options

Rejected. Fixed `chat` and `declared-remote` are sufficient for one proof.

## Trade-offs

The process is intentionally narrow and not generally configurable. It proves
only one remote candidate and cannot demonstrate multiple-candidate ordering,
health behavior, or recovery. This limitation is desirable: it avoids silently
deciding configuration, capability modeling, scheduling, or fallback policy.

## Impact

If accepted, this RFC authorizes a small implementation of the dedicated
proof-only process and its in-memory automatic-routing composition. It does not
authorize changes to ordinary application wiring, the ordinary HTTP contract,
RFC-0022, the existing remote transport abstraction, result attribution, or
the receiving internal endpoint.

## Acceptance criteria

The proof succeeds only when all of the following are observed:

- the ordinary application remains local-only;
- the dedicated command requires explicit operator invocation;
- exactly one remote address is manually supplied;
- no caller-directed selection mode is used;
- the proof request has `local_only=false`;
- no local `chat` candidate is selectable;
- one declared remote `chat` candidate is selectable;
- RFC-0025 automatically selects that remote candidate;
- the request crosses the LAN once;
- the remote machine executes through its local adapter;
- the result returns with `node_id=declared-remote`; and
- no retry or fallback occurs.

## Decision

Pending.
