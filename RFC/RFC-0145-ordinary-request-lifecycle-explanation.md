# RFC-0145: Ordinary Request Lifecycle Explanation

- Status: Draft
- Date: 2026-09-26

## Summary

HAC SHALL allow one explicitly requested actual-request explanation to describe the authoritative ordinary lifecycle of the same request that HAC actually executes.

The explanation SHALL be derived from bounded request-scoped facts already used by ordinary orchestration while making routing, execution-permission, continuation, fallback, and final-attribution decisions.

The explanation SHALL NOT reconstruct those decisions afterward, replay the request, probe candidate health, or run a second routing or fallback policy.

The explanation facts are request-scoped and non-retained. They are not generic tracing, history, telemetry, or observability.

## Motivation

RFC-0032 established an explicit actual-request explanation surface answering, in bounded form:

> What happened to this one actual request?

That proof deliberately selected once and executed once. RFC-0034 later added structured actual-request failures, and later accepted work added bounded execution-permission facts to the explanation account.

Those historical surfaces remain truthful for the special bounded composition they define.

Ordinary HAC request execution has since gained additional accepted semantics, including retained caller composition, execution permission, local-to-declared-remote continuation, ordered declared-remote fallback, and narrow pre-engagement conditions that permit safe continuation.

RFC-0145 therefore extends the actual-request explanation architecture for modern ordinary caller execution. It does not retroactively make RFC-0032 or RFC-0034 incorrect.

Current ordinary orchestration already knows the facts needed to explain its decisions while executing them. In particular, the ordinary fallback path knows the initial selected candidate, local execution-permission result, concrete conditions that permit or prohibit continuation, candidate-specific execution/contact facts, and final result or terminal failure.

The missing architecture is therefore not tracing. It is bounded request-scoped preservation of authoritative facts that ordinary execution already uses and would otherwise discard as control flow advances or stack frames unwind.

## Decision

### One ordinary execution owns both behavior and explanation

An actual-request explanation MUST be produced from the same ordinary orchestration invocation that executes the request being explained.

Explanation MUST NOT independently rediscover candidates, rerun automatic selection, recompute execution permission, reconstruct fallback decisions, or infer consumed continuation reasons after execution.

Ordinary orchestration remains the sole owner of routing and execution decisions.

Explanation is observational only.

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

### Bounded request-scoped lifecycle truth

Ordinary orchestration SHALL be able to preserve bounded request-scoped explanation facts for the request being explicitly explained.

Those facts SHALL contain only authoritative semantic truth already known while ordinary orchestration executes the request.

They MAY include, when they occur:

- requested capability and accepted request constraints relevant to routing;
- initial automatic selection and its existing bounded selection explanation;
- whether local execution permission was granted or denied;
- existing authoritative candidate-specific facts, such as selection, permission denial, adapter invocation, remote contact/refusal, or pre-transmission unavailability;
- a concrete accepted reason that allowed continuation to another candidate;
- corresponding facts for subsequent declared-remote candidates under accepted ordered fallback;
- final successful execution attribution;
- terminal failure semantics already authoritative at their existing owner.

This list defines semantic categories, not a required serialized schema or internal representation.

RFC-0145 does not define a new generic candidate `attempted` state. Implementations MUST preserve existing distinctions among selection, permission denial, adapter invocation, remote contact/refusal, pre-transmission unavailability, and execution where current architecture distinguishes them.

The explanation MUST NOT invent a generalized engagement state when current execution uses a narrower authoritative fact.

For example, safe continuation may be explained by the concrete accepted condition that actually authorized it, such as:

- local execution permission denied before local adapter invocation;
- `RuntimeConnectionUnavailableBeforeRequestError` before request transmission;
- the accepted receiver execution-permission refusal before receiver adapter invocation;
- another currently accepted narrow pre-engagement condition used by ordinary ordered fallback.

Such a reason MUST be preserved at the point ordinary orchestration consumes it. It MUST NOT be inferred later from the final result or final exception.

### Authority and representation

RFC-0145 decides ownership, lifetime, non-interference, and privacy. It does not prescribe one internal representation for explanation facts.

Implementation MAY use the smallest suitable bounded request-local mechanism, including richer internal outcomes, a request-local structure, or another private representation, provided that:

- ordinary routing and execution remain the sole authority for every recorded fact;
- ordinary routing and execution decisions remain unchanged;
- ordinary success results remain unchanged;
- established exception types, propagation semantics, and ownership remain unchanged;
- explanation collection cannot affect execution behavior;
- no second orchestrator or routing policy is introduced;
- no generic callback, event, middleware, plugin-observer, tracing, or telemetry architecture is created.

A narrowly request-scoped internal collection mechanism is not prohibited merely because it receives authoritative facts during execution. It MUST remain private to this bounded purpose and MUST NOT become a generic observer API.

User-facing explanation is a projection of authoritative ordinary-execution truth, not an independently produced account.

### Success, failure, and stack unwinding

A successful explained request SHALL preserve the ordinary normalized result and MAY project final execution attribution already accepted for that result family.

A failed explained request SHALL preserve ordinary terminal failure behavior.

Bounded request-scoped explanation facts MAY survive ordinary stack unwinding long enough for the explicit explanation surface to project them. This temporary survival remains request-scoped and non-retained.

The mechanism used to preserve those facts MUST NOT change the type, meaning, precedence, or semantic ownership of the established terminal exception.

RFC-0145 does not require a universal outcome wrapper or a unified core lifecycle failure taxonomy.

Where ordinary execution consumes a non-terminal failure or refusal in order to continue safely, the explanation facts MAY preserve the accepted semantic reason for that continuation.

For a terminal failure, explanation MAY project only semantics already authoritative at their existing owner. Existing surface-specific normalization remains owned by that surface unless separately changed by accepted architecture.

Raw exception text MUST NOT become lifecycle explanation data merely to provide additional detail.

### Fallback and continuation

Explanation MAY describe authoritative candidate-specific facts that actually occurred and concrete accepted reasons for continuation.

It MUST NOT expose hypothetical candidates that ordinary execution did not consider merely to make the explanation appear complete.

It MUST NOT evaluate fallback eligibility independently.

The same ordinary control flow that decides whether execution may continue is authoritative for explanation.

No generalized timeline is accepted by this RFC.

### Cancellation and HTTP disconnect

Core ordinary routing/execution lifecycle facts are in scope.

HTTP client-disconnect ownership currently exists at an outer HTTP execution boundary rather than inside the core ordered-fallback owner.

This RFC does not require moving cancellation ownership into the core lifecycle explanation or changing current cancellation semantics.

A future extension MAY decide whether an HTTP-surface explanation needs a bounded disconnect fact, but that is not required for this RFC's core proof.

### Capability scope

The architecture applies to ordinary single-request capability execution that already shares the ordinary capability-centered routing lifecycle, including:

- Chat;
- Summarize;
- Classify;
- Code;
- Image Generation.

This is an architectural applicability statement. It does not require identical internal/result representation for every capability family.

Source-grounded Chat may use the same lifecycle for the Chat request after evidence already exists.

This RFC does not make External Information acquisition part of ordinary request lifecycle explanation. Acquisition has separate higher-level authority, and evidence/source content MUST NOT enter the explanation through the subsequent Chat request.

This RFC also does not make the complete workspace-aware Code interaction part of the explanation. Individual ordinary Code inference requests may participate, but filesystem operations, repeated interaction, and workspace authority remain owned by the workspace-aware Code lifecycle.

### Privacy boundary

Explanation facts MUST remain request-scoped and non-retained.

They MUST NOT contain or expose:

- prompt or request content;
- source/evidence content;
- workspace/file content;
- credentials;
- remote URLs;
- raw retained configuration objects;
- raw adapter/runtime objects;
- raw remote declaration objects;
- generic topology snapshots;
- generic health/readiness state;
- raw exception text merely for explanation detail.

Minimal caller-owned node identity and existing result attribution MAY be projected where already necessary to explain which accepted candidate actually executed or which candidate-specific fact occurred.

Explanation MUST remain capability-centered and topology-minimal.

### Explicit explanation only

Request-scoped explanation-fact preservation is required only for an explicitly requested actual-request explanation path.

Ordinary requests that are not being explained MUST NOT be required to retain explanation history after completion.

This RFC does not introduce background recording, retained history, request lookup, request IDs, telemetry, or post-hoc inspection of arbitrary past requests.

Non-retained does not require explanation facts to disappear at the exact instant execution returns or raises. They MAY live only as long as necessary for the explicit explanation owner to render the result of that same request, then cease to be retained.

### Relationship to RFC-0032 and RFC-0034

RFC-0145 extends/amends the actual-request explanation authority established by RFC-0032 and RFC-0034 for the modern ordinary caller lifecycle.

The historical select-once/local-only proof remains valid for the bounded special composition those RFCs originally defined.

Once RFC-0145 is implemented, that historical special composition MUST NOT by itself be presented as the semantic authority for modern ordinary-request lifecycle explanation.

Implementation MAY preserve historical proof helpers internally where still useful for tests or bounded compatibility. User-facing wording MUST distinguish or retire any surface that would otherwise imply that the historical special composition explains the effective modern ordinary caller lifecycle.

No compatibility alias may silently preserve misleading modern semantics.

### Relationship to RFC-0035 bounded history

RFC-0035 remains unchanged.

RFC-0145 does not authorize retaining new continuation, fallback, candidate-specific lifecycle, or failure-path facts in bounded local request history.

Any RFC-0035 retained projection MUST continue to obey its existing field allowlist and retention semantics unless separately amended by future accepted architecture.

The temporary request-scoped explanation facts defined here MUST NOT automatically enlarge retained history.

## Non-goals

This RFC does not introduce:

- distributed tracing;
- generic observability;
- an event bus;
- generic callbacks or plugin observers;
- retained request history beyond existing RFC-0035 semantics;
- a database;
- request replay;
- health probing;
- topology discovery;
- scheduling;
- routing changes;
- fallback changes;
- execution-permission changes;
- a new failure taxonomy;
- a new generic candidate-attempt state;
- a generic engagement model;
- a generalized lifecycle timeline;
- browser-owned routing or explanation logic;
- explanation of External Information acquisition;
- explanation of the complete workspace-aware Code interaction lifecycle.

## Required invariants

Implementation MUST preserve all of the following:

1. The request being explained is the request actually executed.
2. Ordinary orchestration remains authoritative for routing, permission, execution, continuation, fallback, and terminal failure semantics it owns.
3. Explanation facts are captured from the actual decision or event, never recomputed afterward.
4. `ExecutionIntervalCardinality.try_enter()` or equivalent state-changing permission checks are never repeated for explanation.
5. Safe continuation reasons are preserved before ordinary control flow consumes them.
6. Existing ordinary results and exception type/meaning/precedence semantics remain unchanged.
7. Request-scoped explanation facts may survive stack unwinding only long enough for the explicit explanation owner to project the same request.
8. No explanation collection mechanism can influence execution.
9. No raw content, credentials, remote URLs, raw configuration/runtime objects, or raw exception text enter explanation merely for detail.
10. Explanation facts are request-scoped and non-retained.
11. No generic tracing/history/observer surface is created.
12. Capability behavior remains engine-independent.
13. Image Generation follows the generic capability-centered architectural rule rather than a special explanation architecture.
14. RFC-0035 retained history does not gain new lifecycle/fallback fields through this RFC.

## Expected implementation boundary

The expected authority is the existing ordinary orchestration chain that currently composes, as applicable:

- candidate discovery;
- automatic selection;
- execution permission;
- local execution;
- safe local-to-remote continuation;
- ordered declared-remote processing;
- terminal result/failure.

Implementation SHOULD introduce the smallest private request-scoped mechanism that can preserve already-authoritative facts at the appropriate owners.

The RFC intentionally leaves the exact internal representation open.

Implementation MUST NOT copy the ordinary fallback algorithm into the explanation command.

It MUST NOT require broad instrumentation across unrelated execution layers merely to collect explanation facts.

If implementation reveals that truthful explanation requires materially broader lifecycle instrumentation than established by this RFC, implementation MUST stop and return to architecture rather than silently expanding scope.

## User-facing semantics

The explicit explanation surface SHALL continue to answer the bounded question:

> What happened to this one actual request?

For modern ordinary execution, that means explanation may state, when applicable:

- what HAC initially selected;
- whether local execution permission allowed local adapter invocation;
- authoritative candidate-specific facts that occurred under existing semantics;
- whether ordinary execution continued to another candidate and the concrete accepted reason why;
- which candidate ultimately produced the result;
- or terminal failure semantics already owned by the relevant existing layer.

It does not answer:

- what HAC might do for a hypothetical request;
- whether a node is healthy now;
- what happened to another process's request;
- the history of previous requests;
- every internal execution event.

## Acceptance proof

The implementation proof MUST demonstrate at least:

1. A local-success request produces the same ordinary result and explanation facts derived from that same execution.
2. Local execution-permission denial followed by allowed remote continuation preserves the denial/continuation truth without re-running the permission check and without claiming local adapter invocation.
3. A local `RuntimeConnectionUnavailableBeforeRequestError` followed by allowed remote fallback preserves that concrete continuation reason from the actual branch.
4. A local failure that is not accepted for fallback remains terminal, preserves its existing exception semantics, and does not produce a fabricated fallback fact or require a new core failure classification.
5. A direct declared-remote success preserves the existing facts needed to attribute the candidate that actually produced the result.
6. Ordered remote continuation after an accepted pre-engagement remote condition preserves the concrete consumed reason and the existing authoritative facts for the subsequent candidate, without collapsing remote contact/refusal into adapter execution.
7. Ordered remote exhaustion preserves existing terminal exception type/meaning/precedence while making bounded consumed continuation facts available to the explicit explanation owner across stack unwinding.
8. `local_only` prevents remote continuation exactly where ordinary execution already does.
9. Existing execution-limit/cardinality behavior is unchanged by explanation.
10. An explanation path cannot explain the current cardinality state of a different already-running process merely by loading the same retained configuration.
11. Chat, Summarize, Classify, Code, and Image Generation are covered by the same architectural ownership rule where their current ordinary composition supports it, without requiring identical internal/result representation.
12. External Information acquisition and the complete workspace-aware Code lifecycle remain outside explanation; source/evidence content does not enter through source-grounded Chat.
13. No prompt/content, credentials, remote URLs, raw configuration/runtime objects, or raw exception text appear in projected explanation merely for detail.
14. Ordinary non-explained requests do not gain retained request history, and RFC-0035 history does not gain new lifecycle/fallback fields.
15. Existing ordinary success and failure semantics remain unchanged when explanation is not requested.

## Consequences

### Positive

- Actual-request explanation can describe modern ordinary caller execution while deriving from the same authoritative decisions.
- Fallback and execution-permission explanation reuse ordinary execution truth.
- No second router or fallback engine is required.
- No generic tracing or persistence architecture is introduced.
- Privacy remains bounded and request-scoped.
- The explanation surface remains capability-centered and engine-independent.
- Implementation remains free to choose the smallest private representation consistent with the architectural invariants.

### Negative

- Ordinary orchestration gains a bounded optional responsibility to preserve explanation facts during an explicitly explained request.
- Some currently implicit control-flow truths need to survive their branch, and failure-path facts may need to survive stack unwinding until the same request is rendered.
- Failure-path preservation must be implemented carefully so established exception ownership is not disturbed.

### Intentionally unresolved

This RFC does not decide:

- the private internal representation of request-scoped explanation facts;
- a generic public lifecycle-account schema;
- post-hoc lookup of completed requests;
- retained request history beyond RFC-0035;
- distributed tracing;
- HTTP-disconnect explanation beyond current outer-boundary ownership;
- External Information acquisition explanation;
- workspace-aware Code interaction explanation;
- generic observability APIs.
