# RFC-0023: Result Node Attribution

Status: Accepted

Date: 2026-07-11

Author: @frian

## Summary

Every successful normalized cluster result must identify the cluster-facing node
whose selected routing candidate produced that result.

The attribution is represented by one required field:

```text
node_id: str
```

The selected-candidate execution boundary assigns this value from the candidate
that it actually executes. Runtime adapters and remote transports do not choose,
infer, or authoritatively report cluster node identity.

For a local selected candidate, `node_id` is the selected local node id. For a
declared remote selected candidate, `node_id` is the selected remote
declaration's node id.

This RFC adds visible node attribution only. It does not add a routing
explanation object, execution history, failure attribution, remote identity
proof, or observability subsystem.

## Problem

Phase 3 has demonstrated one real request routed from one machine to another
through one user-facing endpoint. The response currently identifies the runtime
adapter and model, but it does not identify the cluster node that handled the
request.

This leaves the final Phase 3 roadmap outcome incomplete:

> visible explanation of which node handled the request.

Adapter and model names are not sufficient node attribution. Multiple nodes may
use the same adapter and model, and the project is explicitly engine-independent.

The project needs one small and stable answer to this question:

> Which selected cluster node produced this successful result?

Without an explicit rule, future implementations could attach machine names,
transport addresses, runtime names, remote self-reported identities, or
orchestrator-selected identities inconsistently.

## Goals

This RFC must:

- make the handling node visible in every successful cluster result;
- use the existing cluster-facing node identity;
- keep attribution independent from machine names, addresses, models, and
  runtime engines;
- define which boundary owns attribution;
- behave consistently for local and declared remote execution;
- remain compatible with explicit selected-candidate orchestration;
- complete the minimal visibility required by the Phase 3 roadmap.

## Non-goals

This RFC does not define:

- a structured routing explanation or decision trace;
- failure attribution;
- request history, logging, metrics, or a dashboard;
- remote identity authentication or cryptographic proof;
- node registration or discovery;
- transport address exposure;
- machine hostnames or display names in results;
- adapter or model selection policy;
- retries or fallback;
- multi-node or delegated execution;
- an OpenAI-compatible response format.

## Proposal

### Required result field

Every successful normalized cluster result includes:

```text
node_id: str
```

A representative result is:

```json
{
  "content": "...",
  "adapter": "ollama",
  "model": "llama3.2",
  "node_id": "declared-remote"
}
```

`node_id` uses the existing cluster-facing node identifier. It is not a machine
hostname, transport address, adapter name, model name, or display label.

### Attribution meaning

`node_id` means:

> the cluster-facing id of the selected routing candidate whose successful
> execution produced this result.

This is routing attribution within the orchestrator's known cluster model. It is
not a claim that a remote machine independently authenticated or proved that
identity.

### Attribution authority

The boundary executing an already selected routing candidate owns result node
attribution.

It must assign `node_id` from the candidate that it actually executes:

- local selected candidate: use the selected local node id;
- declared remote selected candidate: use the selected declaration's node id.

The selected candidate is authoritative for attribution because it is the
explicit cluster-facing identity chosen before execution.

### Adapter responsibility

Runtime adapters remain responsible for runtime-specific execution and runtime
result data such as content, adapter name, and model name.

Runtime adapters must not:

- choose a cluster node id;
- derive a node id from the runtime or hostname;
- derive a node id from configuration outside the selected candidate;
- decide whether execution was local or remote.

This keeps cluster identity outside engine-specific integration code.

### Transport responsibility

Remote transports remain responsible for carrying normalized requests and
results to and from an explicitly declared remote node.

Remote transports must not:

- choose the result node id;
- infer identity from a URL or network address;
- treat a remote self-reported identity as authoritative;
- rewrite routing policy;
- retry or fall back to another node.

The caller-owned selected remote declaration remains the cluster-facing
attribution authority for that execution.

### Successful results only

This RFC defines attribution only for successful `ClusterResult` values.

A failed request does not manufacture a successful result solely to carry
`node_id`. Failure visibility and structured failure attribution remain outside
this RFC.

### No fallback ambiguity

Current selected-candidate orchestration performs no retry and no fallback.
Therefore one successful result corresponds to one selected candidate and one
`node_id`.

Future RFCs introducing retry, fallback, delegated execution, or multi-node
workflows must revisit whether one `node_id` remains sufficient.

## Rationale

### Use the existing node id

The project already has an explicit cluster-facing node identity. Reusing it is
smaller and clearer than introducing a second result-specific identifier.

It also avoids coupling attribution to unstable or private infrastructure data
such as hostnames, IP addresses, runtime process ids, or model names.

### Attribute from the selected candidate

The selected candidate is already the explicit orchestration decision consumed
by execution. It is the narrowest existing source of truth for which cluster
node the orchestrator asked to handle the request.

Assigning attribution at that boundary keeps the rule deterministic and
consistent across local and declared remote execution.

### Keep adapters engine-specific

Adapters are engine-specific. Allowing them to choose node identity would mix
cluster architecture with runtime details and weaken engine independence. The
same adapter may run on multiple nodes.

### Keep transport metadata separate from identity

Addresses are transport metadata, not node identity. They may change while node
identity remains stable, and exposing them would unnecessarily leak network
details.

### Do not claim remote identity trust

The current LAN-only proof has no authentication, registration, or remote
identity protocol. Treating remote self-reporting as authoritative would imply a
trust guarantee the architecture does not provide.

Using the caller-owned static declaration is consistent with the accepted
manual declaration model and does not pretend to solve remote trust.

### Keep the response flat

A single required `node_id` field is sufficient for the Phase 3 requirement. A
nested routing explanation object would add vocabulary and compatibility surface
before the project needs it.

## Alternatives considered

### Keep adapter and model only

Rejected because adapter and model names do not identify a cluster node.

### Add a human-readable machine name

Rejected because machine names are not stable cluster identity and may expose
private infrastructure details.

### Add the remote transport address

Rejected because transport addresses are not node identity and should not become
part of the result contract.

### Let the receiving node report its own id

Rejected for this phase because there is no accepted remote identity or trust
protocol. The receiver may also use a local-only id different from the caller's
static declaration.

### Let the transport add the node id

Rejected because transport carries execution data; it does not own routing
identity. Attribution must work the same way for local and remote candidates.

### Make `node_id` optional

Rejected because optional attribution preserves the current ambiguity and does
not reliably satisfy the Phase 3 visibility requirement.

### Add a structured routing or execution object

Rejected as premature. One required field is enough for the current proof and
keeps future routing-explanation decisions open.

### Add a full node description

Rejected because it duplicates registry data, expands the result contract, and
exposes metadata not needed for attribution.

## Trade-offs

This decision makes successful results self-attributing within the
orchestrator's cluster model and completes the minimal Phase 3 visibility goal.

It adds one required field to the normalized result contract. Existing result
construction, tests, examples, and prototype callers must provide or handle a
node id.

The attribution represents the orchestrator-selected cluster identity, not a
cryptographically proven physical executor. This limitation is deliberate and
must remain explicit.

The flat field cannot describe retries, fallback chains, delegated execution, or
multi-node workflows. Those features do not exist in the current system and
must not shape the first attribution model.

## Impact

Implementation work must:

- add required `node_id` attribution to successful normalized results;
- assign it at local selected-candidate execution;
- assign it at declared remote selected-candidate execution;
- keep runtime adapters independent from node identity;
- keep transport addresses out of the public result;
- update API response examples and tests;
- repeat the static two-machine proof and confirm that the result identifies
  `declared-remote`;
- update Phase 3 current-state documentation after implementation.

This RFC does not activate remote routing by default. The ordinary application
remains local-only, and the explicit proof process remains caller-owned and
opt-in.

## Open questions

None for this RFC.

Future RFCs may need richer attribution if the project introduces retries,
fallback, delegation, multi-node workflows, or authenticated remote identity.

## Decision

Accepted.

Every successful normalized `ClusterResult` must contain a required `node_id`
string.

`node_id` is the cluster-facing id of the selected routing candidate whose
execution produced the successful result.

The selected-candidate execution boundary assigns this value from the candidate
it actually executes. Runtime adapters and remote transports do not own node
attribution.

This RFC covers successful results only. Failure attribution, structured routing
explanations, retries, fallback, delegated execution, multi-node workflows, and
authenticated remote identity remain outside its scope.
