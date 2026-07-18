# Phase 17 End-to-End Ordinary Remote Request Investigation

Status: Complete

## Question

Can the existing accepted ordinary client, static-cluster process, routing,
bounded fallback, remote transport, receiving application, runtime adapter, and
attribution boundaries already produce one real end-to-end ordinary remote
request without architectural or implementation changes?

## Scope

This investigation considers the composition of already accepted and implemented
surfaces. It does not accept a new roadmap phase, change a command, alter
routing or transport, add a proof runbook or retained proof, or change any RFC.

The technical objective remains:

> Fake in distribution, but not fake in architecture.

The ordinary running process, not the client, owns topology, routing, fallback,
remote transport, execution, result attribution, and cluster failures. The
one-shot client remains a topology-blind client of the caller's existing
loopback endpoint.

## Existing accepted components

The following accepted components already form the relevant path.

| Component | Existing boundary |
| --- | --- |
| One-shot client | `home-ai-cluster-chat --message "<MESSAGE>"` constructs one fixed-`chat` request, sends one `POST` to `http://127.0.0.1:8000/v1/chat`, validates one complete `ClusterResult`, and exits. It has no topology, declaration, runtime, node, retry, or fallback input. [RFC-0045](../RFC/RFC-0045-one-shot-ordinary-request-command.md) remains authoritative. |
| Ordinary static caller | `home-ai-cluster-static-cluster --declaration <path>` loads an explicit static declaration, constructs one local composition plus declared remote candidates, and exposes the ordinary caller endpoint on loopback. [RFC-0038](../RFC/RFC-0038-ordinary-static-multi-node-mode.md), [RFC-0039](../RFC/RFC-0039-repeatable-static-cluster-declaration.md), and [RFC-0040](../RFC/RFC-0040-multiple-explicit-static-remote-nodes.md) define that shape. |
| Local composition | The static caller and ordinary local process support one explicit local composition from the closed `ollama` and `llama-server` set; no-option operation remains Ollama-backed. Runtime identity remains outside declarations and requests. [RFC-0043](../RFC/RFC-0043-explicit-static-cluster-local-composition.md) defines the caller boundary. |
| Fallback | The caller attempts its eligible local candidate once. Only a connection failure known to occur before request transmission can advance to already declared remote candidates; there is no retry, reselection, or client-side fallback. [RFC-0028](../RFC/RFC-0028-minimal-pre-execution-candidate-fallback.md) and RFC-0040 define this bounded behavior. |
| Remote transport | The repository-owned HTTP transport carries the normalized request only to a declared remote's existing `POST /internal/cluster/request` endpoint. It validates the returned normalized result and does not let an address become node identity. [RFC-0013](../RFC/RFC-0013-minimal-remote-transport-boundary.md) and [RFC-0014](../RFC/RFC-0014-minimal-concrete-transport-protocol.md) define the boundary. |
| Ordinary receiver | `home-ai-cluster-local` constructs one ordinary local composition and can use its existing `--host` and `--port` startup inputs. When deliberately bound to the trusted LAN, the ordinary application exposes the existing internal request endpoint; it does not need to know that another process declared it as remote. |
| Result attribution | After remote execution, caller-side execution projects the result to the declared remote node ID. The receiver's address and self-reported node identity do not own the caller's cluster attribution. [RFC-0023](../RFC/RFC-0023-result-node-attribution.md) and the fallback RFCs retain this rule. |
| Status, if used | `home-ai-cluster-status --declaration <path>` provides an optional finite, read-only pre-request observation. It neither selects a candidate nor changes routing or fallback. [RFC-0041](../RFC/RFC-0041-explicit-static-cluster-status.md) and [RFC-0044](../RFC/RFC-0044-explicit-static-cluster-status-composition.md) define it. |

The current code confirms these seams. The chat client posts only to the fixed
caller loopback target in
[`chat_command.py`](../src/home_ai_cluster/chat_command.py). The static command
builds declared remote wiring and a process-owned HTTP client in
[`static_cluster.py`](../src/home_ai_cluster/static_cluster.py). The remote
transport posts normalized requests to the internal request path and validates a
`ClusterResult` in
[`core/remote_transport.py`](../src/home_ai_cluster/core/remote_transport.py).
The existing route invokes the local composition on that internal endpoint, and
the caller-side executor replaces remote result attribution with the declaration
node ID in [`core/executor.py`](../src/home_ai_cluster/core/executor.py).

No missing implementation seam was found. The composition is already covered by
focused source and test boundaries; what has not been retained is the complete
operator-facing path beginning with the Phase 16 installed client and ending
with real trusted-LAN remote attribution.

## Existing remote-execution evidence

Phase 12 already retained a real two-machine proof. It is not theoretical.
[The retained record](phase-12-heterogeneous-runtime-cluster-proof.md) shows:

- a calling machine running an ordinary static-cluster process;
- a request entering the caller's ordinary `/v1/chat` endpoint;
- an unavailable local Ollama connection meeting the accepted pre-request
  condition;
- fallback selecting one explicitly declared remote on a trusted LAN;
- the receiving Home AI Cluster process executing through `LlamaServerAdapter`;
- a normalized caller result attributed to the caller-owned declared remote
  `node_id`; and
- no runtime, adapter, model, or node selector in the request or declaration.

Phase 14 then retained a fallback observation using two distinct ordinary
processes, rather than a proof-specific receiver, on one trusted host. Its
limitation was physical-machine separation, not ordinary static-cluster or
fallback behavior. See [the proof](phase-14-static-cluster-local-composition-proof.md)
and [closeout](phase-14-closeout.md). Phase 15 further confirms that ordinary
static declarations and ordinary receiving applications can be inspected through
the existing bounded status protocol without changing routing. See [the proof](phase-15-static-cluster-status-composition-proof.md)
and [closeout](phase-15-closeout.md).

Phase 16 proved the installed client boundary:

```sh
home-ai-cluster-chat --message "<MESSAGE>"
```

It proved that this unchanged invocation can send one ordinary native request to
an already running local-only or static-cluster process. Its retained
static-cluster observation used one physical machine and selected `local`; it did
not prove that the Phase 16 client invocation itself participates in a real
trusted-LAN remote execution. See [the investigation](phase-16-ordinary-operator-request-access-investigation.md),
[proof runbook](phase-16-ordinary-request-access-proof-runbook.md),
[retained proof](phase-16-ordinary-request-access-proof.md), and
[closeout](phase-16-closeout.md).

The Phase 17 ordinary-input investigation is separate: it leaves the accepted
`--message` contract unchanged and does not affect this path. See
[its investigation](phase-17-ordinary-request-input-investigation.md).

## Exact missing operator-facing evidence

The missing evidence is the composition of two already proven paths, not proof
of every internal seam from zero:

```text
Phase 16 one-shot client
  -> caller ordinary loopback /v1/chat
  -> existing static-cluster routing
  -> accepted local pre-request unavailability
  -> declared remote HTTP adapter
  -> real trusted-LAN transport
  -> receiving ordinary Home AI Cluster application
  -> receiving local runtime adapter
  -> normalized ClusterResult
  -> declared remote node_id returned to the client
```

The retained Phase 16 proof establishes the first client-to-caller boundary but
not the remote outcome. The retained Phase 12 proof establishes the caller-to-
receiver remote path and attribution but did not begin with
`home-ai-cluster-chat`. A combined real observation would establish that the
ordinary client preserves the already accepted remote path without gaining any
knowledge of it.

## Candidate proof topologies

### Two physical machines

This is the smallest credible topology for the missing claim and is preferred.

```text
calling machine
  home-ai-cluster-chat
  ordinary home-ai-cluster-static-cluster process
  one selected local runtime candidate, unavailable before transmission
  explicit remote declaration

receiving machine
  ordinary home-ai-cluster-local process exposed to the trusted LAN
  one supported local composition
  one operator-managed local runtime
```

It exercises the fixed client-to-caller loopback boundary and the actual
machine-to-machine HTTP crossing, while retaining one operator, explicit
topology, and manual process ownership. The client and caller can share the
calling machine because the client contract is deliberately loopback-only.

### One physical machine with multiple processes

This can exercise separate process boundaries, the internal HTTP request,
ordinary static fallback, and remote attribution. Phase 14 already provides
useful evidence of that shape. It cannot establish that the request crossed a
trusted LAN or reached a distinct physical receiver, so it is insufficient for
the specific missing end-to-end claim.

### Three physical machines

Separating the client, static caller, and receiver would require either changing
the client’s fixed loopback target or adding a forwarding arrangement outside
the accepted ordinary client contract. It therefore adds complexity without
evidence value for this claim. The client belongs on the caller machine.

## Calling-side local unavailability

The smallest honest condition is to use one accepted caller local composition
and ensure only its selected runtime endpoint is unavailable before the one
request. With the default Ollama composition, the caller's ordinary local Ollama
endpoint can be left stopped or otherwise unavailable while the receiving
runtime remains available. The static command constructs its local composition
without probing it, so the caller can start normally; the first request then
attempts the local candidate.

Both supported adapters translate a connection-establishment failure into the
existing `RuntimeConnectionUnavailableBeforeRequestError`. The fallback path
accepts that condition because it establishes that the selected runtime
connection could not receive the request. It must not be simulated through a
test transport, a patched exception, a post-execution failure, a timeout, or a
new failure category. It must not modify candidate order, select a node directly,
or retry.

The retained evidence need not contain raw errors or logs. It can establish the
accepted condition through the controlled operator sequence and the resulting
complete normalized outcome: the local runtime was unavailable before the sole
client invocation; the receiver remained available; the final validated result
has the declared remote ID rather than `local`; and no second client invocation
occurred. This is a bounded claim about the accepted path, not a packet-level
account of every failed connection.

## Receiving ordinary process

The receiver can use an existing ordinary supported startup path; the historical
Phase 12 proof-scoped receiver is not required. The current
`home-ai-cluster-local` command constructs one supported ordinary local
composition and accepts the ordinary process host and port inputs. Binding that
process to the trusted-LAN interface is sufficient for the caller's existing
remote transport to address its internal request endpoint.

For the smallest no-option arrangement, the receiving command is equivalent to:

```sh
uv run home-ai-cluster-local --host 0.0.0.0 --port 8000
```

The LAN bind is an explicit operator action. Firewall scope, runtime startup,
model availability, application shutdown, and removal of temporary firewall
allowances remain operator-owned. The receiver does not parse the caller's
declaration, perform remote routing, or need a remote-specific mode; its
existing internal request route executes through its one local composition.

The canonical workflow also documents ordinary application startup on a trusted
LAN interface. Either existing ordinary path must be used exactly as supported
by the chosen runtime composition; no proof-only launcher or custom Python
wiring is necessary.

## Runtime arrangement

Use Ollama on both machines unless the operator's available environment makes a
different accepted composition materially simpler. This is the smallest
arrangement because the default local composition on both the static caller and
ordinary receiver is already Ollama-backed. The caller's Ollama is deliberately
unavailable for the request; the receiver's Ollama remains operator-managed and
available.

Heterogeneous runtimes are not required: Phase 12 already proved that different
runtime families can participate in the remote path. A llama-server composition
remains an accepted alternative for either process, but selecting it must occur
only in process startup arguments. Runtime identity must not appear in the
client invocation, request, declaration, routing selection, or final node
attribution.

## Expected end-to-end path

The likely supported sequence, to be refined only if a future runbook is
authorized, is:

1. Use the same repository revision on both physical machines and synchronize
   dependencies.
2. Prepare the receiver's operator-managed local runtime and allow only the
   required trusted-LAN application exposure.
3. Start the receiver through an ordinary local process path on the accepted
   LAN bind.
4. On the caller, create one operator-owned explicit declaration containing one
   placeholder remote node ID and the receiver's trusted-LAN base URL. Do not
   retain real declaration content in repository evidence.
5. Configure the caller's accepted local composition and ensure only that local
   runtime endpoint is unavailable before the request.
6. Optionally run the existing finite status command to distinguish a coherent
   declaration, unavailable caller local runtime, and reachable receiver. This
   is diagnostic only and must not be represented as routing or proof of remote
   execution.
7. Start the ordinary static-cluster caller on its fixed loopback endpoint.
8. Invoke exactly once on the caller machine:

   ```sh
   uv run home-ai-cluster-chat --message "<REDACTED_TEST_MESSAGE>"
   ```

9. Validate the one compact client result, including that `node_id` equals the
   sanitized declared remote ID, then stop the caller, receiver, and any
   temporary firewall exposure in operator-controlled order.

The client receives no declaration, host, port, node, runtime, adapter, model,
capability, retry, or timeout option. It has only the existing `--message`
input, sends only to caller loopback, and cannot choose the remote outcome.

## Proof claims

A successful real proof would demonstrate that:

- the unchanged Phase 16 client invocation works in this topology;
- the client sends one request only to the caller's fixed loopback endpoint;
- the caller owns the declared topology, candidate selection, and fallback;
- the caller's local candidate is attempted under existing policy and the
  accepted pre-request condition permits exactly the existing remote advance;
- one explicitly declared remote receives the existing normalized request over a
  real trusted LAN and executes through its ordinary local process;
- the caller validates the remote result and assigns its declared remote ID;
- the one-shot client validates and prints the complete `ClusterResult`; and
- final `node_id` is the declared remote ID, not `local`, without infrastructure
  selectors in the client request.

It would not demonstrate discovery, registration, scheduling, load balancing,
retries, dynamic topology, internet operation, authentication, supervision,
runtime lifecycle management, model selection, broad distributed inference, or
universal client compatibility.

## Privacy and retained evidence

A future runbook and retained record can retain only the information needed to
support the claims:

- exact repository revision and date;
- sanitized caller and receiver process roles and commands;
- placeholder node IDs, addresses, ports, paths, runtime values, and message;
- one client invocation shape and its exit status;
- whether standard output and standard error were empty or non-empty as required;
- a sanitized normalized result shape, including the declared remote `node_id`;
- adapter or model fields only when already public in the result and appropriately
  redacted; and
- confirmation that one request was sent.

It must not retain prompt or generated-response content, real private addresses,
hostnames, usernames, paths, credentials, tokens, runtime URLs, real declaration
contents, raw logs, packet captures, tracebacks, raw HTTP bodies, or unnecessary
model identity.

Packet capture is not required by default. Distinct physical machines, explicit
process roles and LAN placement, the existing accepted transport implementation,
the controlled pre-request local condition, and successful declared-remote
attribution provide sufficient evidence for this bounded operator claim without
retaining request payloads or network traces. Packet capture would add privacy
risk and does not change routing or attribution authority.

## RFC assessment

No new RFC or RFC amendment appears necessary if a future proof uses only the
accepted client, static declaration, ordinary caller, ordinary receiving
application, existing runtime composition, bounded fallback, remote transport,
and result contract.

An RFC is required before any necessary change to command behavior, receiver
bind semantics, routing or fallback, transport, request or result shape,
declaration format, attribution, errors, privacy boundary, or lifecycle
ownership. This investigation identifies none. A failed proof may reveal such a
gap, but the gap must be observed and assessed rather than anticipated into this
document.

## Roadmap assessment

| Framing | Assessment |
| --- | --- |
| Formal Phase 17 | Not recommended now. The work adds no operator capability or architectural decision, and the filename does not create a roadmap phase. |
| Phase 16 proof extension | Plausible, because it strengthens the client evidence, but Phase 16 is already complete and its stated success criterion did not require a remote execution. Reopening it would blur its completed scope. |
| Standalone post-roadmap integration proof | Preferred. It validates the real composition of independently accepted Phase 12 and Phase 16 paths without treating evidence alone as a product phase. |
| No further work | Not preferred. The existing evidence proves the individual paths but not the complete installed-client-to-real-LAN-remote operator path. |

## Recommendation

Existing code and accepted contracts appear sufficient. Perform one two-physical-
machine, documentation-and-proof-only integration using the unchanged Phase 16
client, an ordinary static-cluster caller, an ordinary trusted-LAN receiver, the
existing accepted pre-request fallback condition, and the simplest available
supported runtime arrangement (normally Ollama on both machines).

No implementation change or RFC is needed unless preparing a runbook or running
the proof exposes a missing accepted startup or bind contract. Treat the work as
a standalone post-roadmap integration proof, rather than accepting a formal
Phase 17 or reopening Phase 16. This preserves the completed phases while making
the previously unretained composition visible.

## Proposed next step

If the operator wants this evidence, create one small privacy-safe integration
proof runbook, followed only after a real run by one retained proof record. The
runbook should use the sequence above, make the two-machine limitation and
trusted-LAN boundary explicit, and retain no prompt or generated response. It
should not add code, tests, commands, configuration, or an RFC.

## Non-goals retained

This investigation does not add discovery, dynamic registration, supervision,
remote process control, automatic runtime lifecycle, client-side routing or
fallback, direct node selection, retry, a new endpoint or transport, request or
result changes, a runtime adapter, a generic proof framework or configuration
system, sessions, history, dashboard, database, Docker, or Kubernetes.
