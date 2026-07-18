# RFC-0045: One-shot ordinary request command

Status: Draft

Date: 2026-07-18

Author: frian

## Summary

Home AI Cluster should provide `home-ai-cluster-chat`: one installed, thin,
one-shot command that sends one ordinary chat request to an already running
ordinary cluster process through the existing native HTTP contract.

The command is a client of `POST http://127.0.0.1:8000/v1/chat`. It constructs
one fixed-`chat` request from one `--message` value, emits the existing
normalized `ClusterResult` unchanged on success, otherwise emits one safe error
line, and exits. It does not become another orchestrator, runtime client,
process launcher, topology reader, explanation command, OpenAI-compatible
client, session, or interactive chat application.

## Context

The ordinary local-only and ordinary static-cluster processes both expose the
same loopback cluster-native `POST /v1/chat` contract. Operators currently
construct the target URL, HTTP method, headers, JSON envelope, response parsing,
and failure interpretation manually with curl.

The Phase 16 investigation records that `home-ai-cluster-explain-request` is a
separate in-process explanation and execution surface, not a client of the
running ordinary process. It also concludes that one thin installed Python
command is the smallest access surface that removes manual transport
construction without changing the native protocol. See
`docs/phase-16-ordinary-operator-request-access-investigation.md`.

## Decision

Pending review. This RFC proposes that Home AI Cluster provide the
`home-ai-cluster-chat` command with the following operator contract.

## Command contract

One invocation MUST:

1. validate one local message input;
2. construct one existing native request;
3. perform one HTTP request;
4. emit one success result or one safe failure; and
5. exit.

The command MUST NOT start or stop a cluster process, retry, perform
client-side fallback, retain state, enter an interactive loop, or send more than
one cluster request.

### Target

The command MUST send:

```text
POST http://127.0.0.1:8000/v1/chat
```

This fixed target represents the established ordinary loopback process, whether
that process is local-only or an explicit static cluster. The command MUST NOT
add a base URL, host, or port option; environment-variable configuration;
configuration files; process discovery; declaration parsing; remote-node
addressing; or runtime addressing.

The command MUST NOT add an endpoint or alter `/v1/chat`.

### Message input

The command MUST accept exactly one required option:

```text
--message <MESSAGE>
```

The value MUST contain non-whitespace content, represent exactly one `user`
message, and otherwise be preserved as supplied. The command MUST NOT accept
positional prompt input, standard input, files, multiple messages, arbitrary
roles, system messages, assistant messages, sessions, conversation identifiers,
history input, or interactive prompting.

Command arguments can be retained in shell history or visible through local
process inspection. This command is not secure secret input, and this limitation
MUST be documented with the implementation.

### Capability

The command MUST construct the existing fixed `chat` capability. It MUST NOT
expose a capability option, node selection, adapter selection, runtime
selection, model selection, routing constraints, or generation controls.

This remains capability-centered: the command has one explicit, bounded chat
purpose and does not expose infrastructure selectors.

## Request boundary

The command MUST construct the existing native request equivalent to:

```json
{
  "messages": [
    {
      "role": "user",
      "content": "<MESSAGE>"
    }
  ],
  "capability": "chat"
}
```

This RFC does not define a new request schema or redefine underlying core model
fields. The existing native HTTP and normalized `ClusterRequest` contracts
remain authoritative.

## Success output

On HTTP success with one valid normalized cluster result, the command MUST write
exactly one compact JSON object to standard output representing the complete
existing `ClusterResult`. Standard error MUST remain empty and the exit status
MUST be `0`.

The result remains cluster-owned and includes existing truthful node attribution
and adapter/model information where those fields are currently defined. The
command MUST NOT print only generated content, rename result fields, add wrapper
metadata or routing explanation, pretty-print, add colors, select an output
format, or stream partial output.

An HTTP success alone is insufficient. Before writing output, the command MUST
verify that the response conforms to the authoritative normalized
`ClusterResult` contract. It MUST NOT pass through arbitrary or malformed JSON
returned by another process. Reusing the existing model or placing a narrow
transport helper is an implementation decision; a second independent result
model is not required by this RFC.

## Failure and exit contract

On failure, standard output MUST be empty and standard error MUST contain
exactly one stable, prompt-free category line. The command MUST exit non-zero.

| Condition | Standard error | Exit |
| --- | --- | --- |
| Invalid local input | `error: invalid request input` | 2 |
| Connection failure or timeout | `error: ordinary cluster unavailable` | 1 |
| HTTP 422 native validation rejection | `error: cluster rejected request` | 1 |
| HTTP 404 no chat capability | `error: no available chat capability` | 1 |
| HTTP 503 runtime unavailable | `error: runtime adapter unavailable` | 1 |
| Unexpected HTTP status | `error: ordinary request failed` | 1 |
| Malformed or invalid success response | `error: invalid cluster response` | 1 |
| Other client failure | `error: ordinary request failed` | 1 |

The command MUST NOT emit raw exceptions, tracebacks, raw response bodies, URLs,
prompts, generated responses, private machine identities, remote addresses,
runtime addresses, authorization values, or other private details. The
implementation MAY share handling internally only when the operator-visible
result remains exactly this contract. This RFC does not introduce a larger
generic error taxonomy.

## Timeout

The command MUST perform one request with one finite, implementation-owned
timeout. A timeout MUST map to `error: ordinary cluster unavailable`. The
command MUST NOT retry or perform client-side fallback, and it MUST NOT expose a
timeout option or configuration system.

The numeric timeout duration is an implementation detail selected and tested by
the implementation PR. Cluster routing and accepted fallback remain
process-owned.

## Privacy

The command MUST NOT retain the submitted message, generated response, full
request, or full response. It MUST NOT write request history; expose a history
flag; log prompts or generated content; create files; or persist configuration.

Writing a successful result to standard output is direct operator output, not
project-controlled persistence. The surrounding shell, terminal, operating
system, redirection, and other external tools may retain data outside Home AI
Cluster's control.

## Separation from existing commands

`home-ai-cluster-explain-request` constructs registries, performs routing and
execution in-process, emits an explanation account, and can opt into bounded
history. It is not a client of the separately running ordinary process. The new
command MUST NOT reuse its orchestration behavior. Small input-validation
helpers MAY be shared only when doing so does not merge these responsibilities.

`home-ai-cluster-openai-compatibility` starts the separately accepted
OpenAI-compatible process and protocol. `home-ai-cluster-chat` MUST use only
the native endpoint and MUST NOT call `/v1/chat/completions`.

The new command does not start, configure, inspect, supervise, or stop the
ordinary process; startup and status commands retain those distinct boundaries.

## Engine and topology independence

The command knows only one native cluster endpoint, one native request, and one
native result. It knows nothing about active local runtimes, runtime adapters,
models, local or remote node declarations, static-cluster declaration files,
routing candidates, fallback execution, or topology.

Local-only and static-cluster behavior remain entirely owned by the running
process.

## Rationale

Documentation-only curl remains a useful transparent reference, but it leaves
operators to reconstruct HTTP and JSON details for each request. A maintained
shell wrapper would add shell, external-tool, quoting, and cross-platform
behavior without fitting the existing installed-command model.

An installed Python command can reuse the existing `httpx` dependency, install
with the package's other console commands, make one predictable cross-platform
HTTP exchange, and preserve the correct process boundary. It consumes the
existing native protocol rather than creating another protocol or duplicating
orchestration. A small, focused implementation is consequently reviewable and
reversible.

Changing or renaming the explanation command would preserve neither the running
process boundary nor its ordinary static-cluster composition. A new endpoint is
unnecessary because `/v1/chat` already expresses the needed request and result.

## Consequences

The command makes one ordinary request easier to send while retaining the
ordinary process as the authority. Local-only and static-cluster operation share
one client, normalized result attribution is preserved, and no runtime-specific
client behavior is added.

The deliberate limitations are a fixed loopback target, fixed `chat` capability,
one user message, possible command-line exposure of that message, compact JSON
only, no interactive mode, no configuration, and no remote administration.

## Alternatives considered

The following alternatives are rejected for this contract:

* curl-only access, because it does not remove manual transport construction;
* a maintained shell wrapper, because it adds shell and escaping assumptions;
* changing or renaming `home-ai-cluster-explain-request`, because it is an
  in-process orchestrating explanation surface;
* direct orchestrator invocation or direct runtime access, because both bypass
  the ordinary running process;
* a new native endpoint, because the existing native contract is sufficient;
* OpenAI-compatible reuse, because it is a separate accepted access protocol;
* standard input in the first contract, because it adds blocking and input-source
  semantics without demonstrated need;
* configurable target or capability, because they add ownership and validation
  semantics beyond the first ordinary need;
* content-only output, because it discards truthful normalized attribution;
* interactive chat, because it creates session and lifecycle questions; and
* client retry or fallback, because routing and fallback are cluster-owned.

## Implementation boundaries

The future implementation PR MAY decide module and function names, internal
helper structure, exact timeout duration, precise `httpx` API usage, test
organization, and whether existing request/result models are imported directly
or a narrow transport helper is used.

The implementation PR MUST NOT change this operator contract without an RFC
amendment.

## Proof requirement

After implementation, retain one privacy-safe proof covering:

1. a successful request to an ordinary local-only process;
2. a successful request to an ordinary explicit static-cluster process;
3. the ordinary process being unavailable; and
4. one normalized cluster-owned failure.

The retained proof MUST NOT include the submitted prompt, generated response
content, runtime or remote URLs beyond the fixed public loopback command target,
private machine names, private IP addresses, credentials, or raw exceptions.
Neutral redacted or structural evidence MAY be used where needed.

## Non-goals

This RFC does not add interactive chat, conversational sessions, persistent or
automatic history, standard input, prompt files, arbitrary message arrays,
arbitrary roles, system prompts, generation parameters, streaming, tools,
multimodal input, embeddings, node/adapter/runtime/model selection, routing
configuration, client retry or fallback, direct runtime access, topology or
declaration parsing, process startup, process supervision, lifecycle management,
process discovery, configurable host or port, environment-variable
configuration, config files, a generic HTTP client library, a client SDK, a
generic CLI framework, OpenAI-compatible expansion, authentication, TLS
management, remote administration, a dashboard, database, Docker, or
Kubernetes.
