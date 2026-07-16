# RFC-0034: Structured Actual Request Failures

Status: Accepted

Date: 2026-07-16

Author: frian

## Summary

Home AI Cluster should extend the existing explicit local operator command:

```text
home-ai-cluster-explain-request
```

so that one invocation emits one structured JSON account for either a successful
actual request or a safely classified failed actual request.

The command should preserve the existing routing explanation produced by the same
automatic selection used for execution.

The first failed-outcome vocabulary should contain only:

- `no-selectable-candidate`;
- `runtime-unavailable`;
- `execution-failed`.

A structured failed outcome should be written to standard output and the process
should exit non-zero.

The command should remain local, explicit, request-scoped, prompt-free in its
output, and non-retained. It should not introduce request identifiers, timestamps,
history, retry, fallback, reselection, health-aware routing, or changes to ordinary
HTTP contracts.

## Problem

RFC-0032 established one truthful account for one successfully completed actual
request. The command executes one automatically routed request and returns:

- the routing explanation produced by that same selection; and
- the normalized successful `ClusterResult`.

When the request fails, the command currently emits only one safe human-readable
stderr message and exits non-zero.

The repository already owns useful structured evidence for some failures:

- `NoSelectableRoutingCandidateError` preserves the complete automatic routing
  explanation when no candidate can be selected;
- `RuntimeAdapterUnavailableError` represents a selected runtime adapter that
  cannot complete the request;
- unexpected execution exceptions can be safely normalized without exposing raw
  runtime details.

Without one stable failed-request projection, an operator cannot answer basic
questions such as:

- did routing fail before a candidate was selected?
- which node had been selected before execution failed?
- did the selected runtime report a known unavailable outcome?
- was the failure unexpected and therefore normalized?

Adding request history now would require request identity, retention, ordering,
concurrency, lifecycle ownership, access, and privacy decisions. The project needs
a smaller step first.

## Goals

This RFC should:

- extend the existing actual-request explanation command rather than add an
  overlapping command;
- preserve the existing successful routing and result account;
- return one structured JSON account for supported failed outcomes;
- preserve the routing explanation produced by the same selection used for
  execution;
- expose selected-node attribution when selection succeeded;
- distinguish no selectable candidate from known runtime unavailability and an
  unexpected execution failure;
- use stable cluster-owned reasons;
- keep raw exception, transport, URL, authorization, payload, stack-trace, and
  private machine details hidden;
- emit structured failure JSON to stdout;
- retain a non-zero process exit status for failed outcomes;
- remain local-only and use ordinary static local wiring for the first proof;
- leave `/v1/chat` and `/v1/chat/completions` unchanged.

## Non-goals

This RFC does not define or authorize:

- request identifiers;
- request history;
- retained request outcomes;
- prompt or response logging;
- timestamps or durations;
- a general request lifecycle model;
- a complete failure taxonomy;
- validation-error integration from the OpenAI-compatible edge;
- retry;
- candidate reselection;
- fallback changes;
- health-aware routing;
- aggregate node health changes;
- remote-node failure protocols;
- fallback-path attribution;
- adapter health probing during request execution;
- a database;
- a dashboard;
- metrics;
- tracing;
- an event bus or generic observability event abstraction;
- changes to `ClusterRequest` or `ClusterResult`;
- changes to ordinary distributed activation;
- changes to `/v1/chat`;
- changes to `/v1/chat/completions`.

## Proposal

### Extend the existing command

The existing command name should remain:

```text
home-ai-cluster-explain-request
```

The command should continue to accept the existing required arguments:

```text
--capability
--message
```

No new command-line options are required for the first proof.

The command should execute exactly one automatic selection and at most one selected
candidate execution attempt.

It should not retry, reselect, or invoke fallback.

### Top-level outcome contract

Every successfully constructed account should contain:

- `status`;
- `routing`;
- `result`;
- `failure`.

`status` should be either:

- `succeeded`;
- `failed`.

For a successful request:

- `result` should contain the existing normalized successful result projection;
- `failure` should be `null`;
- the process should exit zero.

For a failed request:

- `result` should be `null`;
- `failure` should contain one stable failed-outcome projection;
- the process should exit non-zero.

### Successful outcome

The successful contract should be:

```json
{
  "status": "succeeded",
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
  },
  "failure": null
}
```

This intentionally changes the existing top-level success shape by adding
`status` and `failure`.

The command is an explicit operator surface rather than an ordinary public API.
The change is acceptable because the new discriminated shape makes success and
failure machine-readable without ambiguous key presence.

### Routing projection

The `routing` object should preserve the existing RFC-0032 eight-field projection:

- `requested_capability`;
- `matched_candidate_families`;
- `selectable_candidate_families`;
- `excluded_candidate_families`;
- `selected_candidate_family`;
- `selected_node_id`;
- `outcome_rule`;
- `failure_reason`.

The projection must come from the same automatic selection used for the execution
attempt.

The command must not perform a second synthetic selection for explanation.

For `no-selectable-candidate`, the routing explanation preserved on
`NoSelectableRoutingCandidateError` should be projected directly.

For execution failures after selection, the routing explanation should retain the
selected candidate family and selected node id.

### Failed outcome vocabulary

The first `failure.status` vocabulary should contain exactly:

- `no-selectable-candidate`;
- `runtime-unavailable`;
- `execution-failed`.

These statuses are intentionally narrow. They are not a complete failure taxonomy.

#### `no-selectable-candidate`

Use this status when automatic capability selection produces no selected
candidate.

The failure projection should be:

```json
{
  "status": "no-selectable-candidate",
  "reason": "no selectable routing candidate"
}
```

The complete routing explanation should still be present. Its existing
`failure_reason` may provide the more specific cluster-owned selection reason.

No node, adapter, or model attribution should be invented.

#### `runtime-unavailable`

Use this status when selected-candidate execution raises
`RuntimeAdapterUnavailableError`, including its narrower
`RuntimeConnectionUnavailableBeforeRequestError` subtype.

The failure projection should be:

```json
{
  "status": "runtime-unavailable",
  "reason": "selected runtime adapter unavailable"
}
```

The first contract should not expose the pre-transmission subtype separately.
That distinction currently exists to support one narrow fallback proof and is not
yet justified as a general operator status.

The routing projection should identify the selected candidate family and selected
node id.

Adapter and model fields should not be added to the failed projection because no
successful `ClusterResult` exists and the selected routing explanation currently
owns node attribution, not a guaranteed runtime-model result.

#### `execution-failed`

Use this status when selection succeeded but selected-candidate execution raises
an unexpected exception not covered by `RuntimeAdapterUnavailableError`.

The failure projection should be:

```json
{
  "status": "execution-failed",
  "reason": "selected candidate execution failed"
}
```

The routing projection should identify the selected candidate family and selected
node id.

The raw exception message, type, traceback, transport details, URLs,
authorization values, payloads, and private machine details must not be exposed.

### Failed example: no selectable candidate

```json
{
  "status": "failed",
  "routing": {
    "requested_capability": "vision",
    "matched_candidate_families": [],
    "selectable_candidate_families": [],
    "excluded_candidate_families": [],
    "selected_candidate_family": null,
    "selected_node_id": null,
    "outcome_rule": "no-selectable-candidate",
    "failure_reason": "no-capability-match"
  },
  "result": null,
  "failure": {
    "status": "no-selectable-candidate",
    "reason": "no selectable routing candidate"
  }
}
```

The exact routing values must remain those produced by the existing selection
explanation model.

### Failed example: runtime unavailable

```json
{
  "status": "failed",
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
  "result": null,
  "failure": {
    "status": "runtime-unavailable",
    "reason": "selected runtime adapter unavailable"
  }
}
```

### Process output and exit behavior

When an account can be constructed, the command should emit exactly one compact
JSON object followed by one newline to stdout.

For `succeeded`, the process should exit zero.

For every structured `failed` account, the process should exit non-zero after
writing the JSON object.

No duplicate human-readable failure message should be written to stderr for a
structured failed account.

Argument parsing failures may continue to use the standard `argparse` stderr and
exit behavior because no cluster request account exists yet.

If the command cannot construct a safe structured account because of an internal
failure outside the supported selection and execution boundary, it may emit one
safe human-readable stderr message and exit non-zero without JSON.

### Privacy and safe reasons

The stable failed reasons should be exactly:

```text
no selectable routing candidate
selected runtime adapter unavailable
selected candidate execution failed
```

These strings are cluster-owned and must not include the original exception text.

The command output must not expose:

- the prompt or messages supplied through `--message`;
- runtime URLs;
- transport addresses;
- authorization values;
- raw HTTP payloads;
- exception messages;
- exception class names;
- stack traces;
- private machine details.

A successful result may continue to include generated response content because
that is already part of the accepted RFC-0032 result contract. Nothing should be
retained after process exit.

### First proof remains local-only

The first implementation should use the ordinary static local node and adapter
registries and an empty declared-remote registry, as the existing command does.

It should not accept remote addresses, activate distributed proof wiring, or add
remote failure semantics.

### Ordinary contracts remain unchanged

`POST /v1/chat` should remain unchanged.

The dedicated OpenAI-compatible process and `POST /v1/chat/completions` should
remain unchanged.

This RFC affects only the explicit local operator command.

## First implementation proof

A later implementation satisfies this RFC only if it demonstrates all of the
following:

1. `home-ai-cluster-explain-request` remains the command name.
2. Existing required arguments remain unchanged.
3. Exactly one automatic selection is performed.
4. At most one selected-candidate execution attempt is performed.
5. The same selection explanation drives the routing projection and execution.
6. Every constructed account has `status`, `routing`, `result`, and `failure`.
7. Successful accounts use `status: succeeded`, retain the existing result
   projection, set `failure` to null, and exit zero.
8. No-selectable-candidate accounts use the preserved routing explanation,
   `failure.status: no-selectable-candidate`, the stable safe reason, null result,
   and a non-zero exit.
9. Runtime adapter unavailable accounts use
   `failure.status: runtime-unavailable`, the stable safe reason, null result, and
   a non-zero exit.
10. The pre-transmission connection-unavailable subtype is not exposed as a
    distinct first-contract status.
11. Unexpected execution exceptions use `failure.status: execution-failed`, the
    stable safe reason, null result, and a non-zero exit.
12. Execution failures retain selected candidate family and selected node id from
    the routing explanation.
13. Failed accounts do not invent adapter or model attribution.
14. Structured failed accounts emit one compact JSON object and no duplicate
    stderr message.
15. Raw exception, URL, transport, authorization, payload, traceback, and private
    machine details are not exposed.
16. Prompt content is not included in the account.
17. No retry, reselection, fallback, or routing-policy change is introduced.
18. No request id, timestamp, duration, history, retention, database, metrics,
    tracing, or event abstraction is introduced.
19. `/v1/chat` and `/v1/chat/completions` remain unchanged.
20. Automated tests require no live runtime.
21. One explicit local success proof and one explicit local failure proof are
    performed without retaining sensitive evidence.

## Rationale

Extending the existing command keeps one clear answer to the operator question:

> What happened to this one actual request?

A separate failure command would duplicate request construction, routing,
execution, and projection responsibilities while explaining constructed failures
rather than the actual invocation.

A discriminated top-level outcome makes machine-readable use straightforward.
Callers can inspect `status` first, while `result` and `failure` remain explicit
and mutually exclusive.

Keeping the routing projection present on failures preserves the most valuable
trust evidence: what matched, what was selectable, what was selected, and why
selection failed when no candidate existed.

The three failed statuses correspond to distinctions already supported by current
architecture. They do not claim universal runtime progress, side-effect knowledge,
or a complete lifecycle.

A non-zero exit remains important for shell and automation semantics. Writing the
structured account to stdout still lets operators and tools inspect the failure
without treating it as process success.

## Alternatives considered

### Keep safe stderr only

This preserves the existing RFC-0032 success-only contract.

It is not selected because it hides structured routing evidence already available
for no-selectable-candidate and selected execution failures.

### Add a separate failed-request command

This avoids changing the existing successful output shape.

It is not selected because it adds an overlapping command and risks duplicated
selection and execution logic.

### Preserve the old successful top-level shape and add `failure` only on errors

This minimizes successful-output changes.

It is not selected because consumers would need ambiguous key-presence rules and
would not receive one discriminated outcome contract.

### Exit zero for structured failed accounts

This would mean that successfully producing JSON is command success.

It is not selected because the command executes an actual request, and a failed
request should remain a non-zero process outcome for scripts and operators.

### Expose the pre-transmission connection failure separately

This could distinguish a request known not to have been sent.

It is not selected for the first contract because that subtype currently exists
for one narrow fallback proof. Generalizing it would imply broader runtime-progress
semantics that are not yet established.

### Include adapter and model fields on failed execution

This could provide more attribution.

It is not selected because no successful normalized runtime result exists. The
current stable evidence supports selected node attribution through routing, but
not universal model attribution on failure.

### Begin request history now

This would address the remaining roadmap history outcome.

It is not selected because it requires identity, retention, ordering, concurrency,
access, lifecycle, and privacy decisions before the one-request failure shape is
proven.

## Trade-offs

The successful operator JSON shape changes by adding `status` and `failure`.
Existing ad hoc consumers of the command output may need adjustment.

The command remains purpose-specific rather than introducing a generic request
outcome or observability abstraction.

The failed status vocabulary is deliberately coarse. In particular, it does not
expose whether the runtime received or partially processed a request.

A structured failed account exits non-zero, so callers piping directly into other
tools must preserve or intentionally handle the original process status.

These costs are acceptable because the result is a truthful, minimal, and useful
request-scoped trust surface without retained state.

## Impact

Implementation should primarily affect:

- `home_ai_cluster.actual_request_explanation`;
- focused tests for its orchestration and CLI projection.

A small request-scoped internal outcome representation may be added only if needed
to preserve the same selection explanation across successful and failed execution.
It must remain specific to this accepted command behavior and must not become a
generic lifecycle abstraction.

The implementation should reuse:

- `AutomaticCapabilitySelectionExplanation`;
- `NoSelectableRoutingCandidateError`;
- `RuntimeAdapterUnavailableError`;
- `orchestrate_request_with_automatic_capability_explanation` or a narrowly
  adjusted same-selection orchestration seam;
- the existing routing projection vocabulary.

It should not require changes to:

- `ClusterRequest`;
- `ClusterResult`;
- candidate selection policy;
- adapter chat interfaces;
- fallback orchestration;
- remote transport;
- node health;
- `/v1/chat`;
- `/v1/chat/completions`.

Future RFCs may separately address:

- retained prompt-free request history;
- request identifiers;
- timestamps and durations;
- fallback-path attribution;
- remote-node failure semantics;
- compatibility-edge validation outcomes;
- more evidence-based failure categories.

## Open questions

The following remain open during review:

- Should the top-level successful status use `succeeded` or `success`?
- Should the failure object field be named `status` or `category`?
- Should compact JSON remain the only output formatting, consistent with current
  operator commands?
- Should the generic internal-account construction failure keep the current stderr
  string or receive a new stable safe message?

These questions must not broaden the RFC into request history, retry, fallback,
monitoring, or a general lifecycle model.

## Decision

Accepted as proposed on 2026-07-16.
