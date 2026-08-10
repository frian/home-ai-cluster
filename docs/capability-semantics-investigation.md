# Capability semantics investigation

## Status

Investigation only. This document proposes no architecture or behavior change.

## Question

What makes a capability valid in Home AI Cluster? In particular, may a
capability be a bounded, explicit operator-declared semantic suitability promise
when its request/result transport is shared with another capability, or must
every capability be a distinct cluster-owned request/result and adapter
contract?

This question arose from the bounded `code` investigation but is not a decision
about `code`.

## What the repository demonstrates

The accepted architecture consistently makes capabilities cluster-facing
semantic requirements rather than model, runtime, machine, or vendor names.
The current implementation reflects that shape: a request has a requested
capability; routing filters nodes by that capability; local execution also
requires a matching registered adapter; and static declared-remote eligibility
uses caller-owned declarations without probing a remote runtime.

| Capability | Semantic meaning and request | Result and invariant | Adapter and transport | Declaration and routing |
| --- | --- | --- | --- | --- |
| `chat` | Ordered plain-text conversation messages. | Free-form normalized text with cluster attribution. | Named `chat` responsibility; runtime chat transport. | Declared `chat` membership permits eligibility for chat requests. |
| `summarize` | One bounded, non-blank source text. Caller-side files and browser-local PDF extraction normalize to this request instead of becoming capabilities. | Free-form normalized summary text with cluster attribution. | Named `summarize` responsibility; existing adapters may use a runtime chat transport. | Declared `summarize` membership permits eligibility for summarize requests. |
| `classify` | One bounded source text plus a finite exact operator label set. | Exactly one supplied label; the cluster validates exact membership. | Named `classify` responsibility; adapters may use a runtime chat transport with adapter-owned mechanics. | Declared `classify` membership permits eligibility for classification requests. |

These examples establish several facts:

- A capability can have a distinct semantic request/result contract.
- A distinct capability does not require a distinct runtime transport.
- Adapters are the engine-specific execution boundary; the core does not route
  by model or runtime identity.
- Existing static capability declarations are explicit operator-owned routing
  facts. They are not runtime/model discovery, health observation, or remote
  verification.
- Static preflight projects declaration data without contacting runtimes or
  remotes; health and availability remain separate concerns.
- The ordinary static vocabulary is closed and RFC-owned. Existing RFCs reject
  arbitrary capability strings and preserve omission defaults deliberately.

They do **not** establish that every possible capability must use a separate
request class, result class, adapter method, or transport. Nor do they establish
that every operator suitability judgment is an acceptable capability. All
existing accepted names happen to be contract-backed, but that is evidence of
the current set, not a stated universal admission rule.

## The candidate models

### Contract-backed capability

Under this model, a capability exists only when the cluster defines a distinct
semantic request/result contract and adapters explicitly implement that
responsibility. `summarize` and `classify` directly fit this model.

It provides a clear meaning, enforceable request/result boundaries, predictable
interoperability, and simple explanations. It can also over-couple capability
identity to an API shape: a new request class would be artificial if the real
difference is only which nodes are permitted to receive a shared textual
operation.

### Operator-declared semantic suitability capability

Under this model, a capability may be a closed project-defined semantic task
category. An operator explicitly declares a node suitable for it, and the
declaration controls hard eligibility even when the normalized request and
result are shared with another capability.

This model is compatible with static ownership only if HAC does not infer the
declaration from model names, runtime brands, metadata, benchmarks, hardware,
or quality scores. An operator may know why a node is suitable without that
reason becoming part of the cluster-facing domain. In that sense, the following
is not automatically model routing:

```text
request requires semantic capability X
  -> node-a did not declare X
  -> node-b declared X
  -> node-b is eligible
```

However, it becomes hidden model preference when X means only “the operator
likes this model better” or “this node is good/smart/fast.” Those are
comparative or qualitative judgments, not stable boolean semantic requirements.
They would require ranking, scoring, benchmarks, or a policy system that the
accepted architecture does not own.

### Combination

The architecture already combines project and operator ownership in practice:
the project owns the semantic vocabulary and execution contracts, while an
operator owns the static eligibility declaration. What remains undecided is
whether the project may define a closed semantic suitability category whose
node declaration is meaningful without adding a separate request/result
representation.

## Truthfulness and static trust

Static declarations are neither mechanically verified facts nor arbitrary
labels. They are caller-owned configuration claims that limit what the router
may consider. This is a deliberately weaker, but useful, notion of truthfulness:
the cluster does not prove the claim, yet the claim has a stable project-defined
meaning, is explicit, and has a deterministic eligibility consequence.

Mechanical verification would require discovery, probes, model inventory, or
runtime-specific interpretation; none is authorized or needed for the present
static architecture. Operator ownership alone is insufficient, though, because
an unbounded label would make explanations and interoperability meaningless.

For a static declaration to be truthful enough for routing, the investigation
finds that it must at least be:

1. a member of a closed, project-defined vocabulary with a bounded semantic
   meaning independent of model and runtime identity;
2. explicitly declared by the operator who owns the relevant routing topology;
3. a hard eligibility claim, not a comparative recommendation, score, or
   implicit quality assertion;
4. compatible with the node's actual execution composition: its adapter can
   accept the normalized operation, and the declaration does not promise tools,
   authority, result guarantees, or behavior the composition cannot provide;
   and
5. explainable from request requirement and declaration membership alone,
   without exposing hidden model/runtime reasoning.

These conditions distinguish a semantic eligibility promise from dynamic
verification. They also show the open question: when the operation is shared,
what project-defined semantic meaning makes the fourth condition more than a
quality preference?

## Capability, constraint, and preference

The current `RequestConstraints` already separates at least some execution
conditions from capability: `local_only` is a caller privacy boundary, while
the requested capability describes what the request needs. The architecture
also contains future-looking constraints such as minimum context size and fast
response preference, but does not make them accepted capability semantics.

The useful distinction is:

| Concept | Architectural role | Examples for analysis only |
| --- | --- | --- |
| Capability | A boolean semantic requirement that determines whether a node is eligible to handle the request. | Chat, vision, embeddings, or a bounded semantic specialization if accepted. |
| Constraint | A caller condition on where or how execution may occur. | Local-only, a latency bound, or a context requirement. |
| Preference / quality | A comparative recommendation among otherwise eligible candidates. | Better reasoning, higher quality, faster, smarter, or a preferred model. |

The existing static router uses boolean membership and deterministic order; it
does not rank candidates. A qualitative label cannot safely become a boolean
capability merely by being written in a declaration. A bounded semantic
category might be eligible for boolean treatment, but this requires a defined
meaning distinct from “better.” This investigation does not classify any
individual proposed category.

## Adapter relationship

An adapter must remain the engine-specific execution boundary. Current
contract-backed capabilities have named adapter responsibilities, and local
routing requires both node declaration and adapter capability membership. A
declared remote is selected from its caller-owned declaration; its local
receiving composition is not probed by the caller.

No accepted RFC answers all of these general questions:

- Must every capability have a dedicated adapter method, or can several
  capabilities share one normalized adapter operation?
- If transport is shared, what must adapter support mean beyond “can send the
  same text to the runtime”?
- When project semantic meaning and operator suitability differ, which layer
  owns each assertion?
- How should a receiving boundary preserve that meaning without capability
  negotiation or runtime discovery?

The answer must not be a generic adapter API, plugin system, or dynamic
capability protocol. It need only establish the minimum ownership semantics for
a future concrete proposal.

## Caller requirement and explainability

A routing capability matters only when the request can explicitly require it.
The core model can represent a named requested capability, while `summarize`
and `classify` fix theirs through dedicated request types. Existing public and
compatibility contracts do not authorize arbitrary caller-selected capabilities,
and the OpenAI-compatible surface intentionally translates only to `chat`.
Automatic intent classification would violate the project's explicit-boundary
approach.

For a shared-shape capability, a future decision must therefore say whether a
caller can make an existing request require a different accepted capability, or
whether every such semantic requirement must be expressed by a distinct request
contract. This is an architecture question, not an implementation gap.

Either accepted form must remain explainable. A valid explanation can state:

```text
request required capability X
node-a did not declare X
node-b declared X
node-b was eligible
```

It must not say, imply, or depend on “HAC judged node-b's model better.”

## Reusable admission test

A future capability proposal should answer all five questions before an RFC can
be accepted:

1. **Meaning:** Is this a closed, bounded semantic requirement rather than a
   model/runtime name, UI category, quality claim, or preference?
2. **Requirement:** Can the caller require it explicitly, without automatic
   intent detection or silently changing the request's authority?
3. **Eligibility:** Does explicit operator-owned membership create a real hard
   eligibility difference, rather than ranking otherwise eligible nodes?
4. **Execution truth:** Can the relevant adapter/composition accept the
   normalized operation without the capability promising tools, execution,
   result guarantees, or runtime behavior it does not provide?
5. **Explanation and stability:** Can routing explain the requirement and
   membership without model/runtime identity, while the vocabulary remains
   closed and stable enough for interoperability?

A distinct request/result contract is strong evidence for these answers and is
required whenever the capability needs new cluster-owned validation or result
invariants. It is not yet established as a universal prerequisite for every
semantic eligibility capability.

## Relationship to code

The merged bounded-code investigation properly found that text-only code
assistance duplicates Chat at the request/result layer but may have a routing
non-duplication layer. This general investigation does not resolve whether a
future `code` category passes the admission test. It shows why that question
must follow, rather than create, a general capability-semantics decision.

## Next step

A small general capability-semantics RFC is warranted before any further
capability proposal that relies on operator-declared semantic suitability rather
than a distinct request/result contract. It should decide only the ownership and
admission rule above: closed vocabulary, semantic meaning, explicit caller
requirement, operator declaration, adapter/composition truthfulness,
explainability, and the exclusion of quality ranking or hidden model selection.

It must not authorize `code`, arbitrary tags, automatic model classification,
model inventories, benchmarks, scoring, schedulers, policy engines, dynamic
discovery, capability negotiation, databases, plugins, dashboards, or execution
authority.

## Primary outcome

Outcome B — A small general capability-semantics RFC is warranted
