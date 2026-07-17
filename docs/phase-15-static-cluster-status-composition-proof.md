# Phase 15 Static-Cluster Status Composition Proof

Status: Retained

Date: 2026-07-18

## Scope

This record retains privacy-safe evidence that the ordinary
`home-ai-cluster-status` command can inspect one explicitly selected local
llama-server composition while preserving normalized, engine-independent cluster
status output.

The proof used ordinary operator-owned processes on one trusted host. It did not
use custom Python wiring, a proof-specific launcher, mocked adapters, Docker,
Kubernetes, runtime discovery, persisted runtime configuration, or request-level
runtime selection.

## Observed revision

The operator executed the proof against this repository revision:

```text
2278f4d37f80748e88c863f54c32144c0fc28337
```

This revision contains the merged RFC-0044 implementation for explicit
static-cluster status composition. The retained proof document was added later
from the repository main branch after the proof runbook had been merged.

## Topology

The proof used separate ordinary processes on one trusted host:

```text
operator-managed llama-server
  loopback runtime boundary: http://127.0.0.1:<LOCAL_RUNTIME_PORT>
  explicit model alias: <LOCAL_MODEL_IDENTIFIER>

ordinary Home AI Cluster remote node
  command: home-ai-cluster-local
  remote boundary: http://127.0.0.1:<REMOTE_HOME_AI_CLUSTER_PORT>

finite status inspection
  command: home-ai-cluster-status
  declaration: one explicit remote node
  selected local composition: llama-server for explicit observations
  selected local composition: default Ollama for compatibility observation
```

The processes were distinct ordinary processes. This proof does not claim
physical-machine separation or network-isolation coverage.

## Sanitized declaration

The declaration used for all observations was equivalent to:

```toml
[[remote_nodes]]
node_id = "proof-remote"
base_url = "http://127.0.0.1:<REMOTE_HOME_AI_CLUSTER_PORT>"
```

The declaration contained no runtime choice, adapter name, model identifier,
local runtime URL, credential, lifecycle configuration, or request selector.

## Sanitized runtime command

The operator-managed llama-server was equivalent to:

```sh
llama-server \
  -hf <MODEL_SOURCE> \
  --alias <LOCAL_MODEL_IDENTIFIER> \
  --host 127.0.0.1 \
  --port <LOCAL_RUNTIME_PORT> \
  -c <CONTEXT_SIZE> \
  -t <THREAD_COUNT>
```

## Sanitized explicit status command

The positive and negative observations used the same ordinary command shape:

```sh
uv run home-ai-cluster-status \
  --declaration <DECLARATION_PATH> \
  --runtime llama-server \
  --llama-server-base-url http://127.0.0.1:<LOCAL_RUNTIME_PORT> \
  --llama-server-model <LOCAL_MODEL_IDENTIFIER>
```

Only the availability of the operator-managed llama-server changed between the
positive and negative observations.

## Directly observed evidence

### Explicit llama-server available

With the selected llama-server available and the declared remote ordinary node
available, the command returned exactly this normalized result:

```json
{"declaration_status":"coherent","nodes":[{"node_id":"local","application_status":"local","runtime_status":"available"},{"node_id":"proof-remote","application_status":"reachable","runtime_status":"available"}]}
```

This directly shows that:

- the declaration remained coherent;
- the fixed local node remained `local`;
- the explicitly selected local composition was observed as available;
- the declared remote remained reachable and available;
- declaration order was preserved; and
- no runtime, adapter, model, URL, executable, filesystem path, or private machine
  identity appeared in the normalized result.

### Explicit llama-server unavailable

The operator stopped only the selected llama-server and reran the same explicit
status command without changing the declaration or runtime arguments. The command
returned exactly:

```json
{"declaration_status":"coherent","nodes":[{"node_id":"local","application_status":"local","runtime_status":"unavailable"},{"node_id":"proof-remote","application_status":"reachable","runtime_status":"available"}]}
```

This directly shows that:

- the declaration remained coherent;
- the fixed local node remained present;
- local runtime unavailability normalized to `unavailable`;
- the declared remote was still observed normally and remained available; and
- no raw adapter exception, runtime URL, model identifier, transport detail, or
  private machine identity appeared.

The command did not switch the explicit llama-server selection to Ollama.

### No-option Ollama compatibility

With the ordinary default Ollama service available, the operator ran:

```sh
uv run home-ai-cluster-status \
  --declaration <DECLARATION_PATH>
```

The command returned exactly:

```json
{"declaration_status":"coherent","nodes":[{"node_id":"local","application_status":"local","runtime_status":"available"},{"node_id":"proof-remote","application_status":"reachable","runtime_status":"available"}]}
```

The normalized output intentionally contains no runtime identity. The merged
focused tests on the observed revision establish that the no-option composition is
the existing Ollama-backed default; the real operator observation confirms that
this compatibility path remained operational.

## Privacy and boundary observations

The retained declaration and outputs contain only the approved proof node identity
`proof-remote` and normalized cluster-facing status values.

This record retains no real hostname, private address beyond loopback, port,
username, absolute filesystem path, model source, model identifier, credential,
authorization header, environment dump, process listing, runtime log, exception,
HTTP trace, prompt, generated response, or screenshot.

Runtime choice, runtime URL, and model identifier remained operator-owned process
inputs. They did not become part of the declaration, status schema, topology,
request, routing, fallback, or node attribution.

## Proof obligations covered

- The ordinary status command accepted the same explicit llama-server composition
  inputs used by ordinary static-cluster startup.
- The selected local composition was inspected through the fixed local node.
- Available and unavailable local runtime states used only existing normalized
  status vocabulary.
- Declared remotes remained observed through the existing normalized status
  protocol and in declaration order.
- The declaration remained topology-only.
- Normalized output contained no runtime, adapter, model, URL, or private machine
  identity.
- The no-option status path remained operational and compatible with the existing
  Ollama-backed default established by focused tests.
- No routing, fallback, request, discovery, inventory, scheduling, lifecycle,
  monitoring, persistence, plugin, database, dashboard, Docker, or Kubernetes
  behavior was introduced or required.

## Limitations

This was a trusted-host proof using separate ordinary processes, not a physical
multi-machine proof. It did not inspect packet traffic and does not claim network
isolation, discovery, model inventory, lifecycle ownership, scheduling, runtime
repair, or remote process control.

The real normalized status output cannot identify the selected runtime by design.
The explicit operator command and focused construction tests establish the runtime
composition used for each observation.

## Conclusion

The Phase 15 operator proof succeeded. One ordinary status command inspected an
explicit local llama-server composition as available, normalized the same selected
composition as unavailable after only llama-server stopped, continued to observe
the declared remote through the existing protocol, and preserved the operational
no-option Ollama compatibility path without exposing runtime-private identity in
cluster status or topology.
