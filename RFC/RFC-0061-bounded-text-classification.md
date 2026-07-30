# RFC-0061: Bounded Text Classification

Status: Accepted

Date: 2026-07-30

Author: frian

## Summary

Home AI Cluster should add one bounded executable capability, `classify`.
It selects exactly one label from a finite operator-supplied set for one
bounded text source.

`classify` is a first-class capability, not a prompt convention layered on
`chat`. It has a dedicated request, a dedicated normalized result, one explicit
adapter responsibility, a closed internal transport variant, receiver-local
execution, and a native operator command. It preserves local-first routing,
ordered declared remotes, bounded pre-request fallback, and engine independence.

The accepted explicit static vocabulary would become `chat`, `summarize`, and
`classify`, but the omission compatibility default would remain `chat` plus
`summarize`. Consequently, `classify` eligibility is always explicit in an
ordinary static caller-local or remote declaration.

## Problem

The repository has two closed executable semantics: conversational `chat` and
bounded-source `summarize`. `summarize` established that a second capability
needs a dedicated request, adapter operation, native endpoint, closed internal
transport envelope, local and declared-remote execution, and privacy-safe proof;
it is not a chat prompt convention. [RFC-0051](RFC-0051-bounded-text-summarization.md)

The completed third-capability investigation selected `classify` over `rewrite`
and `question-answer`. A finite operator-supplied label set gives classification
an exact input and output boundary: the cluster can guarantee only that a
successful selected label belongs to that set, without claiming that a model's
semantic judgment is correct. [Third executable capability investigation](../docs/third-executable-capability-investigation.md)

Without a dedicated contract, classification would be an unbounded chat prompt
with inconsistent runtime behavior, no structural result validation, and no
truthful capability declaration. Generic structured output would over-solve this
single capability by introducing arbitrary payloads, schemas, and runtime-specific
mechanisms before evidence requires them.

## Goals

- Establish one real third executable capability with bounded text and labels.
- Keep request validation and result normalization cluster-owned and
  engine-independent.
- Guarantee exact structural membership of a successful selected label in the
  operator-supplied label set, without asserting semantic correctness.
- Support local and declared-remote execution through the existing
  capability-centered, local-first architecture.
- Support heterogeneous nodes through explicit `classify` eligibility.
- Preserve the `chat` plus `summarize` omission compatibility default.
- Reuse ordinary local/remote transport, native CLI, timeout, preflight, and
  attribution boundaries where their existing meaning applies.
- Avoid generic structured output, runtime discovery, retrieval, persistence,
  and scheduling.

## Non-goals

This RFC does not authorize:

- multi-label, ranked, weighted, or hierarchical classification;
- confidence scores, thresholds, explanations, rationales, alternatives, or
  automatic label generation;
- generic structured output, arbitrary JSON schemas, or arbitrary payloads;
- embeddings, retrieval, indexing, document stores, persistence, classification
  history, training, or fine-tuning;
- model selection, dynamic node selection, scheduling, load balancing, or
  performance scoring;
- streaming, tools, agents, web access, filesystem discovery, or autonomous
  loops;
- OpenAI-compatible classification access or a new general public API;
- receiver capability discovery, remote runtime verification, or cross-node
  capability negotiation; or
- implementation, tests, examples, proof execution, or a roadmap change in
  this RFC pull request.

## Proposal

### Capability definition

`classify` selects exactly one label from a finite operator-supplied set for one
bounded text source.

Labels belong to the request. Home AI Cluster owns request validation and result
normalization. A runtime adapter receives the normalized source and exact ordered
label set, then proposes one label. A result succeeds only when that proposal is
exactly one supplied label.

The cluster does not promise that the selected label is semantically correct,
complete, useful, or appropriate for the operator's unstated intent. It does
promise structural membership in the supplied set. Classification does not treat
labels as code, commands, routing selectors, model names, or node identities.

### Request validation

The capability introduces a dedicated normalized request concept:

```text
ClassifyRequest
  text: str
  labels: ordered sequence[str]
  constraints: existing request constraints
```

The source follows the existing bounded summarize input convention:

- it must be valid UTF-8 input;
- it must not be blank after the existing non-blank source check;
- it must be at most 65,536 UTF-8 bytes; and
- it is never truncated.

The labels must satisfy all of the following before client construction, request
sending, routing, or runtime execution:

- at least two and at most 32 labels;
- each item is a string;
- each label is non-empty;
- each label is at most 128 UTF-8 bytes;
- labels are unique by exact string/code-point equality; and
- supplied order is preserved.

Label order has no capability-routing, fallback, or remote-priority meaning.
Remote declaration order remains the only remote priority rule. No label
descriptions, IDs, aliases, examples, weights, schemas, probabilities, or
confidence thresholds are added.

There is no implicit `unknown`, `none`, `other`, or fallback outcome. An operator
who needs one includes its own label, for example
`["invoice", "personal", "unknown"]`. Home AI Cluster reserves no spelling and
does not assign meaning to that label.

### Result validation and projection

`classify` uses a dedicated capability result rather than extending the current
plain-text `ClusterResult` with a generic payload. The conceptual normalized
success shape is:

```text
ClassifyResult
  selected_label: str
  node_id: str
```

`node_id` retains existing cluster-owned execution attribution. The result does
not expose adapter name, model metadata, confidence, rationale, alternatives,
raw runtime output, or adapter prompts.

After adapter execution, the cluster accepts a result only when its proposed
selected label exactly equals one label in the original request. It performs no
trimming, case folding, Unicode normalization, fuzzy matching, prose parsing,
silent repair, or conversion of values such as `"Label: invoice"` to `"invoice"`.
Missing, non-string, or non-member output is an invalid classification result.

Exact matching keeps result policy visible and cluster-owned instead of allowing
each adapter to hide repair semantics. The adapter remains free to use a runtime
prompt, grammar, JSON mode, or constrained decoding internally, but none becomes
part of the cluster contract.

Ordinary non-verbose output prints only `selected_label` followed by a newline.
Verbose and JSON forms may project only the selected label and existing
cluster-owned attribution, following the ordinary native-command presentation
conventions. They must not expose raw model output or new model metadata.

### Static declaration compatibility

After implementation, the accepted explicit static capability vocabulary is:

```text
chat
summarize
classify
```

The omission compatibility default remains exactly:

```text
chat
summarize
```

These are deliberately separate concepts. Existing inline, flat TOML, and
ordered remote declarations that omit capability data remain eligible only for
`chat` and `summarize`; they do not silently assert `classify` support. A caller
must explicitly declare `classify` for the fixed caller-local candidate or a
remote node. The existing flat TOML, `[[remote_nodes]]`, and repeated inline
capability forms receive `classify` only as a new accepted explicit name.

For example, after a separate implementation:

```toml
local_capabilities = ["chat", "classify"]

[[remote_nodes]]
node_id = "classification-node"
base_url = "http://192.0.2.10:8000"
capabilities = ["classify"]
```

This example is explanatory only. It does not change examples or configuration
in this RFC PR. Static declarations remain caller-owned eligibility assertions;
they do not verify a receiver, adapter, runtime, or model. [RFC-0058](RFC-0058-explicit-static-remote-capabilities.md), [RFC-0059](RFC-0059-caller-local-static-capabilities.md)

### Routing, preflight, and status

Existing routing policy remains authoritative:

1. capability membership filters eligibility;
2. an eligible local candidate has local-first precedence;
3. eligible remotes retain declaration order;
4. only the accepted pre-request connection-unavailable fallback applies; and
5. no load balancing, busy/idle selection, model selection, scoring, or dynamic
   scheduler is introduced.

A node is eligible for `classify` only when it explicitly declares `classify`.
Preflight projects the constructed explicit capability exactly as it does current
declared capabilities, validates no remote runtime support, and remains
network-free. The public status contract remains unchanged and does not become
capability discovery. [RFC-0036](RFC-0036-static-operator-preflight.md), [RFC-0041](RFC-0041-explicit-static-cluster-status.md)

### Adapter boundary

The runtime-adapter protocol gains one explicit capability-specific future
responsibility conceptually equivalent to:

```text
classify(ClassifyRequest) -> proposed selected label
```

The adapter receives the normalized source and exact ordered labels, maps them
to its runtime, and returns one proposed label. It must not expose runtime-
specific structured-output machinery, scores, rationales, or raw model output
through the cluster boundary. The cluster, not the adapter, enforces exact
membership after return.

This adds one named operation rather than a generic `execute()` method or a
plugin-shaped capability framework. It preserves the runtime adapter boundary:
the core has no runtime prompt, grammar, JSON-mode, constrained-decoding, or
model-specific field. [RFC-0003](RFC-0003-runtime-adapter-interface.md)

### Local, internal transport, and receiver execution

Implementation must create one complete capability-specific vertical slice:
dedicated request model, application dispatch, adapter method, local execution,
result validation, closed remote transport variant, receiver validation,
receiver-local execution, and native CLI.

The existing internal receiver endpoint gains exactly one closed tagged
classification request variant. Its final field nesting should follow the
existing tagged internal request convention, conceptually:

```json
{
  "kind": "classify",
  "request": {
    "text": "...",
    "labels": ["...", "..."]
  }
}
```

Unknown tags remain invalid. Malformed source or labels fail before runtime
execution. The receiver revalidates source and labels at its trust boundary,
executes locally, and never forwards the request. The response carries only the
normalized selected label and accepted cluster-owned attribution or existing
safe failure behavior. No new distributed protocol family, version negotiation,
arbitrary payload schema, or receiver capability discovery is introduced.
[RFC-0013](RFC-0013-minimal-remote-transport-boundary.md), [RFC-0014](RFC-0014-minimal-concrete-transport-protocol.md)

There is no new general public classification API and no OpenAI-compatible
expansion. The internal receiver transport remains closed; ordinary native
`hac classify` is the operator-facing surface.

### Native CLI and timeout

The root command gains:

```text
hac classify
home-ai-cluster classify
```

No standalone executable is added. Input mirrors ordinary summarize:

```sh
hac classify --text "..." --label invoice --label personal
hac classify --file note.txt --label invoice --label personal
printf '...' | hac classify --label invoice --label personal
```

Exactly one source is selected from `--text`, `--file`, or stdin. Explicit
source input ignores stdin as the accepted summarize command does; repeated
`--text` or `--file` is invalid. At least two repeated `--label` options are
required and duplicate labels are invalid. Source and labels are validated before
HTTP client construction or request sending. `--verbose` and `--json` retain the
existing mutually exclusive presentation convention.

`--timeout-seconds SECONDS` applies with RFC-0060's existing native-client
semantics: one finite, topology-blind, per-invocation HTTPX scalar timeout,
defaulting to 120.0 seconds when omitted. This RFC creates no
classification-specific timeout. [RFC-0054](RFC-0054-minimal-summarize-cli.md), [RFC-0060](RFC-0060-explicit-native-client-timeout.md)

### Failures

The implementation should retain existing safe stdout, stderr, and exit-code
ownership wherever possible. It must distinguish these internal conditions:

1. invalid operator input;
2. no eligible `classify` candidate;
3. ordinary cluster unavailable;
4. runtime unavailable;
5. malformed or unsupported internal request; and
6. invalid classification result (missing, non-string, or not exactly a supplied
   label).

Invalid classification result is a narrow execution-boundary condition, but it
does not create a new public error vocabulary. It reuses the existing structured
actual-request `execution-failed` category and the ordinary native client's safe
generic request-failure behavior. Raw adapter output, runtime output, prompts,
labels, source text, transport details, and exception details are never returned
as error details. [RFC-0034](RFC-0034-structured-actual-request-failures.md)

### Privacy and trust boundary

Source text, labels, selected labels, request bodies, receiver payloads, adapter
prompts, raw model output, and classification statistics are not retained by this
capability. No database, history, metrics, or persistence is introduced.

RFC-0035's bounded local history belongs only to the explicit
`explain-request --record-history` surface; this RFC does not extend that history
to ordinary `classify` requests. [RFC-0035](RFC-0035-bounded-local-request-history.md)

Labels are untrusted operator input. Receiver-side validation repeats trust-
boundary validation; exact membership is enforced after runtime execution; and
remote declarations remain caller assertions rather than receiver verification.
Labels are never executed as commands or code.

### Testing and proof

After implementation, focused tests must cover:

- source missing, blank, oversized, and malformed input;
- fewer than two or more than 32 labels; blank, oversized, duplicate, and
  malformed labels;
- exact local and declared-remote success, output presentation, attribution,
  timeout reuse, and receiver validation;
- invalid adapter output: missing, non-string, unknown, extra prose, case
  mismatch, and whitespace mismatch;
- omitted defaults excluding `classify`, explicit local and remote eligibility,
  exclusion of non-classify candidates, declaration order, preflight projection,
  and rejection of unknown explicit capability names; and
- absence of retained source, labels, selected-label history, prompts, raw
  outputs, or receiver payloads.

One local operator proof, one real two-machine routed classify proof, and one
heterogeneous eligibility proof are required. Retained proof material may record
only structural facts such as selection of an explicitly classify-capable remote,
acceptance of a supplied-label result, exclusion of non-eligible candidates, and
caller-owned attribution. It must not retain source, real labels, selected label,
prompts, raw model output, addresses, hostnames, model/runtime identifiers,
hardware identity, credentials, or raw logs.

## Rationale

Classification is a small, useful local triage operation with a capability-
centered request and a structurally verifiable result. It demonstrates a
non-free-text result without requiring generic structured output. Explicit label
sets leave semantics under operator control while exact matching prevents hidden
adapter-specific repair policy.

Explicit declaration preserves honest static eligibility. Keeping the omission
default unchanged avoids claiming that every existing remote supports the new
contract. The capability remains usable on heterogeneous personal nodes while
preserving static deterministic routing and local-first behavior.

## Alternatives considered

### Keep only chat and summarize

Rejected. It leaves the selected bounded third-capability need unresolved and
does not exercise a non-free-text result boundary.

### Add rewrite

Rejected for this RFC. Free-form rewrite instructions are close to chat, while a
style taxonomy adds policy and cannot make semantic meaning preservation
verifiable.

### Add question-answer

Rejected for this RFC. Source-only grounding is either unverifiable or requires
citations/offset semantics; retrieval would be a larger excluded system.

### Use a chat prompt convention

Rejected. It hides source/label/result semantics in prompts and cannot enforce
the selected-label contract at the capability boundary.

### Add generic structured output first

Rejected. One exact selected label does not justify schemas, arbitrary JSON, or
a generalized result framework.

### Multi-label classification or confidence scores

Rejected. Both multiply result semantics and validation without evidence that
one exact label is insufficient.

### Add classify to the omission default

Rejected. Existing omitted declarations must not silently become eligible for a
new runtime contract.

### Reserve unknown or none

Rejected. A universal spelling would impose cluster policy on operator labels.
An operator can explicitly supply any desired fallback label.

### Receiver-reported capability verification

Rejected. It introduces observation, trust, staleness, compatibility, and
protocol concerns beyond static caller-owned eligibility.

## Trade-offs

This proposal makes structurally verifiable success, heterogeneous explicit
routing, bounded local triage, a clear CLI, and engine-independent adapter
responsibility easier.

It makes a first capability-specific non-free-text result necessary; requires
exact normalization failure handling and explicit opt-in declarations; and
requires a complete vertical-slice implementation. Some runtimes may need
careful adapter-owned prompting or constrained decoding. That complexity is
acceptable because it remains one bounded request/result contract, does not
leak runtime mechanisms into the core, and avoids a generic framework.

## Impact

After acceptance, a separate implementation sequence may change only the
dedicated request/result models, adapter protocol and supported adapters,
application dispatch, local execution, closed internal transport and receiver
validation, native root command and output, explicit static-capability
validation/declaration/preflight support, focused tests, operator documentation,
and bounded proof material.

It must preserve existing chat and summarize behavior, local-first routing,
remote order, accepted fallback, static status fields, receiver non-forwarding,
privacy defaults, and engine-independent core boundaries. It must not create a
general capability registry, generic result model, generic structured output,
or OpenAI-compatible expansion.

## Open questions

- Do implementation evidence and supported runtimes confirm the initial maximum
  of 32 labels and 128 UTF-8 bytes per label, or require a narrower bound?
- What exact model names and helper placement best implement the dedicated
  `ClassifyResult` while preserving existing ordinary presentation conventions?

The central capability, request, exact-result, explicit-opt-in default, routing,
receiver, CLI, and privacy decisions are not open.

## Decision

Home AI Cluster accepts `classify` as its third executable capability.

`classify` selects exactly one label from a finite operator-supplied label set
for one bounded text source. The request has one non-blank UTF-8 source of at
most 65,536 bytes and between 2 and 32 non-empty labels. Labels are unique by
exact string equality, at most 128 UTF-8 bytes each, and retain supplied order.

A successful result contains exactly one `selected_label` that exactly equals
one supplied label. Home AI Cluster performs no trimming, case folding, Unicode
normalization, fuzzy matching, prose repair, or implicit fallback-label
handling. There is no reserved `unknown`, `none`, or `other` label; operators
include one explicitly when needed.

The accepted explicit static capability vocabulary is `chat`, `summarize`, and
`classify`. The omission compatibility default remains `chat` plus `summarize`,
so `classify` eligibility is always explicit for caller-local and remote static
declarations.

The capability reuses existing local-first routing, ordered declared remotes,
bounded pre-request fallback, closed internal receiver transport, native client
timeout semantics, preflight projection, normalized attribution, and safe
structured failure boundaries. Implementation must add one complete
capability-specific vertical slice: dedicated request and classification result,
one adapter method, local and receiver-local execution, one closed internal
transport variant, trust-boundary validation, native `hac classify` and
`home-ai-cluster classify` commands, exact membership validation, and focused
local, remote, heterogeneous, and privacy-safe proof coverage.

This decision does not authorize generic structured output, arbitrary schemas,
multi-label classification, scores, rationales, persistence, retrieval,
discovery, scheduling, model selection, OpenAI-compatible expansion, or
receiver capability verification.
