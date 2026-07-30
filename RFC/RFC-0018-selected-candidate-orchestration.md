# RFC-0018: Explicit Selected Candidate Orchestration

Status: Accepted

Date: 2026-07-08

Author: frian

## Summary

Home AI Cluster should define a narrow explicit opt-in orchestration boundary
for consuming an already selected routing candidate.

The project already has separate preparation steps for:

- declared remote eligibility;
- routing candidate discovery;
- routing candidate composition;
- explicit routing candidate selection.

This RFC proposes the next small boundary: how a caller-controlled
orchestration seam may execute a selected local or declared remote candidate
without re-running discovery, re-running selection, changing active
orchestration, or activating remote execution by default.

Discovery, selection, and execution remain separate. The active `/v1/chat` path
remains unchanged. `route_request(...)` remains unchanged. `RoutingDecision`
remains unchanged. This RFC does not activate remote routing or remote
execution.

## Problem

Home AI Cluster can now prepare and select routing candidates explicitly, but
there is no written boundary for how a future opt-in orchestration helper may
consume a selected candidate.

Without that boundary, future code could hide architecture inside an
implementation detail. It could accidentally re-run discovery, re-run
selection, call `route_request(...)`, choose a different candidate after
failure, or make remote execution look like default behavior.

The next architectural question is smaller than public routing behavior:

```text
Given an already selected candidate, how may an explicit opt-in caller execute
that selected candidate while preserving the existing boundaries?
```

Selected candidate orchestration needs to keep caller intent visible. A local
selected candidate should use the existing local execution boundary. A declared
remote selected candidate should require an explicit caller-provided
`RemoteTransport` before request contents may cross a transport boundary.

## Goals

This RFC should:

- define a minimal draft proposal for explicit selected candidate
  orchestration;
- keep candidate discovery, candidate selection, and execution separate;
- make the orchestration seam opt-in and caller-controlled;
- allow an already selected local candidate to execute through the existing
  local execution boundary;
- allow an already selected declared remote candidate to execute only through
  an explicit `RemoteTransport`;
- require explicit failure when a declared remote candidate is selected without
  a remote transport;
- avoid changing active `/v1/chat` behavior;
- avoid changing `route_request()`;
- avoid changing `RoutingDecision`;
- avoid changing active `orchestrate_request(...)`;
- avoid activating remote routing or remote execution by default;
- keep the proposal small enough to test without hidden policy.

## Non-goals

This RFC does not define:

- active `/v1/chat` remote routing;
- changes to `route_request()`;
- changes to `RoutingDecision`;
- changes to active `orchestrate_request(...)`;
- automatic candidate selection;
- automatic remote execution;
- retries;
- fallback after failed execution;
- health probing;
- discovery;
- registration;
- config loading;
- persistence;
- daemon-owned registry state;
- scoring;
- scheduling;
- performance-based routing;
- public API behavior;
- distributed behavior.

## Proposal

Home AI Cluster should define a small explicit orchestration boundary for
consuming an already selected routing candidate.

The boundary should be opt-in. It should not be called by the active
`/v1/chat` path unless a future RFC explicitly changes that behavior. It should
not replace `orchestrate_request(...)`.

One possible future helper shape is:

```python
async def orchestrate_request_with_selected_candidate(
    request: ClusterRequest,
    selected: SelectedRoutingCandidate,
    *,
    remote_transport: RemoteTransport | None = None,
) -> ClusterResult: ...
```

The exact implementation shape may vary, but the architectural boundary should
preserve these semantics.

### Local selected candidate

If the selected candidate is local, the helper should execute through the
existing local execution boundary.

Local selected candidate execution should not require `RemoteTransport`.

### Declared remote selected candidate

If the selected candidate is declared remote, the helper should require an
explicit caller-provided `RemoteTransport`.

Declared remote selected candidate execution should use the existing declared
remote execution boundary. The local orchestrator should not call a remote
node's runtime adapter directly.

If no `RemoteTransport` is provided for a declared remote selected candidate,
the helper should fail explicitly.

### Empty or invalid selection

If the selected candidate is empty, missing, or invalid, the helper should fail
explicitly.

The helper should not choose a different candidate on its own.

### Boundary behavior

The helper should not:

- re-run discovery;
- re-run selection;
- call `route_request(...)`;
- change `RoutingDecision`;
- execute another candidate after failure;
- retry through another candidate family;
- call remote transport unless a declared remote selected candidate is being
  executed and the caller provided `RemoteTransport`;
- activate remote routing or remote execution by default.

The selected candidate is the caller's explicit intent. The orchestration seam
consumes that intent; it does not create a new routing policy.

## Rationale

The project already separates candidate discovery and selection. Adding a
selected-candidate orchestration boundary preserves that separation when moving
from selected candidate to execution.

Without an explicit boundary, consuming selected candidates would become hidden
architecture. A future helper might accidentally blend discovery, selection,
execution, and fallback into one step. That would make the behavior harder to
review and harder to explain.

Requiring `RemoteTransport` for declared remote execution preserves privacy and
explicit data movement. Request contents should not cross a transport boundary
unless the caller intentionally provides the remote execution mechanism.

Not re-running discovery or selection keeps the seam small and testable. It
also prevents selected candidate orchestration from becoming a second router.

This keeps the current Phase 2 posture intact: fake in distribution, but not
fake in architecture. The project can prepare and test the boundaries that
future opt-in flows may need without pretending that active distributed routing
already exists.

## Alternatives considered

### Keep selected candidate orchestration undefined

The project could leave selected candidate consumption to future implementation
details.

That is rejected because the transition from selection to execution affects
privacy boundaries, caller intent, and routing behavior. The decision should be
visible before implementation.

### Re-run routing from the selected candidate helper

The helper could call `route_request(...)` internally and then execute the new
decision.

That is rejected because the helper's purpose is to consume an already selected
candidate. Re-running routing would blur discovery, selection, and execution
and could ignore the caller's selected candidate.

### Re-run selection inside orchestration

The helper could accept candidate collections and choose a candidate internally.

That is rejected for this boundary. RFC-0017 defines explicit selection as its
own step. Selected candidate orchestration should consume selection output, not
hide selection policy.

### Fall back to another candidate after execution failure

The helper could try local execution first and then remote execution, or remote
execution first and then local execution, after a failure.

That is rejected as premature and outside this RFC. Runtime fallback after
failed execution is a separate routing and execution policy decision.

### Wire selected candidate orchestration into `/v1/chat`

The project could make the active public chat route use selected candidate
orchestration.

That is rejected for this RFC. Public route behavior, default remote routing,
and default remote execution require separate architectural decisions.

## Trade-offs

Adding a selected-candidate orchestration boundary introduces one more small
concept in the Phase 2 routing and execution area.

That cost is acceptable because it keeps caller intent explicit and prevents
the transition from selection to execution from becoming implicit policy.

The proposed boundary deliberately does not solve fallback, scoring,
scheduling, health probing, config loading, discovery, or public API behavior.
Those omissions keep the seam boring and reviewable, but future RFCs may need
to address them before any active public routing behavior changes.

## Impact

If accepted, this RFC may affect future implementation of:

- explicit opt-in selected candidate orchestration helpers;
- selected candidate orchestration tests;
- Phase 2 current-state documentation.

It must not require changes to:

- `/v1/chat`;
- `route_request()`;
- `RoutingDecision`;
- active `orchestrate_request(...)`;
- active execution;
- config loading;
- discovery;
- registration;
- persistence;
- daemon lifecycle.

This RFC does not require production code changes by itself.

It does not require tests by itself.

It does not change current runtime behavior.

It does not activate remote routing or remote execution.

It does not introduce distributed behavior.

## Open questions

- What exact failure shape should represent a missing `RemoteTransport` for a
  declared remote selected candidate?
- Should the helper accept only `SelectedRoutingCandidate`, or should it accept
  a small wrapper that can represent no selection explicitly?
- Should selected candidate orchestration live near orchestration helpers,
  routing candidate helpers, or execution helpers?
- What future RFC should decide whether any selected candidate orchestration
  helper becomes part of an active public API path?

## Decision

Accepted.

Home AI Cluster will use a narrow explicit opt-in orchestration boundary for
consuming an already selected routing candidate.

The accepted boundary keeps candidate discovery, candidate selection, and
execution separate. It consumes caller-provided selected candidate intent; it
does not create a new routing policy.

For a local selected candidate, selected candidate orchestration may execute
through the existing local execution boundary and must not require a
`RemoteTransport`.

For a declared remote selected candidate, selected candidate orchestration must
require an explicit caller-provided `RemoteTransport` and must execute only
through the existing declared remote execution boundary.

The boundary must fail explicitly for missing or invalid selections, and for
declared remote selections without a caller-provided `RemoteTransport`.

The boundary must not re-run discovery, re-run selection, call
`route_request(...)`, change `RoutingDecision`, retry another candidate, or
fall back to another candidate after execution failure.

This decision does not change `/v1/chat`, does not change active
`orchestrate_request(...)`, does not change active execution, does not activate
remote routing, does not activate remote execution by default, and does not
introduce distributed behavior.
