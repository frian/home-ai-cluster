# Phase 12 Heterogeneous Runtime Cluster Proof

Status: Pending operator execution

## Purpose

Retain privacy-safe evidence that one ordinary capability-centered request can
cross an explicitly declared static cluster while the calling machine uses
Ollama and the receiving machine executes through the existing
`LlamaServerAdapter`.

## Repository revision

No real two-machine execution has been performed yet. The operator must use the
same committed proof-branch revision on both machines and record that exact
commit here after successful execution.

Automated validation for the proof launcher is recorded by this draft pull
request; it is not retained evidence of a real heterogeneous request.

## Topology

```text
calling machine
  ordinary Home AI Cluster static-cluster caller
  local runtime: Ollama
  local candidate attempted first

receiving machine
  Phase 12 proof-scoped receiving application
  local adapter: LlamaServerAdapter
  operator-managed llama-server
```

Only the caller holds the explicit static declaration. It contains the declared
receiver node ID and the receiver Home AI Cluster base URL, not runtime, adapter,
model, credential, or lifecycle data.

## Runtime placement

The calling machine retains ordinary local Ollama wiring. The receiving proof
launcher explicitly constructs one `LlamaServerAdapter`; llama-server and its
model remain fully operator-managed and loopback-reachable from the receiving
Home AI Cluster process.

## Preconditions

- Two separate trusted-LAN machines are available to the operator.
- Both check out the same committed proof-branch revision.
- The caller has a usable local Ollama runtime before the fallback observation.
- The receiver has an operator-managed llama-server and model available only to
  its local Home AI Cluster process.
- The receiver Home AI Cluster port is reachable from the caller for the proof.
- The operator owns all runtime and process lifecycle actions.

## Commands

On the receiving machine, start the proof-scoped receiver:

```sh
uv run home-ai-cluster-phase-12-heterogeneous-receiver \
  --host 0.0.0.0 \
  --port <RECEIVER_HOME_AI_CLUSTER_PORT> \
  --llama-server-base-url <LLAMA_SERVER_LOOPBACK_URL> \
  --llama-server-model <MODEL_VALUE>
```

Confirm its normalized local status endpoint before the caller request:

```sh
curl -s http://<RECEIVER_ADDRESS>:<RECEIVER_HOME_AI_CLUSTER_PORT>/internal/cluster/status
```

On the calling machine, create one temporary operator-owned declaration:

```toml
[[remote_nodes]]
node_id = "phase-12-receiver"
base_url = "http://<RECEIVER_ADDRESS>:<RECEIVER_HOME_AI_CLUSTER_PORT>"
```

Start the ordinary caller and use the existing static declaration path:

```sh
uv run home-ai-cluster-static-cluster --declaration <OPERATOR_DECLARATION_PATH>
```

Before sending the request, use the existing operator-owned fallback-proof
method to make the caller's Ollama connection unavailable before request
transmission. Do not alter application configuration or manufacture a failure
after request execution begins.

## Request

Send one harmless request to the caller's ordinary boundary. It contains no
runtime, adapter, model, or node selector:

```sh
curl -s http://127.0.0.1:8000/v1/chat \
  -H 'content-type: application/json' \
  -d '{"messages":[{"role":"user","content":"Reply with: ok"}],"capability":"chat"}'
```

## Normalized result

Pending real operator execution. A successful retained result will record only
the existing normalized fields with a minimal non-sensitive response, for
example:

```json
{"content":"ok","adapter":"llama-server","model":"<MODEL_VALUE>","node_id":"phase-12-receiver"}
```

The final node attribution must be the caller-owned declared remote ID.

## Status observation

Pending real operator execution. The receiver must return its existing
normalized status shape before the caller request:

```json
{"runtime_status":"available"}
```

The calling status observation, when performed, must preserve the existing
status vocabulary and report the declared remote node ID without runtime or
model identity.

## Architecture observations

Automated launcher tests verify only proof-scoped construction: one local
`chat` node, one matching `llama-server` adapter, and one
`create_proof_receiving_app(...)` call. The ordinary caller remains the existing
static-cluster process and retains local-first routing plus its accepted narrow
pre-request connection-unavailable fallback.

No runtime identity is added to the declaration or request. The caller crosses
the existing normalized internal request and status boundaries and does not
select the receiving runtime, adapter, or model.

## Privacy review

No real-machine evidence has been collected. This pending record contains only
placeholders, a harmless request, and expected normalized shapes. It contains no
private address, hostname, username, path, credential, token, raw runtime log,
full prompt, or generated response.

## Result

Pending operator execution. The real two-machine proof has not been run, so this
document does not claim success or Phase 12 completion.

## Non-goals

This proof does not add ordinary runtime selection, declaration runtime fields,
engine-aware routing or fallback, status protocol changes, a new adapter,
adapter factories, discovery, model inventory, runtime installation or
lifecycle management, persistence, Docker, Kubernetes, or a third machine.
