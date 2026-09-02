# Phase 16 Closeout

Status: Complete

Date: 2026-07-18

## Purpose

This document records completion of Phase 16:

> One operator can send one ordinary capability-centered request without
> manually constructing HTTP transport details.

The completed result is deliberately bounded to one installed, one-shot native
request command.

## Phase outcome

The final operator surface is:

```sh
uv run home-ai-cluster-chat --message "<MESSAGE>"
```

The command sends one request to an already running ordinary cluster process
through the fixed native `POST http://127.0.0.1:8000/v1/chat` boundary. It
constructs exactly one `user` message and the fixed `chat` capability, validates
the complete normalized `ClusterResult`, emits one compact JSON object on
success or one stable safe standard-error line on failure, then exits after one
request.

It is a client of the ordinary process, not another orchestrator.

## Architectural result

The ordinary running process remains authoritative. Local-only and explicit
static-cluster processes share the same client surface, while routing, fallback,
topology, runtime selection, and attribution remain process-owned. The client
does not inspect declarations or address nodes or runtimes.

The client consumes only the native request and normalized result contracts,
preserving engine independence, local-first operation, and the established
privacy boundary. The solution is intentionally boring and small: topology is
hidden from the client, while the process boundary and cluster-owned attribution
remain real. It is fake in distribution, but not fake in architecture.

## Completed sequence

### Investigation

[The Phase 16 investigation](phase-16-ordinary-operator-request-access-investigation.md)
established that operators otherwise had to reconstruct HTTP details manually;
that the existing explanation command was not a client of the running process;
that the existing `/v1/chat` boundary was sufficient; that a thin installed
Python command using existing `httpx` was the smallest fit; and that an RFC was
required before implementation.

### Accepted decision

[RFC-0045](../RFC/RFC-0045-one-shot-ordinary-request-command.md) accepted
`home-ai-cluster-chat` with required `--message`, the fixed loopback endpoint,
the fixed `chat` capability, exactly one request, a complete validated
`ClusterResult`, fixed safe error mapping, a finite fixed timeout, and no
retries. It adds no session, history, configuration, selectors, or lifecycle
behavior.

### Implementation

[The implementation](../src/home_ai_cluster/commands/chat_command.py) and its focused
tests in `tests/test_chat_command.py` added one installed console entry. It
reuses `httpx` and the authoritative `ClusterRequest` and `ClusterResult`, sends
exactly one HTTP request, validates successful response data, preserves the
stable standard-output, standard-error, and exit behavior, and includes focused
privacy regression coverage. It added no dependency, endpoint, protocol,
configuration, or abstraction layer.

The merged implementation validation recorded:

```text
18 focused tests passed
622 full tests passed
ruff check passed
changed-file format check passed
help invocation passed
git diff --check passed
```

At implementation review time, the repository-wide formatter still reported 17
unrelated pre-existing files. Phase 16 did not introduce or fix those files.

### Proof runbook

[The Phase 16 proof runbook](phase-16-ordinary-request-access-proof-runbook.md)
separated the reviewed procedure from later real evidence. It required four
observations: unavailable ordinary process, local-only success, normalized
runtime-unavailable failure, and explicit static-cluster success.

### Retained proof

[The retained Phase 16 proof](phase-16-ordinary-request-access-proof.md) ran at
revision:

```text
4917b3bc748822cdea1050392c898bf8e6193567
```

It observed:

- unavailable ordinary process: empty standard output,
  `error: ordinary cluster unavailable`, and exit `1`;
- local-only success: exit `0`, empty standard error, a complete normalized
  result, and `local` attribution;
- runtime unavailable: empty standard output,
  `error: runtime adapter unavailable`, and exit `1`;
- explicit static-cluster success: exit `0`, empty standard error, a complete
  normalized result, `local` attribution, and no client selector or declaration
  input.

The proof used one physical machine and the Ollama runtime family. Static-cluster
routing selected the local candidate; no remote execution or real network
transport was demonstrated. It retained no prompt, generated content, topology,
model identifier, runtime URL, log, trace, or exception.

## Final command contract

### Success

```sh
uv run home-ai-cluster-chat --message "<MESSAGE>"
```

It produces one compact normalized result equivalent to:

```json
{"content":"...","adapter":"...","model":"...","node_id":"..."}
```

This is illustrative shape only, not retained proof content.

### Failures

| Condition | stderr | Exit |
| --- | --- | --- |
| Invalid local input | `error: invalid request input` | 2 |
| Connection failure or timeout | `error: ordinary cluster unavailable` | 1 |
| HTTP 422 | `error: cluster rejected request` | 1 |
| HTTP 404 | `error: no available chat capability` | 1 |
| HTTP 503 | `error: runtime adapter unavailable` | 1 |
| Other HTTP or client failure | `error: ordinary request failed` | 1 |
| Invalid success response | `error: invalid cluster response` | 1 |

Failures keep standard output empty and do not emit raw private details.

## Privacy boundary

Home AI Cluster does not retain the submitted message or generated result. No
history or persistence is added, and the command does not log prompt or
generated content. Command-line arguments may still be visible to the shell or
operating system, so the command is not secure secret input. Successful standard
output may be retained by external redirection or terminal tooling outside
project control.

## What Phase 16 does not establish

Phase 16 does not establish interactive chat, sessions, multiple messages,
system messages or arbitrary roles, standard input or prompt files, streaming,
generation controls, tools, multimodal input, embeddings, configurable host or
port, remote administration, node/runtime/adapter/model selection, discovery,
client-side routing, retry, fallback, client process startup or supervision,
authentication or TLS management, a generic client SDK, a generic HTTP
abstraction, a dashboard, database, Docker, Kubernetes, or proof of remote
execution.

## Phase completion statement

Phase 16 is complete because the access need was investigated, RFC-0045 was
accepted, the implementation was merged, focused and full automated tests
passed, the proof runbook was merged, and one real privacy-safe proof was
retained. Both local-only and explicit static-cluster ordinary processes were
reached through the same one-shot client, and stable unavailable-process and
runtime-unavailable failures were observed.

## Follow-up

- Merge this closeout record.
- Then update `ROADMAP.md`, `README.md`, and the public documentation index in a
  separate small pull request.
- Any new client capability requires a new demonstrated need and, where
  architectural, an RFC.
