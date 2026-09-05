# RFC-0106: Retained Local HAC Execution Limit

Status: Accepted

Date: 2026-09-05

Author: frian

## Summary

Home AI Cluster should make the finite positive HAC execution concurrency limit from Accepted RFC-0105 one optional retained fact in the existing Accepted RFC-0094 `hac config local` ownership domain.

The fact belongs to the local HAC application process which enforces it. It is not caller-owned remote topology, remote availability, or runtime capacity.

When absent, the effective HAC execution limit remains `1`. A retained value greater than `1` permits only that many overlapping HAC-owned execution intervals in the ordinary composed local process. It makes no claim about runtime concurrency or success.

This RFC adds no new configuration subsystem, protocol, status, health, preflight, scheduler, polling, balancing, or distributed state.

## Problem

Accepted RFC-0105 establishes one finite positive process-local HAC execution concurrency limit while deliberately leaving ordinary operator selection out of scope. Its implementation proof preserves ordinary effective limit `1` and demonstrates that a non-`1` internal limit can be enforced coherently.

Accepted RFC-0094 already establishes three retained configuration surfaces with separate ownership:

```text
config local -> facts belonging to this executing machine
config node  -> caller-owned static remote topology and eligibility
config show  -> local read-only retained-state inspection
```

The remaining question is whether the HAC-owned process-local execution limit belongs in the first domain without turning caller-owned remote declarations into remote execution policy or availability state.

## Goals

This RFC should:

- retain one optional local HAC execution limit through `hac config local`;
- keep the effective limit `1` when the retained fact is absent;
- preserve RFC-0105 finite-positive semantics;
- apply the same retained value to the shared process-local execution interval policy used by originating-local and receiver-side execution;
- keep the retained fact distinct from runtime composition and runtime capacity;
- preserve RFC-0094's local-versus-caller-side remote ownership boundary; and
- permit `hac config show` to inspect this retained local fact only.

## Non-goals

This RFC does not add:

- remote execution-limit declarations;
- caller control of a receiver's limit;
- remote synchronization or advertisement;
- active interval or remaining-concurrency display;
- polling, heartbeat, remote availability state, or runtime-capacity observation;
- runtime-specific concurrency settings;
- per-capability, per-model, per-runtime, or per-adapter limits;
- a scheduler, queue, waiting, fairness, balancing, round robin, weights, priorities, reservations, or distributed semaphore;
- dynamic topology or multi-process coordination;
- a new persistence file, general configuration subsystem, profiles, inheritance, named environments, database, or schema-versioning framework; or
- an invocation-time temporary execution-limit override.

## Proposal

### One retained local HAC policy fact

The existing `hac config local` domain should own one optional retained **HAC execution limit**.

The value follows Accepted RFC-0105 exactly:

- it is a finite positive integer;
- its smallest value is `1`;
- zero, negative, non-integer, infinite, and unlimited values are invalid;
- absence means an effective limit of `1`; and
- a retained value greater than `1` permits at most that many overlapping HAC-owned execution intervals in that local process.

Invalid retained presence must fail locally and visibly under RFC-0094 retained-state validation. HAC must not silently replace an invalid explicit value with `1`; only absence selects the default. Validation requires no runtime or network observation.

### Local ownership only

The value is owned by the same machine which enforces it:

```text
Machine A: config local -> A's HAC execution limit
Machine B: config local -> B's HAC execution limit

Caller C: config node A -> A's node ID, URL, and capabilities only
Caller C: config node B -> B's node ID, URL, and capabilities only
```

`hac config node` and retained remote declarations remain unchanged. They must not contain `execution_limit`, `available_slots`, `max_concurrency`, `capacity`, `busy`, `load`, or equivalent facts.

A caller must not decide how much work a receiver allows itself to engage. Duplicating a receiver-local limit in caller configuration would create stale state and conflicting authority and would conflict with RFC-0104's deliberate absence of pre-transmission remote execution-permission knowledge.

A caller learns only the request-specific grant or exact pre-execution refusal already established by RFC-0104, never a receiver's configured limit or current cardinality.

### Effective local composition

At ordinary startup, the effective retained local HAC execution limit flows only within the local application:

```text
retained local HAC execution limit
  -> effective local HAC composition
  -> RFC-0105 execution-interval limit
```

Exact class and function names are implementation details.

The single effective limit governs both already-established local boundaries in that process:

1. originating-process local execution; and
2. receiver-side execution before adapter invocation.

They consume the same RFC-0101 cardinality and RFC-0105 limit. This RFC does not authorize separate hidden limits.

### Independence from runtime-composition source

The HAC execution limit is local HAC application policy, semantically distinct from the local runtime composition also owned by `config local`.

Accepted RFC-0094 keeps `--runtime-config PATH` as an explicitly selected, self-contained **runtime-composition** source. Selecting `--runtime-config PATH` therefore bypasses the retained local runtime-composition baseline for that invocation, but it does not suppress an independently retained HAC execution limit.

Conceptually:

```text
retained local execution limit = 2
explicit --runtime-config PATH

-> runtime composition comes from PATH
-> HAC execution limit remains 2
```

This does not merge runtime-specific fields across sources. The retained execution limit is simply outside the runtime-composition domain being replaced.

A future explicit invocation-time execution-limit override would require a separate decision; this RFC defines none.

### Default and correction

When no retained local execution limit exists:

```text
no retained local execution limit -> effective HAC execution limit = 1
```

Operators are not required to configure the fact.

The fact must be correctable or removable through RFC-0094's existing bounded `config local` mutation model. Exact CLI spelling for correction or removal remains implementation-level, consistent with RFC-0094.

A spelling such as `--execution-limit` is acceptable if it remains a narrow field on `config local`; this RFC does not create a generic settings mechanism.

### Local retained inspection only

Accepted RFC-0094 permits `hac config show` to display retained state. It may therefore display the retained local HAC execution limit.

This is read-only local retained-state inspection. It does not observe runtime or cluster truth and must not display:

- active interval cardinality;
- remaining concurrency;
- busy/free state;
- remote limits or cardinality;
- runtime load; or
- runtime queue state.

This RFC does not add the limit to `hac status`, `hac health`, or `hac preflight`.

### Runtime-capacity boundary

The retained HAC execution limit is not runtime configuration or runtime capacity.

For example:

```text
runtime = ollama
model = example
HAC execution limit = 2
```

means only that HAC permits itself up to two overlapping HAC-owned execution intervals in that process. It does not configure Ollama for concurrency two and does not claim Ollama can execute two requests concurrently.

Changing runtime must not reinterpret the retained HAC execution limit as a runtime-specific fact. An operator can choose a valid HAC value that performs poorly for a particular runtime or machine; HAC does not auto-tune it or validate runtime suitability.

### Privacy and network boundary

The retained value remains local configuration. It is not transmitted to callers, advertised to remote nodes, or used as remote pre-screening state.

It does not persist active work and introduces no telemetry, network observation, prompt, request, or result data.

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

Each machine owns and enforces its own value locally. No node learns another node's configured limit.

### Caller declaration

```text
rasp config node sat:
  node ID
  URL
  capabilities

not:
  execution limit
```

### Explicit runtime composition source

```text
sat retained local execution limit = 2
sat starts with --runtime-config PATH

runtime composition -> PATH
HAC execution limit -> retained local value 2
```

## Alternatives considered

### Put the value in `config node`

Rejected. This would give a caller authority over receiver-local policy, duplicate remote state, risk staleness, and violate RFC-0094 ownership.

### Advertise the value remotely

Rejected for this increment. RFC-0104 request-specific refusal already enables bounded safe continuation without distributed state or remote availability knowledge.

### Treat it as runtime configuration

Rejected. The value is HAC policy, not runtime capacity or runtime concurrency.

### Let `--runtime-config` disable the retained limit

Rejected. `--runtime-config` replaces the runtime-composition domain under RFC-0094. The HAC execution limit is a separate local HAC policy fact; coupling them would make a runtime source choice silently alter unrelated execution policy.

### Introduce a separate config command

Rejected. `config local` is the existing boring ownership surface.

### Keep the limit permanently fixed at 1

Valid conservative alternative, but RFC-0105 already establishes that a finite positive HAC-owned generalization is coherent. Explicit local operator selection can remain truthful without claiming HAC knows runtime suitability.

## Trade-offs

A retained local value greater than `1` gives an operator deliberate control over HAC-level overlap but requires the operator to choose a policy value without HAC pretending to know runtime capacity.

A valid configuration can therefore be a poor operational choice for a given runtime or machine. This is accepted because the value is explicit local operator policy and not a performance guarantee.

Keeping the value independent from the selected runtime-composition source preserves clean ownership, but it also means an operator changing runtimes remains responsible for deciding whether their retained HAC policy is still a sensible choice.

## Relationship to existing RFCs

Accepted RFC-0094 owns retained `config local`, `config node`, and `config show` semantics and their separate local/runtime/topology boundaries.

Accepted RFC-0098 through RFC-0105 define execution availability, HAC authority, process-local interval scope and representation, permission-denial semantics, receiver refusal, and the finite positive HAC execution limit.

This RFC extends only RFC-0094's local retained ownership domain with one RFC-0105 policy fact. It does not modify caller-side remote topology ownership or remote protocol semantics.

## Impact

This RFC changes no product behavior by itself.

If accepted, it authorizes one bounded implementation which may:

- extend retained local state with the optional finite positive execution limit;
- add the narrow `config local` mutation needed to retain it;
- show that retained fact in `config show`;
- apply the retained value to ordinary local HAC composition while preserving absence as effective limit `1`;
- preserve the retained limit when an explicit `--runtime-config PATH` supplies only the runtime-composition domain; and
- add focused compatibility and validation tests.

It does not authorize a general configuration framework, remote declaration field, runtime-capacity claim, status/health/preflight observation, protocol advertisement, scheduler, queue, polling, balancing, or distributed state.

## Open questions

- Whether an invocation-time temporary execution-limit override is useful.
- Whether current active interval cardinality should ever have a separate operator observation surface.
- Whether future multi-process HAC needs coordination semantics.
- Whether evidence later justifies per-capability limits.

None of these questions blocks the bounded retained-local decision.

## Decision

Accepted. RFC-0106 adds one optional retained local HAC execution limit to Accepted RFC-0094's `config local` ownership domain, preserves effective limit `1` on absence, keeps the value independent from runtime-composition source selection, and authorizes only the bounded implementation described above.
