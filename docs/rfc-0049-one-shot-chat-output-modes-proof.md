# RFC-0049 one-shot chat output modes proof

## Status

Retained implementation evidence for accepted RFC-0049. This record is not a
new decision or contract.

## Scope

The proof covers the installed `home-ai-cluster-chat` client against ordinary
local-only and ordinary explicit static-cluster processes through their ordinary
loopback endpoint. It verifies that RFC-0049 presentation occurs only after the
existing request path produces a validated result.

## Repository state

- Proof date: 2026-07-21.
- Branch: `prove-rfc-0049-one-shot-chat-output-modes`.
- Tested commit: `6e0b17f`.
- Python: 3.13.1.
- Relevant commands: `home-ai-cluster-chat`,
  `home-ai-cluster-static-cluster`, and `home-ai-cluster-local`.
- RFC-0049 status: Accepted.

## Automated validation

The following completed successfully:

```text
uv run ruff format --check src/home_ai_cluster/chat_command.py tests/test_chat_command.py
uv run ruff check src/home_ai_cluster/chat_command.py tests/test_chat_command.py
uv run pytest tests/test_chat_command.py
uv run pytest
```

The focused chat-command suite passed 40 tests. The full repository suite passed
688 tests. The focused tests cover default newline and empty-content behavior,
multiline and Unicode content, verbose model omission, the `-v` alias, exact
compact JSON compatibility, shared failures, and mutual exclusion without an
HTTP request.

## Ordinary local-only live proof

The documented local-only preflight was coherent and local health observed the
external adapter as available. The documented ordinary local-only application
was then started on the loopback endpoint, without a static-cluster process.

- One successful one-shot verbose chat request completed through the ordinary
  loopback client.
- `Response:` and `Execution:` sections were observed.
- `Node`, then `Adapter`, then optional `Model` ordering was observed.
- Cluster-owned local attribution was observed.
- Standard error was empty.
- Exit status was 0.

The local-only application was stopped normally after the check. No static
declaration or remote topology was involved, and no private runtime or transport
value was retained.

## Ordinary explicit static-cluster live proof

An operator-prepared ordinary explicit static-cluster calling process was
already running on the documented loopback endpoint. The existing receiving
application and calling process were not stopped, replaced, or supplemented.
The installed client made one successful request in each mode below.

### Default output

- Direct generated-content presentation was observed.
- No JSON envelope was observed.
- Standard error was empty.
- Exit status was 0.

### Verbose output

- `Response:` and `Execution:` sections were observed.
- `Node`, then `Adapter`, then optional `Model` attribution order was observed.
- Cluster-owned local attribution was observed through accepted local-first
  routing.
- Standard error was empty.
- Exit status was 0.

### `-v` alias

- The same response and execution structure as `--verbose` was observed.
- Cluster-owned local attribution was observed.
- Standard error was empty.
- Exit status was 0.

### JSON output

- One compact complete `ClusterResult` object was observed.
- Historical `content`, `adapter`, `model`, `node_id` field order was observed.
- One final newline and no human framing were observed.
- Standard error was empty.
- Exit status was 0.

The static-cluster requests exercised accepted local-first selection. Remote
execution was not required for this RFC-0049 presentation proof and is not
claimed by this record. The observed result presentation remained at the CLI
edge; the client continued to address one ordinary loopback cluster endpoint.

## Invalid mode combination check

One `--verbose --json` invocation completed before HTTP client construction:

```text
stdout: empty
stderr: error: invalid request input
exit: 2
```

Focused automated coverage also verifies the no-request mutual-exclusion path.

## Privacy review

This retained record contains no prompt text, generated response content,
complete JSON output, declaration path or contents, remote URL, private IP
address, username, home-directory path, machine name, credential, authorization
value, raw exception, or runtime response body.

## Result

RFC-0049 proof requirements are satisfied. Automated tests establish exact
byte-level JSON compatibility, newline and empty-content contracts, model
omission behavior, shared stable failures, Unicode behavior, and local
mutual-exclusion behavior. Local-only live evidence establishes the ordinary
local process and successful verbose presentation with cluster-owned local
attribution. Static-cluster live evidence establishes default, `--verbose`,
`-v`, and `--json` presentation through the ordinary explicit static-cluster
client path with successful local-first cluster-owned attribution.

## Limitations

This proof does not add or demonstrate sessions, streaming, standard-input or
file input, tools, direct node selection, balancing, discovery, supervision,
topology mutation, persistence, history, TTY-dependent behavior, or a generic
formatter framework. It does not claim remote execution or alter routing,
fallback, topology, runtime ownership, or process lifecycle.
