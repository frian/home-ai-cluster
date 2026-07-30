# RFC-0060: Explicit Native Client Timeout

Status: Draft

Date: 2026-07-30

Author: frian

## Summary

Ordinary native `chat` and `summarize` clients should accept one optional,
shared `--timeout-seconds SECONDS` value for a single invocation. Omission
retains RFC-0055's 120.0-second HTTPX scalar default.

The option changes only how long the one-shot client waits at its fixed
loopback HTTP boundary. It does not configure the static-cluster caller,
declared remote, receiver, adapter, runtime, model, topology, routing, or
fallback. It remains finite, capability-neutral, topology-blind, and free of
retry and cancellation behavior.

## Problem

RFC-0055 established one shared, implementation-owned 120.0-second HTTPX
scalar timeout for ordinary native `chat` and `summarize` clients. At that
time, a fixed default was the smallest correction and public configuration was
deliberately rejected.

A later privacy-safe operator observation showed a legitimate ordinary static
cluster summarize request repeatedly exceeding that waiting boundary. The
caller-local routing declaration allowed `chat`; one declared remote was
eligible for `summarize`; routing therefore selected the remote directly. The
workload was valid, but three separate client invocations reached the timeout.
The observation contains no private topology, request, result, runtime, model,
or hardware data, and it does not prove cancellation or completion after a
timeout.

The merged timeout configurability investigation concluded Outcome C: the
accepted fixed timeout contract must be reconsidered through an RFC. It
identified a revised fixed default and one explicit per-invocation value as
credible alternatives. This draft proposes the latter because it addresses the
observed slow-but-valid work without increasing the waiting boundary for every
ordinary invocation.

## Goals

This RFC proposes to:

- support demonstrated slow-but-valid ordinary work without changing the
  universal 120.0-second default;
- preserve finite one-shot client commands;
- preserve compatibility when the option is omitted;
- expose one explicit local per-invocation operator control;
- keep chat and summarize under one shared capability-neutral contract;
- preserve topology blindness, existing routing, and existing fallback;
- preserve privacy-safe failure behavior; and
- avoid ambient, durable, or per-topology timeout policy.

## Non-goals

This RFC does not propose:

- changing the default from 120.0 seconds;
- an infinite timeout, disabled timeout, or zero-as-disabled value;
- environment, TOML, project, or user configuration;
- a static-cluster startup, receiver, remote-node, adapter, runtime, model, or
  capability timeout;
- server, runtime, or adapter timeout changes;
- per-capability, per-model, per-runtime, per-node, per-remote, or
  hardware-specific policy;
- retries, client-side fallback, request duplication, cancellation, streaming,
  partial results, background jobs, request tracking, persistence, lifecycle
  management, or supervision;
- changes to status, health, preflight, Uvicorn, ASGI, Ollama, llama-server,
  the internal request protocol, LAN exposure, authentication, attribution,
  routing, or fallback; or
- implementation, tests, operator documentation, roadmap work, or Phase 19
  work in this RFC PR.

## Proposal

### Public forms

The ordinary native client parsers should accept one optional value:

```text
--timeout-seconds SECONDS
```

After a separate implementation, the option has identical meaning for these
current public forms:

```sh
hac chat --timeout-seconds 300 "Hello"
home-ai-cluster chat --timeout-seconds 300 "Hello"
hac summarize --timeout-seconds 300 --text "Source text"
home-ai-cluster summarize --timeout-seconds 300 --text "Source text"
home-ai-cluster-chat --timeout-seconds 300 "Hello"
```

`hac` and `home-ai-cluster` delegate to the same root command and then to the
same chat or summarize command parser. `home-ai-cluster-chat` is an existing
standalone public chat executable using that same chat parser, so it receives
the same chat behavior. There is no standalone summarize executable; this RFC
does not create one.

No option is added to `static-cluster`, `local`, receivers, declarations,
adapters, runtime commands, status, health, preflight, or compatibility.

### Default and ownership

When omitted, the selected value remains:

```text
120.0 seconds
```

The value applies to exactly one one-shot client invocation. It is not
persisted and is not inherited from environment variables, TOML, static-cluster
or remote-node declarations, runtime/model/capability configuration, or user
or project configuration files.

The option controls only the ordinary client's wait for its existing fixed
loopback HTTP endpoint. The client remains topology-blind: it does not know
whether the running caller process executes locally or through a declared
remote, whether fallback occurs, or which adapter, runtime, model, node, or
hardware eventually handles the request.

### HTTPX scalar semantics

The selected value retains the current scalar construction semantics:

```python
httpx.Client(timeout=<selected seconds>)
```

It applies equally to HTTPX pool, connect, write, and read timeout categories.
It is not a strict total command deadline; total command duration can exceed
the selected number because the scalar applies to individual timeout categories
and operations. It is not a server, runtime, model, remote-node, or
cancellation timeout.

### Validation and local failure

`SECONDS` is one decimal number of seconds satisfying:

```text
1 <= SECONDS <= 3600
```

Valid examples include `1`, `120`, `300`, `300.5`, and `3600`. Missing values,
malformed text, non-finite values, zero, negative values, values below `1`, and
values above `3600` are invalid. Seconds are the only unit; duration strings
such as `5m` and `2h` are not accepted.

The parser must reject invalid values before constructing an HTTP client or
sending a request. Current ordinary client parser failures already produce no
standard output, the stable safe line below on standard error, and exit 2:

```text
error: invalid request input
```

An implementation should retain that existing bounded argument-failure contract
rather than introduce a timeout-specific error taxonomy or generic duration
parser.

### Request, failure, and cancellation behavior

Each valid invocation still sends at most one ordinary request. The option does
not add automatic retry, client-side fallback, request duplication, background
continuation, or a routing change. Existing capability eligibility, local-first
selection, bounded fallback, result attribution, and successful output remain
unchanged.

The existing safe failure translations remain unchanged:

```text
timeout:    error: ordinary request timed out
connection: error: ordinary cluster unavailable
other:      error: ordinary request failed
```

Failures must not expose raw exceptions, URLs, addresses, prompts, source text,
generated text, credentials, or runtime details.

A client timeout does not prove that the caller process, remote receiver, or
runtime cancelled the work. This RFC adds no cancellation, idempotency, request
ID, completion tracking, queue, lifecycle, or supervision contract. A later
operator proof must not immediately repeat a timed-out request unless the
operator knowingly accepts that each invocation can create additional work.

### Server and transport boundary

This RFC changes neither the static caller-to-remote request timeout ownership
nor receiver-to-runtime inference timeout ownership. In particular, it retains
the accepted `timeout=None` inference paths, separate status and health
observation boundaries, and all existing server, transport, runtime, and
protocol behavior.

## Rationale

The existing 120.0-second default remains a reasonable ordinary feedback
boundary. One slow-but-valid workload does not establish that every operator
should wait longer when a request is stalled or unavailable. Hardware, model,
input size, cold-load state, and runtime conditions vary, while the ordinary
client's waiting preference belongs to the invoking operator.

An explicit per-invocation override is visible in shell history and scripts,
creates no ambient configuration or precedence, and does not contaminate
static topology declarations with performance expectations. It permits a
slow-but-valid request to wait longer while retaining finite behavior and one
shared client contract. It does not guarantee completion.

## Alternatives considered

### Keep fixed 120 seconds

Rejected. The concrete observation demonstrates that it is insufficient for at
least one legitimate accepted workload.

### Increase the shared fixed default

Rejected for this proposal. No universal replacement value is established, and
a larger default delays feedback for every stalled or unavailable long-running
request.

### Remove the timeout

Rejected. Ordinary commands could block indefinitely.

### Environment variable or configuration file

Rejected. Either creates ambient hidden policy, precedence, and durable
configuration behavior beyond one invocation.

### Static-cluster TOML, remote-node, or startup timeout

Rejected. These configure the wrong ownership boundary: a topology declaration
owns eligibility and transport address, while the timed-out boundary belongs to
the one-shot loopback client. They would also mix performance expectations into
topology or long-running caller-process policy.

### Summarize-only or other capability-specific timeout

Rejected. The waiting boundary is shared and capability-neutral; one slow
summarize observation does not justify making ordinary client contracts drift.

### Read-only timeout

Rejected for this RFC. It changes the accepted scalar semantics and introduces
a lower-level HTTP policy not required by the evidence.

### Strict total deadline

Rejected. It has different elapsed-time meaning and may require cancellation
semantics that this RFC deliberately does not add.

### Infinite or zero-as-disabled value

Rejected. Ordinary client commands must remain finite.

### Generic configuration framework

Rejected as premature and unnecessary for one explicit option.

## Trade-offs

Users and scripts gain one durable public option and validation contract.
Different invocations may choose different, still-finite waits, and an operator
can choose an excessively patient value up to one hour. Timeout still cannot
prove that remote work stopped. The generous but finite maximum is simpler than
ambient configuration or per-topology policy.

## Impact

After acceptance, a separate implementation PR may make only the smallest
necessary changes to the shared ordinary-client argument parsing seam, HTTPX
client construction, focused tests, command reference, and operator
documentation. It must not create a general client or timeout framework.

This RFC would amend only RFC-0055's configurable-timeout portions while
retaining its 120.0-second default, shared scalar semantics, failure
translations, topology blindness, no-retry behavior, and server/runtime
ownership boundaries. RFC-0045's chat invocation boundary, RFC-0049's chat
presentation, and RFC-0054's summarize behavior otherwise remain unchanged.

## Later implementation evidence

A later implementation must prove at minimum that:

1. omission passes 120.0 to HTTPX for chat and summarize;
2. one explicit valid value reaches HTTPX for chat and the same value reaches
   HTTPX for summarize;
3. both root executable names and the standalone chat executable expose the
   accepted chat behavior;
4. the minimum, maximum, and decimal finite values are accepted;
5. zero, negative, malformed, non-finite, below-minimum, and above-maximum
   values fail before HTTP client construction and send no request;
6. each valid invocation sends at most one request;
7. timeout, connection, generic request failure, and success behavior remain
   unchanged; and
8. no topology, capability, runtime, model, or remote timeout option appears.

A bounded privacy-safe operator proof should demonstrate:

```text
a legitimate request exceeding 120 seconds
+ one explicit larger finite timeout
-> successful completion
```

The proof must retain no prompt, source text, generated output, real address,
hostname, username, filesystem path, model identifier, runtime URL, hardware
identifier, raw log, token, or credential. A real one-hour timeout-path test is
not required.

## Open questions

Pending review of this draft, including whether the selected upper bound and
decimal representation are the smallest useful durable validation contract.

## Decision

Pending.
