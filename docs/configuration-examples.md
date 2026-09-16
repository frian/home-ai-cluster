---
order: 40
---

# Configuration Examples

Status: Current

Home AI Cluster keeps static-cluster topology declarations and local
runtime-composition files separate. Topology declarations describe explicit
cluster nodes and routing eligibility; runtime-composition files configure only
the caller-local runtime adapter. Neither introduces discovery, scheduling,
supervision, or implicit configuration lookup.

The canonical repository examples remain under [`examples/` on GitHub](https://github.com/frian/home-ai-cluster/tree/main/examples).
Users of an installed HAC package can copy and adapt the TOML shown here into a
local file, then pass that file's path explicitly. From a repository checkout,
the corresponding files under `examples/` can be used directly.

## Static-cluster topology declarations

### One remote node

This saved declaration file form declares one remote node. The `192.0.2.0/24`
address is
documentation address space; replace it with an operator-owned trusted-LAN
address.

Source: [`examples/static-cluster-single-remote.toml`](https://github.com/frian/home-ai-cluster/blob/main/examples/static-cluster-single-remote.toml).

```toml
remote_node_id = "remote-node"
remote_base_url = "http://192.0.2.10:25042"
```

### Two ordered remote nodes

Declaration order is remote priority order. It does not introduce load balancing
or scheduling.

Source: [`examples/static-cluster-two-remotes.toml`](https://github.com/frian/home-ai-cluster/blob/main/examples/static-cluster-two-remotes.toml).

```toml
[[remote_nodes]]
node_id = "remote-a"
base_url = "http://192.0.2.10:25042"

[[remote_nodes]]
node_id = "remote-b"
base_url = "http://192.0.2.11:25042"
```

### Local Chat-only eligibility

`local_capabilities = ["chat"]` restricts caller-local routing eligibility. It
does not disable adapters or configure the runtime; the remote declaration
remains separate.

Source: [`examples/static-cluster-local-chat-only.toml`](https://github.com/frian/home-ai-cluster/blob/main/examples/static-cluster-local-chat-only.toml).

```toml
local_capabilities = ["chat"]

[[remote_nodes]]
node_id = "remote-node"
base_url = "http://192.0.2.10:25042"
```

## Local runtime composition

### Retained local HAC execution limit

Use `hac config local` to retain an HAC execution limit for this machine's
ordinary HAC process:

```sh
hac config local \
  --runtime ollama \
  --ollama-model llama3.2:1b \
  --execution-limit 2
```

This means this HAC process may engage up to two overlapping HAC-owned
execution intervals. The value limits overlapping HAC-owned execution
intervals. It does not describe or guarantee runtime concurrency. It belongs
only to this machine's local HAC configuration; do not add it to `config node`
or a remote declaration.

Inspect retained configuration with:

```sh
hac config show
```

The output displays an explicitly retained local value, or `HAC execution
limit: not retained`. `not retained` preserves the ordinary effective limit of
`1`. This command reports retained configuration only: it does not inspect
current work or runtime load. `hac config local --reset` clears the retained
local record. Configuring a complete local record without `--execution-limit`
also leaves the limit not retained, with effective limit `1`.

### Ollama

`runtime = "ollama"` selects Ollama, and `[ollama]` contains local adapter
configuration. `model` names an already-installed operator-owned model, while
`disable_thinking = true` requests the already-documented Ollama behavior. This
file does not configure topology.

Source: [`examples/runtime-ollama.toml`](https://github.com/frian/home-ai-cluster/blob/main/examples/runtime-ollama.toml).

```toml
runtime = "ollama"

[ollama]
# Replace with an already-installed operator-owned Ollama model.
model = "replace-with-installed-model"
disable_thinking = true
```

### llama-server

`runtime = "llama-server"` selects an already-running local llama-server. Its
base URL points to that server, and `model` is the server's model identifier.
This file does not start or supervise llama-server and does not configure
topology.

Source: [`examples/runtime-llama-server.toml`](https://github.com/frian/home-ai-cluster/blob/main/examples/runtime-llama-server.toml).

```toml
runtime = "llama-server"

[llama_server]
# Adapt this loopback port to the already-running local llama-server.
base_url = "http://127.0.0.1:8080"
# Replace with that server's model identifier.
model = "replace-with-server-model"
```

## Using the files

Use topology declarations explicitly with the ordinary static-cluster commands:

```sh
hac preflight --declaration <PATH>
hac status --declaration <PATH>
hac static-cluster --declaration <PATH>
```

Use a runtime-composition file explicitly for the caller-local adapter:

```sh
hac local --runtime-config <PATH>

hac static-cluster \
  --declaration <TOPOLOGY_PATH> \
  --runtime-config <RUNTIME_PATH>

hac status \
  --declaration <TOPOLOGY_PATH> \
  --runtime-config <RUNTIME_PATH>
```

The existing single-runtime file shape works with all three commands. An
RFC-0110 multi-binding file uses only `[[bindings]]` entries and is accepted by
request-capable `hac local` and `hac static-cluster`; `hac status` rejects it
locally before observation, and `hac health` remains unchanged.

These are explicit declaration and runtime-composition files: commands use them
only when their paths are supplied. They are distinct from HAC-managed retained
configuration created with `hac config`. That retained configuration is an
ordinary baseline for `hac static-cluster` when applicable, but bare
`hac preflight` remains local-only and `hac status` requires
`--declaration <PATH>`. `--runtime-config` remains a self-contained alternate
runtime-composition source and does not carry an HAC execution limit.

From a repository checkout, the example files are available directly under
`examples/`. See the [Command Reference](command-reference.md) for exact command
contracts and the [Canonical Operator Workflow](operator-workflow.md) for the
supported operating procedure.
