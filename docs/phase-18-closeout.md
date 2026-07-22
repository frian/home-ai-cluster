# Phase 18 Closeout

Status: Complete

Date: 2026-07-22

## Purpose

This document records completion of Phase 18:

> Prove that Home AI Cluster supports a second real executable capability,
> `summarize`, through local and declared-remote execution while preserving
> existing capability-based routing, attribution, privacy, and engine
> independence.

## Phase outcome

Home AI Cluster now has exactly two closed executable request semantics:

```text
chat
summarize
```

`summarize` is not a chat prompt convention. It has a dedicated
`SummarizeRequest`, exact `Capability(name="summarize")`, bounded source-text
validation, an explicit adapter operation, a native endpoint, strict tagged
internal transport, and local and declared-remote execution. This is not a
generic multi-capability framework.

Accepted [RFC-0051](../RFC/RFC-0051-bounded-text-summarization.md) is the
architectural authority.

## Completed sequence

- PR [#330](https://github.com/frian/home-ai-cluster/pull/330) — normalized
  request and validation.
- PR [#331](https://github.com/frian/home-ai-cluster/pull/331) — adapter
  protocol and Ollama/llama-server mappings.
- PR [#332](https://github.com/frian/home-ai-cluster/pull/332) — local
  orchestration and native endpoint.
- PR [#333](https://github.com/frian/home-ai-cluster/pull/333) — closed tagged
  internal chat/summarize transport.
- PR [#334](https://github.com/frian/home-ai-cluster/pull/334) — declared-remote
  summarize execution and fallback proof.
- PR [#335](https://github.com/frian/home-ai-cluster/pull/335) — retained
  automated privacy evidence and physical two-machine runbook.

## Final public contract

```text
POST /v1/summarize
```

Public callers send:

```json
{"text":"source text"}
```

The successful result remains the unchanged `ClusterResult` shape:

```json
{
  "content": "summary",
  "adapter": "adapter-name",
  "model": "model-name-or-null",
  "node_id": "cluster-owned-node-id"
}
```

Public callers cannot provide capability, constraints, prompt, model, style,
language, length, file metadata, or node selection. Surrounding whitespace is
preserved. Source text is limited to 65,536 UTF-8 bytes. Extra public fields
follow the existing ignored-extra-field policy. An empty generated summary is a
valid successful result.

## Exact failures

Invalid public summarize input returns:

```http
422
{"detail":"Invalid summarize request"}
```

No selectable summarize candidate returns:

```http
404
{"detail":"No adapter provides capability: summarize"}
```

Runtime or selected execution unavailability returns:

```http
503
{"detail":"Runtime adapter unavailable"}
```

An invalid internal request returns:

```http
422
{"detail":"Invalid internal cluster request"}
```

Validation details, source text, remote URLs, runtime-private errors, and
receiver-provided identity are not exposed.

## Internal transport

The internal request family is closed to exactly these tagged envelopes:

```json
{
  "kind": "chat",
  "request": { "...normalized chat request..." }
}
```

```json
{
  "kind": "summarize",
  "request": {
    "text": "source text",
    "constraints": {
      "local_only": false,
      "prefer_fast_response": false,
      "min_context_size": null
    }
  }
}
```

Exactly chat and summarize are accepted. The old untagged chat body is rejected.
There is no generic payload, version negotiation, or dual parser. The receiver
executes locally and does not forward.

## Routing, fallback, and attribution

Existing routing authority remains unchanged. Eligibility is capability-based;
local-first ordering remains; and chat-only candidates are ineligible for
summarize. Declarations remain topology-only. Runtime, adapter, model, URL, and
machine names are not routing selectors.

Fallback occurs only for the accepted pre-transmission connection-unavailable
condition. No fallback occurs after transmission or runtime execution failure.
No retry loop, balancing, scoring, or scheduling was added.

Local results use the selected local node ID. Remote results use the
caller-owned declared remote node ID; receiver-provided `node_id` is not trusted.
An IP address, hostname, transport URL, adapter name, or model name is never
node identity.

## Engine independence

Both Ollama and llama-server implement the same normalized `SummarizeRequest`
semantics through adapter-owned mappings. Normalized requests contain no
runtime, adapter, model, or engine-specific field. Phase 18 does not claim
automatic engine selection.

## Privacy boundary

Summarize currently creates no bounded request-history entry. Retained tests
prove no source or summary content is stored for successful local execution,
remote caller execution, internal receiver execution, invalid public requests,
or invalid internal envelopes. The adapter-owned prompt and raw internal
envelope are not retained. Chat request-history behavior is unchanged.

## Retained proof and proof deviation

See the [Phase 18 two-machine summarize proof](phase-18-two-machine-summarize-proof.md).

In the physical workflow, Machine A runs ordinary static-cluster mode and its
normal local adapter advertises summarize. Its external local runtime is
intentionally unavailable before request execution, so existing bounded fallback
selects Machine B. Machine B runs the ordinary local receiver on the trusted LAN,
executes locally without forwarding, and Machine A returns its caller-owned
declared remote node ID.

The accepted roadmap text described a retained two-machine proof with one
chat-only node and one summarize-capable node. Current ordinary operator
surfaces cannot configure the local node or a remote declaration as chat-only:
ordinary adapters advertise summarize and declarations are topology-only.
Capability discrimination and chat-only exclusion are therefore retained as
controlled automated tests. The physical proof truthfully exercises remote
summarize through the accepted pre-transmission fallback boundary. No production
or declaration behavior was changed merely to manufacture the originally
described topology.

This does not weaken the architectural proof: capability-only eligibility is
automated, real network transport is physically observed, caller-owned
attribution is retained, and both use the same accepted production paths.

## What Phase 18 does not establish

Phase 18 does not establish a generic capability framework, document ingestion,
files or standard input, PDF or OCR, RAG, embeddings, indexing, vector storage,
structured or configurable summaries, sessions, streaming, caller-supplied
prompts, a CLI summarize command, OpenAI-compatible summarize access, discovery,
scheduling, balancing, lifecycle management, authentication or encryption,
internet-safe operation, a database, dashboard, Docker, Kubernetes, or
production readiness.

## Phase completion statement

Phase 18 is complete because RFC-0051 was accepted; the dedicated normalized
request exists; both adapters implement it; local and declared-remote execution
are merged; capability discrimination and chat-only exclusion are tested; exact
public and internal validation are retained; strict internal transport is
merged; fallback and attribution remain existing and caller-owned; privacy
evidence is retained; a truthful two-machine runbook exists; and roadmap and
public documentation are synchronized.

> Prove that Home AI Cluster supports a second real executable capability,
> `summarize`, through local and declared-remote execution while preserving
> existing capability-based routing, attribution, privacy, and engine
> independence.

## Follow-up

- Merge this closeout PR.
- Do not infer or begin a next phase.
- Future capability, document, CLI, persistence, or architectural expansion
  requires investigation and, where architectural, an accepted RFC.
