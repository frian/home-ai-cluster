# RFC-0028: Minimal Pre-Execution Candidate Fallback

Status: Accepted

Date: 2026-07-12

Author: frian

## Summary

Home AI Cluster should add the smallest explicit fallback behavior needed to complete the current Phase 4 roadmap outcome.

In one dedicated proof-only composition, RFC-0025 automatic capability selection first selects the local candidate through its existing fixed local precedence.

If, and only if, that selected local candidate reports a narrowly classified unavailability failure before useful execution may have begun, the orchestrator may execute the already discovered declared-remote candidate once.

This RFC satisfies the roadmap fallback outcome only for one explicitly defined
candidate-unavailability condition; it does not define general node
availability. Failure to establish a local runtime connection does not prove
that the machine or node itself is unavailable.

The fallback behavior is therefore:

```text
select local
  -> local reports unavailable before useful execution begins
  -> execute declared remote once
```

There is no retry of the local candidate, no fallback after ambiguous or potentially effective execution, no fallback from declared remote to local, no health probing, no loop, and no change to ordinary `/v1/chat`.

## Problem

The Phase 4 roadmap includes:

> fallback when a node is unavailable

For this increment, that roadmap wording is satisfied only by one explicitly
defined candidate-unavailability condition. It does not define general node
availability, node health, probing, or a conclusion that a machine is down.

The current accepted routing increment deliberately does not implement that outcome.

RFC-0025 discovers local and declared-remote candidates, applies request constraints, automatically selects exactly one candidate, and executes that candidate exactly once. An execution failure remains visible and does not cause retry or fallback.

That behavior was necessary to establish deterministic automatic selection without silently deciding resilience semantics.

The project now needs the smallest explicit answer to the following question:

> What should happen when the automatically selected local runtime connection
> cannot be established before request transmission can begin, while another
> already discovered and selectable candidate exists?

A broad fallback mechanism would introduce unresolved questions about retries, timeouts, health, duplicate execution, idempotency, ordering, and ordinary application activation.

This RFC must not solve those general problems.

## Goals

This RFC should:

* define one narrow meaning of fallback for the current two-candidate model;
* preserve RFC-0025 discovery, request constraints, and initial automatic selection;
* permit at most one fallback candidate;
* permit fallback only after a narrowly classified pre-execution unavailability failure;
* prevent fallback when execution may already have become effective;
* prevent retry of the initially selected candidate;
* preserve `local_only` as a hard restriction;
* preserve deterministic execution and attribution;
* keep the behavior inside a dedicated proof-only composition;
* allow a real two-machine proof; and
* require focused proof and test evidence that each allowed candidate attempt
  occurs at most once.

## Non-goals

This RFC does not introduce:

* fallback in ordinary `/v1/chat`;
* a general retry mechanism;
* retry of the same candidate;
* more than one fallback attempt;
* fallback from declared remote to local;
* fallback after a timeout with ambiguous execution state;
* fallback after an HTTP response status;
* fallback after an invalid response;
* fallback after runtime or model execution failure;
* fallback after partial or complete result production;
* health-aware routing;
* health probing;
* periodic reachability checks;
* dynamic availability;
* scoring, scheduling, load balancing, or performance routing;
* multiple local candidates;
* multiple declared-remote candidates;
* candidate rediscovery after failure;
* a generic resilience framework;
* queues, background workers, persistence, or execution history;
* idempotency keys or duplicate-execution recovery;
* changes to RFC-0027 or `home-ai-cluster-explain-routing`;
* changes to the ordinary public HTTP contract;
* configuration design; or
* production deployment behavior.

## Proposal

### Existing selection remains authoritative

Candidate discovery and initial selection remain governed by RFC-0025.

The proof-only composition discovers at most:

* one eligible local candidate; and
* one eligible manually declared remote candidate.

The existing automatic capability-selection policy is applied without modification.

When both candidates are selectable, RFC-0025 selects local through fixed local precedence.

Fallback must not change that initial selection decision.

It is an execution consequence of one narrowly classified failure, not a second routing policy.

### Fallback direction

This RFC permits only:

```text
local -> declared-remote
```

The initial local candidate must have been selected by RFC-0025.

The declared-remote candidate must:

* have been discovered before initial execution;
* have matched the same exact requested capability;
* have remained selectable after request constraints;
* not have been contacted before fallback; and
* still be the same caller-owned declaration used during initial discovery.

Fallback from declared remote to local is not defined.

Under the current RFC-0025 policy, declared remote is initially selected only when no local candidate is selectable. There is therefore no already discovered selectable local alternative in that outcome.

Defining broader directional fallback would require a later RFC.

### Request constraint

Fallback is allowed only when:

```text
request.constraints.local_only == false
```

When `local_only=true`, declared remote must not be selected, contacted, or executed, including as fallback.

An execution failure must never override the request privacy boundary.

### Pre-execution unavailability

Fallback is eligible only when the selected local execution boundary reports the dedicated semantic condition:

```text
candidate unavailable before useful execution began
```

This condition means the implementation can affirmatively determine that the selected candidate did not accept the request for useful runtime execution and did not produce a useful result.

It is a candidate-execution condition only. It is not general node
availability, does not establish node health, and does not prove that the
machine itself is unavailable.

The condition must be represented explicitly.

The orchestrator must not infer it from an arbitrary exception, generic timeout, error message, HTTP status, or broad exception hierarchy.

The first implementation may recognize only one concrete, narrowly proven adapter-side condition.

All unclassified or ambiguous failures remain ordinary visible failures without fallback.

### Eligible first implementation condition

For the first implementation and proof, the only eligible concrete condition
should be failure to establish the local runtime connection before request
transmission can begin.

The current broad `RuntimeAdapterUnavailableError` semantics are not sufficient
and must not be reused unchanged as the fallback trigger. The current Ollama
adapter maps every `httpx.HTTPError` to that error, including connection
failures, timeouts, HTTP status failures, and other ambiguous cases.

The implementation must introduce either a new narrow cluster-owned signal or
an explicitly refined outcome. Its only first allowed adapter mapping is
failure to establish the local runtime connection before request transmission
can begin. Every other case currently represented by
`RuntimeAdapterUnavailableError` remains a visible failure without fallback.

The core must depend only on the cluster-owned semantic signal.

It must not depend directly on Ollama, `httpx`, operating-system socket errors, or runtime-specific exception types.

The adapter translation is intentionally narrow.

It must not classify the following as safely unavailable:

* any timeout, including connection or read timeout;
* HTTP status errors;
* malformed or incomplete responses;
* connection loss after request transmission may have begun;
* runtime rejection;
* model loading failure;
* model execution failure;
* result normalization failure; or
* cancellation.

Those failures may be ambiguous or may occur after useful execution has begun.

They must remain visible without fallback.

### Execution rule

The fallback orchestration performs these steps:

```text
discover candidates once
  -> apply RFC-0025 automatic selection once
  -> execute selected local candidate once
  -> if execution succeeds:
       return its result
  -> if execution reports eligible pre-execution unavailability:
       execute the already discovered declared-remote candidate once
       return its result or visible failure
  -> for every other failure:
       return visible failure without fallback
```

The orchestration must not:

* rediscover candidates;
* rerun automatic selection;
* retry local;
* try remote more than once;
* return to local after remote failure;
* enter a loop; or
* execute candidates concurrently.

The maximum number of candidate execution attempts is two:

```text
one initial local attempt
+
one declared-remote fallback attempt
```

### Fallback candidate ownership

The fallback candidate is not newly selected after failure.

It is the one already discovered and selectable declared-remote candidate retained from the original RFC-0025 candidate collection.

This preserves the original request, capability match, request constraints, declaration, node identity, and operator-owned remote composition boundary.

The failure must not cause candidate rediscovery or policy reevaluation.

### Result attribution

If local execution succeeds, the existing local `ClusterResult.node_id` attribution remains authoritative.

If declared-remote fallback succeeds, the result must use the caller-owned declared remote node id:

```text
declared-remote
```

The result must not report the failed initial local candidate as the executing node.

The remote transport address remains transport metadata and must not become node identity.

### Failure behavior

If no fallback candidate was already discovered and selectable, the eligible local unavailability failure remains visible.

If declared-remote fallback execution fails, that failure remains visible.

There is no further fallback, retry, recovery, or masking.

The system must not return a successful local-looking result after remote fallback failure.

### Proof and test evidence

RFC-0027 remains a no-execution explanation of RFC-0025 selection and is unchanged.

Because fallback depends on execution, its facts do not belong in `home-ai-cluster-explain-routing`.

This RFC does not require a new execution-explanation object or stable
representation. Focused tests and the dedicated proof process must instead
provide the minimum deterministic evidence of:

* initial local selection;
* one local attempt;
* the narrow eligible pre-execution condition;
* one declared-remote fallback attempt;
* no rediscovery;
* no reselection;
* no retry; and
* final node attribution or visible failure.

This evidence must not log or persist prompt or response contents. It does not
authorize persistence, logging, tracing, metrics, or a change to
`ClusterResult`.

### Dedicated proof-only process

Implementation should begin with a dedicated proof-only process, separate from:

* the ordinary application;
* ordinary `/v1/chat`;
* `home-ai-cluster-static-proof`;
* `home-ai-cluster-automatic-proof`; and
* `home-ai-cluster-explain-routing`.

The proof composition should contain:

* one matching local `chat` candidate;
* one matching manually declared remote `chat` candidate;
* `local_only=false`;
* RFC-0025 automatic selection;
* local fixed precedence;
* one deliberately unavailable local runtime connection;
* one real remote machine with a working runtime;
* one operator-supplied remote transport address; and
* the narrow fallback orchestration defined by this RFC.

The expected proof is:

```text
caller Ubuntu
  -> proof-only /v1/chat
  -> discover local and declared-remote chat candidates
  -> RFC-0025 selects local by fixed precedence
  -> local runtime connection cannot be established
  -> adapter reports pre-execution unavailability
  -> declared-remote candidate executes once
  -> remote Ollama returns a normalized result
  -> ClusterResult.node_id = declared-remote
```

The ordinary application must remain unchanged and local-only.

## Rationale

This proposal satisfies the remaining Phase 4 roadmap outcome only for one
explicitly defined candidate-unavailability condition. It does not define
general node availability or a general resilience subsystem. Failure to
establish the local runtime connection does not prove that the node or machine
is unavailable.

It reuses the existing candidate collection and RFC-0025 initial selection rather than adding a second routing policy.

It permits only one directional fallback that can actually occur under the current fixed local-precedence rule.

It protects against duplicate execution by allowing fallback only for one narrow failure that is affirmatively known to precede useful runtime execution.

It preserves engine independence by requiring adapters to translate a specific runtime-side condition into a cluster-owned semantic signal.

It preserves privacy and user authority because `local_only` continues to prohibit all remote contact.

It remains understandable:

```text
Try the selected local candidate once.

Only when it definitely could not receive the request, try the already allowed remote candidate once.
```

## Alternatives considered

### Fallback for every local execution exception

Rejected.

Many failures are ambiguous. The request may have reached the runtime or useful execution may already have begun. Automatically executing another candidate could duplicate work.

### Fallback on timeouts

Rejected.

A timeout does not prove that execution did not begin. The runtime may still be processing the request.

Timeout fallback requires idempotency and duplicate-execution semantics that are outside this RFC.

### Retry the selected local candidate first

Rejected.

That would introduce retry policy, retry count, and timing semantics without helping prove candidate fallback.

### Re-run automatic selection after failure

Rejected.

Selection has already occurred. Re-running it would blur routing policy with execution recovery and could later make failure alter candidate ordering unpredictably.

### Rediscover candidates after failure

Rejected.

Dynamic rediscovery, availability updates, and health-aware routing are outside this increment.

### Permit remote-to-local fallback

Rejected.

Under RFC-0025, remote is selected only when no local candidate is selectable. Supporting this direction would require new discovery or selection semantics.

### Use health probing before selection

Rejected.

The roadmap gap is fallback, not health-aware routing. Probing introduces additional network activity, stale-state questions, and operational complexity.

### Activate fallback in ordinary `/v1/chat`

Rejected.

Remote request movement and automatic execution recovery should first be proven in an explicit operator-owned process.

### Add a generic retry or resilience abstraction

Rejected.

There is only one accepted fallback condition and one fallback direction. A general abstraction would be premature.

## Trade-offs

The proposed fallback handles only a small class of real failures.

A local request can still fail without fallback even when the remote candidate might have succeeded.

That limitation is deliberate.

The system prefers a visible failure over possible duplicate execution whenever it cannot prove that useful execution did not begin.

The adapter must translate one concrete failure into a cluster-owned semantic condition. This adds a small error boundary but keeps runtime-specific details outside the core.

The dedicated proof process adds another explicit entrypoint. This is acceptable because it prevents experimental fallback behavior from silently changing ordinary request movement.

## Impact

If accepted, this RFC authorizes:

* one cluster-owned pre-execution unavailability signal;
* one narrow adapter translation for the first proven condition;
* one fallback orchestration seam retaining the original candidate collection;
* one dedicated proof-only process;
* focused unit and integration tests;
* one real two-machine proof result document; and
* updates to the Phase 4 current-state and completion-assessment documents.

It does not authorize:

* ordinary application fallback;
* general retry behavior;
* general availability modeling;
* health-aware routing;
* additional fallback directions; or
* changes to the public API.

## Acceptance criteria

The RFC is implemented and demonstrated only when all of the following are true:

* ordinary `/v1/chat` remains unchanged and local-only;
* the fallback behavior requires a dedicated explicit proof process;
* one local and one declared-remote candidate match exact `Capability("chat")`;
* the proof request has `local_only=false`;
* RFC-0025 selects local through fixed local precedence;
* local execution is attempted exactly once;
* the local failure is only failure to establish the local runtime connection
  before request transmission can begin;
* the failure is translated through an adapter boundary into a new narrow
  cluster-owned signal or explicitly refined outcome, not the current broad
  `RuntimeAdapterUnavailableError` semantics reused unchanged;
* every other existing `RuntimeAdapterUnavailableError` case, including
  timeouts, HTTP status failures, and ambiguous failures, remains visible
  without fallback;
* the already discovered declared-remote candidate is executed exactly once;
* candidates are not rediscovered;
* automatic selection is not rerun;
* the local candidate is not retried;
* the remote candidate is not retried;
* no third execution occurs;
* successful fallback returns `node_id=declared-remote`;
* ambiguous failures do not trigger fallback;
* `local_only=true` prevents all remote contact and execution, including
  fallback;
* focused tests and the dedicated proof demonstrate initial local selection,
  one local attempt, the narrow eligible condition, one declared-remote
  fallback attempt, no rediscovery, no reselection, no retry, and final node
  attribution or visible failure;
* this RFC satisfies the roadmap fallback outcome only for the explicitly
  defined candidate-unavailability condition and does not define general node
  availability;
* no prompt or response contents are logged or persisted;
* a real two-machine fallback proof succeeds; and
* the proof result is recorded without claiming broader resilience behavior.

## Open questions

The following implementation details remain open:

* What should the cluster-owned pre-execution unavailability type be named?
* Should it be an exception or an explicit execution outcome?
* What is the smallest proof-only command name?
* What is the smallest operator-visible proof evidence needed in addition to the final result?
* Which existing module should own the narrow fallback orchestration seam?

These questions may be resolved during implementation only if they do not change the semantics defined by this RFC.

## Decision

Accepted.

Home AI Cluster will permit one proof-only fallback from an initially selected
local candidate to the already discovered and selectable declared-remote
candidate.

Fallback is allowed only when a narrow cluster-owned signal confirms that the
local runtime connection could not be established before request transmission
could begin.

The existing broad `RuntimeAdapterUnavailableError` semantics must not be reused
unchanged as the fallback trigger. Timeouts, HTTP status failures, ambiguous
transport failures, runtime failures, and every condition that may occur after
request transmission begins remain visible failures without fallback.

The initial RFC-0025 selection remains authoritative. Candidates are discovered
once, selection occurs once, the local candidate is attempted once, and the
declared-remote fallback candidate may be attempted once. There is no retry,
rediscovery, reselection, loop, concurrency, or further fallback.

`local_only=true` continues to prohibit all remote contact and execution.
Ordinary `/v1/chat` remains unchanged and local-only. Implementation must begin
through a dedicated proof-only process.

This decision satisfies the Phase 4 fallback roadmap outcome only for the
explicitly defined candidate-unavailability condition. It does not define
general node availability, health-aware routing, or general resilience.
