# Phase 13 Explicit Local Runtime Composition Proof

Status: Retained

## Purpose

Retain privacy-safe evidence that one ordinary Home AI Cluster node started with
an explicitly chosen supported local runtime composition and participated in an
ordinary statically declared heterogeneous cluster without making runtime
identity part of cluster-facing requests, declarations, routing, attribution, or
normalized status.

## Repository revisions

The successful ordinary heterogeneous request used the repository revision after
PR #256:

```text
2e6aeb7096a97fd7eda5155b1131dfe5246cda7d
```

The normalized negative control was repeated after PR #257 at:

```text
472b67710b312f69786af98156bdea37ecdfcede
```

PR #257 changed only the API error boundary for exhausted runtime-unavailable
static fallbacks. It did not change runtime composition, routing, candidate
ordering, fallback conditions, request or result schemas, attribution, adapters,
or proof wiring.

## Topology

```text
calling machine
  ordinary Home AI Cluster static-cluster caller
  ordinary local runtime composition: default Ollama
  caller boundary: http://127.0.0.1:8000/v1/chat

receiving machine
  ordinary Home AI Cluster local runtime process
  explicit local runtime composition: llama-server
  operator-managed llama-server on receiver loopback
  Home AI Cluster receiver port: <RECEIVER_HOME_AI_CLUSTER_PORT>
```

The caller held one explicit declaration for `pi-receiver` at
`http://<RECEIVER_ADDRESS>:<RECEIVER_HOME_AI_CLUSTER_PORT>`. The declaration
contained no receiving runtime, adapter, model, credential, capability, or
lifecycle information.

## Runtime placement

The caller retained the ordinary default Ollama composition. The receiver used
the ordinary `home-ai-cluster-local` command with `--runtime llama-server` to
construct one `LlamaServerAdapter`, one matching ordinary local node, one
`NodeRegistry`, one `AdapterRegistry`, and one `LocalAppComposition`.

The Phase 12 proof-specific receiver command was not used.

## Preconditions

- Two separate trusted-LAN machines used the recorded successful-proof revision.
- The receiver's operator-managed llama-server was reachable only through its
  local loopback boundary from the Home AI Cluster receiver process.
- The receiver's Home AI Cluster port was reachable from the caller.
- The caller used the ordinary static declaration path.
- The operator established the already accepted pre-request
  connection-unavailable condition for the caller's local Ollama connection
  before sending the heterogeneous request.

The failure was not manufactured after request transmission began.

## Receiver startup

The operator started the ordinary receiver through:

```sh
uv run home-ai-cluster-local \
  --runtime llama-server \
  --llama-server-base-url <LLAMA_SERVER_LOOPBACK_URL> \
  --llama-server-model <MODEL_VALUE> \
  --host 0.0.0.0 \
  --port <RECEIVER_HOME_AI_CLUSTER_PORT>
```

The runtime choice and runtime-specific values were consumed only while the
receiving process was constructed. They were not added to any request, remote
declaration, routing candidate, fallback rule, attribution value, or normalized
status shape.

## Receiver status

The operator observed the existing normalized receiver status through:

```sh
curl -s http://<RECEIVER_ADDRESS>:<RECEIVER_HOME_AI_CLUSTER_PORT>/internal/cluster/status
```

The receiver returned:

```json
{"runtime_status":"available"}
```

The status response contained no runtime name, adapter name, model identifier,
base URL, machine identity, or private network address.

## Caller declaration and startup

The caller used one operator-owned declaration equivalent to:

```toml
[[remote_nodes]]
node_id = "pi-receiver"
base_url = "http://<RECEIVER_ADDRESS>:<RECEIVER_HOME_AI_CLUSTER_PORT>"
```

The declaration contained only the cluster-owned remote node identity and its
transport address.

The ordinary caller started through:

```sh
uv run home-ai-cluster-static-cluster --declaration <OPERATOR_DECLARATION_PATH>
```

## Capability-centered request

The request entered through the caller's ordinary `/v1/chat` endpoint:

```json
{
  "messages": [
    {
      "role": "user",
      "content": "Reply with exactly: ordinary heterogeneous cluster works"
    }
  ],
  "capability": "chat"
}
```

The request contained no runtime, adapter, model, or node selector.

## Successful normalized result

The caller returned a successful existing `ClusterResult` equivalent to:

```json
{
  "content": "ordinary heterogeneous cluster works",
  "adapter": "llama-server",
  "model": "<MODEL_VALUE>",
  "node_id": "pi-receiver"
}
```

The final `node_id` was the caller-owned declared remote identity. The runtime
and model observed in the result were execution facts returned through the
existing normalized result contract; they were not request or routing inputs.

## Architecture observations

The ordinary caller attempted its local Ollama candidate first. After the
operator-established accepted pre-request connection-unavailable condition, the
existing static fallback selected the explicitly declared receiver. The ordinary
receiver executed through its process-local explicit llama-server composition
and returned the existing normalized result attributed to `pi-receiver`.

The proof required no proof-specific receiver launcher, runtime-aware remote
declaration, runtime-aware route, model selector, discovery, runtime inventory,
or lifecycle ownership.

## Negative control

The operator stopped the receiver Home AI Cluster process while leaving the
ordinary caller running, then repeated the same capability-centered request.

Before PR #257, this real negative control exposed an unhandled terminal
`RuntimeConnectionUnavailableBeforeRequestError` as HTTP 500. PR #257 corrected
only the API normalization boundary.

After restarting the ordinary static-cluster caller on revision
`472b67710b312f69786af98156bdea37ecdfcede`, the repeated request returned:

```http
HTTP/1.1 503 Service Unavailable
content-type: application/json
```

```json
{"detail":"Runtime adapter unavailable"}
```

The response exposed no remote address, local runtime URL, model identifier,
`httpx` error, connection exception class, transport detail, or traceback.

## Compatibility evidence

Automated verification for the implementation and corrective boundary included:

- zero-argument explicit local startup defaulting to the existing Ollama adapter;
- explicit Ollama startup;
- explicit llama-server startup with required loopback HTTP URL and non-empty
  model identifier;
- invalid combinations failing before `uvicorn.run(...)`;
- construction performing no health probe, chat call, network access, model
  inventory, or runtime lifecycle action;
- one ordinary local node and one adapter per explicit composition;
- ordinary request and normalized status paths consuming `LocalAppComposition`;
- existing `create_app()` and module-level default behavior remaining unchanged;
- exhausted single and ordered static remote fallbacks returning the same stable
  HTTP 503 response without leaking endpoint, exception, or model details.

The final automated suite at the corrective revision reported 572 passing tests,
and Ruff lint passed.

## Privacy review

This record retains only repository revisions, placeholder receiver and runtime
addresses, sanitized commands, one harmless synthetic request, normalized status,
a minimal normalized result with a placeholder model value, and the stable
negative-control response.

It contains no private network address, hostname, username, filesystem path,
credential, token, raw traceback, real model path, prompt history, or unnecessary
model output.

## Result

Phase 13 ordinary explicit local runtime composition proof succeeded.

One operator started an ordinary receiver with an explicitly chosen supported
llama-server composition. An ordinary statically declared caller routed one
capability-centered request to it without runtime identity entering requests,
remote declarations, routing, fallback, attribution, or normalized status.

## Non-goals

This proof does not add request-level runtime selection, multiple local adapters,
automatic runtime choice, engine-aware routing or fallback, discovery, model
inventory, runtime installation, model downloading, supervision, restart,
repair, generic factories, plugins, retained runtime configuration, hidden
environment configuration, persistence, Docker, Kubernetes, a dashboard, or
broader production deployment claims.
