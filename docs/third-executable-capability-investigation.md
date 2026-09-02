# Third Executable Capability Investigation

Status: Complete

## Question

> Which single third executable capability should Home AI Cluster define next?

This investigation evaluates only `rewrite`, `question-answer`, and `classify`.
It records investigation guidance, not an accepted capability contract or
implementation authorization.

## Current Baseline

The executable vocabulary is closed to `chat` and `summarize`.
`summarize` has a bounded `SummarizeRequest`, a capability property, explicit
adapter method, native `/v1/summarize` route, closed tagged internal envelope,
local and declared-remote execution, and an unchanged text `ClusterResult`.
It is expressly not a chat prompt convention or a generic capability framework.
[`models.py`](../src/home_ai_cluster/core/models.py),
[`base.py`](../src/home_ai_cluster/adapters/base.py),
[`routes.py`](../src/home_ai_cluster/api/routes.py),
[Phase 18 closeout](phase-18-closeout.md),
[RFC-0051](../RFC/RFC-0051-bounded-text-summarization.md)

Both static remote and caller-local declarations can express explicit non-empty
unique subsets of exactly those two names. Omission retains `chat` plus
`summarize`; it is a compatibility rule, not runtime discovery. Preflight
projects constructed capability lists without network activity; public status
does not report capability lists. [RFC-0058](../RFC/RFC-0058-explicit-static-remote-capabilities.md),
[RFC-0059](../RFC/RFC-0059-caller-local-static-capabilities.md),
[`static_capabilities.py`](../src/home_ai_cluster/static_capabilities.py),
[`static_preflight.py`](../src/home_ai_cluster/commands/static_preflight.py),
[`cluster_status.py`](../src/home_ai_cluster/cluster_status.py)

The current remote transport accepts only the tagged `chat` and `summarize`
internal variants and the receiver executes them locally without forwarding.
The ordinary summarize command demonstrates the current bounded-source input
pattern: exactly one of `--text`, `--file`, or standard input, locally bounded
before a native loopback request. [`remote_transport.py`](../src/home_ai_cluster/core/remote_transport.py),
[`routes.py`](../src/home_ai_cluster/api/routes.py),
[`summarize_command.py`](../src/home_ai_cluster/commands/summarize_command.py),
[Phase 18 two-machine proof](phase-18-two-machine-summarize-proof.md)

## Candidate A — Rewrite

`rewrite` would transform one bounded source text according to one explicit
instruction while attempting to preserve its essential meaning. It has useful
operator-facing cases—clarity, formality, simplification, grammar, and
shortening—but the instruction creates the central boundary problem.

A free-text instruction keeps the surface small but makes the capability close
to one-turn chat with pasted text. A closed style vocabulary makes validation
deterministic, but choosing even a small style taxonomy is new policy and does
not honestly cover arbitrary transformations. “Preserve meaning” can be a
stated model objective, not a success condition that Home AI Cluster can verify.
The likely plain-text result is compatible with the existing result shape, but
structural tests could only verify bounds, dispatch, transport, and attribution,
not semantic preservation or style quality.

The capability is feasible, but its distinction from `chat` is weaker than the
existing distinction between `summarize` and chat. Its free-form instruction
also gives adapters considerable hidden prompt-policy ownership. The future
RFC would need to decide that policy before a useful request shape exists;
therefore it is not the smallest next executable capability.

## Candidate B — Question Answer

`question-answer` would answer one explicit question using one bounded,
operator-supplied source text. A source-only grounding rule would make it
meaningfully narrower than chat with pasted context, while a required plain-text
“not answered in source” outcome could avoid an unsupported factual claim.

It has direct local-first value for reading a supplied note or file without
retention, search, indexing, embeddings, or document storage. Existing
summarize `--text`/`--file`/stdin input patterns offer a credible bounded
operator surface. A plain-text answer can reuse the present successful result
shape, and tests can verify structural validation and that the exact normalized
source/question crosses the local and remote boundaries.

However, the grounding guarantee is not independently verifiable without
citations, offsets, or semantic judging. Adding either citations or offsets
changes the result contract and creates source-location semantics. Excluding
them leaves a valuable but chat-adjacent response; adding retrieval would be a
different, explicitly excluded architecture. Question-answer is a credible
future bounded capability, but its primary distinction relies on a semantic
promise that the cluster cannot observe.

## Candidate C — Classify

`classify` would select exactly one label from a bounded operator-supplied set
for one bounded source text. It is a real capability rather than a prompt
template because its input has a first-class label set and its sole successful
result is one member of that set.

Exactly one label is the smallest unambiguous initial result. The RFC should
decide whether `unknown` is a mandatory reserved outcome; this investigation
recommends requiring an explicit caller-supplied `unknown` label when an
operator needs that outcome, rather than creating a hidden universal label.
Duplicate, blank, and over-limit labels should be invalid. Confidence scores,
multiple labels, rationales, schemas, and arbitrary JSON are unnecessary.

This candidate has immediate operator value for bounded local triage such as
selecting a caller-defined category for a note. It is engine-independent: an
adapter maps the normalized source and labels to its runtime, while the cluster
owns the exact label validation and accepts no runtime-specific label metadata.
Most importantly, it gives a small, testable proof that a capability result need
not be free text: acceptance is structural membership, not an assertion that a
model made the best semantic choice.

## Full-Stack Comparison

All three candidates require a complete new vertical slice; none is implemented
or accepted today. The table identifies the new work a future RFC and
implementation would need to authorize.

| Slice | Rewrite | Question answer | Classify |
| --- | --- | --- | --- |
| 1. Meaning | Transform source under instruction; preservation is aspirational. | Answer from supplied source; grounding is aspirational without evidence fields. | Select one supplied label; membership is structurally checkable. |
| 2. Request model | `text`, free instruction or a new closed style set. | `text`, `question`. | `text`, non-empty unique `labels`. |
| 3. Result model | Plain text is plausible. | Plain text is plausible; citations/offsets are a separate decision. | Exact `selected_label`; a dedicated result is needed. |
| 4. Dispatch | New capability-specific request branch. | New capability-specific request branch. | New capability-specific request branch plus result projection. |
| 5. Adapter method | Named rewrite method plus prompt-policy mapping. | Named question-answer method plus grounding mapping. | Named classify method plus constrained-label mapping. |
| 6. Local execution | Add request to explicit local execution dispatch. | Same. | Same, with label-result normalization. |
| 7. Remote transport | Add one tagged internal request variant. | Add one tagged internal request variant. | Add one tagged internal request and exact result variant. |
| 8. Receiver endpoint | Existing internal receiver accepts a new closed tag. | Same. | Same. |
| 9. Receiver validation | Source and instruction bounds; style policy if closed. | Source/question bounds and source-only rule boundary. | Source, label count/size, blank, duplicate, and selected-label validation. |
| 10. Native CLI | Source input plus instruction option; free text is awkward. | Source input plus required question option. | Source input plus repeated `--label`; concise and deterministic. |
| 11. Static vocabulary | RFC must add `rewrite` and define declaration semantics. | RFC must add `question-answer` and define declaration semantics. | RFC must add `classify` and define declaration semantics. |
| 12. Omission default | Expanding it makes every omitted node eligible for subjective transforms. | Expanding it makes every omitted node eligible for a grounded-answer assertion. | Keep unchanged; require explicit eligibility for the new non-text result. |
| 13. Preflight | Project it only after accepted declaration support. | Same. | Same. |
| 14. Status | No change is needed; it remains a different observation contract. | Same. | Same. |
| 15. Structured failures | Invalid request and execution failures; preservation has no honest failure test. | Invalid request, no candidate, execution, and possibly unanswerable-source policy. | Invalid request, no candidate, execution, and invalid adapter-selected label. |
| 16. Focused tests | Bounds/dispatch only; no semantic-preservation assertion. | Bounds/dispatch only; no semantic-grounding assertion. | Bounds, labels, exact result membership, dispatch, and failure mapping. |
| 17. Two-machine proof | One transformed text and caller-owned attribution. | One bounded source/question answer and attribution. | One bounded source/labels request returning an accepted label and attribution. |
| 18. Documentation | Explain instruction ownership and non-verifiable preservation. | Explain source-only scope and no retrieval/citations. | Explain exactly-one label, supplied-label ownership, and no confidence. |

`classify` has the clearest distinct request/result meaning, deterministic
validation, and smallest semantic claim. Its dedicated result requires more
care than the two plain-text alternatives, but that is deliberate bounded work
rather than a generic structured-output abstraction.

## Compatibility Default

For all candidates, this investigation favors **Option 2**: leave omission as
`chat` plus `summarize` and require an explicit local or remote declaration for
the third capability. This preserves existing operator meaning and avoids
making a node eligible for a new operation merely because a legacy declaration
omitted capabilities.

For selected `classify`, Option 2 is especially important: an omitted
declaration should not assert that a remote runtime can satisfy a constrained
label-selection contract. A future RFC owns the final compatibility decision,
including the relationship between ordinary local adapter advertisement and
caller-local declaration eligibility; this investigation only recommends the
narrow, honest transition.

## Decision

**Outcome C — Select classify.**

`classify` is the smallest useful third capability because it has a simple
operator-supplied input boundary, an exact non-free-text output, no storage or
retrieval requirement, and meaningful structural tests. It remains
capability-centered and can demonstrate heterogeneous eligibility without
turning route selection into scheduling. Unlike rewrite and question-answer, it
does not require Home AI Cluster to claim it can verify meaning preservation or
source grounding.

## Proposed RFC Boundary

The following is investigation guidance only; it is not an accepted contract.

- **Definition:** Select exactly one operator-supplied label for one bounded
  source text.
- **Request:** `text: str` and `labels: list[str]`; initially non-blank text,
  at least two non-blank unique labels, source at most 65,536 UTF-8 bytes,
  labels at most 32, and each label at most 128 UTF-8 bytes. The future RFC
  should validate these limits against implementation evidence.
- **Result:** one exact `selected_label: str` that belongs to the request's
  labels, with existing cluster attribution retained. This should be a
  capability-specific result, not a generic JSON result or score container.
- **CLI:** `hac classify` with exactly one bounded source input (`--text`,
  `--file`, or stdin) and repeated `--label LABEL`; ordinary output prints the
  selected label, while the existing verbose/JSON conventions can expose only
  normalized attribution.
- **Adapter responsibility:** map the normalized source and label set to the
  runtime, return one proposed label, and never leak prompts, raw runtime
  responses, scores, or model-specific schema through the cluster contract.
- **Remote/receiver shape:** add one exact `kind: "classify"` internal envelope
  to the existing closed endpoint, with the receiver validating and executing
  locally without forwarding.
- **Likely failures:** invalid public input; invalid internal envelope; no
  selectable `classify` candidate; runtime unavailable; and an adapter result
  that is absent, malformed, or not one supplied label. The RFC must decide
  normalized public status/message ownership without exposing raw output.
- **Static declarations:** add `classify` only through the existing bounded
  capability validation and declaration surfaces after an RFC decision;
  preflight may project it and status remains unchanged.
- **Default:** retain omission as `chat` plus `summarize`; opt in to `classify`
  explicitly.
- **Minimum proof:** focused tests for labels and invalid results; one local
  native request; one declared-remote request with caller-owned attribution;
  and a heterogeneous eligibility test showing a non-`classify` candidate is
  excluded. Retained evidence must contain no source text, labels, raw request,
  generated output, or private topology.

## Required Follow-up

Write and review a new RFC before implementation. It must decide the exact
`classify` request/result types, label and source limits, `unknown` treatment,
adapter-normalization boundary, public and internal failure mapping, transport
tag, static-vocabulary/default change, CLI/output contract, and proof scope.
Only after acceptance should implementation, tests, and a two-machine proof be
planned.

## Deferred Work

This investigation does not authorize rewrite, question-answer, retrieval,
citations, source offsets, conversation history, persistence, databases,
embeddings, indexing, filesystem discovery, web access, tools, agents,
streaming, model selection, dynamic node selection, scheduling, load balancing,
generic structured output, arbitrary JSON schemas, or OpenAI-compatible API
expansion. It also does not change the accepted `chat`/`summarize` vocabulary,
declaration defaults, routes, transport, adapters, tests, or runtime behavior.
