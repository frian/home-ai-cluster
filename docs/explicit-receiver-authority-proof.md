# Explicit Receiver Authority Proof

Status: Post-1.0 development record

## Scope

This factual, privacy-safe manual proof record was performed on 2026-09-06 on
the `post-1.0-development` line. It retains evidence for the already accepted
RFC-0109 route-authority boundary and RFC-0111 receiver-activation boundary.
It is not a new architectural decision and is not part of the published Home
AI Cluster 1.0 release.

PR #699 implemented RFC-0111 receiver authority activation. The first physical
run exposed a clean dual-listener shutdown defect, which PR #700 corrected.

## Physical topology

The bounded two-machine topology was:

```text
caller
    |
    | ordinary static remote request
    v
receiver LAN authority
    |
    +-- one HAC foreground process
            |
            +-- native/local authority
            |      127.0.0.1:25042
            |
            +-- explicit receiver authority
                   <receiver-lan-ip>:25042
```

The two listener startup messages reported the same server process. This
supports the one-process boundary, but does not by itself prove every internal
object-identity invariant; automated tests remain responsible for exact
`LocalAppComposition` identity.

## Route-boundary observations

On the receiver's loopback native/local authority:

```text
GET /
-> 200
```

From the caller to the receiver LAN authority:

```text
GET /
-> 404

GET /openapi.json
-> 404

POST /v1/chat
-> 404

GET /internal/cluster/status
-> 200
```

The status response was:

```json
{"runtime_status":"available"}
```

The receiver log also showed:

```text
POST /internal/cluster/request
-> 200
```

The native browser remained available on loopback. The LAN receiver authority
did not expose the browser, framework OpenAPI, or native `/v1/chat`, while the
accepted receiver status and internal request routes remained available.

```text
route isolation != authentication
route isolation != transport confidentiality
```

This proof used plain HTTP on a trusted LAN. It makes no authentication,
authorization, or confidentiality claim.

## Real remote request

The caller used ordinary static-cluster routing: `chat` remained caller-local
eligible and `summarize` was remote eligible on the declared receiver. One real
command equivalent to:

```text
hac summarize \
  --text "Home AI Cluster routes requests by capability." \
  --json
```

returned a successful response with these relevant facts:

```json
{
  "adapter": "ollama",
  "model": "llama3.2:1b",
  "node_id": "receiver"
}
```

The request crossed the explicit receiver authority, executed through the
receiver's ordinary local runtime composition, and reported caller-owned
`receiver` node attribution. Capability-centered remote routing remained
functional through the new route boundary. This is not evidence of load
balancing, discovery, scheduling, or capacity behavior.

## Native-LAN fail-closed check

The former generic native-LAN invocation:

```text
hac local --host 0.0.0.0
```

was rejected locally with:

```text
--host must be exactly 127.0.0.1
```

No listener started. The former accidental generic native-LAN exposure path is
therefore no longer accepted; receiver exposure must be activated through
explicit `--receiver-host`.

## Shutdown correction and final proof

During the first physical run after PR #699, both listeners started, route
isolation and status passed, and the real remote summarize request passed. One
Ctrl-C closed both listener sockets, but shutdown emitted an asyncio/Starlette
cancellation traceback:

```text
listeners closed
but receiver lifespan was cancelled during process signal propagation
```

That real defect led to the bounded correction in PR #700.

After PR #700 merged, the shutdown-only portion was repeated. Startup again
showed one server process serving:

```text
http://127.0.0.1:25042
http://<receiver-lan-ip>:25042
```

One Ctrl-C produced two normal Uvicorn shutdown sequences:

```text
Shutting down
Waiting for application shutdown.
Application shutdown complete.
Finished server process [...]
```

There was no asyncio, Starlette lifespan, or TaskGroup traceback. After return
to the shell:

```text
echo $?
-> 130
```

and a listener check for port `25042` found no remaining listener. One Ctrl-C
therefore terminates the combined foreground invocation, both listeners
complete normal application shutdown, root HAC preserves interruption exit
code `130`, and no listener remains bound afterward. This does not claim
daemon, service, or supervisor semantics.

## What this establishes

The physical evidence supports this accepted shape:

```text
one HAC foreground process
one cluster-visible local node
one process-local execution composition/state
        |
        +-- loopback native/local authority
        |
        +-- explicit bounded receiver authority
```

It directly observed one process serving both network authorities, route
isolation, native loopback preservation, real remote request execution,
caller-owned receiver attribution, fail-closed old native LAN bind, and
coordinated clean foreground shutdown. Automated tests, not this manual proof
alone, establish exact Python object identity for the shared
`LocalAppComposition` and focused internal lifecycle invariants.

## Boundaries preserved

This proof does not establish or introduce authentication, authorization
credentials, TLS or confidentiality, hostile-network safety, discovery,
dynamic membership, remote capacity knowledge, scheduling, load balancing,
queues, retained receiver configuration, daemonization, supervision,
multi-process coordination, generic multi-listener architecture, or runtime
capacity guarantees. The successful request does not make the receiver's
runtime or model remotely configurable.

## Architecture references

- Accepted RFC-0109 — explicit LAN receiver route boundary
- Accepted RFC-0111 — explicit receiver authority activation
- RFC-0098 through RFC-0106 — independent shared process-local execution-state
  boundaries
- PR #699 — RFC-0111 implementation
- PR #700 — clean dual-listener shutdown correction
