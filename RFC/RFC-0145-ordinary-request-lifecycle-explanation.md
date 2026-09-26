# RFC-0145: Ordinary Request Lifecycle Explanation

- Status: Draft
- Date: 2026-09-26

## Summary

HAC SHALL allow one explicitly requested actual-request explanation to describe the authoritative ordinary lifecycle of the same request that HAC actually executes.

The explanation SHALL be derived from bounded request-scoped facts already used by ordinary orchestration while making routing, execution-permission, continuation, fallback, and final-attribution decisions.

The explanation SHALL NOT reconstruct those decisions afterward, replay the request, probe candidate health, or run a second routing or fallback policy.

The account is request-scoped and non-retained. It is not a generic tracing, history, telemetry, or observability facility.

## Motivation

RFC-0032 established an explicit actual-request explanation surface answering, in bounded form:

> What happened to this one actual request?

That proof deliberately selected once and executed once. RFC-0034 later added structured actual-request failures, and later accepted work added bounded execution-permission facts to the explanation account.

Ordinary HAC request execution has since gained additional accepted semantics, including retained caller composition, execution permission, local-to-declared-remote continuation, ordered declared-remote fallback, and narrow pre-engagement failure conditions that permit safe continuation.

The historical explanation command remains truthful about the special request it executes, but it no longer represents the full lifecycle of a modern ordinary caller request.

Current ordinary orchestration already knows the facts needed to explain its decisions while executing them. In particular, the ordinary fallback path knows the initial selected candidate, local execution-permission result, concrete conditions that permit or prohibit continuation, declared-remote candidates actually attempted, and final result or terminal failure.

The missing architecture is therefore not tracing. It is bounded retention of authoritative facts that ordinary execution already uses and would otherwise discard as control flow advances.

## Decision

### One ordinary execution owns both behavior and explanation

An actual-request explanation MUST be produced from the same ordinary orchestration invocation that executes the request being explained.

Explanation MUST NOT independently rediscover candidates, rerun automatic selection, recompute execution permission, reconstruct fallback decisions, or infer consumed continuation reasons after execution.

The ordinary orchestrator remains the sole owner of routing and execution decisions.

The explanation account is observational only.

### Effective caller composition

The explained request MUST execute through the effective composition of the caller handling that request.

That includes, where applicable, the active in-memory truths already used by ordinary execution:

- local routing eligibility and bindings;
- caller-local routing restrictions;
- declared-remote topology and capability eligibility;
- remote transport;
- process-local execution cardinality;
- capability-specific companion composition such as Image Generation.

A separately launched finite process that merely reconstructs the same retained configuration is not equivalent to an already-running caller for process-local execution-permission truth.

For example, two processes may share the same retained execution-limit value while holding different current execution cardinalities. An explanation MUST NOT claim to describe another process's permission decision by reconstructing its retained configuration.

A finite explanation invocation MAY explain the ordinary request that the finite invocation itself executes through its own effective composition. It MUST NOT present that execution as an explanation of a different already-running caller process.

### Bounded request-scoped lifecycle account

Ordinary orchestration SHALL be able to retain one bounded internal account for the request being explicitly explained.

The account SHALL contain only authoritative semantic facts already known while ordinary orchestration executes the request.

It MAY retain facts in these categories when they occur:

- requested capability and accepted request constraints relevant to routing;
- initial automatic selection and its existing bounded selection explanation;
- whether local execution permission was granted or denied;
- the candidate actually attempted;
- a concrete accepted reason that allowed continuation to another candidate;
- subsequent declared-remote candidate attempts under accepted ordered fallback;
- final successful execution attribution;
- terminal failure classification already owned by current execution semantics.

This list defines semantic categories, not a required serialized schema.

The account MUST NOT invent a generalized engagement state when current execution uses a narrower authoritative fact.

For example, safe continuation may be explained by the concrete accepted condition that actually authorized it, such as:

- local execution permission denied before local execution began;
- `RuntimeConnectionUnavailableBeforeRequestError` before request transmission;
- the accepted receiver execution-permission refusal;
- another currently accepted narrow pre-engagement condition used by ordinary ordered fallback.

The account MUST retain such a reason at the point ordinary orchestration consumes it. It MUST NOT infer the reason later from the final result or final exception.

### Shared lifecycle truth, not a recorder architecture

The accepted architecture is a bounded shared internal lifecycle account owned by ordinary orchestration.

It is not a caller-provided callback, event stream, middleware hook, generic recorder, or observer API.

Implementation MAY use richer internal outcome values or similarly small internal structures where necessary, provided that:

- ordinary routing and execution decisions remain unchanged;
- ordinary success results remain unchanged;
- existing exception propagation and ownership remain unchanged;
- account production cannot affect execution behavior;
- no second orchestrator or routing policy is introduced.

The account is internal execution truth first. User-facing explanation is a projection of that truth.

### Success and failure

A successful explained request SHALL preserve the ordinary normalized result and MAY project final execution attribution already accepted for that result family.

A failed explained request SHALL preserve the ordinary terminal failure behavior. Explanation support MUST NOT require converting established exceptions into a new universal outcome or public error taxonomy.

Where ordinary execution consumes a non-terminal failure or refusal in order to continue safely, the bounded account MAY retain the accepted semantic reason for that continuation.

Terminal failure explanation SHALL use the authoritative failure family already owned by current execution. It MUST NOT reclassify failures merely to produce a more detailed explanation.

### Fallback and continuation

The explanation account MAY describe candidates actually attempted and concrete accepted reasons for continuation.

It MUST NOT expose hypothetical candidates that ordinary execution did not consider or attempt merely to make the explanation appear complete.

It MUST NOT evaluate fallback eligibility independently.

The same ordinary control flow that decides whether execution may continue is authoritative for the account.

No generalized timeline is accepted by this RFC.

### Cancellation and HTTP disconnect

Core ordinary routing/execution lifecycle facts are in scope.

HTTP client-disconnect ownership currently exists at an outer HTTP execution boundary rather than inside the core ordered-fallback owner.

This RFC does not require moving cancellation ownership into the core lifecycle account or changing current cancellation semantics.

A future extension MAY decide whether an HTTP-surface explanation needs a bounded disconnect fact, but that is not required for this RFC's core proof.

### Capability scope

The architecture applies to ordinary single-request capability execution that already shares the ordinary capability-centered routing lifecycle, including:

- Chat;
- Summarize;
- Classify;
- Code;
- Image Generation.

Source-grounded Chat may use the same lifecycle for the Chat request after evidence already exists.

This RFC does not make External Information acquisition part of the ordinary request lifecycle account. Acquisition has separate higher-level authority.

This RFC also does not make the complete workspace-aware Code interaction part of the account. Individual ordinary Code inference requests may participate, but filesystem operations, repeated interaction, and workspace authority remain owned by the workspace-aware Code lifecycle.

### Privacy boundary

The lifecycle account MUST remain request-scoped and non-retained.

It MUST NOT contain or expose:

- prompt or request content;
- source/evidence content;
- workspace/file content;
- credentials;
- remote URLs;
- raw retained configuration objects;
- raw adapter/runtime objects;
- raw remote declaration objects;
- generic topology snapshots;
- generic health/readiness state.

Minimal caller-owned node identity and existing result attribution MAY be projected where already necessary to explain which accepted candidate actually executed.

The account MUST remain capability-centered and topology-minimal.

### Explicit explanation only

Lifecycle-account retention is required only for an explicitly requested actual-request explanation path.

Ordinary requests that are not being explained MUST NOT be required to retain explanation history after completion.

This RFC does not introduce background recording, retained history, request lookup, request IDs, telemetry, or post-hoc inspection of arbitrary past requests.

### Existing historical proof surface

The historical select-once explanation composition MUST NOT remain the semantic authority for modern ordinary-request explanation once this RFC is implemented.

Implementation MAY preserve historical proof helpers internally where still useful for tests or bounded compatibility, but user-facing wording MUST distinguish or retire any surface that would otherwise imply that the historical special composition explains the effective modern ordinary caller lifecycle.

No compatibility alias may silently preserve misleading semantics.

## Non-goals

This RFC does not introduce:

- distributed tracing;
- generic observability;
- an event bus;
- callbacks or plugin observers;
- retained request history;
- a database;
- request replay;
- health probing;
- topology discovery;
- scheduling;
- routing changes;
- fallback changes;
- execution-permission changes;
- a new failure taxonomy;
- a generic engagement model;
- a generalized lifecycle timeline;
- browser-owned routing or explanation logic;
- explanation of External Information acquisition;
- explanation of the complete workspace-aware Code interaction lifecycle.

## Required invariants

Implementation MUST preserve all of the following:

1. The request being explained is the request actually executed.
2. Ordinary orchestration remains authoritative for routing, permission, execution, continuation, fallback, and terminal failure.
3. Explanation facts are captured from the actual decision, never recomputed afterward.
4. `ExecutionIntervalCardinality.try_enter()` or equivalent state-changing permission checks are never repeated for explanation.
5. Safe continuation reasons are retained before ordinary control flow consumes them.
6. Existing ordinary results and exception semantics remain unchanged.
7. No explanation observer can influence execution.
8. No raw content, credentials, remote URLs, or raw configuration/runtime objects enter the account.
9. The account is request-scoped and non-retained.
10. No generic tracing/history surface is created.
11. Capability behavior remains engine-independent.
12. Image Generation follows the generic capability-centered rule rather than a special explanation architecture.

## Expected implementation shape

This section constrains implementation without prescribing detailed code structure.

The expected seam is the existing ordinary orchestration chain, especially the owner that currently composes:

- candidate discovery;
- automatic selection;
- execution permission;
- local execution;
- safe local-to-remote continuation;
- ordered declared-remote attempts;
- terminal result/failure.

Implementation SHOULD introduce the smallest internal request-scoped lifecycle-account representation that can retain already-authoritative facts at this seam.

It SHOULD prefer shared internal lifecycle truth over parallel explanation orchestration.

It MUST NOT copy the ordinary fallback algorithm into the explanation command.

It MUST NOT require broad instrumentation across unrelated execution layers merely to collect an account.

If implementation reveals that truthful explanation requires materially broader lifecycle instrumentation than established by this RFC, implementation MUST stop and return to architecture rather than silently expanding scope.

## User-facing semantics

The explicit explanation surface SHALL continue to answer the bounded question:

> What happened to this one actual request?

For modern ordinary execution, that means the account may explain, when applicable:

- what HAC initially selected;
- whether local execution permission allowed the local candidate to run;
- which candidate was actually attempted;
- whether ordinary execution continued to another candidate and the concrete accepted reason why;
- which candidate ultimately produced the result;
- or which existing terminal failure family ended the request.

It does not answer:

- what HAC might do for a hypothetical request;
- whether a node is healthy now;
- what happened to another process's request;
- the history of previous requests;
- every internal execution event.

## Acceptance proof

The implementation proof MUST demonstrate at least:

1. A local-success request produces the same ordinary result and an account derived from that same execution.
2. Local execution-permission denial followed by allowed remote continuation records the denial/continuation truth without re-running the permission check.
3. A local `RuntimeConnectionUnavailableBeforeRequestError` followed by allowed remote fallback records that concrete continuation reason from the actual branch.
4. A local failure that is not accepted for fallback remains terminal and does not produce a fabricated fallback event.
5. A direct declared-remote success attributes the candidate actually executed.
6. Ordered remote continuation after an accepted pre-engagement remote condition retains the consumed reason and subsequent attempted candidate.
7. Ordered remote exhaustion preserves existing terminal exception precedence while retaining only bounded consumed continuation facts.
8. `local_only` prevents remote continuation exactly as ordinary execution already does.
9. Existing execution-limit/cardinality behavior is unchanged by explanation.
10. An explanation path cannot explain the current cardinality state of a different already-running process merely by loading the same retained configuration.
11. Chat, Summarize, Classify, Code, and Image Generation participate through the same ordinary lifecycle seam where their current composition supports it.
12. External Information acquisition and the complete workspace-aware Code lifecycle remain outside the account.
13. No prompt/content, credentials, remote URLs, or raw configuration/runtime objects appear in the projected explanation.
14. Ordinary non-explained requests do not gain retained request history.
15. Existing ordinary success and failure semantics remain unchanged when explanation is not requested.

## Consequences

### Positive

- Actual-request explanation becomes truthful for modern ordinary caller execution rather than a historical proof composition.
- Fallback and execution-permission explanation reuse authoritative ordinary decisions.
- No second router or fallback engine is required.
- No generic tracing or persistence architecture is introduced.
- Privacy remains bounded and request-scoped.
- The explanation surface remains capability-centered and engine-independent.

### Negative

- Ordinary orchestration gains a bounded optional responsibility to retain explanation facts during an explicitly explained request.
- Some currently implicit control-flow truths need a small internal representation before they are consumed.
- Failure-path account retention must be implemented carefully so established exception ownership is not disturbed.

### Intentionally unresolved

This RFC does not decide:

- a generic public lifecycle-account schema;
- post-hoc lookup of completed requests;
- retained request history;
- distributed tracing;
- HTTP-disconnect explanation beyond current outer-boundary ownership;
- External Information acquisition explanation;
- workspace-aware Code interaction explanation;
- generic observability APIs.
