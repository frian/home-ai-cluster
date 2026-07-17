# Phase 15 Closeout: Explicit Static-Cluster Status Composition

Status: Complete

Date: 2026-07-18

## Purpose

Record completion of Phase 15 — Explicit static-cluster status composition —
against the accepted decision, merged implementation, automated checks, and
retained privacy-safe operator proof.

## Accepted decision

[RFC-0044](../RFC/RFC-0044-explicit-static-cluster-status-composition.md)
decided that the existing `home-ai-cluster-status` command may explicitly select
one supported local runtime composition from the same closed choices used by
ordinary static-cluster startup:

```text
ollama
llama-server
```

Ollama remains the no-option default. Runtime selection stays an operator-owned
process-composition concern and does not enter declarations, topology, status
models, requests, routing, fallback, attribution, or lifecycle behavior.

The command must load and validate the static declaration before conditional
runtime validation and composition construction. It constructs exactly one
existing `LocalAppComposition`, then passes its local node and adapter registries
to the unchanged status collector. Remote observation remains sequential and uses
the existing normalized Home AI Cluster status protocol.

## Delivered sequence

- Investigation PR [#269](https://github.com/frian/home-ai-cluster/pull/269)
  recorded that the existing status command should be extended, that the shared
  `local_runtime_composition` boundary already fits, and that no new generic
  factory, plugin, registry abstraction, persistence, discovery, or status model
  was required.
- RFC proposal PR [#270](https://github.com/frian/home-ai-cluster/pull/270)
  introduced RFC-0044.
- RFC acceptance PR [#271](https://github.com/frian/home-ai-cluster/pull/271)
  changed RFC-0044 to `Accepted` before implementation.
- Implementation PR [#272](https://github.com/frian/home-ai-cluster/pull/272)
  added the shared runtime CLI arguments to `home-ai-cluster-status`, preserved
  declaration-first validation, constructed exactly one local composition, and
  injected its registries into the unchanged collector. Focused tests covered
  default Ollama, explicit llama-server, declaration-first construction blocking,
  invalid runtime combinations, and unchanged remote observation behavior.
- Proof runbook PR [#273](https://github.com/frian/home-ai-cluster/pull/273)
  defined the minimum real proof and strict privacy-safe evidence boundary.
- Proof PR [#274](https://github.com/frian/home-ai-cluster/pull/274) retained the
  real operator evidence in
  [the Phase 15 proof](phase-15-static-cluster-status-composition-proof.md).

## Compatibility and ordinary use

The existing no-option status command remains valid and Ollama-backed:

```sh
uv run home-ai-cluster-status \
  --declaration <DECLARATION_PATH>
```

An operator can inspect an explicit llama-server local composition with:

```sh
uv run home-ai-cluster-status \
  --declaration <DECLARATION_PATH> \
  --runtime llama-server \
  --llama-server-base-url http://127.0.0.1:<LOCAL_RUNTIME_PORT> \
  --llama-server-model <LOCAL_MODEL_IDENTIFIER>
```

The declaration remains topology-only. The output remains compact normalized JSON
and contains no runtime, adapter, model, URL, executable, filesystem path, or
private machine identity.

## Retained operator proof

The proof ran against revision:

```text
2278f4d37f80748e88c863f54c32144c0fc28337
```

It used ordinary operator-owned processes on one trusted host: one loopback
llama-server, one ordinary `home-ai-cluster-local` remote node, and one finite
`home-ai-cluster-status` invocation. It did not claim physical-machine separation.

With explicit llama-server available, the normalized result was:

```json
{"declaration_status":"coherent","nodes":[{"node_id":"local","application_status":"local","runtime_status":"available"},{"node_id":"proof-remote","application_status":"reachable","runtime_status":"available"}]}
```

After only llama-server stopped, the same explicit command returned:

```json
{"declaration_status":"coherent","nodes":[{"node_id":"local","application_status":"local","runtime_status":"unavailable"},{"node_id":"proof-remote","application_status":"reachable","runtime_status":"available"}]}
```

The no-option Ollama compatibility path also returned the expected normalized
available result. The retained proof contains placeholders rather than real ports,
paths, model identifiers, hostnames, credentials, logs, prompts, responses, or
screenshots.

The run did not independently start `home-ai-cluster-static-cluster`. Reuse of the
same shared local composition boundary and argument shape is established by the
accepted architecture, merged implementation, focused tests, and the retained
Phase 14 ordinary static-cluster proof. This Phase 15 proof directly demonstrates
finite status inspection.

## Boundaries preserved

Phase 15 does not add runtime fields to declarations or status output; runtime,
adapter, model, or node selectors to requests; engine-aware routing; multiple local
adapters; runtime fallback; discovery; model inventory; scheduling; supervision;
lifecycle management; monitoring; background polling; dynamic plugins; a generic
factory; dependency injection; persisted configuration; environment-variable
configuration; a database; dashboard; Docker; or Kubernetes.

Routing, fallback, topology, declaration semantics, remote transport, status
vocabulary, request and result models, retained history, attribution, and runtime
lifecycle ownership remain unchanged.

## Verification

The implementation branch was validated by the operator with:

```text
uv run ruff check .  -> passed
uv run pytest        -> passed
```

The retained proof then exercised the merged implementation with real ordinary
processes and normalized cluster-facing output.

## Conclusion

Phase 15 is complete. An operator can explicitly inspect one supported local
runtime composition through the ordinary finite static-cluster status command,
while no-option Ollama compatibility, topology-only declarations, sequential
normalized remote observation, and engine-independent status output remain intact.
