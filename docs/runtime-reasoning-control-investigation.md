# Runtime Reasoning Control Investigation

Status: Investigation only

## Question

How, if at all, should Home AI Cluster expose an operator choice about selected
runtime/model reasoning without placing a model- or engine-specific control in
cluster requests, capability semantics, or routing?

## Why this investigation exists

The ordinary Ollama adapter sends a process-local selected model, ordered
messages, and `stream=false`; it sends no thinking control and normalizes only
final textual content. Reasoning trace content is not a cluster result.

Privacy-safe real-local evidence established a material difference for one
already-installed, explicitly selected thinking-capable local model. A bounded
Aider interaction through HAC/Ollama exceeded a 300-second wait and a later
equivalent correction exceeded a 600-second wait; the latter was an HTTPX read
timeout. A direct diagnostic with thinking explicitly disabled completed in
about 91 seconds after 927 prompt-evaluation and 221 generated tokens.

This establishes a difference in one local environment, not that reasoning
alone caused either timeout or should be universally disabled. No model identity,
prompt, source, target, host detail, raw HTTP, transcript, or trace is retained.

## Accepted architectural boundary

Cluster requests remain model-independent and capability-centered. Routing
selects capabilities, not model identity or reasoning mode. RFC-0071 keeps
concrete Ollama model selection process-local and adapter-owned. RFC-0067 does
not permit `code`, or another capability, to imply a model/runtime policy.
RFC-0068/RFC-0072 keep Aider from selecting a model, runtime, node, or route.
Static declarations describe topology/capabilities, not runtime internals. No
generic runtime-options dictionary, reasoning trace in `ClusterResult`, trace
persistence, or runtime lifecycle authority is accepted.

## Current HAC behavior

### Ollama adapter

`OllamaAdapter` sends a configured model, ordered messages, and non-streaming
mode to native Ollama chat. It reads final `message.content`, does not map a
`thinking` field, and has no process-local reasoning setting.

### llama-server adapter

`LlamaServerAdapter` uses its existing Chat-like boundary and returns ordinary
text. It has no HAC reasoning control and does not make llama-server format or
budget settings cluster semantics.

### Aider caller edge

The caller edge translates up to two strict private interactions to ordinary
native `capability=code` requests. It must not select a model/runtime/node/route
or inspect response semantics; a reasoning policy cannot be added there without
changing accepted ownership.

### Timeout boundary

RFC-0060's timeout is a finite native-client wait. It is not cancellation, does
not prove runtime work stopped, and grants HAC no runner/service lifecycle
authority. The continued-runner observation is separate from reasoning control.

## Upstream runtime behavior

### Ollama

Official [Ollama chat API documentation](https://docs.ollama.com/api/chat)
defines `think` for thinking models as a request field accepting either a
boolean or levels including `low`, `medium`, `high`, and `max`. Its assistant
message has separate `thinking` and `content` fields. The documentation does
not state one uniform default for all thinking-capable models; this is explicitly
model-dependent. An Ollama policy therefore cannot safely be assumed to be a
universal boolean semantic.

### llama.cpp / llama-server

Official [llama-server documentation](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md)
exposes distinct startup controls: `--reasoning on|off|auto`,
`--reasoning-effort`, `--reasoning-format`, and `--reasoning-budget`. The budget
is `-1` unrestricted, `0` immediate end, or a positive token limit. Template
kwargs are separate. Its server schema also accepts request-level format and
budget fields, and its format can leave thought tags in content or extract them
to `message.reasoning_content`.

Both runtimes may influence or represent reasoning, but that is not evidence of
one shared semantic: their controls differ in meaning, granularity, defaults,
and template/model dependence.

## Ownership analysis

| Possible owner | Assessment |
| --- | --- |
| Cluster request | Reject now: it expands schemas, transport, browser, compatibility, and caller-visible runtime detail. |
| Capability or routing | Reject: capability is an operation requirement, not a thinking-quality policy. |
| Aider caller edge | Reject: it would give caller-edge mechanics runtime-policy authority. |
| Process-local runtime composition | Credible narrow location for an explicit runtime-specific operator choice, analogous in ownership—not semantics—to RFC-0071. |
| Concrete adapter | Translates an accepted process-local setting; a hidden permanent policy is observable behavior, not a private refactor. |
| Externally managed runtime | Retains installation, service lifecycle, and server-startup control; HAC must not start, stop, or cancel it. |

## Options

| Option | Assessment |
| --- | --- |
| A. No HAC change | Safe present default; no RFC or implementation. |
| B. Hidden adapter policy | Reject. Hard-coding disabled reasoning changes selected-model behavior without operator choice; it is architectural, not a correction. |
| C. Runtime-specific process-local configuration | Credible smallest next decision for Ollama only. It can remain node/process-local and adapter-translated while requests, routes, Aider, browser, compatibility, and declarations stay unchanged. It requires an RFC because it adds a configuration/operator contract and must handle boolean-or-levelled semantics. It adds no lifecycle, persistence, remote declaration, or generic-option authority. |
| D. Engine-independent process-local setting | Not justified. Present Ollama and llama-server evidence does not establish a real shared concept. |
| E. Cluster request-level control | Reject here: it changes schemas, transport, browser, compatibility, Aider, and privacy review; it would require a broad RFC. |
| F. Capability-specific policy | Reject. `code => no reasoning` would infer runtime/model behavior from capability. |
| G. Aider-specific prompting/control | Reject. It changes RFC-0068/RFC-0072 ownership and creates caller-specific runtime policy. |
| H. Generic runtime option pass-through | Reject. It creates an open configuration surface and hides runtime contracts behind a dictionary. |
| I. Reasoning-budget configuration | Not justified. llama-server budgets and Ollama levels are not equivalent; it needs direct evidence and a separate RFC. |

## Timeout and cancellation boundary

RFC-0060 need not change. The evidence confirms its warning that a client timeout
does not establish cancellation. A future reasoning control would influence an
ordinary request before the existing wait; it would not cancel work after timeout.
The post-timeout runner behavior is a separate lifecycle/cancellation
investigation. Solving reasoning control leaves the no-cancellation contract
unchanged.

## Smallest justified next step

**Outcome C — an architectural decision is justified and requires a new RFC.**

The smallest credible RFC question is whether one explicitly selected Ollama
composition may accept one narrow process-local operator-controlled
thinking/reasoning value, and how it validates/translates Ollama's current
model-dependent boolean-or-levelled contract. It should decide value domain and
omission/default semantics without choosing CLI spelling prematurely.

It must not change cluster request schemas, capability meanings, routing,
remote declarations/transport, Aider ownership, browser/compatibility surfaces,
llama-server behavior, model selection, result shapes, trace handling,
logging/persistence, target authority, timeout/cancellation semantics, or
external runtime lifecycle ownership. It must not add a generic options map,
capability-derived policy, token budget, or cross-runtime abstraction.

## Conclusion

The observation justifies deciding whether an Ollama-specific process-local
control belongs in HAC, not silently imposing a policy. Current upstream
evidence does not support a shared engine-independent setting. A narrow RFC is
the next step; this investigation authorizes no implementation.
