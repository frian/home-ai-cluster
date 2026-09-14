# Workspace Code Model Compatibility Investigation

Status: Investigation only

## Purpose and boundary

This record retains factual evidence from completed workspace-aware Code model
compatibility observations following PR #753. It does not select a model,
generation default, runtime configuration, or new configuration contract. It
does not authorize an RFC, implementation, test change, or further model
experiment.

RFC-0116 defines bounded workspace-aware Code interaction: ordinary
`capability=code` inference is composed with caller-local workspace authority
and a closed workspace/final JSON response grammar. RFC-0123 defines the
native interactive workspace Code surface, and RFC-0124 defines its loopback
browser workspace-enabled surface. In every case, filesystem authority remains
caller-local; models produce untrusted textual responses; and HAC strictly
parses the closed workspace/final grammar.

This is not a model guarantee. Parser recovery, Markdown-fence stripping,
retries, generic tools or function calling, and model-specific parser behavior
are outside the accepted boundary. Capability semantics also remain independent
of model and runtime. PR #753 changed only HAC-generated response-format
guidance within RFC-0116's accepted textual-control boundary.

## Concepts kept separate

The observations below use five distinct measures.

1. **Closed response-format compatibility** — whether a response is accepted
   by HAC's strict parser.
2. **Workspace-operation usefulness** — whether a model requests HAC-owned
   read/write operations and produces useful filesystem changes.
3. **Explicit action-sequence adherence** — whether it follows instructions
   such as read-before-write and read-back-after-write.
4. **Completion reliability** — whether the bounded interaction reaches a
   final response within the ordinary timeout.
5. **Filesystem result correctness** — whether the resulting file contains the
   intended change and executes correctly.

These measures can differ. A correct final file does not prove the requested
action sequence occurred. A missing read-back does not prove that a model
cannot use workspace Code. A timeout after a successful mutation does not roll
back the already committed filesystem effect. One failure under one sampling
configuration is not evidence of an architectural incompatibility.

## PR #753 response-format evidence

A shortened global workspace-Code contract was tested with `qwen2.5-coder:7b`.
A temporary out-of-repository diagnostic wrapper captured the raw first model
response before strict parsing. On the first inference of the first human turn,
with no prior conversation and therefore no history reminder, the model
returned valid workspace-request JSON inside Markdown JSON fences. HAC's strict
parser correctly rejected it.

That observed failure established that the shortened global contract was not
sufficiently salient in that run; retained multi-turn history was not involved.
PR #753 restored the stronger evidence-backed global response-format guidance
while preserving strict parsing. A fresh native interactive Qwen 2.5 Coder 7B
production smoke then completed both turns as:

```text
read -> write -> read -> final
```

The resulting file executed as:

```text
25
27
```

## Common synthetic workflow

All CLI comparisons used this initial file:

```python
def square(n):
    return n * n

if __name__ == '__main__':
    print(square(5))
```

Turn 1 requested a read of the current file; retention of `square(n)`;
addition of `cube(n)` returning `n * n * n`; complete-file replacement; a
read-back; and final code. Turn 2 requested another read; retention of
`square(n)`; changing `cube(n)` to `n ** 3`; complete-file replacement; a
read-back; and final code. The expected final execution was `25` then `27`.

The deliberately strict experiment result required each turn to complete the
requested `read -> write -> read -> final` sequence. It is therefore a
sequence-and-completion measure, not a general measure of whether a model can
use workspace Code.

## CLI comparison at ordinary settings

The first additional-model production validation ran at repository commit
`65b9f297078c731325034e05086d3fd284b0eb1a`, with the ordinary 120.0-second
request timeout and thinking enabled.

| Model | Turn 1 | Turn 2 | Final file execution | Strict result |
| --- | --- | --- | --- | --- |
| `mistral-nemo:12b` | `read -> final` | `read -> write -> final` | `25`, `27` | FAIL |
| `qwen3.5:9b` | `read -> write -> read -> ordinary request timeout` | `read -> write -> read -> final` | `25`, `27` | FAIL |

For Mistral NeMo, the requested write and read-back did not occur on Turn 1;
the requested read-back did not occur on Turn 2. This is evidence of incomplete
requested action-sequence adherence, not that Mistral cannot use workspace
Code: its final filesystem result was correct.

For Qwen 3.5, Turn 1 reached the requested read/write/read operations but did
not reach a final response before the ordinary timeout. The cause of that
timeout was not established and is not inferred here.

## Temperature=0 follow-up

The bounded follow-up changed only `temperature = 0`. Temporary Ollama aliases
were created from already-installed models using local model layers; no model
download occurred. HAC production code and configuration schema were unchanged.
Thinking remained enabled and the ordinary request timeout remained 120.0
seconds.

| Model | Turn 1 | Turn 2 | Final file execution | Strict result |
| --- | --- | --- | --- | --- |
| `mistral-nemo:12b`, temperature=0 | `read -> write -> final` | `read -> write -> final` | `25`, `27` | FAIL |
| `qwen3.5:9b`, temperature=0 | `read -> write -> read -> final` | `read -> write -> read -> final` | `25`, `27` | PASS |

For the observed Mistral runs, temperature=0 changed the initial action pattern
from `read -> final` to `read -> write -> final`, but both turns still omitted
the requested read-back. This is an observation about these runs, not a general
improvement claim.

For the observed Qwen 3.5 runs, changing temperature changed the strict result
from FAIL at ordinary settings to PASS while the timeout, thinking setting, HAC
contract, parser, workflow, and filesystem authority were held constant.
Generation settings can therefore materially affect practical workspace-Code
protocol compatibility in at least one observed model/environment. This does
not establish that temperature=0 is universally required, optimal, or
sufficient for Qwen 3.5 or any other model.

## Browser observations

Later manual loopback Web UI observations covered `qwen2.5-coder:7b` at its
existing configuration, `qwen3.5:9b` through a temporary temperature=0 alias,
and `mistral-nemo:12b` through a temporary temperature=0 alias. For each
model, two `/workspace-code` requests returned HTTP 200 and the resulting
`math_tool.py` executed successfully with final output:

```text
25
27
```

The operator observed incomplete requested read-back adherence in some browser
turns: activity could be `read -> write` rather than `read -> write -> read`.
The exact six per-turn sequences were not recorded model by model. Accordingly,
these observations establish correct final filesystem behavior through the
browser workspace surface for all three models in those manual runs; they do
not establish strict CLI-criterion passes, universal read/write/read adherence,
or full protocol compliance from HTTP 200 alone.

## What the evidence does not decide

This investigation does not establish a supported-model compatibility matrix,
model certification, deterministic repeatability across machines or runs, a
recommended default model, a recommended temperature, a generic
inference-parameter abstraction, or that Mistral NeMo is incompatible with
workspace Code. It does not establish that Qwen 3.5 universally requires
temperature=0, that browser HTTP 200 alone proves full protocol compliance, or
that correct filesystem output proves every requested action occurred.

It also does not decide whether HAC should expose temperature; whether such a
setting belongs to local runtime composition; whether it should be
runtime-specific or engine-independent; whether settings should be per
capability or per model; whether temperature=0 should be a default; or whether
a generic runtime-options surface should exist. Those are architectural
questions requiring separate review and RFC reasoning if pursued.

The smallest later question motivated by this evidence is:

> Is any HAC-owned inference-generation setting justified for reliable local
> capability execution, or should such settings remain entirely
> external/runtime-owned?

This investigation offers no configuration shape. In particular, it does not
propose a generic `options` dictionary, arbitrary Ollama parameters, a
capability-to-runtime-options map, an OpenAI-compatible parameter schema, or
per-request model controls.
