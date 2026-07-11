# First Two-Machine Proof Result

Status: Completed

Date: 2026-07-11

This document records the first successful execution of the accepted RFC-0022
static two-machine proof.

It is descriptive. It does not introduce a new architectural decision.
Accepted RFCs remain the source of architectural decisions.

## Proof statement

The following target was demonstrated on two real machines:

```text
One endpoint. Two machines. One routed request.
```

A user request sent to the calling machine's local `/v1/chat` endpoint was
selected as `declared-remote-only`, transported over the trusted local network,
executed by the receiving machine's local Ollama adapter, and returned as a
normalized cluster result.

## Actual topology

### Calling machine

- Ubuntu Linux;
- Home AI Cluster explicit static proof process;
- proof endpoint bound to `127.0.0.1:8000`;
- manually declared receiving address `http://192.168.0.55:8000`;
- fixed remote node id `declared-remote`;
- selection mode `declared-remote-only`.

### Receiving machine

- Dell OptiPlex;
- Windows 11 Pro;
- 8 GB RAM;
- Home AI Cluster ordinary local application;
- application bound to `0.0.0.0:8000` for the trusted LAN proof;
- Ollama running natively on Windows;
- `llama3.2:1b` installed and exposed locally under the adapter's expected
  `llama3.2` name.

No virtual machine, container, VPN, overlay network, discovery mechanism, or
registration mechanism was used.

## Executed path

```text
user curl
  -> calling machine 127.0.0.1:8000/v1/chat
  -> explicit declared-remote-only selection
  -> HTTP transport over the trusted LAN
  -> receiving machine /internal/cluster/request
  -> receiving machine local Ollama adapter
  -> llama3.2
  -> normalized ClusterResult
  -> calling machine response
```

## Successful request

The final request was sent on the calling machine:

```sh
time curl -i http://127.0.0.1:8000/v1/chat \
  -H 'content-type: application/json' \
  -d '{
    "messages": [
      {
        "role": "user",
        "content": "Reply with exactly: remote proof works"
      }
    ],
    "capability": "chat"
  }'
```

The proof process returned HTTP `200 OK` with a normalized result containing:

```json
{
  "content": "...",
  "adapter": "ollama",
  "model": "llama3.2"
}
```

The observed end-to-end command duration was approximately `4.821` seconds.
The model did not follow the exact requested wording, but model answer quality
was not part of this proof. The relevant result was successful remote routing,
execution, and normalized return.

## Independent checks performed

Before the final proof, the following boundaries were verified separately:

1. the receiving application was reachable from the calling machine;
2. `POST /v1/chat` on the receiving machine returned HTTP `200`;
3. `POST /internal/cluster/request` on the receiving machine returned HTTP
   `200`;
4. Ollama's HTTP API worked locally on Windows;
5. the receiving Home AI Cluster application could call Ollama locally;
6. a direct `httpx.AsyncClient` request from Ubuntu to the receiving internal
   endpoint returned HTTP `200`.

These checks isolated the proof-process timeout from networking, Windows,
Ollama, model naming, and internal endpoint behavior.

## Issue discovered during the proof

The first proof attempts failed after approximately five seconds with
`httpx.ReadTimeout`.

The explicit proof process originally used HTTPX's default request timeout. A
slow model response could therefore complete successfully on the receiving
machine but exceed the calling process's read timeout.

The proof-owned HTTP client was changed to use no accidental model read timeout:

```python
httpx.AsyncClient(timeout=None)
```

This change applies only to the explicit static proof process. It does not add
retry, fallback, discovery, configuration, or new routing behavior. The default
local-only application remains unchanged.

The runbook's nonexistent `/health` check was also replaced with a request to a
real application endpoint.

## What this proves

This result proves that the accepted static architecture can operate across two
real machines and two operating systems while preserving:

- one user-facing endpoint on the calling machine;
- explicit caller-owned remote wiring;
- deterministic declared-remote-only selection;
- normalized cluster requests and results;
- a real HTTP transport boundary;
- execution through the receiving machine's local runtime adapter;
- visible failure without retry or fallback;
- unchanged default local-only behavior outside the proof process.

It also demonstrates the intended Phase 3 principle:

```text
fake in distribution, but not fake in architecture
```

The distribution setup is deliberately static and manual. The architectural
boundaries used by the proof are real.

## What this does not prove

This result does not establish:

- production security or authentication;
- encryption;
- dynamic discovery or registration;
- persistent configuration;
- multiple remote nodes;
- health-aware routing;
- retries or fallback;
- scheduling or load balancing;
- streaming;
- daemon lifecycle management;
- deployment readiness;
- cross-site or untrusted-network operation;
- model quality or performance suitability.

## Reproduction

Use the operator runbook:

- [Static Two-Machine Proof Runbook](static-two-machine-proof.md)

The proof must remain limited to two manually prepared machines on the same
trusted local network.

## Result attribution and cold-model rerun

Date: 2026-07-11

This section extends the original proof record. It describes later implemented
behavior and an observed rerun; it does not introduce a new architectural
decision.

### Result attribution

PR #137 implemented accepted RFC-0023 result node attribution. Successful
`ClusterResult` values now require `node_id`. Runtime adapters return
runtime-owned result data without cluster node identity; the selected-candidate
execution boundary creates the successful cluster result and attributes it to
the selected cluster-facing node.

For declared remote execution, the caller-owned declaration is authoritative.
The remote response identity, transport URL, and IP address are not
authoritative node identities. The proof declaration therefore reports:

```json
{
  "node_id": "declared-remote"
}
```

### Cold-model timeout incident

After result attribution was implemented, a cold Ollama model on the Windows
receiver caused the internal endpoint to return `503 Service Unavailable`.
The direct local Windows endpoint and Ollama API were otherwise functional.
A cold Ollama request could legitimately take longer than approximately five
seconds; warming the model allowed the proof to succeed and identified an
implicit HTTPX default timeout in the client owned by `OllamaAdapter.chat()`.

This was separate from the earlier timeout incident recorded above. The earlier
change removed an accidental timeout from the proof-owned HTTP transport client
on the calling machine. The later issue was in the Ollama adapter's
asynchronous inference client on the receiving machine.

PR #138 changed only the adapter-owned chat client to use `timeout=None`.
The synchronous `/api/version` health client remained unchanged. The correction
added no retry, fallback, timeout configuration surface, global HTTP policy,
routing change, orchestration change, transport ownership change, or
attribution change. The full validation suite passed with 206 tests.

### Successful cold-model rerun

The static two-machine proof was rerun without warming the model first. The
Ubuntu portable caller used the explicit proof endpoint at
`127.0.0.1:8000/v1/chat`; the Windows 11 Pro Dell OptiPlex receiver at
`192.168.0.55` ran Ollama with the adapter configuration `llama3.2`.
Installed `llama3.2:latest` and `llama3.2:1b` variants were observed to refer
to the same 1.2B Q8_0 model data.

The cold request completed in approximately ten seconds and returned
`HTTP/1.1 200 OK`. Its normalized result included:

```json
{
  "adapter": "ollama",
  "model": "llama3.2",
  "node_id": "declared-remote"
}
```

The model did not follow the requested wording exactly. That answer-quality
detail does not affect the architectural proof: a slow cold local model
completed through the explicit static two-machine path without an accidental
client timeout.
