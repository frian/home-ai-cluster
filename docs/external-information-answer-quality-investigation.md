# External Information Answer Quality Investigation

Status: Investigation only

Date: 2026-10-13

## Question and scope

Does the current bounded External Information path produce sufficiently reliable,
source-supported technical answers, and how do Tavily Search depth and model
choice affect the observed result?

This is a finite operator-run investigation, not a release-quality benchmark,
a supported-model recommendation, an architectural decision, or authorization
to change code, prompts, search configuration, routing, or accepted RFCs.
The question was evaluated using public Python 3.14 free-threading material
and fictional node-selection evidence. No private source material was needed.

## Relevant accepted boundaries

- [RFC-0077](../RFC/RFC-0077-bounded-source-grounded-chat.md) governs bounded,
  supplied-source Chat and preserves supplied-source provenance separately from
  model-generated claims; it does not verify individual claims or citations.
- [RFC-0078](../RFC/RFC-0078-optional-external-information-acquisition-plugin-boundary.md)
  places explicitly selected acquisition at the caller edge, before ordinary
  `chat` routing.
- [RFC-0093](../RFC/RFC-0093-bounded-tavily-acquisition-plugin.md) governs the
  fixed Tavily plugin request shape.
- [RFC-0154](../RFC/RFC-0154-bounded-external-information-source-expansion.md)
  accepted a 2,048-UTF-8-byte per-source content limit and two Tavily Search
  chunks per source; this changes evidence capacity, not answer correctness.
- The earlier [Source-Grounded Chat proof](source-grounded-chat-proof.md)
  already distinguishes supplied-source provenance from claim-level truth.
  This investigation extends that distinction with observed model failures.

## Method and limitations

The operator first checked that the existing local source-grounded route
passed a unique, synthetic calibration value through to a `qwen3.5:9b`
response. A second fictional test, FALCON-62, distributed an explicit
selection rule, two node capabilities, privacy constraints, latencies, and
validation tokens across five separate source records. One unrelated requested
hardware detail was intentionally absent. No Tavily call was involved in
those tests.

For the public technical question about free-threading in Python 3.14
versus 3.13, two Tavily Search acquisitions were compared with the same
targeted query, `max_results=5`, `chunks_per_source=2`, raw content disabled,
and other existing fixed plugin request flags preserved. The only deliberately
changed provider option was `search_depth` (`basic` versus `advanced`).
Candidate results were checked against current HAC evidence validation.
The selected five-source sets were then frozen for downstream generation:
each model received the same Basic set and the same Advanced set, through
`POST /v1/chat/sources`, with the same technical question and additional
instructions to avoid unsupported claims and identify missing evidence.
No fresh provider calls occurred during those four generations.

The 9B ran on the operator's local system. The
`qwen3.5:27b-q4_K_M` model ran via Ollama and the ordinary HAC loopback
application inside a temporary, operator-controlled RunPod GPU instance.
Only public or synthetic information was used; RunPod was an explicit
one-off experiment, not a new HAC deployment path or dependency.

These are individual observations (one generation per model and source set,
two 9B FALCON-62 variants, one 27B FALCON-62 run), not repeated
sampling with controlled seeds. Runtime, quantization, and hardware differed.
There was no independent claim-verification system. Provider result selection
can vary between calls, so source sets are not a controlled ranking comparison.
The reported durations are end-to-end wall-clock times, not isolated model
decode throughput. No raw prompts, source URLs, full source texts, API keys,
provider responses, or generated answers are retained in this document.

## Evidence acquisition results

| Observation | Basic | Advanced |
| --- | ---: | ---: |
| Returned sources | 5 | 5 |
| Total source-content UTF-8 bytes | 4,273 | 5,910 |
| Acquisition wall time | 0.56 s | 3.07 s |
| Full HAC request validation | Passed | Passed |
| Official Python documentation among selected results | No | Yes |

The acquisitions shared only two source URLs. Advanced returned about 38%
more source-content bytes and, in this sample, included an official passage
confirming that Python 3.14 re-enabled the specializing adaptive interpreter
(PEP 659) for free-threaded builds and reduced approximate single-thread
overhead to 5-10%. Basic instead included a historical statement that
re-enablement was *expected* in Python 3.14, not evidence that it had occurred.
Basic also contained the earlier approximate 40% Python 3.13 overhead figure,
which the sampled Advanced result set omitted.

More retrieved text did not ensure coverage of every relevant fact. Advanced
contained redundant secondary reporting, an unrelated release-details passage,
and a social-media result. Neither five-source set constituted a complete
technical reference.

## Model observations

### Synthetic five-source reasoning

The expected FALCON-62 selection was the local-capable node Delta-47, with
145 ms p95 latency and validation token `PHOENIX-604`. No source identified
its GPU; GPU identity was an additional requested fact, **not** an eligibility
requirement. Boreal-19 failed the local-only requirement.

The 9B recovered the relevant facts in two attempts, including one with a
stricter source-only instruction, but both final answers incorrectly claimed
that no node could be selected because GPU identity was unavailable.
One attempt also attributed the validation token to the wrong source title.
The 27B selected Delta-47, cited the validation-token source correctly,
and explicitly left the GPU unknown. This is one observed improvement in
reasoning and provenance attribution, not a general pass rate.

### Fixed-source technical answers

| Model and environment | Basic wall time | Advanced wall time |
| --- | ---: | ---: |
| `qwen3.5:9b`, operator-local Ollama | 507.20 s | 509.99 s |
| `qwen3.5:27b-q4_K_M`, temporary RunPod Ollama | 95.41 s | 108.39 s |

With Basic sources, the 9B incorrectly asserted that PEP 659 remained
disabled in Python 3.14, treating a dated expectation as present fact.
The 27B more appropriately identified that those sources did not establish
whether re-enablement occurred, but its own conclusion still described
re-enablement as a future optimization. It also labeled figures from a
source table headed "bubble 1 thread" as a multithreaded bubble-sort
comparison.

With Advanced sources, both models correctly reported PEP 659 re-enablement
and the approximate 5-10% single-thread overhead, facts actually present in
the official-documentation excerpt. The 9B nonetheless generalized a
CodSpeed performance observation beyond its stated scope and did not cleanly
separate free-threading (PEP 703) from multiple interpreters (PEP 734).
The 27B was more careful about unsupported benchmark claims and missing
compatibility information, but still blurred the PEP 703/734 distinction
and phrased PEP 779 as introducing the no-GIL mode rather than moving an
already experimental mode to official support.

In this particular workload the RunPod executions finished roughly
4.7-5.3 times sooner than the operator-local 9B executions. That compares
different **systems and response lengths**, not model-intrinsic speed.
A contemporaneous `ollama ps` observation showed the 27B loaded
`100% GPU` with an 8,192-token context. The corresponding local
execution's phase timing was not instrumented.

## Findings

1. **Transport works; answer trust is unproven.** HAC supplied the selected
   evidence to ordinary Chat. Returned provenance does not certify that any
   generated claim was supported by the source it cites.
2. **Source quality matters.** In this example Advanced supplied a decisive
   official passage missing from Basic, correcting one important fact in
   downstream answers. It also omitted a useful historical comparison.
3. **Model choice matters, but does not solve grounding.** The 27B performed
   better on the fictional selection test and avoided some unsupported
   assertions, yet it still misinterpreted benchmarks, blurred independent
   features, and produced an overconfident conclusion in one Basic answer.
4. **A stronger instruction is not a guarantee.** A source-only instruction
   did not resolve either 9B FALCON-62 contradiction. Source citation,
   logical consistency, and factual correctness remain separate concerns.
5. **Reliability is not established.** These polished answers still contained
   plausible errors. The tests do not justify treating External Information
   as independently verified technical advice or claiming a failure rate.

## Open questions and next evidence

- Before any product or architecture change, define a small explicit answer
  rubric: factual accuracy, claim-to-source support, citation correctness,
  missing-information handling, reasoning consistency, and relevance.
- Continue the already planned bounded provider-only comparison of Tavily
  `advanced` source selection with preferred versus excluded domains.
  Such settings are experimental: RFC-0154 explicitly did **not** authorize
  production-domain filtering.
- If the evidence warrants it, repeat selected fixed-source tests with
  controlled generation parameters and multiple runs, preserving the
  separation between acquisition effects, model effects, and hardware timing.
- Investigate long local generation times independently of provider latency.
- Keep the possible instruction change and any claim-checking strategy as
  unresolved questions. Changing accepted Source-Grounded Chat framing or
  provider configuration would require the applicable RFC process.

## Outcome

Retain this as an investigation record only. Make **no** change to HAC core,
Tavily plugin, adapter behavior, default models, source framing, retained
configuration, privacy boundaries, or accepted RFCs on the strength of these
observations alone.
