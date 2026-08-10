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
currently contains `chat`, `summarize`, and `classify`. A node is eligible only
when its static declaration and a registered adapter both provide the requested
capability; routing then applies existing local-first and declared-remote order
only among eligible candidates. Capability membership filters eligibility. It
does not score response quality, inspect models, probe runtimes, or select a
machine directly.

| Capability | Request and input semantics | Result semantics | Eligibility and adapter consequence |
| --- | --- | --- | --- |
| `chat` | A non-empty ordered sequence of plain-text system, user, and assistant messages in `ClusterRequest`. | Free-form normalized text with cluster attribution. | A chat-capable node and adapter are required; the adapter has an explicit `chat` operation. |
| `summarize` | One non-blank source text, bounded to 65,536 UTF-8 bytes, in `SummarizeRequest`. Caller-side file, standard-input, browser PDF, and other accepted conveniences normalize to this same text request rather than becoming capabilities. | Free-form normalized summary text with cluster attribution. | A summarize-capable node and adapter are required; the adapter has an explicit `summarize` operation. |
| `classify` | One bounded source text plus an ordered, finite, exact-unique operator label set in `ClassifyRequest`. | Exactly one supplied label, structurally validated by the cluster, with cluster attribution. | A classify-capable node and adapter are required; the adapter has an explicit `classify` operation and the cluster validates the proposed label. |

`summarize` and especially `classify` therefore add more than a caller
instruction. They introduce distinct normalized inputs that the cluster owns
and, for `classify`, an exact result invariant that it can enforce. The
adapters may use a runtime's chat transport internally, but that does not erase
the separate cluster request/result contract. Conversely, the accepted browser
PDF path is input acquisition before an unchanged `summarize` request; it is
not a PDF capability. This is a useful precedent for separating caller-side
convenience from cluster semantics.

### Capability admission test

A proposed capability earns a new name only when all of the following have a
concrete, cluster-owned answer:

1. It has a request semantic that is not merely Chat messages plus instructions.
2. It has a result semantic or invariant that is not merely free-form text.
3. An explicit, operator-owned declaration can truthfully make a node eligible
   or ineligible without referring to model or runtime identity, heuristics, or
   presumed quality.
4. It needs a distinct adapter responsibility rather than only a different
   prompt convention over Chat.
5. Removing the proposed name would lose an observable architectural behavior,
   not merely a caller UX label.

## Candidate `code` semantics and routing value

The narrow candidate accepts textual instructions and optional pasted textual
code, then returns textual code or an explanation/transformation. It has no
specified input field beyond text, no bounded output form beyond ordinary
response text, and no cluster-verifiable success property. Adding language,
filename, repository, model, runtime, execution permission, or similar fields
would broaden the problem without establishing a need.

This makes the candidate indistinguishable from a Chat request whose messages
ask for a Bash administration script, a Python maintenance utility, or an
explanation or transformation of pasted code. The current native Chat request
already carries plain-text messages and returns plain text through the existing
adapter and routing path.

The conceptual topology below is not yet an honest routing fact:

```text
node-a: chat
node-b: chat, code
```

For it to be meaningful, an operator would need an objective fact that makes
node-b able to satisfy the `code` request while node-a cannot. In the proposed
text-in/text-out scope, neither the request nor result establishes such a fact.
Declaring `code` from a model name, runtime name, benchmark, automatic model
inspection, or a quality judgment would violate the accepted capability and
engine-independence boundaries. An unverified operator declaration could state
the distinction, but would not make it truthful or explain what adapter-level
contract node-b supports.

The existing architecture already establishes that static capability ownership,
where valid, is operator-owned routing permission rather than runtime discovery
or health. It does not supply a semantic basis for a `code` declaration. A new
declaration mechanism is therefore not the missing piece; a distinct capability
contract is.

## Request and adapter implications

No new first request/result shape is justified by the candidate. A conceptual
`instruction -> generated text` request duplicates the free-form message and
content semantics of Chat. The existing adapters already translate Chat text to
their runtime chat operations. A `code` adapter method that differs only by its
prompt wording would be a prompt convention disguised as a capability.

This differs from the accepted `classify` adapter responsibility, which receives
labels and returns a proposal the cluster can validate exactly. It also differs
from `summarize`, whose bounded source-text normalization is owned outside a
conversation. No evidence shows that code text needs an engine-independent
adapter operation, result normalization rule, or closed transport variant that
Chat lacks.

## Operator usefulness

| Bounded use | Does `code` improve routing? | Current architectural fit |
| --- | --- | --- |
| Generate a small Bash administration script from explicit instructions. | No identified eligibility fact distinguishes it from text Chat. | Chat with caller-owned instructions. The script is output, not authority to execute it. |
| Produce a short Python maintenance utility. | No identified eligibility fact distinguishes it from text Chat. | Chat with caller-owned instructions. No filesystem, test, or repository action follows. |
| Explain or transform a pasted code fragment. | No identified eligibility fact distinguishes it from text Chat. | Chat with caller-owned instructions; the pasted fragment remains private request content under existing rules. |

These uses may be valuable to operators, but usefulness or expected response
quality alone is not a routing criterion. The cluster would behave exactly as
it does for a well-formed Chat request.

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

## Duplication test

Removing the word `code` and submitting the same instruction and pasted text
through Chat loses no identified cluster-owned request validation, result
invariant, adapter responsibility, routing rule, eligibility fact, privacy
boundary, or attribution behavior. It only loses a caller label or prompt
convention. Under the capability admission test, that is insufficient.

## Next-step guidance

No RFC is warranted next. A future investigation would need evidence of a
bounded, engine-independent code-specific request/result contract and an
objective operator-owned eligibility fact that cannot be expressed truthfully
as Chat. A caller-side UX or coding-tool integration investigation could be
useful later, provided it begins from existing Chat boundaries and does not
silently add execution authority or expand compatibility.

## Primary outcome

Outcome B — code should remain Chat usage
