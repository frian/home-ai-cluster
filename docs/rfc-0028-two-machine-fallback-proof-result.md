# RFC-0028 Two-Machine Fallback Proof Result

Status: Completed

Date: 2026-07-13

This document records an observed proof result. It is descriptive only;
accepted RFCs remain the source of architectural decisions.

## Proof statement

```text
One endpoint. Two machines. One pre-execution candidate fallback.
```

This is the dedicated RFC-0028 proof-only process. It does not activate
fallback for ordinary application traffic.

## Actual topology

### Calling machine

- Linux;
- `uv run home-ai-cluster-fallback-proof http://192.168.0.55:8000`;
- proof-only application bound to `127.0.0.1:8000`.

### Declared-remote machine

- Windows;
- ordinary application on the local network, started with:

  ```sh
  uv run uvicorn home_ai_cluster.main:app --host 0.0.0.0 --port 8000
  ```

- Ollama running with `llama3.2`.

The two machines communicated over the local network. No dynamic network
discovery, registration service, VPN, overlay network, or general
configuration surface was used.

## Remote readiness check

Before the fallback proof, Linux successfully sent a direct request to the
Windows internal execution endpoint:

```text
POST http://192.168.0.55:8000/internal/cluster/request
```

Its normalized result identified receiver-local execution as:

```json
{
  "adapter": "ollama",
  "model": "llama3.2",
  "node_id": "local"
}
```

This was a remote readiness and connectivity check only. It was not the
fallback proof.

## Executed fallback path

The dedicated process intentionally configured its local Ollama endpoint as
`http://127.0.0.1:1`. The proof request was sent to
`POST http://127.0.0.1:8000/v1/chat` with a non-sensitive request for the
fixed phrase `fallback proof succeeded`.

```text
proof-only /v1/chat with local_only=false
  -> one local and one declared-remote exact Capability("chat") candidate
  -> RFC-0025 fixed local precedence selects local
  -> local runtime endpoint connection cannot be established before request transmission
  -> adapter reports RuntimeConnectionUnavailableBeforeRequestError
  -> already discovered declared-remote candidate executes
  -> HTTP transport across the local network
  -> Windows /internal/cluster/request
  -> Windows Ollama llama3.2
  -> normalized result with node_id=declared-remote
```

The calling machine returned `HTTP/1.1 200 OK` with:

```json
{
  "content": "Fallback proof succeeded.",
  "adapter": "ollama",
  "model": "llama3.2",
  "node_id": "declared-remote"
}
```

## What this proves

The real two-machine run directly observed a successful `HTTP/1.1 200 OK`,
Windows Ollama execution with `llama3.2`, and final caller-owned
`node_id="declared-remote"` attribution through the dedicated proof-only
endpoint.

The implemented adapter and orchestration boundaries, together with focused
automated tests, establish the narrower execution facts: the deliberately
unavailable local runtime endpoint is classified as candidate/runtime endpoint
connection unavailability before request transmission; discovery and automatic
selection occur once; local and declared-remote execution are each attempted
once; and no retry, rediscovery, reselection, concurrent execution, or third
execution occurs. The declared-remote candidate used for that one fallback is
the candidate retained from the original discovery.

Ordinary `/v1/chat` remains unchanged and local-only outside this explicit
proof process.

## What this does not prove

This result does not establish general node availability, machine health
detection, arbitrary failure recovery, timeout fallback, HTTP error fallback,
retry behavior, high availability, fault tolerance, general resilience, or
automatic failover for ordinary application traffic. It does not establish that
the local node was down; it demonstrates only the RFC-0028 candidate/runtime
endpoint connection condition before request transmission.

## Relevant references

- [RFC-0025](../RFC/RFC-0025-minimal-capability-based-candidate-selection.md)
- [RFC-0028](../RFC/RFC-0028-minimal-pre-execution-candidate-fallback.md)
- [Phase 4 Current State](phase-4-current-state.md)
- [Phase 4 Completion Assessment](phase-4-completion-assessment.md)
