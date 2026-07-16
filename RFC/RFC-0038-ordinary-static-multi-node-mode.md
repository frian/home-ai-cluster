# RFC-0038: Ordinary static multi-node mode

Status: Proposed

Date: 2026-07-16

Author: frian

## Summary

Home AI Cluster should add one ordinary static multi-node operating mode that
supports exactly:

- the existing local node;
- one explicitly declared remote node;
- one ordinary loopback-only cluster endpoint on the calling machine.

The remote declaration should be supplied when the process starts through narrow
CLI arguments rather than a new configuration file or generic configuration
system.

The first accepted topology should therefore be:

```text
operator request
  -> ordinary static multi-node process
  -> existing capability-based router
     -> existing local node and adapter
     -> one explicit remote node and remote HTTP adapter
  -> normalized cluster result
```

The mode should reuse existing node, adapter, routing, fallback, health,
attribution, error, and privacy boundaries.

It must not add discovery, dynamic registration, supervision, remote process
control, automatic lifecycle management, a database, containers, or a broad
configuration abstraction.

## Problem

Phase 8 proved that one request can be routed across two real machines from a
canonical operator workflow.

The current distributed topology remains proof-only:

- the receiving machine runs the ordinary application;
- the calling machine runs `home-ai-cluster-static-proof`;
- the proof process constructs a fixed proof-specific remote declaration;
- the remote endpoint is supplied explicitly;
- process and runtime lifecycle remain manual.

This proves the architecture, but ordinary operation still exposes a split:

- local-only operation uses the normal application;
- multi-machine operation uses proof scaffolding.

The smallest unresolved architectural question is whether the already-proven
static topology should become an ordinary supported mode without introducing
network discovery or lifecycle ownership.

## Goals

This RFC should:

- make one local-plus-remote topology an ordinary supported operating mode;
- keep node declaration explicit and operator supplied;
- keep the existing local-only mode unchanged and default;
- expose one ordinary loopback-only native cluster endpoint on the calling
  machine;
- reuse existing capability-based routing and accepted fallback behavior;
- preserve cluster-owned node identity and result attribution;
- keep remote execution behind a runtime-adapter boundary;
- keep external runtime and remote application lifecycle operator-owned;
- require no new configuration file or generic configuration subsystem;
- define the smallest useful static remote declaration;
- provide a privacy-safe reproducibility proof.

## Non-goals

This RFC does not add or define:

- more than one explicitly declared remote node;
- automatic node discovery;
- automatic model discovery;
- dynamic node registration;
- node leases, expiry, heartbeats, or membership protocols;
- process supervision;
- remote process control;
- service installation;
- automatic runtime startup or shutdown;
- automatic repair;
- new retry behavior;
- new routing policy;
- load balancing;
- scheduling policy;
- a distributed configuration service;
- a database;
- a configuration file format;
- a generic configuration abstraction;
- authentication;
- internet-facing operation;
- a dashboard or web UI;
- Docker or Kubernetes;
- changes to the native chat request or response schema;
- changes to the ordinary local-only application contract.

## Proposal

Add one new operator command:

```text
home-ai-cluster-static-cluster \
  --remote-node-id <remote-node-id> \
  --remote-base-url <remote-base-url>
```

The command should start one ordinary static multi-node application process on
the existing native application port and loopback interface by default.

It should construct:

1. the existing ordinary local node and local adapter registry entries;
2. one explicit remote node declaration;
3. one remote HTTP adapter bound internally to the supplied remote base URL;
4. one ordinary orchestrator and router using the existing abstractions;
5. the existing native `/v1/chat` endpoint and accepted operator surfaces that
   can be truthfully reused without contract changes.

The command name describes the supported operating mode rather than a proof.

The existing `home-ai-cluster-static-proof` command should remain unchanged
through this RFC. Retirement or redirection of the proof command may be
considered only after the ordinary mode is implemented and reproduced.

## Supported topology

The first ordinary static multi-node mode should support exactly two declared
nodes on the calling process:

### Existing local node

The local node should retain its existing declaration and behavior:

- existing cluster-owned node identity;
- `chat` capability;
- existing local runtime adapter declaration;
- externally owned local runtime;
- existing local health and failure semantics.

### One explicit remote node

The remote node should require exactly two operator-supplied facts:

- `remote_node_id`;
- `remote_base_url`.

The remaining first-increment facts should be fixed by the accepted mode:

- capability: `chat`;
- adapter role: repository-owned remote HTTP adapter;
- transport target: the receiving machine's native Home AI Cluster endpoint;
- availability declaration: available at construction time, subject to existing
  request-time adapter observation and failure normalization;
- lifecycle ownership: external to the calling process.

The remote node ID must:

- be non-empty;
- be distinct from the existing local node ID;
- be used for cluster-owned routing explanation and result attribution;
- not be inferred from a hostname, address, model, runtime, or machine name.

The remote base URL must:

- be supplied explicitly by the operator;
- target a trusted-LAN receiving endpoint;
- not be persisted by Home AI Cluster;
- not appear in retained request history or privacy-safe proof records;
- be passed only to the repository-owned remote adapter construction.

## Why CLI arguments

The first ordinary static topology needs only two new operator values.

Narrow CLI arguments are preferred because they:

- make the topology explicit at process startup;
- avoid creating a configuration file before multiple stable configuration
  domains exist;
- avoid a parser, schema version, search path, precedence rules, reload behavior,
  and migration policy;
- preserve boring process-local construction;
- are sufficient for one local-plus-one-remote proof.

A later RFC may introduce a configuration format only when more than one accepted
feature requires it.

## Application and network boundary

The calling process should:

- bind to loopback by default;
- expose the existing native endpoint on the existing ordinary application port;
- make outbound requests only to the explicitly supplied remote base URL;
- not expose a new remote-control endpoint;
- not start, stop, configure, or inspect the remote operating system or runtime.

The receiving machine should continue to run the ordinary Home AI Cluster
application and its externally owned local runtime.

The ordinary static multi-node mode is supported only on a trusted LAN in this
increment.

Internet-facing operation is out of scope.

## Adapter boundary

Remote execution must remain behind the existing runtime-adapter abstraction.

The repository-owned remote HTTP adapter should:

- accept normalized cluster requests from the orchestrator;
- call the receiving machine's native Home AI Cluster endpoint;
- normalize the remote response into the existing cluster result boundary;
- normalize transport, timeout, remote HTTP, and invalid-response failures through
  accepted adapter failure semantics;
- return cluster-owned attribution for the declared remote node;
- never expose the supplied remote base URL through public errors;
- not log prompts, generated responses, credentials, or private addresses by
  default.

The core router must not become HTTP-aware.

## Routing boundary

This RFC must not introduce a new routing policy.

The local node and explicit remote node should enter the existing node registry
in deterministic declaration order:

1. existing local node;
2. explicit remote node.

Existing capability matching, availability handling, fallback behavior, routing
explanations, and result normalization should apply unchanged.

Consequently, with both nodes usable and both declaring `chat`, the existing
router may prefer the local node according to its accepted policy.

The remote node becomes useful when the existing policy selects it, including
accepted fallback behavior when the local path is unavailable.

This RFC does not add direct node targeting, machine-name routing, balancing,
weights, priorities, scores, or policy configuration.

## Health boundary

The existing `home-ai-cluster-health` command remains an ordinary local health
surface and should not be silently broadened by this RFC.

The new process may expose only health information that can be truthfully derived
from existing accepted runtime and adapter boundaries.

This RFC does not require background polling, heartbeats, cached remote health,
or a distributed health service.

Remote adapter availability may be observed during an explicit request or through
an already-accepted direct adapter observation path if implementation can reuse
one without changing its contract.

Any new operator-facing distributed health contract requires a separate RFC.

## Preflight boundary

RFC-0036 currently validates one static rule:

> Every adapter declared by a configured node resolves in the inspected adapter
> registry.

For the new ordinary process, static preflight should be able to inspect the
registries constructed for that process and apply the same accepted rule to both
nodes.

This means the remote node's declared adapter must resolve in the same inspected
adapter registry.

Preflight must not:

- contact the remote endpoint;
- test DNS or LAN reachability;
- inspect the receiving runtime or model;
- validate remote execution;
- perform health polling;
- mutate declarations;
- repair any condition.

If exposing process-specific preflight requires a new invocation contract, that
contract must remain within RFC-0036 semantics and be reviewed during
implementation. It must not broaden preflight into network observation.

## Failure behavior

The ordinary static multi-node mode should preserve existing public failure
boundaries.

At minimum:

- invalid CLI declarations should fail before application startup with a compact
  operator-facing error and non-zero exit status;
- a duplicate remote node ID should fail before startup;
- an invalid remote base URL should fail before startup;
- local runtime failures should retain existing local adapter semantics;
- remote transport or receiving-endpoint failures should be normalized by the
  remote adapter;
- routing explanations should continue to identify considered nodes and accepted
  reasons without exposing private endpoint values;
- no hidden retry, repair, discovery, or remote restart should occur.

## Lifecycle boundary

Home AI Cluster should own only the lifecycle of the process started by
`home-ai-cluster-static-cluster`.

The operator remains responsible for:

- preparing both machines;
- keeping both repositories on a compatible revision for the first proof;
- starting the receiving application;
- starting external runtimes;
- supplying the remote node ID and base URL;
- creating and removing any temporary trusted-LAN firewall allowance;
- stopping the calling process;
- stopping the receiving application;
- deciding whether external runtimes remain running.

No remote start, stop, restart, install, repair, or supervision behavior is
introduced.

## Privacy boundary

The new mode may retain or expose only the metadata already allowed by accepted
contracts, including:

- cluster-owned node IDs;
- capability names;
- adapter names;
- normalized public status and failure categories;
- routing decision metadata;
- model and adapter metadata already present in normalized results.

It must not retain by default:

- prompts;
- generated responses;
- private LAN addresses;
- supplied remote base URLs;
- authorization values;
- credentials;
- machine names;
- hardware details;
- filesystem paths;
- raw transport exceptions;
- personal account details;
- secrets.

The CLI process may hold the supplied remote base URL in memory for its lifetime.
It must not persist it.

## Operator workflow impact

Implementation should update `docs/operator-workflow.md` only after this RFC is
accepted.

The canonical workflow should then describe three clearly separated modes:

1. ordinary local-only operation;
2. ordinary explicit static multi-node operation;
3. explicit historical two-machine proof operation.

The local-only mode must remain the default and shortest path.

The proof-only mode should remain documented until the new ordinary mode is
implemented, reproduced, and shown to preserve the relevant proof evidence.

## Rationale

The founding distributed architecture has already been proven.

The next boring step is not automatic discovery or lifecycle automation. It is to
remove the proof-only application shape while preserving explicit topology and
manual ownership.

Supporting exactly one remote node is intentionally narrow:

- it proves ordinary multi-node operation;
- it avoids an arbitrary topology language;
- it avoids a configuration subsystem;
- it reuses the existing remote request path;
- it keeps architecture real while distribution remains deliberately small.

This follows the project objective:

> fake in distribution, but not fake in architecture.

## Alternatives considered

### Introduce a static configuration file

Deferred.

Two operator-supplied values do not yet justify file discovery, format versioning,
validation precedence, reload behavior, migration, or generic configuration
abstractions.

### Promote `home-ai-cluster-static-proof` unchanged

Rejected.

The proof command has proof-specific naming and fixed declarations. Calling it
ordinary would preserve scaffolding rather than define an ordinary contract.

### Extend the ordinary `uvicorn` startup through environment variables

Rejected for this increment.

Environment-variable topology would be less visible, harder to inspect, and would
create naming and precedence rules without improving the architecture.

### Support arbitrary numbers of remote nodes

Deferred.

One explicit remote node is sufficient to prove the ordinary multi-node shape.
Repeated declarations and topology validation should follow only after evidence
from this mode.

### Add node discovery

Rejected.

Discovery introduces identity, trust, freshness, expiry, conflict, and network
scope before explicit static operation is ordinary.

### Add direct node targeting

Rejected.

The project is capability-centered. The user should not select machines through
the request contract.

### Add process supervision

Rejected.

Ordinary static routing does not require Home AI Cluster to own remote or runtime
lifecycle.

## Trade-offs

The operator must still:

- know the receiving endpoint;
- start both application paths manually;
- manage trusted-LAN exposure;
- understand local, remote, runtime, and network failure layers.

The first mode supports only one remote node and only the existing `chat`
capability.

CLI arguments do not scale to arbitrary topologies. That limitation is accepted
because this RFC is intended to produce evidence before a configuration format is
designed.

Keeping local-first routing policy unchanged may mean the remote node is primarily
exercised through existing fallback behavior. This is preferable to introducing a
new scheduler merely to demonstrate remote use.

## Impact

This RFC may affect:

- one new CLI entry point;
- process-local application construction;
- reuse or extraction of the existing remote HTTP adapter path;
- ordinary node and adapter registry construction;
- focused static declaration validation;
- routing and failure tests using existing policies;
- operator documentation;
- one retained privacy-safe proof.

It must not affect:

- the ordinary local-only application behavior;
- the native request or response schema;
- accepted routing policy;
- accepted fallback policy;
- external runtime ownership;
- remote process lifecycle;
- compatibility endpoint behavior;
- request-history privacy defaults;
- discovery or registration.

## Proof requirements

Implementation should not be considered complete until a retained privacy-safe
proof demonstrates that an operator can:

1. prepare one calling machine and one receiving machine on a trusted LAN;
2. start the receiving ordinary application and externally owned runtime;
3. start `home-ai-cluster-static-cluster` with one explicit remote node ID and
   remote base URL;
4. inspect coherent local process registries without network observation;
5. submit a request to the calling machine's loopback native endpoint;
6. demonstrate existing local routing behavior when the local path is usable;
7. demonstrate routing to the declared remote node through existing accepted
   fallback behavior when the local path is unavailable;
8. observe cluster-owned remote node attribution;
9. observe a normalized remote failure without hidden retry or repair;
10. stop the calling process before the receiving application;
11. remove temporary firewall exposure when created;
12. retain no prompt, generated response, private address, endpoint URL, machine
    name, hardware detail, path, credential, raw exception, or personal detail.

## Implementation boundary

Acceptance of this RFC would authorize only the minimum required to implement the
specified mode.

Implementation should proceed in small branches and draft PRs.

It should first identify which existing static-proof components can be reused
without moving proof-specific assumptions into ordinary architecture.

Agents may implement the accepted decisions, but they must not choose broader
configuration, routing, lifecycle, discovery, or supervision behavior.

## Decision

Proposed.
