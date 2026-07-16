# RFC-0032: Actual Request Routing Explanation

Status: Accepted

Date: 2026-07-16

Author: frian

## Summary

Home AI Cluster should add one explicit, local, opt-in operator command that
executes one actual automatically routed request and returns a truthful JSON
account of both the routing decision and the final successful cluster result.

The first command should be:

```text
home-ai-cluster-explain-request
```

It should reuse the existing automatic capability-selection policy, the existing
selection explanation facts, the existing selected-candidate execution boundary,
and the existing normalized `ClusterResult`.

The command should not add request history, request identifiers, persistence,
prompt or response logging, a dashboard, metrics, tracing, or a new generic
observability abstraction.

It should be an explicit first Phase 7 proof that answers:

> What happened to this one actual request?

The ordinary `/v1/chat` contract and the dedicated OpenAI-compatible process
should remain unchanged.

## Problem

The Phase 7 investigation found that Home AI Cluster already has meaningful
observability and trust building blocks:

- final `node_id`, adapter, and runtime-model attribution on successful
  cluster-native results;
- deterministic automatic-selection explanation facts;
- an operator-facing routing explanation vocabulary;
- normalized safe failures;
- node and adapter health models;
- explicit privacy boundaries;
- narrow proof-only fallback evidence.

These facts are currently separated.

The existing `home-ai-cluster-explain-routing` command explains a constructed
selection scenario and deliberately stops before execution. It does not explain
an actual completed request.

Automatic orchestration already produces the routing explanation in memory, but
returns only the final `ClusterResult`. A user can therefore see which node,
adapter, and runtime model produced a result, but cannot obtain one coherent
request-scoped answer describing:

- which candidate families matched;
- which candidate families were selectable;
- which candidate families were excluded;
- which deterministic rule selected the node;
- which node was selected;
- which node, adapter, and model produced the final result.

Adding history immediately would require decisions about identifiers, retention,
concurrency, failure taxonomy, access, and privacy. Changing `/v1/chat`
immediately would broaden a central public contract before the smallest useful
shape has been proven.

The project needs a smaller step.

## Goals

This RFC should:

- expose the existing automatic routing explanation for one actual request;
- keep explanation and execution connected in one command invocation;
- reuse cluster-owned selection and execution boundaries;
- preserve deterministic, capability-centered, engine-independent explanation
  semantics;
- return final node, adapter, and runtime-model attribution;
- avoid prompt and response retention;
- avoid request history and request identifiers;
- avoid changing ordinary `/v1/chat`;
- avoid changing the OpenAI-compatible endpoint;
- remain explicit, local, and opt-in;
- define the smallest implementation proof without starting implementation.

## Non-goals

This RFC does not define or authorize:

- persistent or in-memory request history;
- request identifiers or cross-request correlation;
- prompt logging or response logging;
- database storage;
- a dashboard or web interface;
- metrics collection or export;
- distributed tracing;
- an event bus or generic observability event model;
- a node-status or health-view endpoint;
- health-aware routing;
- timing, latency, token, or resource accounting;
- changes to the routing policy;
- general retry or fallback behavior;
- ordinary application remote routing;
- changes to `POST /v1/chat` request or response shapes;
- custom observability fields in the OpenAI-compatible response;
- a general command framework;
- a stable long-term public observability API.

The first proof may expose a successful request only. Failure and fallback
explanation may require later RFCs because they introduce lifecycle and failure
semantics beyond the existing successful result contract.

## Proposal

### One explicit operator command

Add one explicit local command:

```text
home-ai-cluster-explain-request
```

The command should execute exactly one actual request through the existing
automatic capability-routing path and emit one JSON object to standard output.

It is an operator inspection surface, not an ordinary application endpoint.

It should remain opt-in and should not run as part of the normal FastAPI
application.

### Request input

The first proof should accept one capability and one plain user message.

An approximate command shape is:

```sh
home-ai-cluster-explain-request \
  --capability chat \
  --message "Hello"
```

The exact CLI parsing details are implementation details unless they change the
privacy or architectural boundary.

The command should construct the existing cluster-owned request concepts:

```text
ChatMessage
Capability
RequestConstraints
ClusterRequest
```

The request should use the same default privacy constraint as ordinary requests
unless an existing explicit proof process is reused to demonstrate declared
remote selection.

The command must not accept a node id, adapter name, runtime name, or runtime
model as a routing selector.

### Routing and execution flow

The command should use this conceptual flow:

```text
operator input
  -> ClusterRequest
  -> existing routing candidate discovery
  -> existing automatic capability selection
  -> existing AutomaticCapabilitySelectionExplanation
  -> existing selected-candidate execution boundary
  -> existing ClusterResult
  -> one explanation JSON projection
```

The command must not duplicate candidate matching, selection rules, adapter
calls, remote transport calls, or node attribution.

The selection explanation used in output must be the explanation produced for
the same selection whose candidate is executed.

The implementation must not perform a second synthetic selection after
execution merely to reconstruct an explanation.

### Successful output

On success, the command should emit one JSON object with two top-level sections:

```json
{
  "routing": {
    "requested_capability": "chat",
    "matched_candidate_families": ["local"],
    "selectable_candidate_families": ["local"],
    "excluded_candidate_families": [],
    "selected_candidate_family": "local",
    "selected_node_id": "local",
    "outcome_rule": "local-only",
    "failure_reason": null
  },
  "result": {
    "node_id": "local",
    "adapter": "ollama",
    "model": "llama3.2",
    "content": "..."
  }
}
```

The `routing` section should reuse the current RFC-0027 vocabulary and meanings:

- `requested_capability`;
- `matched_candidate_families`;
- `selectable_candidate_families`;
- `excluded_candidate_families`;
- `selected_candidate_family`;
- `selected_node_id`;
- `outcome_rule`;
- `failure_reason`.

The `result` section should project the existing successful `ClusterResult`:

- `node_id`;
- `adapter`;
- `model`;
- `content`.

The command must not invent timing, request identity, token usage, health status,
fallback status, or failure lifecycle fields.

### Result content and privacy

The response content is shown because the operator explicitly invoked a command
to execute one request and receive its answer. This is direct command output,
not logging or retained history.

The command must not:

- write prompt or response content to a file;
- retain prompt or response content after process completion;
- add default application logs containing prompt or response content;
- store the command input or output in repository evidence automatically;
- print runtime URLs, raw transport exceptions, authorization values, or private
  machine details.

Standard shell history and terminal capture are outside Home AI Cluster's
storage ownership, but documentation should avoid encouraging secrets in command
arguments.

A later implementation may choose standard input for message content if that is
a small implementation-level privacy improvement. This RFC does not establish a
general secret-input mechanism.

### Local and proof-only boundaries

The first implementation should support the smallest truthful local execution
proof.

A separate explicit proof invocation may reuse existing declared-remote proof
wiring to demonstrate an actual remote automatic selection, but this is not
required to change ordinary application behavior.

The command must not:

- activate distributed behavior in the normal application;
- discover machines dynamically;
- create persistent node membership;
- expose a listening observability service;
- require a dashboard or database.

### Failure boundary

The first implementation proof may limit the stable JSON contract to successful
execution.

Before a successful `ClusterResult` exists, the command should fail visibly with
a non-zero exit status and a safe error message.

It should preserve existing non-leaking exception boundaries and must not print
raw runtime URLs, raw HTTP payloads, prompt content, response content, or
transport internals.

This RFC does not define a stable JSON lifecycle model for:

- no selectable candidate;
- adapter unavailability;
- runtime failure;
- fallback use;
- fallback failure;
- compatibility validation failure.

Those cases need evidence before a cluster-owned request-lifecycle vocabulary is
accepted.

### No request identity or history

The command concerns one invocation and one request. Correlation is provided by
the process boundary itself.

It should not add a request id to `ClusterRequest`, `ClusterResult`, HTTP
responses, or logs.

It should not retain a last-request object, ring buffer, in-memory list, file,
or database record.

This preserves the option to design request identity and history later from
actual use rather than anticipation.

### Ordinary and compatibility surfaces remain unchanged

`POST /v1/chat` should remain unchanged.

The dedicated OpenAI-compatible process should remain unchanged and should not
receive custom routing fields.

The first Phase 7 proof belongs to a cluster-native operator surface, not to the
compatibility projection.

## First implementation proof

A later implementation satisfies this RFC only if it demonstrates all of the
following:

1. The command executes one actual request, not a synthetic explanation-only
   scenario.
2. Candidate discovery and automatic selection occur exactly once.
3. The explanation returned is the explanation from the same selection whose
   candidate is executed.
4. Exactly one selected candidate is executed on the successful non-fallback
   path.
5. Execution uses the existing selected-candidate orchestration boundary.
6. Runtime adapters remain responsible only for runtime-specific translation.
7. Node attribution remains cluster-owned.
8. The output uses the existing eight-field routing explanation vocabulary.
9. The result projection uses the existing `ClusterResult` values.
10. No request id, history, persistence, database, event stream, metrics, or
    tracing is introduced.
11. Prompt and response content are not logged or retained by default.
12. `/v1/chat` and `/v1/chat/completions` remain unchanged.
13. Ordinary automated tests require no live runtime.
14. One explicit local live-runtime proof succeeds and its retained evidence
    records only non-sensitive observations.

## Rationale

The Phase 7 investigation recommends actual-request routing explanation as the
smallest useful trust increment.

An explicit command is preferred for the first proof because it provides
request-scoped correlation without introducing request identity or retention.
It also avoids changing a central HTTP contract before the explanation shape has
been used on a real execution.

The command reuses already accepted architecture:

- capability-centered requests;
- candidate discovery;
- deterministic automatic selection;
- cluster-owned explanation facts;
- selected-candidate execution;
- normalized results;
- cluster-owned node attribution;
- runtime adapter boundaries;
- safe error translation.

This follows the project's established proof pattern: make the path explicit,
small, and opt-in before deciding whether it belongs in ordinary application
behavior.

The proposal is deliberately less ambitious than request history. It answers
one immediate user question without deciding how many requests should be
retained, how long they should live, or how concurrent requests should be
correlated.

## Alternatives considered

### Add routing explanation directly to every `/v1/chat` response

This would give immediate visibility to every cluster-native caller.

It is not selected for the first proof because it changes a central public
contract, forces optional-versus-required response semantics, and may broaden
ordinary local results before actual-request explanation has been proven useful.

A later RFC may choose this after the command establishes the truthful data
shape.

### Add an optional explanation flag to `/v1/chat`

This would preserve the default response while allowing opt-in explanation.

It is not selected because it still changes the public request and response
contracts and requires deciding how explanation is represented on failures.
The operator command provides a smaller proof boundary.

### Add a separate HTTP explanation endpoint

This could keep `/v1/chat` unchanged.

It is not selected because a second request would need correlation with the
executed request. That would pressure the project toward request ids or retained
last-request state before either is justified.

### Add a last-request inspection command

This could let an operator execute normally and inspect afterward.

It is not selected because it requires retention, concurrency semantics, and a
meaning for "last". One command invocation already provides correlation without
history.

### Add bounded in-memory request history first

This would serve more of the Phase 7 roadmap immediately.

It is rejected as the first increment because it combines request identity,
lifecycle, retention, concurrency, access, failure, and privacy decisions. It is
larger than necessary to explain one real request.

### Extend the existing explanation-only command to execute conditionally

This could reuse one command name with an execution flag.

It is not selected because explanation without execution and explanation of an
actual executed request have different safety and side-effect semantics. A
separate explicit command keeps those boundaries understandable.

## Trade-offs

The proposal adds another explicit command instead of immediately improving the
ordinary API.

That is acceptable because the first goal is to prove the smallest truthful
request-scoped explanation path.

The command output includes response content, which is sensitive by nature.
This is acceptable only because it is direct output requested by the operator,
not retained telemetry. The implementation and documentation must keep that
boundary explicit.

The first proof does not provide a stable structured failure explanation or
fallback account. This makes it incomplete as a full Phase 7 solution, but keeps
it from inventing lifecycle semantics prematurely.

The command may initially exercise proof-only automatic routing rather than
ordinary application routing. That is acceptable as long as the documentation
states the boundary and ordinary behavior is not broadened implicitly.

## Impact

This RFC affects a future explicit operator command and the internal composition
of existing automatic selection and selected-candidate execution values.

It should not require changes to:

- the accepted automatic selection policy;
- capability matching;
- runtime adapter interfaces;
- `ClusterRequest`;
- `ClusterResult`;
- `/v1/chat`;
- the OpenAI-compatible endpoint;
- node identity authority;
- ordinary application defaults.

Implementation may require one narrow internal outcome value that carries the
existing selection explanation alongside the existing successful result for the
duration of one call. Such a value must remain request-scoped and must not become
a generic event, history, or tracing abstraction.

Future RFCs may separately address:

- stable failure and fallback explanation;
- request identifiers;
- bounded metadata history;
- node and adapter health views;
- optional cluster-native API explanation;
- timing or resource metadata.

## Open questions

The following remain open during review:

- Should the first command accept the message through an argument, standard
  input, or both?
- Should the first proof be local-only, or should it also include one existing
  declared-remote automatic-routing proof invocation?
- Should successful output always include response `content`, or should a
  metadata-only output option exist?
- What should the safe human-readable error messages be before a stable failure
  JSON contract exists?
- Does implementation need a new narrow internal result type, or can existing
  orchestration composition expose both values without one?

These questions must not broaden the RFC into request history, lifecycle
tracking, or a general observability framework.

## Decision

Accepted on 2026-07-16.
