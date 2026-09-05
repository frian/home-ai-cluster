# RFC-0106: Retained Local HAC Execution Limit

Status: Draft

Date: 2026-09-05

Author: frian

## Summary

Home AI Cluster should make the finite positive HAC execution concurrency limit
from Draft RFC-0105 one optional retained fact in the existing `hac config
local` ownership domain. The fact belongs to the local HAC application process
which enforces it; it is not caller-owned remote topology, remote availability,
or runtime capacity.

When absent, the effective HAC execution limit remains `1`, preserving the
RFC-0102/RFC-0104 first proof and the RFC-0105 implementation proof. A
retained value greater than `1` permits only that many overlapping HAC-owned
execution intervals in the ordinary composed local process. It makes no claim
about runtime concurrency or success.

This RFC adds no implementation, protocol, status, health, preflight,
scheduler, polling, or distributed state.

## Problem

Draft RFC-0105 establishes one finite positive, process-local HAC execution
concurrency limit but deliberately defines no operator configuration surface.
Its limit is a self-imposed HAC policy over RFC-0101 execution intervals, not
runtime capacity. The RFC-0105 implementation proof demonstrates that `1` is
the ordinary default and that a local limit of `2` is coherent, but that proof
does not decide how an operator selects a non-`1` value.

Accepted RFC-0094 already establishes separate retained ownership domains:

```text
config local -> facts belonging to this executing machine
config node  -> caller-owned static remote topology and eligibility
config show  -> local read-only retained-state inspection
```

The question is whether this HAC-owned process-local policy cleanly extends
the first domain without turning caller-owned remote declarations into remote
execution policy or availability state.

## Goals

- Retain one optional local HAC execution limit through `hac config local`.
- Keep the default effective limit `1` when the fact is absent.
- Preserve RFC-0105 finite-positive semantics and its shared process-local
  cardinality for originating local and receiver-side execution.
- Keep the retained fact distinct from runtime configuration and capacity.
- Preserve RFC-0094's local-versus-caller-side remote ownership boundary.
- Permit `hac config show` to inspect this retained local fact only.

## Non-goals

This RFC does not add remote execution-limit declarations, caller control of a
receiver limit, remote synchronization, advertising, active interval display,
remaining concurrency display, polling, heartbeat, runtime capacity
observation, runtime-specific concurrency settings, per-capability/model/
runtime/adapter limits, a scheduler, queue, waiting, fairness, balancing,
round robin, weights, priorities, reservations, distributed semaphore, dynamic
topology, or multi-process coordination.

It does not add a persistence file, configuration subsystem, profiles,
inheritance, named environments, generic settings, database, or configuration
schema-versioning framework.

## Proposal

### One retained local HAC policy fact

The existing `hac config local` domain should own one optional retained **HAC
execution limit**. It belongs to the executing machine's ordinary composed HAC
application process and is enforced only there.

The value follows Draft RFC-0105 exactly:

* it is a finite positive integer;
* its smallest value is `1`;
* zero, negative, non-integer, infinite, and unlimited values are invalid;
* absence has a distinct meaning: effective limit `1`; and
* a retained value greater than `1` authorizes at most that many overlapping
  HAC-owned execution intervals in that local process.

Invalid retained presence must fail locally and visibly under RFC-0094
retained-state validation. HAC must not silently replace an invalid explicit
value with `1`; only absence selects the default. Validation requires no
runtime or network observation.

### Local ownership, never caller-side remote ownership

The value is owned by the same machine which enforces it:

```text
Machine A: config local -> A's own HAC execution limit
Machine B: config local -> B's own HAC execution limit

Caller C: config node A -> A's node ID, URL, and capabilities only
Caller C: config node B -> B's node ID, URL, and capabilities only
```

`hac config node` and retained remote declarations remain unchanged. They must
not contain `execution_limit`, `available_slots`, `max_concurrency`,
`capacity`, `busy`, `load`, or equivalent facts.

A caller must not decide how much work a receiver allows itself to engage.
Duplicating a receiver-local limit in caller configuration would create stale
state and conflicting authority, and would conflict with RFC-0104's deliberate
absence of pre-transmission remote availability knowledge. A caller learns only
the request-specific grant or exact pre-execution refusal already established
by RFC-0104, never a receiver's configured limit or current cardinality.

### Effective local composition

At ordinary startup, the effective retained local HAC execution limit flows
only within the local application:

```text
retained local HAC execution limit
  -> effective local HAC composition
  -> RFC-0105 execution-interval limit
```

Exact class and function names are implementation details. The single effective
limit governs both established local boundaries in that process:

1. originating-process local execution; and
2. receiver-side execution before adapter invocation.

They consume the same RFC-0101 cardinality and RFC-0105 limit; this RFC does
not authorize separate hidden limits.

### Default and removal

When no retained local execution limit exists, effective behavior remains:

```text
no retained local execution limit -> effective HAC execution limit = 1
```

Operators are not required to configure the fact. An operator must be able to
remove or correct it through RFC-0094's existing bounded `config local`
correction/removal model; after removal, the effective limit returns to `1`.
The exact command spelling is implementation-level, because RFC-0094 leaves
local correction/removal spelling outside its architectural contract.

`config local` is the decided semantic mutation surface. A future spelling may
use an explicit `--execution-limit` flag if consistent with the existing CLI,
but this RFC does not freeze that spelling or add an invocation-time temporary
override. Whether such an override is useful is deferred.

### Local retained inspection only

RFC-0094 permits `hac config show` to display retained state. It may therefore
display the retained local HAC execution limit, for example:

```text
retained local HAC execution limit: 2
```

This is read-only local retained-state inspection. It does not observe runtime
or cluster truth and must not display active interval cardinality, remaining
concurrency, busy/free state, remote limits or cardinality, runtime load, or
runtime queue state. This RFC does not add the limit to `hac status`, `hac
health`, or `hac preflight`.

### Runtime and privacy boundaries

The HAC execution limit is local HAC application policy, semantically distinct
from the local runtime composition also retained by `config local`:

```text
runtime = ollama
model = example
HAC execution limit = 2
```

This does not configure Ollama, llama-server, or another runtime for
concurrency two. Changing runtime must not reinterpret the local HAC policy as
a runtime-specific fact. An operator can select a valid HAC value that performs
poorly for their runtime or machine; HAC does not auto-tune it or validate
runtime suitability.

The retained value is local configuration. It is not transmitted to callers,
does not persist current work, and introduces no telemetry, network
observation, prompt, request, or result data.

## Examples

### Default

```text
no retained local execution limit
-> effective limit = 1
```

### Local retained value

```text
Machine sat:
  retained local HAC execution limit = 2

sat ordinary HAC process:
  request A permitted
  request B permitted
  request C denied while A and B remain active
```

This makes no runtime-capacity statement.

### Different machines

```text
rasp:     local execution limit = 1
sat:      local execution limit = 2
debian-1: local execution limit = 1
```

Each machine owns and enforces its own value locally. No node learns another
node's configured limit.

### Caller declaration

```text
rasp config node sat:
  node ID
  URL
  capabilities

not:
  execution limit
```

## Alternatives considered

### Put the value in `config node`

Rejected. This would give a caller authority over receiver-local policy,
duplicate remote state, risk staleness, and violate RFC-0094 ownership.

### Advertise the value remotely

Rejected/deferred. RFC-0104's request-specific refusal already enables bounded
safe continuation without distributed state or remote availability knowledge.

### Treat it as runtime configuration

Rejected. The value is HAC policy, not runtime capacity or runtime
concurrency.

### Introduce a separate config command

Rejected. `config local` is the existing boring ownership surface.

### Keep the limit permanently fixed at 1

Valid conservative alternative, but RFC-0105's limit-2 proof shows that one
finite positive HAC-owned generalization is coherent. Explicit local operator
selection is useful without claiming HAC knows runtime suitability.

## Trade-offs

A retained local value greater than `1` gives an operator deliberate control
over HAC-level overlap, but requires them to choose a policy value without HAC
pretending to know runtime capacity. A valid configuration can be a poor
operational choice for a given runtime or machine. This is acceptable because
the value is explicit local operator policy and not a performance guarantee.

## Impact

This is architecture/documentation only. It changes no product behavior.

If accepted, later implementation may extend the existing retained local state,
its bounded `config local` mutation, `config show`, and ordinary local
composition; it must preserve default `1` and add focused tests. It must not
add a configuration framework, remote declaration field, runtime-capacity
claim, status observation, protocol, scheduler, polling, or distributed state.

## Open questions

- Whether an invocation-time temporary override is useful.
- Whether current active interval cardinality should ever have a separate
  operator observation surface.
- Whether future multi-process HAC needs coordination semantics.
- Whether evidence later justifies per-capability limits.

## Decision

Pending.
