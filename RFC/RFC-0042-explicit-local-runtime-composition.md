# RFC-0042: Explicit Local Runtime Composition

Status: Accepted

Date: 2026-07-17

Author: frian

## Summary

Home AI Cluster should add one explicit ordinary local runtime-composition path.
At process startup, an operator may choose exactly one supported local runtime:
`ollama` or `llama-server`. The process constructs one matching local node
announcement, `NodeRegistry`, and `AdapterRegistry`, then supplies those
already-built registries to ordinary application composition.

The first explicit path should be CLI-first. It should use a closed runtime
choice, require llama-server's local base URL and model identifier, and perform
only local validation before the server starts. It should not add a retained
configuration file, environment-variable-only configuration, generic factories,
plugins, runtime discovery, or runtime lifecycle ownership.

No explicit composition input preserves current zero-argument, Ollama-backed
ordinary behavior. Runtime identity and values remain local to the executing
process; they do not enter cluster requests, routing, remote declarations,
attribution, or normalized status.

## Problem

The current ordinary composition is intentionally fixed. In
`src/home_ai_cluster/api/wiring.py`,
`create_static_local_node_announcement()` declares local `chat` support and
`adapters=["ollama"]`; `create_static_runtime_adapter_registry()` creates one
default `OllamaAdapter`. `create_app(...)` in
`src/home_ai_cluster/main.py` has no ordinary local-composition input.

The existing `LlamaServerAdapter` proves that the cluster-owned adapter
boundary supports another runtime. Phase 12 proved a real heterogeneous
two-machine request, but its receiver is a deliberately proof-scoped launcher
that builds registries and calls `create_proof_receiving_app(...)`. It is not
an ordinary operator startup contract.

Without an ordinary composition decision, a user cannot start an ordinary node
with the already-supported llama-server adapter. Making that possible by
changing a request, remote declaration, routing rule, or proof-only launcher
would violate accepted capability, static-declaration, attribution, status, and
runtime-adapter boundaries.

## Goals

This RFC should:

* define one operator-owned ordinary local-composition boundary;
* support exactly one configured local runtime adapter per ordinary process in
  Phase 13;
* support the closed initial runtime choices `ollama` and `llama-server`;
* use explicit CLI startup rather than a retained configuration file;
* preserve the existing zero-argument Ollama composition;
* allow ordinary request and normalized status paths to consume supplied local
  registries without changing their cluster-facing contracts;
* keep runtime-specific values local to adapter construction;
* define small, deterministic startup validation and failure behavior; and
* require focused compatibility tests and a privacy-safe real operator proof.

## Non-goals

This RFC does not add:

* request-level runtime, adapter, model, or node selectors;
* runtime identity, adapter identity, model identity, or local-composition fields
  in remote declarations;
* automatic runtime choice, discovery, or model inventory;
* multiple local adapters per process, runtime scheduling, priorities, or local
  adapter fallback;
* engine-aware routing or fallback;
* model downloading, runtime installation, supervision, restart, repair, or
  lifecycle management;
* retained local runtime configuration files in Phase 13;
* environment-variable-only hidden configuration;
* generic adapter factories, service containers, provider registries, plugins,
  dynamic loading, or framework-level dependency injection;
* database-backed configuration, distributed configuration propagation,
  dashboard work, Docker, or Kubernetes; or
* OpenAI-compatible API changes.

## Proposal

### One local composition value

Ordinary application construction may receive one already-built local composition
containing exactly:

* one `NodeRegistry`; and
* one `AdapterRegistry`.

The exact type and symbol name remain an implementation naming decision, but it
must be one small explicit value rather than unrelated loose registry arguments.
It must validate that both registries are present. It is process-local,
operator-owned application construction input, not a general dependency
injection facility.

When present, ordinary local request handling and the existing normalized local
status handling use this composition's registries. When absent, they continue to
use `create_static_local_node_registry()` and
`create_static_runtime_adapter_registry()`. The latter path retains current
Ollama behavior.

This proposal extends ordinary application composition. It does not promote
`create_proof_receiving_app(...)`, `ProofReceivingAppWiring`, or its
proof-specific app-state key into the ordinary contract. The proof seam remains
available as evidence until an ordinary path has been implemented and proven.

### One supported local adapter per process

For Phase 13, an ordinary process has exactly one supported local runtime
adapter and one matching local node announcement. The announcement retains the
existing local node identity, `chat` capability, static availability and health
shape, and declares the chosen adapter's existing stable name.

A process does not compose both adapters, choose among adapters later, or expose
an adapter selection policy. This is explicit local startup composition, not
cluster runtime selection.

### Explicit adapter-specific ordinary startup

One ordinary operator startup path should accept a closed runtime choice at
process startup. Its exact command name and flag spelling are open, but the
semantic contract is:

```text
runtime choice: ollama | llama-server
```

With an explicit `ollama` choice, the process constructs the ordinary Ollama
composition. With an explicit `llama-server` choice, it constructs the ordinary
llama-server composition. The runtime choice is consumed only while the local
process is built; it is never converted into a request constraint, route,
candidate attribute, remote declaration field, attribution value, or status
field.

The normal ordinary runtime-specific path must construct an application through
the ordinary composition seam. It must not execute through the Phase 12
proof-specific receiver launcher.

### CLI-first configuration

The Phase 13 startup contract uses explicit CLI arguments. A retained runtime
configuration file is not added. This keeps the first composition choice visible
at process startup and avoids a file format, search location, precedence,
retention, migration, reload, and permissions contract before evidence requires
one.

Environment variables may not be an implicit alternative input. They must not
silently select a runtime or supply configuration values under this RFC.

### Adapter-specific values

For `ollama`, no new Phase 13 runtime-specific override is required. The
existing `OllamaAdapter` defaults remain the initial ordinary behavior. Whether
explicit Ollama base-URL or model overrides later provide sufficient operator
value remains open.

For `llama-server`, startup requires both:

* a local llama-server base URL; and
* a model identifier.

The base URL is held only by the local `LlamaServerAdapter`. It must satisfy
the established local HTTP boundary used by the Phase 5 and Phase 12 proofs:
an absolute `http` URL whose host is loopback. The model identifier must be
non-empty. Neither value appears in a request, declaration, route, normalized
status response, attribution, default logs, retained request history, or
privacy-safe proof record.

### Validation and failure behavior

Parsing and local composition validation happen before server startup. They do
not perform health probes, network reachability checks, runtime discovery, model
inventory, or model generation.

Validation must reject:

* a runtime choice outside the closed supported set;
* a missing llama-server base URL or model identifier when llama-server is
  selected;
* llama-server-specific arguments when another runtime is selected;
* empty required values; and
* a llama-server URL outside the defined local HTTP boundary.

Invalid startup input must produce a compact operator-facing failure and a
non-zero exit before endpoint binding. It must not reveal secrets, private
addresses beyond operator-supplied local input, raw transport exceptions, or
runtime responses. Runtime availability remains an adapter health and request
execution concern under accepted boundaries, not a configuration-parsing probe.

## Compatibility

No explicit local-composition input preserves existing zero-configuration
Ollama-backed behavior for:

* `create_app()` and the module-level `app = create_app()` in
  `src/home_ai_cluster/main.py`;
* the ordinary local request and internal request/status paths that currently
  fall back to the static local registry factories;
* the dedicated OpenAI-compatibility application, which calls `create_app()`;
* ordinary static-cluster construction in
  `src/home_ai_cluster/static_cluster.py`, which continues to use the default
  local Ollama composition unless a later accepted implementation explicitly
  supplies the new composition; and
* the existing local health, preflight, and status commands, which retain their
  current default factory behavior unless a later accepted implementation
  deliberately reuses the ordinary composition seam.

Existing remote declarations remain topology-only. They continue to contain only
accepted remote identity and transport facts, never local runtime configuration.

The Phase 12 receiver command remains proof evidence during implementation.
Removing, reducing, or retaining it after a successful ordinary proof is a
separate implementation and closeout decision; its deletion is not a
prerequisite for the first Phase 13 implementation.

## Privacy and trust boundary

The explicit composition is local to the executing process. The operator chooses
the local runtime and supplies its values; Home AI Cluster does not discover
runtimes, models, endpoints, or configuration files.

A request remains a capability-centered `ClusterRequest`. Routing continues to
reason about capabilities, accepted availability, and existing failure
boundaries—not runtime, adapter, or model identity. Remote callers never learn
the receiving runtime from a request, a static declaration, a normalized status
response, or routing behavior.

The system must not log prompts or responses by default. It must not expose
base URLs, model identifiers, raw errors, credentials, or other private process
facts in cluster-facing outputs. The operator remains responsible for starting,
stopping, and securing the local runtime.

## Alternatives considered

### Retain Ollama hard-coded and keep llama-server proof-only

Rejected. It leaves the Phase 13 roadmap outcome unsatisfied and preserves the
proof-only launcher as the only way to run an already-supported adapter in a
receiving application.

### Promote the Phase 12 proof receiver directly

Rejected. Its command, receiver identity, binding, argument names, and proof
scope were intentionally narrow. Promoting it would make proof details the
ordinary operating contract without deciding ordinary compatibility or startup
semantics.

### Retained local runtime configuration file

Rejected for Phase 13. A file may be useful later, but it requires new decisions
about schema, explicit selection or search paths, location, permissions,
precedence, retention, migration, and reload behavior. One explicit startup
choice does not yet justify that contract.

### Generic adapter factory or plugin mechanism

Rejected. The project has two concrete adapters and explicit construction
evidence, not evidence for dynamic loading, generic registration, or a plugin
lifecycle. Such a mechanism would hide supported choices and add premature
abstraction.

### Explicit adapter-specific CLI startup

Selected as the smallest adequate approach. It is visible, process-local, uses
a closed supported set, preserves the default, and has a small validation
surface. It can be reconsidered only through a later RFC if actual operation
shows that a retained configuration format is needed.

## Trade-offs

CLI values can be visible in shell history and process inspection. That is an
operator-facing trade-off, but it is smaller than a retained configuration
contract for the first proof. Operators should avoid putting credentials in
these values; credentials are not supported by this RFC.

One adapter per process deliberately gives up intra-process runtime fallback,
parallelism, and scheduling. That limitation preserves a simple ownership and
failure model.

The ordinary composition seam adds a small application-construction value.
This is acceptable because it reuses existing registries, makes local runtime
ownership explicit, and avoids a general container or factory system.

The initial llama-server boundary is loopback HTTP. It does not solve every
local deployment arrangement, but matches current proof evidence and avoids
broadening trust, authentication, or network-scope decisions.

## Impact

After acceptance, implementation may affect:

* ordinary application construction and its focused tests;
* local registry construction and construction-specific tests;
* one ordinary startup command and its argument validation;
* ordinary local request and normalized internal status composition;
* documentation and one retained privacy-safe operator proof; and
* reuse of the same explicit local composition in a static-cluster receiving
  application.

It must not change:

* `ClusterRequest`, capability semantics, routing candidate selection, routing
  policy, fallback policy, or remote declaration schema;
* cluster-owned node attribution or normalized result and status shapes;
* default prompt/response logging behavior;
* remote process or runtime lifecycle ownership; or
* the OpenAI-compatible request contract.

## Implementation sequence

After this RFC is accepted, implementation should proceed through small,
separately reviewable pull requests:

1. introduce the narrow ordinary local-composition seam with compatibility
   tests;
2. make ordinary local request and normalized status paths consume it;
3. add explicit ordinary llama-server startup composition and validation;
4. prove zero-configuration Ollama startup remains unchanged;
5. exercise the ordinary static-cluster receiving path through the new
   composition;
6. retain a real privacy-safe operator proof; and
7. decide the Phase 12 proof-launcher disposition during closeout.

This sequence does not authorize implementation until the RFC is accepted.

## Proof obligations

Phase 13 is not complete until retained privacy-safe evidence demonstrates:

1. zero-configuration ordinary Ollama startup remains compatible;
2. one ordinary node starts with explicit llama-server composition;
3. that ordinary node exposes the existing normalized runtime status;
4. one ordinary capability-centered request succeeds through that node;
5. a statically declared caller routes to it without runtime-specific
   declaration fields;
6. the normalized result is attributed to the declared node;
7. requests contain no runtime, adapter, model, or node selector;
8. invalid runtime and argument combinations fail before server startup;
9. no runtime-specific routing, fallback, discovery, lifecycle, or logging
   behavior was introduced; and
10. the Phase 12 proof-specific launcher was not the ordinary execution path.

The retained record must not expose private addresses, hostnames, usernames,
filesystem paths, credentials, tokens, raw logs, prompts, or unnecessary model
output.

## Open questions

* What exact ordinary command name and argument spelling should carry the
  accepted CLI semantics?
* What should the small local-composition value be named?
* Do explicit Ollama base-URL or model override arguments provide enough
  Phase 13 value to justify their validation surface?
* After the ordinary proof succeeds, should the Phase 12 launcher be retained,
  reduced, or removed without losing proof evidence?

These are naming, ergonomics, or closeout questions. They do not alter the
proposed one-composition, one-adapter, CLI-first, default-compatible boundary.

## Decision

Accepted.

Home AI Cluster will add one explicit ordinary local runtime-composition seam
containing one `NodeRegistry` and one `AdapterRegistry`. Phase 13 ordinary startup
will be CLI-first, support exactly one local adapter per process, and use the
closed initial runtime choices `ollama` and `llama-server`.

Zero-configuration ordinary behavior remains Ollama-backed. Explicit
llama-server startup requires a loopback HTTP base URL and a non-empty model
identifier, with deterministic local validation before endpoint binding and no
network probing during parsing.

Runtime identity and runtime-specific values remain local to the executing
process. They do not become request selectors, routing inputs, remote declaration
fields, attribution values, normalized status fields, discovery inputs, or
lifecycle-management responsibilities. Retained configuration files, multiple
local adapters, generic factories, plugins, and other deferred mechanisms remain
outside Phase 13.
