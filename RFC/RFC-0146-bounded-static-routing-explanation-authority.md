# RFC-0146: Bounded Static Routing Explanation Authority

Status: Accepted

Date: 2026-10-03

Author: frian

## Summary

Home AI Cluster should define one bounded non-effectful routing-explanation authority answering:

> Given the current effective ordinary caller composition, one accepted capability, and routing-relevant constraints, what routing facts can HAC truthfully determine before execution?

This explanation is a projection of routing truth already present in the effective caller composition.

It does not execute a business request.

It does not require business request content.

It does not probe a local runtime or remote node.

It does not evaluate execution permission.

It does not predict execution success, fallback consumption, or final execution attribution.

The explanation may expose:

- the requested accepted capability;
- routing-relevant constraints;
- whether an eligible local candidate exists;
- eligible declared-remote candidates in their existing caller-owned declaration order;
- candidates excluded by accepted routing constraints;
- the initial candidate selected by the existing ordinary selection policy, if one is statically selectable; and
- the existing static reason for no selection when ordinary pre-execution routing already owns such a reason.

Minimal caller-owned node identity may be exposed where necessary to distinguish ordered declared-remote candidates.

Runtime names, model names, adapter identity, local binding details, transport addresses, URLs, health, readiness, execution cardinality, and business payload remain excluded.

This RFC defines the semantic authority and privacy boundary only.

It does not yet select the public carrier, command spelling, endpoint, serialization schema, or compatibility treatment of the retained `home-ai-cluster-explain-routing` launcher.

No implementation of a new public surface is authorized until those exposure and compatibility questions are separately resolved.

## Context

HAC now has three related but distinct explanation or projection boundaries.

### RFC-0144 caller-routable capability projection

RFC-0144 answers:

> Which accepted capabilities are present on this currently running caller's ordinary routing surface before additional request-specific constraints?

That projection is deliberately capability-only.

It does not expose:

- nodes;
- local-versus-remote provenance;
- declared-remote order;
- bindings;
- adapters;
- runtimes;
- models;
- routing reasons;
- routing priority; or
- selection.

Its first purpose is browser capability presentation.

RFC-0144 therefore answers whether one capability belongs to the current caller routing surface, but deliberately cannot explain why or how that capability is represented there.

### RFC-0145 ordinary request lifecycle explanation

RFC-0145 answers:

> What happened to this one actual request?

The request being explained is actually executed.

The lifecycle explanation observes authoritative facts from that same ordinary execution.

It may therefore explain facts that cannot exist before execution, including execution permission, concrete continuation reasons, adapter invocation, remote transport invocation, remote permission refusal, consumed fallback, final execution attribution, and terminal failure semantics.

RFC-0145 explicitly does not answer what HAC might do for a hypothetical request.

### RFC-0027 historical routing explanation

RFC-0027 established the non-effectful `home-ai-cluster-explain-routing` command.

Its concept remains useful:

> explain routing without candidate execution.

However, its accepted and implemented composition belongs to an earlier architectural stage.

The current command constructs a synthetic explanation-only composition from explicit invocation inputs such as local and declared-remote presence.

It does not inspect the effective ordinary caller composition now used by modern local and static-cluster operation.

It therefore answers a different bounded question:

> Given this explicitly constructed synthetic candidate composition, how does the historical automatic selection rule resolve it?

It does not currently answer:

> What can this effective ordinary caller truthfully determine before execution?

RFC-0027 remains historically valid for the composition it defines.

The need addressed by this RFC is the modern ordinary-caller equivalent.

## Problem

Operators can currently inspect several distinct kinds of HAC truth.

RFC-0144 can show which capabilities are routable by the active caller, but not why.

Retained Configuration can show future invocation state, but is not current-process truth.

Preflight can inspect static configuration coherence, but does not represent the effective running caller.

Health and status intentionally answer different observation questions.

RFC-0145 can explain modern routing and fallback in detail, but only by actually executing the business request.

The retained RFC-0027 routing explanation performs no execution, but its synthetic composition is not the effective ordinary caller composition.

This leaves a narrow diagnostic gap.

An operator may want to understand, before sending business content:

- whether a capability has a local routing candidate;
- whether declared remotes are statically eligible;
- which declared remotes are eligible and in what existing declaration priority order;
- whether an accepted routing constraint excludes a candidate family;
- which candidate the existing ordinary initial-selection policy would choose from current static routing facts; or
- why no candidate is statically selectable.

HAC already knows these facts before execution.

However, exposing them requires a deliberate architectural boundary.

The implementation must not solve this gap by:

- reconstructing active state from retained configuration;
- probing runtimes or remote nodes;
- running execution-permission checks;
- constructing synthetic business payloads;
- duplicating routing policy;
- predicting fallback;
- or treating a static explanation as a promise of future execution behavior.

## Goals

This RFC should:

- define the smallest modern non-effectful routing-explanation authority;
- derive explanation only from the effective ordinary caller composition;
- reuse existing routing and candidate-eligibility authorities;
- remain capability-centered and engine-independent;
- require no business request payload;
- allow accepted routing-relevant constraints to affect static selectability;
- expose enough candidate identity to make ordered declared-remote eligibility useful;
- clearly distinguish static eligibility and initial selection from actual execution;
- preserve RFC-0144 as the smaller capability-only projection;
- preserve RFC-0145 as the authoritative actual-execution explanation;
- avoid a second router, fallback engine, health model, or observability framework; and
- preserve local-first and privacy-first defaults.

## Non-goals

This RFC does not define or authorize:

- request execution;
- runtime execution;
- remote transport invocation;
- health probing;
- runtime availability probing;
- remote reachability probing;
- execution-permission evaluation;
- execution cardinality inspection;
- admission prediction;
- final-node prediction;
- execution-success prediction;
- fallback prediction;
- retry prediction;
- a generalized execution plan;
- tracing;
- telemetry;
- retained explanation history;
- monitoring;
- polling;
- background work;
- scheduling;
- scoring;
- load balancing;
- model selection;
- runtime selection;
- capability discovery;
- topology discovery;
- remote administration;
- a dashboard;
- generic introspection;
- a generic observer or event API;
- a new routing policy;
- a new fallback policy;
- a new failure taxonomy;
- exposure of local binding internals;
- exposure of adapter or runtime internals;
- exposure of remote transport addresses or URLs;
- a command name;
- CLI option spelling;
- an HTTP endpoint;
- a JSON schema;
- browser presentation; or
- compatibility treatment of the retained RFC-0027 launcher.

This RFC also does not authorize implementation of a new public carrier.

A follow-up architectural decision is required before exposing this authority through a new or changed public surface.

## Decision

### One static-routing explanation authority

HAC may derive one bounded non-effectful explanation from the effective ordinary caller routing composition.

Conceptually, the explanation evaluates:

```text
accepted capability
+
accepted routing-relevant constraints
+
effective ordinary caller routing composition
```

It does not evaluate a business request.

The explanation is a projection of existing routing truth.

It must not become an independent source of routing truth.

### Effective ordinary caller composition

The active ordinary caller composition is authoritative.

Relevant existing facts include, where applicable:

- active local routing eligibility;
- explicit local capability-binding ownership;
- caller-local routing restrictions;
- active declared-remote capability eligibility;
- declared-remote declaration order; and
- the existing ordinary initial candidate-selection policy.

A retained configuration file or HAC-managed retained state is not equivalent to the effective currently running caller composition.

A separately launched finite process that merely loads equivalent retained configuration must not claim to explain another already-running caller.

If a future finite surface constructs and owns its own ordinary composition, it may explain that composition only.

It must not represent that result as current-process truth for a different process.

### No business request payload

Static routing explanation must not require:

- Chat messages;
- Summarize source text;
- Classify source text or labels;
- Code instructions;
- Image Generation instructions or image bytes;
- source-grounded evidence;
- workspace content; or
- other business request content.

The routing question is smaller than an executable request.

Its conceptual inputs are:

```text
capability
routing-relevant constraints
```

If an existing implementation helper requires a complete executable request merely to access capability or routing constraints, implementation should extract or reuse a payload-free routing seam rather than inventing synthetic business content.

In particular, static routing explanation must not construct a fake Chat request merely because Chat was historically the first request representation.

### Accepted capability

The requested capability must belong to the existing accepted HAC capability vocabulary.

The explanation must not:

- invent capability names;
- infer capabilities from models or runtimes;
- expose arbitrary adapter capability strings as public routing facts; or
- create a new extensible capability registry.

Existing capability admission remains unchanged.

### Local candidate eligibility

The explanation may state whether an eligible local routing candidate exists for the requested capability.

That fact must be derived from the same existing local routing relationships used by ordinary routing.

Where explicit local capability bindings exist, binding ownership remains part of the eligibility calculation.

Adapter execution support alone must not create local routing eligibility.

Caller-local static capability restrictions must continue to constrain local routing eligibility where applicable.

Existing static node availability used by routing remains part of existing routing truth.

It must not be reinterpreted as live runtime health or readiness.

### Local binding privacy boundary

Local bindings may influence the result.

Their internal representation should not be exposed by this first static explanation authority.

The explanation therefore may state:

```text
local candidate eligible
```

or the equivalent semantic fact.

It must not require exposing:

- binding identity;
- binding configuration;
- adapter identity;
- adapter instance;
- runtime identity;
- runtime model;
- runtime URL; or
- process-local runtime configuration.

A future demonstrated debugging need for those details requires separate architectural evaluation.

### Declared-remote eligibility

The explanation may project every active caller-owned declared remote that is statically eligible for the requested capability under existing routing semantics.

Remote eligibility remains declaration-based.

The explanation performs no remote contact.

It does not verify that a declared remote:

- is running;
- is reachable;
- is healthy;
- currently has the capability;
- can obtain execution permission;
- can invoke its adapter;
- or can successfully complete the request.

### Declared-remote order

Eligible declared remotes may be represented in the same deterministic declaration priority order already owned by ordinary routing.

The explanation must not sort, rank, score, probe, or reorder them.

This order means only:

> These caller-owned declarations are statically eligible in this existing declaration priority order.

It does not mean:

> HAC will execute these nodes in this sequence.

Execution continuation depends on request-time facts that do not yet exist.

### Minimal caller-owned node identity

A static explanation may expose the caller-owned node IDs of eligible declared remotes when necessary to make declaration order and candidate distinction useful.

These IDs are cluster-level caller-owned identities.

They are not:

- transport addresses;
- URLs;
- IP addresses;
- hostnames;
- runtime identities;
- model identities; or
- remote-reported execution identity.

No transport address or remote URL may be exposed merely to add diagnostic detail.

The local candidate may be represented by its candidate family without requiring additional local topology detail.

### Routing-relevant constraints

The explanation may apply accepted constraints that already affect pre-execution routing selectability.

For the current architecture, `local_only` is such a constraint.

For example:

```text
eligible remote declaration
+
local_only = true
=
statically eligible by capability
but excluded from selection by the request constraint
```

The explanation may distinguish:

- eligibility before routing-relevant constraints;
- exclusion caused by an accepted constraint; and
- selectability after those constraints.

This RFC does not make every request field a routing constraint.

A request field may enter static explanation only when existing accepted routing architecture already gives it routing significance.

### Initial static selection

The explanation may apply the existing ordinary initial-selection policy to the current statically selectable candidates.

It may therefore state, where applicable:

- local is the current initial selected candidate;
- one declared remote is the current initial selected candidate;
- or no candidate is statically selectable.

This is not a new selection policy.

The explanation must reuse the same policy authority ordinary routing already uses.

It must not independently reproduce or approximate that policy.

### Initial selection is not execution attribution

A projected initial candidate means only:

> Under the current effective composition and supplied routing-relevant constraints, this is the candidate ordinary routing would select before execution-time facts occur.

It does not mean:

> This candidate will execute the request successfully.

It also does not mean:

> This candidate will produce the final result.

For example, an initially selected local candidate may later fail to obtain execution permission or may encounter an accepted pre-transmission failure.

A later actual request may therefore continue under existing fallback semantics.

That possibility does not make the static initial selection false.

### Eligible next candidates are not predicted fallback

The static explanation may expose eligible declared remotes in declaration priority order.

It must not label them as an execution plan or guaranteed fallback sequence.

The distinction is mandatory:

```text
eligible declared remotes in priority order
```

is statically knowable.

```text
fallback will execute remote-a, then remote-b
```

is not.

Whether ordinary execution advances from one candidate to another depends on concrete accepted request-time conditions such as:

- execution-permission refusal;
- pre-transmission runtime connection unavailability;
- remote receiver execution-permission refusal; or
- another accepted narrow continuation condition.

Those facts belong to actual execution and therefore to RFC-0145 when an actual request is explicitly explained.

### No execution permission

Static routing explanation must not call:

```text
ExecutionIntervalCardinality.try_enter()
```

or any equivalent state-changing or time-sensitive execution-permission operation.

Current process cardinality is execution-time truth.

It is not static routing truth.

The explanation must not predict whether local or remote execution permission will later be granted.

### No probing

Constructing the explanation must perform no:

- adapter health call;
- inference request;
- remote HTTP request;
- receiver request;
- status observation;
- model inventory query;
- runtime lifecycle operation;
- network discovery;
- filesystem discovery; or
- plugin/provider access.

The explanation is derived solely from already composed caller-owned routing state.

### No success prediction

The explanation must not state or imply that a future request:

- will succeed;
- will fail;
- will reach a specific remote;
- will consume fallback;
- will use a specific final node;
- will receive execution permission;
- or will invoke a specific runtime successfully.

A static explanation is descriptive of current routing state.

It is not a forecast.

## Relationship to RFC-0144

RFC-0144 remains unchanged.

Its capability-only projection continues to answer:

> Which accepted capabilities are currently present on this caller's ordinary routing surface?

That projection remains suitable for low-information browser presentation.

RFC-0146 does not enlarge RFC-0144's existing browser endpoint or authorize the browser to receive candidate topology, node IDs, ordering, or selection details.

Conceptually:

```text
RFC-0144
    capability membership only

RFC-0146
    explicit bounded static routing diagnosis
```

RFC-0146 must reuse the same underlying routing authorities where applicable rather than creating a second interpretation.

## Relationship to RFC-0145

RFC-0145 remains the authority for actual execution explanation.

The two questions are distinct:

```text
RFC-0146
    What is statically knowable before execution?

RFC-0145
    What actually happened during this execution?
```

RFC-0146 must not infer RFC-0145 lifecycle facts in advance.

RFC-0145 must not reconstruct RFC-0146 predictions after execution.

For example:

```text
RFC-0146:
initial candidate = local
eligible declared remotes = [remote-a, remote-b]
```

does not imply that RFC-0145 will later report:

```text
local -> remote-a -> remote-b
```

RFC-0145 may report only continuation and candidate-specific facts that actually occurred.

## Relationship to RFC-0027

RFC-0146 narrows RFC-0027's routing-explanation authority.

RFC-0027 remains valid only for the synthetic explanation composition it explicitly constructs from its own invocation inputs. It remains authoritative for explaining that synthetic composition according to its accepted historical contract.

RFC-0027 is not authoritative for static explanation of an effective ordinary caller composition.

For that question, RFC-0146 supersedes RFC-0027's broader historical routing-explanation framing and establishes the sole modern semantic authority:

> What can this effective ordinary caller truthfully determine before execution?

This semantic ownership correction does not decide the compatibility treatment of the retained `home-ai-cluster-explain-routing` launcher.

A future RFC may choose among several compatibility strategies, including:

- modernizing the retained `home-ai-cluster-explain-routing` launcher;
- retaining the RFC-0027 launcher with its historical bounded synthetic-composition semantics while adding a distinct modern carrier;
- providing an explicit compatibility distinction;
- or retiring the historical launcher if compatibility evidence supports that decision.

Until that compatibility decision is made, no implementation may silently reinterpret the RFC-0027 launcher as an explanation of another effective ordinary caller merely because its existing name appears suitable.

## Relationship to retained Configuration

Retained Configuration and static routing explanation answer different questions:

```text
retained Configuration
    -> what future HAC invocations are configured to use

static routing explanation
    -> what this effective ordinary caller can statically determine now
```

Static routing explanation must not reconstruct current-process truth from retained Configuration.

A retained configuration mutation that affects only future invocations need not alter an already-running caller's static explanation.

Conversely, an active caller may have been built from explicit invocation inputs that differ from retained state.

The effective active composition remains authoritative.

## Relationship to preflight, health, and status

This RFC does not consolidate existing inspection surfaces.

Preflight remains static coherence inspection.

Health remains bounded local declared/runtime observation.

Status remains bounded declared static-cluster observation.

Static routing explanation answers a narrower routing question.

It must not absorb those surfaces or borrow their observations to create stronger routing claims.

In particular:

```text
routing eligibility
!=
runtime health
!=
remote reachability
!=
execution permission
!=
execution success
```

## Privacy and security

The static explanation contains no business request content.

It must not contain or expose:

- prompts;
- messages;
- source text;
- Classify labels;
- evidence;
- file or workspace content;
- image bytes;
- credentials;
- remote URLs;
- transport addresses;
- runtime URLs;
- runtime names;
- model identifiers;
- raw retained configuration;
- raw binding objects;
- raw adapter objects;
- raw runtime objects;
- raw remote declaration objects;
- health observations;
- execution-cardinality state;
- raw exception text; or
- execution history.

Minimal caller-owned node IDs for eligible declared remotes may be projected only for candidate distinction and declaration ordering.

The explanation is non-retained unless a later accepted RFC explicitly defines otherwise.

## Required invariants

Any later implementation of this authority must preserve all of the following:

1. Static explanation performs no business request execution.
2. Static explanation requires no business request payload.
3. The effective ordinary caller composition is authoritative.
4. Retained Configuration is not reinterpreted as current process truth.
5. Existing routing authorities are reused; no second router is introduced.
6. Local bindings may affect local eligibility without being exposed.
7. Declared-remote eligibility is capability-based and declaration-backed.
8. Eligible remote ordering preserves existing caller-owned declaration priority.
9. Routing-relevant constraints affect selectability only where already accepted by routing architecture.
10. Initial static selection reuses existing ordinary selection policy.
11. Initial selection is not represented as guaranteed execution attribution.
12. Ordered eligible remotes are not represented as guaranteed fallback.
13. No execution-permission operation is invoked.
14. No runtime, remote, health, status, or availability probe is performed.
15. No success, failure, fallback-consumption, or final-node prediction is made.
16. No transport URL, runtime, model, adapter, or binding detail is exposed merely for diagnostic detail.
17. Explanation remains capability-centered and engine-independent.
18. RFC-0144 remains capability-only.
19. RFC-0145 remains actual-execution-only.
20. No generic introspection, tracing, monitoring, or event architecture is created.

## Expected implementation seam

This RFC intentionally does not authorize implementation of a public surface.

A later implementation should nevertheless be expected to reuse small existing seams rather than reconstruct routing.

Current relevant authorities include conceptually:

```text
local routing eligibility for capability
declared-remote eligibility for capability
declared-remote declaration order
routing-relevant constraints
ordinary initial selection policy
```

If implementation requires constructing fake request content, probing execution state, or reproducing ordinary routing logic, implementation should stop and return to architecture.

## Acceptance proof for a future implementation

A later public-surface RFC and implementation should prove at least:

1. A locally eligible capability can be explained without adapter execution.
2. An adapter-supported but unbound capability does not become locally eligible when explicit bindings own another capability.
3. Caller-local routing restriction is preserved.
4. One eligible declared remote can be represented without contacting it.
5. Multiple eligible declared remotes preserve declaration priority order.
6. `local_only` may exclude eligible remotes from selectability without removing the fact that they matched capability eligibility.
7. Existing local-first initial selection is represented when local and remote candidates are selectable.
8. Remote initial selection is represented when no local candidate is selectable and remote execution is allowed by routing constraints.
9. A no-selectable-candidate state is represented without execution.
10. The explanation requires no Chat, Summarize, Classify, Code, or Image Generation business content.
11. Classify requires no synthetic labels merely to explain routing.
12. Image Generation requires no synthetic instruction or image/result representation merely to explain routing.
13. No execution-permission check occurs.
14. No runtime health or remote network activity occurs.
15. Remote node IDs may distinguish ordered candidates while URLs and addresses remain absent.
16. Binding, adapter, runtime, and model identity remain absent from the public projection.
17. RFC-0144 behavior remains unchanged.
18. RFC-0145 actual-request behavior remains unchanged.
19. Ordinary routing, fallback, success, and failure semantics remain unchanged.
20. The implementation creates no generic introspection framework.

## Alternatives considered

### Use RFC-0144 only

RFC-0144 already provides a safe capability-only answer.

This remains sufficient for the question:

> Can this caller route this capability at all?

It is insufficient for diagnostic questions involving:

- local versus declared-remote eligibility;
- constraint exclusion;
- initial selection;
- multiple eligible declared remotes; or
- declaration priority order.

Expanding RFC-0144 itself is rejected because its narrow capability-only browser boundary is deliberate and useful.

### Use RFC-0145 with a harmless payload

Rejected.

RFC-0145 explains an actual executed request.

Inventing a harmless payload would still cause execution and would misrepresent a pre-execution diagnostic as an actual-request explanation.

Different capabilities also have different valid request contracts.

A synthetic payload would therefore add unnecessary content and capability-specific fabrication.

### Reuse RFC-0027 unchanged

Rejected as the modern semantic authority.

RFC-0027's non-execution concept remains sound, but its current synthetic composition does not represent the effective ordinary caller.

Its public contract also predates ordered modern remote composition, current binding ownership, retained/effective composition distinctions, and later ordinary fallback semantics.

Its compatibility treatment requires a separate explicit decision.

### Load retained Configuration and explain it

Rejected.

Retained Configuration represents future invocation state.

It may differ from the currently running caller.

Reconstructing routing from retained state would answer the wrong question and could create a second interpretation of current routing truth.

### Probe runtimes and remotes

Rejected.

Reachability, runtime availability, receiver permission, and adapter success are distinct from static routing eligibility.

Probing them would create an observation surface rather than a static routing explanation.

It would also introduce network effects and freshness semantics not required by this decision.

### Expose bindings, adapters, runtimes, and models

Rejected for the first boundary.

Those facts may contribute internally to eligibility but are not required to answer the bounded routing question.

Exposing them would widen the diagnostic into runtime-composition introspection and weaken the capability-centered boundary.

### Return an execution plan

Rejected.

The future lifecycle depends on execution-time facts that do not yet exist.

A static ordered set of eligible candidates is not an execution plan.

Calling it one would create a false prediction.

## Trade-offs

This decision exposes more routing structure than RFC-0144.

In particular, minimal declared-remote node identity and declaration order may become visible through a future explicit diagnostic surface.

That additional visibility is justified only for explicit operator diagnosis and must not automatically widen ordinary browser or request surfaces.

The explanation is deliberately incomplete.

It cannot tell the operator whether a request will succeed.

It cannot tell the operator which node will ultimately execute.

It cannot tell the operator whether fallback will occur.

Those limitations are desirable because HAC should distinguish what it knows statically from what it can know only by executing.

The decision also leaves one important implementation question unresolved: how an operator reaches the effective caller's in-memory authority without turning retained configuration into a substitute.

That question affects process authority, exposure, and compatibility and therefore should not be hidden as an implementation detail.

## Impact

This RFC establishes a semantic boundary for future modern static-routing diagnosis.

It may later affect:

- a dedicated operator diagnostic surface;
- ordinary caller application composition;
- internal payload-free routing-query seams;
- compatibility treatment of `home-ai-cluster-explain-routing`;
- focused tests for static eligibility and selection truth; and
- documentation distinguishing static explanation from actual-request lifecycle explanation.

It does not itself change:

- ordinary request execution;
- routing;
- fallback;
- execution permission;
- capability admission;
- retained Configuration;
- RFC-0144 browser projection;
- RFC-0145 lifecycle explanation;
- preflight;
- health;
- status;
- receiver behavior;
- compatibility behavior; or
- any public command or endpoint.

## Open questions

The following questions remain intentionally unresolved:

- What public carrier should expose modern static-routing explanation?
- Must it be served by the already-running ordinary process in order to preserve effective caller truth?
- If so, should a local CLI act only as a client of that process?
- Should the existing loopback application expose a dedicated diagnostic endpoint, or would that widen browser authority unnecessarily?
- Should `home-ai-cluster-explain-routing` be modernized, preserved with historical semantics, or retired?
- What is the smallest public representation that preserves candidate distinction and declaration order without becoming generic topology inspection?
- Should the local candidate expose only its family, or also its existing caller-owned node ID?
- Which existing static no-selection reasons are sufficiently stable to expose publicly?
- Should the first public surface support only `local_only` as a routing-relevant constraint, while allowing later accepted constraints to extend the semantic input?
- Does selecting the public carrier require a dedicated follow-up RFC, or can that decision be added to this RFC before acceptance?

## Decision

Pending.
