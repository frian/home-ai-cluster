# Phase 14 Static-Cluster Local Composition Proof

Status: Retained

Date: 2026-07-17

## Scope

This record retains privacy-safe evidence that the ordinary
`home-ai-cluster-static-cluster` command can construct one explicitly selected
local runtime composition while retaining capability-centered, engine-independent
cluster behavior.

The proof used ordinary operator-owned processes only. It did not use a
proof-specific launcher, custom Python wiring, mocked adapter, test client,
runtime discovery, runtime selector in a request, Docker, or Kubernetes.

## Revision

The observed proof run used this repository revision:

```text
d26eb7524aa8bbea72193cc4a35d7ad81247b53d
```

## Topology

The proof used two separate ordinary Home AI Cluster processes as equivalent
operator-owned nodes on one trusted host:

```text
caller node
  ordinary home-ai-cluster-static-cluster process
  explicit local composition: operator-managed llama-server on loopback
  caller boundary: http://127.0.0.1:<HOME_AI_CLUSTER_PORT>

declared remote node
  ordinary home-ai-cluster-local process
  ordinary default Ollama composition
  remote boundary: http://<REMOTE_HOST>:<REMOTE_HOME_AI_CLUSTER_PORT>
```

The processes were distinct ordinary nodes and communicated through the normal
static remote HTTP path. The proof did not claim physical-machine separation;
that remains the limitation of this retained run.

## Preconditions

- An operator-managed llama-server accepted one locally available model on the
  caller's loopback interface.
- An operator-managed Ollama service accepted one locally available model for
  the declared ordinary remote node.
- The caller and remote Home AI Cluster processes used the recorded revision.
- The caller's declaration contained only one remote node identity and its
  Home AI Cluster transport address.

## Sanitized commands

The ordinary remote node used the existing default Ollama composition:

```sh
uv run home-ai-cluster-local \
  --host 127.0.0.1 \
  --port <REMOTE_HOME_AI_CLUSTER_PORT>
```

The ordinary caller used the accepted explicit llama-server composition:

```sh
uv run home-ai-cluster-static-cluster \
  --declaration <DECLARATION_PATH> \
  --runtime llama-server \
  --llama-server-base-url http://127.0.0.1:<LOCAL_RUNTIME_PORT> \
  --llama-server-model <LOCAL_MODEL_IDENTIFIER>
```

No retained command contains a real hostname, port, filesystem path, or model
identifier.

## Sanitized declaration

The caller's declaration was equivalent to:

```toml
[[remote_nodes]]
node_id = "proof-remote"
base_url = "http://<REMOTE_HOST>:<REMOTE_HOME_AI_CLUSTER_PORT>"
```

It contains no local runtime choice, adapter, local runtime URL, model,
credential, or lifecycle setting.

## Directly observed evidence

### Startup and normalized status

Both ordinary Home AI Cluster processes started successfully. While the caller's
explicit local llama-server composition was running, the caller returned the
existing engine-independent status:

```json
{"runtime_status":"available"}
```

The remote node returned the same normalized status shape. Neither retained
status value names a runtime, adapter, model, or node.

### Successful capability-centered request

The caller received one ordinary request equivalent to:

```json
{
  "messages":[{"role":"user","content":"Reply with exactly: proof ok"}],
  "capability":"chat"
}
```

The request contained no runtime, adapter, model, or node selector. The
minimal successful result content was `Proof OK`, and the cluster-owned
attribution was:

```json
{"node_id":"local"}
```

This directly observed local attribution, together with the operator-owned
caller startup command, shows that the explicitly selected local composition
handled the primary request. Runtime identity is not inferred from status or
attribution.

### Narrow fallback observation

The operator stopped the caller's loopback llama-server before transmitting a
second request, while leaving the declared ordinary Ollama node available. The
same capability-centered request shape then succeeded with minimal content
`fallback ok` and cluster-owned attribution:

```json
{"node_id":"proof-remote"}
```

This directly observed the declared remote as the accepted bounded fallback.
The successful primary request above establishes that the local candidate was
first; the fallback ran only after the local runtime became unavailable before
request transmission.

### Negative control

After the declared remote Home AI Cluster process was stopped as well, the
caller received one further capability-centered request. The normalized result
was exactly:

```http
HTTP/1.1 503 Service Unavailable
```

```json
{"detail":"Runtime adapter unavailable"}
```

No raw adapter exception, runtime URL, model value, remote address, or transport
detail appeared in that cluster-facing failure.

## Privacy and boundary observations

The retained request, normalized status, selected-node attribution, fallback
attribution, declaration, and negative-control failure contain no runtime,
adapter, model, or node selector beyond the declaration's accepted remote node
identity. The ordinary caller emitted no separate routing-explanation payload,
so none is retained. No request-history recording command was invoked, and no
history payload is retained here.

The explicit local runtime values were operator-owned startup inputs only. The
retained record replaces their real values with placeholders. It contains no
real IP address, hostname, username, absolute filesystem path, token,
credential, raw log, full prompt, full model response, or process listing.

The implementation's focused construction tests on this revision establish that
runtime argument parsing and composition construction do not probe a runtime.
This retained operator run did not use packet capture; the no-probe conclusion
is therefore an implementation-boundary conclusion, not a claim of direct
network tracing.

## Proof obligations covered

- The ordinary static-cluster command accepted one explicit supported local
  llama-server composition.
- The ordinary default Ollama remote node remained declaration-backed and
  topology-only.
- The successful request remained capability-centered and selected the local
  candidate first.
- The declared remote remained available only as the accepted narrow fallback.
- Cluster-facing status and attribution remained engine-independent.
- Exhausted pre-request availability normalized to the required HTTP 503 body.
- No generic runtime abstraction, runtime discovery, lifecycle feature, or
  proof-specific launcher was introduced or used.

## Limitations

This was an equivalent-node proof using two ordinary processes on one trusted
host, not a physical two-machine network-separation proof. It does not add a
claim about discovery, model inventory, runtime lifecycle ownership, scheduling,
or remote process control.

## Conclusion

The Phase 14 ordinary static-cluster local composition proof succeeded. One
ordinary caller selected an explicit local llama-server composition, served a
capability-centered request locally, used one declared ordinary Ollama node as
the accepted narrow fallback when needed, and normalized exhausted availability
without exposing runtime-private details.
