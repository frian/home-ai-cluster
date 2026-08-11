# RFC-0067: Bounded Textual Code Assistance

Status: Draft

Date: 2026-08-11

Author: frian

## Summary

Home AI Cluster should add the closed `code` capability for bounded textual
code generation, transformation, and explanation. It reuses `ClusterRequest`
with explicit `capability=code`, the existing free-form `ClusterResult`, and
the existing Chat-like adapter execution and internal transport boundary.

`code` requests have an aggregate message-content limit of 65,536 UTF-8 bytes.
They require explicit caller and static-declaration opt-in; omission defaults
remain `chat` plus `summarize`. Generated code and commands are response text
only and confer no execution authority.

## Problem

RFC-0066 and the merged admission investigation establish that bounded textual
code assistance has independent semantic and hard-eligibility meaning. The
project needs the smallest concrete contract before implementation.

Keeping it as ordinary Chat cannot express:

```text
request requires code
node-a: chat       -> ineligible
node-b: chat, code -> may be eligible
```

Dedicated request/result, adapter, or transport shapes would be artificial
unless the concrete semantics require them.

## Goals

- Define `code` as a closed semantic requirement, not a quality label.
- Reuse the smallest truthful request, result, adapter, and transport shapes.
- Keep caller requirement and eligibility explicit and boolean.
- Bound input without token estimation or model-context discovery.
- Preserve routing, compatibility, privacy, and model-independent explanation.

## Non-goals

This RFC does not authorize filesystem or repository access or editing; shell,
command, or test execution; Git; tool or function calling; agents; autonomous
loops; multi-step planning/execution; indexing, RAG, embeddings, or web access.
It also does not authorize automatic intent or programming-language detection,
model/runtime inspection or selection, benchmarking, scoring, ranking, quality,
correctness, syntax-validity, executable-output, or security guarantees,
browser editor work, persistence, or OpenAI-compatible expansion.

## Proposal

### Semantic capability

`code` means bounded textual code generation, transformation, and explanation.
Examples include a small Bash administration script from explicit instructions,
a small Python maintenance utility, explanation of pasted source, correction or
transformation of pasted textual code, and textual source generation explicitly
requested by the caller.

It does not mean a better or preferred coding model, coding quality tier, smart
or reasoning model, model family, runtime feature, or machine class. An
operator's private reason for a declaration is not routing data.

### Request and result

`code` reuses:

```text
ClusterRequest
  messages: existing ordered plain-text messages
  capability: code
  constraints: existing constraints
```

The caller explicitly supplies `code`; HAC must not infer it from source text,
a language name, prompt appearance, or presumed intent. Existing message-role
and non-empty validation remains applicable.

For `code` only, all message contents together must be at most 65,536 UTF-8
bytes. Oversized input is not truncated and fails before routing, transport, or
runtime execution. This reuses the accepted bounded-text scale of Summarize and
Classify without token counting, language detection, model-context inspection,
a separate limit system, or a new request class. Current Chat has no equivalent
content-byte bound; this is the smallest validation needed to make “bounded”
contractual and changes neither Chat, Summarize, nor Classify validation.

`code` reuses free-form textual `ClusterResult`, including node attribution. It
does not promise parseable source, one code block, a language, syntax validity,
compilation, execution, explanation-free output, structured patches, diffs, or
file operations.

### Adapter, routing, and declarations

An adapter/composition may report `code` when it can accept the normalized
bounded textual request through its existing Chat-like method and promises no
more than textual assistance. No adapter method is required. Reporting is an
explicit composition claim, not model inspection, probing, benchmark evidence,
or a quality signal. Local routing retains its existing requirement for both
node declaration and matching adapter capability reporting.

`code` joins the closed ordinary executable capability vocabulary after
implementation. Ordinary executable surfaces and ordinary static declarations
accept only the names authorized by their accepted contracts. Membership is hard
eligibility only. Existing constraints, local-first selection among eligible
candidates, declared-remote order, availability, and pre-request fallback remain
unchanged. No ranking, weights, code-specialist bonus, scheduler, or model
preference is added.

Routing remains explainable only as:

```text
request required code
node-a did not declare code
node-b declared code
node-b was eligible
```

`code` is one additional accepted explicit static capability name for both
caller-local and declared-remote declarations. Explicit lists use the existing
non-empty, unique, closed-vocabulary validation. Omission defaults remain
exactly `chat` plus `summarize`; no existing node silently becomes code-capable.
Preflight stays local and network-free. Status remains unchanged and does not
become discovery, receiver verification, or runtime observation. RFC-0058 and
RFC-0059's operator-owned declaration boundary remains authoritative.

### Shared message representation and internal envelope

`ClusterRequest` remains the existing ordered-message request representation.
After implementation, the closed ordinary executable semantics using that
representation are `chat` and `code`; the embedded `capability` is their
semantic requirement, while ordered messages and free-form results are shared
representation mechanics.

This does not globally constrain `ClusterRequest.capability` to `chat | code`.
RFC-0034's accepted actual-request explanation surface may continue to construct
a `ClusterRequest` containing another non-empty capability name in order to
truthfully observe and report a no-selectable-candidate outcome. RFC-0067 does
not reinterpret or modify that diagnostic contract, and it does not create
arbitrary executable capabilities.

The existing `ChatInternalRequest` wire shape and `kind: "chat"` discriminator
are retained. For this RFC, `kind: "chat"` identifies the legacy
ordered-message envelope variant, not permission to overwrite or downgrade the
embedded request capability to `chat`. For ordinary remote execution it may
therefore carry only a valid embedded `ClusterRequest` requiring `chat` or
`code`; no other capability is admitted by this trust-boundary rule.
Implementation must update misleading Chat-only docstrings and internal
documentation without changing the wire shape.

### Local and remote execution

Local execution routes the bounded `ClusterRequest` through the selected
adapter's existing Chat-like method and returns `ClusterResult` attribution.
Remote execution reuses `ChatInternalRequest`, which carries the explicit
capability and messages in `ClusterRequest`. The receiver preserves the embedded
capability, revalidates the `code` aggregate bound at its trust boundary, routes
by that capability, and executes locally. It must never reinterpret
`kind: "chat"` as permission to downgrade `code` to Chat. It returns the
existing textual result. No transport variant, protocol family, capability
negotiation, or receiver discovery is needed.

Existing fallback boundaries are unchanged. A chat-only candidate is excluded
before selection; eligible runtime or transport failure retains its meaning.

### Native, browser, and compatibility surfaces

After separate implementation, `home-ai-cluster code --message TEXT` and
`hac code --message TEXT` are the initial native surfaces. They construct one
explicit bounded `ClusterRequest` with `capability=code` and reuse ordinary
native timeout, presentation, failure, and process-ownership conventions. They
do not add a `home-ai-cluster-code` console-script entry point.

A dedicated root subcommand is one clear semantic operation. Extending
`home-ai-cluster-chat` with arbitrary `--capability` would create a new generic
capability surface, so this RFC does not do that.

The loopback web client remains unchanged; a Code page is a later separate
convenience decision. No dashboard, editor, Monaco, syntax highlighting,
browser filesystem/repository access, or persistence is added.

OpenAI compatibility remains Chat-only: no `code` model, endpoint, alias, tool,
field, routing behavior, or automatic coding-prompt mapping is added.

### Privacy and failures

Code, pasted source, generated text, filenames, repository and language names,
and tool metadata remain private request or response content. Ordinary code
requests add no history, logs, metrics, database, or persistence. Existing
explicit history semantics do not expand.

Implementation preserves safe failures and conceptually distinguishes invalid
caller input, no eligible `code` capability, runtime unavailable, and execution
failure. It creates no code-specific public failure taxonomy and leaks no model,
runtime, or private topology details.

## Rationale

This realizes RFC-0066's admitted semantic and eligibility distinction without
manufacturing symmetry. `code` shares free-form text input/output and transport
with Chat, but explicit membership independently excludes nodes. The aggregate
bound keeps its first contract finite and implementation-visible. Explicit
opt-in preserves compatibility and truthfulness.

## Alternatives considered

### Keep code as ordinary Chat only

Rejected: it cannot express the accepted chat-only/code-capable eligibility
distinction.

### Reuse Chat-like request, result, and execution mechanics

Accepted: the existing shapes represent the text operation; only the concrete
bound and explicit capability support are needed.

### Introduce CodeRequest, CodeResult, or a dedicated adapter method

Rejected: the candidate needs no new fields, normalization, result invariant, or
adapter behavior. These abstractions would exist only for symmetry.

### Expose model preference, infer intent, or add tools/execution

Rejected: preference is not a semantic requirement; inference violates explicit
requirement; and authority has distinct safety and privacy boundaries.

### Expose code through OpenAI compatibility now

Rejected: the accepted compatibility edge translates only Chat and no concrete
integration need requires expansion.

## Trade-offs

The contract adds one explicit name, opt-in declaration, and aggregate byte
validation. That cost preserves a genuine routing boundary without model
selection or a generic framework. The 65,536-byte limit may reject some
Chat-representable requests, but only for this bounded category; expansion needs
a new decision.

## Impact and implementation boundary

After acceptance, a separate implementation PR may make only changes needed for
this vertical slice: closed capability validation and composition reporting;
aggregate validation at caller and receiver boundaries; existing routing and
execution reuse; static local/remote declaration support; the native command;
focused tests; and privacy-safe proof material.

It must preserve existing Chat, Summarize, Classify, ordering, fallback, status,
OpenAI compatibility, browser, and privacy behavior. It must not add request or
result classes, an adapter method, transport variant, discovery, verification,
tools, execution authority, persistence, or roadmap change.

## Proof expectations

A later proof must show explicit accepted `code`, oversized aggregate rejection,
chat-only exclusion and code-capable selection, capability-only explanation,
local and real static remote textual assistance, unchanged local-first and
fallback behavior, text-only results with no authority, and unchanged existing
capabilities, compatibility, and privacy behavior. Retained evidence must not
contain real prompts, generated code, private addresses, model/runtime IDs,
machine names, credentials, or private paths.

## Open questions

None within this contract. Browser or compatibility exposure requires a later
independent, bounded decision.

## Decision

Pending.
