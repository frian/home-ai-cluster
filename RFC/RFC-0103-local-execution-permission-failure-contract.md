# RFC-0103: Local Execution Permission Failure Contract

Status: Draft

Date: 2026-09-04

Author: frian

## Summary

When Accepted RFC-0102 denies a new caller-local HAC execution and no other
statically allowed candidate remains to be considered, Home AI Cluster should
produce one distinct cluster-owned semantic failure:

```text
execution-permission-denied
```

At the native cluster HTTP boundary, that failure maps to `409 Conflict`. A
native CLI treats it as an ordinary request/execution failure and exits with
code `1`. The structured actual-request failure vocabulary established by
RFC-0034 gains `failure.status = "execution-permission-denied"` with a concise
safe cluster-owned reason equivalent to `local execution permission denied`.

Actual-request routing explanation must preserve that the local candidate was
statically eligible and separately represent the local execution-permission
denial. The semantic is not an RFC-0028 fallback condition, does not change
remote protocol behavior, and does not imply runtime capacity or unavailability.

## Problem

Accepted RFC-0102 defines the first bounded local execution-permission policy.
The policy can deny a caller-local execution after valid request validation and
static candidate discovery, before local adapter invocation, runtime contact,
or remote transport. When another statically eligible candidate remains, HAC
continues consideration in the existing deterministic order. When none remains,
the resulting request failure needs a truthful representation at existing
public failure contracts.

No current failure meaning describes this outcome. `NoSelectableRoutingCandidateError`
would be false because the local candidate remains statically selectable.
`RuntimeAdapterUnavailableError`,
`RuntimeConnectionUnavailableBeforeRequestError`, and remote transport errors
would be false because HAC did not invoke an adapter or attempt transport.
Validation, cancellation, and execution-result failures likewise describe
different stages and causes.

## Goals

This RFC should:

* define one stable, cluster-owned semantic for RFC-0102's no-alternative
  local execution-permission denial;
* map that semantic to native HTTP `409 Conflict` without claiming runtime
  capacity exhaustion;
* preserve ordinary native CLI failure behavior with exit code `1`;
* extend RFC-0034's structured failure vocabulary by one status;
* require truthful actual-request routing explanation across static eligibility,
  permission denial, and final outcome or continued consideration;
* preserve RFC-0028 fallback semantics exactly; and
* leave the receiver-side remote protocol and OpenAI-compatible containment
  unchanged.

## Non-goals

This RFC does not define:

* receiver-side refusal, remote permission failure, remote execution
  availability, or internal remote protocol fields or response semantics;
* retry-after behavior, automatic client retry, waiting, queues, scheduling,
  fairness, runtime capacity, runtime load, or process-local cardinality
  exposure;
* operator status or health fields, configuration keys, persistence, discovery,
  dynamic membership, cross-process coordination, routing algorithms,
  balancing, or a 2.0 feature commitment;
* exact Python exception or outcome types, class hierarchy, CLI wording, or
  routing-explanation field names; or
* an implementation or changes to source code, tests, fallback behavior, or
  remote protocol behavior.

## Proposal

### Semantic failure

HAC defines `execution-permission-denied` to mean exactly:

> The request is valid, an originating-process local candidate remains
> statically eligible, HAC does not permit this new local execution under the
> local execution-permission policy defined by RFC-0102, and no other
> statically allowed candidate remains to be considered at that decision point.

This is specifically the RFC-0102 first-policy no-alternative outcome. It is
not a general category for arbitrary policy refusal. It must not mean runtime
unavailable, runtime busy, remote receiver state, transport failure, no static
candidate, invalid request, cancellation, queueing, waiting timeout, or remote
refusal.

The semantic does not expose process-local interval cardinality.

### Native HTTP contract

At the native cluster HTTP contract boundary,
`execution-permission-denied` maps to HTTP `409 Conflict`.

The request is valid and a statically eligible candidate exists, but HAC's
current execution-permission state prevents this new local execution. `409`
therefore represents a cluster-owned request-time policy conflict. It does not
mean runtime capacity exhaustion.

This RFC defines neither `Retry-After` nor automatic client retry semantics.
It does not change the current mapping for any other failure.

### Native CLI contract

When the native CLI receives this server-side ordinary request outcome, it
remains an ordinary request/execution failure and exits with code `1`. Exit
code `2` remains reserved for local command, input, or operator misuse under
existing conventions.

The human-readable text must remain truthful and must not claim no selectable
candidate, runtime unavailability, or runtime busy. This RFC deliberately does
not prescribe its exact wording.

### Structured actual-request failure

RFC-0034's closed first failure vocabulary is extended by one later,
cluster-owned semantic status:

```json
{
  "status": "execution-permission-denied",
  "reason": "local execution permission denied"
}
```

The exact safe internal wording may follow repository conventions, but it must
describe a cluster-owned execution-permission outcome and must not say no
selectable candidate, runtime unavailable, runtime busy, capacity exhausted,
or transport unavailable. This RFC does not rewrite or otherwise modify
RFC-0034.

### Routing explanation

The actual-request routing explanation established by RFC-0032 must preserve
three separate facts:

```text
static eligibility/selectability
    -> local execution-permission decision
    -> final failure or continued candidate consideration
```

For the no-alternative outcome, it must be possible to represent that the local
candidate matched and remained statically eligible, execution permission was
denied at the local execution-permission stage, and no other statically allowed
candidate remained. For the alternative case, it must be possible to represent
that same eligibility and denial followed by consideration of the next
statically eligible candidate.

The denied local candidate must not be relabeled statically ineligible, assigned
an existing static exclusion reason, or converted into `no-selectable-candidate`.
This RFC defines the semantic distinction only, not an explanation schema,
field names, or presentation layout.

### Candidate continuation and final authority

The new failure is produced only when local execution permission is denied and
no other statically allowed candidate remains at that decision point.

If a remote candidate remains, HAC continues candidate consideration according
to Accepted RFC-0102. The local denial is not the final request failure. If the
subsequently attempted remote candidate fails, the existing remote
transport/runtime/fallback outcome remains authoritative; the earlier local
permission denial must not mask it.

### No fallback and no remote protocol semantics

`execution-permission-denied` is not an RFC-0028 fallback condition. It must
never be classified as `RuntimeConnectionUnavailableBeforeRequestError` or an
equivalent pre-transmission connection-unavailable condition: the denied local
candidate had no execution or transport attempt.

When no candidate remains, HAC terminates with the new failure. When another
candidate remains, consideration continues before an attempt; existing
RFC-0028 behavior applies only to subsequently attempted candidates under its
accepted rules.

Accepted RFC-0102's first policy does not apply receiver-side after
`/internal/cluster/request` transmission. This failure contract consequently
requires no internal remote request or response fields, receiver refusal
semantics, or caller interpretation of remote permission denial.

The OpenAI-compatible surface continues to use its existing generic
compatibility error containment when it reaches this policy. This RFC introduces
no new compatibility-specific public error taxonomy or envelope.

## Examples

```text
valid request
local candidate statically eligible
local execution permission denied
no other statically allowed candidate remains

=> execution-permission-denied
=> HTTP 409
=> CLI exit 1
```

In contrast:

```text
local execution permission denied
remote candidate remains
remote candidate is attempted
remote attempt fails

=> final failure is the existing remote failure
=> not execution-permission-denied
```

## Distinction from current failures

`execution-permission-denied` differs from `no-selectable-candidate` because a
static candidate exists and remains statically eligible/selectable. It differs
from runtime unavailable because no adapter or runtime invocation occurred. It
differs from pre-transmission connection unavailable and remote transport
failure because the no-alternative case makes no connection or remote transport
attempt. It differs from invalid request because validation succeeded, and from
execution failed because adapter execution did not begin on the denied local
candidate.

## Relationship to existing RFCs

RFC-0034 establishes structured actual-request failures around prior accepted
distinctions. This RFC adds one later extension because HAC now owns a distinct
request-time execution-permission semantic. RFC-0032 remains the authority for
truthful actual-request routing explanation; this RFC requires only the minimum
additional semantic distinction.

RFC-0028 remains unchanged. This failure is neither connection unavailability
nor a retry trigger, does not broaden candidate retry after an attempted
request, and does not authorize speculative duplicate execution.

Accepted RFC-0098 defines execution-availability semantics; Accepted RFC-0099
defines HAC's authority boundary; Accepted RFC-0100 defines the first bounded
process-local scope; Accepted RFC-0101 defines active execution-interval
cardinality; and Accepted RFC-0102 defines the first local execution-permission
policy. This RFC defines the no-alternative failure contract required by that
policy.

If any prerequisite is later superseded or materially changed, this RFC must be
reviewed again.

## Alternatives considered

### Reuse no-selectable-candidate / HTTP 404

Rejected. A statically selectable local candidate exists, so this would state a
false static-routing cause.

### Reuse runtime-unavailable / HTTP 503

Rejected. HAC did not contact an adapter or runtime. `503` would falsely state
service or runtime unavailability.

### Reuse validation / HTTP 422

Rejected. The request is valid; the conflict occurs at HAC's execution
permission decision.

### Reuse generic execution failure / HTTP 500

Rejected. The denial is an expected cluster-owned policy outcome, not an
internal execution failure.

### Reuse pre-transmission connection unavailable

Rejected. No transport attempt occurred, and this classification could corrupt
RFC-0028 fallback semantics.

### HTTP 409 Conflict

Accepted as the native HTTP category because the valid request conflicts with
current HAC execution-permission state without implying static absence or
runtime failure. It does not claim runtime capacity exhaustion.

### Add remote protocol semantics now

Rejected and deferred. Accepted RFC-0102's first policy does not apply
receiver-side.

### Expose cardinality in the error

Rejected for this RFC. Process-local cardinality is an internal representation;
the failure semantic does not require public cardinality exposure.

## Trade-offs

Adding a failure semantic slightly expands the public contract. That expansion
is justified because each existing semantic would communicate a false cause.
HTTP `409` introduces one native status for a cluster-owned request-time policy
conflict, while the CLI remains simple with exit code `1`. Structured
explanation becomes more truthful but gains one semantic distinction. No remote
protocol or runtime semantics are added.

## Impact

This Draft RFC changes no implementation.

If accepted, a later implementation may add a distinct internal
execution-permission failure representation, map it to native HTTP `409`, keep
native CLI handling as exit `1`, extend structured actual-request failure status
with `execution-permission-denied`, and minimally extend routing explanation so
static eligibility and permission denial remain distinguishable. It must
preserve existing behavior for every other failure.

## Open questions

* What exact Python exception or outcome type should represent the semantic?
* Where should the native HTTP mapping live?
* What concise privacy-safe native CLI text should be used?
* What minimal explanation-structure extension is sufficient?
* What tests prove local-only HTTP 409 behavior?
* What tests prove local-denied then remote-fails preserves the remote failure?
* What OpenAI-compatible generic error response results from the ordinary
  failure path?
* Should a later operator surface expose execution permission or cardinality?

## Decision

Pending.
