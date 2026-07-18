# Phase 16 Ordinary Operator Request Access Investigation

Status: Complete

## Question

What is the smallest ordinary operator access surface that lets one operator
send one capability-centered request to an already running ordinary Home AI
Cluster process without manually constructing HTTP transport details?

## Scope

This investigation concerns one ordinary request to the existing cluster-native
contract. It recommends a possible next step but does not accept or implement a
command, protocol, or operator contract.

## Current ordinary request path

The ordinary FastAPI application exposes `POST /v1/chat` in
`src/home_ai_cluster/api/routes.py`. `home-ai-cluster-local` starts that
application with an explicit local runtime composition; its default target is
`127.0.0.1:8000`. `home-ai-cluster-static-cluster` starts the same application
shape for an explicit static cluster and binds the same loopback target. The
static process changes only its process-local composition and routing wiring;
the operator still addresses the same native endpoint. See
`src/home_ai_cluster/local_runtime.py`, `src/home_ai_cluster/static_cluster.py`,
and `docs/operator-workflow.md`.

The public request is a JSON object with a non-empty `messages` array and a
non-empty string `capability`. Each message has a `system`, `user`, or
`assistant` role and non-empty string content. The route turns the capability
into the normalized `ClusterRequest` used by routing; it does not accept node,
adapter, runtime, or model selection. The successful normalized JSON result is
`content`, `adapter`, optional `model`, and cluster-owned `node_id`. The route
does not expose routing explanation fields. See `api/routes.py`,
`core/models.py`, and `tests/test_routes.py`; this preserves RFC-0001,
RFC-0005, and RFC-0023.

The ordinary route normalizes unavailable runtime adapters to HTTP 503 with
`{"detail":"Runtime adapter unavailable"}` and hides runtime-specific detail.
It returns HTTP 404 with a capability-only detail when no matching adapter is
available. Request-shape failures use FastAPI/Pydantic validation rather than a
separate native error envelope. These are safe HTTP boundaries, not a client
exit-status contract. RFC-0007 and `tests/test_routes.py` establish the
unavailability boundary.

There is no supported non-HTTP input to an already running ordinary process.
The operator currently has to construct the target URL, `POST` method,
content-type header, JSON envelope, capability, message array, response
parsing, and HTTP/process failure interpretation. The curl examples in
`README.md` and `docs/operator-workflow.md` make that work visible.

## Current operator friction

The canonical local-only and explicit static-cluster workflows both require an
operator to reproduce the same curl request against
`http://127.0.0.1:8000/v1/chat`. This is portable as documentation, but it does
not remove JSON quoting, message escaping, HTTP status handling, or choosing
which JSON to inspect after a failure. It also leaves each caller to decide how
to distinguish a missing process from a normalized cluster failure.

## Existing operator request commands

`home-ai-cluster-explain-request` is not a thin client of an ordinary running
cluster process. `src/home_ai_cluster/actual_request_explanation.py` parses
`--capability` and `--message`, constructs its own local node and adapter
registries, selects a candidate, and calls selected-candidate orchestration in
its own process. It neither sends HTTP nor reuses `POST /v1/chat`.

It also has an explicit `--record-history` option and emits an explanation
account rather than the ordinary `ClusterResult`. It cannot use the explicit
static-cluster composition of a separately running process because it has no
connection to that process or its process-local wiring. It is therefore an
explanation and inspection surface, not an ordinary request client. Reusing or
renaming it would fail the Phase 16 requirement and should not be used to avoid
a separate bounded surface. RFC-0032, RFC-0034, and RFC-0035 intentionally
govern this distinct behavior.

The `pyproject.toml` console scripts likewise provide startup, status,
preflight, health, proof, history, explanation, and separate OpenAI-compatible
access commands, but no command that sends an ordinary native request to an
already running process. `home-ai-cluster-openai-compatibility` starts a
separate loopback process on port 8001 for RFC-0031's deliberately separate
`/v1/chat/completions` compatibility surface; it is not a replacement for the
native endpoint.

## Options investigated

### Documentation-only curl

Curl documentation has no implementation cost and remains useful as a
transparent reference. It is portable where curl exists, but retains all manual
transport construction, JSON escaping, response parsing, and shell-dependent
error handling. It cannot by itself satisfy Phase 16 success. It has no
project-owned retention, but command arguments may still enter shell history.

### Maintained shell script

A shell wrapper could hide some curl syntax, but introduces shell and external
tool assumptions, difficult multiline and JSON escaping, and an additional
error/exit contract outside the Python package. Installation and discoverability
would also be separate from the existing console-script mechanism. It would
duplicate HTTP and validation behavior while providing less consistent
cross-platform behavior than the installed package. It is not simpler than a
small Python entry point.

### Thin one-shot Python command

An installed command, provisionally named `home-ai-cluster-chat`, can use the
existing `httpx` dependency to send exactly one `POST /v1/chat` request to an
already running ordinary process. It need not construct registries, call an
adapter or orchestrator, start a process, interpret declarations, or know a
topology, runtime, adapter, model, or remote node.

This option can own only input validation, construction of the existing native
request, one finite HTTP exchange, truthful projection of the existing result,
safe client-side failure reporting, and one exit. It works for both ordinary
local-only and ordinary static-cluster processes because both retain the same
endpoint contract. It would create a durable operator contract and therefore
requires an RFC before implementation.

### New or changed HTTP endpoint

No new endpoint and no change to `/v1/chat` is needed. The native contract
already carries the one needed capability-centered request and normalized
result. A convenience client should consume that contract, not create a second
native protocol. The separate RFC-0031 OpenAI-compatible surface is evidence
that a different public protocol is an architectural decision, not a shortcut
for ordinary operator access.

## Request input

A positional message is short but offers no advantage over an explicit option
and is easier to confuse with future arguments. A required `--message` option
is clearest for one plain user message, but its value can appear in shell
history and process inspection. Standard input better supports multiline and
some scripted input, but can block accidentally and requires an explicit
empty-input and terminal policy. Supporting both creates source precedence and
ambiguity when both are supplied.

The smallest first proof should accept one required `--message` value only,
preserve it exactly after non-empty validation, and document its exposure
limits. It should not introduce roles, system prompts, arbitrary message arrays,
conversation files, sessions, or an interactive loop. Standard input can be
reconsidered only when an operator need is demonstrated.

## Capability behavior

A required or optional `--capability` option is flexible, but there is no
evidence that the first ordinary operator request needs a capability other than
chat. An optional default silently broadens the command's supported surface;
requiring it recreates friction that the command is meant to remove. The first
proof should construct the existing `chat` capability as a fixed, documented
part of a one-message chat command. This remains capability-centered without
adding node, adapter, runtime, or model selectors.

## Cluster target

The ordinary workflows already establish `http://127.0.0.1:8000/v1/chat` as
the default loopback target. A fixed target is sufficient for the first proof
and keeps target ownership with the operator who starts the ordinary process.
An optional base URL is not currently needed and would expand validation,
privacy, compatibility, and target-ownership semantics. Environment-variable
configuration, process discovery, and static-declaration parsing would add
hidden precedence or topology knowledge and are rejected.

The client must address the ordinary cluster endpoint only. It must not address
a runtime or receiving node directly.

## Success output

The command should write the complete existing normalized `ClusterResult` JSON
unchanged to standard output on success. Printing only generated content would
discard truthful cluster-owned adapter, model, and node attribution; selectable
formats would create a new output framework without evidence. One compact JSON
object is enough for a terminal and scripts.

## Failures and exit behavior

The following is the smallest candidate client boundary for an RFC to decide:

| Failure layer | Standard output | Safe standard error category | Exit |
| --- | --- | --- | --- |
| Invalid local command input | empty | `invalid request input` | 2 |
| Cannot connect or finite timeout | empty | `ordinary cluster unavailable` | 1 |
| Native HTTP validation failure | empty | `cluster rejected request` | 1 |
| Native HTTP 404 capability failure | empty | `no available chat capability` | 1 |
| Native HTTP 503 runtime failure | empty | `runtime adapter unavailable` | 1 |
| Malformed or unexpected success response | empty | `invalid cluster response` | 1 |
| Other client failure | empty | `ordinary request failed` | 1 |

The command should not print raw response bodies, exception text, stack traces,
URLs, authorization values, private machine details, prompts, or generated
responses in errors. It should not emit error JSON to standard output. The
exact mapping must preserve existing cluster failures rather than invent a broad
taxonomy.

## Timeout

One finite, implementation-owned HTTP timeout is appropriate so a one-shot
command cannot wait indefinitely. It should not be configurable in the first
proof and should not add client retries or fallback. Cluster routing and the
accepted fallback remain wholly cluster-owned. The RFC should define the
operator-visible timeout category; the tested fixed duration can remain a small
implementation detail.

## Privacy boundary

Home AI Cluster must not retain the submitted message or returned response.
Writing the result directly to the operator's terminal is not project logging or
persistence. Command-line arguments may be retained in shell history or visible
to local process inspection; standard input reduces some exposure but is not a
universal secret channel. Application logs must remain prompt-free and
response-free. The first access surface must not add a history flag or connect
to bounded request history.

## Architectural assessment

Yes. An RFC is required before implementation. Although the code can be small,
the command would establish a durable operator contract: name, one-message
input, fixed chat capability, fixed target behavior, native HTTP boundary,
success JSON, safe failures, exit behavior, timeout, and privacy rules. These
affect user-facing operation, compatibility, request access, and privacy
boundaries under the repository's RFC criteria. The concrete `httpx` call,
module names, and tests can remain implementation details.

## Recommendation

Recommend a future RFC for one installed, thin, one-shot Python chat command.
It should send one fixed-`chat`, one-user-message request to the already running
ordinary loopback native endpoint, print the unchanged normalized result, and
exit. This is the only investigated option that removes manual HTTP construction
while preserving the cluster as the request, routing, and execution authority.

Curl remains useful reference documentation but is insufficient; a shell script
adds portability and escaping burden; an endpoint change has no demonstrated
need. The existing explanation command is intentionally in-process and cannot
substitute for the recommended client.

## Proposed next step

Draft an RFC defining the narrow operator contract above. After acceptance,
implement the command with the existing `httpx` dependency and prove it against
both an ordinary local-only process and an ordinary explicit static-cluster
process. The proof should retain only privacy-safe evidence that one request
received one normalized result or safe failure; it must not retain prompt or
generated-response content.

## Non-goals retained

This investigation retains the exclusions of conversational or interactive chat,
sessions, persistent or automatic history, databases, streaming, tools,
multimodal input, arbitrary role/message arrays, generation controls, new
routing, client retry or fallback, node/adapter/runtime/model selection, direct
runtime access, a new endpoint, OpenAI-compatible expansion, discovery,
declaration parsing, process startup or supervision, lifecycle management, a
generic client SDK or command framework, configuration files, environment
variable configuration, dashboards, Docker, and Kubernetes.
