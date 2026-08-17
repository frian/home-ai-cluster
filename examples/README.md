# Topology and Local Runtime Composition Examples

These examples retain two separate kinds of operator-owned TOML documents:
static-cluster topology declarations and local runtime-composition files.

## Static-cluster topology declarations

These small examples show accepted static-cluster declaration shapes. Replace
the `192.0.2.0/24` documentation addresses with operator-owned trusted-LAN
addresses before use.

- `static-cluster-single-remote.toml` shows the minimal legacy flat declaration
  for one remote.
- `static-cluster-two-remotes.toml` shows the ordered `[[remote_nodes]]`
  collection form for two remotes. Declaration order is the remote priority
  order.
- `static-cluster-local-chat-only.toml` restricts only the caller-local routing
  candidate to `chat`; a `summarize` request cannot use that local candidate.

Do not combine the flat single-remote form with the `[[remote_nodes]]`
collection form.

`local_capabilities` configures only caller-local routing eligibility. It does
not configure a local runtime or model, assert remote capabilities, or verify
remote runtime support. The local chat-only example intentionally omits remote
capability fields; their compatibility default does not verify that a receiver
can serve a request. A remote must be eligible under the active static routing
declaration for a routed capability.

These examples configure explicit topology and caller-local capability
eligibility only. They do not configure runtime, model, timeout, retry,
discovery, scheduling, or supervision.

Use a declaration with the existing finite commands:

```sh
hac preflight --declaration examples/static-cluster-two-remotes.toml
hac status --declaration examples/static-cluster-two-remotes.toml
hac static-cluster --declaration examples/static-cluster-two-remotes.toml
```

See the [canonical operator workflow](../docs/operator-workflow.md) and
[command reference](../docs/command-reference.md) for the supported procedure
and command boundaries.

## Local runtime-composition files

`runtime-ollama.toml` and `runtime-llama-server.toml` configure only this
process's local adapter composition. Select one explicitly with
`--runtime-config`; it does not configure topology, and there is no implicit
config discovery. A runtime-composition file cannot be combined with an
equivalent runtime CLI argument explicitly supplied by the operator.

The `[ollama]` table and its `model` and `disable_thinking` values are optional
under the accepted schema. Their omission preserves existing defaults.
`llama-server` requires both `base_url` and `model` in `[llama_server]`.

Topology declarations and runtime-composition files have different ownership
and meaning. A static-cluster declaration describes declared nodes and
caller-local eligibility; a runtime-composition file constructs only the local
adapter for the current process.

```sh
hac local --runtime-config examples/runtime-ollama.toml

hac static-cluster \
  --declaration examples/static-cluster-two-remotes.toml \
  --runtime-config examples/runtime-ollama.toml

hac status \
  --declaration examples/static-cluster-two-remotes.toml \
  --runtime-config examples/runtime-ollama.toml
```
