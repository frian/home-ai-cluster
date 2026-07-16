# Phase 7 Node and Adapter Health View Investigation

Status: Investigation

Date: 2026-07-16

## Purpose

This document investigates the next smallest Phase 7 observability and trust
increment after the accepted and implemented actual-request routing explanation.

The question is:

> What truthful current node and runtime-adapter health information can Home AI
> Cluster expose through one explicit local operator surface without claiming
> continuous monitoring, routability, distributed membership, or retained status
> history?

This investigation does not select an endpoint, command name, response contract,
probe schedule, cache, timestamp model, persistence mechanism, or routing-policy
change.

Any architectural decision requires a later RFC before implementation.

## Project boundaries

The investigation preserves the current project boundaries:

- local-first and privacy-first operation;
- capability-centered and engine-independent core concepts;
- ordinary application behavior remains local and static by default;
- distributed proof behavior remains explicit and opt-in;
- no database, dashboard, metrics platform, tracing system, or event bus;
- no continuous background monitoring;
- no request history;
- no health-aware routing without a separate architectural decision;
- static declarations must not be presented as live observations;
- agents may implement accepted decisions but do not create architecture implicitly.

## Current evidence

### Node descriptions

`NodeDescription` already represents:

- node id;
- human-readable name;
- declared availability with `available`, `unavailable`, or `unknown`;
- node health with a boolean and optional reason;
- capabilities;
- adapter names.

The ordinary local application creates one static local node description for each
request. Its current values are configuration declarations, not retained live
measurements.

The local node currently declares:

- id `local`;
- availability `available`;
- healthy node status;
- the `chat` capability;
- the `ollama` adapter.

Those values describe the configured prototype shape. They do not prove that the
Ollama process is reachable at the time an operator asks.

### Runtime-adapter health

The shared `RuntimeAdapter` boundary exposes a synchronous `health()` operation
returning `AdapterHealth`:

- `available`;
- optional `reason`.

The Ollama and llama-server adapters implement this boundary. This is direct
adapter-owned health information behind an engine-independent model.

The current system can therefore ask an instantiated adapter for its current
health without executing a chat request.

This does not automatically establish:

- continuous runtime availability;
- node-wide health;
- capability routability;
- remote-machine reachability;
- historical uptime;
- health-aware selection.

### Static registries

The ordinary application constructs static local node and adapter registries.
They are simple and useful first-proof inputs, but they are rebuilt rather than
maintained as a long-lived cluster membership or status service.

A first operator view could inspect the same configured node and adapter objects.
It must not imply that the registry is a dynamic inventory.

### Remote proof nodes

Declared remote nodes currently exist only in explicit proof wiring. Their node
descriptions are caller-owned declarations, and their transport addresses are
used by explicit remote execution paths.

There is no accepted general remote health protocol. A successful or failed HTTP
request is not currently converted into a retained remote-node health status.

A first health-view increment should therefore not claim a general multi-machine
health view.

## Important semantic distinctions

### Declared availability

Declared availability answers:

> How is this node described in the current configured registry?

It does not answer:

> Was the machine or runtime probed successfully just now?

### Declared node health

The current node health field is part of the node description. In ordinary local
wiring it is static input, not an independently measured aggregate.

It must therefore be labeled as declared metadata if exposed.

### Direct adapter health

Direct adapter health answers:

> What did this adapter's health operation report during this invocation?

It is the strongest current observation available without performing a real
inference request.

It still does not prove that a later request will succeed, because state may
change immediately after the probe.

### Routability

Routability depends on more than health:

- a requested capability;
- request constraints;
- candidate discovery;
- selection policy;
- required transport availability;
- valid configured relationships between node and adapter.

A health view must not state that a node is routable merely because one adapter
reports available.

### Continuous status

Continuous status would require polling or observation over time, scheduling,
retention, timestamps, and stale-data semantics.

None of those concepts is accepted today. The first increment should not
introduce them indirectly.

## Operator questions that can be answered truthfully now

For the ordinary local configuration, the system can truthfully answer:

1. Which local node is currently configured by the inspected process?
2. What node id and display name are declared?
3. What availability and node-health metadata are declared?
4. Which capabilities and adapter names are declared on that node?
5. Which runtime adapters are instantiated in the inspected registry?
6. What does each instantiated adapter's direct `health()` call report now?

The system cannot yet truthfully answer:

1. Are all machines in a general cluster online?
2. Is a declared remote node reachable now?
3. Was this node healthy five minutes ago?
4. How long has an adapter been unavailable?
5. Will a request definitely succeed?
6. Which healthy candidate would routing select for an arbitrary request?
7. Is the routing policy health-aware?

## Candidate small outcomes

### Candidate A: Documentation only

Document the meaning of existing node and adapter health fields without adding a
new surface.

Advantages:

- no architectural risk;
- clarifies important semantics;
- prevents static declarations from being mistaken for live status.

Limitations:

- does not provide an operator inspection experience;
- does not advance the roadmap's health-view outcome materially.

Assessment:

Useful as part of this investigation, but insufficient as the next implementation
increment.

### Candidate B: Explicit local operator command with declared and observed sections

Add one opt-in local command that inspects the ordinary static local registries
and emits one JSON object with clearly separated sections, for example:

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
          "available": true,
          "reason": null
        }
      ]
    }
  ]
}
```

The exact shape is illustrative only and is not selected by this investigation.

Advantages:

- directly advances node-status and health-view roadmap outcomes;
- makes declared metadata and direct observations visibly different;
- requires no persistence or background work;
- reuses existing models and ordinary local wiring;
- can be tested with fake adapters;
- remains explicit and local.

Limitations:

- requires a stable operator projection contract;
- must define behavior when a declared adapter is absent from the registry;
- must define safe handling if `health()` raises unexpectedly;
- remains a snapshot from one process invocation;
- does not cover remote proof nodes generally.

Assessment:

Recommended as the smallest truthful next increment.

### Candidate C: Add an HTTP health endpoint

Expose the same information from the ordinary FastAPI process.

Advantages:

- convenient for local tools;
- could be queried repeatedly.

Limitations:

- broadens the ordinary public application surface;
- invites polling and continuous-status interpretations;
- requires binding and access-boundary decisions;
- may become an accidental monitoring API before command semantics are proven.

Assessment:

Not recommended as the first proof. An explicit operator command is a smaller
boundary.

### Candidate D: Use health during routing

Change candidate selection to exclude unhealthy adapters or nodes.

Advantages:

- potentially improves successful execution rates;
- connects health to operational behavior.

Limitations:

- changes routing policy;
- requires precise freshness and failure semantics;
- static node health and direct adapter health are not yet one accepted signal;
- remote health is not generally defined;
- introduces correctness and fallback questions beyond a read-only view.

Assessment:

Out of scope. Health-aware routing requires separate evidence and RFC work after
a truthful inspection surface exists.

### Candidate E: Retained or periodically refreshed status

Store the most recent health observations or probe adapters on a schedule.

Advantages:

- supports later inspection without an immediate probe;
- could show changes over time.

Limitations:

- introduces timestamps, staleness, retention, concurrency, scheduling, and
  lifecycle ownership;
- begins continuous monitoring architecture;
- is larger than necessary for one current snapshot.

Assessment:

Deferred.

## Recommended next architectural question

The recommended next question is:

> How should one explicit local operator command expose the ordinary configured
> node declarations and direct runtime-adapter health observations while keeping
> those meanings separate and avoiding claims about continuous status,
> routability, or remote-node health?

A later RFC should compare and decide at least:

- command-only versus an ordinary HTTP surface;
- one combined node projection versus separate node and adapter lists;
- the exact labels for declared metadata and direct observations;
- safe behavior when a declared adapter is missing from the adapter registry;
- safe behavior when an adapter health operation raises;
- whether unavailable adapter reasons are exposed verbatim or normalized;
- whether the first proof includes only the ordinary local configuration;
- whether any timestamp is necessary for a one-invocation snapshot.

## Recommended boundaries for the RFC

The RFC should preserve:

- one explicit local opt-in surface;
- ordinary static local configuration only for the first proof;
- no remote-node health protocol;
- no background polling;
- no retained status;
- no timestamps unless their meaning is strictly necessary and defined;
- no history;
- no health-aware routing;
- no changes to `/v1/chat` or `/v1/chat/completions`;
- no database, dashboard, metrics, tracing, or event abstraction;
- safe errors without runtime URLs or raw transport details;
- clear distinction between declared metadata and directly observed adapter health.

## Deferred questions

The following remain unresolved:

- how remote nodes should be probed;
- whether nodes need an independent active health protocol;
- whether adapter health should influence candidate discovery or selection;
- whether health observations need timestamps;
- whether observations should be retained;
- whether an HTTP status endpoint is useful after a command proof;
- whether multiple adapters per node need aggregate node-health semantics;
- how a failed adapter probe differs from an unavailable adapter result;
- whether future health views should include capabilities proven by adapters rather
  than only declared capabilities.

## Conclusion

The project already owns enough information for a small, truthful local snapshot:
static node declarations and direct adapter health observations.

The main architectural risk is not implementation complexity. It is semantic
overstatement. A configured node marked available is not the same as a directly
probed runtime adapter, and neither is the same as routability or continuous
availability.

The recommended next increment is therefore an RFC for one explicit local
operator command that separates declared node metadata from direct adapter health
observations. It should remain a one-invocation snapshot with no persistence,
background monitoring, health-aware routing, or remote-health claim.
