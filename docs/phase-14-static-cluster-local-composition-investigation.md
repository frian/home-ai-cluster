# Phase 14 Static-Cluster Local Composition Investigation

Status: Complete

## Purpose

Investigate the smallest architecture that could let an operator start the
ordinary explicit static cluster with one explicitly chosen supported local
runtime composition. This document records current implementation facts,
compatibility constraints, options, and the likely RFC boundary. It does not
accept an architecture or authorize implementation.

## Phase 14 boundary

Phase 14 concerns only the local candidate constructed by the ordinary
`home-ai-cluster-static-cluster` process. Remote declarations remain
operator-owned topology facts. Requests remain capability-centered, routing
remains local-first, fallback retains its accepted pre-request boundary, and
result attribution remains node-based.

Runtime choice, adapter identity, local runtime URL, and model identity must not
enter remote declarations, requests, routing candidates, fallback policy,
normalized status, or declared-remote attribution.

## Current static-cluster startup

`src/home_ai_cluster/static_cluster.py` exposes two topology input modes:

- `--declaration <path>` for one retained static declaration; or
- the paired inline arguments `--remote-node-id` and `--remote-base-url`.

The parser requires exactly one complete topology mode. Declaration loading and
validation complete before `uvicorn.run(...)`.

Both application constructors currently create the local candidate directly
through the fixed ordinary factories:

- `create_static_local_node_registry()`; and
- `create_static_runtime_adapter_registry()`.

Those factories produce the existing Ollama-backed local composition. The
single-remote and ordered-remote constructors then pass those registries into
the existing static remote wiring builders. The static-cluster command has no
local-composition input and no seam through which a caller can provide one.

The command binds the caller endpoint to the existing fixed loopback host and
port. Its remote HTTP client, lifespan, topology parsing, candidate selection,
and remote wiring are independent from local adapter construction.

## Existing Phase 13 composition

`src/home_ai_cluster/local_runtime.py` owns the explicit ordinary standalone
startup contract introduced by Phase 13:

- closed runtime choices `ollama` and `llama-server`;
- default runtime `ollama`;
- required loopback HTTP base URL and non-empty model for `llama-server`;
- rejection of llama-server arguments with the Ollama choice;
- validation before server startup and without a network probe; and
- construction of one `LocalAppComposition` containing one matching
  `NodeRegistry` and one `AdapterRegistry`.

The module currently combines three concerns:

1. parsing and validation of explicit local-runtime CLI arguments;
2. constructing the supported local compositions; and
3. starting the standalone ordinary application.

The composition constructors are concrete and reusable, but the parser is tied
to the `home-ai-cluster-local` program and its complete argument set, including
standalone host and port.

## Existing reusable seams

The static remote wiring builders already accept constructed `NodeRegistry` and
`AdapterRegistry` values. They do not require the fixed Ollama factories.
Therefore Phase 14 does not require a routing, fallback, request, result,
status, declaration, or transport change.

`LocalAppComposition` is the accepted Phase 13 value for carrying the two local
registries together. A static-cluster application constructor could consume its
registries when building existing single-remote or ordered-remote wiring.

The existing remote HTTP client and lifespan can remain process-owned by the
static-cluster command. Local runtime composition does not need to own or alter
that client.

## Compatibility constraints

The current static-cluster command is an ordinary operator contract. With no new
local-runtime input it must continue to:

- accept the existing declaration and inline topology modes;
- construct the current default Ollama local candidate;
- bind the caller endpoint to the existing loopback address and port;
- preserve declaration validation before startup;
- preserve remote declaration order;
- preserve local-first capability routing and narrow fallback; and
- return the existing normalized results, errors, status, and attribution.

Remote declaration files must remain topology-only. Adding local runtime,
adapter, model, or local base-URL fields to the declaration would mix local
process construction with remote topology and would contradict the Phase 14
roadmap boundary.

The existing `home-ai-cluster-local` command must remain compatible. Phase 14
must not silently change its argument behavior while trying to share parsing or
construction code.

## Questions requiring an RFC

The implementation is mechanically small, but ordinary CLI and construction
contracts require explicit decisions:

1. whether `home-ai-cluster-static-cluster` is extended or a second combined
   command is added;
2. the exact local-runtime flags, defaults, validation, and error messages;
3. whether Phase 14 reuses one shared local-runtime argument helper or duplicates
   the closed argument set;
4. where supported composition construction lives after reuse;
5. whether static-cluster application constructors accept one
   `LocalAppComposition` or two loose registries;
6. how no-input Ollama compatibility is represented and tested;
7. whether existing fixed caller host and port remain unchanged; and
8. the smallest retained real operator proof.

These decisions affect an ordinary startup command and shared application
construction. They should be owned by an accepted RFC before implementation.

## Options

### Option A — Extend the existing static-cluster command

Add the same closed local-runtime choice and llama-server-specific values to
`home-ai-cluster-static-cluster`. Keep topology input unchanged. Construct one
local composition before creating the existing static remote wiring.

This produces one canonical ordinary static-cluster command and directly closes
the Phase 14 asymmetry. It requires careful parser composition so topology and
local-runtime validation remain explicit and understandable.

### Option B — Add a separate combined command

Keep `home-ai-cluster-static-cluster` unchanged and add another ordinary command
that accepts both static topology and explicit local-runtime composition.

This offers strong compatibility isolation but creates two ordinary commands
for nearly the same static-cluster behavior. It risks permanent duplication of
topology parsing, validation, remote client ownership, and application
construction.

### Option C — Put local composition in the static declaration

Extend the TOML declaration with local runtime, base URL, or model fields.

This is not recommended. The declaration currently represents remote topology.
Adding process-local runtime facts would broaden its schema, privacy boundary,
ownership, validation, migration, and precedence contracts. Phase 13 explicitly
chose CLI-first local composition and did not establish evidence for retained
runtime configuration.

### Option D — Introduce a generic adapter factory or plugin layer

Build static-cluster composition from generic runtime configuration.

This is not supported by current evidence. The project has two explicit
supported adapters and an accepted small composition value. A generic factory,
provider registry, plugin mechanism, or service container would be premature.

## Comparison

| Option | Simplicity | Compatibility | Duplication risk | Architectural impact |
| --- | --- | --- | --- | --- |
| A — extend existing command | One ordinary path; smallest operator model. | Requires preserving all old invocations and defaults. | Low if local parsing and construction are shared narrowly. | Small but changes an ordinary CLI contract; RFC required. |
| B — separate combined command | Isolates the old command. | Existing command remains byte-for-byte compatible. | High: likely duplicates topology and process construction. | Adds another ordinary operating surface. |
| C — declaration fields | Repeatable retained input. | Broadens the declaration beyond topology. | Medium, plus schema migration and precedence. | Large new configuration and privacy contract. |
| D — generic factory/plugins | Flexible in theory. | Obscures the closed supported set. | Replaces small duplication with premature abstraction. | Unjustified and outside Phase 14. |

Option A is the likely smallest direction for an RFC to evaluate. The strongest
implementation evidence is that static remote wiring already accepts constructed
registries, while Phase 13 already defines the supported local compositions.
The unresolved work is command composition and ownership, not core orchestration.

## Likely minimal implementation shape

Subject to RFC acceptance, the smallest implementation would likely:

- preserve the existing `home-ai-cluster-static-cluster` command;
- add a closed local runtime choice defaulting to Ollama;
- reuse the accepted llama-server local URL and model validation;
- construct exactly one `LocalAppComposition` before server startup;
- pass its registries into both existing static-cluster application constructors;
- keep remote declarations and topology parsing unchanged; and
- keep all routing, fallback, transport, request, result, status, and attribution
  code unchanged.

A narrow shared helper for local-runtime arguments and composition construction
may be justified. It must remain explicit and concrete for the two supported
runtimes. It must not become a generic adapter factory, plugin mechanism, or
dependency-injection framework.

## Required compatibility and proof evidence

An RFC should require focused tests demonstrating:

- every existing static-cluster invocation remains Ollama-backed and compatible;
- explicit Ollama composition produces the same local candidate behavior;
- explicit llama-server composition constructs exactly one matching local node
  and adapter;
- invalid local-runtime combinations fail before endpoint binding;
- declaration and inline topology validation remain unchanged;
- declaration order and fallback behavior remain unchanged;
- requests and declarations contain no runtime, adapter, model, or node selector;
- normalized status remains engine-independent; and
- runtime-specific values do not leak through public failures.

The retained real proof should use the ordinary static-cluster command with an
explicit local composition and at least one statically declared remote. It
should demonstrate local-first behavior and one bounded remote fallback without
requiring a new topology size, runtime discovery, or lifecycle management.

## Deferred work

This investigation does not propose:

- runtime, adapter, model, or node selectors in requests;
- runtime identity in remote declarations;
- more than one local adapter per process;
- automatic runtime selection or local adapter fallback;
- engine-aware routing or fallback;
- model discovery, inventory, downloading, or installation;
- runtime supervision, restart, repair, or remote process control;
- retained local runtime configuration;
- environment-variable-only hidden selection;
- generic factories, plugins, dynamic loading, or service containers;
- database-backed configuration or distributed configuration;
- dashboard work, Docker, Kubernetes, or OpenAI-compatible API changes.

## Conclusion

Phase 14 is supported by a real, narrow implementation gap. The ordinary static
cluster hard-codes the default Ollama registries even though Phase 13 now has an
accepted explicit local composition value and concrete constructors for both
supported runtimes.

No core orchestration change appears necessary. The next step should be an RFC
deciding the ordinary CLI relationship, the narrow reuse boundary for local
runtime parsing and construction, compatibility behavior, and proof obligations.
No implementation is authorized by this investigation.
