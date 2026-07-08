# RFC-0017: Explicit Routing Candidate Selection

Status: Accepted

Date: 2026-07-08

Author: frian

## Summary

Home AI Cluster should define a narrow explicit opt-in selection boundary for
choosing between already-discovered routing candidates.

The current implementation can expose:

- a local adapter-backed candidate;
- a declared remote candidate.

This RFC proposes a small caller-controlled selection mode for a future explicit
helper. It does not define a final routing policy for the whole project.

Candidate discovery, candidate selection, and execution remain separate steps.
The active `/v1/chat` path remains unchanged. The existing local
`route_request(...)` path remains unchanged. `RoutingDecision` remains
unchanged. This RFC does not activate remote routing or remote execution.

## Problem

Home AI Cluster now has explicit routing candidate preparation.

The current implementation can discover local and declared remote candidates
side by side without choosing between them. That keeps the local
adapter-backed routing path separate from declared remote eligibility.

The next architectural question is smaller than active routing:

```text
Given already-discovered candidates, how may an explicit opt-in caller choose
which candidate family to select?
```

If this boundary is not written down first, future implementation could hide a
routing policy inside code. That would make it harder to review whether the
caller intended local-only behavior, declared-remote-only behavior, or a
deterministic preference between available candidate families.

Selection also needs to remain separate from execution. Selecting a declared
remote candidate must not imply that remote execution is active in the default
path, wired into `/v1/chat`, or automatic.

## Goals

This RFC should:

- define a minimal draft proposal for explicit routing candidate selection;
- keep candidate discovery and candidate selection separate;
- keep candidate selection and execution separate;
- make selection opt-in and caller-controlled;
- support local adapter-backed candidates and declared remote candidates;
- avoid changing active `/v1/chat` behavior;
- avoid changing `route_request()`;
- avoid changing `RoutingDecision`;
- avoid activating remote routing or remote execution;
- keep the proposal small enough to implement and test without hidden policy.

## Non-goals

This RFC does not define:

- active `/v1/chat` remote routing;
- changes to `route_request()`;
- changes to `RoutingDecision`;
- remote execution;
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
- a final routing policy for the whole project;
- public API behavior;
- distributed behavior.

## Proposal

Home AI Cluster should define a tiny explicit selection mode for future
opt-in candidate selection.

The selection input is an already-discovered candidate collection, such as the
current `RoutingCandidates` shape:

- optional local candidate;
- optional declared remote candidate.

The selection mode expresses caller intent. It is not automatic system choice.

The proposed modes are:

```text
local-only
declared-remote-only
prefer-local
prefer-declared-remote
```

The proposed semantics are:

- `local-only`: select the local candidate if present, otherwise produce no
  selected candidate.
- `declared-remote-only`: select the declared remote candidate if present,
  otherwise produce no selected candidate.
- `prefer-local`: select the local candidate if present; otherwise select the
  declared remote candidate if present.
- `prefer-declared-remote`: select the declared remote candidate if present;
  otherwise select the local candidate if present.

The failure shape should remain small. A future implementation may return
`None` or a small result object when no candidate matches the selected mode.
This RFC does not require an exception hierarchy.

The `prefer-*` modes define deterministic selection order among
already-discovered candidates. They do not define runtime fallback after failed
execution.

The selection helper remains opt-in. It must not be wired into the active
`/v1/chat` path by this RFC. It must not change the existing local
`route_request(...)` path. It must not change `RoutingDecision`.

Selection does not execute a candidate. Execution remains a separate concern
behind existing execution boundaries.

## Rationale

The project already has candidate discovery, but it does not yet have an
explicit selection boundary.

A small selection mode keeps caller intent visible. A caller can say whether it
only wants local candidates, only wants declared remote candidates, or wants a
deterministic preference between already-discovered candidate families.

Caller-controlled selection preserves user boundaries and avoids magic. The
system does not silently decide that remote should win, local should win, or
that one should be tried after execution failure.

Separating discovery, selection, and execution keeps the system testable and
boring:

- discovery finds candidate families;
- selection chooses one candidate family according to explicit caller intent;
- execution remains behind explicit execution boundaries.

This keeps runtime-specific details behind adapters and keeps remote execution
behind `RemoteTransport` when it is explicitly used by a separate path.

The active `/v1/chat` path remains local-only, so this proposal does not expand
where request contents may go.

## Alternatives considered

### Keep selection undefined

The project could continue exposing both candidate families and let future code
choose between them ad hoc.

That is rejected because the choice would become hidden architecture. Routing
candidate selection affects user boundaries and privacy expectations, so the
intent should be visible before implementation.

### Always prefer local candidates

The project could define one opt-in helper that always selects the local
candidate first.

That is too narrow. Some explicit callers may be trying to prove declared
remote routing eligibility and should be able to express declared-remote-only
or declared-remote-preferred intent without changing the global routing policy.

### Always prefer declared remote candidates

The project could define one opt-in helper that always selects declared remote
candidates first.

That is rejected for the same reason. It would hide a policy preference and
could make remote selection look automatic when the project still requires
explicit caller intent.

### Activate selection in `/v1/chat`

The project could wire candidate selection into the active public chat route.

That is rejected for this RFC. Activating remote routing in `/v1/chat` is a
separate architectural decision with privacy, behavior, error, and user-facing
API implications.

### Add scoring or scheduling

The project could introduce scores, weights, scheduling rules, or
performance-based routing.

That is rejected as premature. The next decision only needs a deterministic
caller-selected mode over already-discovered candidate families.

## Trade-offs

Adding selection modes creates one more small concept in the routing area.

That cost is acceptable because it makes caller intent explicit and avoids
burying selection policy in implementation details.

The proposed modes are intentionally simple. They do not optimize for
performance, load, latency, health, or model quality. More advanced routing
policy may need a future RFC.

The `prefer-*` names may sound like fallback. This RFC uses them only for
candidate selection order before execution. They do not mean retrying another
candidate after execution failure.

Keeping the failure shape conceptual avoids over-designing implementation
details before the draft has been reviewed.

## Impact

If accepted, this RFC may affect future implementation of:

- routing candidate selection helpers;
- routing candidate selection tests;
- explicit opt-in orchestration seams;
- Phase 2 current-state documentation.

It must not require changes to:

- `/v1/chat`;
- `route_request()`;
- `RoutingDecision`;
- active orchestration;
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

- Should the future helper return `None` when no candidate matches the selected
  mode, or should it return a small result object that carries the reason?
- What should the selected candidate shape be if local and declared remote
  candidates remain distinct types?
- Should selection explanations be separate from routing explanations?
- Should the explicit selection helper live next to candidate discovery or in a
  separate module?
- What future RFC should decide if and when any selection mode becomes part of
  an active public API path?

## Decision

Accepted.

Home AI Cluster will use an explicit opt-in routing candidate selection boundary
for choosing between already-discovered local and declared remote routing
candidates.

The accepted initial selection modes are:

- `local-only`;
- `declared-remote-only`;
- `prefer-local`;
- `prefer-declared-remote`.

These modes express caller intent for candidate selection only. They do not
activate remote routing or remote execution, do not change `/v1/chat`, do not
change `route_request()`, do not change `RoutingDecision`, and do not define
runtime fallback after failed execution.

Candidate discovery, candidate selection, and execution remain separate steps.
