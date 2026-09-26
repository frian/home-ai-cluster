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

The three single-runtime files construct one local runtime composition:

- `runtime-ollama.toml` is the ordinary Ollama composition. It intentionally
  omits temperature, preserving the runtime's native sampling behavior.
- `runtime-llama-server.toml` is the minimal llama-server composition.
- `runtime-vllm.toml` is the minimal vLLM composition.

`runtime-ollama-explicit-temperature.toml` demonstrates an operator-controlled
RFC-0125 temperature without recommending a value. Omission and an explicit
zero or non-zero value are distinct operator choices.

`runtime-multi-binding.toml` demonstrates multiple explicit local capability
bindings. Each binding owns its concrete runtime composition; any temperature
belongs to that binding rather than to a capability.

`runtime-stable-diffusion-cpp.toml` demonstrates RFC-0126's explicit
image-only multi-binding construction for an already-running local `sd-server`.
Its illustrative port must be adapted to the operator's endpoint; it is not a
HAC default and does not provide an Image Generation request/output surface.

`runtime-ollaya.toml` demonstrates RFC-0141's explicit classify-only
multi-binding construction for an already-running local Ollaya runtime. Its
endpoint and model are explicit; `laya` is an example, not a HAC default or
recommendation. HAC performs no runtime or model discovery, and Ollaya is not
available through ordinary `--runtime`.

Select a file explicitly with `--runtime-config`; it does not configure
topology, and there is no implicit config discovery. A runtime-composition file
cannot be combined with an equivalent runtime CLI argument explicitly supplied
by the operator. Files are self-contained and do not inherit retained
runtime-composition values.

The `[ollama]` table and its `model` and `disable_thinking` values are optional
under the accepted schema. Their omission preserves existing defaults.
`llama-server` requires both `base_url` and `model` in `[llama_server]`.

Topology declarations and runtime-composition files have different ownership
and meaning. A static-cluster declaration describes declared nodes and
caller-local eligibility; a runtime-composition file constructs only the local
adapter for the current process.

```sh
hac local --runtime-config examples/runtime-ollama.toml

hac local --runtime-config examples/runtime-llama-server.toml

hac local --runtime-config examples/runtime-vllm.toml

hac local --runtime-config examples/runtime-ollama-explicit-temperature.toml

hac local --runtime-config examples/runtime-multi-binding.toml

hac local --runtime-config examples/runtime-ollaya.toml

hac static-cluster \
  --declaration examples/static-cluster-two-remotes.toml \
  --runtime-config examples/runtime-ollama.toml

hac status \
  --declaration examples/static-cluster-two-remotes.toml \
  --runtime-config examples/runtime-ollama.toml
```

## Other post-1.0 operator surfaces

Retain one local runtime composition for ordinary later invocations with
[`hac config local`](../docs/command-reference.md#hac-config), for example:

```sh
hac config local --runtime ollama --ollama-model <MODEL_IDENTIFIER>
```

Use bounded workspace-aware Code with explicit local authority:

```sh
hac code-workspace --root <PATH> --grant list --grant read "<INSTRUCTION>"
```

RFC-0126 provides explicit multi-binding runtime configuration for the accepted
local Image Generation adapter, but bounded local Image Generation still has no
ordinary CLI, request/output, or browser surface; see the
[stable-diffusion.cpp Image Generation proof](../docs/stable-diffusion-cpp-image-generation-proof.md)
for its current local composition boundary.
