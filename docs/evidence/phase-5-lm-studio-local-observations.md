# Phase 5 Evidence — LM Studio Local Observations

Status: Investigation

Date: 2026-07-13

This document records direct observations from André's Linux machine for the
Phase 5 LM Studio local server investigation. It is descriptive only and makes
no architectural decision.

## Initial state

Before installation:

```text
lms not installed
llmster not installed
```

No existing LM Studio configuration files were found in the searched paths.

Evidence type: direct command output.

## Installer inspection

The official installer was downloaded but not executed through `curl | sh`.
The observed script had:

```text
APP_NAME="llmster"
APP_VERSION="0.0.19-2"
APP_VARIANT="full"
ARTIFACT_DOWNLOAD_URL="llmster.lmstudio.ai/download"
```

The script installs under the user's home directory, can skip shell `PATH`
modification with `LMS_NO_MODIFY_PATH=1`, and downloads a `.tar.gz` archive plus
a `.sha512` checksum when available.

Observed installer SHA-256:

```text
eccd90140452a826bac33ea7484588c607a664b15e2f98398fec2e3dccda0a56
```

Evidence type: direct installer inspection.

## Installation

The installer was run with:

```text
LMS_NO_MODIFY_PATH=1 sh ./install.sh
```

Observed result:

```text
Downloading llmster 0.0.19-2 Linux x86_64
Verifying checksum...
Installing llmster...
Install completed at /home/lpa/.lmstudio/llmster/0.0.19-2.
Installation finished successfully!
lms install location: /home/lpa/.lmstudio/bin/lms
```

Observed installed files:

```text
/home/lpa/.lmstudio/bin/lms
/home/lpa/.lmstudio/llmster/0.0.19-2/llmster
```

Approximate observed sizes were 109 MB for `lms` and 151 MB for `llmster`.

Evidence type: direct command output.

## Versions and lifecycle commands

Observed versions:

```text
$ ~/.lmstudio/bin/lms --version
CLI commit: 9902c3a
```

```text
$ ~/.lmstudio/llmster/0.0.19-2/llmster --version
0.0.19+2
```

The CLI exposes separate lifecycle commands for:

```text
lms daemon up|down|status|update
lms server start|stop|status
lms load|unload|ps
```

The server start command supports explicit `--bind` and `--port` options. The
observed default bind documented by the CLI is `127.0.0.1`.

Evidence type: direct command output.

## Daemon and server startup

The daemon was started explicitly:

```text
$ lms daemon up
llmster started (PID: 274694).
```

Status then reported:

```text
llmster v0.0.19+2 is running (PID: 274694)
```

The HTTP server was started separately:

```text
lms server start --bind 127.0.0.1 --port 1234
```

Observed result:

```text
Success! Server is now running on port 1234
```

This directly proves that daemon lifetime and HTTP server lifetime are separate.

Evidence type: disposable local experiment.

## Native model API without authentication

With the server running, this request succeeded without an API token:

```text
GET http://127.0.0.1:1234/api/v1/models
```

Observed response:

```text
HTTP/1.1 200 OK
```

The native response listed one existing embedding model. This proves that the
local REST API was reachable on loopback without account authentication in the
tested configuration.

Evidence type: disposable local experiment.

## Reusing the llama.cpp proof model

The Gemma GGUF downloaded by `llama-server` was found in the Hugging Face cache:

```text
~/.cache/huggingface/hub/models--ggml-org--gemma-3-1b-it-GGUF/
  snapshots/f9c28bcd85737ffc5aef028638d3341d49869c27/
  gemma-3-1b-it-Q4_K_M.gguf
```

The snapshot path was a symbolic link to an 806,058,240-byte blob.

The model was imported into LM Studio using a symbolic link, preserving the
existing cache file and avoiding a second copy.

Observed model metadata:

```text
modelKey: gemma-3-1b-it
publisher: ggml-org
format: gguf
quantization: Q4_K_M
sizeBytes: 806058240
maxContextLength: 32768
```

Evidence type: disposable local experiment.

## Explicit model loading

The model was loaded explicitly with:

```text
lms load gemma-3-1b-it \
  --identifier phase-5-gemma \
  --gpu off \
  --context-length 4096 \
  -y
```

Observed result:

```text
Model loaded successfully in 2.10s.
(768.72 MiB)
To use the model in the API/SDK, use the identifier "phase-5-gemma".
```

`lms ps --json` reported:

```text
identifier: phase-5-gemma
contextLength: 4096
status: idle
parallel: 4
```

Evidence type: disposable local experiment.

## Successful native chat

The native endpoint was called with storage explicitly disabled:

```text
POST /api/v1/chat
store: false
model: phase-5-gemma
system_prompt: Answer briefly.
input: Confirm that the runtime works.
```

Observed response:

```json
{
  "model_instance_id": "phase-5-gemma",
  "output": [
    {
      "type": "message",
      "content": "Yes."
    }
  ]
}
```

The response also contained runtime-specific statistics. Normalized assistant
content was available at:

```text
output[0].content
```

The returned runtime model identifier was available at:

```text
model_instance_id
```

Evidence type: disposable local experiment.

## Native conversation-shape limitation

A native request attempted to pass a role-based history containing:

```text
user
assistant
user
```

under `input`. The server returned:

```text
HTTP/1.1 400 Bad Request
```

```json
{
  "error": {
    "message": "Invalid discriminator value. Expected 'text' | 'image', Invalid discriminator value. Expected 'text' | 'image', Invalid discriminator value. Expected 'text' | 'image'",
    "type": "invalid_request",
    "code": "invalid_union",
    "param": "input"
  }
}
```

This directly proves that the tested native `/api/v1/chat` input shape is not a
drop-in representation of the current `ClusterRequest.messages` history.

This is a runtime interface fact, not a decision about which LM Studio endpoint
a future adapter should use.

Evidence type: disposable local experiment.

## Unknown model behavior

A request using:

```text
model: does-not-exist
```

returned:

```text
HTTP/1.1 404 Not Found
```

```json
{
  "error": {
    "message": "Invalid model identifier \"does-not-exist\". Please specify a valid downloaded model (e.g., gemma-3-1b-it).",
    "type": "invalid_request",
    "param": "model",
    "code": "model_not_found"
  }
}
```

No model execution occurred. In the tested native API, the requested model
identifier was therefore authoritative, unlike the single-model `llama-server`
behavior observed separately.

Evidence type: disposable local experiment.

## Daemon alive while HTTP server is unavailable

The HTTP server was stopped while the daemon remained active.

Observed status:

```text
llmster v0.0.19+2 is running (PID: 274694)
The server is not running.
```

A request to the native models endpoint then failed before any HTTP response:

```text
curl: (7) Failed to connect to 127.0.0.1 port 1234 after 0 ms: Could not connect to server
```

This directly proves that daemon availability does not imply HTTP server
availability. An eventual adapter health check must target the execution
boundary it actually depends on rather than treating daemon process existence
as sufficient readiness.

Whether an eventual adapter maps the equivalent `httpx` connection failure to
the existing narrow cluster-owned pre-request exception must be decided by
RFC-0030.

Evidence type: disposable local experiment.

## Findings supported by direct observation

The local experiment established that LM Studio can:

* install in the user's home directory without Docker;
* operate locally without an account or API token in the tested configuration;
* run daemon, HTTP server, and loaded model as separate lifecycle layers;
* bind the HTTP server explicitly to loopback;
* expose a native REST API distinct from compatibility endpoints;
* load a model explicitly under an API identifier;
* perform a simple non-streaming native chat request;
* disable native chat storage explicitly with `store: false`;
* return content and model attribution that can be normalized by an adapter;
* reject unknown model identifiers explicitly; and
* exhibit connection unavailability while the daemon remains alive.

It also established that the tested native chat input does not directly accept
the current role-based `ClusterRequest.messages` history.

## Remaining local unknowns

The following were not yet directly observed:

* exact health or readiness endpoint semantics beyond successful API access;
* behavior while a model is loading;
* behavior when the daemon itself is stopped;
* exact support of the OpenAI-compatible chat endpoint with all current roles;
* timeout and ambiguous transport behavior;
* exact exception types produced by `httpx` in a disposable adapter test; and
* whether a future proof should prefer the native or compatibility endpoint.
