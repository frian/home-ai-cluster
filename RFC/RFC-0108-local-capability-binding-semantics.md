# RFC-0108: Local Capability-Binding Semantics

Status: Draft

Date: 2026-09-05

Author: frian

## Summary

Home AI Cluster should permit one local HAC process to compose more than one
concrete runtime-adapter instance without changing its cluster-visible identity:
the process remains one local node. A local capability binding assigns one
non-empty, pairwise-disjoint set of cluster capabilities to exactly one
concrete adapter instance. A capability therefore has one local adapter owner
within a process, while a binding may assign several capabilities to that same
instance.

`RuntimeAdapter.name` remains a runtime-type identity such as `ollama`; it is
not an adapter-instance identifier. Consequently, two distinct Ollama adapter
instances are architecturally valid local binding targets even though both have
the name `ollama`.

This Draft deliberately decides no operator-facing input, retained
configuration, runtime-config shape, status, health, preflight, routing
explanation, remote protocol, or real-machine workflow. If accepted, it
authorizes only a bounded in-memory core proof, including a mandatory proof
using two distinct Ollama adapter instances in the same HAC process.

## Context

RFC-0042 and RFC-0043 deliberately establish one supported local runtime
composition for an ordinary process. RFC-0059 separately establishes
caller-local static routing capabilities, while RFC-0058 keeps remote
declarations capability-only. The current ordinary composition consequently
has one cluster-visible local node and one local runtime adapter.

That shape does not express the narrower architectural fact needed before any
operator-facing multiple-runtime work: a process may need to bind different
local capabilities to distinct concrete adapter instances. The missing decision
is neither a new node topology nor a request-level runtime choice. It is the
core ownership relationship from a local capability to one adapter instance
inside the existing local process.

The same-runtime case is essential. Two Ollama instances can differ by their
operator-managed endpoint or other adapter construction values while retaining
the same runtime type. Treating `RuntimeAdapter.name` as an instance key would
make that valid arrangement impossible and would incorrectly turn runtime type
into cluster-facing instance identity.

## Problem

The existing single-adapter local composition cannot state which concrete local
adapter instance owns each capability when more than one instance exists. A
naive extension risks one of several architectural errors:

- presenting one HAC process as multiple local cluster nodes;
- using the runtime type name as if it uniquely identified an adapter instance;
- allowing two local instances to claim the same capability without a defined
  selection rule; or
- leaking runtime or adapter-instance facts into remote declarations or a
  remote protocol.

Before configuration, observation, or a two-machine experiment are considered,
HAC needs a small, engine-independent core rule that makes local ownership
unambiguous and permits a same-runtime proof.

## Goals

- Define local capability binding independently of Ollama and any other
  runtime.
- Preserve one HAC process as one cluster-visible local node.
- Require every local binding to map a non-empty, disjoint capability set to
  exactly one concrete adapter instance.
- Permit multiple capabilities to share one binding and therefore one adapter
  instance.
- Explicitly support multiple instances of the same runtime type in one local
  process.
- Preserve `RuntimeAdapter.name` as runtime-type identity, not adapter-instance
  identity.
- Keep remote declarations and any remote protocol capability-only.
- Preserve the current single-runtime local behavior as a compatibility case.
- Authorize only a bounded in-memory core proof after acceptance, including two
  distinct Ollama instances.

## Non-goals

This RFC does not add or decide:

- operator configuration, retained configuration, a runtime-config file shape,
  CLI flags, environment-variable inputs, or any other operator-facing
  composition input;
- status, health, availability, preflight, runtime probing, readiness,
  routing-explanation, metrics, logging, tracing, or observation changes;
- routing policy, capability vocabulary, candidate order, local-first
  precedence, fallback, scheduling, balancing, priorities, weights, or direct
  adapter selection by a request;
- a new cluster-visible local node, local node identifiers, adapter-instance
  identifiers, adapter discovery, model inventory, runtime lifecycle, or
  runtime installation;
- remote declaration fields for runtime, adapter, model, binding, instance, or
  local composition facts; or a remote protocol change, negotiation, or
  receiver advertisement;
- a real-machine, cross-process, cross-host, or remote execution proof;
- a vLLM-specific rule, implementation, or proof; or any dependency on the
  Draft execution-availability work and its vLLM rails; or
- implementation other than the bounded in-memory core proof explicitly
  authorized on acceptance.

## Proposal

### One local node, with local bindings

One HAC process continues to expose exactly one cluster-visible local node. A
local binding is process-local composition data; it does not create another
node, endpoint, topology member, remote declaration, or request attribute.

Conceptually, a process-local local composition has one local node and a finite
collection of bindings:

```text
one HAC process
  -> one cluster-visible local node
  -> local capability bindings
       {capability set} -> one concrete adapter instance
```

The exact public type, constructor, storage, and symbol names remain
implementation details. This RFC defines semantic constraints, not a
configuration representation or a generic dependency-injection framework.

### Binding validity

Each binding has exactly these semantic parts:

```text
LocalCapabilityBinding
  capabilities: non-empty set of cluster capabilities
  adapter: one concrete RuntimeAdapter instance
```

Every binding must contain at least one capability and exactly one concrete
adapter instance. Its capability set may contain more than one capability;
those capabilities share that one adapter instance.

Within one local composition, binding capability sets must be pairwise disjoint.
A local capability may therefore be bound to exactly one adapter instance. An
overlap is invalid composition and must fail locally before a request is
executed. This first scope deliberately introduces no local adapter-selection,
priority, fallback, or conflict-resolution rule.

The proposal does not infer bindings from adapter method names, runtime health,
models, endpoint addresses, or `RuntimeAdapter.name`. Binding ownership is
explicit local composition data.

### Runtime type is not adapter instance identity

`RuntimeAdapter.name` continues to mean runtime type identity only. Its value
may identify `ollama`, `llama-server`, `vllm`, or another adapter family, but it
must not be used as a unique key for a concrete adapter instance.

Multiple distinct adapter instances with equal `name` values are valid binding
targets. In particular, a process may contain two distinct Ollama adapter
instances. Their distinction is local object/construction identity; this RFC
does not introduce a serialized, operator-visible, request-visible,
cluster-visible, or remote-visible adapter-instance ID.

This rule is engine-independent. Ollama is required only as the first
same-runtime proof target, not as a core binding concept.

### Capability-only cluster and remote boundary

Local binding decides only which local adapter instance receives an already
selected local capability execution. Cluster-facing eligibility and routing
continue to reason in capabilities, according to their existing accepted
boundaries. A request does not select an adapter, runtime, model, binding, or
instance.

Remote declarations remain capability-only caller-owned topology data. They
must not contain runtime type, adapter name, adapter-instance identity, local
binding representation, or endpoint construction details. A remote protocol,
if and where one exists, remains capability-only under this RFC. This decision
does not create cross-process binding agreement or remote binding validation.

### Backward compatibility

The current ordinary single-runtime composition remains valid without changed
operator behavior. It is the degenerate binding collection: the existing local
capability set maps to its existing one concrete local adapter instance.

No existing request, result, declaration, status, health, preflight, or
routing-explanation contract changes. No current single-runtime invocation
requires a new value or migration.

## Authorized acceptance proof

Acceptance authorizes only one bounded in-memory core proof. It must not add
operator configuration, retained state, runtime-config parsing, status, health,
preflight, routing-explanation, remote protocol, network listener, or
real-machine work.

The proof must establish all of the following:

1. one composed HAC process remains represented as one cluster-visible local
   node;
2. a non-empty binding maps each of its capabilities to its exact concrete
   adapter instance;
3. several capabilities may share a single binding and reach that binding's
   adapter instance;
4. overlapping capability bindings are rejected before execution and no
   selection policy is silently introduced;
5. the existing one-adapter local composition continues to execute through its
   existing adapter behavior; and
6. two distinct Ollama adapter instances with the same `RuntimeAdapter.name`
   can be bound to disjoint local capabilities in one HAC process, and each
   bound capability reaches its designated instance.

The mandatory Ollama proof may use in-memory or test-double transport beneath
the concrete Ollama adapter instances. It must prove distinct adapter-instance
ownership, not merely two references to one instance, two different runtime
names, or two separately running HAC processes. It must neither contact a real
Ollama service nor make a real-machine claim.

## Consequences

The core gains one explicit, testable local ownership rule while preserving the
cluster's capability-centered surface. It makes a same-runtime multi-instance
composition architecturally possible without prematurely deciding how an
operator constructs, persists, observes, validates, or explains it.

The deliberate cost is that there is no ordinary user-facing way to request or
inspect such a composition yet. That is intentional: configuration and
observation would introduce independent product and compatibility contracts and
must follow only after the in-memory and same-runtime proof establishes the
core semantics.

## Alternatives considered

### Keep exactly one local adapter indefinitely

Rejected. It prevents a same-runtime multi-instance arrangement before its core
semantics can be proven, and it treats a current composition limitation as an
architectural identity rule.

### Use `RuntimeAdapter.name` as the binding key

Rejected. A runtime type is not an adapter-instance identity. This would forbid
two Ollama instances and couple core binding semantics to a runtime-name
uniqueness rule that adapters do not promise.

### Create one local node per adapter instance

Rejected. It changes one process into a multi-node topology, broadens node
identity and status semantics, and makes local adapter composition look like
remote topology. None is needed for the bounded core proof.

### Permit overlapping bindings and select later

Rejected for this first scope. It would require a priority, fallback,
scheduling, or selection policy. Pairwise-disjoint capability sets make
ownership unambiguous without creating that policy.

### Start with operator configuration or status

Rejected. Those surfaces would freeze composition and observation contracts
before the core rule and same-runtime behavior are proven in memory.

### Make remote declarations runtime-aware

Rejected. Remote topology remains capability-only and caller-owned. Local
adapter binding provides no reason to expose runtime or instance facts across a
remote boundary.

## Deferred follow-up sequence

This RFC intentionally establishes only the first two steps:

```text
core binding semantics
        ↓
bounded in-memory proof, including two distinct Ollama instances
        ↓
later operator configuration
        ↓
later observation/status
        ↓
later real-machine proof
```

Each later step requires its own explicit decision. Acceptance of this RFC does
not imply acceptance of any configuration, observation, or real-machine design.

## Open questions

- After the bounded proof, what is the smallest operator-owned composition
  input that can express local bindings without revising retained-configuration
  ownership prematurely?
- What bounded observation/status information, if any, is necessary to explain
  a binding without exposing runtime or adapter-instance identity as a new
  cluster-facing contract?
- What real-machine proof can demonstrate same-runtime behavior while preserving
  one local node per HAC process and capability-only remote declarations?

## Decision

Draft. No implementation is authorized until this RFC is accepted. If accepted,
authorization is limited to the bounded in-memory core proof defined above.
