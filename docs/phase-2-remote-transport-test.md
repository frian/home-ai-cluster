# Phase 2 Remote Transport Test Checkpoint

Status: Draft

This document describes the current remote transport test checkpoint after the
in-process endpoint proof.

It is descriptive, not a new architectural decision. Accepted RFCs remain the
source of architectural decisions.

## Current state

`POST /internal/cluster/request` exists as the RFC-0014 internal endpoint shape.

`HttpRemoteTransport` exists as the concrete RFC-0014 HTTP transport
implementation.

The current test suite now proves that `HttpRemoteTransport` can call the
internal endpoint in-process through `httpx.ASGITransport`.

That proof verifies that the transport:

- uses the declared `RemoteNodeDeclaration.transport_address`;
- posts to `POST /internal/cluster/request`;
- exercises the FastAPI app without real network I/O;
- returns a normalized `ClusterResult`.

## What this does not change

This checkpoint does not activate remote execution.

The active `/v1/chat` path remains local-only.

`orchestrate_request_with_declared_remote()` remains an explicit opt-in helper
and is not wired into API routes.

The test does not introduce:

- remote nodes;
- real network calls;
- discovery;
- registration;
- config loading;
- retries;
- fallback;
- daemon lifecycle;
- streaming;
- public node API;
- OpenAI-compatible API.

## Meaning

The project has now proven the local protocol shape end-to-end inside one
process:

```text
HttpRemoteTransport
  -> POST /internal/cluster/request
  -> local-only orchestrator path
  -> normalized ClusterResult
```

This remains fake in distribution, but not fake in architecture.
