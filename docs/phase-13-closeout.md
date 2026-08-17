# Phase 13 Closeout

Status: Complete

Date: 2026-07-17

## Purpose

Record completion of Phase 13 — Explicit local runtime composition — against the
roadmap outcomes, RFC-0042, implementation, automated verification, and retained
real operator proof.

## Roadmap outcome review

The following Phase 13 outcomes are complete:

- An operator can start one ordinary Home AI Cluster node with one explicitly
  selected supported local runtime composition.
- The closed startup choices are `ollama` and `llama-server`.
- Existing zero-argument ordinary Ollama-backed application construction remains
  compatible.
- The existing `LlamaServerAdapter` can run through an ordinary application path
  without the Phase 12 proof-specific receiver launcher.
- Local runtime configuration remains explicit, static, CLI-owned, and local to
  the executing process.
- Ordinary requests, routing, remote declarations, attribution, and normalized
  status remain capability-centered and engine-independent.
- One retained privacy-safe real operator proof demonstrates ordinary
  heterogeneous node operation.

The retained proof is recorded in
`docs/phase-13-explicit-local-runtime-composition-proof.md`.

## Accepted architectural boundaries

Phase 13 implements RFC-0042 through one small explicit ordinary composition
value containing one `NodeRegistry` and one `AdapterRegistry`. One ordinary
process owns exactly one supported local adapter and one matching local node
announcement.

Runtime selection happens only at process startup. Runtime-specific base URLs and
model identifiers remain inside local adapter construction. They do not become
request constraints, routing candidate attributes, remote declaration fields,
node attribution values, or normalized status fields.

The phase did not add:

- request-level runtime, adapter, model, or node selectors;
- multiple local adapters, local adapter scheduling, or local runtime fallback;
- runtime-aware cluster routing or fallback;
- runtime or model discovery, inventory, installation, download, supervision,
  restart, repair, or lifecycle ownership;
- retained runtime configuration files or environment-variable-only hidden
  configuration;
- generic adapter factories, plugins, dynamic loading, or a service container;
- database-backed configuration, distributed configuration propagation,
  dashboard work, Docker, Kubernetes, or OpenAI-compatible API changes.

## Implementation summary

Phase 13 added `LocalAppComposition` as the narrow ordinary application
composition seam. Ordinary local request handling, internal receiving, and
normalized status can consume supplied registries while preserving the existing
factory-backed default when no explicit composition is supplied.

The `home-ai-cluster-local` command provides the explicit ordinary startup path:

```text
runtime choice: ollama | llama-server
```

The Ollama path retains the existing adapter defaults. The llama-server path
requires one loopback HTTP base URL and one non-empty model identifier. Argument
and local composition validation happen before endpoint binding and perform no
network, health, discovery, inventory, or generation probe.

Automated verification covers default compatibility, both supported runtime
choices, invalid argument combinations, local URL validation, explicit registry
composition, ordinary request and status use, and unchanged cluster-facing
contracts.

## Operator proof

The retained proof records two separate trusted-LAN machines.

The successful ordinary heterogeneous request used repository revision:

```text
2e6aeb7096a97fd7eda5155b1131dfe5246cda7d
```

The receiving machine started an ordinary application through
`home-ai-cluster-local --runtime llama-server`. The caller used the ordinary
`home-ai-cluster-static-cluster` declaration path. The request contained only
messages and the `chat` capability, and the declaration contained only remote
node identity and transport location.

The receiver exposed the existing normalized runtime status, and the caller
returned the existing normalized result attributed to the caller-owned declared
remote node.

A real negative control exposed an unhandled exhausted static-cluster connection
failure. PR #257 normalized that existing runtime-unavailability boundary without
changing routing or fallback semantics. The negative control was repeated at
revision:

```text
472b67710b312f69786af98156bdea37ecdfcede
```

It returned HTTP 503 with exactly:

```json
{"detail":"Runtime adapter unavailable"}
```

The retained proof contains no private network address, hostname, username,
filesystem path, credential, token, raw traceback, private runtime URL, or real
model identifier.

## Phase 12 proof-launcher disposition

At Phase 13 closeout, `home-ai-cluster-phase-12-heterogeneous-receiver` was
intentionally retained as historical reproducibility evidence. It remained
proof-only and was not part of the ordinary operator path.

Accepted RFC-0075 later changed only that compatibility disposition: the
launcher is now retired from current installations. The Phase 12 proof record
and Git history remain retained. Ordinary runtime composition continues through
`home-ai-cluster-local`, including the accepted llama-server path.

## Deferred work

Phase 13 does not establish dynamic runtime choice, multiple local runtimes,
engine-aware routing, runtime configuration files, discovery, scheduling, model
inventory, lifecycle management, monitoring, production authentication, or
broader deployment readiness.

Any future architectural change in these areas requires investigation and an RFC
when applicable.

## Conclusion

Phase 13 is complete.

The project now supports one explicit ordinary local runtime composition while
preserving local-first, privacy-first, capability-centered, and engine-independent
cluster-facing boundaries.
