---
order: 99
---

# Retained HAC Execution-Limit Validation

Status: Evidence record

Date: 2026-09-05

This document records a factual real-machine operator validation of the
post-1.0 Draft execution-availability rail. It exercises Draft RFC-0098 through
RFC-0106 and the implemented retained local HAC execution-limit behavior from
PR #665, documented for operators in PR #666. It is not released 1.0 behavior,
and it introduces no product or architectural change.

## Test topology

The caller/orchestrator was `sat`, running the
`impl-retained-local-hac-execution-limit` implementation with an isolated
`XDG_CONFIG_HOME=/tmp/hac-limit-proof-caller` retained configuration. Its
Ollama model was `qwen2.5-coder:7b`; its retained caller-local capability was
`chat`; and its HAC execution limit was not retained, so its effective local
limit was `1`. The tested `summarize` capability was intentionally not eligible
locally.

The caller ran ordinary `hac static-cluster`. Ordinary loopback `hac summarize`
requests were routed through this caller process to the retained remote nodes,
in this static order:

| Node | Base URL | Capability | Runtime | Model | Retained HAC execution limit |
| --- | --- | --- | --- | --- | --- |
| `debian-1` | `http://192.168.1.9:25043` | `summarize` | Ollama | `llama3.2:1b` | `2` |
| `debian-2` | `http://192.168.1.9:25044` | `summarize` | Ollama | `llama3.2:1b` | `1` |

`debian-1` and `debian-2` were respectively the `hac-debian-1` and
`hac-debian-2` machines/containers. Each used the isolated
`XDG_CONFIG_HOME=/tmp/hac-limit-proof` retained configuration and ordinary
`hac local` startup. Each receiver configured its own local value with
`hac config local`; `hac config show` reported `HAC execution limit: 2` on
receiver A and `HAC execution limit: 1` on receiver B. The already-established
Incus host proxy ports exposed the receivers to the caller.

The caller's remote declarations contained only node identity, base URL, and
capability. They contained no receiver execution limits. The caller did not
pre-query receiver limits, current interval counts, remaining allowance, or
runtime load.

## Successful validation

The bounded request text was:

```text
Home AI Cluster is local-first and routes AI requests by capability. Summarize this in one short sentence.
```

Three ordinary requests were started approximately 0.1 seconds apart and were
intentionally allowed to overlap:

```sh
hac summarize \
  --text "$TEXT" \
  --timeout-seconds 180 \
  --json
```

All three completed with exit code `0`. Their returned attribution and content
were:

| Request | `node_id` | Result |
| --- | --- | --- |
| 1 | `debian-1` | The Home AI Cluster is designed to route AI requests by capability, suggesting a local-first approach. |
| 2 | `debian-1` | The Home AI Cluster routes AI requests by capability, making it a local-first solution. |
| 3 | `debian-2` | The Home AI Cluster routes AI requests by capability, making it a local-first platform. |

All results reported `adapter: "ollama"` and `model: "llama3.2:1b"`. The
observed routing was:

```text
request 1 -> debian-1
request 2 -> debian-1
request 3 -> debian-2
```

Receiver A locally enforced its own HAC execution limit. The caller still
attempted remote candidates in deterministic static order: `debian-1` before
`debian-2`. When receiver A could not accept another HAC-owned execution
interval, ordinary caller handling could continue safely to the next statically
eligible receiver; receiver B then completed the later request.

## Preliminary diagnostic observation

A preliminary attempt used a much larger repeated input and a 120-second
timeout. All three caller requests timed out, so that attempt is not the
successful proof and no cause is asserted. While two executions occupied
receiver A, its HAC receiver log recorded:

```text
POST /internal/cluster/request HTTP/1.1" 409 Conflict
```

This is retained only as concise diagnostic evidence of receiver-side
pre-adapter HAC execution-permission enforcement.

## Conclusions

This real-machine validation establishes that retained local HAC execution
limits are consumed by ordinary receiver startup; receiver A with retained
limit `2` can engage two overlapping HAC-owned execution intervals; and
receiver B with retained limit `1` successfully executed the later request.
It also establishes deterministic candidate order, safe next-candidate
continuation after receiver A's pre-execution refusal, and truthful successful
attribution of `debian-1`, `debian-1`, then `debian-2`.

These observations passed through real retained configuration, ordinary
`hac static-cluster`, receiver HTTP transport, Ollama adapters, and distinct
machines/containers.

## What this validation does not establish

This validation does not establish runtime capacity, runtime parallelism, GPU
capacity, available runtime slots, least-loaded routing, round robin, fairness,
scheduler behavior, queues, polling, heartbeats, remote load advertisement,
distributed execution state, dynamic discovery, dynamic membership,
multi-process coordination, per-capability execution limits, predictive
completion, or speculative retries.

An HAC-owned execution interval ending does not prove that an underlying runtime
stopped processing work.
