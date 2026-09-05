# Remote Pre-Execution Permission Refusal

Status: Post-1.0 development record

This page documents behavior accepted by RFC-0098 through RFC-0104 and implemented on the `post-1.0-development` line by the local execution-permission work and PR #659.

It is not part of the published Home AI Cluster 1.0 release.

## Same-capability remote continuation

Home AI Cluster keeps explicit static candidate order. For example, declared Code candidates remain ordered:

```text
1. node-a
2. node-b
3. node-c
```

The caller does not know remote execution permission in advance. It does not poll, cache, probe, or otherwise infer whether a remote will permit a new HAC-owned execution.

For the accepted first proof, one ordinary composed HAC process permits a new HAC-owned execution only while its process-local active execution-interval cardinality is zero:

```text
0 active HAC-owned execution intervals
-> permit

more than 0
-> deny
```

This is HAC-owned permission policy. It is not a statement about runtime capacity, model capacity, GPU slots, queue depth, host load, or actual runtime idleness.

When a remote permits execution, it executes normally. When it refuses before adapter invocation, the caller may continue to the next already-known statically eligible remote in the same deterministic order:

```text
node-a receives request
-> node-a denies HAC execution permission before adapter invocation
-> node-a returns the exact refusal contract
-> caller considers node-b
-> node-b decides from its own process-local HAC permission state
```

This is deterministic ordered continuation, not load balancing. It adds no round robin, fairness mechanism, scheduler, queue, least-loaded selection, remote availability state, or distributed coordination.

## Exact safe refusal

Continuation after request transmission is authorized only when the caller validates both parts of the internal refusal contract:

```text
HTTP 409
{"detail":"execution-permission-denied"}
```

That exact response means the receiver received the request and refused it before adapter execution began.

A bare `409`, malformed body, different `detail`, timeout, `500`, `503`, generic transport failure, connection loss after transmission may have begun, or any other ambiguous post-transmission outcome is not safe continuation evidence.

The caller must not send the same independent request to another candidate when HAC cannot affirmatively establish that adapter execution did not begin at the contacted receiver.

## Distinction from RFC-0028

RFC-0028 and RFC-0104 define two separate safe-continuation facts on opposite sides of request transmission:

```text
RFC-0028
candidate cannot be contacted before request transmission
-> HAC may continue

RFC-0104
candidate receives request
-> receiver refuses before adapter invocation
-> caller validates exact refusal
-> HAC may continue
```

Neither rule is generic retry or failover. Both preserve the anti-double-execution boundary by requiring affirmative evidence that useful execution did not begin at the skipped candidate.

## Failure authority

If every remaining considered candidate is skipped only because of caller-local execution-permission denial and/or validated remote pre-execution permission refusal, the terminal machine semantic is:

```text
execution-permission-denied
```

Native HTTP maps that semantic to `409 Conflict`. Native CLI handling remains exit code `1` with the human-facing message:

```text
error: execution permission denied
```

A permission refusal never masks a later authoritative runtime or transport failure. Likewise, RFC-0104 does not rewrite RFC-0028 exhaustion semantics.

For example:

```text
remote-a -> validated execution-permission-denied refusal
remote-b -> ambiguous transport failure

final outcome -> remote-b failure
```

## Real three-node proof

PR #659 records a real manual proof performed on 2026-09-04:

- `rasp` was the caller;
- `debian-1` was the first explicit remote Code candidate using Ollama with `llama3.2:1b`;
- `sat` was the second explicit remote Code candidate using Ollama with `qwen2.5-coder:7b`.

The proof established three bounded outcomes:

1. With `debian-1` permitted, normal static precedence selected and executed there.
2. While `debian-1` already had one active HAC-owned execution interval, it refused a new independent request before adapter invocation; `rasp` validated the exact refusal and `sat` executed successfully.
3. While both remotes denied permission, the request terminated as `execution-permission-denied` and the CLI exited with code `1`.

When `debian-1` became permitted again, normal static precedence returned to it.

Automated tests additionally cover multiple consecutive permission refusals, permission-only exhaustion, malformed or bare `409` responses, preservation of RFC-0028 connection-unavailability authority, and preservation of later authoritative remote failures.

This proof demonstrates same-capability remote work sharing without pre-transmission remote availability knowledge and without speculative duplicate execution.

## Explainability boundary

Accepted RFC-0032 and RFC-0034 remain authoritative for the explicit actual-request explanation surface. That surface remains select-once, local-only, and execute-at-most-one.

This page does not claim that current `explain-request` output records a complete multi-candidate sequence such as:

```text
A refused -> B considered -> B executed
```

A future operator-visible multi-candidate request timeline requires a separate architectural decision.

## Boundaries preserved

The accepted behavior adds no:

- polling or heartbeat;
- cached remote availability state;
- runtime-capacity claim;
- queue or waiting policy;
- scheduler or load balancer;
- round robin, weights, scores, or fairness policy;
- dynamic discovery or membership;
- cross-process execution cardinality;
- remote cardinality exposure;
- generic HTTP retry; or
- multi-candidate explanation timeline.

The receiver owns only its current HAC process-local permission truth at the pre-adapter boundary. The caller learns only the request-specific refusal after contact.

## Architecture references

- Accepted RFC-0098: Execution Availability Semantics
- Accepted RFC-0099: Execution Availability Authority Boundary
- Accepted RFC-0100: Execution Availability First-Proof Scope
- Accepted RFC-0101: Process-Local Execution Interval Representation
- Accepted RFC-0102: Local Execution Permission Policy
- Accepted RFC-0103: Local Execution Permission Failure Contract
- Accepted RFC-0104: Remote Pre-Execution Permission Refusal
- Accepted RFC-0028: Minimal Pre-Execution Candidate Fallback
- Accepted RFC-0032 and RFC-0034: bounded actual-request explanation and failure contracts

Later changes to execution limits, configuration, scheduling, availability observation, or operator-visible multi-candidate explanation require their own accepted architecture before this record should describe them as current behavior.
