# Qwen 3.5 Workspace Code Composition Study

Status: Investigation only

## Purpose and boundary

This record retains finite observations from one synthetic workspace-Code
workflow. It is not a benchmark claim, model or runtime recommendation,
configuration recommendation, supported-model matrix, certification, product
contract, RFC, or architectural decision.

Capability semantics remain independent of model and runtime. Filesystem
authority remained HAC-owned and caller-local; model output remained untrusted
textual input to HAC's strict workspace/final grammar. These experiments add no
architecture, runtime default, configuration contract, or supported-model
matrix. Correct filesystem output and strict protocol compliance are separate
measures.

RFC-0116 defines the bounded workspace-aware Code composition. RFC-0123 and
RFC-0124 define its interactive CLI and loopback-browser surfaces. They retain
caller-local workspace authority and strict parsing; this evidence does not
weaken either boundary. RFC-0073 remains the accepted, bounded Ollama-specific
process-local thinking-disable decision. Draft RFC-0125 is a separate,
unresolved proposal and is neither changed nor pre-accepted here.

## Common workflow and scoring

Each fresh workspace began with `math_tool.py` containing:

```text
def square(n):
    return n * n


if __name__ == '__main__':
    print(square(5))
```

Turn 1 requested: read the current file; keep `square(n)`; add `cube(n)`
returning `n * n * n`; replace the complete file; read it back; and return a
final answer. Turn 2 requested: read the current file; keep `square(n)`;
change `cube(n)` to return `n ** 3`; replace the complete file; read it back;
and return a final answer.

Strict turn PASS means exactly:

```text
read(success) -> write(success) -> read(success) -> final
```

Strict run PASS requires both turns to pass. Functional PASS requires the final
Python file to execute successfully and print exactly:

```text
25
27
```

Functional correctness does not imply strict protocol compliance.

## Repository and lab boundary

The cloud campaigns used HAC commit
`86d4c6cac6269274e920b691af2279ff294e4b2a`. That experimental revision is
not the newer documentation branch base. The cloud lab was disposable external
infrastructure used only for these experiments; it is not a HAC dependency or
supported topology. Its relevant hardware was an NVIDIA RTX 6000 Ada Generation
48 GB-class GPU. The observations do not establish that this hardware caused
any behavioral improvement.

## Experiment 1 — Ollama Qwen 3.5 model ladder

Evidence identifier: `qwen35-model-ladder-20260915T123946Z`.

This predeclared 15-run campaign used Ollama 0.34.0 and the experimental HAC
commit above. Every model had five scored runs in a fixed order interleaved
before results, with a fresh workspace, no retries, and the same prompts and
read/write grants. The observed native Qwen 3.5 settings were temperature 1,
top_k 20, top_p 0.95, presence_penalty 1.5, thinking enabled, and native model
context 262144.

| Model | Valid | Strict | Functional | Interaction times (s) | Median (s) |
| --- | ---: | ---: | ---: | --- | ---: |
| Qwen3.5 9B | 5/5 | 1/5 | 3/5 | 336.751, 139.400, 116.586, 35.192, 103.694 | ~116.586 |
| Qwen3.5 27B dense | 5/5 | 5/5 | 5/5 | 68.086, 56.718, 64.589, 59.204, 66.903 | 64.589 |
| Qwen3.5 35B-A3B | 5/5 | 2/5 | 5/5 | 270.580, 159.768, 34.742, 156.749, 196.789 | 159.768 |

Observed 9B failures included timeouts, malformed responses, and sequence
deviation. The 27B campaign had no scored strict failures. The 35B-A3B strict
failures were action-sequence deviations while final filesystem behavior
remained correct.

The predeclared strong-separation condition was a larger model at least 4/5
strict while 9B was at most 1/5 strict. It was met for 9B versus 27B, and was
not met for 9B versus 35B-A3B. This is not statistical significance, a
monotonic parameter-count result, a claim that 27B is universally better, or a
general dense-versus-MoE rule. The expensive GPU did not itself eliminate the
9B protocol failures; the evidence therefore does not support the simple claim
that earlier model/protocol failures were merely caused by weak local hardware.

## Experiment 2 — Ollama Qwen3.5-27B thinking ON/OFF

Evidence identifier: `qwen35-27b-thinking-ab-20260915T140613Z`.

This predeclared, interleaved campaign had five ON and five OFF runs. Only the
thinking condition intentionally changed. OFF used RFC-0073's accepted
Ollama-specific mechanism, which maps to native `think: false`; model, runtime,
GPU, workflow, grants, fresh-workspace policy, HAC revision, and ordinary HAC
execution limits otherwise remained the same.

| Condition | Valid | Strict | Functional | Interaction times (s) | Median (s) |
| --- | ---: | ---: | ---: | --- | ---: |
| Thinking ON | 5/5 | 5/5 | 5/5 | 72.191, 60.240, 68.915, 71.159, 66.899 | 68.915 |
| Thinking OFF | 5/5 | 5/5 | 5/5 | 25.826, 30.359, 27.044, 27.100, 28.193 | 27.100 |

The predeclared practical criterion—OFF at least 4/5 strict, 5/5 functional,
and median at most 70% of ON—was met. In this exact composition and workflow,
the OFF median was about 39.3% of ON: about 60.7% lower median latency, or
about 2.54x lower median elapsed time. This does not establish that thinking is
generally harmful, unnecessary, or a default to disable.

## Experiments 3 and 4 — vLLM Qwen3.5-27B-FP8

Both campaigns used the `Qwen/Qwen3.5-27B-FP8` artifact, vLLM 0.29.0, maximum
model length 32768, `max_num_seqs=8`, the `qwen3` reasoning parser,
language-model-only mode, the same HAC revision and workflow, fresh workspaces,
and no retries. vLLM emitted a runtime warning on this RTX 6000 Ada that FP8
computation was not native for this path and that weight-only FP8 compression
using the Marlin kernel was used, with possible compute-heavy performance
impact. Performance interpretation must include that limitation.

| Campaign / thinking | Valid | Strict | Functional | Interaction times (s) | Median / mean (s) | Threshold |
| --- | ---: | ---: | ---: | --- | --- | --- |
| `qwen35-27b-vllm-nothink-20260915T173412Z` / OFF | 5/5 | 5/5 | 5/5 | 18.681, 18.782, 17.569, 19.498, 18.115 | 18.681 / 18.529 | MET |
| `qwen35-27b-vllm-thinking-20260915T180917Z` / ON | 5/5 | 5/5 | 5/5 | 45.432, 46.749, 45.416, 44.172, 43.926 | 45.416 / 45.139 | MET |

For OFF, thinking was disabled server-wide with `enable_thinking=false`. Its
predeclared threshold was all five valid, at least 4/5 strict, and 5/5
functional. The ON campaign retained the Qwen/vLLM default and used the same
threshold.

The ON and OFF campaigns were successive, not interleaved. They are therefore
not a randomized, interleaved, or statistical A/B experiment. The artifact,
vLLM version, GPU, context limit, `max_num_seqs`, HAC revision, prompts,
grants, workspace policy, and scoring criterion were held the same; thinking
enabled versus disabled was the principal intentional difference. Both were
5/5 strict and 5/5 functional. In this composition and task, OFF's 18.681 s
median was about 58.9% lower than ON's 45.416 s, or about 2.43x lower elapsed
time. This does not generalize beyond the composition and task.

## Relationship to earlier temperature evidence

[The Workspace Code model compatibility investigation](workspace-code-model-compatibility-investigation.md)
retains the local repeated Ollama Qwen3.5:9b observation: valid ordinary
settings were 0/4 strict, while `temperature=0` was 5/5 strict. Model source,
thinking setting, HAC contract/parser/workflow/filesystem authority, and
production code were held constant.

A later separate llama-server experimental follow-up, retained by the operator
outside the repository before this study, prevents treating that favorable
Ollama direction as engine-independent semantics. Because the tested
llama-server build could not load the exact Ollama GGUF, it used a compatible
but different Qwen3.5-9B GGUF artifact and was not a byte-identical
cross-runtime comparison. Native/default was 3/5 strict; `temperature=0` was
0/5 strict; a later explicit `temperature=1` condition was 2/5 strict; and
explicit `temperature=0` was 0/5 strict. Temperature changed behavior, but
`temperature=0` was not a portable reliability recipe. The evidence supports
only that generation settings can materially affect protocol behavior and that
numeric temperature values have no demonstrated portable reliability meaning
across engine/model-artifact compositions.

## Restrained synthesis

These finite observations support the following bounded interpretation:

1. Functional correctness and strict workspace-protocol adherence differ:
   35B-A3B was 5/5 functional but 2/5 strict.
2. Parameter count did not monotonically predict strict reliability in the
   tested Ollama ladder: 27B was 5/5 strict and 35B-A3B was 2/5.
3. Strong hardware alone was insufficient to eliminate model/protocol failures:
   9B was 1/5 strict on the RTX 6000 Ada campaign.
4. For Qwen3.5-27B in this exact workflow, disabling thinking preserved all
   observed strict and functional passes while substantially reducing latency
   in both tested Ollama and vLLM compositions.
5. That repeated thinking signal is useful engineering evidence, not
   authorization for a generic engine-independent thinking control or default.
6. Temperature materially affected one local Ollama Qwen3.5-9B composition,
   but the favorable `temperature=0` direction did not reproduce in the
   separate llama-server composition.
7. Practical compatibility is appropriately discussed at the composition
   level: model artifact + runtime + generation settings + operational limits
   + hardware. This is experimental interpretation, not a HAC protocol or core
   abstraction.
8. The strict fail-closed parser and caller-local workspace authority remain
   justified. Correct final output after a protocol deviation is not evidence
   to weaken parsing, authority, or action-sequence expectations.
9. The completed vLLM campaigns provide real workspace-Code evidence for this
   specific composition: 10/10 strict and 10/10 functional combined. They do
   not certify vLLM generally.

## Cross-runtime comparison boundary

The Ollama and vLLM entries above are different compositions: their 27B
artifacts/quantizations, context configuration, runtime implementation, and
native generation behavior differ. Their table placement is only orientation,
not a controlled runtime benchmark. No Ollama-versus-vLLM speedup or
runtime-only causal comparison follows from these numbers.

## Explicit non-conclusions

This evidence does not establish that cloud hardware causes fewer model errors;
that Qwen3.5-27B is universally best; that larger models are always better;
that dense models are generally more protocol-reliable than MoE models; that
vLLM is intrinsically faster than Ollama; or that the Ollama and vLLM latency
figures are a runtime-only comparison.

It also does not establish that thinking should generally be disabled;
that `temperature=0` is deterministic, optimal, a reliability mode, or has
portable engine semantics; a supported-model matrix or certification; a new
capability contract; generic inference options or reliability mode; a routing
rule; a workspace-authority or strict-parsing change; or any architecture or
implementation authorization.

## Architectural consequence

No new architectural decision is required now. The evidence reinforces
composition-aware empirical validation, engine-independent cluster-facing
semantics, and runtime-specific details staying at runtime/composition
boundaries. It supports no generic reliability-mode abstraction and no
weakening of fail-closed parsing or workspace authority. If a future shared
thinking or generation-control concept is proposed, it requires an RFC before
architecture. RFC-0073 remains the accepted bounded Ollama-specific decision;
Draft RFC-0125 remains a separate unresolved proposal.
