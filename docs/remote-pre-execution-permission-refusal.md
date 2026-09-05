# Remote Pre-Execution Permission Refusal

Status: Draft post-1.0 documentation

This page documents the behavior proposed by Draft RFC-0098 through RFC-0104
and implemented on Draft PR #659. It is not part of the published Home AI
Cluster 1.0 release, and it must not be treated as accepted architecture until
that Draft RFC chain is accepted and the implementation rail is integrated.

## Same-capability remote continuation

Home AI Cluster retains explicit static candidate order. For example, declared
code candidates remain ordered as follows:

```text
1. node-a
2. node-b
3. node-c
```

The caller sends a request to the first eligible candidate. It does not know in
advance whether a remote node will permit a new HAC-owned execution interval,
and it does not poll, cache, or otherwise infer remote execution permission.

For a received internal request, the remote receiver decides whether HAC may
begin its own new execution interval. The RFC-0104 first proof used the
effective HAC execution limit of `1`:

```text
0 active HAC-owned execution intervals
-> permit

more than 0
-> deny
```

Later Draft RFC-0105 generalizes that first-proof threshold to one finite,
positive effective HAC execution limit:

```text
active HAC-owned execution intervals < effective HAC execution limit
-> permit

active HAC-owned execution intervals >= effective HAC execution limit
-> deny before adapter invocation
```

Draft RFC-0106 later defines retained local selection of that limit. An
effective limit of `1` is exactly the RFC-0104 first-proof case.

This is HAC policy, not a statement about runtime capacity, model capacity,
GPU slots, queue depth, host load, or actual runtime idleness. Its current
scope is process-local; it provides no distributed availability state,
cross-process coordination, or runtime-wide serialization.

When the first remote permits execution, it executes there. When it refuses
before adapter invocation, the caller can continue in the same declared order:

```text
Request 1:
node-a permits execution
-> node-a executes

Request 2 while node-a is already at its effective HAC execution limit:
node-a receives the request
-> node-a refuses before adapter invocation
-> HAC continues to node-b
-> node-b may execute
```

This is deterministic ordered continuation, not load balancing. It adds no
round robin, fairness mechanism, scheduling, least-loaded routing, node-busy
detection, remote availability polling, queue management, or distributed
coordination.

## Exact safe refusal

Continuation after a transmitted request is safe only when the caller validates
both parts of this internal refusal contract:

```text
HTTP 409
{"detail":"execution-permission-denied"}
```

That exact response means the receiver received this request and refused it
before adapter execution began. A bare `409`, malformed body, different
`detail`, timeout, `500`, `503`, transport ambiguity, or any other
post-transmission uncertainty is not safe continuation. HAC must not send the
same independent request to another candidate when it cannot prove execution
did not begin.

Draft RFC-0105 and Draft RFC-0106 change only the local HAC permission
threshold. They do not change this exact pre-execution refusal contract.

The two safe continuation categories remain distinct:

```text
RFC-0028
A cannot be contacted before request transmission
-> HAC may continue to B

Draft RFC-0104
A receives the request
-> A does not start adapter execution
-> A returns the exact permission refusal
-> HAC may continue to B
```

They are not a generic failover mechanism. In particular, a remote refusal
does not establish that the remote was busy before transmission or that the
next candidate is available.

If each remaining candidate returns the validated refusal, no candidate remains
and the terminal human-facing outcome is:

```text
execution permission denied
```

The corresponding machine semantic is `execution-permission-denied`.

## Draft proof record

Draft PR #659 includes a real three-node manual proof of the RFC-0104
effective-limit-`1` policy, performed on 2026-09-04:
`rasp` was the caller; `debian-1` was the first explicit remote Code candidate
using Ollama with `llama3.2:1b`; and `sat` was the second explicit remote Code
candidate using Ollama with `qwen2.5-coder:7b`.

With `debian-1` permitted, it executed the request. Once it had reached the
effective limit of `1`, `rasp` contacted it first, it refused before adapter
execution, and `sat` executed successfully. With both remotes denied, the CLI
reported `error: execution permission denied` and exited with code `1`. When
`debian-1` became permitted again, static precedence returned to it.

Automated hardening also covers ordered N-candidate sequences in which A and B
refuse before C succeeds, and one in which all candidates refuse and the result
is `ExecutionPermissionDeniedError`.

This is Draft post-1.0 evidence only. It is separate from the published 1.0
five-node validation record.

## Explainability boundary

The current accepted RFC-0032 actual-request explanation remains a
select-once, execute-at-most-once contract. It must not be described as showing
the complete sequence of a request that contacts A, receives a refusal,
continues to B, and executes there. A later accepted architecture decision is
required before such an explanation is presented as a supported feature.

## Related Draft architecture

- Draft RFC-0098: Execution Availability Semantics
- Draft RFC-0099: Execution Availability Authority Boundary
- Draft RFC-0100: Execution Availability First-Proof Scope
- Draft RFC-0101: Process-Local Execution Interval Representation
- Draft RFC-0102: Local Execution Permission Policy
- Draft RFC-0103: Local Execution Permission Failure Contract
- Draft RFC-0104: Remote Pre-Execution Permission Refusal

Draft RFC-0105 later generalizes the fixed effective-limit-`1` permission
policy to one finite positive HAC execution limit. Draft RFC-0106 later defines
retained local selection of that limit. Neither changes the exact RFC-0104
pre-execution refusal contract. These later Draft RFCs are not linked here
because they are not present on this implementation branch; see Draft PR #662
and Draft PR #664 respectively.

The Draft RFC chain's acceptance, and integration of the implementation rail,
remain prerequisites for this documentation to become current operator
guidance.
