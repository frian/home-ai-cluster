# RFC-0119: Capability-Coherent Adapter Execution Contracts

Status: Draft

Date: 2026-09-12

Author: frian

## Summary

Home AI Cluster should separate the common adapter surface from the distinct execution contracts that concrete adapters support.

Every adapter participating in HAC composition continues to expose common concerns conceptually equivalent to:

```text
stable adapter name
adapter-wide health
explicit execution-capability support
```

Distinct execution forms remain explicit contracts. One concrete adapter may satisfy one or several such contracts, and an adapter need not implement operations for capabilities it does not support.

For purposes of this RFC, existing accepted execution behavior is grouped into the following execution shapes:

```text
chat
code
    -> Chat execution shape

summarize
    -> Summarize execution shape

classify
    -> Classify execution shape
```

Capabilities and execution shapes are different concepts. Multiple capabilities may share one execution shape.

Adapter capability support remains explicit semantic truth. HAC must not infer capabilities from method presence, class identity, runtime identity, model identity, endpoint behavior, probing, or discovery.

For every capability positively claimed by an adapter instance, that adapter must have the execution contract HAC requires for the capability. A contradictory claim is invalid executable composition, not runtime unavailability, routing ineligibility, or an ordinary request-time unsupported-operation failure.

This execution-contract coherence must be established fail-fast before the adapter enters request-executable use.

Generic `AdapterRegistry` membership alone does not establish executable admission. RFC-0108 local binding validation remains a separate proof of assigned capability subset and non-overlap.

Routing remains capability-centered and operation-blind. Normalized request shape determines the exact execution path after routing. Result validity, runtime health, and execution availability remain separate concerns.

This RFC refines RFC-0003's deliberately small runtime-adapter boundary using evidence that distinct runtime adapters need not implement the same execution-operation suite. It does not accept any new capability.

## Context

RFC-0003 established the first runtime-adapter boundary and deliberately rejected a premature generic:

```text
execute(request)
```

abstraction.

That decision remains valid.

As HAC gained bounded capabilities, the current concrete `RuntimeAdapter` interface accumulated two kinds of responsibility:

```text
common adapter concerns:
    name
    health()
    capabilities()

execution operations:
    chat()
    summarize()
    classify()
```

This remained practical while the current concrete runtime adapters happened to implement the same textual operation suite.

The architecture now has evidence that this need not remain true. Investigation of a possible bounded future image-generation capability produced the first concrete case where a legitimate adapter could require a new non-textual execution form without implementing Chat, Summarize, or Classify.

That investigation does not accept image generation. It only exposes a general adapter-interface seam.

## Problem

Being a HAC adapter and implementing every HAC execution operation are different responsibilities.

Requiring every adapter to implement every operation would eventually force unrelated or fake methods onto adapters that do not support those capabilities.

The reverse is also invalid: an adapter must not positively claim a capability when HAC has no valid execution contract through which that adapter can perform it.

The architecture must therefore preserve three distinct facts:

```text
adapter execution support
    -> what this configured adapter instance truthfully says it can execute

local capability binding
    -> which supported capabilities this process assigns to this adapter

caller/static routing permission
    -> which capabilities the caller permits for routing
```

These facts may narrow one another, but they are not interchangeable.

## Goals

This RFC aims to:

* preserve one common adapter surface;
* keep genuinely distinct execution shapes as explicit contracts;
* permit one concrete adapter to satisfy one or several execution contracts;
* preserve explicit adapter capability-support claims;
* keep capability semantics independent of implementation mechanics;
* make HAC own the accepted capability-to-execution-shape relationship;
* require every positive adapter capability claim to have its required execution contract;
* establish that coherence before request-executable use;
* preserve RFC-0108 binding validation as a separate ownership proof;
* preserve equal adapter-support truth for binding and legacy non-binding execution paths;
* keep routing operation-blind;
* keep normalized request shape responsible for exact execution dispatch;
* keep result validation, runtime health, and execution availability separate.

## Non-goals

This RFC does not:

* accept image generation or any other new capability;
* define an image request, result, operation, representation, format, or limit;
* define binary, blob, attachment, or generic media semantics;
* change remote transport or HTTP behavior;
* add or change UI;
* add filesystem authority;
* add runtime or model discovery;
* infer capabilities from model metadata or runtime probing;
* add automatic capability detection;
* add dynamic adapter loading;
* add a plugin framework;
* add handler or operation registries;
* add per-capability adapter registries;
* add a generic `execute()` method;
* add `AnyRequest`, `AnyResult`, or equivalent generic execution objects;
* add per-operation health;
* change execution availability;
* change routing, ranking, scheduling, load balancing, or fallback;
* change RFC-0108 ownership semantics;
* retire or redesign the legacy non-binding execution path;
* choose a Python implementation mechanism;
* require a static type checker;
* choose `Protocol`, ABC, inheritance, decorators, reflection, `isinstance`, `hasattr`, wrappers, markers, or validated-registry types.

## Terminology

### Adapter execution support

The explicit semantic capabilities that one configured adapter instance truthfully claims it can execute.

This is distinct from local binding ownership and caller routing permission.

### Execution shape

For purposes of this RFC, one explicit adapter-operation contract used by one or more semantic capabilities.

An execution shape is not a routing capability.

### Executable admission

The point at which HAC requires an adapter's positive capability claims to have their required execution contracts before that adapter may influence request execution.

Generic storage or observation of an adapter does not necessarily perform executable admission.

### Binding ownership

RFC-0108's process-local assignment of a supported capability subset to one concrete adapter instance.

## Decision

HAC adopts the following adapter architecture:

```text
one common adapter surface

distinct execution shapes remain explicit contracts

one concrete adapter may satisfy one or several execution contracts

adapter capability support remains explicitly declared

capabilities are never inferred from execution mechanics

HAC owns the accepted capability -> required execution-shape relationship

every positive adapter capability claim must have
its required execution contract

execution-contract coherence is established fail-fast
before request-executable use

generic AdapterRegistry membership alone
does not imply executable admission

RFC-0108 separately validates ownership subset and non-overlap

routing remains operation-blind

normalized request shape owns exact execution dispatch

result validity, runtime health, and execution availability remain separate
```

## Common adapter surface

Every adapter participating in HAC composition has common concerns conceptually equivalent to:

```text
stable adapter name
adapter-wide health
explicit adapter execution-capability support
```

The exact implementation form is outside this RFC.

These facts are needed independently of any particular execution operation.

They do not imply that every adapter implements every execution shape.

A concrete adapter supporting several execution shapes remains one adapter with one common identity, one adapter-wide health boundary, and one explicit capability-support set.

## Explicit operation-shaped execution contracts

Distinct execution forms remain explicit.

For purposes of this RFC, current accepted behavior is grouped as:

```text
Chat execution shape
Summarize execution shape
Classify execution shape
```

Future RFCs may accept additional execution shapes when concrete evidence requires them.

One adapter may satisfy one execution contract or several.

An adapter need not implement contracts required only by capabilities it does not support.

Execution contracts are therefore **operation-shaped**, not automatically one-per-capability.

## Capability and execution shape are not one-to-one

Code is the primary control case.

Accepted behavior is:

```text
chat
code
    -> Chat execution shape
```

Code is a distinct semantic capability but does not require a separate adapter-level `code` operation.

Source-grounded Chat provides a second control case. Its normalized request receives capability `chat`, but HAC projects it through the existing Chat execution behavior before adapter invocation.

Therefore:

```text
semantic capability
    !=
normalized request variant
    !=
adapter execution shape
```

A new capability earns a new execution contract only when its adapter execution requirements are genuinely different.

## Project-owned capability-to-execution-shape semantics

HAC owns the relationship between accepted capabilities and their required execution shapes.

For purposes of this RFC, current accepted behavior maps as follows:

```text
chat
code
    -> Chat execution shape

summarize
    -> Summarize execution shape

classify
    -> Classify execution shape
```

This relationship is part of HAC architecture.

It is not defined by:

* the runtime;
* the adapter;
* the adapter class;
* the model;
* the endpoint;
* operator-provided arbitrary mappings.

This RFC does not require a public or runtime-configurable mapping registry.

## Capability support remains explicit

An adapter's execution support remains an explicit semantic claim.

HAC must not infer positive support from:

```text
method presence
class identity
adapter name
runtime name
model identity
model metadata
endpoint behavior
successful probing
automatic discovery
```

This is necessary even for current capabilities.

An implementation containing the Chat execution operation does not tell HAC whether a configured adapter supports:

```text
chat
```

or:

```text
chat
code
```

or only another allowed subset.

Mechanical execution possibility and positive capability support remain distinct.

## Positive capability claims require their execution contracts

For every capability positively claimed by an adapter, that adapter must have the execution contract HAC requires for the capability.

Conceptually:

```text
for each capability X in adapter execution support:

    required execution shape for X
        must be present for this adapter
```

Several capabilities may reduce to one required contract.

For example:

```text
adapter supports:
    chat
    code

required execution contracts:
    Chat
```

A state such as:

```text
adapter claims capability X

but

adapter lacks X's required execution contract
```

is invalid executable composition.

It is not:

* runtime unavailability;
* execution-permission refusal;
* routing ineligibility;
* an ordinary unsupported-operation result;
* a result-validation failure.

## Operation mechanics without a positive claim do not create support

The reverse state is valid.

An adapter may mechanically implement an execution shape while omitting one or more capabilities that could use it.

For example:

```text
adapter has Chat execution contract

adapter positively supports:
    chat

adapter does not positively support:
    code
```

Code remains unsupported for that configured adapter instance.

Capabilities are never inferred from mechanical implementation.

## Executable admission

Execution-contract coherence must be established fail-fast before an adapter enters request-executable use.

Conceptually:

```text
adapter instance
    ->
executable admission
    ->
execution-coherent adapter
    ->
request-executable composition
```

After admission, HAC may rely on this invariant:

> Every positive adapter capability claim has the execution contract required by HAC for that capability.

Executable admission does not:

* contact or probe the runtime;
* inspect models;
* depend on current health;
* execute a request;
* validate future results.

It verifies operation coherence of explicit composition facts.

## All positive adapter claims are covered

The coherence proof applies to the adapter's complete positive support set, not only to capabilities currently assigned by a local binding.

For example:

```text
adapter supports:
    chat
    future-X

binding assigns:
    chat
```

If the adapter positively claims `future-X`, it must still have the execution contract required by `future-X`.

Binding omission does not make a false adapter claim truthful.

## Generic `AdapterRegistry` membership is not executable admission

Generic adapter registration does not itself establish execution-contract coherence.

The existing registry also participates in observation and preflight paths that do not universally represent request-executable composition.

Those paths may inspect adapter or topology facts without evaluating execution support.

Therefore:

```text
present in a generic AdapterRegistry
```

does not necessarily mean:

```text
admitted for request execution
```

The stronger invariant begins when an adapter is admitted into request-executable use.

This RFC does not choose an implementation representation for that admitted state.

## One shared coherence rule

The capability-to-execution-contract rule is project-owned and should have one semantic meaning across composition paths.

Concrete adapter implementations must satisfy it, but runtime-specific adapters do not independently define it.

The rule must not acquire different meanings in:

* adapter constructors;
* registries;
* bindings;
* routing;
* executor branches.

Modern binding compositions and legacy non-binding request execution consume the same coherent adapter-support truth.

## Relationship to RFC-0108 local bindings

RFC-0108 remains authoritative for local capability ownership.

Once adapter execution support is coherent, a binding separately establishes:

```text
binding.capabilities
    subset-of
adapter.capabilities()
```

and the complete binding collection separately establishes pairwise-disjoint local ownership.

These checks answer a different question.

Executable admission asks:

> Are this adapter's positive support claims executable through the required HAC contracts?

Binding validation asks:

> Which subset of that support does this process assign to this concrete adapter instance?

A binding may therefore continue to omit capabilities that the adapter supports.

For example:

```text
adapter supports:
    chat
    summarize
    classify
    code

binding assigns:
    chat
```

remains valid.

An unsupported binding remains invalid:

```text
adapter supports:
    chat

binding assigns:
    classify
```

and overlapping local ownership remains invalid under RFC-0108.

This RFC changes neither rule.

## Legacy non-binding execution

The legacy non-binding execution path remains supported by this RFC.

Where that path can select adapters using their positive capability-support claims, those claims must have passed the same executable-admission coherence rule before routing consumes them.

There is one meaning of:

```text
adapter execution support
```

across binding and non-binding execution.

The legacy path does not receive a weaker contract in which a positively claimed capability may lack its required execution operation and fail only later.

This RFC does not otherwise redesign or retire that path.

## Routing remains operation-blind

Routing does not inspect execution contracts.

It continues to reason about accepted routing facts such as:

```text
required capability
eligibility
static declarations
local ownership
candidate order
execution availability
```

An adapter that claims a capability without its required execution contract represents invalid executable composition and must already have failed admission.

Treating that mismatch as another routing filter would incorrectly turn composition invalidity into ordinary candidate ineligibility.

## Normalized request shape owns execution dispatch

After routing has selected an execution-coherent adapter, the normalized request shape determines the exact execution path.

Conceptually:

```text
ClusterRequest
    -> Chat execution shape

SourceGroundedChatRequest
    -> HAC projection
    -> Chat execution shape

SummarizeRequest
    -> Summarize execution shape

ClassifyRequest
    -> Classify execution shape
```

Capability remains the routing requirement.

Request shape remains the execution-dispatch discriminator.

The router does not become an operation dispatcher.

## Result validation remains downstream

Execution-contract coherence proves only that HAC has a valid operation contract through which to attempt the capability.

It does not prove that any future runtime output is valid.

For example:

```text
Classify execution contract exists

adapter later proposes a label outside request.labels
    -> result validation failure
```

The same separation applies to any future execution shape.

Result truth remains capability-specific and downstream from execution.

## Dynamic health and execution availability remain separate

An execution-coherent adapter may currently be unavailable.

Execution-contract validity and dynamic runtime state answer different questions.

This RFC therefore does not change:

* adapter-wide `health()`;
* execution permission;
* execution concurrency;
* execution availability;
* pre-execution refusal;
* fallback semantics.

It adds no per-operation health.

## Compatibility

Existing concrete textual adapters remain conceptually valid.

Current Ollama, llama-server, and vLLM adapters positively support:

```text
chat
summarize
classify
code
```

Their required execution contracts are:

```text
Chat
Summarize
Classify
```

which they already implement.

Code continues to reuse Chat.

The architectural change is therefore primarily a refinement of adapter interface ownership and executable-admission coherence, not a rewrite of existing runtime behavior.

Existing tests using partial adapter doubles are useful supporting evidence that operation-specific doubles are natural even though the current monolithic interface suggests a broader suite. Test structure itself is not normative architecture.

## Relationship to RFC-0003

RFC-0003 remains authoritative for the fundamental runtime boundary:

```text
HAC core
    -> normalized HAC concepts
    -> runtime adapter
    -> runtime-specific behavior
```

RFC-0119 refines that deliberately small first boundary using later evidence.

RFC-0003 did not need to solve heterogeneous adapter-operation sets before such evidence existed.

Its rejection of a premature generic `execute()` abstraction is explicitly reaffirmed.

The evidence motivating RFC-0119 demonstrates heterogeneous execution contracts, not a useful universal execution contract.

## Relationship to RFC-0058 and RFC-0059

RFC-0058 remote static capability declarations and RFC-0059 caller-local static capabilities remain routing-permission facts.

They do not establish adapter execution support.

Adapter execution support does not create caller routing permission, and caller permission does not create adapter execution support.

This RFC changes neither boundary.

## Relationship to RFC-0066

RFC-0066 remains authoritative for what constitutes a HAC capability and what a positive capability claim means semantically.

RFC-0119 only establishes how accepted adapter capability support relates to executable adapter operations.

An execution contract cannot create a new capability.

## Relationship to RFC-0108

RFC-0108 remains authoritative for process-local capability ownership.

RFC-0119 strengthens the prerequisite truth consumed by its subset rule: adapter capability support used by an executable composition must have the required execution contracts.

RFC-0108 then independently assigns a subset of that support to concrete local ownership.

## Relationship to RFC-0110

RFC-0110 remains the accepted explicit configuration source for multi-binding local composition.

This RFC adds no configuration field, runtime option, operation name, or adapter mapping to that format.

A request-executable composition produced from RFC-0110 input must simply satisfy the execution-contract coherence required here before execution.

## Relationship to execution-availability RFCs

Execution-contract coherence answers:

> Does this adapter have a valid HAC operation contract for every capability it positively claims?

Execution availability answers later questions such as:

> May this otherwise valid candidate begin work now?

The two remain independent.

An incoherent adapter is not a temporarily unavailable candidate.

## Relationship to future image-generation investigation

A bounded investigation of possible future image generation produced the first concrete example where a legitimate adapter could need a new non-textual execution contract without implementing the existing textual operations.

That evidence exposed the seam accepted by this RFC.

This RFC does not accept:

* an image capability;
* an image adapter operation;
* image request semantics;
* image result semantics;
* an image format;
* image limits;
* image transport;
* image UI;
* image filesystem behavior.

Those remain separate future decisions if pursued.

## Alternatives considered

### Add every operation to one monolithic adapter interface

Rejected.

Text-only adapters would eventually need unrelated operations, and adapters supporting only a different execution form would need fake textual methods.

The fact that current adapters implement the same textual suite is not a durable architectural requirement.

### Fake unsupported methods

Rejected.

For example:

```text
future_operation(...)
    -> UnsupportedOperation
```

would allow an invalid positive capability claim to survive until request execution.

Unsupported capabilities should instead be absent from the adapter's positive support set, and unrelated operations need not exist.

### Optional methods on one adapter interface

Rejected.

Optional methods create two competing sources of truth:

```text
capabilities()
```

and:

```text
which optional operations happen to exist
```

They also move operation-presence handling toward request-time checks.

Explicit execution contracts state the requirement more directly.

### Infer capabilities from methods

Rejected.

Code already proves this mapping is invalid:

```text
chat
code
    -> Chat execution shape
```

Method presence cannot identify the semantic capabilities a configured adapter supports.

### Generic `execute()`

Rejected.

RFC-0003 deliberately deferred this abstraction, and the new evidence does not justify it.

Current operation contracts remain heterogeneous. A generic method would merely move the distinctions into generic request/result unions or adapter-internal dispatch.

HAC has not earned a universal execution abstraction.

### Handler or operation registry

Rejected.

A runtime mapping such as:

```text
operation -> handler
```

would introduce dynamic registration and another dispatch layer without solving a demonstrated requirement.

It would also risk duplicating capability-support truth.

### Separate top-level text and future image adapter abstractions

Rejected as the general solution.

They would duplicate the common adapter surface and become awkward when one concrete runtime supports execution contracts from both groups.

One common adapter plus multiple explicit execution contracts remains smaller.

### Child executor objects

Deferred.

Separate child execution objects could become useful if future evidence requires independent lifecycle or resource ownership.

No current requirement justifies that additional object model.

### Validate only in `LocalCapabilityBinding`

Rejected.

Binding validation sees only the assigned subset.

For:

```text
adapter supports:
    chat
    future-X

binding assigns:
    chat
```

a false positive `future-X` claim would remain false even though the binding omitted it.

Binding-only validation would also leave the legacy non-binding execution path exposed.

### Validate in routing

Rejected.

Routing-time execution-contract checks would convert invalid executable composition into ordinary routing ineligibility and could hide the defect by selecting another candidate.

Routing must remain operation-blind.

### Validate primarily during executor dispatch

Rejected.

Request time is too late to discover that the selected adapter never had the execution contract required by its positive capability claim.

Executable composition must already be coherent before routing.

### Make generic `AdapterRegistry.register()` the proof boundary

Rejected.

Generic registry use also supports observation and preflight contexts that do not universally imply request-executable composition.

Registry membership therefore remains weaker than executable admission.

### Make each runtime adapter constructor authoritative

Rejected as the architecture-wide owner.

Concrete adapters must satisfy the rule, but the relationship between HAC capabilities and required execution contracts is project-owned, not runtime-owned.

Duplicating that semantic rule across runtime-specific constructors would create unnecessary drift.

### Retire the legacy non-binding execution path

Deferred.

This RFC can give binding and non-binding execution the same adapter-support truth without retiring or redesigning the legacy path.

No broader compatibility change is justified here.

## Trade-offs

### More explicit adapter vocabulary

The architecture now distinguishes:

```text
common adapter surface
```

from:

```text
operation-specific execution contracts
```

This adds terminology, but reflects responsibilities that can no longer be truthfully represented as one mandatory operation suite.

### Execution-contract growth

Future execution contracts could proliferate if created mechanically for every capability.

This RFC explicitly rejects that rule.

New contracts are justified only by genuinely distinct execution forms.

Code remains the control case showing that a new capability may reuse an existing execution contract.

### Explicit executable-admission lifecycle

HAC now distinguishes generic adapter storage or observation from admission into request-executable use.

That distinction adds one lifecycle concept but avoids overloading generic registry semantics.

### Implementation mechanism remains open

The architecture requires HAC to prove execution-contract coherence before request-executable use.

This RFC intentionally does not choose how Python represents or enforces that proof.

## Impact

### Adapter architecture

The common adapter surface remains shared by all execution adapters.

Operation-specific execution contracts are required only where supported.

### Existing adapters

Current Ollama, llama-server, and vLLM behavior remains compatible.

### Adapter registry

Generic registry membership does not gain executable-admission semantics.

### Local bindings

RFC-0108 subset and non-overlap rules remain unchanged.

### Legacy execution

Legacy non-binding request execution consumes the same coherent adapter-support truth as binding-based execution.

### Routing

No routing semantics change.

### Execution dispatch

Normalized request shape continues to select the exact adapter execution path after routing.

### Results, health, and availability

No change to result validation, adapter health, or execution-availability architecture.

### Transport, API, configuration, UI, and filesystem

No change.

## Decision

Home AI Cluster will preserve one common adapter surface and represent genuinely distinct execution forms as explicit execution contracts.

One concrete adapter may satisfy one or several execution contracts.

Adapter capability support remains explicit semantic truth. HAC will not infer capabilities from implementation mechanics, runtime identity, model identity, probing, or discovery.

HAC owns the accepted relationship between capabilities and required execution shapes. Multiple capabilities may share one execution shape, including:

```text
chat
code
    -> Chat execution shape
```

Every positive adapter capability claim must have its required execution contract before the adapter enters request-executable use.

Execution mechanics without a positive capability claim do not create support.

Generic `AdapterRegistry` membership alone does not imply executable admission.

RFC-0108 remains separately responsible for local binding subset and non-overlap, and a binding may omit capabilities the adapter supports.

Legacy non-binding execution consumes the same coherent adapter-support truth.

Routing remains operation-blind.

Normalized request shape remains responsible for exact execution dispatch.

Result validity, runtime health, and execution availability remain separate downstream concerns.

This RFC accepts no new capability, generic execution framework, plugin mechanism, handler registry, optional or fake operation model, image architecture, transport, UI, or filesystem behavior.
