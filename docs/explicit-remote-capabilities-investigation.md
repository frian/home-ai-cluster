# Explicit Remote Capabilities Investigation

Status: Complete

## Question

> Should ordinary static remote capabilities become explicitly
> operator-declared before Home AI Cluster adds a third functional capability?

**Outcome B — Explicit operator-declared remote capabilities.**

That outcome is already the accepted and implemented repository contract, not
a new architectural decision made by this investigation. RFC-0058 accepted it
on 2026-07-28; RFC-0059 subsequently added the separate caller-local
restriction surface. The smallest sufficient next step before a third
capability was therefore explicit remote declarations, and it has already
occurred. A third capability must not be implemented by extending the current
two-name default informally: its executable meaning and the bounded declaration
vocabulary need their own RFC first. [RFC-0058](../RFC/RFC-0058-explicit-static-remote-capabilities.md), [RFC-0059](../RFC/RFC-0059-caller-local-static-capabilities.md)

## Current Contract

### Capability ownership and vocabulary

The ordinary static capability vocabulary is closed to `chat` and `summarize`.
`DEFAULT_STATIC_CAPABILITY_NAMES` is exactly that ordered pair, and one shared
validator rejects empty lists, non-strings, unknown names, and duplicates while
preserving supplied order. This is a bounded declaration contract, not a
general capability registry. [`static_capabilities.py`](../src/home_ai_cluster/static_capabilities.py)

The caller-local node has the same compatibility default. A top-level TOML
`local_capabilities` field, or repeated inline `--local-capability`, restricts
only the fixed caller-side routing candidate. It does not change `hac local`,
receiver execution, adapter implementation, runtime health, or a remote
declaration. Omission retains `chat` plus `summarize`. [`static_cluster.py`](../src/home_ai_cluster/static_cluster.py), [RFC-0059](../RFC/RFC-0059-caller-local-static-capabilities.md)

### Ordinary remote declarations

Remote capabilities are now explicit, optional, static, and operator-owned:

```toml
[[remote_nodes]]
node_id = "remote-node"
base_url = "http://192.0.2.10:8000"
capabilities = ["chat", "summarize"]
```

The legacy flat one-remote TOML form accepts the corresponding optional
`remote_capabilities` field. The exactly-one-remote inline form accepts
repeatable `--remote-capability NAME`. TOML and inline construction share the
same validation and produce equivalent one-remote declarations. Omission in
any of these forms is valid and constructs the compatibility default `chat` plus
`summarize`; it does not trigger discovery or observation.
[`static_cluster_declaration.py`](../src/home_ai_cluster/static_cluster_declaration.py), [`static_cluster.py`](../src/home_ai_cluster/static_cluster.py), [`test_static_cluster_cli.py`](../tests/test_static_cluster_cli.py)

The capability set is created during caller-side declaration parsing or inline
argument validation, then copied into the remote `NodeDescription` by
`create_remote_declaration()`. It is fixed at process construction, is neither
runtime-derived nor observed, and is not duplicated as competing default sets:
the shared default constant is used by the parser and both construction paths.
[`static_cluster_declaration.py`](../src/home_ai_cluster/static_cluster_declaration.py), [`static_cluster.py`](../src/home_ai_cluster/static_cluster.py), [`test_static_cluster_declaration.py`](../tests/test_static_cluster_declaration.py)

### Eligibility, preflight, status, and execution

Remote candidate collection filters declared remotes by membership in the
constructed `NodeDescription.capabilities`, preserving declaration order. The
automatic path gives an eligible local candidate precedence; if it encounters
the accepted pre-request connection-unavailable failure, traversal tries only
eligible remotes in declaration order. A declared remote that lacks the
requested capability is never tried. [`remote_node.py`](../src/home_ai_cluster/core/remote_node.py), [`routing_candidates.py`](../src/home_ai_cluster/core/routing_candidates.py), [`ordered_remote_fallback.py`](../src/home_ai_cluster/core/ordered_remote_fallback.py)

Preflight is a local, network-free projection of constructed local and remote
capability lists. Its multi-remote test disables both the HTTP client and name
resolution while asserting explicit and default remote lists. Status is a
different contract: after declaration validation it reports coherence plus
local/remote application and runtime observations, and its public node result
does not include capabilities. [`static_preflight.py`](../src/home_ai_cluster/commands/static_preflight.py), [`test_multi_remote_static_preflight.py`](../tests/test_multi_remote_static_preflight.py), [`cluster_status.py`](../src/home_ai_cluster/cluster_status.py), [RFC-0058](../RFC/RFC-0058-explicit-static-remote-capabilities.md)

Accordingly, eligibility is an operator assertion about what the caller may
route to a remote. It does not verify that the receiver application, adapter,
or runtime can execute that capability. If an eligible receiver cannot execute
the request, the existing execution-time transport/runtime failure remains
authoritative; neither preflight nor status turns a declaration into a runtime
guarantee. [RFC-0058](../RFC/RFC-0058-explicit-static-remote-capabilities.md), [RFC-0016](../RFC/RFC-0016-declared-remote-routing-eligibility.md)

## Evidence

| Question | Current evidence |
| --- | --- |
| What does ordinary local declare by default? | `chat`, `summarize`; omission of `local_capabilities` preserves both. [`static_capabilities.py`](../src/home_ai_cluster/static_capabilities.py), [`test_static_cluster_declaration.py`](../tests/test_static_cluster_declaration.py) |
| What does an omitted remote declaration declare? | `chat`, `summarize` in ordered TOML, flat TOML, and inline construction. [`static_cluster_declaration.py`](../src/home_ai_cluster/static_cluster_declaration.py), [`static_cluster.py`](../src/home_ai_cluster/static_cluster.py), [`test_static_cluster_declaration.py`](../tests/test_static_cluster_declaration.py) |
| Can an operator express different remote sets? | Yes: `capabilities` per `[[remote_nodes]]`, `remote_capabilities` in flat TOML, and repeated inline `--remote-capability`. [`static_cluster_declaration.py`](../src/home_ai_cluster/static_cluster_declaration.py), [`test_static_cluster_cli.py`](../tests/test_static_cluster_cli.py) |
| Are invalid declarations rejected locally? | Yes: empty, duplicate, unknown, non-string, and non-array values fail parsing; preflight projects only validated data without network use. [`static_capabilities.py`](../src/home_ai_cluster/static_capabilities.py), [`test_static_cluster_declaration.py`](../tests/test_static_cluster_declaration.py), [`test_multi_remote_static_preflight.py`](../tests/test_multi_remote_static_preflight.py) |
| Does routing honor the declared set? | Yes: the heterogeneous proof records `chat`/`summarize` exclusion, and focused tests cover restricted caller-local plus remote eligibility. [`heterogeneous-static-capabilities-proof.md`](heterogeneous-static-capabilities-proof.md), [`caller-local-static-capabilities-proof.md`](caller-local-static-capabilities-proof.md), [`test_static_cluster.py`](../tests/test_static_cluster.py) |
| Is remote support verified? | No. The accepted contract explicitly keeps receiver/runtime verification outside static declarations, preflight, and status. [RFC-0058](../RFC/RFC-0058-explicit-static-remote-capabilities.md) |

## Third-Capability Pressure

The current architecture can represent the following existing-capability
topologies truthfully:

| Topology | Current result |
| --- | --- |
| Homogeneous: local and every remote declare both accepted capabilities | Supported by the compatibility default. |
| Local restricted, remote broad | Supported: `local_capabilities = ["chat"]` can exclude the caller-local candidate while a remote still declares both accepted capabilities. |
| Heterogeneous remotes | Supported: each remote can declare a non-empty unique subset of `chat` and `summarize`; membership controls eligibility. |
| Incorrect operator assumption | Representable only as an assertion: the caller can declare an eligible remote whose receiver cannot execute it. The failure is discovered at execution, not declaration or preflight. |

The third topology has a retained healthy-operation proof: a caller-local
`chat` candidate stays local, while a `summarize` request excludes it and
reaches a summarize-only remote. The remote-only heterogeneous proof separately
establishes that wrong-capability remotes are excluded. [`caller-local-static-capabilities-proof.md`](caller-local-static-capabilities-proof.md), [`heterogeneous-static-capabilities-proof.md`](heterogeneous-static-capabilities-proof.md)

For a future capability, the first two and the heterogeneous topology are not
automatically supported: the accepted vocabulary currently rejects every name
other than `chat` and `summarize`. Extending that vocabulary also requires an
executable request, adapter, transport, receiver, validation, and failure
contract. It is therefore a new architectural decision, not a parser-only
addition. [RFC-0051](../RFC/RFC-0051-bounded-text-summarization.md), [RFC-0058](../RFC/RFC-0058-explicit-static-remote-capabilities.md)

## Candidate Outcomes

### Outcome A — Keep the current compatibility contract

This is simple and backward-compatible for homogeneous personal clusters, but
adding a third capability to the shared default would make every omitted remote
eligible for it. That eligibility would still be an operator assumption, not
verified runtime fact. It cannot express heterogeneous remotes without the
already accepted explicit form, and broadening the default would make the
compatibility assertion larger. The current compatibility default remains
valuable for old two-capability declarations; it is not sufficient as the only
future capability contract.

### Outcome B — Explicit operator-declared remote capabilities

This is the accepted current contract. Omission remains valid with the
two-capability default; explicit sets are non-empty, unique, closed-vocabulary
lists whose order has no priority meaning. Remote declaration order remains the
deterministic priority rule. Preflight exposes declared lists, status does not,
and the declaration remains an assertion rather than receiver verification.
Inline and TOML parity is tested. [RFC-0058](../RFC/RFC-0058-explicit-static-remote-capabilities.md), [`test_static_cluster_cli.py`](../tests/test_static_cluster_cli.py)

For a third capability, this outcome supplies the necessary declaration shape,
but not permission to extend its vocabulary. A new RFC must decide the third
capability's bounded semantics and its compatibility-default treatment before
implementation.

### Outcome C — Receiver-reported remote capabilities

Receiver reporting would require a new remote request or endpoint, a trust
boundary for reported data, a lifecycle for startup- or request-time
observation, stale-data and failure rules, and compatibility behavior for older
receivers. It would couple caller and receiver beyond static declarations and
would begin dynamic capability observation. That is materially larger than the
current static, deterministic mode and is deferred.

### Outcome D — Declaration plus bounded verification

Comparing an operator declaration to a receiver-owned snapshot could expose a
mismatch more eagerly than Outcome B, but it still creates the reporting,
trust, staleness, request, and compatibility concerns in Outcome C. It also
needs rules for unreachable receivers and disagreement. It is not a small
validation extension because remote network activity would no longer be outside
declaration preparation and preflight. It is deferred.

### Outcome E — Add the third capability first

This would have been evidence-driven only before RFC-0058 if homogeneous
operation were the sole proven need. The repository now has stronger evidence:
explicit remote sets and healthy caller-local specialization are implemented,
tested, and retained in proofs. Adding a third capability must build on that
accepted contract, not temporarily enlarge the compatibility default and infer
heterogeneity later.

## Comparison with Dynamic Selection

This investigation is more valuable than busy/idle, measured-performance,
hardware-power, model-size, or estimated-latency selection because it preserves
an already bounded, capability-centered operator declaration boundary. Dynamic
selection would introduce observation frequency, metric definitions, trust and
privacy handling, stale state, failure and tie-breaking rules, policy ownership,
and a scheduler or scoring model. Those are separate architectural concerns;
the current remote order is intentionally deterministic and capability
membership only filters eligibility. [RFC-0040](../RFC/RFC-0040-multiple-explicit-static-remote-nodes.md), [RFC-0058](../RFC/RFC-0058-explicit-static-remote-capabilities.md)

## Decision

**Outcome B — Explicit operator-declared remote capabilities.**

The evidence supports it as the smallest sufficient step before a third
capability because it is already accepted in RFC-0058 and implemented with
bounded validation, compatibility omission, TOML/inline parity, deterministic
eligibility, network-free preflight, and unchanged status. It lets an operator
state heterogeneous remote eligibility without pretending to discover runtime
truth.

An RFC is required before a third capability is implemented: it must decide the
new executable capability and whether and how it enters the fixed static
vocabulary and compatibility default. No RFC is required to add explicit remote
capabilities themselves; that decision is already accepted. Implementation of
the explicit remote-capability contract has already preceded any third
capability.

## Required Follow-up

If a concrete third capability is proposed, first write an RFC that defines its
capability meaning, request and response boundaries, adapter and receiver
responsibilities, remote transport behavior, static declaration vocabulary,
compatibility omission behavior, validation, routing eligibility, and test/proof
scope. That RFC may reuse RFC-0058's bounded operator-declaration pattern, but
must not silently generalize it.

## Deferred Work

This investigation does not authorize receiver capability reporting or
verification, remote probing, discovery, polling, status capability lists,
cross-node negotiation, dynamic health/load/performance/hardware/model-aware
selection, scheduling, scoring, priority weights, a generic metadata model, or
any third capability. It retains local-first routing, remote declaration order,
privacy-first non-collection, and engine-independent adapter boundaries.
