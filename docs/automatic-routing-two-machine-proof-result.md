# Automatic Routing Two-Machine Proof Result

Status: Completed

Date: 2026-07-12

This document records an observed proof result. It is descriptive only;
accepted RFCs remain the source of architectural decisions.

## Proof statement

```text
One endpoint. Two machines. One automatically routed request.
```

Unlike RFC-0022's caller-directed `declared-remote-only` proof, this run proves
cluster-owned RFC-0025 automatic selection: the declared remote was the sole
selectable exact `chat` match. Ordinary `/v1/chat` remains local-only outside
the dedicated proof process.

## Actual topology

### Calling machine

- Ubuntu Linux;
- `home-ai-cluster-automatic-proof REMOTE_ADDRESS`;
- proof-only application bound to `127.0.0.1:8000`.

### Receiving machine

- Dell OptiPlex running Windows 11 Pro;
- receiving application bound to `0.0.0.0:8000` on the trusted LAN;
- `POST /internal/cluster/request` and local Ollama execution using `llama3.2`.

No container, virtual machine, discovery, registration, VPN, or overlay network
was used.

## Executed path

```text
user curl
  -> calling machine proof-only 127.0.0.1:8000/v1/chat
  -> proof request constructed with local_only=false
  -> no selectable local chat candidate
  -> one selectable declared-remote chat candidate
  -> RFC-0025 automatic capability selection
  -> declared remote selected as sole selectable candidate
  -> HTTP transport across the trusted LAN
  -> receiving machine /internal/cluster/request
  -> receiving machine local Ollama adapter
  -> llama3.2
  -> normalized ClusterResult with caller-owned node_id=declared-remote
  -> HTTP 200 response on the calling machine
```

No caller-directed selection mode was supplied, and no retry or fallback was
added or observed.

## Successful request

```sh
curl -i -X POST http://127.0.0.1:8000/v1/chat \
  -H 'Content-Type: application/json' \
  --data-raw '{"messages":[{"role":"user","content":"Reply with exactly: automatic routing proof succeeded"}],"capability":"chat"}'
```

## Observed result

The calling machine returned `HTTP/1.1 200 OK` with:

```json
{"content":"automatic routing proof succeeded","adapter":"ollama","model":"llama3.2","node_id":"declared-remote"}
```

## What this proves

The result demonstrates deliberate automatic-proof startup, proof-only
`local_only=false`, one manually declared remote `chat` candidate, no selectable
local `chat` candidate, RFC-0025 automatic selection, real two-machine HTTP
movement, receiver-local adapter execution, normalized success, and
authoritative caller-owned attribution. It further demonstrates:

```text
fake in distribution, but not fake in architecture
```

The setup remains static and manual; the architectural boundaries and automatic
selection are real.

## What this does not prove

It does not establish production readiness, authentication, authorization, TLS
policy, trust establishment, discovery, registration, persistence, multiple
remote candidates, scoring, scheduling, load balancing, health-aware routing,
retry, fallback, failure recovery, streaming, cross-site execution, performance
suitability, model quality, or ordinary application automatic routing.

## Operator-input failures observed

An invalid placeholder hostname and an incorrect address produced visible
resolution or connection failures. Supplying the reachable trusted-LAN address
corrected these operator-input incidents; they were not implementation defects.

## Architectural boundary

PR #147 implemented the dedicated proof-only process. It introduced no general
routing or configuration surface. The ordinary application and RFC-0022 proof
path remain unchanged.

## Relevant references

- [RFC-0025](../RFC/RFC-0025-minimal-capability-based-candidate-selection.md)
- [RFC-0026](../RFC/RFC-0026-explicit-automatic-routing-proof.md)
- [Phase 4 Current State](phase-4-current-state.md)
