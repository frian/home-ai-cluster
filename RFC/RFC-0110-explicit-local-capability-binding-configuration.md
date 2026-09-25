# RFC-0110: Explicit Local Capability-Binding Configuration

Status: Accepted

Date: 2026-09-06

Author: frian

## Summary

Home AI Cluster should extend the existing explicitly selected
`--runtime-config PATH` boundary from RFC-0074 with one alternative, closed
TOML document shape for constructing the local capability bindings accepted by
RFC-0108. The existing RFC-0074 single-runtime document remains valid,
unchanged, and is the degenerate one-binding compatibility case.

A multi-binding document contains a finite non-empty collection of explicit,
pairwise-disjoint capability bindings. Each binding constructs exactly one
concrete adapter instance from already accepted runtime-specific facts. The
binding relation, not adapter name or declaration order, remains authoritative
for capability-to-instance ownership. One HAC process remains exactly one
cluster-visible local node.

This proposal adds neither retained multi-binding configuration nor a general
configuration system. It decides no multiple-adapter status, health,
preflight, routing-explanation, inspection, remote declaration, or protocol
semantics. In particular, a multi-binding document is not accepted by the
existing `status` surface until a separate observation decision exists.

A valid multi-binding document is an ordinary request-capable local-composition
source for both `local` and `static-cluster`. Its binding union remains separate
from RFC-0059's caller-side local routing permission in static-cluster mode.

## Context

RFC-0074 establishes one optional explicitly selected, closed TOML source for
constructing the ordinary local runtime adapter. RFC-0094 keeps that source
self-contained: selecting `--runtime-config PATH` bypasses the retained local
runtime-composition baseline for that invocation. RFC-0107 extends the closed
ordinary runtime set with vLLM and its loopback base URL plus served-model
identity.

RFC-0108 then establishes the missing process-local semantic: a capability
binding maps one non-empty, explicit capability set to one concrete adapter
instance; binding sets are pairwise disjoint; and their union is local
execution-capability truth. Its bounded in-memory proof deliberately leaves
operator input and observation for later decisions.

The next small question is which explicit operator input can construct that
already accepted relation without inventing retained state, a second general
configuration mechanism, or multi-adapter observation semantics.

## Problem

The accepted binding semantics have no bounded operator-facing construction
form. Continuing to require in-memory construction prevents an operator from
expressing more than one local adapter instance in one ordinary HAC process.

Adding a new configuration source, generic runtime options, binding IDs, or
adapter-name lookup would broaden the architecture unnecessarily. Extending
the existing status or retained-configuration surfaces at the same time would
also decide separate observation and persistence contracts before they are
needed.

## Goals

- Reuse RFC-0074's explicit-path-only `--runtime-config PATH` boundary.
- Preserve the existing RFC-0074 single-runtime TOML shape unchanged.
- Define one alternative closed TOML shape for a finite non-empty collection
  of local capability bindings.
- Construct each binding from only already accepted runtime-specific facts.
- Preserve RFC-0108's explicit, disjoint, truthful capability-to-concrete-
  adapter ownership semantics.
- Preserve one HAC process as one cluster-visible local node.
- Keep caller-local RFC-0059 routing permission separate from local execution
  ownership.
- Accept a valid multi-binding document for ordinary request-capable `local`
  and `static-cluster` composition, including static-cluster's accepted
  explicit topology input modes.
- Preserve remote declarations and the HAC-to-HAC protocol as capability-only.
- Define focused later implementation proof criteria and compatibility rules.

## Non-goals

This RFC does not add:

- retained multi-binding state, `hac config` commands, or changes to the
  retained-configuration storage shape;
- a second config source, automatic discovery, reload, watch, includes,
  inheritance, profiles, or environment-variable selection;
- generic provider options, arbitrary key/value maps, plugin-like runtime
  options, adapter factories, provider IDs, runtime discovery, or model
  discovery;
- a serialized adapter-instance ID, a binding ID, or adapter-name-based
  instance selection;
- routing priority, adapter selection, scheduling, load balancing, capacity
  claims, runtime worker configuration, per-binding limits, or per-adapter
  limits;
- status, health, preflight, routing explanation, adapter-instance
  observation, configuration inspection, or `hac config local` changes;
- remote runtime, model, binding, adapter, or instance facts; remote protocol
  changes; or local binding advertisement;
- real-machine proof, dynamic mutation, database, daemon/service manager,
  Docker, Kubernetes, or dashboard work.

## Proposal

### One existing explicit source, two complete shapes

`--runtime-config PATH` remains the only selection mechanism. It remains an
explicit path: HAC performs no automatic configuration discovery or source
selection.

The path selects exactly one of two complete, closed document shapes:

1. the existing RFC-0074 single-runtime document; or
2. the multi-binding document defined below.

They are alternatives, not layers. A document must not mix their keys or
tables. A document containing `[[bindings]]` must contain no RFC-0074
single-runtime `runtime` root key or runtime-specific root table. Conversely,
an RFC-0074 document must not contain `bindings`. Unknown keys and tables fail
locally before application construction or execution.

The RFC-0074 shape, including its spelling and semantics, remains unchanged.
It remains the compatibility representation of one concrete adapter and its
existing local capability set.

### Closed multi-binding document

A multi-binding document has no root configuration facts. It contains one or
more `[[bindings]]` entries. Each entry has a non-empty `capabilities` array,
one `runtime`, and exactly the facts already accepted for that runtime:

```toml
[[bindings]]
capabilities = ["chat", "summarize"]
runtime = "ollama"
model = "llama3.2"
disable_thinking = true

[[bindings]]
capabilities = ["classify", "code"]
runtime = "vllm"
base_url = "http://127.0.0.1:8000"
model = "Qwen/Qwen2.5-0.5B-Instruct"
```

The accepted closed per-binding runtime forms are:

```text
runtime = "ollama"
  required: capabilities
  optional: model, disable_thinking

runtime = "llama-server"
  required: capabilities, base_url, model

runtime = "vllm"
  required: capabilities, base_url, model
```

`base_url` for llama-server and vLLM retains the separately accepted loopback
HTTP base-URL rules. `model` for llama-server retains its accepted model
identifier meaning; `model` for vLLM retains RFC-0107's served-model API
identity meaning. Each has its runtime-specific validation. The common spelling
does not make the meanings generic.

For Ollama, the only configurable facts remain the optional model and optional
thinking-disable choice accepted by RFC-0071 and RFC-0073. This RFC does not
add an operator-facing Ollama base URL merely because the adapter has an
internal constructor value for one.

No binding may contain a key for another runtime, an arbitrary option map, or a
runtime-specific fact not listed above. Runtime construction must not discover
models, runtimes, or capabilities, contact a runtime, or manage its lifecycle.

### Binding semantics and validation

The TOML entries are explicit construction input for RFC-0108 bindings. A
valid multi-binding document has a finite, non-empty collection of bindings.
For every binding:

- `capabilities` is a non-empty explicit set in the accepted capability
  vocabulary, with no duplicate values;
- its capability set is pairwise disjoint from every other binding's set;
- its closed runtime facts construct exactly one concrete adapter instance;
- its capability set satisfies RFC-0108's subset rule against that exact
  instance's supported capabilities; and
- no assignment is inferred from `adapter.capabilities()`, an adapter name,
  runtime health, a model, or an endpoint.

Invalid shape, empty binding collection, empty or duplicate capability values,
overlap, unsupported assignment, or invalid runtime-specific facts fail locally
before execution. The implementation may use its existing local error boundary;
this RFC creates no new public request failure contract.

The local execution-capable set is exactly the union of valid binding capability
sets. Once an already selected local capability reaches execution, its binding
selects the exact concrete adapter object. `RuntimeAdapter.name` is not an
adapter-instance key. Two separately constructed `OllamaAdapter` objects with
`name == "ollama"` remain valid targets for different disjoint bindings.

Binding declaration and construction order have no routing priority or
adapter-selection meaning. Reversing it must not change capability ownership.
There is no binding ID because the explicit capability-to-concrete-object
relation is sufficient within the process.

### One local node and separate caller permission

The multi-binding document changes only process-local construction. One HAC
process still presents exactly one cluster-visible local node; bindings do not
create nodes, endpoints, topology members, or request fields.

RFC-0059 caller-local static capabilities remain caller-side routing permission.
They are not inferred from the multi-binding union and do not configure, alter,
narrow, expand, or otherwise mutate the binding collection. A caller-local
permission may be narrower than local execution truth without changing binding
ownership:

```text
binding union             -> receiver/process-local execution ownership
RFC-0059 local capability -> caller-side routing permission
```

A valid multi-binding `--runtime-config PATH` is accepted by ordinary
request-capable `local`. It is also accepted by ordinary request-capable
`static-cluster`, including its accepted explicit declaration and complete
inline topology input modes. In static-cluster local-candidate use, a requested
capability is locally usable only when both independent truths hold:

```text
requested capability is in the RFC-0108 binding union
    AND
RFC-0059 caller-local permission allows that capability locally
    -> local static-cluster candidate may be eligible
```

Caller permission narrower than the binding union may prevent local selection,
but it does not remove or reassign any binding. Conversely, a caller-local
permission containing a capability that has no local binding does not create
local execution capability, infer a binding, or select an adapter. Binding
ownership remains determined only by the explicit binding relation.

This RFC does not collapse RFC-0108 and RFC-0059 by treating one fact as the
other. A later implementation must preserve their separation even where the
current single-adapter static-cluster construction carries its caller-local
capability restriction into local composition construction. That existing
construction is implementation evidence, not an authorization to make caller routing
permission binding ownership in the multi-binding path.

Remote declarations remain caller-owned capability-only topology facts. They
must not contain a runtime, model, binding, adapter, or instance fact. HAC does
not advertise local binding information, and this RFC changes neither the
HAC-to-HAC request nor status protocol.

Existing remote candidate behavior remains governed by its accepted routing
rules. This RFC adds no fallback, priority, scheduling, or adapter-selection
policy.

### Existing configuration and execution-policy boundaries

Legacy runtime-composition CLI arguments remain mutually exclusive with an
explicitly selected runtime-config source as RFC-0074 already defines. This RFC
adds no CLI-over-file or file-over-CLI precedence. Selecting a multi-binding
document cannot be combined with those arguments.

RFC-0094 retained configuration remains a separate layer. This RFC adds no
retained multi-binding data. Selecting `--runtime-config PATH` continues to
bypass the retained local runtime-composition baseline for that invocation; it
does not bypass unrelated retained local HAC policy.

In particular, RFC-0106's retained `execution_limit` remains process-level HAC
execution-permission policy. It is not adapter capacity, runtime worker count,
model concurrency, or binding capacity. It remains outside the runtime-
composition document and is neither replaced nor partitioned by binding data.

### Observation boundary and `status`

RFC-0108 sequences operator configuration before any later observation/status
decision. Therefore this RFC adds no representation for multiple local adapters
in status, health, preflight, routing explanation, or configuration inspection.

RFC-0074 currently applies its single-runtime file contract to `status`. That
legacy behavior remains compatible: `status --runtime-config PATH` accepts an
RFC-0074 single-runtime document exactly as before. A multi-binding document at
that surface must fail locally before status observation or runtime contact.
This is the smallest fail-closed boundary: it neither silently chooses one
adapter nor invents aggregate multi-adapter status semantics.

No preflight output or behavior is changed, and no multi-binding inspection
surface is introduced. `health` is not expanded: its current surface gains
neither `--runtime-config` nor multi-adapter semantics.

## Compatibility

Existing valid RFC-0074 single-runtime documents remain valid, unchanged, and
produce existing behavior. They are the degenerate one-binding case; no current
operator needs a migration. Existing CLI-only and zero-argument behavior remain
outside file mode and unchanged.

Existing `--runtime-config` explicit-path selection, missing/invalid-file local
failure behavior, and supplied-argument mutual exclusion remain authoritative.
The selected document does not merge with CLI or retained runtime-composition
facts. Caller-local capability permission, remote topology, requests, results,
routing, and remote protocol remain unchanged.

The only intentional compatibility restriction is observational: an existing
single-runtime file remains accepted by `status`, while the new multi-binding
shape is rejected there until a separate RFC decides truthful multiple-adapter
observation. `health` remains unchanged and does not accept a runtime-config
source. After its bounded implementation proof, ordinary request-capable
`local` and `static-cluster` composition may use the new shape; static-cluster
retains the independent RFC-0108 execution-ownership and RFC-0059 caller-
permission requirements for local candidate use.

## Rationale

Reusing the already explicit RFC-0074 path is smaller than creating a second
operator-facing configuration system and keeps the source visibly
process-local. Two complete document shapes avoid difficult merging and retain
the legacy schema exactly.

An array of closed binding entries states the new fact directly: each explicit
capability set belongs to a concrete adapter constructed from known facts. It
does not turn runtime names, models, or adapter names into request-routing
inputs. Pairwise disjoint sets avoid an unchosen selection policy, while the
same-runtime case prevents a false uniqueness requirement for adapter names.

Keeping retained configuration, execution policy, topology, and observation
outside the document preserves their distinct owners and prevents the binding
schema from becoming a general local-machine configuration format.

## Alternatives considered

### A separate multi-binding configuration mechanism

Rejected. RFC-0074 already provides an explicit, closed process-local source.
A second source would create needless selection and precedence semantics.

### Extend the RFC-0074 single-runtime shape in place

Rejected. Mixing a root single runtime with a collection changes a valid legacy
document's meaning and invites partial hybrid documents. Complete alternatives
preserve compatibility and fail closed.

### Infer bindings from adapter capabilities or adapter names

Rejected. RFC-0108 requires explicit ownership, and adapter names are not
concrete-instance identity. Either inference would fail the two-Ollama-instance
case or silently assign capabilities.

### Add binding IDs or use declaration order as a tie-breaker

Rejected. Pairwise-disjoint explicit capability ownership provides the needed
local relation. IDs and ordering would imply a selection surface that this RFC
does not need or decide.

### Add an Ollama base URL, generic runtime options, or provider factories

Rejected. They would expand accepted operator-facing construction facts and
turn a closed composition document into a generic provider framework.

### Add retained multi-binding configuration now

Rejected. RFC-0094's retained domain is a separate architectural layer. One
explicit-path proof is sufficient before persistence is considered.

### Make multi-binding status work by aggregating or selecting an adapter

Rejected. Either choice would define observation semantics prematurely and
could hide the distinct adapter instances. Failing closed preserves truthful
legacy status behavior.

## Trade-offs

The proposal adds one alternative TOML shape and validation work. Operators
must state every binding capability explicitly, even when an adapter supports
more capabilities. This is intentional: explicit ownership is clearer than
implicit adapter-derived composition.

The initial shape cannot be inspected through status and cannot be retained.
Those omissions make the first configuration step less convenient, but avoid
premature persistence and observation contracts while preserving a small,
operator-owned execution path.

## Implementation boundary

If accepted, implementation is authorized only to:

- parse and validate the alternative closed multi-binding runtime-config shape;
- construct its concrete local adapter instances and RFC-0108 binding relation
  for ordinary request-capable `local` and `static-cluster` execution
  composition, including static-cluster's accepted explicit topology inputs;
- preserve the distinction between the binding union as local execution truth
  and RFC-0059 caller-local permission as static-cluster routing permission;
- retain the existing RFC-0074 single-runtime path unchanged;
- reject a multi-binding file on the existing status surface before observation;
- add focused tests and accurate operator documentation.

It must not add retained state or `hac config` changes; status, health,
preflight, routing-explanation, or inspection semantics; remote declaration or
protocol changes; real-machine proof; reload or mutation; scheduling; capacity
or worker controls; per-binding/adaptor limits; discovery; database; daemon;
Docker/Kubernetes; or dashboard work.

## Proof expectations

A later implementation must prove all of the following:

1. an existing RFC-0074 single-runtime configuration remains valid and has its
   existing behavior;
2. one multi-binding configuration constructs one HAC process with one
   cluster-visible local node and at least two explicit bindings;
3. disjoint capability sets are enforced before execution;
4. an empty capability set is rejected;
5. an unsupported binding capability assignment is rejected;
6. the union of binding capability sets is local execution-capability truth;
7. a capability reaches the exact concrete adapter instance assigned by its
   binding;
8. two distinct concrete `OllamaAdapter` instances whose `name == "ollama"`
   can be constructed from explicit operator input and own different disjoint
   capabilities;
9. reversing binding declaration/construction order does not change
   capability-to-adapter ownership;
10. RFC-0059 caller-local routing permission remains separate from binding
    ownership;
11. in an in-memory static-cluster case with deliberately different binding
    union and RFC-0059 caller-local permission, caller permission does not
    mutate bindings and a local capability is usable only when both execution
    ownership and caller permission allow it;
12. legacy runtime CLI and explicit runtime-config mutual exclusion remains
    intact;
13. retained process-level `execution_limit` remains separate and is not
    replaced by runtime-config binding data;
14. remote declarations and protocol shapes do not change; and
15. no new observation or status semantics are introduced, including local
    rejection of a multi-binding file by `status`.

The same-runtime Ollama proof may use distinct models, which are already
accepted Ollama configuration facts, to demonstrate two separately constructed
adapters. It must not add an Ollama endpoint configuration decision or contact
a real Ollama service. The static-cluster proof may remain in memory and must
not require a real remote machine or new protocol behavior.

## Open questions

- What is the smallest truthful status or health representation for multiple
  local adapters, if one is needed after this explicit execution path is
  proven?
- Should retained configuration ever represent multi-bindings, and if so, what
  narrow ownership and correction surface would preserve RFC-0094's boundaries?
- What later real-machine proof, if any, is sufficient without exposing local
  binding facts remotely?

None of these questions is answered or authorized by this RFC.

## Decision

Accepted. Home AI Cluster accepts one alternative, closed multi-binding TOML
document selected only through `--runtime-config PATH`, while preserving the
existing RFC-0074 single-runtime document unchanged. Acceptance authorizes
only the bounded request-capable `local` and `static-cluster` composition path,
with fail-closed multi-binding `status`; it does not authorize retained
multi-binding configuration, observation/health changes, remote protocol
changes, or the other deferred work defined by this RFC.
