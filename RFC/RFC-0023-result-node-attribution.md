# RFC-0023: Result Node Attribution

Status: Draft

Date: 2026-07-11

Author: @frian

## Summary

A successful cluster result must identify the cluster-facing node whose selected
routing candidate produced that result.

The attribution is represented by one required string field:

```text
node_id
```

The orchestration and execution boundary assigns this value from the selected
routing candidate. Runtime adapters and remote transports do not choose or infer
node identity.

For a local selected candidate, `node_id` is the selected local node id. For a
declared remote selected candidate, `node_id` is the selected remote
declaration's node id.

This RFC adds visible node attribution only. It does not add a routing
explanation object, execution history, trust protocol, remote identity proof, or
observability subsystem.

## Problem

Phase 3 has demonstrated one real request routed from one machine to another
through one user-facing endpoint. The response currently identifies the runtime
adapter and model, but it does not identify the cluster node that handled the
request.

This leaves the final Phase 3 roadmap outcome incomplete:

> visible explanation of which node handled the request.

Adapter and model names are not sufficient node attribution. Two nodes may use
the same adapter and model, and the project is explicitly engine-independent.

The project therefore needs one small, stable answer to this question:

> Which selected cluster node produced this successful result?

Without an explicit rule, future implementations could attach machine names,
transport addresses, runtime names, self-reported remote identities, or
orchestrator-selected identities inconsistently.

## Goals

This RFC should:

- make the handling node visible in every successful cluster result;
- use the existing cluster node identity model;
- keep attribution independent from machine names, addresses, models, and
  runtime engines;
- define which boundary owns attribution;
- behave consistently for local and declared remote execution;
- remain compatible with explicit selected-candidate orchestration;
- complete the minimal visibility required by the Phase 3 roadmap.

## Non-goals

This RFC does not define:

- a structured routing explanation;
- a routing decision trace;
- request history;
- logging or metrics;
- a dashboard or status view;
- remote identity authentication or cryptographic proof;
- node registration or discovery;
- transport address exposure;
- machine hostnames or display names in results;
- adapter or model selection policy;
- retries or fallback;
- multi-node execution;
- delegated or nested execution attribution;
- user-configurable response metadata;
- an OpenAI-compatible response format.

## Proposal

### Required result field

The normalized successful cluster result includes one required field:

```text
node_id: str
```

A representative response is:

```json
{
  "content": "...",
  "adapter": "ollama",
  "model": "llama3.2",
  "node_id": "declared-remote"
}
```

`node_id` uses the existing cluster-facing node identifier. It is not a machine
hostname, transport address, adapter name, model name, or human-readable label.

### Attribution meaning

`node_id` means:

> the cluster-facing id of the selected routing candidate whose successful
> execution produced this result.

This is routing attribution within the orchestrator's known cluster model. It is
not a claim that the remote machine has independently authenticated or proven
that identity.

### Attribution authority

The boundary executing an already selected routing candidate owns result node
attribution.

It must assign `node_id` from the selected candidate that it actually executes:

- local selected candidate: use the selected local node id;
- declared remote selected candidate: use the selected declaration's node id.

The selected candidate is the authority because it is the explicit
cluster-facing identity chosen before execution.

### Adapter responsibility

Runtime adapters remain responsible for runtime-specific execution and runtime
result data such as content, adapter name, and model name.

Runtime adapters must not:

- choose a cluster node id;
- derive a node id from the runtime;
- derive a node id from the machine hostname;
- derive a node id from configuration outside the selected candidate;
- decide whether execution was local or remote.

This preserves engine independence and keeps cluster identity outside runtime
integration code.

### Transport responsibility

Remote transports remain responsible for carrying normalized requests and
results to and from an explicitly declared remote node.

Remote transports must not:

- choose the result node id;
- infer identity from a URL or network address;
- treat a remote self-reported identity as authoritative;
- rewrite routing policy;
- retry or fall back to another node.

The caller's selected remote declaration remains the cluster-facing attribution
authority for that execution.

### Successful results only

This RFC defines attribution for successful cluster results.

A failed request does not need to manufacture a successful result solely to
carry `node_id`. Failure visibility and structured failure attribution remain
outside this RFC.

### No fallback ambiguity

The current selected-candidate orchestration performs no retry and no fallback.
Therefore one successful result corresponds to one selected candidate and one
`node_id`.

If future RFCs introduce retries, fallback, delegated execution, or multi-node
workflows, they must revisit whether one `node_id` remains sufficient.

## Rationale

### Use the existing node id

The project already has an explicit cluster-facing node identity. Reusing that
identity is smaller and clearer than introducing a second result-specific node
identifier.

It also avoids coupling attribution to unstable or private infrastructure data
such as hostnames, IP addresses, runtime process ids, or model names.

### Attribute from the selected candidate

The selected candidate is already the explicit orchestration decision consumed
by execution. It is therefore the narrowest existing source of truth for which
cluster node the orchestrator asked to handle the request.

Assigning attribution there keeps the rule deterministic and identical across
local and declared remote execution.

### Do not let adapters own node identity

Adapters are engine-specific. Allowing them to choose node identity would mix
cluster architecture with runtime details and weaken engine independence.

The same adapter may run on multiple nodes, so adapter identity cannot reliably
identify the handling node.

### Do not infer identity from transport addresses

Addresses are transport metadata, not node identity. They may change while node
identity remains stable, and exposing them would unnecessarily leak network
details.

### Do not trust remote self-reporting yet

The current LAN-only proof has no authentication, registration, or remote
identity protocol. Treating a self-reported remote node id as authoritative
would imply a trust guarantee the architecture does not provide.

Using the caller-owned static declaration is consistent with the accepted
manual declaration model and does not pretend to solve remote trust.

### Keep the response flat

A single `node_id` field is sufficient for the Phase 3 requirement. A nested
routing explanation object would introduce vocabulary and compatibility surface
before the project has a real need for it.

## Alternatives considered

### Keep adapter and model only

Rejected because adapter and model names do not identify a cluster node. Several
nodes may expose the same runtime combination.

### Add a human-readable machine name

Rejected because machine names are not stable cluster identity, may expose
private infrastructure details, and are not sufficient for deterministic
attribution.

### Add the remote transport address

Rejected because transport addresses are not node identity and should not become
part of the user-facing result contract.

### Let the receiving node report its own id

Rejected for this phase because there is no accepted remote identity or trust
protocol. The receiving process may also use a local-only node id that differs
from the caller's static declaration.

### Let the transport add the node id

Rejected because transport should carry execution data, not own routing
identity. Attribution must work the same way for local and remote candidates.

### Add an optional `node_id`

Rejected because optional attribution would preserve the current ambiguity and
would not reliably satisfy the Phase 3 visibility requirement.

### Add a structured `routing` or `execution` object

Rejected as premature. One required field is enough for the current proof and
keeps future routing explanation decisions open.

### Add a full node description to every result

Rejected because it duplicates registry data, expands the response contract,
and exposes metadata not required for attribution.

## Trade-offs

This proposal makes successful results self-attributing within the
orchestrator's cluster model and completes the minimal Phase 3 visibility goal.

It adds one required field to the normalized result contract. Existing result
construction and tests must therefore provide a node id.

The attribution represents the orchestrator-selected cluster identity, not a
cryptographically proven physical executor. This limitation is deliberate and
must remain explicit.

The flat field will not describe retries, fallback chains, delegated execution,
or multi-node workflows. Those features do not exist in the current system and
should not shape the first attribution model.

## Impact

If accepted, implementation work will need to:

- add required `node_id` attribution to successful normalized results;
- assign it at local selected-candidate execution;
- assign it at declared remote selected-candidate execution;
- keep runtime adapters independent from node identity;
- keep transport addresses out of the public result;
- update API response examples and tests;
- repeat the static two-machine proof and confirm that the response visibly
  identifies `declared-remote`;
- update the Phase 3 current-state documentation after implementation.

This RFC does not activate remote routing by default. The ordinary application
remains local-only, and the explicit proof process remains caller-owned and
opt-in.

The result contract changes, so internal tests and prototype callers must be
updated. The project is still an early prototype and does not promise stable
external compatibility.

## Open questions

None for this RFC.

Future RFCs may need richer attribution if the project introduces retries,
fallback, delegation, multi-node workflows, or authenticated remote identity.

## Decision

Pending.
