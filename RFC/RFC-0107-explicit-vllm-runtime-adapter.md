# RFC-0107: Explicit vLLM Runtime Adapter

Status: Accepted

Date: 2026-09-05

Author: frian

## Summary

Home AI Cluster should add vLLM as a third explicit ordinary local runtime,
beside `ollama` and `llama-server`. One concrete `VllmAdapter` should implement
the existing cluster-owned `RuntimeAdapter` protocol unchanged. It should own
vLLM-specific loopback HTTP transport, request and response translation,
served-model attribution, structured-output behavior, health, and failures.

The smallest supported topology is an ordinary HAC process communicating over
loopback HTTP with one operator-managed vLLM server. The operator launches and
configures vLLM and its model. HAC receives only a configured loopback base URL
and one non-empty served-model API identity.

This proposal adds no generic OpenAI-compatible runtime boundary, SDK, vLLM
library dependency, lifecycle management, model discovery, credentials,
arbitrary-network runtime transport, capacity observation, or scheduler
integration. Acceptance authorizes a later bounded implementation; it does not
by itself make vLLM a supported release behavior.

## Problem

The existing ordinary local-runtime and retained/runtime-configuration surfaces
deliberately define a closed supported-runtime set: `ollama` and
`llama-server`. The cluster-owned `RuntimeAdapter` protocol has already been
proven by RFC-0030 with two explicit concrete adapters, but vLLM is not an
ordinary operator-selectable runtime.

An operator who runs vLLM locally therefore cannot use it through the ordinary
HAC composition, retained local configuration, or explicitly selected runtime
composition file. Treating vLLM as merely another OpenAI-compatible server
would hide its distinct health, structured-output, model-identity, chat-template,
failure, and operator-lifecycle semantics behind a premature shared boundary.

Doing nothing preserves the current closed runtime set. Adding vLLM without an
RFC would silently extend an architectural product surface: supported ordinary
local runtime composition and retained runtime configuration.

## Goals

This RFC should:

* add `vllm` as one explicit ordinary local runtime identity;
* retain the existing `RuntimeAdapter` contract unchanged;
* keep all vLLM transport and wire behavior private to `VllmAdapter`;
* preserve the existing ordinary local capability names: `chat`, `summarize`,
  `classify`, and `code`;
* require truthful support for all four capabilities before `vllm` is enabled
  in ordinary local composition;
* define one operator-managed loopback HTTP runtime topology;
* define minimal process-local, retained, and runtime-config composition facts;
* preserve cluster-owned classification validation and failure semantics; and
* specify the focused automated and real-local evidence required before vLLM
  can be described as an ordinary supported runtime.

## Non-goals

This RFC does not add:

* a `GenericOpenAIAdapter`, `OpenAICompatibleAdapter`,
  `OpenAICompatibleRuntime`, `CompatibilityRuntimeFactory`, or equivalent
  compatibility abstraction;
* the OpenAI Python SDK, a vLLM Python dependency, PyTorch, or Transformers;
* vLLM installation, starting, stopping, restart, supervision, model download,
  model discovery, automatic model selection, or Hugging Face credential
  management;
* API-key or credential storage, arbitrary-LAN or Internet runtime endpoints,
  TLS, or a vLLM network-exposure design;
* GPU selection, GPU-memory, quantization, dtype, maximum-model-length,
  tensor/pipeline/data parallelism, Ray, scheduler, queue, or runtime
  concurrency configuration;
* runtime capacity, load, metrics, `/load`, queue-depth, active-sequence, or
  GPU observation, nor load-aware routing;
* Docker, Kubernetes, distributed vLLM serving, dynamic discovery, or a
  dashboard;
* multiple local runtime bindings or capability-specific runtime bindings;
* a change to `RuntimeAdapter`, current HAC capability semantics, routing,
  static topology declarations, remote protocol, or caller-local capability
  restrictions; or
* streaming, tools, multimodal input, reasoning controls, HAC sampling
  configuration, prompt-template configuration, code execution, or sandboxing.

## Proposal

### One third explicit adapter

Add one concrete adapter with stable internal identity `vllm`:

```text
HAC core
   |
   +-- OllamaAdapter
   |
   +-- LlamaServerAdapter
   |
   +-- VllmAdapter
```

`VllmAdapter` fits the existing `RuntimeAdapter` protocol without a new method:

```text
name
health
capabilities
chat
summarize
classify
```

Current textual, non-executing `code` behavior remains routed through the
existing normalized Chat execution seam. This RFC does not add a `code()`
runtime-adapter method.

The cluster continues to depend only on this protocol. `VllmAdapter` owns all
vLLM-specific HTTP paths, request forms, response parsing, model behavior,
structured-output details, health behavior, and error translation. Protocol
similarity must not become a HAC architectural boundary.

### Runtime ownership and transport

vLLM is an external, operator-managed local runtime process:

```text
ordinary HAC process
        |
        | loopback HTTP
        v
operator-managed vLLM server
```

HAC does not install, launch, stop, restart, supervise, configure, or otherwise
manage the server, its models, GPUs, parallelism, quantization, scheduling,
concurrency, or Hugging Face credentials. The operator launches a suitable
vLLM server with a suitable model and chat template.

Only an explicitly configured absolute loopback `http` base URL is authorized,
using the existing local-runtime transport boundary. HAC does not authorize
arbitrary LAN or Internet runtime endpoints. Remote HAC callers continue to
communicate with an HAC receiver; they do not communicate directly with that
receiver's vLLM process.

This RFC does not define vLLM network exposure. It adds no API-key support,
TLS, or authentication architecture. Even where vLLM is configured with an API
key, its server surface can include inference-capable and control endpoints that
are not all authenticated. An API key alone would therefore not establish a
safe arbitrary-network HAC runtime boundary. Non-loopback transport and its
authentication model require a separate architectural decision.

### Capability behavior

The ordinary local capability set remains exactly:

```text
chat
summarize
classify
code
```

Before `vllm` becomes enabled as an ordinary local runtime, its adapter must
truthfully implement all four. This RFC neither changes their semantics nor
creates per-runtime default capability subsets. Caller-local capability
restrictions remain routing eligibility; they do not redefine an adapter's
supported capability set.

#### Chat and Summarize

For Chat, the adapter may privately use vLLM's non-streaming Chat Completions
endpoint:

```text
POST /v1/chat/completions
```

It maps existing normalized HAC message history to normal string-content chat
messages. It does not add new HAC message semantics. The served model must have
a working chat template, or the operator must configure vLLM appropriately
outside HAC; HAC neither owns nor discovers templates.

Summarize follows the existing adapter pattern:

```text
normalized HAC SummarizeRequest
        |
        v
adapter-private summarization prompt
        |
        v
vLLM chat generation
```

There is no vLLM-specific summarize protocol and no movement of summarization
prompt semantics into routing.

#### Code

Code remains textual and non-executing behavior over normalized adapter Chat.
vLLM needs no special Code API and receives no execution, tool, sandbox, or
code-running authority.

#### Classify and structured output

The accepted classification boundary remains authoritative:

```text
adapter proposes one label
        |
        v
cluster validates exact membership in the caller-supplied bounded label set
```

`VllmAdapter` may use an adapter-private vLLM structured-output mechanism,
including the current `structured_outputs.choice` request form, to constrain
generation to exactly one caller-provided label. The vLLM payload need not and
must not be standardized to match llama-server's structured-output payload.

```text
HAC classification contract
        !=
runtime structured-output request shape
```

The adapter returns one proposed string through the existing `classify()`
contract. HAC retains exact-label validation; runtime structured-output does not
become a HAC protocol.

### Health, failures, and attribution

`VllmAdapter.health()` may use the descriptive local health endpoint:

```text
GET /health
```

Health remains descriptive adapter availability only. It authorizes no
health-based routing, polling, heartbeat, scheduler state, metrics, `/load`,
queue observation, active-sequence observation, or GPU-load observation.

Existing cluster-owned error meanings remain sufficient:

* a connection failure before request transmission maps to the existing
  pre-transmission runtime connection-unavailable semantic;
* an HTTP failure after connection/request transmission maps to the existing
  generic runtime-adapter-unavailable semantic; and
* a malformed or unusable response maps to the existing generic
  runtime-adapter-unavailable semantic.

No vLLM-specific cluster error type is authorized unless later implementation
evidence establishes a concrete truthful mismatch.

One non-empty configured served-model API identity is required. HAC sends it
in requests and uses the returned vLLM model value for normal
`RuntimeResult.model` attribution. HAC does not call `/v1/models`, inspect an
underlying Hugging Face model path, discover models, or choose models
automatically. Where the operator supplies vLLM's `--served-model-name`, HAC
uses that API identity; otherwise the effective identity is what the operator's
vLLM server exposes.

### Closed local configuration

The authorized vLLM local composition facts are exactly:

```text
runtime = vllm
vLLM loopback base URL
vLLM served-model identity
```

Later implementation may use clear operator spelling such as:

```text
--runtime vllm
--vllm-base-url <LOOPBACK_URL>
--vllm-model <SERVED_MODEL_ID>
```

The exact implementation spelling follows repository conventions. No other
vLLM-specific local value is authorized, including API key, GPU selection,
memory utilization, parallelism, quantization, dtype, model length, scheduler
parameters, maximum sequences, concurrency, queue settings, Hugging Face token,
download directory, or runtime launch command.

RFC-0094's retained `hac config local` domain may represent precisely the same
three facts. `hac config node` remains limited to node identity, base URL, and
capabilities. Remote retained declarations must not reveal remote runtime,
model, vLLM settings, concurrency, or GPU facts. If retained local runtime
facts are displayed by `hac config show`, it may factually display `vllm`, the
configured loopback base URL, and configured served-model identity. It must not
observe or display health, loaded state, current work, queue depth, concurrency,
or GPU information.

RFC-0074's explicit `--runtime-config` remains a closed composition source. It
may represent vLLM with the equivalent two runtime-specific facts, for example:

```toml
runtime = "vllm"

[vllm]
base_url = "http://127.0.0.1:8000"
model = "operator-chosen-served-name"
```

The schema remains closed; this RFC does not authorize a generic
provider/options map.

### Dependencies and execution-availability compatibility

Implementation should use existing `httpx` only. This RFC authorizes no new
Python dependency merely to communicate with an operator-managed HTTP runtime.

This RFC is architecturally independent of Accepted RFC-0098 through RFC-0106.
That accepted execution-availability rail's HAC execution limit remains
runtime-independent:

```text
HAC execution limit
        !=
vLLM runtime concurrency
```

The HAC limit concerns overlapping HAC-owned execution intervals only. HAC must
not query or infer vLLM capacity or load to set the limit or route requests.

## Rationale

vLLM is a useful explicit local runtime only when it fits the project without
turning HAC into an inference engine or runtime manager. One concrete adapter
preserves engine independence because core code continues to speak in
cluster-owned capabilities, requests, results, health, and failures. A
loopback external-process boundary preserves local-first operation and keeps
large inference dependencies, model memory, server lifecycle, and GPU concerns
outside HAC.

RFC-0030 established that OpenAI-compatible endpoint resemblance is not a
shared HAC runtime contract. vLLM and llama-server differ in health behavior,
structured-output request form, served-model identity, chat-template
requirements, failures, and operator lifecycle/options. Small duplicated HTTP
translation is clearer and safer than a generic layer that pretends those
semantics are identical.

The configuration is intentionally minimal and closed. It gives an operator a
stable local binding while preserving the accepted separation between
process-local runtime composition, caller-owned topology, cluster-facing
capabilities, and live runtime observation.

## Alternatives considered

### Generic OpenAI-compatible adapter

Rejected. Endpoint similarity is not an architectural runtime contract, and
RFC-0030 already establishes separate concrete adapters. A generic adapter
would conceal meaningful runtime differences and create a premature boundary.

### Reuse `LlamaServerAdapter` for vLLM

Rejected. Reuse would falsely claim identical health, structured-output,
model-attribution, and future-evolution semantics.

### Use the OpenAI Python SDK

Rejected. Existing `httpx` is sufficient; an SDK adds an unnecessary dependency
and conceptual coupling.

### Import vLLM as a Python library

Rejected. HAC integrates an operator-owned external runtime; it does not become
an in-process inference engine.

### Discover models through `/v1/models`

Rejected. The operator explicitly supplies one served-model identity, which is
smaller and does not create a discovery or automatic-selection surface.

### Expose vLLM directly to remote HAC callers

Rejected. Remote callers use the HAC receiver protocol. The receiver owns its
local runtime boundary.

### Add API-key support immediately

Rejected for this first scope. Loopback-only transport avoids a new credential
architecture, and a vLLM API key alone does not authenticate the entire server
surface.

## Trade-offs

This proposal adds a third explicit adapter, two runtime-specific composition
values, focused test work, and real-local proof work. It deliberately duplicates
some HTTP translation already present in `LlamaServerAdapter`.

That cost is acceptable because the adapter remains small, the runtime boundary
is visible, operator control stays explicit, and the core avoids false
abstraction, inference dependencies, lifecycle ownership, capacity claims, and
generic configuration machinery. The proposal also requires a suitable served
model and externally configured chat template, rather than trying to hide those
operator responsibilities in HAC.

## Impact

Acceptance authorizes a separate implementation PR to add `VllmAdapter`,
explicit `vllm` ordinary local composition, the two minimal CLI/runtime-config
facts, the matching retained-local representation and factual `config show`
display, focused tests, real-local evidence, and then appropriate operator
documentation. It must preserve the existing request, result, routing,
topology, capability, and protocol boundaries.

This RFC authorizes implementation only. vLLM becomes ordinary supported
release behavior only after implementation, focused tests, full regression
validation, truthful all-four-capability proof, real operator-managed vLLM
evidence, documentation, and later integration and release decisions.

## Proof expectations

A later implementation must establish the following in order.

### Stage 1 — adapter transport proof

Focused mocked adapter tests must prove construction, identity, loopback
validation, health success/failure, Chat request/response normalization, model
attribution, pre-transmission connection-unavailable mapping, and generic
HTTP/malformed-response unavailable mapping.

### Stage 2 — existing capability completeness

Before ordinary runtime composition is enabled, tests must prove Summarize,
Classify, and Code. Classification evidence must show that vLLM's constrained
output is private to the adapter and HAC's existing exact-label validation is
still authoritative.

### Stage 3 — ordinary local runtime integration

Focused integration proof must cover `hac local --runtime vllm ...`, retained
`hac config local`, `hac config show`, retained-baseline startup,
`--runtime-config`, ordinary static-cluster receiver use, and the truthful
existing four-capability set.

### Stage 4 — real local proof

One operator-managed loopback vLLM process with one small text-generation
instruct model and a working chat template must demonstrate ordinary HAC Chat,
Summarize, Classify, and Code. Successful results must attribute:

```text
adapter = "vllm"
model = "<configured/returned served model identity>"
```

The proof must also demonstrate unavailable-runtime behavior. It does not
require performance or concurrency benchmarks, capacity discovery, or
distributed vLLM.

## Open questions

None within this proposed architectural scope. Exact implementation names and
the final CLI spelling remain implementation details constrained by the closed
facts above.

## Decision

Accepted. Home AI Cluster will add vLLM as one explicit third ordinary local
runtime through a concrete `VllmAdapter` implementing the existing
`RuntimeAdapter` contract unchanged. vLLM-specific HTTP transport, structured
output, health, failure translation, and served-model attribution remain
adapter-private. The first supported runtime topology is operator-managed and
loopback-only with exactly a configured base URL and served-model identity.
Acceptance authorizes the bounded implementation and proof stages defined here,
without a generic OpenAI-compatible abstraction, runtime lifecycle ownership,
model discovery, credentials, arbitrary-network transport, runtime-capacity
claims, scheduler behavior, or distributed state.
