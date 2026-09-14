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

## Repeated Qwen 3.5 temperature A/B observation

This follow-up was predeclared before its results were seen. It repeated the
same local workspace-Code workflow for `qwen3.5:9b` with two temporary Ollama
aliases created from the same already-installed source model: Condition A,
`hac-exp-qwen35-control`, had no intentional generation overrides; Condition
B, `hac-exp-qwen35-temp0`, had only `PARAMETER temperature 0`. No model
download occurred. Thinking remained enabled, the ordinary request timeout
remained 120.0 seconds, and the HAC workspace contract, strict parser,
filesystem authority, production code, workflow, and prompts were unchanged.
Using aliases for both conditions avoided making base-model-versus-alias an
experimental difference.

The fixed order was A -> B, B -> A, A -> B, B -> A, A -> B. Every intended
run used a fresh disposable workspace with the common initial `math_tool.py`,
a new native interactive `hac code-workspace` invocation, the same two exact
human turns, and no retries, replacement runs, prompt correction, or manual
file repair. Strict PASS required both turns to complete `read -> write -> read
-> final` and the final file to execute as `25`, then `27`. The predeclared
repeatability separation was at least 4/5 strict PASS for one condition and at
most 1/5 for the other. This was not a statistical benchmark or general model
study.

| Run | Pair / condition | Turn 1 (elapsed) | Turn 2 (elapsed) | Final execution | Strict result |
| --- | --- | --- | --- | --- | --- |
| 1 | 1 / A | ordinary cluster unavailable (30s) | ordinary cluster unavailable (30s) | not performed | FAIL |
| 2 | 1 / B | read -> write -> read -> final (150s) | read -> write -> read -> final (270s) | `25`, `27` | PASS |
| 3 | 2 / B | read -> write -> read -> final (150s) | read -> write -> read -> final (270s) | `25`, `27` | PASS |
| 4 | 2 / A | read -> write -> timeout (210s) | timeout (150s) | `25`, `27` | FAIL |
| 5 | 3 / A | read -> timeout (150s) | read -> timeout (150s) | `25` | FAIL |
| 6 | 3 / B | read -> write -> read -> final (150s) | read -> write -> read -> final (270s) | `25`, `27` | PASS |
| 7 | 4 / A | read -> write -> read -> final (210s) | list refused -> final (90s) | `25`, `27` | FAIL |
| 8 | 4 / B | read -> write -> read -> final (150s) | read -> write -> read -> final (270s) | `25`, `27` | PASS |
| 9 | 5 / A | read -> write -> read -> read -> timeout (330s) | read -> write -> read -> final (210s) | `25`, `27` | FAIL |
| 10 | 5 / B | read -> write -> read -> final (150s) | read -> write -> read -> final (210s) | `25`, `27` | PASS |

Run 1 began while `hac local` was stopped. It remains a real recorded strict
FAIL under the predeclared no-retry rule, but it did not exercise the model and
is not valid evidence of `qwen3.5:9b` behavior at ordinary settings. It is
therefore explicitly excluded from causal or model-behavior interpretation.

The raw predeclared record is A: 0/5 strict PASS and B: 5/5 strict PASS. The
valid model-behavior comparison is instead ordinary settings: 0/4 strict PASS,
and temperature=0: 5/5 strict PASS. The four independent ordinary-setting
model runs all failed the strict criterion, although some produced the correct
final file. Condition A had five recorded strict FAIL outcomes, one caused by
`hac local` being unavailable; Condition B had five strict PASS outcomes, no
terminal timeouts, no incomplete requested-action sequences, no parser or
malformed failures, and the correct final file in every run. No parser or
malformed failures were observed in either condition.

Median observed human-turn elapsed time was A: 150s and B: 180s. This is a
secondary observation, not speed evidence: recorded B turns were often longer
while still completing correctly. No raw-response observer was used.

The repeated valid observations make a stochastic one-off explanation for the
earlier single A/B observation materially less credible in this local
environment. With the source model, thinking setting, 120-second ordinary
request timeout, HAC contract, parser, workflow, filesystem authority, and
production code held constant, they provide a strong bounded repeatability
signal that an inference-generation setting can materially affect reliable
workspace-Code protocol completion for one explicitly selected local
model/environment. They do not establish statistical significance, universal
determinism, universal requirement or optimality of temperature=0, improvement
for every model, or a temperature setting belonging to the Code capability.

The repeatability question is no longer merely hypothetical: a generation
setting currently external to retained HAC composition can materially affect
reliable execution in this observed workflow. That creates, but does not
answer, an architectural question about ownership and inspectability. A
separate RFC discussion may evaluate only this neutral question:

> Should an explicitly selected Ollama local runtime composition be able to
> retain one operator-controlled sampling temperature, or should that setting
> remain entirely external/runtime-owned?

This investigation neither authorizes nor designs such a change. It does not
propose capability-specific or per-request temperature, cluster transport
changes, generic inference options, arbitrary Ollama option passthrough,
other sampling/context settings, cross-runtime temperature semantics, or an
OpenAI-compatible parameter surface. The evidence is analogous in
architectural shape, not semantics, to earlier narrow runtime-specific
operator controls such as Ollama thinking control; those controls do not
authorize a temperature decision.

After the experiment, the retained HAC configuration was restored to
`qwen2.5-coder:7b`, thinking enabled, the `code` capability, no execution
limit, and no remote nodes. `hac local` was stopped again as originally found;
the temporary aliases, temporary Modelfiles, and temporary `/tmp` workspaces
were removed. The repository remained clean, and the experiment itself changed
no production code, tests, architecture, RFC, issue, or pull request.

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
