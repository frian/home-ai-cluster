# Phase 3 Current State

Status: Draft

This document describes the current Phase 3 implementation state.

It is descriptive, not a new architectural decision. Accepted RFCs remain the
source of architectural decisions.

## Phase 3 checkpoint

The project has demonstrated the current Phase 3 checkpoint with two real
machines and two operating systems:

- one user-facing endpoint on the Ubuntu caller;
- explicit `declared-remote-only` selection;
- one static in-memory remote declaration;
- real LAN HTTP transport;
- real Home AI Cluster execution on the Windows receiver;
- real remote Ollama execution;
- normalized result return with authoritative selected-node attribution; and
- cold-model execution that exceeded the previous implicit client timeout.

The demonstrated path performs no retry and no fallback.

## Proven flow

```text
Ubuntu caller
  -> explicit static proof process
  -> 127.0.0.1:8000/v1/chat
  -> declared-remote-only selection
  -> declared-remote
  -> LAN HTTP
  -> Windows /internal/cluster/request
  -> local selected execution on Windows
  -> Ollama adapter
  -> llama3.2
  -> normalized ClusterResult
  -> caller-owned attribution as declared-remote
  -> user response
```

The receiver was a Windows 11 Pro Dell OptiPlex at `192.168.0.55`. The caller
was an Ubuntu portable. The remote adapter was Ollama, configured as
`llama3.2`; observed installed `llama3.2:latest` and `llama3.2:1b` variants
referred to the same 1.2B Q8_0 model data.

The cold-model rerun completed in approximately ten seconds with `HTTP 200`.
The model answer did not exactly follow the requested wording, which is outside
the scope of this architectural proof.

## Result attribution boundary

`RuntimeResult` is the runtime-produced data returned by an adapter. A
successful `ClusterResult` is created at selected execution and includes the
required `node_id`.

Local execution attributes that result from the selected local node id.
Declared remote execution attributes it from the caller-owned remote
declaration id. Transport addresses, IP addresses, and remote-reported ids are
not authoritative node identities. In the demonstrated proof, the returned
node id is `declared-remote`.

This describes the implemented RFC-0023 boundary; it does not define a broader
long-term result model.

## Cold-model timeout correction

The initial cold-model incident returned `503 Service Unavailable` from the
Windows internal endpoint despite otherwise working local Ollama requests. The
cause was the HTTPX default timeout in the asynchronous client owned by
`OllamaAdapter.chat()`.

PR #138 removed that implicit inference timeout by setting `timeout=None` on
that client only. The synchronous `/api/version` health client is unchanged.
This change added no retry, fallback, timeout configuration, global HTTP
policy, routing, orchestration, transport ownership, or attribution behavior.

This correction is distinct from the earlier proof-process transport timeout
correction: the two clients are separate timeout boundaries.

## Current defaults

The ordinary application remains local-only by default. Remote behavior
requires the explicit static proof entrypoint, an explicitly supplied declared
remote address, and `declared-remote-only` selection. No remote activation was
added to the ordinary application.

## Current limitations

The demonstrated Phase 3 checkpoint does not provide:

- authentication between nodes;
- application-level encryption;
- verified remote identity;
- discovery or registration;
- persistent configuration;
- health probing;
- multiple declared remote nodes in active proof use;
- automatic capability-based routing policy;
- retry or fallback;
- complete observability; or
- production readiness.

The proof remains static, explicit, and limited to two manually prepared
machines on one trusted LAN. It is not a complete distributed system.

## Phase status

The implementation and proof criteria for the current Phase 3 checkpoint have
been demonstrated.

Whether Phase 3 should now be declared complete is a separate explicit project
decision. No Phase 4 implementation should begin until that decision is
recorded.

## Accepted RFC references

- [RFC-0003: Runtime Adapter Interface](../RFC/RFC-0003-runtime-adapter-interface.md)
- [RFC-0014: Minimal Concrete Transport Protocol](../RFC/RFC-0014-minimal-concrete-transport-protocol.md)
- [RFC-0017: Explicit Routing Candidate Selection](../RFC/RFC-0017-routing-candidate-selection.md)
- [RFC-0018: Explicit Selected Candidate Orchestration](../RFC/RFC-0018-selected-candidate-orchestration.md)
- [RFC-0019: Phase 2 Closeout and Phase 3 Entry](../RFC/RFC-0019-phase-2-closeout-and-phase-3-entry.md)
- [RFC-0020: Minimal Static Two-Machine Proof](../RFC/RFC-0020-minimal-static-two-machine-proof.md)
- [RFC-0021: Explicit Static In-Memory Wiring](../RFC/RFC-0021-explicit-static-remote-proof-wiring.md)
- [RFC-0022: Explicit Static Proof Entrypoint](../RFC/RFC-0022-explicit-static-proof-process-entrypoint.md)
- [RFC-0023: Result Node Attribution](../RFC/RFC-0023-result-node-attribution.md)
