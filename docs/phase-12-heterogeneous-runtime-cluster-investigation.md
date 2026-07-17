# Phase 12 Heterogeneous Runtime Cluster Investigation

Status: Draft

## Purpose

Determine whether one ordinary static cluster request can execute on a receiving
node using a different runtime engine from the calling node without changing the
cluster-facing architecture, or whether that proof requires a new architectural
decision.

The smallest candidate is one calling Home AI Cluster process with one explicitly
declared receiving Home AI Cluster process. The two processes use different local
runtime engines, one ordinary `/v1/chat` request succeeds, and the caller returns
the existing normalized cluster result.

## Accepted starting point

The accepted architecture already establishes the required boundaries:

* `OllamaAdapter` and `LlamaServerAdapter` are concrete implementations of the
  cluster-owned `RuntimeAdapter` boundary.
* Phase 5 proved one real local request through each adapter without changing the
  adapter interface, public API, routing, or node attribution.
* The ordinary static cluster supports one fixed local node and one or more
  explicitly declared remote nodes.
* Remote execution crosses to the receiving Home AI Cluster application through
  normalized cluster objects; it does not expose a runtime protocol to the
  calling cluster.
* Routing is capability-centered and local-first.
* Runtime, adapter, and model identity are not static declaration fields or
  request-level selectors.
* Cluster status reports normalized application and runtime status, rather than
  runtime identity.

These boundaries come from RFC-0003, RFC-0030, RFC-0038, RFC-0039, RFC-0040,
and RFC-0041. They remain subject to the narrower fallback, attribution,
transport, and declaration boundaries in the accepted RFCs they build on.

## Current implementation evidence

### Ordinary local runtime wiring

`api/wiring.py` currently constructs the ordinary local node and its adapter
registry explicitly. `create_static_local_node_announcement()` declares the
`chat` capability and `ollama` adapter, while
`create_static_runtime_adapter_registry()` creates one `OllamaAdapter`.

`api/routes.py` calls those factories for ordinary local `/v1/chat`,
`POST /internal/cluster/request`, and `GET /internal/cluster/status` handling.
`main.py:create_app()` does not accept local node or adapter wiring. The ordinary
local application is therefore Ollama-wired today.

The ordinary static-cluster constructors in `static_cluster.py` reuse the same
two factories for their local caller. The `home-ai-cluster-static-cluster` CLI
accepts only remote topology inputs, not a local runtime choice.

### Second runtime adapter wiring

`adapters/ollama.py` and `adapters/llama_server.py` both implement the unchanged
four-member `RuntimeAdapter` protocol from `adapters/base.py`: `name`, `health`,
`capabilities`, and `chat`.

The Phase 5 proof module explicitly constructs both adapters with operator-owned
loopback URLs and model values. It selects an adapter only for that local proof;
it is not ordinary application startup wiring and does not run a receiving Home
AI Cluster application. Its retained evidence confirms that both adapters accept
the same `ClusterRequest`, return normalized results, and normalize runtime
failures.

### Receiving application boundary

The receiving application exposes the accepted normalized internal endpoints:

* `POST /internal/cluster/request` accepts `ClusterRequest` and executes only
  the receiving process's local path.
* `GET /internal/cluster/status` observes only that process's local node and
  adapter registry, then returns `InternalClusterStatusResponse`.

Neither endpoint receives a runtime name, adapter name, model name, or remote
topology fact from the caller. Tests in `test_app.py` demonstrate that the
internal endpoints remain local even when caller-side static-remote wiring is
present.

The current endpoints are not yet supported as an ordinary llama-server
receiving application, because their local factories are hard-coded to Ollama.
Tests substitute a recording adapter by monkeypatching the factories, which is
evidence that the handlers consume the generic registry boundary, but is not
operator-facing or supported process composition.

### Remote adapter boundary

`HttpRemoteTransport` sends the normalized `ClusterRequest` to the declared
receiving application's `/internal/cluster/request` endpoint and validates the
returned `ClusterResult`. It does not send Ollama-, llama-server-, or
model-specific payloads.

`execute_declared_remote_routing_candidate()` preserves the normalized result
and applies the caller-owned declared remote `node_id`. The caller therefore
receives the existing result shape and cluster-owned attribution, without needing
to know which runtime protocol ran on the receiving machine. Adapter and model
attribution remain generic result fields, not request-level selectors.

### Static declaration boundary

RFC-0039 and RFC-0040 declarations retain only remote node IDs and base URLs.
They have no runtime, adapter, model, capability, credential, or lifecycle
fields. No new declaration field is necessary for the candidate proof.

`static_cluster.py:create_remote_declaration()` currently synthesizes an
`adapters=["ollama"]` value in its in-memory remote node description. This is not
an operator declaration field and declared-remote eligibility does not resolve
that value against the calling process's adapter registry. Remote eligibility is
based on the explicit declaration, static availability, and requested capability.
The value must not be treated as a claim about the receiving runtime or as a
heterogeneous-routing selector. The proof does not need to change it.

### Routing and fallback boundary

`routing_candidates_for_request()` and the ordered static fallback path preserve
capability matching and local precedence. A remote candidate is eligible from the
explicit declaration and requested capability; its runtime or model is not
consulted.

The existing fallback continues only after the accepted pre-request connection
unavailable failure. Remote candidates are attempted once in declaration order.
A successful heterogeneous proof can exercise this path by making the caller's
operator-owned local runtime unavailable before the request. It requires no
runtime-specific routing, retry, ordering, or fallback rule.

### Status boundary

RFC-0041's internal status endpoint returns only `runtime_status`; the remote
status transport projects that result with the caller-owned declared node ID and
normalized application status. The protocol does not contain an adapter, model,
or runtime-engine name.

Accordingly, the protocol remains valid when a receiving application uses
llama-server: its `LlamaServerAdapter.health()` already returns the existing
`AdapterHealth` shape. As with request execution, the current gap is only the
unsupported hard-coded local registry construction, not a status protocol gap.

## Smallest candidate proof

The smallest candidate remains two machines and two existing engines:

```text
calling Home AI Cluster process
  -> one explicit remote declaration
  -> receiving Home AI Cluster process
  -> LlamaServerAdapter on the receiving machine
  -> operator-managed llama-server and one local model
```

The caller may retain the ordinary Ollama local wiring. To exercise the accepted
remote path, its local runtime must fail only with the accepted pre-request
connection-unavailable condition. The caller then sends one normalized request
through `HttpRemoteTransport`; the receiving process executes it through an
explicitly supplied `LlamaServerAdapter`; and the caller returns the normalized
result with the declared remote node ID.

The needed implementation boundary is proof-only receiving-application
composition: construct a local `NodeRegistry` that declares `llama-server` and
an `AdapterRegistry` containing one explicitly configured `LlamaServerAdapter`,
then make those already-created registries available to the receiving local
request and status handlers. The normal `create_app()` default and the ordinary
static-cluster command must remain unchanged.

## What already works

* The two concrete adapters already share the accepted request, capability,
  health, result, and failure boundaries.
* The remote transport carries normalized cluster objects to the receiving
  application, rather than a runtime protocol to a remote runtime.
* The caller owns static topology, remote identity, candidate order, and final
  node attribution.
* The receiving node owns its local runtime adapter, runtime URL, model value,
  and runtime-specific HTTP translation.
* Static declarations need only a remote ID and base URL for the proof.
* Routing and fallback do not use engine identity.
* The status request and result are already engine-neutral and privacy-safe.

## Gaps

The current ordinary receiving application cannot be started with
`LlamaServerAdapter` through supported application wiring. Its request and status
handlers construct the default Ollama local node and registry internally.

Likewise, the ordinary static-cluster CLI has no local runtime selection option.
Adding one would create a new CLI and configuration contract, so it is not an
appropriate way to close this proof gap.

The Phase 5 proof constructs llama-server only in an explicit local proof
process. It does not provide the receiving-application composition required for
a real two-machine request. No evidence requires changing `RuntimeAdapter`,
adding a factory, or making adapter registration dynamic.

## Architectural decision test

No new RFC is needed if the implementation is limited to a proof-only,
explicitly supplied receiving local node and adapter registry. That reuses the
accepted adapter interface, normalized request and result models, static topology
and remote transport, and status protocol. It adds no public CLI, configuration,
declaration, routing, fallback, status, or lifecycle contract.

An RFC is required before implementation if the scope instead needs an ordinary
process-startup runtime selector; a runtime, adapter, or model declaration field;
a changed adapter interface; a generic factory, plugin, or dynamic registry;
engine-aware routing or fallback; changed status semantics; lifecycle ownership;
or another ordinary public operating mode.

## Options considered

1. **Reuse existing explicit proof or composition wiring.** Existing Phase 5
   wiring proves both adapters, but it does not start a receiving application.
   Existing tests use monkeypatching, which is not a supported real-operator
   composition path. Reuse alone is insufficient.
2. **Add one narrow heterogeneous proof-only composition.** Add an explicit
   receiving local node and adapter-registry seam only for the Phase 12 proof.
   It keeps the existing internal endpoints, normalized transport, topology,
   routing, fallback, status, and lifecycle boundaries. This is sufficient.
3. **Make ordinary local runtime selection configurable.** Rejected for this
   proof. A CLI, configuration, precedence, validation, and compatibility
   contract would be a new architectural decision.
4. **Add runtime identity to the cluster declaration.** Rejected. It would make
   engine identity a topology fact despite the remote transport and capability
   boundaries already hiding it from the caller.
5. **Introduce a generic runtime factory or plugin mechanism.** Rejected. Two
   explicit adapter implementations provide no evidence that dynamic loading or
   a generic factory is needed.

## Recommendation

The accepted architecture already supports a heterogeneous request boundary: the
caller does not need the receiving engine identity, declarations need no runtime
field, remote transport exchanges normalized cluster objects, and status remains
runtime-identity-free. The implementation lacks only an explicit proof-scoped
way to compose the receiving application's existing local handlers with the
already accepted llama-server adapter.

No new RFC is required before a narrow Phase 12 proof implementation.

## Proposed next step

A later implementation PR may add one proof-only receiving-application
composition seam that supplies the local node and adapter registries used by the
existing internal request and status handlers. It should construct only the
existing `LlamaServerAdapter` explicitly, preserve ordinary defaults and all
accepted public contracts, add focused boundary tests, and then perform the
separate retained privacy-safe operator proof required by Phase 12.

## Non-goals

This investigation does not add:

* implementation;
* a new runtime engine;
* automatic runtime selection;
* runtime or model discovery;
* runtime fields in cluster declarations;
* request-level runtime, adapter, model, or node selection;
* adapter interface changes without evidence;
* generic factories, plugins, or dynamic loading;
* runtime installation or model downloads;
* runtime startup, supervision, restart, or repair;
* routing or fallback changes;
* status protocol changes;
* a dashboard, database, Docker, or Kubernetes; or
* a retained real operator proof in this investigation PR.
