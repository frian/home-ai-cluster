# Phase 13 Explicit Local Runtime Composition Investigation

Status: Complete

## Purpose

Investigate the smallest architecture that could let an operator start an
ordinary Home AI Cluster node with one explicitly chosen supported local runtime
composition. This document records current implementation facts and options; it
does not accept an architecture or authorize implementation.

## Phase 13 boundary

Local runtime composition is an operator-owned process-startup concern.
Cluster-facing requests remain capability-centered: routing must not inspect
runtime, adapter, or model identity; remote declarations must not gain
runtime-specific fields; and result attribution remains node-based. Status
remains normalized and engine-independent. Runtime-specific base URLs, model
identifiers, payload translation, and runtime health stay local to the executing
node and its adapter.

## Current ordinary composition

The ordinary local composition is fixed in
`src/home_ai_cluster/api/wiring.py`:

* `create_static_local_node_announcement()` constructs the `local` node with
  `chat`, declared availability and health, and `adapters=["ollama"]`.
* `create_static_local_node_registry()` wraps that announcement in a fresh
  `NodeRegistry`.
* `create_static_runtime_adapter_registry()` constructs a fresh
  `AdapterRegistry([OllamaAdapter()])`. `OllamaAdapter` defaults to
  `http://localhost:11434` and `llama3.2` in
  `src/home_ai_cluster/adapters/ollama.py`.

`src/home_ai_cluster/api/routes.py:handle_static_local_cluster_request()` calls
those factories whenever no proof-receiving wiring is present. The same defaults
serve ordinary `/v1/chat`, `/internal/cluster/request`, and
`/internal/cluster/status`.

`src/home_ai_cluster/main.py:create_app(...)` accepts remote-wiring and lifespan
inputs but no ordinary local node or adapter-composition input. Its module-level
`app = create_app()` retains zero-argument Ollama-backed startup. The dedicated
OpenAI-compatibility process also calls `create_app()`.

`src/home_ai_cluster/static_cluster.py` builds ordinary static remote wiring but
passes the same two local factories to `build_static_remote_wiring()` and
`build_static_remote_collection_wiring()`. Its declaration and inline CLI
arguments describe remote topology only; they do not select the local runtime.

The local health and preflight commands likewise default to these factories in
`src/home_ai_cluster/local_health_snapshot.py` and
`src/home_ai_cluster/commands/static_preflight.py`; their optional registry inputs are
testable projection seams, not ordinary process-startup configuration. The
`[project.scripts]` table in `pyproject.toml` exposes a separate
`home-ai-cluster-phase-12-heterogeneous-receiver` proof command alongside the
ordinary static-cluster and operator commands.

## Existing reusable seams

The `RuntimeAdapter` protocol in `src/home_ai_cluster/adapters/base.py` already
covers adapter identity, health, capabilities, and normalized chat execution.
Both `OllamaAdapter` and `LlamaServerAdapter` implement it. `AdapterRegistry`
and `NodeRegistry` in `src/home_ai_cluster/core/registry.py` accept
already-created objects and do not discover or construct runtimes.

The Phase 12 seam proves that request and status handlers can use built
registries without changing cluster-facing contracts. It is evidence for
reusing registry construction and handlers, not for dynamic registration, a
generic factory, or plugins.

`tests/test_api_wiring.py` requires the ordinary node declaration to contain
`ollama` and the ordinary adapter registry to contain one `OllamaAdapter`.
`tests/test_app.py` requires `create_app()` to leave proof-receiving wiring
disabled and `/v1/chat` to remain local-only without explicit remote wiring.
`tests/test_static_cluster_cli.py` verifies that static-cluster CLI input is
limited to remote topology.

## Phase 12 proof-only composition

`create_proof_receiving_app(...)` in `src/home_ai_cluster/main.py` is the only
application-construction path that accepts built `NodeRegistry` and
`AdapterRegistry` values. It stores `ProofReceivingAppWiring` on app state.
Only internal request and status handlers consume it; ordinary `/v1/chat` still
uses its normal local or explicit remote-wiring path.

`src/home_ai_cluster/phase_12_heterogeneous_runtime_cluster_proof.py` is a
proof-scoped launcher. `create_phase_12_receiver_app(...)` builds one
`LlamaServerAdapter(base_url=..., model=...)`, matching single-node and adapter
registries, then calls `create_proof_receiving_app(...)`. Its CLI requires a
loopback llama-server URL and model and has proof-specific receiver identity and
binding defaults. `tests/test_phase_12_heterogeneous_runtime_cluster_proof.py`
verifies those facts and that ordinary `create_app()` remains unchanged.

This seam and launcher must not silently become ordinary contracts. Proof naming,
binding, receiver identity, and argument semantics need not be suitable for
ordinary operation. Phase 12 did not decide configuration location, command
compatibility, validation, or lifecycle ownership for ordinary composition.

## Compatibility constraints

Current zero-configuration startup is a compatibility surface: ordinary
construction creates one local `ollama` declaration and one default
`OllamaAdapter`; ordinary static-cluster callers retain that same composition.
Any Phase 13 proposal must state how these paths remain compatible when no new
local-composition input is supplied.

`LlamaServerAdapter` already owns its configured base URL and required model,
runtime-private HTTP translation, and normalized health and request failures.
Its constructor and the proof's `local_http_url()` validation are evidence, but
do not decide the ordinary validation contract.

## Questions

The RFC must investigate rather than assume:

1. the smallest ordinary composition seam: built registries, a small
   local-composition value, or another explicit input;
2. configuration ownership and location, including whether retained state is
   needed or explicit CLI arguments remain the boring first solution;
3. zero-configuration Ollama compatibility;
4. validation and safe failure behavior for adapter-specific base URLs and
   model identifiers;
5. whether the first ordinary process has exactly one configured local adapter;
6. the Phase 12 proof-code disposition; and
7. the smallest retained real operator proof.

## Options

### Option A — Explicit adapter-specific CLI startup

A dedicated or extended ordinary command accepts explicit runtime-specific
arguments, constructs one supported adapter and matching local registries, and
passes that composition into ordinary application construction. No input could
retain the current Ollama path.

### Option B — Small retained local runtime configuration file

An explicitly selected local-only file describes one supported composition.
Startup loads it once and constructs one adapter and matching registries. This
adds location, schema, ownership, precedence, validation, compatibility, and
privacy decisions.

### Option C — Generic adapter factory or plugin mechanism

A generic factory or plugin layer would load adapters from generic
configuration. Two concrete adapters and explicit proof wiring do not show that
this abstraction is unavoidable; it would add loading, registration, validation,
compatibility, and lifecycle questions beyond Phase 13.

## Comparison

| Option | Simplicity and operator clarity | Compatibility and privacy | Validation and testability | Architectural impact and RFC scope |
| --- | --- | --- | --- | --- |
| A — explicit CLI | Small and visible; no retained state. | Can preserve no-input Ollama behavior; command visibility and shell history need review. | Closed argument combinations and adapter construction are directly testable. | Low abstraction risk; an RFC must own command shape, defaults, values, failures, and proof. |
| B — retained file | Better repeated operation but adds an operator artifact. | May reduce repeated typing, but permissions, location, endpoint exposure, retention, and precedence need a privacy design. | Requires parser, closed schema, invalid-file behavior, and compatibility tests. | Medium abstraction risk: a configuration-format contract broader than present evidence requires. |
| C — factory/plugins | Flexible in theory but obscures supported construction paths. | Dynamic loading expands trust and privacy review without helping the first ordinary path. | Requires discovery, loading, failure, and compatibility matrices. | High premature-abstraction risk with a substantially broader RFC. |

Option A is the likely smallest direction for an RFC to evaluate: it keeps
operator intent at startup and reuses explicit adapter construction. It is not
an accepted decision; the RFC must compare it with a retained-file alternative
and may reject it if compatibility or operator evidence warrants.

## Recommended RFC scope

An RFC is required before implementation because this affects ordinary
application construction, configuration, startup compatibility, adapter
construction and validation, privacy, and failure behavior. It should own:

* the ordinary composition seam and its relationship to `create_app(...)`;
* the supported first runtime set and whether one process has exactly one local
  configured adapter;
* configuration ownership, location, selection, and precedence;
* default Ollama compatibility and startup-command relationship;
* validation and safe failure behavior for runtime-specific values;
* the boundary between ordinary composition and retained Phase 12 proof code;
  and
* tests and a retained real operator proof.

The RFC must preserve the existing engine-independent request, routing,
declaration, attribution, and status boundaries.

## Deferred work

This investigation does not propose request-level runtime, adapter, model, or
node selectors; automatic runtime selection; multiple-runtime scheduling within
one node; engine-aware routing or fallback; runtime identity in remote
declarations; model discovery or inventory; model downloading; runtime
installation; supervision, restart, repair, or lifecycle ownership; dynamic
loading or plugins; a generic adapter factory; environment-variable-only hidden
configuration; database-backed configuration; dashboard work; Docker or
Kubernetes; OpenAI-compatible API changes; or distributed configuration
propagation.

The final command name and arguments, file need, composition-value shape,
supported runtime list, validation messages, and Phase 12 proof-code disposition
remain deferred to the RFC.

## Required proof

After RFC acceptance, the smallest proof should retain evidence that one
operator can start an ordinary node with one explicitly chosen supported local
runtime composition, observe existing normalized status, and complete one
ordinary capability-centered request. It must also prove zero-configuration
Ollama startup remains compatible.

The proof must use privacy-safe evidence, contain no runtime, adapter, model, or
node selector in requests or remote declarations, preserve node attribution, and
not rely on the Phase 12 proof-specific launcher to establish ordinary operation.

## Conclusion

The repository has concrete adapters, explicit registries, and a narrow
proof-scoped receiving-app seam, but no ordinary local runtime-composition
contract. The next step is an RFC evaluating the smallest explicit,
operator-owned startup option—likely adapter-specific CLI input—while preserving
zero-configuration Ollama behavior and every cluster-facing
engine-independent boundary.

No architecture is accepted by this investigation. No code change is authorized
until that RFC is reviewed and accepted.
