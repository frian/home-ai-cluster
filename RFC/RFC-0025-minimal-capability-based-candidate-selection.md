# RFC-0025: Minimal Capability-Based Candidate Selection

Status: Draft

Date: 2026-07-11

Author: frian

## Summary

Phase 4 should begin with the smallest automatic capability-based selection
behavior that preserves the current local-first default.

An explicit, operator-owned composition path may discover one eligible local
candidate and one eligible manually declared remote candidate for a request.
It may then apply a cluster-owned automatic policy: select the only eligible
candidate, or select local when both are eligible.  It must fail explicitly
when no candidate is selectable.  The selected candidate executes exactly once;
execution failure does not cause retry or fallback.

The ordinary application and ordinary `/v1/chat` path remain local-only by
default.  A remote address or declaration alone must not activate this policy
or permit remote execution.

## Problem

Phase 3 proved an explicit, static two-machine path.  It deliberately did not
define automatic capability-based routing.  The existing implementation now
has the necessary separable boundaries:

```text
candidate discovery
  -> explicit selection
  -> selected-candidate execution
```

Discovery can independently expose an adapter-backed local candidate and a
declaration-backed remote candidate.  Existing selection modes express caller
intent, including `PREFER_LOCAL`.  They are useful for the explicit proof but
do not define the first cluster-owned routing policy.

Phase 4 needs a small, deterministic answer to the question, “which allowed
candidate should the cluster use for this capability?”  It must not silently
turn a static remote declaration or transport address into ordinary remote
execution, and it must not turn selection preference into execution fallback.

## Goals

This RFC proposes the first minimal Phase 4 selection behavior:

- retain the existing minimal `Capability(name)` representation;
- retain one requested capability per `ClusterRequest`;
- keep local and declared-remote candidate discovery separate from selection;
- automatically choose exactly one candidate among the discovered eligible
  local and declared remote candidates in an explicit opt-in composition path;
- select the only eligible candidate, and select local if both are eligible;
- fail explicitly before execution if no candidate is selectable;
- execute the selected candidate exactly once;
- preserve authoritative `ClusterResult.node_id` attribution from selected
  execution;
- preserve `local_only` as a safe restriction on remote execution; and
- provide a small deterministic internal explanation without changing the
  public result or HTTP contract.

## Non-goals

This RFC does not introduce:

- a change to the ordinary application or ordinary `/v1/chat` behavior;
- remote activation merely from a declaration, address, or reachable machine;
- retry, execution fallback, or fallback after a remote execution failure;
- health-aware routing, health probing, or dynamic availability;
- scoring, scheduling, load balancing, performance routing, or ordering among
  multiple candidates of one family;
- discovery, registration, persistence, configuration loading, or a database;
- authentication, trust protocol, encryption, or broader production hardening;
- a richer capability taxonomy, multiple-capability expression, model routing,
  or runtime-specific routing policy;
- a public routing explanation field or any expansion of `ClusterResult` or
  the HTTP response contract; or
- use of `prefer_fast_response` or `min_context_size`.

Remote candidates remain manually and statically declared.  Runtime adapters
continue to execute runtime work; they do not own cluster routing policy.

## Proposal

### Candidate matching

The existing `Capability` representation is sufficient for this increment: a
request asks for one `Capability(name)`, and a candidate matches only when its
declared capabilities include that same capability.

Local eligibility remains adapter-backed.  A local candidate is discovered
only when an available local node declares the requested capability and has a
declared adapter that resolves locally and provides it.

Declared-remote eligibility remains declaration-backed.  A remote candidate
is discovered only within an explicitly activated operator-owned composition
when a caller explicitly supplies a manually declared node, that declaration's
node is statically available, and it declares the requested capability.  Its
transport address is transport metadata, not node identity, identity
verification, or eligibility by itself.

For this RFC, **matching** means that a candidate declares the exact requested
`Capability(name)`.  **Eligibility** means that a matching candidate also
satisfies its existing family-specific prerequisites.  **Discovery** exposes
matching eligible candidates without choosing one.  **Selectability** means a
discovered candidate remains allowed after request constraints such as
`local_only`.  **Selection** chooses exactly one selectable candidate or
reports no selectable candidate.  **Execution** invokes the already selected
candidate exactly once.  **Execution failure** means that selected invocation
fails visibly and does not cause retry or fallback.

### Explicitly activated automatic selection

This RFC proposes a distinct cluster-owned automatic capability-selection
policy, used only by a separate, explicit operator-owned composition path.
The explicitly activated composition must have caller-owned access to all of
the following:

- the local registries used for local discovery;
- the caller-owned declared-remote registry;
- the remote transport used only if remote is selected; and
- the deliberate choice to compose the automatic capability-selection path.

An ordinary application instance supplies none of this remote composition.
Its ordinary `/v1/chat` path remains the existing local-only route and does
not invoke declared-remote discovery, automatic capability selection, or
remote transport.  Therefore a remote declaration, address, or transport
existing elsewhere in code cannot silently change normal request handling.

The automatic policy applies after discovery as follows:

| Eligible local | Eligible declared remote | Result |
| --- | --- | --- |
| yes | no | select local |
| no | yes | select declared remote, unless `local_only` prohibits it |
| yes | yes | select local |
| no | no | no matching candidate; no selectable candidate before execution |

Selecting local when both candidates are eligible is fixed precedence for the
first increment, not a score, ranking, health signal, load comparison, or
performance comparison.

If `request.constraints.local_only` is `true`, a declared remote candidate may
be discovered for explanation purposes but must not be selected, contacted,
or executed.  Explicit activation of a remote-capable composition path does
not override this request-level restriction.  A local candidate may still be
selected.  If no local candidate is selectable, the policy reports no selectable
candidate without contacting the declared remote node.  The default value
remains `true`; an explicit opt-in composition path is necessary but not
sufficient to allow remote execution.

The following matrix is normative:

| Explicit remote-capable path | `local_only` | Local match | Declared remote match | Outcome |
| ---------------------------- | -----------: | ----------: | --------------------: | ------- |
| no | true | yes | irrelevant | select local |
| no | true | no | irrelevant | no selectable candidate |
| yes | true | yes | yes | select local |
| yes | true | no | yes | no selectable candidate; do not contact remote |
| yes | false | yes | no | select local |
| yes | false | no | yes | select declared remote |
| yes | false | yes | yes | select local |
| yes | false | no | no | no selectable candidate |

Without the explicit remote-capable path, declared remote candidates are not
part of ordinary request handling.  `local_only=true` remains a hard
request-level restriction even when that path is explicitly active.  Selecting
local when both candidates are selectable is fixed precedence, not execution
fallback.

For this increment, `prefer_fast_response` and `min_context_size` have no
effect on discovery or selection.

### Selection representation

The new policy should be represented as a distinct policy function or policy
object, rather than reusing `RoutingCandidateSelectionMode.PREFER_LOCAL`
unchanged.  This distinction is architectural:

- `PREFER_LOCAL` is an existing explicit caller-directed selection mode;
- the proposed policy is a cluster-owned automatic capability-based choice
  within an explicitly activated allowed composition.

An implementation may later expose the policy through a new explicit selection
mode if that makes the policy's ownership and activation unambiguous.  It must
not make the current `PREFER_LOCAL` mode silently acquire automatic-policy
meaning merely because the implementations are initially similar.  The
decision is about authority and behavior, not implementation convenience.

The policy returns exactly one selected candidate or an explicit
no-selectable-candidate outcome.  The latter occurs before execution,
including when `local_only` excludes the only discovered declared-remote
candidate.  Discovery reports no matching candidate when neither family is
discovered.  The policy must never return both families.

The automatic selection policy must produce deterministic internal explanation
facts stating the requested capability; which candidate families matched;
which candidate families were selectable after request constraints; whether
`local_only` excluded remote selection; the selected node id when selection
succeeds; the fixed rule that produced the outcome; and the
no-selectable-candidate reason when selection fails.  The selection policy owns
these explanation facts.  Their representation remains intentionally open: a
future implementation RFC or implementation change may choose the smallest
internal representation consistent with this RFC.  The facts must not include
prompt or response contents, and this RFC defines no public response field,
persistence mechanism, log format, or new `ClusterResult` structure.

### Execution and failure

Selection is not execution.  After selection, the existing selected-candidate
orchestration boundary executes exactly the selected local adapter or declared
remote transport once.

No retry occurs.  No alternative candidate is retained as an execution
fallback.  In particular, if a selected declared remote candidate fails during
transport or remote execution, the local candidate must not run afterward.
The failure remains visible through the existing normalized failure path.

Health remains descriptive and does not affect discovery, selection, or
execution.  Static availability retains its existing meaning of whether a node
may be considered by routing; it is not a health or reachability claim.

### Static and manual boundaries

The following remain static and manual:

- local node and adapter registration;
- remote node declaration and its declared capability metadata;
- remote transport address;
- explicit remote-capable composition activation; and
- the existing request-level remote permission control,
  `request.constraints.local_only`.

The selected node remains visible as the required `ClusterResult.node_id`.
For declared remote execution, that identity remains the caller-owned declared
node id, not the transport address, IP address, or a remote-reported id.

## Rationale

This is the smallest policy that begins capability-based routing while keeping
the Phase 3 proof's safety properties.  It gives the cluster one deterministic
choice among explicitly allowed candidates without assigning it broader
authority: local wins on ambiguity, and the default request restriction does
not permit remote execution.

Keeping discovery, selection, and execution separate makes each boundary
understandable:

```text
requested capability
  -> discover eligible local and declared-remote candidates
  -> apply explicit automatic capability-selection policy
  -> select exactly one candidate or fail
  -> execute once
```

The proposal is capability-centered and runtime-independent.  Local adapter
availability and remote declaration eligibility remain distinct because local
execution uses an adapter while remote execution uses transport.  It preserves
privacy and user control by making remote request movement require explicit
operator-owned activation and by retaining `local_only` as a hard restriction.

## Alternatives considered

### Reuse `PREFER_LOCAL` unchanged

Rejected as the representation of this policy.  Its result ordering resembles
the proposed rule, but it means explicit caller preference.  Reusing it as
automatic cluster policy would conceal the difference between caller-directed
selection and cluster-owned selection, and could blur the proof path with the
Phase 4 policy.

### Prefer declared remote when both candidates match

Rejected.  It would move requests away from the local default without a need
established by this first increment.  Local preference is more conservative,
easier to explain, and better aligned with local-first and privacy-first
defaults.

### Reject ambiguity when both candidates match

Rejected for the first capability policy.  Both candidates matching is the
ordinary situation this policy is meant to resolve.  A deterministic local
choice is simpler for operators than requiring an additional choice while
preserving a safe default.

### Change ordinary `/v1/chat` immediately

Rejected.  It would change normal request movement and public behavior merely
because a remote declaration is available.  A separate explicit composition
path keeps activation narrow until a future RFC decides whether ordinary access
should change.

### Add scoring or health-aware selection

Rejected.  Scores, dynamic health, load, performance, and scheduling add
operational claims and failure modes not needed to choose between one local and
one manually declared remote candidate.  Health remains descriptive.

### Expand the capability model first

Rejected.  Exact matching of the existing one-name capability is sufficient to
exercise this policy.  A taxonomy, capability combinations, qualifiers, or
model-specific metadata would add design work without improving this narrow
choice.

## Trade-offs

The proposal intentionally provides only one local candidate and one declared
remote candidate family.  It does not solve ordering among multiple local
nodes or multiple remote declarations, nor does it react to an execution
failure.  This can leave a request failed even when another candidate might
have worked.

That limitation is deliberate.  It avoids silently defining fallback,
availability, health, or scheduling semantics.  The benefit is a small policy
whose privacy boundary, failure behavior, and selected-node attribution remain
easy to inspect.

The separate activation path adds an explicit composition seam.  That is
acceptable because remote execution crosses a trust and privacy boundary and
must not be inferred from static metadata alone.

## Impact

If accepted, future implementation may add a narrow automatic
capability-selection policy and an explicit operator-owned composition seam.
It may add internal explanation data and tests for the decision table,
`local_only`, no-match behavior, single execution, and no fallback after
failure.

It must not change the ordinary application's local-only wiring, ordinary
`/v1/chat`, `ClusterResult`, or HTTP response schema without a separate RFC.
It must not change runtime adapter ownership, transport identity rules, or the
static/manual remote declaration boundary.

## Open questions

- What is the narrowest operator-owned API or wiring shape for activating the
  separate composition path without creating a general configuration system?
- Should the internal explanation be an ephemeral value, a small internal
  result type, or an extension of existing internal routing data?
- If multiple candidates of either family are later supported, which separate
  RFC should define their deterministic ordering or policy?
- Should a later RFC expose the internal explanation to users, and if so, how
  can it do so without exposing request contents or runtime internals?
- Should a later RFC make capability-based selection available on ordinary
  `/v1/chat`, and what explicit operator controls would then be required?

## Decision

Pending.
