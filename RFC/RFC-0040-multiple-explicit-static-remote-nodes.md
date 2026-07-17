# RFC-0040: Multiple explicit static remote nodes

Status: Accepted

Date: 2026-07-17

Author: frian

## Summary

Home AI Cluster will extend the accepted ordinary static cluster topology from one
fixed local node plus one explicitly declared remote node to one fixed local node
plus one or more explicitly declared remote nodes.

The topology remains static, local-first, privacy-first, capability-centered,
operator-owned, and loaded once at process startup.

RFC-0039 flat single-remote declarations remain valid. Multiple remote nodes use
one ordered TOML array of tables:

```toml
[[remote_nodes]]
node_id = "remote-a"
base_url = "http://192.0.2.10:8000"

[[remote_nodes]]
node_id = "remote-b"
base_url = "http://192.0.2.11:8000"
```

Declaration order is the only remote priority rule.

## Problem

RFC-0038 established ordinary local-plus-one-remote operation. RFC-0039 made that
topology repeatable through one explicit local declaration file.

A small home cluster may contain more than one explicitly known remote machine.
Supporting that requires architectural decisions about declaration shape,
identity uniqueness, ordering, candidate traversal, failure boundaries,
compatibility, preflight, and privacy.

## Goals

This RFC:

- supports one fixed local node plus one or more explicit remote nodes;
- preserves local-first routing;
- preserves capability-centered candidate eligibility;
- makes remote order deterministic and operator-visible;
- preserves static validation before startup;
- preserves loopback-only exposure on the calling machine;
- preserves operator ownership of runtimes and remote applications;
- preserves cluster-owned attribution;
- preserves RFC-0039 single-remote declarations;
- keeps declaration loading local, static, and network-free.

## Non-goals

This RFC does not add:

- discovery or dynamic membership;
- remote health polling during declaration loading;
- process supervision or remote process control;
- automatic runtime or application startup;
- load balancing, scoring, weights, or scheduling;
- latency- or capacity-based selection;
- parallel execution, request fan-out, or quorum behavior;
- retries of the same candidate;
- direct request-level node targeting;
- runtime topology mutation;
- live reload or file watching;
- environment-variable topology;
- configuration merging or precedence;
- secrets or credentials;
- model, adapter, or capability configuration in the topology file;
- a dashboard, database, Docker, Kubernetes, or distributed configuration service.

## Decision

Accepted.

### Topology

The ordinary static cluster topology is:

```text
one fixed local node + one or more explicitly declared remote nodes
```

The local node remains the existing cluster-owned `local` node.

Remote nodes remain process-local declarations. Home AI Cluster does not discover,
register, supervise, start, stop, repair, or persist remote machines or runtimes.

### Declaration shapes

The RFC-0039 flat declaration remains valid and represents exactly one remote:

```toml
remote_node_id = "remote-node"
remote_base_url = "http://192.0.2.10:8000"
```

The RFC-0040 multi-remote declaration contains exactly one top-level
`remote_nodes` array of tables:

```toml
[[remote_nodes]]
node_id = "remote-a"
base_url = "http://192.0.2.10:8000"

[[remote_nodes]]
node_id = "remote-b"
base_url = "http://192.0.2.11:8000"
```

Each entry contains exactly:

- `node_id` as a string;
- `base_url` as a string.

A declaration uses either the RFC-0039 flat shape or the RFC-0040 list shape.
The shapes cannot be combined.

The multi-remote shape must contain at least one entry. No arbitrary architectural
hard maximum is introduced; the intended scope remains a small explicit home
cluster.

Unknown top-level keys, unknown entry keys, nested tables, and additional values
must fail validation before startup.

No schema-version field is introduced. The two closed shapes are distinguishable.

### CLI compatibility

The existing declaration command remains:

```text
home-ai-cluster-static-cluster --declaration <path>
```

The RFC-0038 inline mode remains supported for exactly one remote node:

```text
home-ai-cluster-static-cluster \
  --remote-node-id <remote-node-id> \
  --remote-base-url <remote-base-url>
```

Multiple remotes are available only through declaration-file mode. Declaration
mode and inline mode remain mutually exclusive.

### Identity and endpoint validation

Every remote node ID must:

- satisfy the existing remote-node ID validation;
- differ from `local`;
- be unique within the declaration.

Every remote base URL must satisfy the existing URL validation and normalization.
Duplicate normalized base URLs fail startup.

One endpoint cannot appear under several cluster-owned identities in one
declaration. A future use case for shared endpoints would require a new RFC.

### Declaration order

The order of `remote_nodes` entries is significant.

It is the operator-declared remote priority order and the only remote priority
rule introduced by this RFC.

Home AI Cluster must not reorder remote nodes based on ID, URL, latency, history,
health, load, capacity, randomness, model, adapter, or runtime identity.

### Capability eligibility

Routing remains capability-centered.

The local candidate is considered first when it satisfies the request capability.
Remote candidates use the existing static capability model. The topology file does
not gain capability, adapter, model, or runtime fields.

Among eligible remote candidates, declaration order decides precedence.

### Bounded candidate traversal

For one request:

1. attempt the eligible local candidate first;
2. if it succeeds, return immediately and contact no remote candidate;
3. if it fails with the accepted pre-request connection-unavailable condition,
   traverse eligible remote candidates in declaration order;
4. attempt each remote candidate at most once;
5. stop at the first success;
6. advance only when the current candidate fails with the same accepted
   pre-request connection-unavailable condition;
7. stop immediately on any other failure.

This is finite candidate traversal, not retry behavior. A candidate is never
retried, revisited, or attempted in parallel.

The implementation must not continue after a failure that may have occurred after
request execution began.

### Attribution and explanation

A successful response continues to expose the cluster-owned ID of the node that
handled the request.

Routing explanation remains privacy-safe. It may expose cluster-owned candidate
IDs and normalized decision categories, but not remote URLs, private addresses,
raw transport errors, declaration contents, prompts, or generated responses.

This RFC does not require a new public response schema for the full attempted
candidate sequence. A richer attempt-sequence explanation would require a later
dedicated RFC.

### Static validation and preflight

The declaration must be parsed and fully validated before application construction
and endpoint binding.

Validation rejects at least:

- missing or unreadable files;
- invalid TOML;
- mixed RFC-0039 and RFC-0040 shapes;
- missing or unknown keys;
- non-string values;
- an empty `remote_nodes` list;
- duplicate node IDs;
- a remote node ID equal to `local`;
- duplicate normalized base URLs;
- invalid base URLs;
- declaration mode combined with inline topology arguments.

Declaration loading and preflight remain local, static, read-only, and network-free.
They do not contact endpoints, poll health, inspect remote runtimes or models, or
mutate the declaration.

### Privacy and retention

The operator-owned declaration may retain private LAN endpoints as accepted by
RFC-0039.

Home AI Cluster must not expose or copy those endpoints through public responses,
normalized errors, routing explanations, request history, proof records, or
ordinary logs.

Repository examples and retained proof records use documentation-only addresses
and placeholder identities. The declaration must not contain secrets,
credentials, authorization values, private keys, usernames, or passwords.

### Lifecycle

The declaration is read once at process startup. Changes require an explicit
operator restart.

Home AI Cluster does not watch, reload, rewrite, synchronize, or lock the file.
The process owns only its own application and HTTP-client lifecycle. External
runtimes and remote applications remain operator-owned.

## Rationale

An ordered list is the smallest static extension of the accepted architecture.
It is deterministic, inspectable, and requires no scheduler.

Preserving RFC-0039 avoids breaking the verified two-machine workflow. Using a
distinct closed TOML shape keeps old and new declarations unambiguous without a
versioning system.

The bounded traversal extends the accepted narrow fallback rather than creating a
general retry policy. Each candidate is attempted once, only on the same accepted
pre-request failure condition.

## Alternatives rejected

- replacing RFC-0039 declarations;
- repeated inline CLI flags;
- a mapping keyed by node ID;
- automatic sorting;
- random or round-robin selection;
- parallel remote attempts;
- probing all remotes before routing;
- continuing after every remote error;
- an arbitrary hard node-count limit;
- schema versioning without an incompatible migration need.

## Trade-offs

The operator must understand that declaration order is meaningful. Sequential
connection attempts can increase worst-case latency when earlier candidates are
unavailable.

The design deliberately gives up dynamic optimization. It does not select the
fastest or least-loaded node and cannot adapt without an operator edit and process
restart.

Preserving both declaration shapes adds one small parser branch but avoids breaking
RFC-0039.

## Implementation sequence

Implementation should proceed in small PRs:

1. extend declaration types and parsing while preserving RFC-0039;
2. extend static validation and preflight for ordered remotes;
3. construct an ordered remote candidate collection;
4. extend narrow fallback to finite ordered traversal;
5. add focused privacy, ordering, duplicate, and failure-boundary tests;
6. update operator documentation and examples;
7. perform and retain a real multi-machine proof.

Agents may implement these accepted decisions. They do not own or revise them.