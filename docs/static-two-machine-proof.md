# Static Two-Machine Proof Runbook

This runbook executes the RFC-0022 LAN-only proof:

```text
One endpoint. Two machines. One routed request.
```

It is intentionally narrow. Both machines must be on the same trusted local
network. Do not use Tailscale, another VPN, an overlay network, or an untrusted
network for this proof.

## Roles

Use two machines:

- **receiving machine**: runs the ordinary local application and Ollama;
- **calling machine**: runs the explicit static proof process and receives the
  user's `/v1/chat` request.

The calling machine sends the normalized cluster request to the receiving
machine through `/internal/cluster/request`.

## Prerequisites

On both machines:

- use the same current repository revision;
- install Python 3.13 and `uv`;
- run `uv sync` from the repository root.

On the receiving machine only:

- install and start Ollama;
- ensure the adapter's current default model, `llama3.2`, is available.

Find the receiving machine's LAN address. The examples below use
`192.168.1.20`. Replace it with the actual address.

## 1. Start the receiving machine

From the repository root on the receiving machine:

```sh
uv run uvicorn home_ai_cluster.main:app --host 0.0.0.0 --port 8000
```

This starts the ordinary application. Its `/internal/cluster/request` endpoint
executes locally and does not re-enter remote routing.

From the calling machine, verify that the receiving process is reachable:

```sh
curl -s http://192.168.1.20:8000/health
```

If a host firewall is enabled, allow TCP port `8000` only from the trusted LAN
for the duration of the proof.

## 2. Start the calling machine

From the repository root on the calling machine:

```sh
uv run home-ai-cluster-static-proof http://192.168.1.20:8000
```

The proof process binds only to:

```text
127.0.0.1:8000
```

It constructs exactly one manual remote declaration with node id
`declared-remote` and uses `declared-remote-only` selection.

## 3. Send one request

On the calling machine, in another terminal:

```sh
curl -s http://127.0.0.1:8000/v1/chat \
  -H 'content-type: application/json' \
  -d '{
    "messages": [{"role": "user", "content": "Reply with exactly: remote proof works"}],
    "capability": "chat"
  }'
```

A successful response demonstrates this path:

```text
caller -> 127.0.0.1:8000/v1/chat
       -> declared-remote-only selection
       -> http://192.168.1.20:8000/internal/cluster/request
       -> Ollama adapter on the receiving machine
       -> normalized result returned to the caller
```

There is no retry and no local fallback. If the receiving machine, Ollama, the
model, or the LAN path is unavailable, the request must fail visibly.

## 4. Stop the proof

Stop both processes with `Ctrl-C`.

The calling process owns its HTTP client and closes it during application
shutdown.

## Troubleshooting

### The receiving machine is unreachable

Confirm the LAN address, that both machines are on the same LAN, and that TCP
port `8000` is not blocked by a host firewall.

### The request returns a runtime unavailable error

On the receiving machine, confirm that Ollama is running and that `llama3.2` is
available.

### The calling command rejects the address

The remote address must be an absolute HTTP URL, for example:

```text
http://192.168.1.20:8000
```

### Port 8000 is already in use

Stop the conflicting process. RFC-0022 fixes the proof process at
`127.0.0.1:8000`; this runbook does not introduce configurable proof host or
port values.

## What this proof does not establish

This proof does not establish production security, authentication, encryption,
dynamic discovery, registration, health-aware routing, retries, fallback,
multiple remote nodes, cross-site execution, or deployment readiness.

It proves only the accepted static architecture across two real machines on one
trusted LAN.
