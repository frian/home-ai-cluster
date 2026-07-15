# Phase 6 Aider Access Proof

Date: 2026-07-15

RFC: [RFC-0031: Minimal OpenAI-Compatible Chat Access](../RFC/RFC-0031-minimal-openai-compatible-chat-access.md)

## Purpose

This document records the opt-in local execution proof that Aider can use the
completed RFC-0031 compatibility endpoint through temporary client-side
configuration only. It records observed proof results; it does not broaden the
endpoint contract, add a project dependency, or make the proof environment a
supported configuration.

## Proof base

The proof ran on branch `prove-phase-6-aider-access` from `main` proof-base
commit `e296fed`. The RFC-0031 implementation commit was `6c06d39`.

The repository working tree was clean before and after the proof.

## Environment observed

The proof environment provided:

* host Python 3.14.4;
* temporary Aider-environment Python 3.13.1;
* `uv` 0.5.9;
* Aider 0.86.0;
* Ollama 0.30.8; and
* an available `llama3.2` model.

Ollama was already running before the proof and remained running afterward.
These versions and local runtime observations are proof observations, not
project requirements.

## Temporary client environment

Aider ran only through a temporary `uv` environment. That environment included
`aider-chat==0.86.0` and `audioop-lts==0.2.2`; `audioop` imported successfully.
Neither package was added to the repository, and no dependency or lockfile
change was retained.

`audioop-lts` resolved a temporary client-environment compatibility issue. It
is not a Home AI Cluster dependency, configuration choice, or architectural
requirement.

## Loopback boundary

The RFC-0031 compatibility process listened on:

```text
127.0.0.1:8001
```

No non-loopback exposure was found. The temporary inspection proxy also bound
only to loopback and forwarded requests to the existing compatibility process.
Both processes were stopped after the proof, and port 8001 was no longer
listening after cleanup.

## Observed Aider request

The inspection mechanism recorded request metadata only; it did not retain
message content, generated response content, or an authorization value. It
observed exactly one Home AI Cluster request:

```text
POST /v1/chat/completions
```

No unsupported preliminary path, including `/v1/models`, was requested. The
observed request had:

* top-level fields: `messages`, `model`;
* wire `model`: `home-ai-cluster`;
* `stream`: absent;
* `temperature`: absent;
* `tools`: absent;
* `tool_choice`: absent;
* `max_tokens`: absent;
* `response_format`: absent;
* `user`: absent;
* unknown top-level fields: absent;
* message count: 8;
* message roles, in order: `system`, `user`, `assistant`, `user`,
  `assistant`, `user`, `assistant`, `user`; and
* every message content value: a non-empty plain string.

An `Authorization` header was present because Aider was configured with a
placeholder loopback key. Its value was neither recorded nor retained.

## Result

The existing compatibility endpoint returned HTTP 200, and Aider parsed the
response successfully. The request used the existing cluster-owned execution
path. No compatibility error occurred.

The generated response is not included or paraphrased here.

## Privacy and cleanup

The proof retained no prompt, response, bearer value, or private machine
detail. No Aider configuration, history, cache, dependency, or lockfile was
retained in the repository.

The temporary directory was removed. The inspection proxy and compatibility
process were stopped. The final repository working tree was clean.

## Scope preserved

This proof does not authorize or imply:

* streaming;
* `temperature` or other generation controls;
* tools or function calling;
* `GET /v1/models`;
* model aliases or a model catalogue;
* request-level runtime-model selection;
* LAN or remote exposure;
* real authentication;
* broad OpenAI API compatibility; or
* general support for every Aider mode.

All adaptations required for this proof were client-side and temporary.

## Conclusion

The proof demonstrates that Aider v0.86.0 can use the existing RFC-0031
loopback endpoint without any Home AI Cluster code or architecture change.
This completes the Phase 6 developer-tool access proof for the tested
non-streaming plain-text Aider configuration.
