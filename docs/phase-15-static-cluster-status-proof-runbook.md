# Phase 15 Static-Cluster Status Composition Proof Runbook

Status: Planned

Date: 2026-07-18

## Purpose

This runbook defines the minimum real operator proof required to close Phase 15.
It does not claim that the proof has already run.

The proof must demonstrate that the ordinary `home-ai-cluster-status` command can
inspect the same explicitly selected local llama-server composition used by an
ordinary `home-ai-cluster-static-cluster` process while retaining normalized,
engine-independent status output.

## Scope

The proof uses only ordinary operator-owned commands and existing repository
interfaces. It must not use custom Python wiring, a proof-specific launcher,
mocked adapters, Docker, Kubernetes, runtime discovery, retained runtime
configuration, or request-level runtime selection.

The proof does not need to repeat Phase 14 routing, fallback, or request execution
coverage. Its narrow subject is explicit local composition selection for finite
static-cluster status inspection.

## Required revision

Run the proof from one exact repository revision that contains the merged Phase 15
implementation. Record that revision in the retained proof document.

## Preconditions

- One operator-managed llama-server is running on a loopback HTTP address.
- The selected llama-server model identifier is locally valid.
- One ordinary `home-ai-cluster-static-cluster` process is started with that same
  loopback URL and model identifier.
- The static declaration is valid and contains only accepted remote topology.
- Every retained value that could identify a machine, path, user, port, model, or
  credential is replaced with a placeholder.

A separate physical remote machine is not required. One trusted host with ordinary
processes is sufficient, provided the limitation is recorded.

## Sanitized startup command

Start the ordinary static cluster with one explicit llama-server local composition:

```sh
uv run home-ai-cluster-static-cluster \
  --declaration <DECLARATION_PATH> \
  --runtime llama-server \
  --llama-server-base-url http://127.0.0.1:<LOCAL_RUNTIME_PORT> \
  --llama-server-model <LOCAL_MODEL_IDENTIFIER>
```

The declaration must remain topology-only and must not contain the local runtime
choice, adapter name, runtime URL, model identifier, credential, or lifecycle
setting.

## Status observation command

While the ordinary static-cluster process uses the explicit llama-server
composition, run status with the same operator-owned local composition values:

```sh
uv run home-ai-cluster-status \
  --declaration <DECLARATION_PATH> \
  --runtime llama-server \
  --llama-server-base-url http://127.0.0.1:<LOCAL_RUNTIME_PORT> \
  --llama-server-model <LOCAL_MODEL_IDENTIFIER>
```

Retain only the compact normalized JSON emitted by the command after replacing any
operator-specific remote node identity with an approved proof placeholder.

## Required positive observation

The retained result must show:

- declaration status remains coherent;
- the fixed local node remains `local`;
- local `application_status` remains `local`;
- local `runtime_status` is `available`;
- declared remotes remain in declaration order;
- remote values use only the existing normalized application and runtime status
  vocabularies; and
- no runtime, adapter, model, URL, executable, filesystem path, or private machine
  identity appears in the result.

An acceptable sanitized shape is equivalent to:

```json
{
  "declaration_status": "coherent",
  "nodes": [
    {
      "node_id": "local",
      "application_status": "local",
      "runtime_status": "available"
    },
    {
      "node_id": "proof-remote",
      "application_status": "reachable",
      "runtime_status": "available"
    }
  ]
}
```

The exact normalized remote statuses may reflect the real remote process state.
The proof must not manufacture a successful remote observation.

## Required negative observation

Stop or make unavailable only the operator-managed loopback llama-server, then run
the same status command again without changing the declaration or local composition
arguments.

The retained result must show the existing normalized local failure category,
expected to be `unavailable` or `observation-failed` according to the existing
collector boundary, while:

- the command still exits according to existing status semantics;
- declared remotes are still observed in declaration order;
- no raw adapter exception, runtime URL, model identifier, transport detail, or
  private machine identity appears; and
- the output schema and vocabulary remain unchanged.

Restarting, supervising, or repairing llama-server is operator-owned and outside the
proof.

## Compatibility observation

Run the no-runtime-option form:

```sh
uv run home-ai-cluster-status \
  --declaration <DECLARATION_PATH>
```

Retain only the fact that it followed the existing default Ollama composition path.
Do not retain runtime-private logs or configuration. Automated focused tests may be
cited for exact registry construction; the real proof does not need to expose a
runtime name in normalized status.

## Evidence to retain

Create `docs/phase-15-static-cluster-status-composition-proof.md` only after the run
has succeeded. The retained record should include:

- status `Retained`;
- date and exact repository revision;
- sanitized topology and declaration shape;
- sanitized startup and status commands;
- one positive normalized status result;
- one local-runtime-unavailable normalized status result;
- the no-option compatibility observation;
- privacy and trust-boundary observations;
- proof obligations covered;
- limitations; and
- a conclusion that states only what was directly demonstrated.

## Evidence not to retain

Do not retain:

- real IP addresses, hostnames, ports, usernames, or absolute paths;
- real model identifiers when they can identify operator configuration;
- credentials, tokens, authorization headers, environment dumps, or process lists;
- raw llama-server or Ollama logs;
- raw Python exceptions or HTTP client traces;
- prompts or generated responses;
- screenshots when normalized text is sufficient; or
- claims about physical machine separation unless the proof actually used it.

## Proof obligations

The retained run must demonstrate that:

1. the ordinary status command accepts the same explicit llama-server composition
   values as ordinary static-cluster startup;
2. the selected local composition is observed as the fixed local node;
3. normalized status contains no runtime, adapter, model, URL, or private machine
   identity;
4. declarations remain topology-only;
5. declared remotes remain observed through the existing normalized protocol and in
   declaration order;
6. local runtime unavailability remains normalized without raw private details;
7. the no-option path remains compatible and Ollama-backed;
8. no routing, fallback, request, lifecycle, discovery, monitoring, persistence,
   plugin, database, dashboard, Docker, or Kubernetes behavior is introduced; and
9. the retained evidence is privacy-safe.

## Completion rule

This runbook may be merged before the proof is executed because it records only the
reviewed procedure. Phase 15 is not complete until a separate retained proof record
contains real sanitized observations from one successful operator run.
