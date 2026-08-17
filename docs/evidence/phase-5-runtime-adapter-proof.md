# Phase 5 Evidence — Runtime Adapter Proof

Status: Proof

Date: 2026-07-15

> Retained historical evidence. The narrow
> `phase_5_runtime_adapter_proof` module was removed after this proof completed.
> The commands below record what was actually executed; exact reproduction
> requires the matching historical repository revision. Current multi-runtime
> operation uses ordinary local runtime composition.

This document records the explicit local proof required by accepted RFC-0030.
It is evidence for the shared runtime-adapter boundary. It does not change the
public API, routing, adapter protocol, or node-attribution rules.

## Revision

The proof script was run on branch:

```text
phase-5-runtime-adapter-proof
```

at commit:

```text
40405f9 Add runtime adapter proof script
```

## Local environment

The observed host was Ubuntu Resolute on Linux x86_64.

Observed runtime versions:

```text
ollama version is 0.30.8
llama-server version: 8681 (Debian), built with GNU 15.2.0
```

Ollama was already managed outside the proof script and exposed a local
`llama3.2:latest` model. The proof used no remote runtime or cloud service.

## Explicit llama-server startup

The operator started llama-server outside the proof script with the existing
local GGUF model and loopback-only binding:

```text
llama-server \
  -m /home/lpa/.cache/huggingface/hub/models--ggml-org--gemma-3-1b-it-GGUF/snapshots/f9c28bcd85737ffc5aef028638d3341d49869c27/gemma-3-1b-it-Q4_K_M.gguf \
  --host 127.0.0.1 \
  --port 8080 \
  --alias phase-5-gemma
```

The observed readiness response was:

```json
{"status":"ok"}
```

## Successful shared-boundary proof

The opt-in proof command was:

```text
uv run python -m home_ai_cluster.phase_5_runtime_adapter_proof \
  --ollama-model llama3.2:latest \
  --llama-server-model phase-5-gemma
```

It explicitly constructed `OllamaAdapter` and `LlamaServerAdapter`, passed the
same cluster-owned chat request through the `RuntimeAdapter` shape, and printed
only normalized proof summaries. The command does not start or stop runtimes.

Observed output, with generated content intentionally omitted:

```json
{"adapter":"ollama","content_length":3,"model":"llama3.2:latest"}
{"adapter":"llama-server","content_length":4,"model":"phase-5-gemma"}
```

Both invocations returned `RuntimeResult` data only: adapter identity, optional
model attribution, and normalized content (represented here by its length).
Neither result includes `node_id`.

## Stopped-runtime failure proof

After the successful llama-server request, the operator stopped that explicit
llama-server process. The same adapter was then invoked with:

```text
uv run python -m home_ai_cluster.phase_5_runtime_adapter_proof \
  --adapter llama-server \
  --llama-server-model phase-5-gemma
```

The command exited with status 1 and reported:

```json
{"adapter":"llama-server","error":"RuntimeConnectionUnavailableBeforeRequestError"}
```

No raw `httpx`, llama.cpp, GGUF, or compatibility-protocol exception was
exposed by the proof output.

## Boundary confirmation and limitations

No public endpoint, `/v1/chat` request or response schema, routing behavior,
node attribution, or `RuntimeAdapter` protocol member changed for this proof.
The ordinary test suite remains live-runtime-free; this proof is opt-in and
requires an operator to manage both local runtimes and models explicitly.

The RFC-0030 smallest shared-proof criteria are satisfied by this evidence:

1. ordinary tests run without either runtime;
2. Ollama succeeds through the shared adapter boundary;
3. llama-server runs explicitly on loopback with one local model;
4. llama-server returns a normalized non-streaming `RuntimeResult`;
5. normalized proof output contains only cluster-owned result information; and
6. stopping llama-server returns the existing cluster-owned unavailable error.

This evidence completes the RFC-0030 proof criteria. It does not claim that
all Phase 5 work or future multi-runtime design questions are complete.
