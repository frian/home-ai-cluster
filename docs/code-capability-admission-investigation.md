# Code capability admission investigation

## Status

Investigation only. This document applies accepted
[RFC-0066](../RFC/RFC-0066-capability-admission-semantics.md); it does not
reconsider that RFC, authorize `code`, or change architecture or behavior.

## Question

Does the following bounded semantic category satisfy RFC-0066's capability
admission test?

> bounded textual code generation, transformation, and explanation

Representative operations are generating a small Bash administration script or
Python maintenance utility from explicit textual instructions, explaining a
pasted source fragment, correcting or transforming a bounded pasted fragment,
or producing source text from an explicit caller request.

The candidate is textual assistance only. Generated code and commands are
output text only; they confer no authority to execute them.

## Scope and exclusions

The candidate does not include filesystem or repository access, repository
editing, shell or command execution, test execution, Git operations, tool
calling, agents, planning/execution loops, indexing, RAG, embeddings, automatic
language or intent detection, model or runtime selection or inspection,
benchmarking, scoring, ranking, or correctness, safety, executability, syntax,
or test guarantees.

It does not propose an OpenAI-compatible change. The accepted compatibility
surface remains Chat-only: it does not expose `code` through
`/v1/chat/completions`, model identifiers, tools, model discovery, or additional
fields.

## Relevant accepted architecture

RFC-0066 defines a capability as a closed, project-defined semantic requirement
that a caller explicitly requires and that may determine hard node eligibility.
It expressly distinguishes that from a model, runtime, machine, vendor, UI
category, quality claim, ranking preference, or arbitrary operator tag. A
separate request/result representation, adapter method, or runtime transport is
required only where the concrete semantic contract needs one; it is not an
admission prerequisite by itself.

The current implementation provides useful, but non-authorizing, evidence:

- `ClusterRequest` contains an explicit `Capability`, while `SummarizeRequest`
  and `ClassifyRequest` expose fixed capabilities. The current static vocabulary
  is closed to `chat`, `summarize`, and `classify`.
- Routing filters node candidates by the requested capability. For local
  execution it also requires a matching adapter capability. Existing ordering is
  local-first, then declared remote order; membership does not rank candidates.
- RFC-0058 and RFC-0059 define static remote and caller-local declarations as
  operator-owned routing permissions. They neither probe nor verify a remote
  runtime, model, or receiver implementation.
- The current Chat path carries text to a chat adapter and returns normalized
  text. The accepted compatibility translator fixes its capability to `chat`.

These are observations of the current architecture, not authorization to add a
new name or alter any of those contracts.

## Applying the RFC-0066 admission criteria

### 1. Meaning

`code` can have the following closed, bounded project-defined meaning:

```text
the request requires bounded textual code generation, transformation, or
explanation
```

That statement describes the requested kind of textual assistance, not a model,
runtime, machine, vendor, UI category, prompt preset, or quality assertion. It
can remain meaningful even if two nodes use the same runtime, if their hardware
changes, or if the operator never discloses why one node is declared capable.

The necessary boundary is strict:

```text
code = request requires bounded textual code assistance
```

may be a capability, whereas:

```text
code = use the model the operator considers better at coding
```

is a preference or quality claim and fails RFC-0066. The latter has no stable
semantic promise to the caller and would hide model-aware selection behind a
label. The former can be kept on the capability side only by defining its
textual-assistance boundary explicitly and excluding all execution authority and
quality guarantees listed above.

**Finding:** the bounded category has a semantic meaning independent of the
operator's private reason for selecting a node.

### 2. Requirement

The smallest conceptually valid requirement is an explicit caller assertion that
the request requires the accepted `code` capability. The cluster must not infer
that requirement because a prompt contains source code, mentions a programming
language, or appears difficult or coding-related.

Existing `ClusterRequest(messages=..., capability=...)` demonstrates that a
free-form textual request can already carry an explicit capability requirement.
This does not choose a public endpoint, CLI, internal-envelope, or new request
class. Per RFC-0066, a later concrete RFC may decide that an existing normalized
text request is sufficient, unless a new validation, normalization, result
invariant, field, or behavior is actually needed.

**Finding:** an explicit requirement is conceptually available without
automatic intent detection or authority expansion.

### 3. Eligibility

The motivating topology creates a real boolean routing distinction:

```text
request explicitly requires code

node-a: chat
  -> node-a is ineligible

node-b: chat, code
  -> node-b may be eligible under existing constraints and ordering
```

Removing `code` would remove the operator-controlled ability to exclude
`node-a` for this bounded semantic requirement. That is routing
non-duplication, even though the textual input and output are also representable
through Chat. The existing router's capability-membership filter and
local-first/declared-remote order fit this hard eligibility use; they do not
need to rank, score, weight, or prefer either node.

The declaration is not an assertion that HAC found node-b's composition better
at coding. It says only that the operator permits node-b to be eligible for the
closed `code` requirement. As RFC-0058 and RFC-0059 establish for static
declarations, that is a caller-owned routing fact rather than runtime discovery
or a comparative recommendation.

**Finding:** the distinction supplies a material hard eligibility boundary, not
merely a quality preference.

### 4. Execution truth

The current chat-like execution composition can accept the underlying bounded
text operation and return textual output. Sharing that transport is not a
failure under RFC-0066: the operation does not itself need filesystem access,
repository awareness, shell execution, Git, testing, tools, agents, runtime
features, or a correctness or executability guarantee.

This finding is deliberately limited. Current production code supports only the
closed `chat`, `summarize`, and `classify` contracts; it does not currently
declare, route, transport, or execute `code`. A future declaration could be
truthful only if the receiving composition can accept the normalized textual
operation and the concrete contract promises no more than textual assistance.
It must not turn generated text into execution authority or infer adapter
support from a model/runtime identity.

Whether a concrete `code` RFC needs a dedicated adapter method, internal
transport variant, or request/result representation is a later smallest-boundary
decision. It must not be invented merely to justify a label.

**Finding:** sharing the Chat-like textual transport can be truthful for the
bounded operation, provided the future contract retains the stated exclusions.

### 5. Explanation and stability

The route can be explained entirely in accepted capability terms:

```text
The request required the code capability.
node-a did not declare code.
node-b declared code.
node-b was eligible.
```

No part of that account needs a model name, runtime name, benchmark, quality
claim, or operator preference. The operator may privately know why node-b was
declared, but that reason is outside the cluster-facing explanation.

The name can remain stable because its meaning is bounded to textual code
generation, transformation, and explanation and the project, rather than an
operator, would own the closed vocabulary. Broadening it later into coding
agents, tools, repositories, execution, or arbitrary labels would be a
different proposal and would need separate evaluation.

**Finding:** the category supports a closed, stable vocabulary entry and a
model-independent explanation.

## Request/result duplication and routing duplication

The earlier [bounded code capability investigation](bounded-code-capability-investigation.md)
correctly separated two questions:

| Layer | Result |
| --- | --- |
| Request/result duplication | Yes. Existing free-form text messages can carry these instructions and pasted fragments, and Chat returns free-form text. |
| Routing duplication | No, if `code` is accepted. The explicit requirement can exclude a chat-only node from the bounded semantic operation. |

The first fact does not disqualify the candidate. RFC-0066 explicitly rejects
making a distinct request class, result class, adapter method, or runtime
transport a prerequisite for a valid semantic eligibility distinction. The
second fact supplies the independent routing consequence required here.

## Compatibility boundary

This conclusion does not propose a change to the existing OpenAI-compatible
Chat subset. A future concrete RFC must decide any caller surface separately;
it must not expose `code` through `/v1/chat/completions`, model identifiers,
tools, model discovery, or extra compatibility fields merely because the
underlying operation is text.

## Primary outcome

**Outcome B — The bounded `code` category appears to satisfy RFC-0066 and a
small concrete capability RFC is warranted.**

It passes the five admission criteria as a closed explicit textual semantic
requirement with a real boolean eligibility consequence, a truthful text-only
execution boundary, and a model-independent explanation. This investigation
does not authorize `code` or implementation. A follow-up RFC must define only
the concrete capability contract and its smallest necessary caller requirement,
request/result, adapter/composition, static-declaration, routing, and
compatibility implications. It must separately preserve every exclusion in this
investigation and RFC-0066.
