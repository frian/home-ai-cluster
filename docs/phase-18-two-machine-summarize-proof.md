# Phase 18 Two-Machine Summarize Proof

Status: Retained runbook

## Purpose

This runbook retains the bounded physical-machine observation for Phase 18's
second executable capability. It exercises remote `summarize` through the
already accepted pre-transmission fallback boundary. It is not direct node
targeting: the declaration does not choose a capability or force a request to a
remote node.

It is not a generic document workflow, discovery procedure, deployment guide,
or Phase 18 closeout.

## Topology

Use two physical machines on one trusted LAN.

Machine A is the caller. It runs ordinary static-cluster mode with its ordinary
local adapter, which advertises `summarize`. Before sending the proof request,
the external local runtime is stopped or otherwise unreachable so that its
local summarize attempt fails with the accepted pre-transmission
connection-unavailable condition.

Machine B is the declared receiver. It runs an ordinary local Home AI Cluster
process with an available external runtime and required model. Machine B is
reachable from Machine A and executes the received request locally; it does not
forward requests.

Machine A's static declaration is topology-only and operator-owned. It contains
only accepted node ID and base URL forms. It cannot add or remove `summarize`,
mark a receiver chat-only, configure remote capabilities, or otherwise select
how a request routes. Use the existing declaration format in
[static-cluster-declaration.md](static-cluster-declaration.md).

## Start the machines

On Machine B, ensure the external runtime and required model are already
available, then start the ordinary receiver:

```sh
uv run home-ai-cluster-local --host 0.0.0.0 --port 8000
```

This is an explicit trusted-LAN exposure. Restrict firewall access to the
trusted LAN and remove that allowance after use. Home AI Cluster does not own
the external runtime, and this process does not forward requests.

On Machine A, set the explicitly chosen declaration path and use the supported
static-cluster commands:

```sh
DECLARATION="<DECLARATION_PATH>"

uv run home-ai-cluster-preflight --declaration "$DECLARATION"
uv run home-ai-cluster-status --declaration "$DECLARATION"
uv run home-ai-cluster-static-cluster --declaration "$DECLARATION"
```

The declaration identifies Machine B with a cluster-owned ID such as
`phase-18-summarize-receiver` and its trusted-LAN base URL. Status can observe
that Machine B is reachable. Stop, or make unreachable, Machine A's external
local runtime before the next step; do not change the local node or declaration
to try to force the remote path.

## Proof request

With Machine A's static-cluster process running on its native loopback endpoint,
send one request:

```sh
curl -sS \
  -X POST \
  -H 'Content-Type: application/json' \
  --data '{"text":"Home AI Cluster routes requests by declared capabilities while preserving local-first behavior and caller-owned node attribution."}' \
  http://127.0.0.1:8000/v1/summarize
```

When Machine A's local runtime is unavailable before request execution and
Machine B is reachable, the normalized response contains one summary plus the
caller-declared remote node ID:

```json
{"content":"<summary>","adapter":"<adapter>","model":"<model-or-null>","node_id":"phase-18-summarize-receiver"}
```

Do not retain source text, generated summary text, raw internal envelopes,
private URLs, or verbose logs. The fixed source in this document is the sole
retained example input.

## Manual operator observations

- Machine B is reachable through the declaration-aware status command.
- Machine A's local runtime is intentionally unavailable before request
  execution.
- The public summarize request succeeds through the accepted fallback path and
  returns `content`, `adapter`, `model`, and Machine A's caller-declared remote
  `node_id`.
- After restoring Machine A's local runtime, the same request returns Machine
  A's local node ID. This demonstrates that a healthy local summarize path wins
  over the declared remote.
- If current request-history file inspection is used, confirm that summarize
  creates no request-history record containing the source or summary. Do not
  retain either value as proof material.

For a multiple-remote declaration, a bounded fallback observation is also
available: make the first declared receiver unreachable before transmission,
keep the second receiver available, and verify the second declared node ID is
returned. Declaration order is the existing bounded fallback order.

If both Machine A's local runtime and the declared receiver are stopped or
unreachable, the selected execution fails with the existing normalized runtime
or transport-unavailable result (HTTP 503). This is distinct from a 404: a
public `{"detail":"No adapter provides capability: summarize"}` response
applies only when no selectable candidate advertises `summarize`, which ordinary
topology declarations cannot configure.

## Automated retained guarantees

The retained tests, rather than unsupported operator manipulations, guarantee:

- exact tagged summarize envelope shape and rejection of the old untagged body;
- chat-only candidate exclusion and capability-only candidate discrimination in
  controlled tests;
- caller-side overwrite of a conflicting receiver node ID with the declared
  node ID;
- bounded fallback to the next declared receiver before transmission, and no
  fallback after a post-transmission failure;
- absence of source and summary from caller and receiver request history; and
- identical normalized `SummarizeRequest` semantics across Ollama and
  llama-server.

An optional engine-independence observation uses Ollama on one machine and
llama-server on the other. The normalized summarize request remains the same;
runtime mapping and model selection remain adapter-owned.

## Privacy and limits

This proof establishes one static trusted-LAN request path only. It does not
establish discovery, scheduling, retries beyond accepted pre-transmission
fallback, authentication, encryption, or production readiness.
