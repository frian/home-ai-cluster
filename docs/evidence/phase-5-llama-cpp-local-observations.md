# Phase 5 Evidence — llama.cpp Local Observations

Status: Investigation

Date: 2026-07-13

This document records direct observations from André's Linux machine for the
Phase 5 `llama.cpp` server investigation. It is descriptive only and makes no
architectural decision.

## Environment

The machine runs Ubuntu Resolute on Linux x86_64.

Before installation:

```text
$ command -v llama-server || echo "llama-server not installed"
llama-server not installed
```

Ubuntu suggested the package `llama.cpp-tools`.

## Package availability

Observed package metadata:

```text
Package: llama.cpp-tools
Version: 8681+dfsg-1
Origin: Ubuntu
Section: universe/science
Installed-Size: 12.4 MB
Download-Size: 3,546 kB
```

The package description explicitly listed these utilities:

```text
llama-cli
llama-server
llama-bench
llama-quantize
```

The package depends on native runtime libraries and does not add a Python
package dependency to Home AI Cluster.

Evidence type: direct command output from `apt-cache policy` and `apt show`.

## Installed executable and build

After installation:

```text
$ command -v llama-server
/usr/bin/llama-server
```

```text
$ llama-server --version
load_backend: loaded CPU backend from /usr/lib/x86_64-linux-gnu/ggml/backends0/libggml-cpu-icelake.so
version: 8681 (Debian)
built with GNU 15.2.0 for Linux x86_64
```

The local build therefore used the packaged CPU Ice Lake backend.

Selected help output confirmed:

```text
-m, --model FNAME
-a, --alias STRING
--host HOST
--port PORT
--chat-template JINJA_TEMPLATE
--chat-template-file JINJA_TEMPLATE_FILE
--models-dir PATH
--models-preset PATH
```

The default port shown by this build was `8080`.

Evidence type: direct command output.

## Existing model files

No existing `.gguf` file was found under the searched home and Ollama paths.

Installed Ollama models were present, but they were not exposed as directly
usable `.gguf` files by that search.

Evidence type: direct command output.

## Startup proof

The server was started with the official example model repository and explicit
local binding:

```text
llama-server \
  -hf ggml-org/gemma-3-1b-it-GGUF \
  --host 127.0.0.1 \
  --port 8080 \
  --alias phase-5-gemma
```

Observed server output included:

```text
srv          init: init: chat template, thinking = 0
main: model loaded
main: server is listening on http://127.0.0.1:8080
main: starting the main loop...
srv  update_slots: all slots are idle
```

This proves successful local model loading and local-only binding for this
build and model.

Evidence type: disposable local experiment.

## Health proof

With the server ready:

```text
$ curl -i http://127.0.0.1:8080/health
HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Server: llama.cpp

{"status":"ok"}
```

This proves that the packaged server exposes a readiness response suitable for
descriptive health translation.

Evidence type: disposable local experiment.

## Successful non-streaming chat

A request using `system` and `user` roles with `stream: false` succeeded.

Relevant response fields:

```json
{
  "choices": [
    {
      "finish_reason": "stop",
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Yes, it does."
      }
    }
  ],
  "model": "phase-5-gemma",
  "object": "chat.completion",
  "system_fingerprint": "b8681-Debian"
}
```

The response also contained runtime-specific usage, timing, identifier, and
fingerprint metadata. The normalized assistant content was located at:

```text
choices[0].message.content
```

Evidence type: disposable local experiment.

## Current role compatibility

A second request used all three roles currently accepted by Home AI Cluster:

```text
system
user
assistant
```

The server returned:

```text
Your name is Andre.
```

This directly proves that the current normalized role set works with this
specific `llama-server` build and the selected Gemma chat template.

Evidence type: disposable local experiment.

## Malformed request behavior

Sending `messages` as a string rather than an array produced:

```text
HTTP/1.1 400 Bad Request
```

```json
{
  "error": {
    "code": 400,
    "message": "Expected 'messages' to be an array",
    "type": "invalid_request_error"
  }
}
```

This is a structured HTTP response after a connection was established. It is
not a pre-transmission connection failure.

Evidence type: disposable local experiment.

## Model field behavior in single-model mode

A request sent:

```text
model: does-not-exist
```

The server still returned HTTP `200` and executed the loaded model. The response
reported:

```text
model: phase-5-gemma
```

For this single-model setup, the request `model` field was therefore not an
authoritative selector. The loaded server model remained authoritative.

This is an observed runtime behavior, not a Home AI Cluster design decision.

Evidence type: disposable local experiment.

## No-listener behavior

After stopping the server, both health and chat requests failed before an HTTP
connection was established:

```text
curl: (7) Failed to connect to 127.0.0.1 port 8080 after 0 ms: Could not connect to server
```

The same result occurred for:

```text
GET /health
POST /v1/chat/completions
```

This establishes a concrete local example of connection unavailability before
any HTTP response is received. Whether an eventual adapter maps the equivalent
`httpx` failure to the existing narrow cluster-owned connection exception must
be decided by RFC-0030.

Evidence type: disposable local experiment.

## Findings supported by direct observation

The local experiment established that this candidate can:

* install from Ubuntu without Docker or a Python binding;
* run as a separate native process;
* bind explicitly to loopback;
* load one model explicitly;
* expose a ready health endpoint;
* perform non-streaming chat;
* accept the current `system`, `user`, and `assistant` roles for the chosen model;
* return content and model attribution that can be normalized by an adapter;
* return structured HTTP validation errors; and
* fail with a clear no-listener connection error before any HTTP response.

It also established that, in the tested single-model mode, the request's
`model` field does not control execution and should not be treated as
authoritative by the cluster.

## Remaining local unknowns

The following were not yet directly observed:

* readiness behavior while the model is still loading;
* startup behavior with a missing local model path;
* behavior with an incompatible or broken GGUF model;
* shutdown exit code and complete shutdown log;
* behavior under timeout or ambiguous transport interruption; and
* exact exception types produced by `httpx` in a future disposable adapter test.
