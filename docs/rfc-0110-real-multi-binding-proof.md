# RFC-0110 real multi-binding proof

Status: Retained real-runtime evidence

Date: 2026-09-08

## Scope and baseline

This is post-1.0 retained real-machine evidence for the implemented request-capable
local path accepted by RFC-0110. It records one bounded same-runtime proof; it is
not a release-1.0.0 claim and does not change architecture, runtime behavior, or
observation semantics.

The HAC checkout was exactly commit
`1d097cde5cc9f75f16ef9ce587405e403670f718` on `post-1.0-development`.

## Proof environment

The proof host was Ubuntu 26.04.1 LTS on Linux `7.0.0-30-generic` (`x86_64`).
The operator-managed loopback Ollama service was version `0.30.8`, at
`http://127.0.0.1:11434`. Its already-installed model inventory included
`llama3.2` and `qwen2.5-coder:7b`. HAC was run from the checkout; its command
reported version `1.0.0`.

No practical second concrete runtime was available without installation or a
large model download: vLLM was not installed and the available `llama-server`
had no suitable local generative model. The proof therefore uses the accepted
two-Ollama-instance case. It establishes explicit capability-to-instance
composition, not heterogeneous-runtime behavior.

## Explicit temporary composition

The following temporary file was created outside retained HAC configuration:

```toml
[[bindings]]
capabilities = ["chat", "summarize"]
runtime = "ollama"
model = "llama3.2"

[[bindings]]
capabilities = ["classify", "code"]
runtime = "ollama"
model = "qwen2.5-coder:7b"
```

One foreground HAC process was started from the checkout:

```sh
uv run hac local --runtime-config /tmp/hac-rfc0110-proof.1GBdx7/multi-binding.toml
```

It started process `3851564` at `http://127.0.0.1:25042`. The two bindings
did not create additional HAC nodes.

## Ordinary capability observations

Each ordinary request named only its capability; none selected a runtime,
adapter, model, binding, or node.

| Capability | Ordinary request outcome | Existing truthful attribution |
| --- | --- | --- |
| Chat | `CHAT_BOUND_OK` | `adapter: ollama`, `model: llama3.2`, `node_id: local` |
| Summarize | Produced `The Home AI Cluster uses explicit capability bindings.` | `adapter: ollama`, `model: llama3.2`, `node_id: local` |
| Classify | `The invoice is due tomorrow.` with `invoice` and `personal` selected `invoice` | `node_id: local`; the current compact Classify result exposes no adapter or model field |
| Code | Returned a textual Python `add(a, b)` function | `adapter: ollama`, `model: qwen2.5-coder:7b`, `node_id: local` |

The explicit document assigns Chat and Summarize only to the `llama3.2`
Ollama adapter instance, and Classify and Code only to the
`qwen2.5-coder:7b` Ollama adapter instance. The distinct available model
attribution for the first and fourth request is consistent with those two
separately constructed same-name adapter instances. Every result remained
attributed to the one local HAC node.

## Observation boundary

The optional status negative observation was not performed. In this checkout,
`hac status` first requires a static-cluster declaration; no unrelated topology
was created merely to exercise that optional command. No multi-binding status,
health, preflight, routing-explanation, or inspection semantics were added or
inferred.

## Cleanup

The HAC proof process was stopped cleanly. The temporary runtime-config and
scratch directory were removed. The existing Ollama process was operator
managed and was left running. Normal retained HAC configuration was not
modified, and the repository contained no generated runtime files.

## Conclusion and non-claims

One real HAC local process used explicit disjoint capability bindings to
execute different capabilities through their configured concrete Ollama adapter
instances while preserving one cluster-visible local node.

This proof does not establish heterogeneous-runtime composition, dynamic
runtime selection, runtime discovery, model discovery, scheduling, load
balancing, capacity, concurrency, performance, retained multi-binding
configuration, or multi-binding observation/status semantics.
