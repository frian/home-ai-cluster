# Aider Code Bridge Proof Runbook

Status: Prepared

## 1. Purpose

This runbook prepares, but does not execute, one bounded one-machine proof:

```text
operator -> Aider -> temporary caller-owned loopback bridge
  -> native Home AI Cluster POST /v1/chat, capability=code
  -> free-form textual result -> bridge response projection
  -> Aider caller-owned edit of one disposable script file
```

The later proof may establish one narrow practical fact: a local developer tool
used RFC-0067's explicit `code` capability to help create or modify one small
disposable script without manual copy/paste. It is not implementation, a
supported integration, or an architectural decision.

## 2. Architectural boundary

| Component | Authority in this proof |
| --- | --- |
| Home AI Cluster | Validates explicit `code`, routes by capability, executes through the selected adapter, and returns a free-form textual `ClusterResult`. |
| Temporary bridge | Binds loopback only, translates one strict request shape, unconditionally sets `capability=code`, and projects one strict response shape. |
| Aider | Reads the disposable target file, interprets returned text, and modifies that file under caller authority. |

HAC does not read or write the target file, inspect a repository, run shell
commands or tests, use Git, invoke tools/functions, control Aider, parse or
apply a patch, or execute generated code. The model receives text and produces
text only.

An Aider file edit is caller action, not HAC tool execution. RFC-0067 free-form
output is not a guaranteed patch or safe-edit representation. This proof
observes only one constrained caller edit.

## 3. What this proof can establish

When all success criteria are met, one later execution establishes only:

```text
Aider owned one disposable-file edit
  after one bridge request explicitly required code
  and HAC returned one textual result.
```

It can also establish that HAC made no filesystem or repository operation.

## 4. What it cannot establish

This proof does not establish general Aider `code` support, a stable bridge API,
a supported HAC integration, general OpenAI compatibility, security sandboxing,
model or script correctness, safe arbitrary editing, tools, command execution,
autonomous coding, production readiness, or distributed execution.

Aider guardrails are not OS-level sandboxing. No sandbox design or
implementation is part of this proof.

## 5. Required environment

Use exactly one machine, one existing operator-owned supported local runtime,
one ordinary HAC native process, one temporary loopback bridge, Aider 0.86.2,
and one disposable temporary workspace.

Before a real attempt, inspect without retaining private output:

```sh
git status --short
git rev-parse HEAD
aider --version
aider --help
```

Proceed only if repository status has no output and Aider reports `0.86.2`. Do
not install, upgrade, or otherwise change Aider.

## 6. Fixed process roles

| Role | Address | Ownership |
| --- | --- | --- |
| Ordinary HAC native process | `127.0.0.1:8000` | Existing Home AI Cluster process |
| Temporary proof bridge | `127.0.0.1:8001` | Caller-owned, outside this repository |
| Aider base URL | `http://127.0.0.1:8001/v1` | Aider client configuration |

Do not use a LAN listener, second machine, Docker, container, proxy, reverse
proxy, VPN, public endpoint, or hosted inference provider. The bridge is not
the RFC-0031 compatibility process; it is a temporary caller-owned test adapter.

## 7. Privacy boundary

Do not retain prompts, generated source, target-file contents or names, bearer
values, private paths, machine names, model/runtime identifiers, request or
response bodies, raw logs, shell history, screenshots, packet captures, or
temporary configuration in repository documentation.

Use neutral placeholders:

```text
<TEMPORARY_DIRECTORY>
<TEMPORARY_BRIDGE_PATH>
<TEMPORARY_AIDER_SETTINGS_PATH>
<DISPOSABLE_TARGET_FILE>
<ONE_HARMLESS_SCRIPT_EDIT_REQUEST>
```

The bearer placeholder is non-secret and is not authentication or authorization.

## 8. Temporary bridge source

Create this single-use source outside the repository at
`<TEMPORARY_BRIDGE_PATH>`. Do not add it to Git. It uses only the Python
standard library, serves one accepted request, emits one content-free success
observation, and stops.

```python
import http.client
import json
import sys
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class BridgeHandler(BaseHTTPRequestHandler):
    accepted_request_count = 0

    def log_message(self, format, *args):
        pass

    def send_json(self, status, body):
        encoded = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def fail(self, status, message):
        self.send_json(status, {"error": {"message": message}})

    def do_POST(self):
        if self.path != "/v1/chat/completions":
            self.fail(404, "Not found")
            return
        authorization = self.headers.get("Authorization")
        if authorization is not None and not authorization.startswith("Bearer "):
            self.fail(400, "Invalid request")
            return
        try:
            size = int(self.headers.get("Content-Length", ""))
            body = json.loads(self.rfile.read(size))
        except (ValueError, json.JSONDecodeError):
            self.fail(400, "Invalid request")
            return
        if not isinstance(body, dict) or set(body) not in (
            {"model", "messages"},
            {"model", "messages", "stream"},
        ):
            self.fail(400, "Unsupported request")
            return
        if body["model"] != "home-ai-cluster" or body.get("stream", False) is not False:
            self.fail(400, "Unsupported request")
            return
        messages = body["messages"]
        if not isinstance(messages, list) or not messages:
            self.fail(400, "Invalid request")
            return
        for message in messages:
            if (
                not isinstance(message, dict)
                or set(message) != {"role", "content"}
                or message["role"] not in {"system", "user", "assistant"}
                or not isinstance(message["content"], str)
                or not message["content"]
            ):
                self.fail(400, "Unsupported request")
                return
        if BridgeHandler.accepted_request_count != 0:
            self.fail(409, "Only one request is permitted")
            return
        BridgeHandler.accepted_request_count = 1
        try:
            connection = http.client.HTTPConnection("127.0.0.1", 8000, timeout=120)
            connection.request(
                "POST",
                "/v1/chat",
                body=json.dumps({"messages": messages, "capability": "code"}),
                headers={"Content-Type": "application/json"},
            )
            response = connection.getresponse()
            hac_body = json.loads(response.read())
            connection.close()
            if response.status != 200 or not isinstance(hac_body.get("content"), str):
                raise ValueError
        except (OSError, ValueError, json.JSONDecodeError):
            self.fail(502, "Home AI Cluster request failed")
            return
        self.send_json(
            200,
            {
                "id": f"chatcmpl-{uuid.uuid4().hex}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": "home-ai-cluster",
                "choices": [{
                    "index": 0,
                    "message": {"role": "assistant", "content": hac_body["content"]},
                    "finish_reason": None,
                }],
            },
        )
        sys.stderr.write(
            "bridge_observation accepted_request=1 capability=code outcome=success\n"
        )
        threading.Thread(target=self.server.shutdown, daemon=True).start()


ThreadingHTTPServer(("127.0.0.1", 8001), BridgeHandler).serve_forever()
```

### Accepted Aider request subset

The bridge accepts exactly one `POST /v1/chat/completions` body:

```json
{
  "model": "home-ai-cluster",
  "messages": [{"role": "system|user|assistant", "content": "non-empty string"}]
}
```

The optional third field is only `"stream": false`; the retained Aider proof
observed an omitted `stream` field under its non-streaming configuration, so
the bridge accepts that current conservative shape too. It allows no bearer
header or a syntactically `Bearer `-prefixed placeholder, but never retains or
forwards it. It rejects all other top-level or message fields, streaming,
tools, functions, multiple choices, generation parameters, multimodal/non-string
content, model discovery, and a second accepted request.

### Native HAC translation and response projection

For the one accepted request, the bridge preserves ordered plain-text messages
and sends exactly one request to `http://127.0.0.1:8000/v1/chat`:

```json
{
  "messages": ["<preserved ordered plain-text messages>"],
  "capability": "code"
}
```

`capability=code` is unconditional bridge behavior for this endpoint. It is
not inferred from prompt content, language, model name, file name, or message
shape; it is not a generic parameter. The bridge selects no node, runtime,
adapter, or concrete model.

On success it projects HAC's actual textual `content` into one non-streaming
Chat-Completions-shaped response. The fixed identifier and `finish_reason: null`
claim neither model selection nor generation-finish provenance. It provides no
usage, tool, routing, node, or runtime data.

## 9. Temporary Aider configuration

Create this settings file outside the repository:

```yaml
- name: openai/home-ai-cluster
  edit_format: whole
  use_temperature: false
```

`whole` keeps the proof out of the tool/function path documented by the Phase 6
investigation. `use_temperature: false` prevents the otherwise default
temperature field. This is Aider-only configuration, not HAC configuration.

Local Aider 0.86.2 help verifies these selected guardrails:

- `--no-stream`, `--no-analytics`, `--no-check-update`, and
  `--no-show-release-notes` avoid streaming, analytics, updates, and release
  activity;
- `--no-cache-prompts`, null input/chat histories, no LLM-history option, and
  `--env-file /dev/null --config /dev/null` avoid selected content retention
  and ambient repository/home configuration;
- `--no-git --no-gitignore --no-auto-commits --no-auto-lint --no-auto-test`
  and `--no-watch-files` avoid Git and automatic commit/lint/test/watch paths;
- `--no-suggest-shell-commands --no-detect-urls --no-gui --no-copy-paste
  --disable-playwright --no-notifications` avoid unrelated command, URL,
  browser, clipboard, scraper, and notification paths.

These are guardrails, not a sandbox. Do not use `--dry-run` because Aider must
modify the disposable target. Do not use `--yes-always`; remain present to
refuse unexpected action.

## 10. Disposable workspace preparation

Create a temporary non-production directory outside this repository. Use no
other source files, repository, worktree, or Aider configuration. Make one
harmless target file with:

```python
# placeholder
```

At execution, request only `<ONE_HARMLESS_SCRIPT_EDIT_REQUEST>`: a very small,
harmless modification, for example a Python script that prints a fixed greeting.
Do not retain the actual request or generated source, and do not execute it.

## 11. Preflight checklist

Before the one attempt, confirm:

1. Repository status is clean and HAC implementation is unchanged.
2. The supported local runtime is already available under operator control.
3. HAC is using `127.0.0.1:8000` and supports `code`.
4. Bridge and Aider files are outside the repository.
5. The bridge binds exactly to `127.0.0.1:8001`.
6. The temporary directory has exactly one intended placeholder target file.
7. No production file, secret, or private prompt is in scope.
8. The Aider command has no `--read`, `--message-file`, `--load`, `--apply`,
   test, lint, or command option and names only the target file.
9. The operator is prepared to stop rather than retry or broaden a failure.

## 12. Startup order

Use three separate terminals:

1. Start the existing ordinary native HAC process by the normal local operator
   path, bound to `127.0.0.1:8000`.
2. Run the temporary bridge with Python; it binds to `127.0.0.1:8001`.
3. From the temporary directory, run the one Aider invocation below.

Do not start `hac compatibility`, static-cluster, a proxy, a second bridge, or
another AI client.

## 13. Single-request execution

Expand placeholders only during the later attempt:

```sh
aider --model openai/home-ai-cluster \
  --openai-api-base http://127.0.0.1:8001/v1 \
  --openai-api-key ignored-loopback-placeholder \
  --model-settings-file <TEMPORARY_AIDER_SETTINGS_PATH> \
  --no-stream --no-analytics --no-check-update --no-show-release-notes \
  --no-cache-prompts --input-history-file /dev/null --chat-history-file /dev/null \
  --env-file /dev/null --config /dev/null \
  --no-git --no-gitignore --no-auto-commits --no-auto-lint --no-auto-test \
  --no-watch-files --no-suggest-shell-commands --no-detect-urls --no-gui \
  --no-copy-paste --disable-playwright --no-notifications \
  --file <DISPOSABLE_TARGET_FILE> \
  --message "<ONE_HARMLESS_SCRIPT_EDIT_REQUEST>"
```

Do not use `--dry-run`, `--yes-always`, retries, a second submission, attached
or read-only files, tools/functions, or a non-loopback model endpoint. If Aider
requests an unexpected command, test, lint action, or edit outside the target,
refuse it and stop. Approving the one intended target-file edit remains caller
authority and does not send another model request.

## 14. Bridge observation

On success the bridge writes exactly this content-free stderr line:

```text
bridge_observation accepted_request=1 capability=code outcome=success
```

This is caller-owned bridge evidence, not HAC observation. Retain only this
structural fact. A second request, unsupported shape, or HAC failure must never
be rewritten as success.

## 15. File-edit observation

Observe without retaining source content that the target existed before the
submission, changed afterward, and no other temporary-workspace file changed.
Attribute the edit to Aider/caller authority. State separately that HAC returned
text only and performed no file operation.

Do not execute the script, test it, lint it, check semantic correctness, or
commit it.

## 16. Success criteria

The later proof passes only if all are true:

1. Initial repository status is clean and HAC implementation is unchanged.
2. The bridge is outside the repository and loopback-only.
3. Aider targets only the bridge for one model request.
4. The bridge accepts exactly one request and emits exactly one success line.
5. The line states `capability=code`.
6. The bridge sends exactly one native HAC `/v1/chat` request with explicit
   `capability=code`.
7. HAC returns one successful textual result, projected to Aider.
8. Aider modifies exactly the intended disposable script file.
9. No generated code executes; no test, lint, shell command, or automatic Git
   commit occurs.
10. HAC performs no filesystem or repository operation.
11. Retained repository evidence contains no prompt, source, bearer, private
    path, machine name, model/runtime identifier, or raw transcript.

## 17. Failure and stop criteria

Stop without retry if the bridge cannot strictly validate Aider's request; Aider
sends a second request, model-discovery request, stream, tool/function request,
or unsupported field; the native request lacks explicit `code`; HAC fails;
Aider does not apply the intended edit; another file changes; command/test/lint
activity occurs; the bridge binds beyond loopback; or private/content-bearing
evidence would be required to make the claim.

Do not broaden HAC or the bridge, change tool/mode, or retry. A failed proof is
useful evidence for separate reassessment.

## 18. Cleanup

After either outcome, stop the HAC process started for the proof and ensure the
bridge has stopped. Remove the bridge source, Aider settings/configuration,
temporary histories/log captures, placeholder bearer material, and disposable
workspace. Do not add them to Git.

Confirm the repository working tree remains unchanged except for this
documentation branch.

## 19. Retained evidence

A later proof result may retain only:

```text
Aider version: 0.86.2
temporary bridge: loopback-only
accepted requests: 1
forwarded capability: code
HAC result: success
caller-owned target-file edit: observed
generated code execution: none
HAC filesystem authority: none
```

Use a neutral file placeholder if needed. Do not retain a prompt, generated
script, bearer, actual path, private machine detail, or raw transcript.

## 20. Pending independent work

The physical two-machine RFC-0067 `code` proof remains pending and independent.
This one-machine proof does not satisfy the physical remote requirement.

Bounded web access for one capability remains the next separate architectural
investigation after this caller-side proof work unless evidence changes
priorities. It is not analyzed or authorized here.
