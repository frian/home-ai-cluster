# RFC-0040: Multiple explicit static remote nodes

Status: Draft

Date: 2026-07-17

Author: frian

## Summary

Home AI Cluster should extend the accepted ordinary static cluster topology from
one local node plus one explicitly declared remote node to one local node plus an
ordered list of explicitly declared remote nodes.

The topology should remain static, local-first, privacy-first, operator-owned,
and loaded once at process startup.

RFC-0039 single-remote declarations should remain valid and unchanged. A new
multi-remote declaration shape should use one ordered TOML array of tables:

```toml
[[remote_nodes]]
node_id = "remote-a"
base_url = "http://192.0.2.10:8000"

[[remote_nodes]]
node_id = "remote-b"
base_url = "http://192.0.2.11:8000"
```

The declared order should be the only remote priority rule.

The calling process should always prefer the usable local candidate. If the
accepted pre-request connection-unavailable condition occurs, it may attempt each
eligible remote candidate once, in declaration order, stopping at the first
success. It must not retry a candidate, probe candidates in advance, run remote
attempts in parallel, score nodes, balance load, or mutate the ordering.

## Problem

RFC-0038 established the ordinary one-local-plus-one-remote topology. RFC-0039
made that topology repeatable through one explicit local declaration file.

This is sufficient for two-machine operation, but it cannot describe a small
home cluster with more than one explicitly known remote machine.

Adding more remote nodes is not only a serialization change. It reopens several
architectural questions:

- how multiple remote nodes are represented;
- whether declaration order has meaning;
- how duplicate identities and endpoints are handled;
- which candidate is attempted first;
- whether fallback may continue across several remote candidates;
- how RFC-0039 declarations remain compatible;
- how preflight and privacy boundaries scale.

These decisions must be explicit before implementation.

## Goals

This RFC should:

- support one local node plus multiple explicitly declared remote nodes;
- preserve local-first routing;
- preserve capability-centered candidate eligibility;
- make remote candidate order deterministic and operator-visible;
- preserve static validation before startup;
- preserve loopback-only exposure on the calling machine;
- preserve operator ownership of every runtime and remote application;
- preserve cluster-owned node attribution;
- preserve RFC-0039 single-remote declarations;
- keep declaration loading local and network-free;
- avoid discovery, supervision, scheduling, or a generic configuration system.

## Non-goals

This RFC does not add or define:

- automatic node discovery;
- dynamic registration or membership;
- remote health polling during declaration loading;
- automatic runtime or application startup;
- remote process control;
- process supervision;
- load balancing;
- weighted routing;
- scoring;
- latency-based selection;
- capacity-based scheduling;
- parallel speculative execution;
- request fan-out;
- quorum behavior;
- retries of the same candidate;
- direct request-level node targeting;
- topology mutation at runtime;
- live reload or file watching;
- environment-variable topology;
- configuration merging or precedence;
- credentials or authorization values;
- arbitrary local-node customization;
- model, adapter, or capability configuration in the topology file;
- internet-facing operation;
- a dashboard;
- Docker or Kubernetes;
- a database;
- a distributed configuration service.

## Proposal

### Topology

The ordinary static cluster topology becomes:

```text
one fixed local node + one or more explicitly declared remote nodes
```

The local node remains the existing cluster-owned `local` node.

Remote nodes remain process-local declarations. Home AI Cluster does not discover,
register, supervise, start, stop, repair, or persist remote machines or runtimes.

### Multi-remote declaration shape

A multi-remote declaration should contain exactly one top-level key represented
as repeated TOML array-of-table entries:

```toml
[[remote_nodes]]
node_id = "remote-a"
base_url = "http://192.0.2.10:8000"

[[remote_nodes]]
node_id = "remote-b"
base_url = "http://192.0.2.11:8000"
```

Each `remote_nodes` entry must contain exactly:

- `node_id` as a string;
- `base_url` as a string.

Unknown top-level keys, unknown entry keys, nested tables, and additional values
must fail validation before startup.

The multi-remote shape must contain at least one entry.

This RFC does not introduce an arbitrary hard maximum. The feature is intended
for small explicit home clusters, but an unexplained implementation limit would
not improve the architecture. Operational documentation should continue to frame
the mode as small and static.

### RFC-0039 compatibility

The accepted RFC-0039 flat declaration remains valid:

```toml
remote_node_id = "remote-node"
remote_base_url = "http://192.0.2.10:8000"
```

It continues to represent exactly one remote node.

A declaration must use either:

- the RFC-0039 flat single-remote shape; or
- the RFC-0040 `remote_nodes` array-of-tables shape.

The shapes must not be combined.

No schema-version field is introduced. The two shapes are closed and
unambiguous. Versioning may be proposed later if an actual incompatible
migration requires it.

### CLI compatibility

The existing command remains:

```text
home-ai-cluster-static-cluster --declaration <path>
```

The existing RFC-0038 inline mode remains supported for exactly one remote node:

```text
home-ai-cluster-static-cluster \
  --remote-node-id <remote-node-id> \
  --remote-base-url <remote-base-url>
```

This RFC does not add repeated inline flags. Multiple remote nodes are declared
through the explicit file mode only.

Declaration mode and inline mode remain mutually exclusive.

### Identity validation

Every remote node ID must:

- satisfy the existing remote-node ID validation;
- differ from the fixed local node ID;
- be unique within the declaration.

Duplicate remote node IDs must fail startup.

Every remote base URL must satisfy the existing accepted URL validation and be
normalized through the same path used by RFC-0038 and RFC-0039.

Duplicate normalized remote base URLs must fail startup. One remote endpoint must
not appear under several cluster-owned identities in the same declaration.

### Declaration order

The order of `remote_nodes` entries is significant.

It is the operator-declared remote priority order and the only remote priority
rule introduced by this RFC.

Home AI Cluster must not reorder remote nodes based on:

- node ID;
- URL;
- observed latency;
- historical success;
- health state;
- load;
- capacity;
- randomness;
- model or runtime identity.

The effective candidate sequence is therefore understandable from the local node
and the declaration file alone.

### Capability eligibility

Routing remains capability-centered.

The local candidate is considered first when it satisfies the request capability.
Remote candidates are eligible through the same existing static capability model
used by the ordinary static cluster path.

This RFC does not add capability fields to the topology file and does not make
machine names, runtime names, adapter names, or model names request-routing inputs.

Among eligible remote candidates, declaration order decides precedence.

### Bounded fallback chain

The existing accepted local-first behavior remains.

For one request:

1. attempt the eligible local candidate first;
2. if it succeeds, return immediately and contact no remote candidate;
3. if it fails with the accepted pre-request connection-unavailable condition,
   attempt eligible remote candidates in declaration order;
4. attempt each remote candidate at most once;
5. stop at the first success;
6. continue to the next remote candidate only when the current candidate fails
   with the same accepted pre-request connection-unavailable condition;
7. stop immediately on any other failure.

This is a finite candidate chain, not a retry loop.

The implementation must not:

- retry the same node;
- cycle back to an earlier node;
- attempt candidates in parallel;
- preflight network reachability before the request;
- silently change declaration order;
- continue after a failure that may have occurred after request execution began.

### Attribution and explanation

A successful response continues to include the cluster-owned ID of the node that
handled the request.

Routing explanation should remain understandable and privacy-safe. It may expose
cluster-owned candidate IDs and normalized decision categories, but must not
expose remote base URLs, private addresses, raw transport errors, declaration
contents, prompts, or generated responses.

This RFC does not require a new public response schema merely to expose the full
candidate chain.

### Static validation and preflight

The declaration must be parsed and fully validated before application
construction and endpoint binding.

Validation must reject at least:

- unreadable or missing files;
- invalid TOML;
- mixed RFC-0039 and RFC-0040 shapes;
- missing or unknown keys;
- non-string entry values;
- an empty `remote_nodes` list;
- duplicate node IDs;
- a remote node ID equal to `local`;
- duplicate normalized base URLs;
- invalid base URLs;
- declaration mode combined with inline topology arguments.

Declaration loading and preflight must remain local, static, and read-only. They
must not:

- resolve remote availability for observation purposes;
- contact any declared endpoint;
- perform health polling;
- inspect remote runtimes or models;
- mutate or repair the declaration.

### Privacy and retention

The operator-owned declaration may retain private LAN endpoints as already
accepted by RFC-0039.

Home AI Cluster must not copy or expose those endpoints through:

- public responses;
- normalized errors;
- routing explanations;
- request history;
- proof records;
- ordinary logs.

Repository examples and retained proof records must use documentation-only
addresses and placeholder identities.

The declaration must not contain secrets, credentials, authorization values,
private keys, usernames, or passwords.

### Lifecycle

The declaration is read once at process startup.

Changes require an explicit operator restart. Home AI Cluster must not watch,
reload, rewrite, synchronize, or lock the file.

The process owns only its own application and HTTP-client lifecycle. External
runtimes and remote applications remain operator-owned.

## Rationale

An ordered list is the smallest static extension of the accepted architecture.

The order is explicit, deterministic, inspectable, and requires no scheduler.
It provides a boring answer to remote precedence while keeping the operator in
control.

Retaining RFC-0039 avoids forcing migration for existing two-machine operation.
Using a distinct closed TOML shape keeps old and new declarations unambiguous
without adding a versioning system.

A bounded fallback chain extends the already accepted narrow fallback rather than
introducing a new routing policy. Each candidate is attempted once, only on the
same pre-request connection-unavailable condition, and the chain stops on success
or any other failure.

## Alternatives considered

### Replace RFC-0039 declarations

Rejected.

Existing single-remote declarations are accepted, implemented, documented, and
verified. Multiple remotes do not justify breaking them.

### Repeated inline CLI flags

Rejected.

Repeated flags would make larger declarations difficult to review, easy to
mis-pair, and likely to retain several private endpoints in shell history. The
file mode already owns repeatable topology.

### Mapping keyed by node ID

Rejected.

A TOML table keyed by node ID would obscure ordering semantics and make identity
part of serialization structure rather than an explicit validated value.

### Sort remote nodes automatically

Rejected.

Sorting by ID or URL would replace operator intent with an arbitrary rule and
would not reflect capability, availability, or trust.

### Random or round-robin selection

Rejected.

These are scheduling policies, not necessary static topology semantics.

### Parallel remote attempts

Rejected.

Parallelism can duplicate work, complicate cancellation and attribution, and
increase privacy exposure. It is unnecessary for the first multi-remote step.

### Probe all remotes before routing

Rejected.

Automatic observation would add network activity, timing state, and health
semantics beyond the accepted static architecture.

### Continue after every remote error

Rejected.

Some failures may occur after request execution begins. Continuing could duplicate
work. The chain may advance only on the accepted pre-request
connection-unavailable condition.

### Add a hard node-count limit

Rejected for the architectural contract.

The intended use remains a small home cluster, but an arbitrary number would need
a concrete operational or safety justification. Tests may use a small number
without making it a permanent architectural limit.

### Add schema versioning now

Rejected.

The RFC-0039 and RFC-0040 shapes are closed and distinguishable. No migration
machinery is currently needed.

## Trade-offs

This proposal increases topology and fallback complexity.

The operator must understand that declaration order is meaningful. A request may
make more than one sequential connection attempt when earlier candidates are
unavailable, increasing worst-case latency.

The proposal deliberately gives up dynamic optimization. It does not choose the
fastest or least-loaded node and cannot adapt without an operator edit and process
restart.

Preserving both declaration shapes adds a small parser branch, but avoids breaking
the verified RFC-0039 workflow.

## Impact

If accepted, implementation should proceed in small PRs:

1. extend declaration types and parsing while preserving RFC-0039;
2. extend static validation and preflight for ordered remote declarations;
3. construct an ordered remote candidate collection;
4. extend the narrow fallback from one remote candidate to a finite ordered chain;
5. add focused privacy, ordering, duplicate, and failure-boundary tests;
6. update operator documentation and examples;
7. perform and retain a real multi-machine proof.

No implementation should begin before this RFC is accepted.

## Open questions

- Does the proposed ordered fallback chain preserve the intended distinction
  between finite candidate traversal and retry behavior clearly enough?
- Should duplicate normalized base URLs always fail, or is there a legitimate
  future case for several cluster identities sharing one endpoint?
- Is preserving the RFC-0039 flat shape preferable to documenting a manual
  migration to the list shape?
- Does routing explanation need a later dedicated RFC if operators need the full
  attempted-candidate sequence?

## Decision

Pending.
