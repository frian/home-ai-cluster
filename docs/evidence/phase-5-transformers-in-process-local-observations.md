# Phase 5 Evidence — Transformers In-Process Local Observations

Status: Investigation

Date: 2026-07-15

This document records direct observations from André's Linux machine for the
Phase 5 Python in-process runtime investigation. It is descriptive only and
makes no architectural decision.

## Candidate under test

The disposable experiment used:

```text
Python 3.12
PyTorch 2.13.0+cu130
Transformers 5.13.1
HuggingFaceTB/SmolLM2-360M-Instruct
x86_64 Linux
CPU execution
```

PyTorch reported:

```text
cuda available: False
```

The installed PyTorch build included CUDA support, but the observed execution
path was CPU-only.

Evidence type: direct command output.

## Isolation from the project

The experiment was created outside the repository under:

```text
~/tmp/home-ai-cluster-phase-5/transformers
```

A disposable virtual environment was created with `uv`. No Home AI Cluster
source file, project dependency, lockfile, or configuration file was modified.

Evidence type: disposable local experiment.

## Runtime shape

The model and tokenizer were loaded directly through Python library calls:

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
model = AutoModelForCausalLM.from_pretrained(MODEL_ID)
```

Generation was performed by calling:

```python
model.generate(...)
```

No HTTP server, daemon, port, socket endpoint, or external runtime process was
created by the probe.

This directly exercises an in-process runtime boundary rather than the HTTP
runtime boundary used by the currently investigated server candidates.

Evidence type: disposable local experiment.

## Role-based conversation history

The probe supplied this role sequence:

```text
system
user
assistant
user
```

The messages were passed to the tokenizer chat template and then to the model.
The final user message asked the model to recall the name introduced earlier in
the conversation.

Observed response:

```text
Your name is Andre.
```

This directly proves that the tested model and chat template can represent the
current role-based conversation history without converting the conversation to
runtime-owned response identifiers or persistent chat state.

Evidence type: disposable local experiment.

## First acquisition and generation

On the first execution, the Hugging Face client downloaded tokenizer files,
configuration files, and model weights.

Observed model acquisition included:

```text
model.safetensors: approximately 724 MB reconstructed
```

Observed timings:

```text
load_seconds: 61.128
generation_seconds: 0.453
response: 'Your name is Andre.'
```

The first load measurement includes network acquisition and local file
reconstruction. It is not a cached local startup measurement.

Evidence type: disposable local experiment.

## Cached execution

The same probe was run again after the model was present in the local cache.

Observed timings:

```text
load_seconds: 1.404
generation_seconds: 0.412
response: 'Your name is Andre.'
```

The model weights were loaded locally and no model file was downloaded again.
The normal client mode still emitted an unauthenticated Hugging Face Hub warning.

Evidence type: disposable local experiment.

## Strict offline execution

The probe was then run with:

```text
HF_HUB_OFFLINE=1
```

Observed timings:

```text
load_seconds: 0.430
generation_seconds: 0.378
response: 'Your name is Andre.'
```

The run completed using only locally cached files. This directly proves that,
after explicit model acquisition, the tested runtime can load and generate
without network access.

The experiment also used `local_files_only=True` in later probes. An eventual
adapter could therefore make local-only loading explicit rather than relying
only on process-wide environment configuration.

Whether local-only behavior is mandatory for a future adapter is an
architectural decision for RFC-0030, not a conclusion of this evidence record.

Evidence type: disposable local experiment.

## Missing local model behavior

A probe attempted to load this nonexistent model identifier:

```text
home-ai-cluster/does-not-exist
```

with:

```python
AutoTokenizer.from_pretrained(
    MODEL_ID,
    local_files_only=True,
)
```

Observed exception:

```text
exception_type: OSError
exception_module: builtins
message: We couldn't connect to 'https://huggingface.co' to load the files, and couldn't find them in the cached files.
```

The exception message combines cache absence, network unavailability, and
installation guidance. The raw exception does not provide a narrow,
cluster-owned model-unavailable category.

This failure is not a connection failure to a runtime server. The runtime is
the current Python process, and the failure occurred while resolving local model
artifacts before generation.

Any normalization of this failure belongs to an eventual adapter and must be
decided by RFC-0030.

Evidence type: disposable local experiment.

## Unknown message role behavior

A probe supplied this message:

```json
{
  "role": "does-not-exist",
  "content": "Hello"
}
```

to `tokenizer.apply_chat_template(...)`.

Observed result:

```text
accepted
```

No exception was raised.

This directly proves that the tested Transformers chat-template path does not
provide universal validation of Home AI Cluster message roles. Validation
behavior depends on the selected model template and cannot be assumed to be a
runtime-wide contract.

This observation does not determine whether validation belongs in the core,
the adapter, or another boundary. That ownership remains subject to existing
contracts and RFC-0030.

Evidence type: disposable local experiment.

## Normalization surface

The generated token sequence was sliced after the input token count and decoded
locally:

```python
generated_ids = output_ids[0, inputs["input_ids"].shape[1] :]
content = tokenizer.decode(
    generated_ids,
    skip_special_tokens=True,
).strip()
```

The observed assistant content was therefore available as a plain string without
exposing PyTorch tensors, tokenizer objects, model objects, generation metadata,
or Transformers-specific types to the cluster core.

Model attribution would have to come from adapter-owned configuration because
the direct generation result did not independently return a server-selected
model identifier.

Evidence type: disposable local experiment.

## Lifecycle implications

The local experiment established a lifecycle distinct from server runtimes:

```text
Python process starts
  -> Python packages import
  -> tokenizer loads
  -> model weights load into process memory
  -> generation executes
  -> process exit releases runtime state
```

There is no separate daemon readiness state and no independent HTTP server
readiness state.

Health semantics therefore cannot be defined only in terms of successful HTTP
connectivity. Potential observable states include package importability, local
model availability, model load completion, and readiness of the in-memory model
object.

Selecting exact health semantics would be an architectural decision and is not
made here.

## Dependency implications

The disposable environment installed large Python runtime dependencies,
including PyTorch and Transformers. The runtime is coupled to:

* the Python interpreter ABI and supported Python versions;
* native wheels for the host platform;
* PyTorch execution backends;
* model and tokenizer implementations distributed through Python packages; and
* model files loaded into the orchestrator process memory.

This is a materially different dependency and isolation profile from invoking a
separate local runtime through HTTP.

No such dependency was added to Home AI Cluster by this experiment.

## Findings supported by direct observation

The local experiment established that the tested Transformers candidate can:

* execute model inference directly inside the Python process;
* operate without a server, daemon, port, or HTTP compatibility layer;
* load a small instruction model on CPU;
* preserve a `system` / `user` / `assistant` / `user` conversation history;
* return assistant content that can be normalized to a plain string;
* start from cached files in approximately one second in the observed normal run;
* start and generate successfully in strict offline mode;
* expose local artifact failures as direct Python exceptions; and
* accept an unknown message role instead of enforcing universal role validation.

The experiment also established that this candidate introduces a stronger
coupling to Python, native package wheels, and orchestrator process memory than
the investigated HTTP server runtimes.

## Remaining local unknowns

The following were not directly observed:

* peak and steady-state process memory usage;
* behavior under concurrent generation requests;
* cancellation behavior during generation;
* timeout semantics for in-process execution;
* out-of-memory exception behavior;
* malformed message content behavior beyond an unknown role;
* model unloading while the orchestrator process remains alive;
* startup behavior with partially corrupted cached files;
* behavior across additional model architectures and chat templates; and
* the smallest sufficient adapter implementation for this runtime shape.
