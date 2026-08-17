# Phase 12 Heterogeneous Runtime Cluster Proof

Status: Retained

> Historical proof. `home-ai-cluster-phase-12-heterogeneous-receiver` was later
> retired by RFC-0075. The command below records what was actually used; exact
> reproduction requires the matching historical repository revision. Current
> heterogeneous ordinary operation uses `home-ai-cluster-local --runtime
> llama-server`.

## Purpose

Retain privacy-safe evidence that one ordinary capability-centered request
crossed an explicitly declared static cluster while the calling machine used
Ollama and the receiving machine executed through the existing
`LlamaServerAdapter`.

## Repository revision

Both machines used this repository revision:

```text
950be2e736c5562f22e33be9157b58bec87c94ab
```

## Topology

```text
calling machine
  Home AI Cluster ordinary static-cluster caller
  ordinary local runtime: Ollama
  caller boundary: http://127.0.0.1:8000/v1/chat

receiving machine
  Phase 12 proof-scoped Home AI Cluster receiver
  existing LlamaServerAdapter
  operator-managed llama-server on receiver loopback
  Home AI Cluster receiver port: <RECEIVER_HOME_AI_CLUSTER_PORT>
```

The caller held one explicit declaration for `phase-12-receiver` at
`http://<RECEIVER_ADDRESS>:<RECEIVER_HOME_AI_CLUSTER_PORT>`. The declaration
contained no receiving runtime, adapter, model, credential, or lifecycle
information.

## Runtime placement

The caller retained ordinary local Ollama wiring. The receiver used the
proof-scoped launcher to construct one existing `LlamaServerAdapter` for its
operator-managed loopback llama-server and model.

## Preconditions

- Two separate trusted-LAN machines used the recorded repository revision.
- The receiver's operator-managed llama-server was reachable locally from its
  Home AI Cluster process.
- The receiver's Home AI Cluster port was reachable from the caller.
- The operator established the already accepted pre-request
  connection-unavailable condition for the caller's local Ollama connection
  before sending the request.

The failure was not manufactured after request execution began.

## Commands

On the receiving machine, the operator started the proof-scoped receiver:

```sh
uv run home-ai-cluster-phase-12-heterogeneous-receiver \
  --host 0.0.0.0 \
  --port <RECEIVER_HOME_AI_CLUSTER_PORT> \
  --llama-server-base-url <LLAMA_SERVER_LOOPBACK_URL> \
  --llama-server-model <MODEL_VALUE>
```

The operator confirmed receiver status through:

```sh
curl -s http://<RECEIVER_ADDRESS>:<RECEIVER_HOME_AI_CLUSTER_PORT>/internal/cluster/status
```

The caller used one operator-owned declaration equivalent to:

```toml
[[remote_nodes]]
node_id = "phase-12-receiver"
base_url = "http://<RECEIVER_ADDRESS>:<RECEIVER_HOME_AI_CLUSTER_PORT>"
```

The ordinary caller was started through the existing declaration path:

```sh
uv run home-ai-cluster-static-cluster --declaration <OPERATOR_DECLARATION_PATH>
```

## Request

The request entered through the caller's ordinary `/v1/chat` endpoint. It
contained no runtime, adapter, model, or node selector:

```json
{
  "messages": [
    {
      "role": "user",
      "content": "Reply with exactly: ok"
    }
  ],
  "capability": "chat"
}
```

## Normalized result

The caller returned this successful normalized result:

```json
{
  "content": "ok",
  "adapter": "llama-server",
  "model": "phase-12-model",
  "node_id": "phase-12-receiver"
}
```

The final node attribution is the caller-owned declared remote ID.

## Status observation

Before the request, the receiver returned this existing normalized status shape:

```json
{"runtime_status":"available"}
```

The observation used:

```text
http://<RECEIVER_ADDRESS>:<RECEIVER_HOME_AI_CLUSTER_PORT>/internal/cluster/status
```

## Architecture observations

The ordinary caller attempted its local Ollama candidate first. After the
operator-established accepted pre-request connection-unavailable condition,
existing static fallback selected the explicitly declared receiver once. The
receiver executed through `LlamaServerAdapter`, and the caller returned the
existing normalized result with declared remote-node attribution.

The static declaration and request remained free of runtime, adapter, model, and
node-selection fields. Existing status, routing, fallback, request, result, and
attribution contracts remained unchanged.

## Privacy review

This record retains only the repository revision, placeholder receiver address
and port, sanitized commands, the harmless request, normalized status, and the
minimal successful normalized result. It contains no private address, hostname,
username, home path, credential, token, raw log, or unnecessary model output.

## Result

Phase 12 heterogeneous runtime cluster proof succeeded.

## Non-goals

This proof does not add ordinary runtime selection, declaration runtime fields,
engine-aware routing or fallback, status protocol changes, a new adapter,
adapter factories, discovery, model inventory, runtime installation or
lifecycle management, persistence, Docker, Kubernetes, or a third machine.
