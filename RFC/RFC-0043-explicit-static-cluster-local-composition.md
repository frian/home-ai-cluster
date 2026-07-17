# RFC-0043: Explicit Static-Cluster Local Composition

Status: Draft

Date: 2026-07-17

Author: frian

## Summary

Home AI Cluster should let an operator start the existing ordinary
`home-ai-cluster-static-cluster` process with exactly one explicitly chosen
supported local runtime composition while preserving every current invocation
as Ollama-backed by default.

The command should reuse the same closed local runtime choices and local
validation contract accepted in RFC-0042: `ollama` or `llama-server`.
`llama-server` requires a loopback HTTP base URL and a non-empty model
identifier. The selected local composition should be constructed before server
startup and supplied to the existing single-remote or ordered-remote static
wiring builders.

Remote declarations remain topology-only. Runtime identity and values remain
local to the calling process and do not enter requests, routing, fallback,
remote declarations, attribution, normalized status, retained history, or
cluster-facing errors.

## Problem

Phase 13 introduced an ordinary standalone startup path for one explicitly
chosen local runtime composition:

```text
home-ai-cluster-local --runtime ollama | llama-server
```

That path constructs one matching local node announcement, one `NodeRegistry`,
and one `AdapterRegistry`, then supplies them through `LocalAppComposition` to
ordinary application construction.

The ordinary static-cluster process still constructs its local candidate
internally through the fixed default factories:

* `create_static_local_node_registry()`; and
* `create_static_runtime_adapter_registry()`.

Those factories produce the existing Ollama-backed local candidate. Both
`create_static_cluster_app(...)` and
`create_static_cluster_collection_app(...)` use them directly before building
single-remote or ordered-remote static wiring.

As a result, an operator can explicitly choose llama-server for an ordinary
standalone node but cannot choose the same already-supported local composition
for an ordinary static-cluster caller. The only workaround would be custom
Python wiring or a new proof-specific launcher, neither of which is an ordinary
operator contract.

The existing static wiring builders already accept constructed local
registries. The missing decision is therefore at process startup and
composition ownership, not in routing, fallback, transport, request, result,
status, or declaration architecture.

## Goals

This RFC should:

* let `home-ai-cluster-static-cluster` use one explicitly selected supported
  local runtime composition;
* preserve all existing static-cluster invocations as Ollama-backed when no new
  runtime option is supplied;
* support the closed initial runtime set `ollama` and `llama-server`;
* reuse the accepted Phase 13 local composition and validation semantics rather
  than inventing a second runtime contract;
* apply the selected local composition to both the single-inline-remote and
  declaration-backed ordered-remote paths;
* preserve topology-only remote declarations;
* preserve local-first capability routing and the accepted narrow fallback;
* keep runtime-specific values local to adapter construction;
* validate all local runtime arguments before server binding and without a
  network probe; and
* require focused compatibility tests and one privacy-safe real operator proof.

## Non-goals

This RFC does not add:

* runtime, adapter, model, or node selectors to ordinary requests;
* runtime, adapter, model, or local-composition fields to static declarations;
* automatic runtime selection, discovery, or model inventory;
* multiple local adapters in one process;
* local adapter priority, scheduling, or fallback;
* engine-aware routing or remote fallback;
* model downloading, runtime installation, supervision, restart, repair, or
  lifecycle management;
* a retained local runtime configuration file;
* environment-variable-only hidden configuration;
* a second static-cluster command with overlapping behavior;
* a generic adapter factory, plugin system, service container, provider
  registry, or dynamic loading;
* changes to remote HTTP transport, request/result schemas, normalized status,
  attribution, or retained request history;
* database-backed configuration, distributed configuration propagation,
  Docker, Kubernetes, or dashboard work; or
* OpenAI-compatible API changes.

## Proposal

### Extend the existing ordinary static-cluster command

The existing `home-ai-cluster-static-cluster` command should remain the one
ordinary process for explicit static local-plus-remote operation.

It should accept the same semantic local runtime choice as the Phase 13 command:

```text
runtime choice: ollama | llama-server
```

The intended operator shape is equivalent to:

```sh
uv run home-ai-cluster-static-cluster \
  --declaration <DECLARATION_PATH> \
  --runtime llama-server \
  --llama-server-base-url http://127.0.0.1:<PORT> \
  --llama-server-model <MODEL_IDENTIFIER>
```

The exact implementation may share parser helpers, argument registration, or a
small validated value with `home-ai-cluster-local`, but it must not create a
generic configuration or dependency-injection framework.

### Default compatibility

When no local runtime option is supplied, the command must retain its current
behavior:

* construct the ordinary default Ollama composition;
* accept the same declaration and inline-remote invocation forms;
* bind to the same loopback host and port;
* build the same single-remote or ordered-remote wiring;
* preserve current local-first candidate ordering; and
* preserve current normalized success and failure behavior.

An explicit `--runtime ollama` choice should construct the same ordinary Ollama
composition as the default path. It should not add Phase 14 Ollama URL or model
overrides.

### Llama-server local composition

When `llama-server` is selected, startup requires:

* one absolute loopback `http` base URL; and
* one non-empty model identifier.

The command should construct the same ordinary local llama-server composition
semantics accepted by RFC-0042:

* local node ID `local`;
* capability `chat`;
* existing static availability and health shape;
* one `LlamaServerAdapter`;
* one matching `NodeRegistry`; and
* one matching `AdapterRegistry`.

The runtime base URL and model identifier belong only to the local adapter.
They must not be copied into static remote declarations, routing candidates,
request constraints, attribution, normalized status, retained history, or
cluster-facing error details.

### One validated local composition input

After argument parsing and validation, the static-cluster process should obtain
one already-built `LocalAppComposition` or equivalent accepted composition value.

Both existing application-construction paths should consume that composition:

* `create_static_cluster_app(...)` for one inline remote; and
* `create_static_cluster_collection_app(...)` for one ordered declaration
  collection.

The static wiring builders already accept a local `NodeRegistry` and
`AdapterRegistry`. The implementation should pass the composition's registries
there instead of unconditionally calling the default Ollama factories.

This is explicit construction reuse. It is not a new core abstraction or a
general runtime factory.

### Keep static declarations topology-only

The existing declaration remains solely an operator-owned description of
remote topology. It must not gain fields for:

* local runtime choice;
* local adapter name;
* local runtime base URL;
* local model identifier;
* local credentials; or
* runtime lifecycle.

Local composition is selected at process startup. Remote declarations continue
to describe only accepted remote node identity and Home AI Cluster transport
addresses.

### Argument ownership and validation

The static-cluster parser should preserve its existing topology input modes:

* one declaration path; or
* one complete inline remote pair.

Local runtime arguments are orthogonal process-startup inputs and may be
combined with either complete topology mode.

Validation must reject before endpoint binding:

* a runtime outside the closed supported set;
* llama-server-specific values when the selected runtime is Ollama;
* missing llama-server base URL or model when llama-server is selected;
* an empty required value;
* a llama-server URL outside the accepted loopback HTTP boundary;
* an incomplete topology mode; and
* incompatible declaration and inline-remote topology inputs.

Validation performs no health probe, network reachability check, runtime
discovery, model inventory, or generation request.

Invalid input must produce a compact non-zero operator-facing failure without
raw adapter exceptions, remote transport details, credentials, or private
values beyond the operator-supplied local input required to identify the error.

### Preserve routing and fallback

The selected local composition changes only which one local adapter backs the
existing local candidate.

It must not change:

* capability matching;
* local-first candidate ordering;
* ordered remote priority;
* the accepted pre-request connection-unavailable fallback boundary;
* the no-retry-after-transmission rule;
* remote HTTP transport behavior;
* declared-node attribution; or
* routing explanation semantics.

Routing continues to ask which candidate provides the required capability, not
which runtime or model should execute the request.

### Preserve normalized status and failures

The existing normalized local status projection should observe the selected
local adapter through the supplied registries. Cluster-facing status remains
engine-independent.

Runtime request exhaustion should continue to normalize at the API boundary to:

```json
{"detail":"Runtime adapter unavailable"}
```

with HTTP 503, without exposing local runtime URLs, model identifiers, adapter
exception names, or remote transport details.

## Rationale

Extending the existing command is the smallest adequate solution.

The static-cluster process already owns:

* topology argument parsing;
* declaration loading and validation;
* remote client lifecycle;
* construction of single or ordered static wiring; and
* loopback server startup.

Phase 13 already owns the explicit local runtime composition contract. Joining
those two existing seams closes one concrete operator asymmetry without changing
core orchestration.

This supports the project principles:

* **local-first:** the chosen local candidate remains first;
* **privacy-first:** runtime-private values remain local and are not retained in
  topology files or cluster-facing outputs;
* **engine-independent:** requests, routing, fallback, status, and attribution
  remain independent from runtime identity;
* **capability-centered:** candidate matching remains based on `chat` capability;
* **boring solutions first:** one existing command gains one closed option set;
* **architecture before implementation:** the CLI and compatibility contract are
  decided before code; and
* **no premature abstraction:** concrete composition reuse replaces factories,
  plugins, or dynamic loading.

## Alternatives considered

### Add local runtime fields to the static declaration

Rejected. The declaration describes remote topology and is retained for
repeatable cluster shape. Adding local runtime values would mix local process
composition with remote topology, introduce sensitive or machine-specific
values into a retained artifact, and require precedence rules between CLI and
file configuration.

### Add a second combined static-cluster command

Rejected. A second command would duplicate topology parsing, declaration
loading, remote client lifecycle, validation, startup, tests, and documentation.
The existing command is already the ordinary operator path for this process
shape.

### Keep the static-cluster caller fixed to Ollama

Rejected. It leaves the Phase 14 roadmap outcome unsatisfied and forces custom
Python wiring for an already-supported ordinary composition.

### Let the command accept built registries through a generic loader

Rejected. Dynamic loading or serialized registry construction is unnecessary.
The project has exactly two supported concrete runtime choices and an accepted
small in-process composition value.

### Introduce a generic runtime factory or plugin system

Rejected. Two concrete adapters do not justify a plugin lifecycle, provider
registry, factory protocol, configuration schema, or service container.

### Put local composition in environment variables

Rejected. Hidden process inputs would make operator intent and precedence less
clear. RFC-0042 already chose explicit CLI-first composition for this stage.

## Trade-offs

The static-cluster command gains additional arguments and validation branches.
This modestly increases CLI surface area, but avoids a second command and keeps
all ordinary static-cluster startup in one place.

Some runtime argument semantics may need to be shared with
`home-ai-cluster-local`. A small concrete helper or validated value can reduce
duplication, but the implementation must resist turning that reuse into a
generic runtime configuration framework.

CLI values remain visible in shell history and process inspection. Credentials
are not supported, and the accepted llama-server values are a loopback URL and
model identifier. A retained configuration file would introduce a larger and
more durable privacy and precedence contract.

One local adapter per process deliberately excludes local runtime fallback and
scheduling. This keeps ownership, health, execution, and failure behavior
simple.

The command remains fixed to its current loopback Home AI Cluster binding. This
RFC does not broaden server exposure or solve general deployment configuration.

## Compatibility

Existing commands must continue to work unchanged, including:

```sh
uv run home-ai-cluster-static-cluster \
  --declaration <DECLARATION_PATH>
```

and:

```sh
uv run home-ai-cluster-static-cluster \
  --remote-node-id <NODE_ID> \
  --remote-base-url <BASE_URL>
```

Both retain the current Ollama-backed local candidate when no runtime option is
supplied.

The following also becomes valid after implementation:

```sh
uv run home-ai-cluster-static-cluster \
  --declaration <DECLARATION_PATH> \
  --runtime llama-server \
  --llama-server-base-url http://127.0.0.1:<PORT> \
  --llama-server-model <MODEL_IDENTIFIER>
```

No declaration migration is required. No request or response schema changes.
No changes are required for remote nodes.

## Privacy and trust boundary

The operator explicitly supplies local runtime composition at process startup.
Home AI Cluster does not discover runtimes, models, endpoints, configuration
files, or credentials.

The llama-server URL must remain loopback HTTP. The selected runtime's lifecycle
remains operator-owned. Home AI Cluster does not install, start, stop, supervise,
restart, repair, or download anything.

The process must not log prompts or responses by default. Runtime URLs, model
identifiers, raw adapter failures, and remote transport details must not appear
in cluster-facing requests, normalized status, attribution, retained request
history, or privacy-safe proof records.

Static remote declarations remain safe to retain because they contain only the
already-accepted topology facts and no local runtime configuration.

## Impact

After acceptance, implementation may affect:

* `src/home_ai_cluster/static_cluster.py` and focused tests;
* narrow sharing of Phase 13 runtime argument validation and concrete
  composition construction;
* the signatures of static-cluster application-construction helpers;
* documentation for the ordinary static-cluster command; and
* one retained privacy-safe real operator proof.

It must not require changes to:

* `ClusterRequest`, `ClusterResult`, or status schemas;
* routing candidate selection or fallback policy;
* remote declaration schema or loading;
* remote HTTP transport;
* adapter protocols;
* cluster-owned node attribution;
* request history semantics; or
* the OpenAI-compatible endpoint.

## Implementation sequence

After this RFC is accepted, implementation should proceed through small,
separately reviewable pull requests:

1. extract or expose the smallest concrete reuse seam for Phase 13 local runtime
   argument validation and composition construction;
2. let single-remote and ordered-remote static-cluster app construction receive
   one explicit local composition while preserving the current default;
3. extend the existing static-cluster CLI with the closed local runtime options;
4. add focused default-compatibility, validation, registry-composition, and
   server-before-binding tests;
5. retain one privacy-safe real operator proof; and
6. close Phase 14 with documentation and any proof-only disposition decision.

Agents may implement these accepted decisions. They must not broaden the
runtime choices, configuration location, declaration schema, routing policy, or
lifecycle ownership without another architectural decision.

## Proof obligations

Phase 14 is not complete until automated and retained real evidence demonstrates:

1. every pre-Phase-14 static-cluster invocation remains Ollama-backed by default;
2. explicit `--runtime ollama` produces the same ordinary local composition;
3. explicit llama-server composition starts through the ordinary
   `home-ai-cluster-static-cluster` command;
4. both inline single-remote and declaration-backed ordered-remote construction
   consume the supplied local composition;
5. existing normalized local status observes the selected local adapter without
   exposing runtime identity;
6. one ordinary capability-centered request succeeds through the explicit
   static cluster;
7. the request and declaration contain no runtime, adapter, model, or node
   selector beyond the accepted remote topology facts;
8. local-first routing and narrow remote fallback remain unchanged;
9. normalized result attribution remains cluster-owned;
10. invalid runtime argument combinations fail before server binding and without
    network probing;
11. exhausted runtime availability returns the existing privacy-safe HTTP 503;
    and
12. the proof record contains no private address, hostname, username, filesystem
    path, credential, token, raw logs, or unnecessary model output.

A two-machine proof is sufficient. It should use the ordinary command, not a
new proof-specific launcher.

## Open questions

Implementation naming for the smallest shared concrete parser or composition
helper remains open. The implementation should prefer an ordinary small module
or functions over a class hierarchy or generic factory.

Whether the retained real proof selects llama-server locally on the caller and
Ollama remotely, or another topology that exercises the same contract, remains
an operator-proof detail. It must still demonstrate ordinary static-cluster
startup and preserve engine-independent cluster-facing behavior.

No other architectural question remains open in this draft.

## Decision

Pending.
