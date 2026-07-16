# Phase 7 Observability and Trust Investigation

Status: Investigation

Date: 2026-07-16

## Purpose

This document investigates the current observability and trust state of Home AI
Cluster before any Phase 7 architectural decision or implementation.

It answers four questions:

1. What observability information already exists?
2. Where is that information available today?
3. What information is missing when trying to understand one real request?
4. What is the smallest useful Phase 7 increment without a database, dashboard,
   prompt logging, distributed observability system, metrics stack, or complex
   tracing?

This investigation does not select a persistence mechanism, logging format,
public API, command shape, storage policy, or final observability model.

Any architectural decision resulting from this investigation requires a later
RFC before implementation.

## Project boundaries

The investigation preserves the existing project boundaries:

- local-first operation;
- privacy by default;
- no prompt or response logging by default;
- capability-centered routing;
- engine-independent core models;
- ordinary application behavior that remains local and static by default;
- distributed proof paths that remain explicit and opt-in;
- boring, understandable solutions before infrastructure;
- no database, dashboard, telemetry platform, tracing system, or generic event
  abstraction without a demonstrated need.

The relevant Phase 7 roadmap goal is to make automatic decisions
understandable. The roadmap names request history without prompt logging,
routing explanation, node status, health view, failure visibility, and clear
privacy boundaries as expected outcomes. Several of those ingredients already
exist in narrower forms.

## Investigation method

The investigation reviewed the current repository shape, including:

- cluster request, runtime result, cluster result, node, health, and capability
  models;
- ordinary `/v1/chat` request handling;
- the explicit OpenAI-compatible process;
- local and declared-remote candidate discovery;
- automatic capability selection and its internal explanation facts;
- the operator-facing routing explanation command;
- selected-candidate orchestration and proof-only fallback behavior;
- runtime adapter health and error translation;
- node attribution;
- real two-machine, fallback, runtime-adapter, OpenAI SDK, and Aider proof
  records;
- focused tests and accepted RFC boundaries associated with those features.

## Current observability inventory

### 1. Request information

`ClusterRequest` currently contains:

- normalized chat messages;
- one requested capability;
- request constraints, including `local_only`;
- currently unused early constraints for fast-response preference and minimum
  context size.

This information exists in memory while a request is processed.

The ordinary public `POST /v1/chat` surface accepts only messages and a
capability name. It constructs the cluster-owned request internally and keeps
`local_only=true` in the ordinary path.

The dedicated automatic proof path constructs requests with
`local_only=false`, but only when that explicit proof process supplies its own
orchestrator.

There is currently no request identifier, start timestamp, completion
 timestamp, elapsed duration, or retained request record in the cluster-owned
request model.

### 2. Successful result attribution

Every successful `ClusterResult` contains:

- response content;
- adapter name;
- runtime model name when available;
- cluster-owned `node_id`.

This means the ordinary `/v1/chat` response already answers one important trust
question:

> Which cluster node produced this successful result?

The attribution is assigned at the selected-candidate execution boundary. It is
not supplied by runtime adapters and is not inferred from URLs or unverified
remote self-reporting.

For declared remote candidates, the authoritative identity is the
caller-owned declared node id.

This information is exposed directly to callers of the cluster-native endpoint.

### 3. Routing decision information in the ordinary local path

The ordinary local path builds a static local node registry and static runtime
adapter registry for each request. The existing local router selects a matching
node and adapter based on capability.

The local routing decision exists in memory and is consumed by orchestration,
but the ordinary public result does not expose a routing explanation object.

The public result exposes the final node, adapter, and runtime model, but not:

- which candidates were considered;
- which candidates matched;
- which candidates were excluded;
- which rule selected the final candidate;
- whether another candidate was available;
- whether a privacy constraint affected selection.

In the ordinary current application, this omission is less visible because the
default path has one static local node and no automatic remote routing. It still
matters conceptually because the result and the decision are separate facts.

### 4. Automatic routing explanation facts

The automatic capability-selection policy produces a dedicated internal
`AutomaticCapabilitySelectionExplanation` value.

It currently records:

- requested capability name;
- whether a local candidate matched;
- whether a declared remote candidate matched;
- whether each candidate family was selectable;
- whether `local_only` excluded the declared remote candidate;
- selected node id;
- deterministic outcome rule;
- no-selectable-candidate reason when selection fails.

The current outcome rules are:

- `local-only`;
- `local-precedence`;
- `declared-remote-only`;
- `no-selectable-candidate`.

The current no-selection reasons are:

- `no-matching-candidate`;
- `local-only-excluded-declared-remote`.

These facts are cluster-owned, deterministic, prompt-free, and engine-
independent.

They exist in memory during automatic selection. They are preserved on the
internal no-selectable-candidate error.

They are not included in the ordinary `/v1/chat` result and are not retained
after the request completes.

### 5. Operator-facing routing explanation command

The explicit `home-ai-cluster-explain-routing` command projects the automatic
selection facts to an eight-field JSON object:

- `requested_capability`;
- `matched_candidate_families`;
- `selectable_candidate_families`;
- `excluded_candidate_families`;
- `selected_candidate_family`;
- `selected_node_id`;
- `outcome_rule`;
- `failure_reason`.

The command deliberately stops before execution.

It uses static command-owned candidate descriptions and a placeholder message
that is neither operator input nor part of the output. It therefore explains a
constructed selection scenario, not the routing history of an actual completed
request.

This surface is useful and already demonstrates a stable, privacy-preserving
explanation vocabulary. It does not currently answer:

> What happened to the request I just sent?

### 6. Node status and health information

The cluster-owned node model already contains:

- node id;
- human-readable node name;
- availability with `available`, `unavailable`, or `unknown` values;
- node health with a boolean and optional reason;
- capabilities;
- adapter names.

The runtime adapter boundary separately exposes descriptive adapter health with:

- `available`;
- optional reason.

The Ollama and llama-server adapters implement health behavior behind the shared
adapter boundary.

However, the ordinary application currently uses a static local node
 description whose status is not a retained live status record. The node model
can represent status and health, but the ordinary application does not expose a
node-status or health-view surface.

The routing policy is also not health-aware. The existence of health fields must
not be confused with demonstrated live health-aware routing.

Proof and explanation processes may construct static healthy node descriptions
for their specific purpose. Those values are proof inputs, not continuous
observations of real machines.

### 7. Failure information

The current system has several useful failure boundaries.

The ordinary `/v1/chat` path translates runtime adapter unavailability to:

```json
{
  "detail": "Runtime adapter unavailable"
}
```

with HTTP 503.

It translates a missing matching adapter to HTTP 404 with the requested
capability name, while avoiding runtime URL and raw transport disclosure.

Runtime adapters normalize their own failures behind engine-independent
exceptions. A narrow cluster-owned
`RuntimeConnectionUnavailableBeforeRequestError` identifies one positively
known pre-transmission connection-establishment failure.

The RFC-0028 proof-only fallback path uses only that narrow signal. It does not
fallback for timeouts, HTTP failures, broad runtime errors, ambiguous failures,
or arbitrary exceptions.

The proof-only fallback orchestration demonstrates:

- one initial automatic selection;
- one local attempt;
- at most one declared-remote fallback attempt;
- no rediscovery;
- no reselection;
- no retry of either candidate;
- no third execution.

Failures are visible as immediate errors or proof outcomes. They are not retained
as request history.

The successful final result does not currently say that fallback occurred, which
candidate failed first, or which narrow failure triggered fallback.

### 8. Proof-process observability

The repository contains explicit proof processes and documents that expose or
record selected facts for narrow validation purposes.

Examples include:

- static two-machine routing proof;
- automatic capability-routing proof;
- routing explanation command;
- proof-only fallback process;
- second runtime-adapter proof;
- OpenAI-compatible endpoint proof;
- OpenAI SDK proof;
- Aider proof.

These proofs record useful evidence such as:

- HTTP success;
- selected `node_id`;
- adapter and model attribution;
- exact request fields observed at a compatibility boundary;
- whether unsupported routes or fields were absent;
- whether fallback completed;
- whether sensitive values and temporary dependencies were retained.

They are explicit, opt-in, and intentionally separate from ordinary application
behavior.

Proof documents are project evidence, not an operational request-history
mechanism.

### 9. OpenAI-compatible edge visibility

The dedicated compatibility process translates strict OpenAI-compatible chat
requests into the existing cluster-owned request flow.

Its public success projection deliberately omits cluster topology, adapter,
node, and routing fields. This preserves a narrow compatibility contract rather
than leaking internal cluster details into an external API shape.

The compatibility proofs can observe request fields at the test or proof edge,
but the compatibility process does not retain a request record and does not
provide a cluster observability surface.

This means the cluster-native endpoint and compatibility endpoint have different
public visibility by design:

- `/v1/chat` exposes final cluster attribution;
- `/v1/chat/completions` exposes only the accepted compatibility projection.

### 10. Privacy boundaries

The project has clear current privacy rules:

- prompts are not logged by default;
- responses are not logged by default;
- request content should not leave the local cluster unless explicitly allowed;
- ordinary requests are local-only by default;
- remote proof paths are explicit and opt-in;
- public errors avoid raw runtime URLs and transport details;
- proof records avoid retaining prompts, responses, bearer values, secrets, and
  private machine details;
- the compatibility endpoint binds only to loopback.

The current architecture therefore already demonstrates that useful routing and
failure metadata can exist without prompt or response retention.

## Where information is available today

| Information | Ordinary `/v1/chat` | OpenAI-compatible process | Explicit proof or operator command | Internal memory/code | Retained history |
| --- | --- | --- | --- | --- | --- |
| Requested capability | Request input | Derived as fixed chat capability | Routing explanation input and proof requests | Yes | No |
| Request constraints | Ordinary path fixes local-only | Compatibility flow preserves cluster defaults | Proof paths may explicitly allow remote | Yes | No |
| Successful node id | Yes | No | Yes in relevant proof results | Yes | Only in manually written proof records |
| Adapter name | Yes | No | Yes in relevant proofs | Yes | Only in manually written proof records |
| Runtime model | Yes when known | Compatibility identifier only, not runtime model | Yes in relevant proofs | Yes | Only in manually written proof records |
| Candidate match facts | No | No | Yes in explanation command | Yes for automatic selection | No |
| Candidate exclusion facts | No | No | Yes in explanation command | Yes for automatic selection | No |
| Selection rule | No | No | Yes in explanation command | Yes for automatic selection | No |
| No-selection reason | Public capability error is narrower and different | Compatibility error projection only | Yes in explanation command | Yes for automatic selection | No |
| Fallback occurrence | No | No | Demonstrated by fallback proof | Known during proof orchestration | No automatic history |
| Initial failed candidate | No | No | Visible through proof behavior and tests | Known transiently | No |
| Node availability and health fields | No public view | No | Static values in some proofs | Representable in models | No |
| Adapter health | No public view | No | Used by adapter proofs and tests | Available by direct call | No |
| Raw prompt or response logging | No | No | Explicitly avoided | Request content exists during processing | No |
| Request id | No | No | No stable cluster request id | No | No |
| Timing or duration | No | No | Sometimes manually observed in proof records | No standard model | No |
| Final status record | No | No | Manually documented proof result | No standard retained record | No |

## Normal path versus proof-only behavior

### Ordinary application

The ordinary application currently provides:

- one cluster-native endpoint;
- static local node and adapter registries;
- capability-based local routing;
- normalized successful results;
- final node, adapter, and runtime-model attribution;
- safe public errors;
- local-only request constraints by default;
- no retained request history;
- no node-status endpoint;
- no health view;
- no routing explanation attached to a real request.

### Explicit proof and operator paths

Explicit paths additionally demonstrate:

- declared remote candidates;
- automatic local or remote selection;
- deterministic explanation facts;
- operator-facing explanation without execution;
- one narrow local-to-remote fallback;
- real two-machine execution;
- two runtime adapters;
- compatibility-edge behavior;
- privacy-conscious proof recording.

These capabilities are not ordinary application defaults and must not be
presented as a general operational observability system.

## What is missing for understanding one real request

The main gap is not absence of all observability data. The main gap is absence of
one request-scoped account that joins the facts already produced at different
stages.

For one real request, a user currently cannot obtain one coherent answer to all
of these questions:

1. What capability and privacy constraint did the cluster evaluate?
2. Which candidate families matched?
3. Which candidates were excluded and why?
4. Which selection rule was applied?
5. Which node was initially selected?
6. Did execution succeed immediately?
7. Did a narrow fallback occur?
8. If fallback occurred, which candidate failed first and why was fallback
   permitted?
9. Which node, adapter, and runtime model produced the final result?
10. Did the request fail before selection, during selection, before transmission,
    during runtime execution, or at the public compatibility edge?

The current code can answer subsets of these questions in different places, but
not as one real-request view.

### Missing correlation

There is no request id shared across:

- public request handling;
- candidate discovery;
- selection;
- execution;
- fallback;
- result or failure.

Without correlation, even a future in-memory history cannot distinguish nearby
requests reliably.

Introducing a request id would be an architectural decision because it affects
core request/result or request-lifecycle semantics. It therefore requires an
RFC before implementation.

### Missing lifecycle outcome

The system has normalized successful results and normalized exceptions, but no
cluster-owned request-lifecycle summary.

There is no stable value representing, for example:

- selected and succeeded;
- no selectable candidate;
- selected but runtime unavailable;
- fallback used and succeeded;
- fallback candidate failed;
- compatibility validation rejected before cluster routing.

A future lifecycle summary must avoid collapsing distinct safe failure classes
or exposing runtime-specific details.

### Missing real-request explanation

The existing explanation command explains a synthetic selection scenario before
execution. It does not explain the completed routing of an actual request.

The automatic orchestration path already has explanation facts in memory. The
smallest useful trust improvement may therefore be to preserve and expose those
facts for the same actual request, without adding a general history mechanism.

That remains an architectural choice because it affects result or operator
surface contracts.

### Missing fallback attribution

The fallback proof knows both the original and fallback candidate and catches one
narrow failure. The final successful `ClusterResult` contains only the final
node attribution.

That is truthful but incomplete for explaining the decision path. A user cannot
see from the result alone that:

- local was selected first;
- local connection establishment failed before request transmission;
- the already discovered declared remote candidate was used;
- no retry or reselection occurred.

### Missing live status view

Node and adapter health models exist, but there is no ordinary operator surface
that reports the current static node description and adapter health.

A future health view must distinguish:

- declared metadata;
- directly probed adapter health;
- last observed health;
- routability;
- continuous availability.

The current implementation proves only some of those concepts. A simple view
must not overstate static declarations as live truth.

### Missing retained request history

There is no automatic request history.

The Phase 7 roadmap explicitly expects request history without prompt logging by
default. Implementing history immediately would force unresolved decisions
about:

- what constitutes a request record;
- record identifiers;
- in-memory versus durable retention;
- retention limits;
- process restarts;
- concurrent access;
- failure taxonomy;
- public or operator access;
- compatibility-edge visibility;
- redaction and privacy guarantees.

Those decisions are larger than the smallest useful trust increment and should
not be smuggled into an implementation without an RFC.

## Candidate small Phase 7 outcomes

The following are investigation candidates, not accepted decisions.

### Candidate A: Document the existing observability contract only

Produce a stable documentation record describing current fields, surfaces, and
privacy boundaries, without implementation changes.

Advantages:

- zero architectural risk;
- clarifies that attribution, explanation facts, health models, and safe errors
  already exist;
- prevents Phase 7 from being treated as a blank slate;
- exposes the distinction between model capability and operational exposure.

Limitations:

- does not improve the experience of understanding a real request;
- does not satisfy request history, node status, or health-view outcomes;
- leaves the most useful existing explanation facts disconnected from execution.

Assessment:

Useful as the current investigation result, but insufficient as the first Phase
7 implementation increment.

### Candidate B: Expose routing explanation for one actual request

Preserve the automatic selection explanation already produced for one real
request and expose it through one narrow cluster-owned surface.

Possible surface choices are deliberately not selected here. They could include
an explicit operator command, an optional cluster-native response projection,
or another small local-only inspection seam.

Advantages:

- directly serves the Phase 7 goal of understandable automatic decisions;
- reuses existing deterministic explanation facts;
- requires no database;
- requires no prompt or response logging;
- remains engine-independent;
- can stay local and in memory;
- can distinguish matched, selectable, excluded, selected, and failed selection
  outcomes.

Limitations:

- requires a decision about the surface and lifecycle of the explanation;
- may require joining selection facts with execution outcome;
- does not by itself provide request history;
- does not expose node health;
- requires an RFC before implementation.

Assessment:

This is the smallest candidate that materially improves trust for an actual
request while reusing proven architecture.

### Candidate C: Add a read-only current node and adapter health view

Expose the currently configured node description plus direct adapter health
through one local-only operator surface.

Advantages:

- addresses node status and health-view roadmap outcomes;
- can remain static and in memory;
- uses existing node and adapter-health models;
- requires no database or dashboard.

Limitations:

- static node availability and direct adapter health have different meanings;
- could easily overstate a declaration as live node status;
- does not explain an actual routing decision;
- remote proof nodes do not yet have a general live health model;
- may create pressure for polling, caching, timestamps, and status history.

Assessment:

Potentially useful, but semantically riskier than it first appears. It should
follow a precise RFC that defines what is observed rather than inferred.

### Candidate D: Add bounded in-memory request metadata history

Retain a small process-local history containing no prompts or responses.

A possible future record might include request id, capability, privacy
constraint, selection outcome, final node, adapter, model, failure category,
fallback use, and timing.

Advantages:

- addresses the request-history roadmap outcome directly;
- could join routing, result, fallback, and failure facts;
- can avoid a database and prompt logging;
- could provide a foundation for later operator views.

Limitations:

- introduces multiple architectural decisions at once;
- requires request identity and lifecycle semantics;
- requires retention and concurrency rules;
- requires a failure taxonomy;
- risks becoming a premature generic event or tracing abstraction;
- makes privacy claims dependent on exact record contents;
- may be larger than necessary before a real-request explanation surface is
  proven useful.

Assessment:

Valuable later, but too broad for the first Phase 7 increment.

### Candidate E: Extend successful results with fallback and lifecycle metadata

Add cluster-owned metadata indicating whether fallback occurred and summarizing
execution outcome.

Advantages:

- closes a real explainability gap in the fallback proof path;
- requires no persistence;
- can remain request-scoped;
- can avoid sensitive content.

Limitations:

- changes a central public result contract;
- affects ordinary, remote, and compatibility projections differently;
- requires a stable lifecycle and failure vocabulary;
- could prematurely couple Phase 7 to proof-only fallback behavior;
- still would not explain candidate matching and exclusion.

Assessment:

Useful but narrower than Candidate B in one dimension and broader in API impact.
It should not be the first choice without evidence that fallback attribution is
the most urgent user problem.

## Comparison

| Candidate | Real-request value | Architectural surface | Persistence | Privacy risk | Scope size |
| --- | --- | --- | --- | --- | --- |
| A. Documentation only | Low | None | None | Very low | Very small |
| B. Actual-request routing explanation | High | Narrow but must be decided | None required | Low | Small |
| C. Current node and adapter health view | Medium | New operator surface and semantics | None required | Low | Small to medium |
| D. Bounded in-memory request history | High | Request identity, lifecycle, retention, access | Process-local | Medium if record scope drifts | Medium to large |
| E. Result lifecycle and fallback metadata | Medium to high | Core public result contract | None required | Low | Medium |

## Recommended smallest next increment

The recommended next architectural question is:

> How should Home AI Cluster expose the routing explanation already produced for
> one actual automatically routed request, without retaining prompt or response
> content and without introducing request history yet?

Candidate B is recommended as the smallest useful Phase 7 increment.

The recommendation is based on current evidence:

- automatic selection already produces deterministic explanation facts;
- those facts are cluster-owned, capability-centered, engine-independent, and
  prompt-free;
- an operator-facing JSON vocabulary has already been proven separately;
- the missing value is correlation with an actual request and execution path;
- no database, dashboard, metrics stack, tracing system, or prompt logging is
  required;
- the increment directly advances the Phase 7 goal of making automatic
  decisions understandable.

The recommendation does not decide the exposure mechanism.

A later RFC should compare at least:

- an explicit local operator inspection command;
- an optional cluster-native explanation response mode;
- a narrowly separate cluster-native explanation endpoint;
- an in-memory last-request inspection seam, if correlation cannot be achieved
  without minimal retention.

The RFC should preserve these boundaries:

- no prompt or response retention;
- no database;
- no general event bus;
- no distributed tracing;
- no metrics platform;
- no dashboard;
- no change to routing policy;
- no activation of proof-only remote behavior in the ordinary application;
- no topology leakage through the OpenAI-compatible public projection unless a
  separate future decision explicitly requires it;
- no claim that static declarations equal live health;
- no generic request-history design in the first increment.

## Deferred Phase 7 questions

The following remain deliberately unresolved:

- whether request ids belong in core requests, results, or an outer lifecycle;
- whether any request metadata should be retained;
- whether retention should be process-local or durable;
- how many records would be retained and for how long;
- whether failed requests receive node attribution;
- how fallback paths should be represented;
- whether elapsed time is useful and where it should be measured;
- what constitutes node status versus adapter health;
- whether health should be probed on demand or observed during normal work;
- whether compatibility clients should ever receive cluster explanation data;
- what operator surface should expose current or historical information;
- what stable failure taxonomy is justified by evidence.

## Conclusion

Home AI Cluster already contains meaningful Phase 7 building blocks:

- final node attribution in successful cluster-native results;
- adapter and runtime-model attribution;
- explicit internal automatic-selection explanation facts;
- a proven operator-facing routing explanation vocabulary;
- node and adapter health models;
- safe error translation;
- a narrowly explainable proof-only fallback path;
- clear local-first and privacy-first boundaries;
- proof documents that distinguish observed behavior from broader claims.

What is missing is not raw information everywhere. What is missing is a small,
truthful, request-scoped way to connect routing facts to one actual request.

The smallest recommended next increment is therefore to define, through a
separate RFC, how an actual automatically routed request can expose its existing
routing explanation without prompt logging, persistent history, or observability
infrastructure.
