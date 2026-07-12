# RFC-0027: Minimal Operator-Facing Routing Explanation

Status: Proposed

Date: 2026-07-12

Author: frian

## Summary

Home AI Cluster has deterministic internal routing explanation facts from
RFC-0025, but they are not yet visible to an operator. This RFC proposes one
explicit, local operator command, `home-ai-cluster-explain-routing`, that
constructs one `ClusterRequest`, discovers candidates, applies existing
constraints, and applies the existing automatic capability-selection policy.
It returns structured routing explanation facts and does not execute a selected
candidate.

The command is a separate operator surface, not an addition to ordinary
`/v1/chat`. It does not change routing policy, ordinary request execution,
`ClusterResult`, the RFC-0026 proof process, or the local-only default.

## Problem

Phase 4 has demonstrated the first automatic capability-selection increment
and a real two-machine proof. RFC-0025 also requires deterministic internal
facts about matching, selectability, selection, and no-selectable-candidate
outcomes. Those facts are useful for the roadmap's basic explanation outcome,
but they have no explicit operator-facing boundary.

Adding them to ordinary chat results would prematurely change a public response
contract and mix runtime results with cluster selection reasoning. Logging or
tracing them would create history, retention, and privacy questions. Doing
nothing leaves a routing decision inspectable only through implementation
internals.

The project needs the smallest explicit way for an operator to ask how the
cluster would route one request without causing model work or remote execution.

## Goals

- Expose the existing RFC-0025 deterministic routing explanation facts through
  one explicit operator-facing surface.
- Keep explanation separate from execution and from ordinary `/v1/chat`.
- Reuse existing exact capability matching, request constraints, selectability,
  selection, identity, and failure semantics.
- Return structured facts for selection and no-selection outcomes without
  prompt or response content.
- Preserve local-first, privacy-first, and engine-independent boundaries.
- Create a small, deterministic boundary that later implementation can test.

## Non-goals

This RFC does not introduce:

- a change to ordinary `/v1/chat` or its response shape;
- a change to `ClusterResult`;
- prompt or response logging, request history, a dashboard, a database, a
  tracing system, or a metrics platform;
- fallback, retry, health-aware routing, scoring, scheduling, or load
  balancing;
- dynamic discovery, registration, persistent configuration, or a general
  configuration format;
- authentication, authorization, trust, encryption, or transport policy;
- an OpenAI-compatible API;
- execution through the explanation surface;
- a change to RFC-0025 routing policy, RFC-0026 proof behavior, or ordinary
  application activation; or
- a declaration that Phase 4 is complete.

## Proposal

### Dedicated explicit command

Provide one dedicated local operator command:

```text
home-ai-cluster-explain-routing
```

The command is the sole operator-facing surface selected by this RFC. It is not
an HTTP endpoint, response header, daemon, or dashboard. One explicit
invocation supplies or constructs exactly one `ClusterRequest` within an
explicit operator-owned composition and returns one structured explanation to
the operator. The precise command argument and serialization syntax are an
implementation detail, but they must not become a general configuration,
selection-mode, or remote-permission interface.

The command may use the same static local registries and caller-owned
declared-remote registry available to an explicit RFC-0025 composition. A
declared remote remains static and declaration-based. Its existence, transport
address, or transport instance does not activate the command, ordinary routing,
or remote execution; the operator must invoke this command deliberately.

The conceptual operation is:

```text
explicit operator action
  -> construct ClusterRequest
  -> discover local and declared-remote candidates
  -> apply request constraints
  -> apply RFC-0025 automatic selection or report no selection
  -> return structured routing explanation
  -> do not execute a candidate
```

Ordinary application startup and ordinary `/v1/chat` remain local-only and do
not emit an explanation unless this separate command is invoked.

### Explanation-only operation

The command must stop after RFC-0025 selection. It must not:

- invoke a local adapter;
- invoke remote transport for execution;
- call Ollama or any other inference runtime;
- create a `ClusterResult`;
- retry, fall back, or select an alternative after an outcome;
- mutate registries, declarations, or node state; or
- contact a declared remote machine during declaration-based discovery.

No execution is safer and smaller than executing with an explanation. It has no
model side effects, causes no duplicate work, requires no execution retry or
fallback semantics, and keeps selection separate from execution. It also makes
the outcome deterministic and directly testable. This RFC does not solve how a
future mutable system might change between an explanation and a later request.

### Returned facts and privacy boundary

The command must reuse the explanation facts owned by RFC-0025 rather than
creating a second routing explanation model. Its structured result must expose
only the following minimum facts, expressed using the existing accepted
semantics:

- `requested_capability`;
- `matched_candidate_families` for local and declared-remote candidates;
- `selectable_candidate_families` after request constraints;
- `excluded_candidate_families`, including declared remote when `local_only`
  excludes it;
- `selected_candidate_family`, when selection succeeds;
- `selected_node_id`, when selection succeeds;
- `outcome_rule`; and
- `failure_reason`, when selection does not succeed.

The selected candidate family is derived from the existing selected candidate;
the remaining fields are direct representations or minimal groupings of
RFC-0025's existing deterministic facts. A no-matching-candidate or
no-selectable-candidate outcome must still return the facts available for that
outcome. It must not be converted into execution fallback.

The explanation must not contain prompt or message content, model output,
secrets, transport credentials, full transport URLs, runtime logs, request
history, scores, probabilities, latency estimates, model rankings, token
budgets, cost, load, historical statistics, or health-based recommendations.
The requested capability and routing facts are sufficient.

### Deterministic outcomes

The explanation command applies accepted RFC-0025 semantics without changing
them. It must return deterministic structured facts for at least these cases:

| Candidate state and constraint | Outcome |
| --- | --- |
| Local candidate only | Select local. |
| Declared-remote candidate only with `local_only=false` | Select declared remote. |
| Local and declared-remote candidates both selectable | Select local by fixed local precedence. |
| Declared remote matched with `local_only=true` and no selectable local candidate | Report no selection and the local-only exclusion. |
| No matching candidate | Report the no-matching outcome. |
| Matching candidates exist but none are selectable | Report the no-selectable-candidate outcome and its accepted reason. |

When a declared remote is selected, `selected_node_id` is the caller-owned
cluster identity, for example `declared-remote`. A transport URL or IP address
is neither authoritative node identity nor an explanation field.

### Compatibility boundary

This RFC exposes existing decisions; it does not revise them. In particular,
it preserves:

- RFC-0025 exact `Capability(name)` matching and its automatic selection
  policy;
- `local_only` as a hard restriction on declared-remote selection, contact,
  and execution;
- fixed local precedence when both candidate families are selectable;
- the accepted no-selectable-candidate behavior;
- exactly-once execution semantics by not entering execution at all;
- RFC-0026's dedicated proof-only automatic-routing process;
- the ordinary application's local-only behavior; and
- caller-owned node attribution for declared-remote selection.

## Rationale

This command is the smallest explicit surface that makes the cluster's
existing selection reasoning visible without exposing it on every ordinary
request. It satisfies the project preference for transparency over magic while
preserving the RFC-0005 boundary against unplanned ordinary response changes.

An explanation-only operation is narrower than a result-plus-explanation
operation. Execution would entangle the explanation surface with runtime side
effects, remote request movement, normalized results, error propagation, and
the already-deliberate no-retry/no-fallback boundary. RFC-0025 already keeps
selection and execution separate, so this proposal uses that boundary rather
than introducing another orchestration path.

A local command is smaller than a dedicated HTTP application: it adds no
listener, endpoint contract, daemon lifecycle, or network exposure. It follows
the repository's established use of explicit operator-owned processes for
narrow behavior while remaining distinct from the RFC-0026 execution proof.

## Alternatives considered

### Add explanation to the ordinary `/v1/chat` response

This would provide direct visibility, for example through a `routing` object
next to `content`, `adapter`, `model`, and `node_id`. It is rejected because it
changes the ordinary public response contract, mixes runtime result data with
routing explanation, raises compatibility expectations, and risks making the
ordinary application appear to activate automatic routing. It is broader than
the current evidence supports.

### Opt-in HTTP response headers

Headers would make a smaller-looking HTTP contract change, but they are a poor
fit for the structured matched, selectable, excluded, selected, and failure
facts. Encoding them creates size, serialization, discoverability, and testing
problems, while a reduced header set would be incomplete. This RFC therefore
does not select headers.

### Dedicated HTTP explanation application or endpoint

A dedicated application could return structured data, but it would add an HTTP
listener, endpoint contract, lifecycle, and deployment questions. The selected
local command is smaller for the immediate operator-facing need and avoids
network exposure.

### Execute a candidate and return a result plus explanation

Rejected because execution is unnecessary to explain the decision. It would
create model side effects, possible remote movement, duplicate work, and new
questions about execution failure, retry, and fallback.

### Logging, tracing, metrics, or a dashboard

Rejected because these create observability infrastructure, persistence or
history concerns, and privacy questions beyond one operator's explicit
one-request explanation.

## Trade-offs

This proposal makes deterministic selection reasoning directly visible without
changing ordinary request behavior or exposing prompts. It makes explanation
and execution two separate operations; a later execution may differ if future
work introduces mutable state. It produces no historical trace and does not
attach explanation directly to ordinary responses. It is not production
observability.

Those limits are acceptable because the goal is a small Phase 4 explanation
boundary, not an operational telemetry system or a general routing interface.

## Impact

If accepted, this RFC authorizes a later small implementation of one explicit
explanation-only operator command, its structured output, and focused tests.
It does not authorize changes to ordinary application wiring, routing policy,
runtime adapters, transport execution, result structures, or Phase 4 status.

Future implementation must keep this command opt-in and local, and must not
turn its input or output into persistent configuration, request history, or a
general remote-routing control plane.

## Acceptance criteria

Future implementation is acceptable only when all of the following are true:

- one explicit operator-facing invocation returns a structured explanation;
- no local adapter executes;
- no remote execution transport call occurs;
- no prompt content appears in the explanation;
- the six deterministic outcomes in this RFC are covered by tests;
- ordinary `/v1/chat` remains unchanged;
- existing tests remain green;
- new tests prove explanation-only behavior; and
- no fallback or retry is introduced.

## Open questions

- What smallest command input and output serialization best represents one
  `ClusterRequest` without becoming a configuration format?
- Which stable field names should a future implementation use while preserving
  the RFC-0025 facts exactly?
- Should a later RFC expose this same explanation through a different
  operator-facing surface after compatibility and privacy requirements are
  established?

## Decision

Pending.
