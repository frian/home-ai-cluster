# Phase 15 Static-Cluster Status Composition Investigation

## Purpose

Investigate the smallest truthful way for `home-ai-cluster-status` to inspect the
same explicitly selected supported local runtime composition as
`home-ai-cluster-static-cluster`.

This document records evidence and a recommendation. It does not authorize or
implement a code change.

## Current accepted boundaries

Phase 14 allows the ordinary static-cluster process to construct exactly one
explicitly selected local composition from the closed set:

```text
ollama
llama-server
```

Ollama remains the no-option default. Runtime identity remains outside static
cluster declarations, requests, routing, fallback, status output, and node
attribution.

RFC-0041 defines one explicit read-only static-cluster status operation. It
requires declaration validation before live observation, local inspection before
remote observation, sequential remote observation in declaration order, and a
normalized engine-independent result.

## Current status command construction

`home_ai_cluster.commands.status_command` currently:

1. accepts only `--declaration`;
2. loads and validates the static declaration;
3. constructs the historical ordinary local node registry through
   `create_static_local_node_registry()`;
4. constructs the historical ordinary local adapter registry through
   `create_static_runtime_adapter_registry()`;
5. constructs the declared remote registry;
6. creates one process-scoped HTTP client;
7. calls `collect_static_cluster_status(...)`;
8. emits one compact normalized JSON result.

The local construction is therefore still implicitly Ollama-backed.

## Current static-cluster construction

`home_ai_cluster.static_cluster` already uses the Phase 14 shared local runtime
composition boundary:

```text
add_local_runtime_arguments(...)
validate_local_runtime_arguments(...)
create_local_runtime_composition(...)
```

The parser accepts:

```text
--runtime ollama | llama-server
--llama-server-base-url
--llama-server-model
```

The no-option behavior remains Ollama.

The resulting `LocalAppComposition` contains the exact local node and adapter
registries passed into the existing static-cluster wiring boundaries.

## Shared composition suitability

`home_ai_cluster.local_runtime_composition` is already the narrow concrete
construction seam needed by status inspection.

It provides:

- one closed runtime choice;
- shared CLI argument definitions;
- shared conditional validation;
- direct Ollama construction;
- direct llama-server construction;
- one `LocalAppComposition` containing exact node and adapter registries.

Reusing this module would not require a generic factory, plugin registry,
dependency-injection container, persisted configuration, environment-variable
configuration, or runtime discovery.

No new shared abstraction is indicated by the evidence.

## Required operation order

The current status contract guarantees that an invalid declaration prevents all
live observation.

A Phase 15 implementation should preserve this order:

1. parse CLI arguments;
2. validate local runtime argument relationships without probing a runtime;
3. load and fully validate the declaration;
4. construct exactly one selected local composition;
5. construct the declared remote registry;
6. begin local and remote observation.

Both static declaration validation and local runtime value validation must finish
before observation.

Construction must perform no health probe. Direct runtime observation remains
owned by `collect_static_cluster_status(...)` through the selected local adapter
registry.

The implementation should keep declaration validation before local composition
construction where practical, preserving the existing guarantee that an invalid
declaration prevents even local construction. Local runtime CLI validation may
occur during argument processing because it is static and network-free.

## CLI compatibility

The smallest compatible extension is to add the same shared runtime arguments to
`home-ai-cluster-status`:

```text
--runtime ollama | llama-server
--llama-server-base-url
--llama-server-model
```

Existing invocations remain valid:

```sh
uv run home-ai-cluster-status --declaration <DECLARATION_PATH>
```

They continue to inspect the default Ollama composition.

The declaration remains topology-only. Runtime selection remains an explicit
operator command concern and is not loaded from the TOML file.

## Status contract impact

No status model change is needed.

The selected local adapter is observed through the existing normalized local
runtime vocabulary:

```text
available
unavailable
observation-failed
```

The output must continue to omit:

- runtime identity;
- adapter identity;
- model identity;
- runtime base URLs;
- declaration endpoint values;
- raw runtime or transport errors.

Remote observation remains unchanged and continues through the normalized Home AI
Cluster internal status endpoint.

## Test implications

Focused tests should demonstrate:

1. existing no-runtime-option status invocations remain Ollama-backed;
2. the shared runtime argument set is accepted by the status parser;
3. llama-server requires both its base URL and model;
4. llama-server-only arguments fail under the Ollama selection;
5. invalid runtime values fail before observation;
6. invalid declarations prevent local and remote observation;
7. the selected `LocalAppComposition` registries are passed unchanged to
   `collect_static_cluster_status(...)`;
8. local status remains normalized and contains no runtime identity;
9. remote declaration order and remote observation behavior remain unchanged;
10. unexpected construction or collection failures retain the existing safe
    operator error.

Ordinary automated tests should require no live runtime.

## Minimum real proof

One privacy-safe proof should use:

- one explicit static declaration with documentation-safe retained values;
- `home-ai-cluster-status --runtime llama-server`;
- one explicitly operator-started local llama-server process;
- one declared remote ordinary Home AI Cluster process using Ollama;
- a result showing the local normalized status and the remote normalized status;
- no retained prompt, generated response, private address, real model path,
  runtime URL, machine name, or raw error.

The proof should demonstrate only equivalent-node behavior if both application
processes run on one trusted host. It must not claim physical two-machine
separation unless two machines are actually used.

## Architectural assessment

An RFC is required before implementation.

The implementation mechanics are small and can reuse accepted Phase 14 seams, but
the operator contract changes in an area explicitly owned by RFC-0041:

- the local observation target changes from one fixed historical composition to
  one explicitly selected supported composition;
- the status CLI gains runtime-selection inputs;
- validation and construction ordering across declaration and composition must be
  specified;
- compatibility and privacy guarantees must be made explicit.

These are not merely internal refactoring details. They define what the status
operation observes and how the operator selects that observation target.

The RFC can remain narrow. It should not redesign status, local composition, or
runtime adapters.

## Recommended RFC scope

A Phase 15 RFC should decide only:

- the shared runtime CLI arguments on `home-ai-cluster-status`;
- Ollama as the preserved default;
- static validation before observation;
- construction of exactly one selected local composition;
- reuse of its exact node and adapter registries for local status observation;
- unchanged remote observation;
- unchanged normalized engine-independent output;
- unchanged declaration, routing, fallback, lifecycle, and privacy boundaries.

It should explicitly reject:

- runtime fields in declarations;
- runtime identity in status output;
- multiple local adapters;
- runtime discovery or automatic selection;
- model inventory;
- health-aware routing;
- scheduling or supervision;
- lifecycle management;
- persistent configuration;
- environment-variable configuration;
- generic factories, plugins, or dependency-injection containers;
- databases, dashboards, Docker, or Kubernetes.

## Recommended delivery sequence

1. merge this investigation record;
2. draft and accept one narrow RFC;
3. add the shared runtime arguments and selected composition construction to the
   status command in one small implementation PR;
4. record one privacy-safe real proof;
5. close Phase 15 in documentation.

## Conclusion

Phase 15 is a small but architectural operator-contract extension.

The existing `local_runtime_composition` module is sufficient. The status command
can reuse it without adding a new abstraction, while preserving normalized
engine-independent output and topology-only declarations.

Implementation should wait for one narrow accepted RFC.
