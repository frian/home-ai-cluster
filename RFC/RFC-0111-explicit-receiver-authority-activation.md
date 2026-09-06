# RFC-0111: Explicit Receiver Authority Activation

Status: Draft

Date: 2026-09-06

Author: frian

## Summary

Home AI Cluster should make the remote receiver authority accepted by RFC-0109
an explicit additive option of the ordinary foreground local-process launcher:

```text
hac local
    -> one HAC process
    -> ordinary native/local authority only

hac local --receiver-host <ADDRESS>
    -> the same one HAC process
    -> ordinary native/local authority
    -> plus explicit RFC-0109 receiver authority
```

The ordinary native/local application remains bound only to `127.0.0.1`.
`--receiver-host` accepts one explicit concrete, non-loopback IP address and
adds a separate receiver listener, defaulting to port `25042`. That listener
serves only RFC-0109's closed receiver route set. It uses the exact same
`LocalAppComposition` as the ordinary application.

This RFC defines explicit operator activation and bind authority. RFC-0109
continues to own which routes belong to receiver authority. This RFC adds no
authentication, TLS, discovery, daemon, second node, or multi-process
coordination.

## Problem

RFC-0109 establishes the necessary route boundary for a HAC process that is
intentionally reachable by a remote HAC caller, but deliberately leaves the
listener and operator-activation representation open. The ordinary `hac local`
launcher currently accepts a generic `--host`; a non-loopback value can expose
the ordinary native application beyond loopback. That is incompatible with a
durable receiver contract because bind location must not silently select route
authority.

The current ordinary launcher already has the relevant local seams:

- `hac` delegates `local` to the ordinary `local_runtime` launcher;
- that launcher constructs one `LocalAppComposition` and passes it to
  `create_app(...)`; and
- RFC-0109's `create_receiver_app(...)` accepts one supplied
  `LocalAppComposition` while mounting only the receiver router.

The activation decision must preserve one intended HAC node and one
process-local execution-accounting scope. Independently launching an ordinary
`hac local` process and a second receiver process for the same node would make
two independently accounted process-local execution states. RFC-0098 through
RFC-0106 deliberately place execution availability, permission, intervals,
and limits within a process-local HAC composition. This RFC must not pretend
that two such processes are one execution scope.

## Goals

- Keep `hac local` as the canonical foreground local-process launcher.
- Preserve one foreground HAC process, one `LocalAppComposition`, one
  cluster-visible local node, and one process-local execution state.
- Make receiver authority additive and explicit through `--receiver-host`.
- Keep ordinary native/local authority on exactly `127.0.0.1`.
- Make the receiver bind one explicit concrete non-loopback IP address, with no
  implicit receiver host or automatic network selection.
- Reuse `25042` as the receiver default port while keeping receiver and native
  port overrides independent.
- Preserve RFC-0109's closed two-route receiver surface and its fail-closed
  multi-adapter status semantics.
- Define focused later implementation proof expectations without implementing
  the decision in this RFC.

## Non-goals

This RFC does not add authentication, authorization credentials, API keys,
bearer tokens, HMAC, TLS, mTLS, certificate management, or secret persistence.
It does not add receiver retained configuration, listener profiles, interface
or DNS discovery, address selection, network probing, firewall or VPN
management, daemonization, service installation, process supervision, PID
files, background operation, or remote process control.

It does not add a generic multi-listener framework, a second HAC
node/composition, multi-process coordination, execution-availability
advertisement, capacity-aware routing, scheduling, load balancing, queues,
Docker, Kubernetes, a dashboard, or a database.

## Proposal

### One foreground process and one composition

Receiver activation remains one invocation of `hac local`:

```text
one HAC foreground process
one LocalAppComposition
one cluster-visible local node
one process-local execution state
```

When explicitly activated, both application authorities consume the same exact
composition object:

```text
one LocalAppComposition
        |
        +-- ordinary native/local application
        |
        +-- RFC-0109 receiver-only application
```

No second composition, adapter registry, binding collection,
execution-permission state, execution-limit state, or orchestrator is created
because receiver authority is enabled. Native/local requests and receiver-side
requests therefore consume the same process-local execution state under
RFC-0098 through RFC-0106. Receiver activation neither advertises availability
nor adds slots, limits, scheduling, or load balancing.

This is not a general answer to multi-process HAC coordination. That problem
remains outside this RFC.

### Native/local authority and `--host`

The ordinary native/local application is bounded to the accepted ordinary
loopback authority:

```text
127.0.0.1
```

`hac local` with no receiver activation remains ordinary loopback-only
operation. Existing native `/v1/*`, caller-local internal, browser, and
framework behavior remain governed by their accepted local contracts; this RFC
does not broaden browser access.

After implementation, a non-loopback `hac local --host` value must fail
locally and explicitly before any server bind. It must not expose native routes
on the LAN, silently choose receiver authority, rewrite itself to
`--receiver-host`, start a partial alternative application, or warn and
continue. The existing exact loopback spelling remains valid:

```text
hac local --host 127.0.0.1
```

RFC-0090 already makes `127.0.0.1` the boring ordinary convention. This RFC
does not require a general loopback-host classifier merely to preserve other
historical spellings.

### Explicit receiver activation and receiver host

Receiver authority is enabled only by:

```text
--receiver-host <ADDRESS>
```

The option means: add the bounded RFC-0109 receiver authority to this same
foreground HAC process. There is no implicit receiver host: `hac local` never
silently binds a receiver to `0.0.0.0` or another non-loopback interface.

For this first operator contract, `<ADDRESS>` is exactly one concrete IP
address. Local validation before listener startup must reject wildcard or
unspecified addresses such as `0.0.0.0` and `::`, loopback addresses,
hostnames/DNS names, and malformed IP values. The standard-library notion of a
concrete IP value is the expected implementation seam. HAC performs no DNS
resolution, network probing, interface enumeration, reachability check, or
automatic address selection.

A syntactically valid concrete non-loopback IP does not assert that the address
is configured locally. Bind failure remains owned by ordinary server/OS startup.
The contract is not restricted to a particular private-address range: the
operator selects the intended interface and network boundary.

### Receiver surface and port

The receiver listener serves only RFC-0109's already accepted closed surface:

```text
POST /internal/cluster/request
GET  /internal/cluster/status
```

It must not expose native `/v1/*`, browser, caller-local internal,
compatibility, runtime-native, FastAPI documentation/schema, or other routes.
Receiver activation never alters native/local route ownership.

The receiver default port is `25042`. This reuses the ordinary HAC convention
without creating another arbitrary service number. The native and receiver
authorities are separate listeners on distinct concrete addresses and may use
the same default port. A later implementation may provide the additive:

```text
--receiver-port <PORT>
```

when needed by the ordinary server contract. It is independent of the existing
native/local `--port`: changing one must not silently change the other. HAC
adds no discovery or port propagation; remote declarations remain explicit
operator-owned URLs. If supported-platform evidence shows that two
concrete-address listeners using the same port cannot work coherently,
implementation must stop and report rather than inventing a new port or
changing this RFC.

### Foreground lifecycle

Both authorities belong to one foreground `hac local` invocation. Normal
process interruption stops the whole invocation. HAC neither daemonizes nor
supervises itself, and startup must not intentionally leave one authority
running as a separately managed HAC service if the combined invocation fails.

Exact asyncio/Uvicorn representation is implementation detail. The later
implementation must use the smallest boring mechanism that runs the two
accepted application authorities over the same composition; this RFC does not
design a generic lifecycle manager.

## Compatibility and boundaries

Previously an operator could use a non-loopback generic host such as:

```text
hac local --host 0.0.0.0
```

and expose the ordinary application. That behavior is deliberately not
retained as supported LAN-native authority. RFC-0109 already states that
accidental LAN reachability of native routes is not an accepted compatibility
contract. The supported shape after implementation is:

```text
local/native authority:       127.0.0.1 only
remote HAC receiver authority: explicit --receiver-host only
```

No redirect, automatic flag translation, compatibility listener, or deprecation
period is introduced unless an independently accepted release policy requires
one.

RFC-0109 owns route authority; RFC-0111 owns explicit operator activation and
bind authority. It neither reopens the closed route set nor changes remote
request/status models. RFC-0050 remains unchanged: `local` is the canonical
launcher, no root `receiver` subcommand is added, and the root command does not
become a lifecycle manager.

Receiver route isolation is not authentication and is not transport
confidentiality. No authentication or TLS is introduced. The existing
trusted-LAN assumption remains. An explicit concrete bind minimizes accidental
exposure while the receiver remains unauthenticated plain HTTP; it is not
secure transport.

## Alternatives considered

### Separate `hac receiver` process

Rejected as the ordinary model. It risks representing one intended HAC node by
another independently accounted process and duplicates process-local execution
state.

### `hac receiver` that also serves native loopback

Rejected. It would name a command as receiver-only while actually launching
both authorities. Keeping `hac local` as the canonical launcher makes the
additive authority explicit.

### `hac local --receiver-only`

Rejected. It removes local/native authority and makes receiver activation an
application replacement rather than additive bounded authority.

### Infer application selection from `--host`

Rejected strongly. Bind location must not silently select application authority.

### Preserve non-loopback ordinary `--host`

Rejected as a durable contract. It leaves a broad LAN-native bypass around the
bounded RFC-0109 receiver surface.

### Default receiver bind to `0.0.0.0`

Rejected. All-interface binding is broader than the authority explicitly
required and is unsuitable while authentication and TLS are absent.

### Two independent foreground commands

Rejected as the ordinary same-node model because execution state is
process-local and independent. General multi-process coordination remains out
of scope.

## Trade-offs

The explicit two-listener invocation is more complex than one generic bind, and
the historical non-loopback native form becomes an intentional compatibility
tightening. In return, an operator can tell from the command which authority is
being exposed, ordinary native routes retain their loopback boundary, and one
intended node retains one composition and one execution scope.

The trusted-LAN receiver remains unauthenticated plain HTTP. The concrete-bind
requirement reduces accidental exposure but does not provide identity,
authorization, or confidentiality.

## Impact

Acceptance authorizes one later bounded implementation in the existing
ordinary `hac local` parser and launcher. It may construct the existing
`create_app(...)` and `create_receiver_app(...)` authorities from the same
already-built `LocalAppComposition`; it must not modify the route contract or
invent parallel composition/accounting machinery.

Current command and operator documentation will need focused alignment. Source
code and tests are deliberately unchanged by this RFC.

## Proof expectations

A later implementation should prove at least:

1. zero-argument `hac local` remains ordinary loopback-only behavior;
2. `hac local --host 127.0.0.1` remains valid;
3. non-loopback `--host` fails before binding;
4. a valid `--receiver-host` constructs exactly one local composition;
5. both application authorities consume that exact composition object;
6. native routes remain reachable only through native loopback authority;
7. the receiver listener exposes only RFC-0109's two routes;
8. receiver `/v1/*` attempts do not execute and receiver docs/schema are absent;
9. one process-local execution permission/execution-limit object governs both
   native and receiver execution;
10. normal foreground shutdown terminates both authorities;
11. wildcard, loopback, hostname, malformed, and invalid receiver hosts fail
    locally before listener startup;
12. no authentication, TLS, discovery, daemonization, scheduling, or protocol
    semantics are introduced; and
13. existing remote callers work when their explicit declaration targets the
    receiver listener.

A privacy-safe two-machine proof may follow implementation if repository
practice warrants it. Drafting this RFC does not perform one.

## Open questions

Whether a later implementation needs `--receiver-port` for the ordinary server
contract remains implementation-level. Authentication, confidential transport,
and any general multi-process coordination require separate architectural
decisions.

## Decision

Pending.
