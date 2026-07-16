# RFC-0033: Local Node and Adapter Health Snapshot

Status: Draft

Date: 2026-07-16

Author: frian

## Summary

Home AI Cluster should add one explicit, local, opt-in operator command that
returns one truthful snapshot of:

- the ordinary configured local node declaration; and
- direct health observations from the runtime adapters instantiated in the
  ordinary local adapter registry.

The first command should be:

```text
home-ai-cluster-health
```

Its JSON output should keep declared node metadata and directly observed adapter
health in visibly separate sections.

The command should not claim continuous monitoring, routability, remote-node
health, retained status, or future request success. It should not add polling,
timestamps, history, persistence, health-aware routing, an HTTP endpoint, or a
generic observability abstraction.

## Problem

Phase 7 requires understandable node status, health visibility, and failure
visibility.

The repository already owns two useful but semantically different sources of
information:

- `NodeDescription` contains configured node metadata, including declared
  availability, declared node health, capabilities, and adapter names;
- each `RuntimeAdapter` exposes a direct `health()` operation returning
  `AdapterHealth`.

These facts are not currently available through one operator-facing surface.

More importantly, their meanings can easily be overstated.

A node declaration marked `available` and `healthy` describes current static
configuration. It does not prove that a runtime process is reachable now.

An adapter health result is a direct observation from one invocation. It does not
prove continuous availability, node-wide health, routability for an arbitrary
request, or success of a later inference.

Adding an HTTP endpoint first would broaden the ordinary application surface and
invite polling or monitoring interpretations before the smallest truthful
snapshot has been proven.

The project needs a smaller and more explicit operator boundary.

## Goals

This RFC should:

- expose the ordinary configured local node declaration;
- expose direct health observations from instantiated local runtime adapters;
- keep declared metadata and direct observations visibly separate;
- reuse existing `NodeDescription`, `NodeHealth`, and `AdapterHealth` meanings;
- remain engine-independent and capability-centered;
- remain explicit, local, opt-in, and process-scoped;
- define safe behavior for missing declared adapters;
- define safe behavior when an adapter health operation raises;
- avoid raw runtime, transport, URL, authorization, and machine-detail leakage;
- avoid changes to routing policy;
- avoid changes to `/v1/chat` and `/v1/chat/completions`;
- define the smallest implementation proof without starting implementation.

## Non-goals

This RFC does not define or authorize:

- continuous monitoring;
- background polling;
- scheduled health probes;
- timestamps or freshness semantics;
- retained last-known status;
- status history;
- uptime or availability metrics;
- a database;
- a dashboard or web interface;
- metrics collection or export;
- distributed tracing;
- an event bus or generic observability event model;
- an HTTP health or status endpoint;
- a remote-node health protocol;
- remote-machine reachability probes;
- distributed membership or discovery;
- aggregate node health derived from adapter observations;
- capability routability claims;
- health-aware candidate discovery or selection;
- routing-policy changes;
- retries or fallback changes;
- a guarantee that a later request will succeed;
- changes to the cluster-native chat contract;
- changes to the OpenAI-compatible process.

## Proposal

### One explicit local operator command

Add one explicit command:

```text
home-ai-cluster-health
```

The command should inspect the same ordinary static local node and adapter
registries used by the local application wiring.

It should execute no chat request and should start no listening service.

It should emit exactly one JSON object to standard output and then exit.

The command is a one-invocation inspection surface, not a monitoring service.

### Ordinary local configuration only

The first proof should inspect only the ordinary local configuration:

- the static local node registry;
- the static local runtime-adapter registry.

It should not inspect declared remote proof nodes or accept remote addresses.

It should not activate distributed behavior or make network requests to other
Home AI Cluster nodes.

### Output structure

The first output contract should contain one top-level `nodes` list.

Each node item should contain:

- `node_id`;
- `name`;
- a `declared` section;
- an `adapter_observations` list.

The first contract should be:

```json
{
  "nodes": [
    {
      "node_id": "local",
      "name": "Local node",
      "declared": {
        "availability": "available",
        "healthy": true,
        "reason": null,
        "capabilities": ["chat"],
        "adapters": ["ollama"]
      },
      "adapter_observations": [
        {
          "adapter": "ollama",
          "status": "available",
          "reason": null
        }
      ]
    }
  ]
}
```

The list shape should remain even though the ordinary first proof currently has
one node. This reflects the existing registry concept without creating dynamic
membership or distribution semantics.

### Declared section

The `declared` section should be a direct projection of configured
`NodeDescription` values:

- `availability` from the declared node availability;
- `healthy` from declared `NodeHealth.healthy`;
- `reason` from declared `NodeHealth.reason`;
- `capabilities` from declared capability names;
- `adapters` from declared adapter names.

These fields must remain labeled `declared`.

The command must not rewrite them based on adapter observations.

A direct adapter observation must not silently change declared node availability
or declared node health in the output.

### Adapter observations

For each adapter name declared by the node, the command should attempt to find the
same-named adapter in the inspected adapter registry.

Each declared adapter should produce exactly one observation item.

The observation status vocabulary should be:

- `available` when `health()` returns `available=True`;
- `unavailable` when `health()` returns `available=False`;
- `missing` when the declared adapter name is absent from the adapter registry;
- `probe-failed` when the adapter exists but its `health()` operation raises.

Each observation should contain:

- `adapter`;
- `status`;
- `reason`.

This vocabulary distinguishes four facts that must not be collapsed:

- a successful available observation;
- a successful unavailable observation;
- invalid or incomplete configured wiring;
- an unexpected health-operation failure.

### Reason handling

When `health()` returns normally:

- an available or unavailable observation may use the adapter-provided
  `AdapterHealth.reason` value;
- no other adapter internals should be added.

For `missing`, the stable reason should be:

```text
declared adapter is not present in the inspected registry
```

For `probe-failed`, the stable reason should be:

```text
adapter health observation failed
```

The command must not expose exception messages from an unexpected health failure.

It must not print runtime URLs, transport addresses, authorization values, raw
HTTP payloads, stack traces, private machine details, or runtime-specific
exception text in its successful JSON projection.

### Process exit behavior

A missing adapter or one failed adapter health observation should remain data in
the successful snapshot rather than aborting the whole command.

The command should still emit one complete JSON object and exit successfully when
it can inspect the registries and project all nodes, even if individual adapter
observations are `missing`, `unavailable`, or `probe-failed`.

The command should exit non-zero with a safe error only when it cannot construct
or inspect the snapshot as a whole.

This RFC does not define a general operator-error JSON contract. Before a complete
snapshot exists, a safe human-readable stderr message and non-zero exit status are
sufficient.

### No timestamps

The first output should contain no timestamp.

The process invocation itself defines when the direct adapter observations were
made. Adding a timestamp would immediately raise clock source, timezone,
freshness, and stale-data questions without improving the first one-shot command.

A future retained or remotely queried status design may require timestamps and
must be decided separately.

### No routability or aggregate status

The output should not contain fields such as:

- `routable`;
- `online`;
- `cluster_healthy`;
- `node_status` derived from adapters;
- `recommended`;
- `selected`;
- `ready_for_requests`.

Those claims require request capability, constraints, candidate discovery,
selection policy, transport availability, or aggregate semantics that this
snapshot does not own.

### Ordinary application and compatibility surfaces remain unchanged

`POST /v1/chat` should remain unchanged.

The dedicated OpenAI-compatible process and `POST /v1/chat/completions` should
remain unchanged.

The first health snapshot belongs to a cluster-native local operator command, not
to either public request response.

## First implementation proof

A later implementation satisfies this RFC only if it demonstrates all of the
following:

1. One explicit `home-ai-cluster-health` command emits exactly one JSON object.
2. The command inspects the ordinary static local node and adapter registries.
3. It performs no chat inference.
4. It starts no listening service.
5. Declared node metadata appears only under `declared`.
6. Direct adapter results appear only under `adapter_observations`.
7. Declared metadata is not rewritten from adapter observations.
8. Each declared adapter produces exactly one observation.
9. Available and unavailable adapter health results preserve existing
   `AdapterHealth` values.
10. A declared adapter missing from the adapter registry produces `missing` with
    the stable safe reason.
11. An adapter whose `health()` raises produces `probe-failed` with the stable
    safe reason.
12. One missing or failed adapter observation does not prevent the remaining
    snapshot from being emitted.
13. No timestamps, history, retention, polling, metrics, tracing, or event model
    are introduced.
14. No routability, continuous availability, aggregate node status, or future
    request-success claim is introduced.
15. No raw runtime URL, exception text, transport detail, or authorization value
    is exposed.
16. `/v1/chat` and `/v1/chat/completions` remain unchanged.
17. Ordinary automated tests require no live runtime.
18. One explicit local live proof observes the ordinary Ollama adapter and retains
    only non-sensitive evidence.

## Rationale

An explicit command is the smallest truthful operator surface.

It provides useful visibility without broadening the FastAPI application,
creating a pollable monitoring endpoint, or introducing process lifetime and
access-control questions.

Separating `declared` and `adapter_observations` makes the most important semantic
boundary visible in the data shape rather than relying only on documentation.

Using one observation item per declared adapter keeps the projection tied to the
node's configured relationships. It also makes missing wiring explicit instead of
silently omitting it.

The four observation statuses are deliberately small and evidence-based. They
represent outcomes that the current code can distinguish without inventing a
health lifecycle or failure taxonomy for requests.

Treating individual adapter failures as snapshot data makes the command more
useful while preserving truthful partial visibility. It is not retry or fallback
behavior and does not change routing.

Omitting timestamps, aggregate status, and routability keeps the first proof from
becoming monitoring architecture by accident.

## Alternatives considered

### Documentation only

This would preserve zero implementation risk and clarify field meanings.

It is not selected because Phase 7 requires an operator-visible health view, and
the repository already has enough existing data for a small truthful snapshot.

### Add an HTTP health endpoint

This would be convenient for repeated local queries.

It is not selected because it broadens the ordinary application surface, raises
binding and access questions, and invites polling and continuous-status
interpretations before command semantics are proven.

### Emit separate node and adapter top-level lists

This would directly represent the two registries.

It is not selected because the first operator question is which declared adapters
belong to each configured node and what each one reported. A node-centered
projection makes that relationship explicit and exposes missing declared adapters.

### Observe every adapter in the registry, including undeclared adapters

This could reveal incomplete or unused runtime wiring.

It is not selected for the first proof because the command is a node-health
snapshot, not a generic adapter inventory. Observing adapters not declared by a
node would require ownership and orphan-adapter semantics.

### Abort on the first missing or failed adapter observation

This would make command success mean that every observation succeeded.

It is not selected because it would hide useful remaining information and confuse
snapshot completeness with runtime availability. Individual observation problems
are better represented explicitly as data.

### Add timestamps

This could state when observations occurred.

It is not selected because one process invocation already supplies the immediate
context. Timestamps become materially useful with retention, remote queries, or
staleness semantics, all of which are deferred.

### Use adapter health during routing

This could improve routing outcomes.

It is not selected because it changes selection policy and requires freshness,
remote health, aggregate semantics, and fallback decisions. A read-only inspection
surface must be proven first.

## Trade-offs

The proposal adds another explicit operator command rather than a unified
observability interface.

That is acceptable because small purpose-specific commands preserve clear
boundaries while Phase 7 semantics are still being proven.

The node-centered projection reports only adapters declared by each node. It does
not diagnose undeclared adapters present in the registry.

The command reports partial snapshots successfully. Operators must inspect each
observation status rather than treating process exit zero as a claim that all
runtimes are available.

The first proof remains local-only and does not answer the larger user question of
whether every machine in a future cluster is online.

Those limitations are preferable to overstating configuration and one-shot probes
as a distributed monitoring system.

## Impact

This RFC affects a future explicit local operator command and one stable
cluster-native JSON projection.

Implementation should reuse:

- ordinary static local node wiring;
- ordinary static local adapter wiring;
- existing node and adapter registries;
- `NodeDescription` and `NodeHealth`;
- `RuntimeAdapter.health()` and `AdapterHealth`.

It should not require changes to:

- `ClusterRequest`;
- `ClusterResult`;
- routing candidates;
- selection policy;
- runtime adapter chat interfaces;
- remote transport;
- node identity authority;
- `/v1/chat`;
- `/v1/chat/completions`;
- ordinary distributed activation.

Future RFCs may separately address:

- an HTTP status surface;
- remote-node health protocols;
- retained last-known observations;
- timestamps and staleness;
- health-aware routing;
- aggregate node health;
- undeclared adapter inventory;
- multi-node operational views.

## Open questions

The following remain open during review:

- Should the command name be `home-ai-cluster-health` or a more explicit
  `home-ai-cluster-health-snapshot`?
- Should capability and adapter lists preserve registry/declaration order or use
  deterministic lexical ordering?
- Should an available adapter reason be preserved when non-null, or normalized to
  null because availability already communicates success?
- Should the successful command use compact JSON only, leaving formatting to
  tools such as `jq`, as existing operator commands do?

These questions must not broaden the RFC into polling, retained status, remote
health, routability, or health-aware routing.

## Decision

Pending.
