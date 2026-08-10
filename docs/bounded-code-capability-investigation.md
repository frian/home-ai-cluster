# Bounded code capability investigation

## Status

Investigation only. This document proposes no architecture or behavior change.

## Question

Should bounded textual source-code or shell/script generation be a
first-class Home AI Cluster `code` capability, or is it ordinary Chat with
caller-owned instructions?

The candidate is deliberately narrow:

```text
explicit textual instruction
  -> bounded textual source code or shell/script text
```

It excludes repository editing, filesystem or shell access, command or test
execution, Git, tools, agents, planning loops, indexing, RAG, embeddings, and
arbitrary structured output. Generated commands remain output text; they do
not grant Home AI Cluster authority to execute anything. Pasted source code is
ordinary potentially sensitive request content and remains subject to existing
local-first, privacy-first request handling.

## Existing capability evidence

Capabilities are cluster-facing semantic requirements, not model, runtime,
machine, prompt-preset, or UI names. The core `Capability` model is name-based,
but the accepted static capability vocabulary is intentionally closed and
currently contains `chat`, `summarize`, and `classify`. Existing routing filters
by capability membership before applying local-first and declared-remote order.
It does not score response quality, inspect models, probe runtimes, or select a
machine directly.

| Capability | Request and input semantics | Result semantics | Eligibility and adapter consequence |
| --- | --- | --- | --- |
| `chat` | A non-empty ordered sequence of plain-text system, user, and assistant messages in `ClusterRequest`. | Free-form normalized text with cluster attribution. | A chat-capable node and adapter are required; the adapter has an explicit `chat` operation. |
| `summarize` | One non-blank source text, bounded to 65,536 UTF-8 bytes, in `SummarizeRequest`. Caller-side file, standard-input, browser PDF, and other accepted conveniences normalize to this same text request rather than becoming capabilities. | Free-form normalized summary text with cluster attribution. | A summarize-capable node and adapter are required; the adapter has an explicit `summarize` operation. |
| `classify` | One bounded source text plus an ordered, finite, exact-unique operator label set in `ClassifyRequest`. | Exactly one supplied label, structurally validated by the cluster, with cluster attribution. | A classify-capable node and adapter are required; the adapter has an explicit `classify` operation and the cluster validates the proposed label. |

`summarize` and especially `classify` therefore add more than a caller
instruction. They introduce distinct normalized inputs that the cluster owns
and, for `classify`, an exact result invariant that it can enforce. The
adapters may use a runtime's chat transport internally, so distinct capability
does not necessarily mean distinct transport primitive. Conversely, the
accepted browser PDF path is input acquisition before an unchanged `summarize`
request; it is not a PDF capability.

The existing examples do not establish a universal admission rule. They prove
that contract-backed capabilities are valid. They do not decide whether an
explicit operator-owned suitability promise may itself be a valid semantic
eligibility distinction when request, result, and adapter transport are shared.

## Declaration ownership and the specialized-node counterexample

The accepted static-declaration RFCs make capabilities caller-owned routing
permissions. A declaration says which capabilities the caller permits the
router to consider; it does not verify that a receiving application, adapter,
or runtime implements a capability, discover runtime state, or derive facts
from a model. The same distinction applies to caller-local static capability
restrictions. This is compatible with a repository owner knowing an external
fact about their local composition and using a static declaration to constrain
routing.

That makes this conceptual topology coherent at the declaration layer:

```text
node-a: chat
node-b: chat, code
```

An operator may have chosen node-b because they consider its model or local
runtime composition suited to coding work. That model or runtime is the
operator's reason for the declaration, not a cluster-facing selector. HAC need
not inspect, name, benchmark, inventory, or compare it. In that limited sense,
the topology can remain engine- and model-name-independent.

However, current RFCs use closed declaration vocabularies for capabilities that
already have defined cluster contracts. They explicitly reject arbitrary
capability names, and the adapter boundary says adapters report capabilities
they can provide. The accepted architecture does not say whether a shared
free-text adapter operation can truthfully provide a second capability solely
because an operator considers its composition more suitable. It also does not
define what `code` promises to a caller beyond a vague quality category.

The risk is not that every operator declaration must be mechanically verified;
accepted static declarations already reject that premise. The risk is that an
undefined label becomes hidden model preference: users cannot tell whether
`code` means syntax-aware generation, a bounded source transformation, an
operator's quality judgment, or execution authority. The current record gives
no general boundary that separates a clear semantic suitability promise from an
arbitrary label.

### Capability truthfulness interpretations

| Interpretation | Fit with accepted evidence | Consequence for `code` |
| --- | --- | --- |
| Contract-backed capability | Directly demonstrated by `summarize` and `classify`; their declarations remain unverified routing permissions, but the capability meaning is cluster-defined. | The text-only candidate remains Chat unless a distinct contract is defined. |
| Operator-declared suitability capability | Static ownership supports an operator controlling eligibility without runtime inspection. | Could make node-b eligible if `code` has a bounded semantic promise, but current RFCs do not establish that this type of capability is permitted. |
| Hybrid | Consistent with explicit operator control and engine independence if the semantic category is closed, bounded, and not inferred from model identity. | Plausible, but needs an architecture decision defining truthfulness, adapter reporting, and caller requirements before it can authorize `code`. |

## Candidate `code` semantics and routing value

The narrow candidate accepts textual instructions and optional pasted textual
code, then returns textual code or an explanation/transformation. It has no
specified input field beyond text, no bounded output form beyond ordinary
response text, and no cluster-verifiable success property. Adding language,
filename, repository, model, runtime, execution permission, or similar fields
would broaden the problem without establishing a need.

This remains textually representable as a Chat request whose messages ask for a
Bash administration script, a Python maintenance utility, or an explanation or
transformation of pasted code. The current native Chat request already carries
plain-text messages and returns plain text through the existing runtime path.

If a caller could explicitly require `code`, however, removing `code` could
also remove the operator's ability to exclude node-a and route only to
coding-designated node-b. That is a real routing consequence, not a different
transport consequence. It may be legitimate operator policy if `code` is an
accepted semantic suitability category. It is hidden model selection if the
label merely means “the operator prefers this model” without a defined promise.
The accepted architecture does not provide the criterion needed to choose
between those descriptions.

## Request, routing, and adapter implications

Three conceptual first shapes have different implications:

| Shape | What it establishes | What remains unresolved |
| --- | --- | --- |
| A. `CodeRequest(text=...)` | A new cluster request could define a distinct input boundary. | No evidence yet requires a new input or result shape. Adding one only to justify routing would be circular. |
| B. Existing `ClusterRequest(messages=..., capability=code)` | The core request concept already carries a requested named capability, so shared Chat messages and a stronger required capability are conceptually representable. | Current accepted public, static-vocabulary, adapter, and transport contracts do not authorize `code`; deciding caller requirement semantics would be architectural work. |
| C. Caller-side Chat only | Preserves present text-in/text-out behavior and needs no new architecture. | Cannot exclude a chat-only node through a `code` eligibility requirement. |

The adapter evidence is similarly mixed. Existing `summarize` and `classify`
have named adapter responsibilities, even where adapters use their runtime's
chat transport. This demonstrates that transport primitive is not the sole
test. It does not decide whether one adapter `chat` operation may honestly
support both `chat` and a suitability-only `code` declaration. If it may, the
declaration must not imply tool access, code execution, or a runtime feature
the adapter does not provide.

## Operator usefulness

| Bounded use | Does `code` improve routing? | Current architectural fit |
| --- | --- | --- |
| Generate a small Bash administration script from explicit instructions. | A declared code-suitability category could restrict routing, but present architecture does not define it. | Text remains Chat-representable; the script is output, not authority to execute it. |
| Produce a short Python maintenance utility. | The same unresolved suitability declaration could affect eligibility. | Text remains Chat-representable; no filesystem, test, or repository action follows. |
| Explain or transform a pasted code fragment. | The same unresolved suitability declaration could affect eligibility. | Text remains Chat-representable; the pasted fragment remains private request content. |

These uses may be valuable to operators, but usefulness or expected response
quality alone is not a routing criterion under the current accepted contracts.
Their request and result behavior remains that of well-formed Chat.

## Compatibility and coding-tool relationship

The accepted OpenAI-compatible surface is deliberately a small public-edge
translation into `chat`; it excludes tools, structured output, model selection,
and broad compatibility. No `code` compatibility exposure is needed or
recommended here.

An external coding tool could eventually use Home AI Cluster without a `code`
capability if its bounded caller behavior fits the existing Chat contract. A
future thin caller could translate a compatible textual coding request into
ordinary Chat messages. That is a caller-side integration question, not
evidence that the cluster needs a new capability. In particular, this does not
claim that Aider's full workflow fits the current compatibility subset or
authorize configuration, implementation, or compatibility expansion.

## Revised duplication test

The duplication question has two layers:

| Layer | Result |
| --- | --- |
| Request/result duplication | Yes. The same textual instruction and pasted source are representable through Chat and return free-form text. |
| Routing duplication | Underspecified. Removing `code` removes a possible operator-owned eligibility restriction to node-b, but accepted architecture does not say whether suitability alone makes that restriction a capability rather than preference or hidden model selection. |

Request/result duplication alone does not settle the question. Routing
non-duplication would be sufficient only if the project first accepts a bounded
operator-declared suitability capability as a valid capability kind.

## Next-step guidance

Do not write a `code` RFC yet. The smallest next architectural question is
whether Home AI Cluster permits a closed, explicitly operator-owned semantic
suitability capability whose request/result transport is shared with another
capability. That question must define the minimum truthfulness boundary,
relationship between node declaration and adapter reporting, caller expression
of the required capability, explainability, and the line between semantic
eligibility and hidden model preference. It must preserve the bans on automatic
model classification, model inventory, benchmarking, scoring, runtime-aware
routing, arbitrary labels, generic policy engines, and execution authority.

A later `code` proposal is appropriate only after that general question is
decided. A caller-side UX or coding-tool integration investigation may still be
useful under existing Chat boundaries, but does not resolve it.

## Primary outcome

Outcome C — Capability semantics are underspecified
