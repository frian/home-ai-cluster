# Phase 18 Two-Machine Summarize Proof

Status: Retained runbook

## Purpose

This runbook retains the bounded operator proof for Phase 18's second executable
capability. It proves one native `summarize` request crosses one explicitly
declared trusted-LAN boundary because of capability eligibility, not a runtime,
model, URL, or machine selector.

It is not a generic document workflow, discovery procedure, deployment guide,
or Phase 18 closeout.

## Topology

Use two physical machines on one trusted LAN.

Machine A is the caller. Start one ordinary static-cluster process with a
declaration that contains Machine B with a cluster-owned ID such as
`phase-18-summarize-receiver`. Machine A's local candidate must be chat-only
or otherwise lack `summarize`.

Machine B is the receiver. Start one ordinary local Home AI Cluster process
with an adapter that advertises `summarize`. It receives the internal request,
executes locally, and does not forward it.

The declaration remains topology-only and explicitly operator-owned. Use the
existing declaration format and commands documented in
[static-cluster-declaration.md](static-cluster-declaration.md).

## Preconditions

On Machine A, validate the explicit declaration and optionally inspect status:

```sh
uv run home-ai-cluster-preflight --declaration <DECLARATION_PATH>
uv run home-ai-cluster-status --declaration <DECLARATION_PATH>
uv run home-ai-cluster-static-cluster --declaration <DECLARATION_PATH>
```

On Machine B, start the existing ordinary receiver using the supported local
runtime composition. Do not add a special summarize command or a new receiver
mode. Confirm its normal local runtime status before sending the request.

## Proof request

With Machine A's static-cluster process running on its native loopback endpoint,
send exactly one request:

```sh
curl -sS \
  -X POST \
  -H 'Content-Type: application/json' \
  --data '{"text":"Home AI Cluster routes requests by declared capabilities while preserving local-first behavior and caller-owned node attribution."}' \
  http://127.0.0.1:8000/v1/summarize
```

The successful response has the existing normalized shape:

```json
{"content":"<summary>","adapter":"<adapter>","model":"<model-or-null>","node_id":"phase-18-summarize-receiver"}
```

Verify all of the following:

- `content` is one summary and `adapter` and `model` are truthful runtime
  results;
- `node_id` equals Machine A's declared ID, not Machine B's host, URL, IP, or
  receiver-provided identity;
- Machine A's chat-only candidate was not selected;
- exactly one tagged internal body with `kind: "summarize"` reached Machine B;
- the body contains only `text` and `constraints` inside `request`, never chat
  messages or a caller-controlled capability;
- no old untagged internal request body was accepted; and
- request history contains neither the source nor generated summary.

An optional stronger engine-independence observation uses Ollama on one machine
and llama-server on the other. The normalized request remains the same; runtime
mapping and model selection remain adapter-owned.

## Bounded negative checks

1. Remove `summarize` from Machine B's declared capabilities. The public result
   is exactly `404 {"detail":"No adapter provides capability: summarize"}` and
   Machine B is not contacted.
2. Declare Machine B as chat-only. It remains ineligible for summarize.
3. Make Machine B return a different node ID. Machine A still returns its
   declared `phase-18-summarize-receiver` ID.
4. Stop the first eligible receiver before request transmission while a second
   eligible declared receiver exists. The existing bounded fallback may try the
   next eligible declaration once.
5. Make the first receiver return an HTTP failure after transmission. The
   request fails without trying another receiver.

## Privacy and limits

Retain only privacy-safe structural observations. Do not retain source text,
summary text, raw envelopes, private URLs, addresses, credentials, or logs.
This proof establishes one static trusted-LAN request path only; it does not
establish discovery, scheduling, retries beyond accepted pre-transmission
fallback, authentication, encryption, or production readiness.

## Automated evidence

The repository's focused Slice 1–5 tests cover the normalized model, both
adapter mappings, native local execution, strict tagged transport, remote
selection, fallback, caller-owned attribution, and absence of summarize content
from request history. This runbook records the complementary physical-machine
operator observation.
