# RFC-0043: Explicit Static-Cluster Local Composition

Status: Accepted

Date: 2026-07-17

Author: frian

## Summary

Home AI Cluster accepts one explicit local runtime-composition path for the
existing ordinary `home-ai-cluster-static-cluster` process.

The command may select exactly one supported local runtime at process startup:
`ollama` or `llama-server`. When no runtime option is supplied, every existing
static-cluster invocation remains Ollama-backed.

The selected local composition is constructed before endpoint binding and is
supplied to the existing single-remote or ordered-remote static wiring path.
Remote declarations remain topology-only. Runtime identity and runtime-specific
values remain local to the calling process and do not enter requests, routing,
fallback, declarations, attribution, normalized status, retained history, or
cluster-facing failures.

## Problem

Phase 13 added an ordinary standalone command that can explicitly construct one
supported local runtime composition:

```text
home-ai-cluster-local --runtime ollama | llama-server
```

That command builds one matching local node announcement, one `NodeRegistry`,
and one `AdapterRegistry`, then supplies them through `LocalAppComposition`.

The ordinary static-cluster process still constructs its local candidate with
the fixed default factories:

- `create_static_local_node_registry()`;
- `create_static_runtime_adapter_registry()`.

Both the single-inline-remote and declaration-backed ordered-remote paths are
therefore fixed to Ollama locally, even though their wiring builders already
accept constructed local registries.

The missing decision is at process startup and composition ownership. It is not
a routing, fallback, transport, request, result, status, or declaration problem.

## Goals

This RFC establishes that:

- `home-ai-cluster-static-cluster` may use one explicitly selected supported
  local runtime composition;
- existing invocations remain Ollama-backed when no runtime option is supplied;
- the closed supported set is `ollama` and `llama-server`;
- the Phase 13 composition and validation semantics are reused;
- both single-remote and ordered-remote construction consume the selected local
  composition;
- static declarations remain topology-only;
- local-first capability routing and narrow fallback remain unchanged;
- runtime-specific values remain local to adapter construction;
- validation completes before server binding and performs no network probe; and
- focused compatibility tests and one privacy-safe real proof are required.

## Non-goals

This RFC does not add:

- runtime, adapter, model, or node selectors to ordinary requests;
- local runtime or model fields to static declarations;
- automatic runtime selection, discovery, or model inventory;
- multiple local adapters in one process;
- local adapter scheduling, priority, or fallback;
- engine-aware routing or remote fallback;
- runtime installation, model downloading, supervision, restart, repair, or
  lifecycle management;
- retained local runtime configuration;
- environment-variable-only hidden configuration;
- a second overlapping static-cluster command;
- generic adapter factories, plugins, provider registries, service containers,
  or dynamic loading;
- changes to request, result, status, attribution, remote transport, or retained
  history contracts;
- database-backed configuration, Docker, Kubernetes, dashboard work, or
  distributed configuration propagation; or
- OpenAI-compatible API changes.

## Decision

### Extend the existing command

`home-ai-cluster-static-cluster` remains the single ordinary local-plus-remote
startup command.

It accepts the same semantic local runtime choice as RFC-0042:

```text
runtime choice: ollama | llama-server
```

The intended operator form is equivalent to:

```sh
uv run home-ai-cluster-static-cluster \
  --declaration <DECLARATION_PATH> \
  --runtime llama-server \
  --llama-server-base-url http://127.0.0.1:<PORT> \
  --llama-server-model <MODEL_IDENTIFIER>
```

The exact helper and function names remain implementation details. Reuse must be
small and concrete; it must not become a generic runtime configuration or
dependency-injection framework.

### Preserve default compatibility

When no local runtime option is supplied, the command retains its current
behavior:

- ordinary default Ollama composition;
- existing declaration and inline-remote invocation forms;
- current loopback host and port;
- current single-remote or ordered-remote wiring;
- current local-first candidate ordering; and
- current normalized success and failure behavior.

Explicit `--runtime ollama` constructs the same ordinary Ollama composition as
the default path. Phase 14 does not add Ollama URL or model overrides.

### Explicit llama-server composition

Selecting `llama-server` requires:

- one absolute loopback `http` base URL; and
- one non-empty model identifier.

The process constructs the ordinary Phase 13 llama-server composition:

- local node ID `local`;
- capability `chat`;
- existing static availability and health shape;
- one `LlamaServerAdapter`;
- one matching `NodeRegistry`; and
- one matching `AdapterRegistry`.

The base URL and model identifier belong only to the local adapter. They are not
copied into declarations, requests, routing candidates, constraints,
attribution, normalized status, retained history, or cluster-facing errors.

### One composition for both static paths

After parsing and validation, the process obtains one already-built
`LocalAppComposition`.

Both existing construction paths consume it:

- `create_static_cluster_app(...)` for one inline remote;
- `create_static_cluster_collection_app(...)` for an ordered declaration
  collection.

The composition's registries are passed to the existing static wiring builders
instead of unconditionally constructing the default Ollama registries.

### Keep declarations topology-only

Static declarations continue to describe only accepted remote node identity and
Home AI Cluster transport addresses.

They do not gain fields for local runtime choice, adapter name, runtime URL,
model identifier, credentials, or lifecycle ownership.

Local composition is explicit process-startup input, orthogonal to the complete
topology input mode.

### Validation

The existing topology modes remain:

- one declaration path; or
- one complete inline remote pair.

Local runtime arguments may accompany either complete topology mode.

Validation rejects before endpoint binding:

- a runtime outside the closed supported set;
- llama-server-specific values with Ollama;
- missing llama-server URL or model;
- empty required values;
- a llama-server URL outside the loopback HTTP boundary;
- incomplete topology input; and
- combined declaration and inline-remote topology input.

Validation performs no health probe, reachability check, runtime discovery,
model inventory, or generation request. Failures are compact and do not expose
raw adapter exceptions, transport details, credentials, or unrelated private
values.

### Preserve routing, fallback, status, and failures

The selected composition changes only the one adapter backing the existing local
candidate.

It does not change:

- capability matching;
- local-first candidate ordering;
- ordered remote priority;
- the accepted pre-request connection-unavailable fallback boundary;
- the no-retry-after-transmission rule;
- remote HTTP transport;
- declared-node attribution;
- routing explanation semantics; or
- normalized status vocabulary.

Runtime availability exhaustion remains normalized at the API boundary as:

```json
{"detail":"Runtime adapter unavailable"}
```

with HTTP 503 and without runtime URLs, model identifiers, exception names, or
remote transport details.

## Rationale

The static-cluster process already owns topology parsing, declaration loading,
remote-client lifecycle, static wiring construction, and loopback server
startup. Phase 13 already owns explicit local composition.

Combining these two existing seams is the smallest adequate solution. It closes
a concrete operator asymmetry without changing core orchestration.

This preserves:

- local-first operation;
- privacy-first runtime ownership;
- engine-independent cluster-facing contracts;
- capability-centered routing;
- boring, explicit startup choices; and
- architecture-before-implementation.

## Alternatives considered

### Runtime fields in the declaration

Rejected. This would mix local process composition with retained remote topology,
introduce machine-specific values into the declaration, and require precedence
rules between CLI and file configuration.

### A second combined command

Rejected. It would duplicate topology parsing, declaration loading, client
lifecycle, startup behavior, tests, and documentation.

### Keep static-cluster local execution fixed to Ollama

Rejected. It leaves the Phase 14 roadmap outcome unsatisfied and requires custom
Python wiring for an already-supported ordinary composition.

### Generic loader, factory, or plugin system

Rejected. Two concrete supported adapters and one accepted composition value do
not justify dynamic loading, provider registration, plugin lifecycle, or a
service container.

### Environment-variable runtime selection

Rejected. Hidden inputs would make operator intent and precedence less explicit.
RFC-0042 already selected CLI-first configuration for this stage.

## Trade-offs

The existing command gains a small argument and validation surface. This is less
complex than adding another command or a retained configuration format.

A small shared concrete helper may be required to avoid duplicating Phase 13
validation and construction. That reuse must remain specific to the two accepted
runtime choices.

CLI values can be visible in shell history and process inspection. Credentials
are not supported. The accepted llama-server values are a loopback URL and a
model identifier.

One adapter per process deliberately excludes local runtime fallback and
scheduling. This keeps execution and failure ownership understandable.

## Compatibility

These existing forms continue unchanged and remain Ollama-backed by default:

```sh
uv run home-ai-cluster-static-cluster \
  --declaration <DECLARATION_PATH>
```

```sh
uv run home-ai-cluster-static-cluster \
  --remote-node-id <NODE_ID> \
  --remote-base-url <BASE_URL>
```

No declaration migration, request-schema change, response-schema change, or
remote-node update is required.

## Privacy and trust boundary

The operator supplies local composition explicitly at process startup. Home AI
Cluster does not discover runtimes, models, endpoints, files, or credentials.

The llama-server URL remains loopback HTTP. Runtime lifecycle remains
operator-owned. Home AI Cluster does not install, start, stop, supervise,
restart, repair, or download runtimes or models.

Prompts and responses are not logged by default. Runtime URLs, model identifiers,
raw failures, and transport details do not appear in cluster-facing outputs,
retained history, or privacy-safe proof records.

## Impact

Implementation may affect:

- `src/home_ai_cluster/static_cluster.py` and focused tests;
- narrow sharing of Phase 13 validation and concrete composition construction;
- static-cluster application-construction helper signatures;
- ordinary static-cluster documentation; and
- one retained privacy-safe real operator proof.

It must not require changes to requests, results, status schemas, routing policy,
fallback policy, declaration schema, remote transport, adapter protocols,
attribution, request history, or the OpenAI-compatible endpoint.

## Implementation sequence

Implementation should proceed through small dedicated pull requests:

1. expose the smallest concrete reuse seam for Phase 13 validation and
   composition construction;
2. let single-remote and ordered-remote static construction receive one explicit
   local composition while preserving the current default;
3. extend the existing static-cluster CLI with the closed runtime options;
4. add focused compatibility, validation, composition, and pre-binding tests;
5. retain one privacy-safe real operator proof; and
6. close Phase 14.

Agents may implement these accepted decisions. They do not own decisions and
must not broaden runtime choices, configuration location, declaration schema,
routing policy, or lifecycle ownership.

## Proof obligations

Phase 14 is not complete until evidence demonstrates:

1. every previous static-cluster invocation remains Ollama-backed by default;
2. explicit `--runtime ollama` produces the same composition;
3. explicit llama-server composition starts through the ordinary command;
4. both static construction paths consume the supplied composition;
5. normalized status observes the selected local adapter without exposing
   runtime identity;
6. one ordinary capability-centered request succeeds;
7. request and declaration remain free of runtime, adapter, model, and node
   selectors beyond accepted remote topology;
8. local-first routing and narrow fallback remain unchanged;
9. result attribution remains cluster-owned;
10. invalid runtime combinations fail before binding and without probing;
11. exhausted runtime availability returns the existing privacy-safe HTTP 503;
12. the retained proof contains no private address, hostname, username, path,
    credential, token, raw log, or unnecessary model output.

A two-machine proof is sufficient and must use the ordinary command rather than
a new proof-specific launcher.

## Open questions

Only implementation naming for the smallest shared concrete helper remains open.
It should prefer ordinary functions or a small concrete value over a class
hierarchy or generic factory.
