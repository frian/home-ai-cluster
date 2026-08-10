# RFC-0066: Capability Admission Semantics

Status: Draft

Date: 2026-08-10

Author: frian

## Summary

Home AI Cluster should admit a first-class capability only when it is a closed,
project-defined semantic requirement that a caller explicitly requires and that
can affect hard node eligibility.

A capability is neither a model, runtime, machine, vendor, UI category, quality
claim, ranking preference, nor arbitrary operator tag. It may require a distinct
cluster-owned request/result contract, but a distinct runtime transport or a
new request/result representation is not required solely to justify a routing
label. When an existing representation is shared, the semantic requirement and
its support still need to be explicit, truthful, and explainable.

Static capability declarations remain operator-owned routing facts. The cluster
does not discover, inspect, benchmark, or mechanically verify an operator's
reason for a declaration. An operator's knowledge of a local composition may
inform a declaration without model or runtime identity becoming a routing input.

This RFC defines an admission rule only. It authorizes no new capability name,
request, adapter method, declaration syntax, route, CLI command, browser UI,
compatibility behavior, or implementation.

## Problem

Accepted architecture is capability-centered and treats current static
declarations as explicit operator-owned eligibility data. Existing capabilities
also happen to have defined cluster request/result contracts and named adapter
responsibilities. They show that separate cluster semantics can share a runtime
chat transport, but they do not state the general rule for admitting future
semantic categories.

Without that rule, a future proposal could create a new request type merely to
manufacture a routing label, or could use an undefined suitability label to hide
model preference. Either outcome would make routing less understandable and
would drift toward model-aware or quality-aware selection.

The project needs the smallest general decision that preserves explicit static
ownership while distinguishing valid semantic eligibility from arbitrary tags,
constraints, and preferences.

## Goals

- Define the general conditions for admitting a capability.
- Preserve closed, project-owned capability vocabulary.
- Preserve explicit caller requirement and boolean hard eligibility.
- Define truthful-enough static operator declaration without dynamic discovery
  or model/runtime inspection.
- Clarify that capability identity, request/result shape, and runtime transport
  are related but not identical concerns.
- Preserve model-independent routing explanations.
- Keep existing capabilities and behavior unchanged.

## Non-goals

This RFC does not authorize or define:

- `code` or any other new capability name;
- arbitrary user-defined capability tags;
- automatic intent detection or semantic request classification;
- model metadata, inventories, brands, benchmarks, or runtime-aware routing;
- quality scoring, ranking, weights, node scoring, or preference policy;
- dynamic discovery, capability negotiation, or runtime probing;
- schedulers, policy engines, generic adapter/plugin systems, persistence,
  databases, dashboards, tools, agents, or execution authority;
- a universal request encoding or a new adapter API; or
- OpenAI-compatible API expansion.

## Proposal

### Capability definition

A Home AI Cluster capability is a closed, project-defined semantic requirement
that a caller may explicitly require and that may determine whether a node is
eligible to execute the request.

A capability is not:

- a model, runtime, machine, vendor, or hardware identity;
- a UI grouping or prompt preset;
- an asserted quality such as better, smarter, stronger, faster, or high
  quality;
- a comparative preference among otherwise eligible nodes; or
- an arbitrary operator label.

Its meaning must be understandable without knowing any particular model or
runtime. An accepted capability name denotes the semantic need, not an
explanation of why an operator considers one node suitable.

### Closed vocabulary

Ordinary capability names remain a closed, project-owned vocabulary. A new name
requires an accepted RFC or another explicit accepted architectural decision.
Operator declarations may select among accepted names, but cannot create names.

This keeps request meaning, eligibility, interoperability, and routing
explanations stable. It does not create an extensible tag system or generic
capability registry.

### Explicit requirement and hard eligibility

A capability affects routing only when the caller explicitly requires it. The
concrete request representation is owned by the RFC for that capability: it may
be a dedicated request contract, an existing normalized request explicitly
requiring another accepted capability, or another bounded explicit form.

Home AI Cluster must not infer a capability from text, request difficulty,
presumed intent, model identity, or runtime metadata.

Capability membership is boolean eligibility:

```text
request requires capability X
node does not declare/support X
  -> node is ineligible

request requires capability X
node declares/supports X
  -> node may be eligible under existing constraints and routing rules
```

Membership does not rank, score, weight, prefer, or claim that one eligible
node is better than another. Existing local-first order, declared-remote order,
and fallback semantics remain authoritative.

### Truthful static declaration

Where the architecture already makes topology and capabilities static and
operator-owned, a capability declaration is a caller-owned routing claim: it
states what the router may consider eligible. It is not runtime discovery,
health observation, model inspection, benchmark evidence, or a remote
verification protocol.

Static trust is intentional. The cluster need not mechanically prove why an
operator declared a node capable. A model or runtime composition may be the
operator's reason without becoming cluster-facing routing data.

A declaration is truthful enough for static routing only when all of the
following are true:

1. the name is an accepted closed capability with a bounded project-defined
   semantic meaning;
2. the declaration is explicit and made by the operator who owns the relevant
   routing topology;
3. the declaration represents a hard semantic eligibility claim, not a quality
   preference or comparative recommendation;
4. the node's execution composition can accept the normalized underlying
   operation, and the declaration does not promise tools, authority, output
   guarantees, or behavior that composition cannot provide; and
5. routing can explain the requirement and eligibility through capability
   membership alone, without exposing model/runtime reasoning.

This condition does not add probing or negotiation. Existing local composition
and adapter checks, caller-owned static declarations, receiving-boundary
validation, and trust separation retain their established meanings.

### Request/result and adapter relationship

A capability needs a distinct cluster-owned request/result contract when its
semantic meaning requires new validation, normalization, result invariants,
fields, or behavior that an existing request form cannot represent. Creating a
new request class alone does not establish a capability; the semantic admission
test comes first.

Conversely, a distinct runtime transport is not required. Existing accepted
capabilities demonstrate that adapters may map different cluster semantics to a
runtime chat transport. Several accepted cluster capabilities may share an
underlying adapter/runtime operation only when each passes this RFC's admission
rule and the composition support remains truthful for each semantic meaning.

This RFC does not require one adapter method per capability and does not define
a generic adapter interface. A future concrete capability RFC must decide the
smallest compatible request, result, adapter, and transport boundary it needs.

### Capability, constraint, and preference

Capabilities describe what the request semantically needs. Constraints describe
how or where a caller permits execution. For example, existing `local_only` is
a caller privacy boundary, not a quality capability.

Preferences compare otherwise eligible candidates. They are not supported by
the current boolean capability model and are not introduced here. A proposed
name whose practical meaning is preferred model, better reasoning, high quality,
faster, stronger, or smarter is a preference or quality claim, not a capability.

### Explainability

A valid capability must permit an explanation in cluster-facing terms:

```text
request required capability X
node-a did not declare/support X
node-b declared/supported X
node-b was eligible
```

The explanation must not depend on or imply that Home AI Cluster inspected a
model, runtime, benchmark, or quality signal. The operator's private reason for
a declaration remains outside routing explanation unless a future architecture
decision explicitly changes that boundary.

### Admission test

A future capability proposal may be accepted only when it answers all five
questions clearly:

1. **Meaning:** Is it a closed, bounded semantic requirement independent of
   model/runtime identity, UI category, quality, and preference?
2. **Requirement:** Can a caller require it explicitly without automatic intent
   detection or implicit authority expansion?
3. **Eligibility:** Does membership create a real hard eligibility difference
   rather than rank otherwise eligible nodes?
4. **Execution truth:** Can the relevant adapter/composition accept the
   normalized operation without promising unavailable tools, execution,
   guarantees, or runtime behavior?
5. **Explanation and stability:** Can routing explain membership without
   model/runtime identity while the accepted vocabulary remains closed and
   stable?

## Existing capabilities and compatibility

`chat`, `summarize`, and `classify` remain valid existing capabilities. This
RFC does not reinterpret their request contracts, result semantics, adapters,
static declarations, or routing behavior, and requires no migration.

The existing static declaration vocabulary and omission defaults remain
unchanged. Status, preflight, health, fallback, local composition, ordinary
request access, the loopback browser, and the bounded OpenAI-compatible Chat
subset remain unchanged. The compatibility surface continues to translate only
its accepted request subset into `chat`.

## Rationale

The proposal preserves the project's central question—what does this request
need?—without allowing the answer to become a model name or opaque quality
judgment. It respects static operator ownership: the operator may make a
bounded routing claim without requiring dynamic inspection, while the project
still owns the meaning and vocabulary that make the claim intelligible.

Separating semantic capability from constraints and preferences prevents the
boolean eligibility model from becoming a scheduler or model-selection policy.
Requiring explicit caller requirement prevents silent request classification.
Requiring truthful execution support prevents a routing label from granting
authority or promising behavior not present in the node composition.

This is smaller than prescribing one request representation or adapter API. It
lets future concrete RFCs use existing representations when appropriate, but
requires them to demonstrate a semantic and routing reason before doing so.

## Alternatives considered

### Require a distinct request/result and adapter method for every capability

Rejected. It would make API shape the sole admission test and could require a
new request solely to label a routing distinction. Existing semantics already
show that runtime transport can be shared.

### Treat every operator-declared label as a capability

Rejected. Unbounded labels would make eligibility opaque and invite hidden
model preference, arbitrary tags, and a policy system without shared meaning.

### Infer capabilities from models, runtimes, or benchmarks

Rejected. This would make routing model- or runtime-aware, introduce dynamic
quality claims, and violate engine independence and explicit operator control.

### Treat semantic suitability as preference or ranking

Rejected. The present model supports hard eligibility and deterministic order,
not comparative candidate quality. Ranking needs separate evidence and an RFC.

### Defer all general guidance until a concrete capability is proposed

Rejected. The completed investigations show a recurring ownership question that
cannot be resolved consistently from current examples alone.

## Trade-offs

The admission test makes adding a capability slower and requires future RFCs to
state their semantic meaning and ownership explicitly. That cost is deliberate:
closed vocabulary and understandable explanations are more valuable than easy
labels.

Static declarations may still be wrong because they are not mechanically
verified. The project accepts that limited operator-owned trust rather than
adding discovery or runtime inspection. The rule constrains the claim's meaning
and execution boundary without converting static routing into a dynamic
verification system.

## Impact

If accepted, this RFC becomes an architectural rule for evaluating future
capability proposals. It authorizes no implementation by itself.

A future concrete capability RFC may cite this admission test and must define
its own request/result representation where needed, caller requirement form,
adapter/composition support, static declaration implications, routing proof,
and compatibility boundary. A later investigation may test whether `code` or
another candidate satisfies this rule; this RFC does not authorize that name or
any behavior.

## Open questions

None within this admission-semantics scope.

Future capability RFCs remain responsible for their own concrete semantics and
implementation evidence.

## Decision

Pending.
