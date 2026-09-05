# Real vLLM Validation

Status: Retained real-runtime evidence

Date: 2026-09-05

## Scope and status

This is post-1.0 retained evidence. It records one real local proof of Accepted
RFC-0107 and its merged Stage 1–3 implementation rail, not a release-documentation
claim. vLLM is not part of the released 1.0.0 baseline. This proof does not, by
itself, make vLLM released or supported 1.0.0 behavior.

The record corresponds to these accepted or merged post-1.0 items:

- Accepted RFC-0107 / PR #669;
- Stage 1 / PR #670;
- Stage 2 / PR #671; and
- Stage 3 / PR #672.

## Proof environment

The proof ran on Ubuntu 26.04.1 LTS, x86_64, with an Intel Core i7-1165G7,
eight logical CPUs, AVX2 and AVX-512, approximately 14 GiB RAM, and 32 GiB
swap. It intentionally used CPU-only vLLM. The host NVIDIA GeForce MX350 was
not used; this is not a general hardware-support matrix.

All mutable proof state was isolated beneath the temporary operator path
`/home/lpa/data/hac-vllm-proof`. That filesystem had 314 GiB free before
installation. Peak proof use was approximately 4.1 GiB, and the complete
scratch directory was removed after the proof. The path is not a product
configuration requirement.

The tested runtime environment was:

```text
vLLM: 0.26.0+cpu
Python: 3.12.8
Torch: 2.11.0+cpu
```

The isolated vLLM wheel supplied `libiomp5.so` and
`libtcmalloc_minimal.so.4`; no system package installation was needed. That
observation is specific to this wheel and environment, not a claim about every
vLLM installation.

The model was `Qwen/Qwen2.5-0.5B-Instruct`, served under the explicit API
identity `hac-vllm-proof`. This small model was chosen for a
correctness/interoperability proof, not as a model-quality or performance
recommendation.

## Operator-managed runtime

The operator started one separate loopback vLLM process before HAC:

```sh
vllm serve Qwen/Qwen2.5-0.5B-Instruct \
  --host 127.0.0.1 \
  --port 8000 \
  --served-model-name hac-vllm-proof \
  --max-model-len 1024 \
  --gpu-memory-utilization 0.5
```

The tested vLLM CPU default attempted to reserve approximately 13.7 GiB while
approximately 8.61 GiB was available. The proof therefore used
`--gpu-memory-utilization 0.5`. Despite its name, this was an operator-side
vLLM CPU memory-reservation control in the tested version. It is not an HAC
configuration fact: HAC did not query, infer, or control vLLM capacity. This
value is not a recommended default.

Before involving HAC, `GET /health` returned HTTP 200. One non-streaming Chat
Completions request returned HTTP 200, model `hac-vllm-proof`, and content
exactly `VLLM_OK`. This separated operator runtime setup correctness from HAC
adapter correctness.

## Ordinary HAC configuration and ownership

With isolated retained configuration, the ordinary Stage 3 surface was used:

```sh
hac config local \
  --runtime vllm \
  --vllm-base-url http://127.0.0.1:8000 \
  --vllm-model hac-vllm-proof
```

`hac config show` reported runtime `vllm`, base URL
`http://127.0.0.1:8000`, and model `hac-vllm-proof`. It observed no live
runtime state. The normal user retained configuration was not modified.

Ordinary `hac local` then started successfully on `127.0.0.1:25042` using
that isolated retained configuration. HAC started only its own ordinary local
process; vLLM was already running as a separate operator-managed process.

```text
ordinary HAC process
        |
        | loopback HTTP
        v
operator-managed vLLM
        |
        v
Qwen/Qwen2.5-0.5B-Instruct
```

Remote HAC architecture is unchanged:

```text
remote HAC caller
        |
        v
HAC receiver
        |
        | loopback
        v
receiver-owned runtime
```

## Capability observations

| Capability | Observation | Attribution / boundary |
| --- | --- | --- |
| Chat | Succeeded; content was exactly `HAC_CHAT_OK`. | `adapter: vllm`, `model: hac-vllm-proof`, `node_id: local` |
| Summarize | A bounded source was summarized successfully. | `adapter: vllm`, `model: hac-vllm-proof`, `node_id: local` |
| Classify | `The invoice is due tomorrow.` with labels `invoice` and `personal` selected `invoice`. | The result was exactly one caller-supplied label; no vLLM-specific structured-output representation leaked into the public HAC result. |
| Code | One textual, non-executing Code request succeeded; returned code was not executed. | `adapter: vllm`, `model: hac-vllm-proof`, `node_id: local` |

The Classify observation validates the intended boundary:

```text
vLLM structured output
        -> adapter-private proposal
        -> HAC exact-label result contract
```

## Unavailable runtime and cleanup

The proof vLLM process was stopped while the ordinary HAC process remained
running. One further ordinary Chat request then returned:

```text
exit status: 1
error: runtime adapter unavailable
```

This is evidence for the existing local runtime-adapter failure boundary only.
It is not execution-availability, scheduling, failover, or remote-fallback
evidence.

Afterward, all proof processes were stopped, ports 8000 and 25042 were free,
and the isolated scratch directory was removed. The repository remained clean;
no normal HAC retained configuration, source, or runtime configuration changed
during the real-runtime proof.

## Conclusions

On this host, version, and model, the evidence establishes that:

1. one real operator-managed loopback vLLM server satisfied the accepted
   `VllmAdapter` transport boundary;
2. ordinary Stage 3 retained vLLM configuration and ordinary HAC local startup
   worked;
3. Chat, Summarize, Classify, and textual Code worked, with truthful available
   adapter/model/node attribution;
4. Classify preserved HAC's exact-label boundary; and
5. stopped vLLM mapped to the existing bounded runtime-adapter-unavailable
   outcome.

The proof required no runtime discovery, lifecycle management, API key,
generic OpenAI-compatible adapter, or HAC capacity/load observation.

## Non-claims

This proof does not establish performance, throughput, latency, model quality,
recommended model choice, recommended memory reservation, GPU support on this
host, distributed vLLM, runtime concurrency capacity, queue depth, scheduling,
load balancing, production network exposure, API-key security, arbitrary LAN
vLLM transport, direct remote-caller-to-vLLM access, multiple local runtime
bindings, capability-specific runtime bindings, or released HAC 1.0.0 support.
