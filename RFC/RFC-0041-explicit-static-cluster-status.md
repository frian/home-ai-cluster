# RFC-0041: Explicit static cluster status

Status: Accepted

Date: 2026-07-17

Author: frian

## Summary

Home AI Cluster will add one explicit, read-only operator status operation for an
already declared static cluster.

The operation will validate the selected declaration locally, inspect the fixed
local node directly, and query each explicitly declared remote node through one
small internal status endpoint.

Remote observations will run sequentially in declaration order with a finite
per-remote timeout. Results will use cluster-owned node identifiers and normalized
status categories. They will not expose remote URLs, private addresses, raw
transport errors, prompts, generated responses, credentials, or declaration
contents.

Status inspection will not affect routing, candidate order, fallback, process
lifecycle, declaration contents, or future requests.

## Problem

The accepted static preflight validates declaration coherence without network
observation. The accepted local health command inspects only the fixed local node
and its local runtime adapters.

After Phase 10, an operator can declare one local node plus multiple ordered remote
nodes, but understanding the cluster before sending a request still requires
unrelated tools such as direct HTTP requests, socket inspection, and separate
terminal checks on each machine.

The project needs one bounded operator-owned observation that clearly separates:

- facts validated from the static declaration;
- direct observations of the local runtime;
- live observations returned by explicitly declared remote applications.

Without such an operation, the cluster remains operable but unnecessarily hard to
inspect. Adding background monitoring or health-aware routing would solve a much
larger problem than Phase 11 requires.

## Goals

This RFC:

- defines one explicit operator-invoked static cluster status operation;
- preserves network-free declaration validation before live observation;
- reports the fixed local node followed by declared remotes in declaration order;
- reuses the existing local health observation behavior for the local node;
- defines one narrow internal remote status protocol;
- bounds remote observation with a finite timeout;
- uses normalized, privacy-safe result categories;
- distinguishes application reachability from runtime availability;
- preserves cluster-owned node attribution;
- keeps the operation read-only and free of routing or lifecycle side effects.

## Non-goals

This RFC does not add:

- background polling or periodic monitoring;
- discovery, registration, or dynamic membership;
- health-aware routing, scheduling, scoring, or load balancing;
- automatic topology mutation;
- process supervision or remote process control;
- automatic runtime or application startup, stop, restart, or repair;
- retries of one remote observation;
- parallel observation or request fan-out;
- persistence, history, alerts, or notifications;
- a dashboard, database, metrics service, or monitoring agent;
- model inventory, capacity, latency, or performance inspection;
- prompt or generated-response logging;
- general authentication, authorization, or production security;
- secrets or credentials in the declaration;
- changes to ordinary request routing or fallback behavior.

## Proposal

### Operator command

Add one explicit command:

```text
home-ai-cluster-status --declaration <path>
```

The command requires one explicitly selected RFC-0039 or RFC-0040 declaration.
It does not search for a default declaration and does not accept inline topology
arguments.

The command performs one finite status operation and exits. It does not remain
running, watch files, poll nodes, or retain results.

### Operation sequence

The command performs these steps in order:

1. load and fully validate the declaration using the accepted static declaration
   rules;
2. if validation fails, perform no network observation and exit unsuccessfully;
3. inspect the fixed local node through the existing local health snapshot seam;
4. inspect each declared remote sequentially in declaration order;
5. project one privacy-safe result containing the local node first and every
   declared remote exactly once;
6. print the result and exit.

Static declaration validation remains local, read-only, and network-free. The
result must make clear that declaration coherence and live status are different
kinds of information.

### Remote status protocol

The ordinary receiving application adds one read-only internal endpoint:

```text
GET /internal/cluster/status
```

The endpoint inspects only the receiving process's fixed local node and local
runtime adapters. It does not inspect other remotes, recurse through another
cluster declaration, route a chat request, or invoke model generation.

A successful endpoint response contains one normalized runtime observation:

```json
{
  "runtime_status": "available"
}
```

The accepted `runtime_status` values are:

- `available`: the receiving application's declared local runtime adapter is
  present and its direct health observation reports available;
- `unavailable`: the adapter is present and its direct health observation reports
  unavailable;
- `observation-failed`: the receiving application could not complete its local
  runtime health observation.

The response does not include the receiving machine's local node ID. The calling
status command owns remote identity through the selected declaration and reports
the corresponding cluster-owned remote node ID.

The response does not include adapter names, model names, runtime URLs, machine
names, private addresses, raw exception text, prompts, generated responses,
credentials, or declaration facts.

Runtime unavailability is an observed status, not an HTTP transport failure. A
valid `unavailable` or `observation-failed` response therefore uses HTTP 200.

### Remote observation categories

For each declared remote, the calling command reports two separate dimensions:

- `application_status`;
- `runtime_status`.

Accepted `application_status` values are:

- `reachable`: the remote application returned a valid status response;
- `unreachable`: no connection was established before the finite timeout;
- `request-failed`: the connection was established but the status request did not
  complete successfully;
- `invalid-response`: the endpoint returned a response that does not satisfy the
  accepted status protocol.

When `application_status` is `reachable`, `runtime_status` is one of the values
returned by the remote protocol.

For any other application status, `runtime_status` is `unknown`.

These categories are observations for the operator. They do not become routing
eligibility, node health state, fallback history, or persistent cluster state.

### Local observation

The fixed local node is inspected through the existing local health snapshot
behavior.

The status command projects the local result into the same normalized runtime
status vocabulary:

- `available`;
- `unavailable`;
- `observation-failed`.

The local result has:

```text
application_status = local
```

The local node remains first in the output and retains the cluster-owned ID
`local`.

### Result shape

The command prints one compact JSON object:

```json
{
  "declaration_status": "coherent",
  "nodes": [
    {
      "node_id": "local",
      "application_status": "local",
      "runtime_status": "available"
    },
    {
      "node_id": "remote-a",
      "application_status": "unreachable",
      "runtime_status": "unknown"
    },
    {
      "node_id": "remote-b",
      "application_status": "reachable",
      "runtime_status": "available"
    }
  ]
}
```

The node list order is always:

1. the fixed local node;
2. declared remotes in declaration order.

The result has no aggregate `healthy`, `ready`, `pass`, or preferred-node field.
The command reports observations rather than making a scheduling or routing
decision.

### Timeout and execution order

Remote observations run sequentially in declaration order.

Each remote observation has one finite implementation-owned timeout. The exact
initial duration is an implementation detail, but it must be fixed, documented,
and covered by tests. Phase 11 does not add timeout configuration to the
declaration or CLI.

A timeout or failure for one remote does not stop observation of later declared
remotes. Each declared remote is observed at most once.

This is bounded status collection, not routing fallback and not retry behavior.

### Exit behavior

The command exits unsuccessfully when it cannot construct the status operation,
including invalid arguments, unreadable declarations, invalid declaration
content, or failure to construct the local inspection boundary.

Once declaration validation succeeds and node observations begin, unavailable or
failed node observations are reported in the JSON result and do not by themselves
make command execution unsuccessful.

This distinction prevents the command's process exit code from becoming an
implicit cluster health policy.

### Privacy and retention

The command and internal endpoint are read-only.

They must not expose or retain:

- remote base URLs or private addresses;
- machine names;
- declaration contents or local filesystem paths;
- raw transport, HTTP, adapter, or runtime errors;
- adapter or model names in the remote protocol;
- prompts or generated responses;
- credentials, authorization values, usernames, passwords, or secrets.

Normalized reasons may be added only when they are closed, privacy-safe
categories accepted by this RFC or a later RFC.

Ordinary logs must not print remote URLs, declaration contents, or raw errors.
The operation creates no persistent history.

### Lifecycle and side effects

Status inspection must not:

- alter declaration files;
- alter node or adapter registries;
- change routing candidates or candidate order;
- change ordinary request fallback behavior;
- start, stop, restart, or repair any process or runtime;
- cache observations for later requests;
- mutate application health state;
- trigger model generation.

The operator remains responsible for starting and stopping remote applications and
runtimes.

## Rationale

A dedicated one-shot command is the smallest operator-facing improvement. It
matches the explicit static architecture and avoids turning Home AI Cluster into a
monitoring service.

A dedicated internal status endpoint is clearer and safer than sending a fake chat
request. It observes the receiving application's local runtime without invoking
model generation or conflating status with request routing.

Separating application reachability from runtime availability gives useful
operator information without introducing scheduling semantics. A remote
application can be reachable while its runtime is unavailable, and those are
different operational problems.

Sequential declaration-order observation is deterministic, easy to explain, and
consistent with the small-cluster scope. Parallel probing would add concurrency
without being required for the first useful status operation.

Using cluster-owned remote IDs from the declaration preserves the existing
identity boundary and avoids trusting receiving-machine identity claims.

## Alternatives considered

### Reuse static preflight

Rejected. Static preflight is intentionally network-free. Adding live observation
to it would erase an important operator distinction and change an accepted
boundary.

### Extend the local health command transparently

Rejected. The existing command describes local process-scoped health. Making it
contact remotes based on implicit configuration would change its meaning and
introduce hidden network behavior.

### Send an ordinary chat request to every node

Rejected. It would invoke model generation, consume more resources, require prompt
content, and confuse status observation with routing and model quality.

### Use raw TCP reachability only

Rejected. A listening port does not prove that the ordinary Home AI Cluster
application is running or that its local runtime is observable.

### Observe remotes in parallel

Rejected for the first version. Parallelism adds concurrency, cancellation, and
ordering complexity without being necessary for a small explicitly declared
cluster.

### Stop after the first unavailable remote

Rejected. Status collection is not routing fallback. The operator needs one result
for every declared node.

### Return an aggregate healthy or ready result

Rejected. An aggregate would introduce an implicit policy about what cluster
health means and could become accidental scheduling behavior.

### Persist observations or add background polling

Rejected. That would create monitoring, history, lifecycle, and retention
responsibilities outside Phase 11.

## Trade-offs

Sequential observation means total worst-case duration grows with the number of
unreachable remotes. This is acceptable for a small explicit home cluster and
keeps behavior deterministic and simple.

A dedicated internal endpoint adds one protocol surface. The surface is narrow,
read-only, non-generative, privacy-safe, and available only when the operator has
already exposed the ordinary receiving application to the trusted LAN.

Normalized categories are less detailed than raw errors. That loss of detail is
intentional: it protects privacy, keeps output stable, and avoids coupling the
operator contract to one HTTP client or runtime engine.

The command does not answer whether the cluster is globally healthy or which node
should handle the next request. The operator receives observations and retains the
responsibility to interpret them.

## Impact

This RFC affects:

- one new operator command;
- one new internal read-only endpoint on the ordinary receiving application;
- reuse and projection of the existing local health observation seam;
- one remote status transport and response validator;
- privacy-safe status result models;
- focused timeout, ordering, failure-category, and no-side-effect tests;
- operator documentation and a real multi-machine proof.

It does not change:

- declaration formats;
- ordinary static cluster startup;
- request schemas or response schemas for `/v1/chat`;
- routing, candidate selection, or fallback;
- runtime adapter interfaces;
- request history;
- OpenAI-compatible access;
- process ownership or lifecycle.

Implementation should proceed in small PRs after acceptance:

1. add normalized status result models and local projection;
2. add the internal remote status endpoint;
3. add the remote status transport and validation;
4. add sequential declaration-order status collection;
5. add the explicit operator command and exit behavior;
6. add focused privacy, timeout, ordering, and side-effect tests;
7. update operator documentation;
8. perform and retain one real multi-machine status proof.

Agents may implement accepted decisions. They do not own or revise them.

## Open questions

- What fixed initial per-remote timeout should the implementation use?
- Should the compact command output be followed later by a separate human-readable
  presentation mode?

Neither question changes the proposed architectural boundaries.

## Decision

Accepted.

Home AI Cluster will provide one explicit, read-only, bounded status operation for
an already declared static cluster. The operation will preserve network-free
static validation, inspect the fixed local node directly, observe declared remotes
sequentially through the narrow internal status endpoint, report normalized
privacy-safe categories, and remain informational with no routing, lifecycle, or
persistent-state effects.
