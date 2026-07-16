# Phase 7 Request Failure Visibility Investigation

Status: Investigation

Date: 2026-07-16

## Purpose

This document investigates the next smallest Phase 7 observability and trust
increment after the accepted and implemented actual-request routing explanation
and local node and adapter health snapshot.

The question is:

> What truthful failure information can Home AI Cluster expose for one actual
> request without introducing request history, retained state, a general failure
> taxonomy, or changes to ordinary request contracts?

This investigation does not select a command name, endpoint, response contract,
request identifier, persistence mechanism, or retry policy.

Any architectural decision requires a later RFC before implementation.

## Project boundaries

The investigation preserves the current project boundaries:

- local-first and privacy-first operation;
- capability-centered and engine-independent core concepts;
- ordinary application behavior remains local and static by default;
- distributed proof behavior remains explicit and opt-in;
- no database, dashboard, metrics platform, tracing system, or event bus;
- no prompt or response logging;
- no retained request history;
- no request identifiers;
- no new retry or fallback behavior;
- no health-aware routing;
- no changes to `/v1/chat` or `/v1/chat/completions`;
- agents may implement accepted decisions but do not create architecture implicitly.

## Current evidence

### Successful actual-request explanation

RFC-0032 introduced one explicit local operator command that executes one actual
automatically routed request and returns:

- the routing explanation produced by the same selection;
- the normalized successful `ClusterResult` produced by the selected candidate.

That command deliberately has a success-only stable JSON contract. When execution
fails, it exits non-zero with a safe human-readable error.

The implementation therefore proves request-scoped correlation for successful
selection and execution, but not a structured failed-request account.

### No selectable candidate

Automatic capability selection raises `NoSelectableRoutingCandidateError` when no
candidate can be selected.

The exception preserves the existing
`AutomaticCapabilitySelectionExplanation`, which can truthfully describe:

- requested capability;
- matched candidate families;
- selectable candidate families;
- excluded candidate families;
- absence of a selected candidate;
- outcome rule;
- failure reason.

This is the strongest existing structured failure evidence because it is already
cluster-owned, deterministic, capability-centered, and independent from runtime
implementation details.

### Runtime adapter failure

The shared adapter boundary currently exposes:

- `RuntimeAdapterUnavailableError`, meaning that a runtime adapter cannot complete
  a request;
- `RuntimeConnectionUnavailableBeforeRequestError`, a narrower subtype meaning
  that a runtime connection could not be established before the request was sent.

These exceptions are intentionally small. They do not yet form a complete request
failure taxonomy.

A runtime adapter may also raise other unexpected exceptions. Existing public and
operator surfaces translate failures safely rather than exposing raw transport,
URL, authorization, payload, stack-trace, or machine-specific details.

### Proof-only fallback evidence

The explicit RFC-0028 fallback path catches only
`RuntimeConnectionUnavailableBeforeRequestError`.

That narrow distinction matters because it proves that:

- the local candidate was selected first;
- the failure happened before request transmission;
- fallback was allowed only under the accepted proof conditions;
- the already discovered declared remote candidate was used;
- no general retry or reselection policy was introduced.

The current successful fallback result contains only final result attribution. It
does not expose the first failed candidate or the reason fallback was permitted.

This is useful evidence, but it belongs to explicit proof-only distributed
behavior rather than the ordinary local application.

### Compatibility-edge failures

The dedicated OpenAI-compatible process can reject malformed or unsupported input
before cluster routing.

Such failures are public-edge validation outcomes, not cluster routing or runtime
execution outcomes.

A future request-failure account must not collapse compatibility validation,
selection failure, and runtime execution failure into one ambiguous status.

## Failure stages that can be distinguished today

The current architecture can distinguish some stages without introducing new
instrumentation:

1. input rejected before cluster routing;
2. candidate discovery and selection completed with no selectable candidate;
3. one candidate was selected and execution began;
4. a runtime connection failed before request transmission;
5. a runtime adapter reported that it could not complete the request;
6. an unexpected execution failure occurred;
7. a narrow proof-only fallback was permitted and attempted;
8. final execution succeeded.

Not every stage has a stable cluster-owned projection today.

The architecture cannot yet truthfully provide a complete lifecycle timeline,
because it does not own:

- request identifiers;
- retained lifecycle records;
- timestamps or durations;
- a stable general failure-category vocabulary;
- universal knowledge of whether a runtime received or partially processed a
  request;
- generalized retry or fallback semantics;
- common ordinary and compatibility-edge lifecycle ownership.

## Operator questions that can be answered truthfully now

For one explicit automatically routed request, the system can potentially answer:

1. What capability and constraints were evaluated?
2. Which candidate families matched?
3. Which candidates were excluded and why?
4. Was a candidate selected?
5. Which node was selected when selection succeeded?
6. Did selection fail because no candidate was selectable?
7. Did a selected adapter report an unavailable execution outcome?
8. Was one known failure specifically a connection failure before transmission?
9. Was the failure unexpected and therefore safely normalized?

The system cannot yet truthfully answer in general:

1. Exactly how far every runtime processed a failed request.
2. Whether a request may have produced side effects.
3. How long each lifecycle stage took.
4. Whether the same failure happened recently.
5. How many requests failed over time.
6. Whether an unavailable runtime should automatically be retried.
7. Whether another candidate should be selected.
8. Whether a failure implies node-wide or continuous unavailability.

## Candidate small outcomes

### Candidate A: Document current failure boundaries only

Document existing exception meanings, safe-error surfaces, and known failure
stages without adding a new operator surface.

Advantages:

- no architectural risk;
- clarifies that selection failure, runtime unavailability, pre-transmission
  connection failure, and compatibility validation differ;
- prevents current exceptions from being mistaken for a complete taxonomy.

Limitations:

- does not improve the experience of understanding one failed request;
- leaves structured selection failure facts inaccessible from the actual-request
  command;
- does not materially advance Phase 7 failure visibility.

Assessment:

Useful as part of this investigation, but insufficient as the next implementation
increment.

### Candidate B: Extend the explicit actual-request command with a failed outcome

Extend the existing explicit local actual-request explanation surface so that one
invocation always produces one structured JSON account for either:

- successful selection and execution; or
- a safely classified failed outcome supported by current evidence.

The first failed contract could remain deliberately narrow:

- `no-selectable-candidate`, preserving the existing routing explanation;
- `runtime-unavailable`, when the selected adapter raises the existing normalized
  adapter-unavailable exception;
- `execution-failed`, for unexpected safely normalized execution failures.

A pre-transmission connection failure could remain represented as
`runtime-unavailable` unless a later RFC finds that the narrower distinction is
needed outside fallback semantics.

Advantages:

- directly improves trust for one actual failed request;
- reuses the existing request-scoped command and same-selection architecture;
- reuses existing routing explanation facts;
- requires no persistence, request id, timestamp, or history;
- can keep raw runtime details private;
- can be tested with fake adapters;
- does not require changes to ordinary HTTP contracts.

Limitations:

- creates the first stable cluster-owned failed-request projection;
- requires exact decisions about status names and safe reason handling;
- must decide whether process exit remains non-zero when structured JSON is
  successfully emitted;
- must not imply a complete lifecycle or general failure taxonomy;
- may make the existing command contract a success-or-failure outcome contract
  rather than success-only.

Assessment:

Recommended as the smallest truthful next increment.

### Candidate C: Add a separate failed-request proof command

Add another explicit command dedicated to constructed failure scenarios.

Advantages:

- leaves the accepted RFC-0032 command contract unchanged;
- can prove selection and runtime failure projections independently;
- keeps implementation narrow.

Limitations:

- explains constructed scenarios rather than the operator's one actual request;
- adds another command with overlapping routing and execution responsibilities;
- risks duplicating orchestration and projection logic;
- provides less real-request value than extending the existing actual-request
  surface.

Assessment:

Not recommended unless RFC review finds that changing the existing command's
failure behavior would be too disruptive.

### Candidate D: Expose fallback attribution

Add request-scoped metadata describing the first failed candidate, the accepted
pre-transmission failure, the fallback candidate, and the final result.

Advantages:

- closes a real explainability gap in the fallback proof;
- uses evidence already present in the proof-only orchestration path;
- requires no persistence.

Limitations:

- prioritizes proof-only distributed behavior over ordinary failure visibility;
- requires a stable execution-path or lifecycle projection;
- can accidentally generalize one narrow fallback into a retry abstraction;
- does not solve ordinary no-candidate or runtime failure visibility.

Assessment:

Useful later, but not the next smallest ordinary trust increment.

### Candidate E: Add bounded in-memory request history

Retain prompt-free metadata for successful and failed requests.

Advantages:

- directly addresses the remaining Phase 7 history outcome;
- could connect selection, execution, failure, fallback, and final attribution;
- could support later operator inspection.

Limitations:

- requires request identity, lifecycle ownership, retention, concurrency, access,
  ordering, failure taxonomy, and privacy decisions at once;
- risks introducing a premature event or tracing abstraction;
- is much larger than proving one structured failed-request account first.

Assessment:

Deferred. A stable one-request outcome should be proven before retaining many
outcomes.

## Recommended next architectural question

The recommended next question is:

> How should the existing explicit actual-request explanation command return one
> safe structured JSON account when automatic selection or selected-candidate
> execution fails, without introducing request history, request identifiers, a
> general lifecycle model, or changes to ordinary HTTP contracts?

A later RFC should compare and decide at least:

- extending `home-ai-cluster-explain-request` versus adding a separate command;
- the smallest stable failed-outcome status vocabulary;
- whether the full routing explanation is included for every failed outcome;
- how selected-node attribution is represented when execution fails;
- whether adapter and model attribution are omitted when no successful runtime
  result exists;
- whether structured failed JSON is emitted to stdout with a non-zero exit status;
- which safe reasons are stable and cluster-owned;
- whether `RuntimeConnectionUnavailableBeforeRequestError` remains an internal
  subtype or receives a distinct operator status;
- how unexpected exceptions are normalized without leaking details;
- whether the first proof remains local-only.

## Recommended boundaries for the RFC

The RFC should preserve:

- one explicit local opt-in request execution surface;
- same-selection routing explanation and execution;
- ordinary static local configuration only for the first proof;
- no prompt or response retention;
- no request identifiers;
- no timestamps or durations;
- no history or retained state;
- no database;
- no dashboard, metrics, tracing, or event abstraction;
- no retry, reselection, fallback, or routing-policy changes;
- no health-aware routing;
- no remote-node failure protocol;
- no changes to `/v1/chat` or `/v1/chat/completions`;
- no raw exception, runtime URL, transport, authorization, payload, or private
  machine-detail leakage;
- no claim that the first status vocabulary is a complete failure taxonomy.

## Deferred questions

The following remain unresolved:

- whether request identifiers belong in core requests, results, or an outer
  lifecycle;
- whether request outcomes should be retained;
- whether retention should be process-local or durable;
- what failure classes justify stable long-term categories;
- whether elapsed time belongs in a request outcome;
- whether compatibility-edge validation should share a cluster lifecycle model;
- whether runtime connection-before-transmission deserves a general public status;
- whether fallback paths need first-candidate failure attribution;
- whether failed requests should carry adapter or model attribution;
- whether future tools need machine-readable non-zero command output conventions;
- whether health observations should ever influence routing after failure evidence
  is better understood.

## Conclusion

Home AI Cluster now explains one successful actual request and exposes one truthful
local health snapshot. The next trust gap is one failed actual request.

The repository already owns enough evidence for a small first step:

- deterministic routing explanation facts;
- explicit absence of a selectable candidate;
- normalized runtime adapter unavailability;
- one narrower pre-transmission connection failure;
- safe exception translation boundaries.

The main architectural risk is not implementation complexity. It is inventing a
general lifecycle or failure taxonomy before the evidence justifies one.

The recommended next increment is therefore an RFC for a narrow structured failed
outcome on the existing explicit actual-request explanation surface. It should
remain request-scoped, local-only, prompt-free, non-retained, and independent from
ordinary HTTP contracts, retry policy, and monitoring infrastructure.
