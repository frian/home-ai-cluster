# Phase 6 OpenAI-Compatible Access Proof

Date: 2026-07-15

RFC: [RFC-0031: Minimal OpenAI-Compatible Chat Access](../RFC/RFC-0031-minimal-openai-compatible-chat-access.md)

## Purpose

This document records the opt-in local execution proof required by RFC-0031
for the minimal OpenAI-compatible chat-completions edge.

It records observed proof results only. It does not define new architecture,
broaden the compatibility contract, or make the proof environment part of the
project's supported configuration.

## Proof base

The proof ran from `main` commit `65a41e0`, which includes the RFC-0031
implementation commit `6c06d39`.

The repository working tree was clean before and after the proof.

## Environment observed

The local proof environment provided:

- `uv` 0.5.9;
- Ollama 0.30.8;
- the already installed `llama3.2:latest` model;
- the official OpenAI Python SDK 2.45.0, installed only in a temporary
  `uv run --with openai` environment.

These versions are observations from this proof, not project requirements.

No dependency or lockfile change was retained.

## Loopback boundary

The compatibility process was started through:

```text
uv run home-ai-cluster-openai-compatibility
```

Socket inspection confirmed that the process listened on:

```text
127.0.0.1:8001
```

No non-loopback listener for port 8001 was present.

The compatibility process was stopped after the proof, and port 8001 was no
longer listening.

Ollama was already running before the proof and was left running afterward.

## Raw HTTP proof

A raw HTTP client sent one valid non-streaming request without an
`Authorization` header to:

```text
POST http://127.0.0.1:8001/v1/chat/completions
```

The request succeeded with HTTP status 200.

The response confirmed:

* `object` was `chat.completion`;
* `model` was a non-empty string;
* exactly one choice was returned;
* the choice index was `0`;
* the message role was `assistant`;
* message content was non-empty;
* `finish_reason` was JSON `null`;
* `usage` was absent;
* adapter, node, routing, and topology fields were absent.

The runtime-generated message content was not retained in the repository.

## Official OpenAI Python SDK proof

The official OpenAI Python SDK was invoked through a temporary environment:

```text
uv run --with openai
```

The client used:

* the loopback base URL `http://127.0.0.1:8001/v1`;
* the endpoint identifier `home-ai-cluster`;
* a placeholder bearer value required by the client.

The request succeeded and the SDK parsed the response successfully.

The parsed result confirmed:

* `object == "chat.completion"`;
* a non-empty model string;
* exactly one choice;
* choice index `0`;
* assistant message role;
* non-empty message content;
* `finish_reason is None`.

The raw HTTP response omitted `usage`. Any absent optional field represented as
`None` by the client object is client-side parsing behavior and does not change
the wire contract.

The placeholder bearer value was not printed, persisted, forwarded, or retained
in the repository.

## Negative checks

The proof also confirmed that:

* `stream: true` was rejected with the RFC-0031 compatibility error envelope
  and did not begin streaming;
* an unsupported endpoint model identifier was rejected with the RFC-0031
  compatibility error envelope.

## Privacy and cleanup

The proof retained no prompt, runtime response, authorization value, or
runtime-specific payload in the repository.

No repository source file, test, dependency declaration, or lockfile changed
during execution.

A temporary untracked `uv.lock` created by the temporary SDK command was removed
during cleanup.

The final working tree was clean.

## Result

The RFC-0031 real compatibility proof passed.

The proof demonstrated:

1. a raw loopback HTTP request without authorization;
2. an official OpenAI Python SDK request with placeholder bearer syntax;
3. successful SDK parsing of `finish_reason: null`;
4. use of the existing cluster-owned execution path with an already supported
   local runtime;
5. explicit rejection of streaming and unsupported model identifiers;
6. preservation of the loopback, privacy, and repository-cleanliness
   boundaries.

This completes the first implementation proof described by RFC-0031 without
broadening its accepted scope.
