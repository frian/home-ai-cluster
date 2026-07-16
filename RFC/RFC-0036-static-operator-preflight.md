# RFC-0036: Static operator preflight

Status: Draft

Date: 2026-07-16

Author: frian

## Summary

Home AI Cluster should add one explicit local operator command:

```text
home-ai-cluster-preflight
```

The command should inspect the ordinary static local node and runtime-adapter
registries and emit one compact JSON report describing whether their declarations
are internally coherent.

The first contract should validate one rule only:

> Every adapter name declared by a node must resolve in the inspected runtime
> adapter registry.

The command must remain read-only and local-only. It must not call runtime
adapter `health()` or `chat()` methods, perform network access, detect processes,
activate distributed proof paths, mutate configuration, or manage lifecycle.

## Problem

Phase 8 aims to make the existing static local cluster understandable and
repeatable as an ordinary operator workflow.

The repository already owns ordinary static node and adapter registries. It also
has an operator health command, but that command deliberately performs direct
runtime observations by calling each declared adapter's `health()` method.

An operator therefore has no dedicated way to answer the smaller question:

> Are the repository-owned static node and adapter declarations internally
> coherent before any runtime observation or request execution occurs?

The repository can already detect one useful inconsistency without network or
runtime access: a node may declare an adapter name that does not exist in the
inspected adapter registry.

Without an explicit preflight contract, this fact remains mixed into the broader
health surface and ordinary operation still requires repository knowledge.

## Goals

This RFC should:

* define one explicit static operator preflight command;
* keep the first contract local-only and read-only;
* use the existing ordinary static node and adapter registry factories;
* validate one repository-supported coherence rule;
* emit one safe compact JSON report;
* distinguish coherent and incoherent reports through stable status and exit
  behavior;
* preserve the existing health command and ordinary application behavior;
* prove that no runtime adapter operation is called.

## Non-goals

This RFC does not define or add:

* runtime health probing;
* network probing;
* node or model discovery;
* process detection;
* process startup or shutdown;
* process supervision;
* remote process control;
* configuration mutation;
* a new configuration format;
* distributed-proof input;
* an HTTP endpoint;
* a daemon;
* a dashboard;
* a database;
* a generic validation or diagnostics framework;
* model availability validation;
* routability validation;
* request execution;
* retained preflight history;
* timestamps or identifiers.

## Proposal

Add one console entry point:

```text
home-ai-cluster-preflight
```

The command should construct the existing ordinary local registries through:

```text
create_static_local_node_registry()
create_static_runtime_adapter_registry()
```

It should inspect only the returned node and adapter declarations.

It must not call any runtime adapter method.

### Operating mode

The first contract should inspect only the ordinary local static registries.

The report should identify the operating mode as:

```text
local-only
```

The command should not accept flags or environment-driven inputs that activate
existing distributed proof paths.

Distributed-proof preflight may be investigated later if an existing explicit
construction seam can be reused without creating a new configuration contract.

### Static validation rule

The first contract should implement exactly one coherence rule:

```text
Every adapter name declared by a node must resolve in the inspected adapter
registry.
```

For each node declaration, the command should inspect its declared adapter names.
If `adapter_registry.adapter_named(name)` returns no adapter, the report should
contain one issue for that node and adapter name.

No adapter method should be called after resolution.

The command should not add speculative rules for empty names, duplicate values,
capability policy, node availability, node health, or unused registered adapters.
Existing models and registries already own their current construction behavior.
Additional validation rules require evidence and a later RFC or RFC amendment.

### Report shape

A successfully constructed report should contain exactly these top-level fields:

```json
{
  "status": "coherent",
  "operating_mode": "local-only",
  "nodes": [],
  "registered_adapters": [],
  "issues": []
}
```

The fields should appear in this order.

#### `status`

Allowed values:

```text
coherent
incoherent
```

Use `coherent` when no issue is found.

Use `incoherent` when one or more declared adapter names are missing from the
inspected adapter registry.

#### `operating_mode`

The first contract should always report:

```text
local-only
```

This value describes the selected registry construction path. It does not claim
that a runtime is available or that a request can execute.

#### `nodes`

`nodes` should preserve the registry order.

Each node projection should contain exactly:

```json
{
  "node_id": "local",
  "capabilities": ["chat"],
  "declared_adapters": ["ollama"]
}
```

The node projection should include no node display name, configured availability,
configured health reason, runtime URL, machine address, or private machine detail.

Capability and declared adapter order should preserve the node declaration order.

#### `registered_adapters`

`registered_adapters` should contain adapter names in registry order.

The command should read only each adapter's stable `name` property. It must not
call `health()`, `capabilities()`, `chat()`, or any other adapter operation.

#### `issues`

`issues` should preserve node order and declared adapter order.

Each issue should contain exactly:

```json
{
  "status": "missing-adapter",
  "node_id": "local",
  "adapter": "ollama",
  "reason": "declared adapter is not present in the inspected registry"
}
```

The first and only allowed issue status is:

```text
missing-adapter
```

The stable reason is:

```text
declared adapter is not present in the inspected registry
```

The report should not include raw exceptions, runtime URLs, authorization values,
filesystem paths, prompts, responses, model contents, or transport details.

### Output and exit behavior

For every successfully constructed report, the command should emit exactly one
compact JSON object followed by one newline on stdout.

It should write nothing to stderr for a coherent or incoherent report.

Exit status should be:

* zero for `coherent`;
* non-zero for `incoherent`.

An incoherent report is still a successfully constructed report. Its issues are
operator data, not a CLI parsing or construction exception.

If the command cannot construct the registries or report, it should:

* emit no JSON on stdout;
* write exactly this safe message to stderr:

```text
error: unable to construct static preflight report
```

* exit non-zero;
* not expose the original exception text.

### Relationship with health

`home-ai-cluster-preflight` and `home-ai-cluster-health` should remain separate
commands with separate meanings.

The preflight answers:

> Are the ordinary static declarations internally coherent under the first
> accepted validation rule?

The health command answers:

> What do the ordinary declarations say, and what did each declared adapter
> report during this invocation?

The preflight implementation should not call or reuse a health projection that
performs adapter observations.

The existing health command should remain unchanged.

### Privacy boundary

The preflight report may include only:

* node ids already owned by the static registry;
* declared capability names;
* declared adapter names;
* registered adapter names;
* the fixed operating mode;
* the fixed issue vocabulary defined by this RFC.

It must exclude:

* prompts and responses;
* generated content;
* runtime URLs;
* authorization values;
* model names or contents;
* filesystem paths;
* node display names;
* machine addresses;
* machine hardware details;
* raw exception details;
* timestamps and identifiers.

The command should not retain its output.

### Implementation boundary

The implementation should remain one small command module plus focused tests and
one proof document.

It may use small local projection helpers.

It should not introduce:

* a generic validator interface;
* a generic diagnostics model;
* a preflight/health superclass;
* a configuration loader abstraction;
* a plugin system;
* persistence;
* background execution.

## Rationale

A dedicated static preflight gives operators one truthful answer before they
start investigating runtime availability.

Using the existing ordinary static registry factories avoids a new configuration
system and preserves local-only default behavior.

Validating only declared adapter resolution is deliberately modest. It is already
supported by repository evidence and can prevent a real configuration mismatch
without inventing new policy.

A compact JSON report follows existing operator command conventions and remains
easy to test, inspect, and compose.

Keeping preflight separate from health protects an important semantic boundary:
configuration coherence is not runtime availability.

The proposal follows the project principles:

* local-first operation;
* privacy by default;
* engine independence;
* capability-centered projection;
* transparency over magic;
* boring solutions first;
* small steps;
* architecture before implementation.

## Alternatives considered

### Reuse `home-ai-cluster-health`

Rejected.

The health command deliberately calls adapter `health()` methods. Reusing it
would make the preflight a runtime probe and blur static declarations with direct
observations.

### Add a universal `start cluster` command

Rejected for this increment.

A start command would require decisions about process ownership, external
runtimes, remote processes, already-running detection, logs, shutdown,
supervision, and operating-system behavior.

### Validate many static invariants immediately

Rejected.

Rules for duplicate ids, empty names, capability policy, unused adapters, or node
health consistency may sound useful, but the current evidence does not justify a
broader validation policy.

### Add distributed-proof mode now

Deferred.

The first command should use the ordinary local registry construction path only.
Distributed proof paths remain explicitly opt-in and should not be silently
activated or converted into a new configuration interface.

### Add a generic diagnostics framework

Rejected.

One small command and one validation rule do not justify a reusable framework.

## Trade-offs

The first preflight will detect only one class of inconsistency.

It will not tell the operator whether Ollama, llama-server, a remote machine, or a
model is available. That limitation is intentional and should be visible.

The report duplicates a small amount of static projection logic also present in
the health command. This is preferable to sharing a projection that accidentally
performs runtime observations or introducing an abstraction before evidence.

The stable JSON shape creates a compatibility obligation. The shape is kept small
to make that obligation manageable.

## Impact

This RFC affects:

* one future CLI entry point;
* one small static projection and validation module;
* focused tests;
* one static proof document;
* Phase 8 operator documentation later.

It does not affect:

* `/v1/chat`;
* `/v1/chat/completions`;
* routing or fallback;
* runtime adapter interfaces;
* node models;
* ordinary application startup;
* `home-ai-cluster-health`;
* request history;
* distributed proof activation;
* configuration formats.

## Proof requirements

Implementation should not be considered complete until tests and a retained proof
demonstrate:

1. the ordinary coherent local registries produce `status: coherent` and exit
   zero;
2. an injected node declaring a missing adapter produces one `missing-adapter`
   issue, `status: incoherent`, and a non-zero exit;
3. adapter `health()`, `capabilities()`, and `chat()` methods are never called;
4. node and adapter ordering is deterministic and follows registry declarations;
5. output contains only the fields permitted by this RFC;
6. construction failure emits only the stable safe stderr message;
7. the existing health command and ordinary application behavior remain
   unchanged.

A live runtime proof is not required because the command must perform no runtime
observation.

## Open questions

The following remain deliberately deferred:

* whether a later preflight should support explicit distributed-proof registries;
* whether additional static validation rules become justified;
* whether a later canonical operator workflow should call preflight before
  health;
* whether preflight output should eventually support a human-readable mode;
* whether packaging should later expose the command differently.

These questions do not block the first contract.

## Decision

Pending.
