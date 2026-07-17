# Phase 14 Closeout: Explicit Static-Cluster Local Composition

Status: Complete

Date: 2026-07-17

## Purpose

Record completion of Phase 14 — Explicit static-cluster local composition —
against the accepted decision, implementation sequence, automated checks, and
retained operator proof.

## Accepted decision

[RFC-0043](../RFC/RFC-0043-explicit-static-cluster-local-composition.md)
decided that one `home-ai-cluster-static-cluster` process owns exactly one
supported local composition. The closed choices are `ollama` and
`llama-server`; the default remains Ollama. Static declarations remain
topology-only: they do not contain a runtime, adapter, model, local runtime URL,
or lifecycle setting.

Runtime-specific values are validated and the local composition is constructed
before endpoint binding, without a network probe. Every process still owns one
local adapter and one matching local node announcement.

## Delivered sequence

- Investigation PR [#261](https://github.com/frian/home-ai-cluster/pull/261)
  (implementation commit `fed62a9`) established that the existing static-cluster
  command should be extended, rather than adding a second command. It recorded
  that runtime choice belongs outside declarations, the Phase 13 composition
  seam should be reused, Ollama stays the default, and an architectural RFC was
  required.
- RFC PR [#262](https://github.com/frian/home-ai-cluster/pull/262) accepted
  RFC-0043 before implementation.
- Implementation PR [#263](https://github.com/frian/home-ai-cluster/pull/263)
  registered the three concrete runtime arguments in a shared seam, made its
  conditional validation and wording canonical, retained defensive direct
  composition validation, and constructed the concrete composition. It added no
  generic factory, plugin, or other runtime architecture, and preserved
  `home-ai-cluster-local` behavior.
- Implementation PR [#264](https://github.com/frian/home-ai-cluster/pull/264)
  made both static-cluster construction paths accept an explicit
  `LocalAppComposition`, reaching the existing registry wiring. The default
  Ollama composition is explicit there; no runtime flags, routing, status,
  request, result, or declaration changes were added.
- Implementation PR [#265](https://github.com/frian/home-ai-cluster/pull/265)
  added the static-cluster runtime CLI: `--runtime ollama | llama-server`,
  `--llama-server-base-url`, and `--llama-server-model`. Both declaration
  topologies share the canonical validation wording, validate before binding,
  and keep declarations topology-only.
- Proof PR [#266](https://github.com/frian/home-ai-cluster/pull/266) retained
  the real operator evidence in
  [the Phase 14 proof](phase-14-static-cluster-local-composition-proof.md).

## Compatibility and ordinary use

The existing no-option static-cluster paths remain valid and Ollama-backed:

```sh
uv run home-ai-cluster-static-cluster --declaration <DECLARATION_PATH>
uv run home-ai-cluster-static-cluster --remote-node-id <NODE_ID> --remote-base-url <BASE_URL>
```

An operator can explicitly select llama-server with either static topology:

```sh
uv run home-ai-cluster-static-cluster \
  --declaration <DECLARATION_PATH> \
  --runtime llama-server \
  --llama-server-base-url http://127.0.0.1:<LOCAL_RUNTIME_PORT> \
  --llama-server-model <LOCAL_MODEL_IDENTIFIER>

uv run home-ai-cluster-static-cluster \
  --remote-node-id <NODE_ID> \
  --remote-base-url <BASE_URL> \
  --runtime llama-server \
  --llama-server-base-url http://127.0.0.1:<LOCAL_RUNTIME_PORT> \
  --llama-server-model <LOCAL_MODEL_IDENTIFIER>
```

The accepted and rejected runtime argument combinations, operator-facing error
wording, pre-bind failure behavior, and no-probe construction boundary remain
shared with `home-ai-cluster-local`. No private runtime value is retained here.

## Retained operator proof

The proof ran at revision:

```text
d26eb7524aa8bbea72193cc4a35d7ad81247b53d
```

It used two separate ordinary Home AI Cluster processes on one trusted host as
equivalent operator-owned nodes, not a physical two-machine proof. The caller
used the ordinary static-cluster command with an explicit local llama-server
composition; the declared remote used the ordinary default Ollama local command.
No proof-specific launcher or custom wiring was used.

A capability-centered primary request returned `Proof OK` with local
attribution. After the caller's local runtime was stopped before a request, the
accepted narrow fallback returned `fallback ok` attributed to `proof-remote`.
After the remote was also stopped, the result was exactly:

```json
{"detail":"Runtime adapter unavailable"}
```

with HTTP 503. The retained proof uses placeholders for operator-owned values
and contains no private address, hostname, path, credential, token, or real
model identifier.

## Boundaries preserved

Phase 14 does not add a second static-cluster command; a generic runtime
factory, factory protocol, plugin, dynamic loading, provider registry, or
dependency-injection container; retained runtime configuration or environment
variables; multiple local adapters; runtime fallback or scheduling; discovery,
inventory, installation, lifecycle management, supervision, restart, or repair;
runtime fields in declarations; runtime, adapter, model, or node selectors in
requests; runtime-aware routing; request/result/status schema changes; remote
transport changes; OpenAI-compatible access changes; Docker, Kubernetes,
dashboard, database, or distributed configuration work.

The local-first routing order, narrow pre-request fallback, declared-node
attribution, normalized status, and existing adapter protocols remain unchanged.

## Verification

Final repository validation on the Phase 14 closeout branch:

```text
uv run ruff check .  -> All checks passed!
uv run pytest        -> 601 passed in 1.24s
```

## Conclusion

Phase 14 is complete. An ordinary explicit static cluster can now select one
supported local runtime composition while preserving Ollama compatibility,
topology-only declarations, and capability-centered cluster behavior.
