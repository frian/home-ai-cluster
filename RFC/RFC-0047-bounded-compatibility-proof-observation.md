# RFC-0047: Bounded compatibility proof observation

Status: Draft

Date: 2026-07-18

Author: frian

## Summary

The planned real Aider static-cluster proof needs one privacy-safe observation
from the caller-owned compatibility process: that one accepted RFC-0031 request
completed, and whether its final normalized result had a declared node ID.

This RFC proposes one explicitly enabled, process-local proof-observation mode:

```text
home-ai-cluster-openai-compatibility --declaration <path> --proof-observation
```

For each accepted request, that mode would write exactly one content-free final
line to standard error. It would expose only a positive process-local accepted
request count, a final success or failure outcome, and, on success, the
caller-owned declared result node ID. The RFC-0031 protocol and its loopback
compatibility boundary would remain unchanged.

## Problem

RFC-0046 composes the strict loopback RFC-0031 compatibility edge with the
ordinary explicit static-cluster process when the operator supplies a
declaration. The compatibility response deliberately omits routing and node
attribution. That preserves client topology blindness, but it also means a
real Aider request cannot itself establish the caller-owned declared-node
attribution of its final `ClusterResult`.

The merged proof-observation investigation found no existing shipped seam that
correlates one live accepted compatibility request with that attribution. A
receiver-side count, runtime output, access log, status snapshot, or weaker
success claim cannot establish both facts. Adding any operator-visible process
output creates an architectural privacy, retention, and compatibility boundary
that must be decided before implementation.

## Goals

This RFC should:

- decide whether one optional proof-observation mode is warranted for the
  planned real Aider static-cluster proof;
- keep the existing no-argument and declaration-backed compatibility modes
  unchanged unless the operator explicitly enables observation;
- correlate each accepted RFC-0031 request with its final caller-owned
  normalized result without exposing that fact to the compatibility client;
- expose only the minimum structural facts needed for one bounded proof;
- keep prompts, responses, private topology, runtime details, and raw errors
  outside the observation; and
- preserve ordinary routing, fallback, lifecycle, and HTTP behavior.

## Non-goals

This RFC does not authorize:

- implementation code, test changes, a proof execution, or a runbook change;
- observation for the local-only compatibility command;
- a generic logging, event, tracing, telemetry, callback, hook, or composition
  framework;
- a public response field, header, endpoint, status field, history record,
  dashboard, database, file, socket, signal, shutdown summary, or query API;
- prompt, response, authorization, declaration-path, remote URL, address,
  runtime, adapter, model, candidate, routing, fallback, or raw-error output;
- streaming, tools, model discovery, generation controls, or broader
  OpenAI-compatible behavior;
- LAN-facing compatibility access, authentication, authorization, discovery,
  scheduling, supervision, retries, lifecycle automation, or remote control;
- request serialization, automatic process exit, a one-request server mode,
  harness callbacks, or test-only production behavior; or
- a durable proof record or a general operational-observability facility.

## Proposal

Add one optional process flag to the explicit static-cluster compatibility
command:

```text
home-ai-cluster-openai-compatibility --declaration <path> --proof-observation
```

The flag enables a bounded operator-facing observation for the lifetime of that
one compatibility process. It is not normal logging and does not create an
application observation API. The operator captures the process's standard
error if evidence is wanted; Home AI Cluster does not retain it.

The conceptual path remains:

```text
strict RFC-0031 validation
  -> accepted-request count
  -> existing ClusterRequest and ordinary static-cluster routing
  -> final normalized ClusterResult or existing compatibility failure mapping
  -> one structural standard-error observation
  -> unchanged RFC-0031 response or error
```

## Command and activation boundary

The supported command forms would be exactly:

```text
home-ai-cluster-openai-compatibility
home-ai-cluster-openai-compatibility --declaration <path>
home-ai-cluster-openai-compatibility --declaration <path> --proof-observation
```

`--proof-observation` would be valid only with `--declaration`. Supplying it
without that option must be rejected as a compact operator startup error before
the listener binds. It must not silently enable observation for the local-only
compatibility command.

Activation is explicit in the command line. No environment variable,
configuration setting, declaration field, default, automatic detection, client
request field, header, or runtime condition may enable it. Omitting the flag
leaves both accepted RFC-0046 command forms unchanged and produces no proof
observation.

The declaration remains an RFC-0039/RFC-0040 operator-owned topology input.
Its loading, validation, ordering, construction, and pre-bind failure behavior
remain unchanged. Startup and declaration failures do not produce an observation
line because no compatibility request was accepted.

## Accepted-request counting

The process-local accepted-request counter begins at zero when an explicitly
enabled process starts. It increments exactly once, after a request has passed
strict RFC-0031 validation and before ordinary request execution begins.

Rejected requests must not increment the counter and must not produce a proof
line. This includes malformed requests, invalid authorization syntax,
unsupported compatibility values, and every request rejected before the
existing compatibility route accepts it for execution.

Each increment yields one positive integer used by the one final observation
for that request. The counter is process-local only: it is neither retained,
resettable through an interface, nor shared across processes.

## Observation point and causal correlation

On success, the observation must use the same complete `ClusterResult` returned
by the existing ordinary static-cluster request path, before RFC-0031 projects
that result into its compatibility response. The success node ID therefore is
the caller-owned declared `ClusterResult.node_id`, not a receiver assertion,
transport value, candidate guess, or client-provided value.

The compatibility edge remains only a routing observer at this point. It must
not select a node, inspect a declaration, influence candidate eligibility,
change local-first order, alter fallback classification, make transport calls,
retry a candidate, or take lifecycle ownership.

There is one final observation per accepted request. It must not emit
candidate-attempt events, local-failure events, remote-success events, partial
events, or duplicate success/failure lines. A local failure followed by an
ordinary remote success therefore produces only the final success line.

## Success and failure output

For each successful accepted request, the process must write exactly:

```text
proof_observation accepted_request=<POSITIVE_INTEGER> outcome=success result_node_id=<NODE_ID>
```

For each accepted request that reaches the existing compatibility failure path,
the process must write exactly:

```text
proof_observation accepted_request=<POSITIVE_INTEGER> outcome=failure result_node_id=none
```

`<POSITIVE_INTEGER>` is that request's process-local accepted count.
`<NODE_ID>` is only the final caller-owned result node ID. The field names,
ordering, lowercase outcomes, and `none` failure value are deliberately fixed
so a shell capture can validate one planned proof attempt without parsing raw
application output.

The line is final: success is determined from the returned `ClusterResult`
before compatibility response projection; failure is determined only after an
accepted request reaches the existing normal failure mapping. It must not claim
failure for a rejected request or a startup error.

## Output and retention boundary

Observation output is written only to the compatibility process's standard
error. It is not sent through Python or server logging, a logging handler,
standard output, an HTTP response, a file, a socket, a queue, a status command,
request history, a database, or any new endpoint.

Home AI Cluster retains no completed observation records. The only permitted
process-lifetime state is the current accepted-request counter and the minimal
coordination needed to assign it safely. The operator alone chooses whether and
how to capture standard error, and must retain only the bounded structural
evidence needed for the proof.

The mode is a narrow proof observation, not regular logging. It must not change
ordinary log configuration, increase server access logging, or make raw access
logs a proof source.

## HTTP compatibility boundary

RFC-0031 remains authoritative. The endpoint, loopback binding, strict request
validation, placeholder bearer treatment, request translation, response shape,
error envelope, status mapping, and client topology blindness remain unchanged.

The observation must not appear in an HTTP response, header, trailer, error
body, model value, completion identifier, or client-visible timing contract.
The client does not learn whether observation was enabled, its counter value,
the selected node, routing outcome, fallback, declaration, or process state.

Normal compatibility errors remain normal compatibility errors. The mode must
not change their status, envelope, message, leakage boundary, or retry meaning.

## Routing and lifecycle boundaries

The accepted RFC-0039/RFC-0040 declaration loading, validation, remote order,
and ordinary static-cluster construction remain authoritative. RFC-0046's
explicit static compatibility composition remains the only topology-bearing
compatibility mode.

Existing cluster-owned local-first routing, candidate selection, narrow
pre-execution fallback, remote transport, validation, and result attribution
remain unchanged. Observation has no authority to schedule, suppress, repeat,
parallelize, reroute, supervise, start, stop, repair, discover, or otherwise
control any runtime, receiver, remote process, or request lifecycle.

The operator remains responsible for declarations, runtimes, receiver startup,
network exposure, process startup and shutdown, and proof capture.

## Privacy boundary

A proof line may contain only its fixed literal fields, the positive accepted
request number, the success/failure outcome, and on success one declared node
ID. It must never contain or derive a value from:

- prompt, message, generated content, source content, request body, or response
  body;
- authorization header, bearer placeholder, credential, token, username, or
  environment value;
- declaration path or contents, remote URL, address, port, hostname, machine
  name, or private topology;
- runtime, adapter, concrete model, capability, candidate list, routing reason,
  fallback reason, transport payload, status, or raw exception; or
- timestamp, duration, request identifier, client address, user agent, or any
  additional correlation value.

The declared node ID is allowed only because ordinary static-cluster routing
already owns it as a cluster identity and the narrow proof needs the caller's
final attribution. It is not exposed by default or to compatibility clients.

## Concurrency

The counter must be safe for concurrent accepted requests in one process. The
implementation may use only the minimal process-local atomic coordination
needed to assign each accepted request one distinct positive number; it must
not hold that coordination across routing or execution.

Request completion order may differ from accepted-request number order. Lines
may consequently appear in completion order, but each line must carry the
number assigned after its own strict validation. The mode must not serialize
requests, block routing on another request's execution, automatically terminate
after one request, or promise a global ordering across processes.

The planned proof has a stricter operator procedure: it sends exactly one
accepted request and succeeds only when the capture contains exactly one
well-formed line with `accepted_request=1` and the expected final outcome. Any
missing, malformed, duplicate, or additional line makes that proof attempt
fail; it does not change HTTP behavior.

## Failure safety

Writing a proof line is best-effort and must never alter request execution,
routing, the normal compatibility response, or the normal compatibility error.
An output failure, including a closed standard error stream, must not turn a
successful request into an HTTP failure or replace an existing HTTP failure.

Conversely, a proof attempt that needs evidence must treat a missing or
malformed captured line as an unsuccessful proof attempt. That is an
operator-side evidentiary failure, not a new protocol result or application
control path.

## Compatibility and migration

The no-argument local-only command and the existing declaration-backed command
remain unchanged. Existing clients, declaration files, response parsing,
loopback deployment, tests, normal logs, and operator workflows need no
migration.

The proposed flag is additive, opt-in, and limited to the lifetime of one
explicitly selected static-cluster compatibility process. Removing the flag
removes the observation behavior completely. No persistent configuration or
state migration is introduced.

## First implementation proof

A later implementation would be complete only when focused tests demonstrate:

1. no observation state or line without `--proof-observation`;
2. the flag is rejected without `--declaration` before listener binding;
3. the flag works only with an accepted static declaration and reuses its
   existing loading and construction path;
4. accepted-request counting starts at zero for each process and assigns the
   first accepted request `1`;
5. rejected authorization, malformed JSON, invalid fields, and unsupported
   compatibility values neither increment nor emit;
6. a successful accepted request emits exactly one success line;
7. a successful line uses the final caller-owned `ClusterResult.node_id`;
8. a post-validation route failure emits exactly one failure line with
   `result_node_id=none`;
9. startup and declaration failures emit no line;
10. a local pre-execution failure followed by ordinary remote success emits no
    intermediate line and one final success line;
11. non-fallback failures preserve their existing HTTP result and emit only one
    final failure line;
12. ordinary routing, declared ordering, bounded traversal, remote transport,
    and attribution behavior are otherwise unchanged;
13. the public RFC-0031 success response is byte-for-byte unchanged in shape;
14. every existing RFC-0031 error shape and status remains unchanged;
15. the listener remains loopback-only in all command forms;
16. observation appears on standard error only, not standard output, logs,
    files, HTTP, history, status, or an endpoint;
17. lines contain no request, response, authorization, declaration, URL,
    address, runtime, adapter, model, routing, fallback, or raw-error data;
18. no completed observation record is retained after output;
19. concurrent accepted requests receive distinct positive numbers without
    serializing execution;
20. output ordering is allowed to follow completion rather than acceptance;
21. an output-write failure does not change the HTTP result;
22. normal operation does not enable or depend on access logs; and
23. a subprocess-oriented proof test can capture exactly one well-formed line
    for one accepted request without retaining sensitive values.

Ordinary automated tests must require no live runtime, receiver, private
declaration, or real Aider invocation. A later real proof remains separately
operator-owned and must follow the accepted privacy boundary.

## Rationale

The smallest useful evidence is not a general request log. It is one final,
content-free statement made at the only caller-side point where the accepted
compatibility request and its fully attributed normalized result coexist. This
preserves RFC-0031's intentional client blindness while allowing a narrowly
defined operator proof of the already accepted static-cluster path.

Standard error makes the boundary visible at the process invocation without
adding a network, storage, or application-query surface. Restricting activation
to the explicit declaration mode prevents a local compatibility request from
gaining a new default observation behavior and ties the mode to the only proof
that needs declared-node attribution.

The fixed one-line format, final-only rule, and no-retention rule minimize the
chance that a proof convenience becomes general telemetry. A node ID is still a
deliberate exposure, so it remains opt-in, caller-owned, and unavailable to the
compatibility client.

## Alternatives considered

### Do nothing and retain no stronger proof

Rejected. It preserves the present boundary but leaves the planned real Aider
static-cluster claim unprovable through the shipped command.

### Make a weaker claim from client or receiver evidence

Rejected. A successful client response or receiver count cannot correlate one
accepted compatibility request with the caller-owned declared result node ID.

### Use receiver-side evidence

Rejected. The receiver cannot establish compatibility acceptance, the caller's
fallback decision, or the caller-owned attribution of the final result.

### Depend on Uvicorn access logging

Rejected. Access logs do not carry the normalized result node ID and are a raw
server behavior rather than a privacy-safe Home AI Cluster proof contract.

### Expose attribution in the public response or a header

Rejected. That would violate RFC-0031 client topology blindness and turn a
proof need into a broad compatibility protocol expansion.

### Add an endpoint, status field, history entry, file, socket, signal, or
shutdown summary

Rejected. Each creates an additional query, retention, access, lifecycle, or
privacy contract broader than one process-bound standard-error line.

### Add a generic harness, callback, event system, or logging framework

Rejected. The proof needs one narrow shipped process behavior, not reusable
observability infrastructure or an alternate launch path.

### Automatically exit after one request

Rejected. Process lifecycle remains operator-owned and request handling must
not be redesigned around the proof procedure.

## Trade-offs

The proposal deliberately adds an operator-visible output contract and exposes
one declared node ID when explicitly enabled. That is a real privacy and
compatibility cost, even though it carries no content or topology address.

The mode also cannot prove every routing detail. It proves an accepted request's
final outcome and attribution, not timestamps, latency, candidate sequence,
receiver internals, runtime identity, or broader reliability claims. A failed
or malformed shell capture invalidates a proof attempt rather than inviting a
more invasive debug facility.

## Impact

If accepted, this RFC would authorize a later focused implementation in the
compatibility command and route, with focused tests for activation, counting,
final attribution, output, privacy, concurrency, and unchanged HTTP behavior.
It would not authorize a change to the public protocol, routing policy,
declaration schema, runtime adapters, receiver process, or lifecycle model.

The RFC itself changes no code, tests, runtime behavior, command behavior, or
operator workflow. The existing runbook remains blocked until this RFC is
accepted, implemented, and independently reviewed.

## Open questions

- Should implementation use the smallest route-local async coordination or a
  similarly narrow process-local counter object, provided neither retains
  completed observations nor serializes execution?
- What exact subprocess test fixture can capture standard error without
  invoking a live runtime or retaining a declaration path?
- Should a later accepted proof procedure require the operator to disable
  Uvicorn access logging explicitly, or is documentation that access logs are
  not proof evidence sufficient?

These questions do not authorize an implementation or broaden the proposed
surface. They are for review of this draft and any later implementation plan.

## Decision

Pending.
