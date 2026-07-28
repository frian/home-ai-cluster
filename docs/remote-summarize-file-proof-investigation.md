# Remote Summarize File Proof Investigation

Status: Complete

Date: 2026-07-28

## Scope and basis

This is an investigation only. It neither runs the proof nor changes the CLI,
request models, routing, transport, runtime adapters, RFCs, roadmap, or Phase
19.

The requested starting commit, `3c371a0fab0e07c19457de74c24badbfa0cec331`,
was fetched from `origin/main` before this investigation branch was based on
it. The working tree was clean before the branch was created.

The question is whether the following can be demonstrated by composing current
ordinary behavior:

```text
local regular UTF-8 file
  -> hac summarize --file
  -> caller-local static cluster
  -> accepted pre-request local fallback
  -> one declared remote receiver
  -> remote summarize execution
  -> caller-normalized result with caller-declared attribution
```

## Existing behavior inventory

| Component | Accepted contract | Current implementation | Change needed? |
| --- | --- | --- | --- |
| Caller `hac summarize --file` | RFC-0054, RFC-0055, RFC-0056, RFC-0057 | `summarize_command.py` | No |
| Caller ordinary static cluster | RFC-0038, RFC-0040 | `static_cluster.py` | No |
| Caller local runtime adapter | RFC-0003, RFC-0028 | `adapters/ollama.py`, local composition | No |
| Caller declared remote adapter | RFC-0013, RFC-0014, RFC-0038, RFC-0040 | `core/remote_transport.py`, static wiring | No |
| Caller routing and bounded fallback | RFC-0028, RFC-0040 | `core/ordered_remote_fallback.py` | No |
| Ordinary receiving application | RFC-0037, RFC-0051 | `main.py`, `api/routes.py` | No |
| Receiver runtime adapter | RFC-0003, RFC-0051 | local composition and runtime adapter | No |
| Native summarize endpoint | RFC-0051 | `POST /v1/summarize` in `api/routes.py` | No |
| Normalized request and result | RFC-0051, RFC-0023 | `core/models.py` | No |
| Result output projection | RFC-0049, RFC-0054 | `chat_command.py`, reused by `summarize_command.py` | No |

The caller is an ordinary `hac static-cluster` process. The receiver is an
ordinary `hac local --host 0.0.0.0 --port 8000` process with an operator-owned
runtime already running. Neither process starts, stops, repairs, or supervises
the external runtime or the other machine.

## Source ownership

`_read_bounded_file()` in `summarize_command.py` interprets the `--file` value
with ordinary process path semantics, verifies a regular file before and after
open, reads bounded bytes, and strictly decodes UTF-8. `_parse_input()` then
constructs `SummarizeRequest(text=...)` before `_post_native_request()` can
construct an HTTP client.

Consequently:

- The path is interpreted and bytes are read only by the caller-side CLI.
- Strict UTF-8 decoding happens before HTTP-client construction.
- Only decoded text enters `SummarizeRequest`; that model has `text` and
  constraints, not a filesystem-path field.
- The public native serializer includes only `text`.
- The remote serializer creates a tagged normalized summarize envelope from
  `SummarizeRequest`; it also has text and constraints, not the source path.
- The caller-local process, remote adapter, receiver, runtime, normalized
  result, and supported history have no path field to receive or report.

Focused evidence is in `tests/test_summarize_command.py`: a valid regular file
makes one loopback native request whose body is exactly `{"text": ...}`;
invalid files fail before a client is constructed; and each output mode preserves
the same request. `tests/test_routes.py` covers the tagged internal summarize
envelope and receiver-local execution. Existing Phase 18 evidence records that
summarize creates no supported history entry. This does not make shell history,
terminal scrollback, or operator-created logs project-controlled storage.

## Expected request path

The actual sequence has two different endpoint shapes:

```text
caller CLI reads regular file bytes
  -> strict UTF-8 decode
  -> SummarizeRequest(text)
  -> POST http://127.0.0.1:8000/v1/summarize with {"text": text}
  -> caller static-cluster routing, local candidate first
  -> caller local adapter connection unavailable before transmission
  -> one declared remote candidate
  -> POST <declared-base-url>/internal/cluster/request
       with tagged normalized summarize envelope
  -> receiver validates and reconstructs SummarizeRequest
  -> receiver local routing and runtime summarize execution
  -> receiver ClusterResult
  -> caller overwrites node_id with declared remote node ID
  -> CLI validates ClusterResult and projects selected output mode
```

`HttpRemoteTransport` owns the second URL and envelope. The receiver's
`/internal/cluster/request` route is not `/v1/summarize`: it receives the
cluster-internal tagged envelope and executes it locally. The caller's
`/v1/summarize` route is the native public endpoint used by the ordinary CLI.

## Local failure setup

The smallest truthful setup is to stop only the caller's external local runtime
after static declaration validation and receiver readiness checks, while leaving
the caller static-cluster process running. Do not alter the declaration, local
node, capabilities, or code to force remote selection. The receiver application
and its external runtime remain available.

The accepted fallback condition is specifically a failed local runtime
connection before request transmission (`RuntimeConnectionUnavailableBeforeRequestError`),
not a timeout, HTTP error, runtime result, or other ambiguous failure. The local
adapter maps the connection-establishment failure to that condition; ordered
fallback then attempts the already discovered remote candidate once. Focused
tests establish this classification and prohibit fallback for ambiguous errors.

An operator can truthfully show the precondition by stopping only the caller
runtime before the request and, if desired, observing caller local health as
unavailable before starting the caller process. A completed live run cannot,
from the ordinary CLI result alone, independently prove an internal exception
classification; it must not claim more than that controlled precondition plus
the documented tested fallback behavior.

## Receiver setup

On the receiving machine, start the supported local composition with a runtime
that provides `summarize` (the current ordinary choices are Ollama or explicit
llama-server composition) and a required model already available. Start:

```sh
hac local --host 0.0.0.0 --port 8000
```

The receiving Home AI Cluster process owns port 8000 and exposes its native and
internal endpoints. The external runtime remains operator-owned. This is an
explicit trusted-LAN exposure: restrict any firewall allowance to that LAN and
remove it afterward. Use placeholders for declaration location, receiver
address, model, and every machine-specific value.

The caller declaration contains exactly one declared node ID and base URL. The
ordinary static constructor gives that declaration `chat` and `summarize`
capabilities; topology does not configure a runtime or directly target a node.

## Attribution

The receiver's own ordinary local node identity, its runtime adapter label, and
its runtime model are distinct from the caller's declared remote node ID. The
receiver initially returns its local `ClusterResult`. At caller-side declared
remote execution, `execute_declared_remote_routing_candidate()` replaces only
`node_id` with `candidate.node.id`, which came from the caller declaration.

RFC-0023 makes the selected candidate, rather than a receiver self-report,
transport address, adapter, or model, authoritative for final cluster node
attribution. The final caller result should therefore contain the caller-declared
remote node ID.

## Output recommendation

All modes make one native loopback request and validate the same result:

| Invocation | Evidence | Recommendation |
| --- | --- | --- |
| `hac summarize --file <PATH>` | Summary content only | Not sufficient for attribution |
| `hac summarize --file <PATH> --verbose` | Human-readable `Node`, adapter, and optional model | Primary live proof output |
| `hac summarize --file <PATH> --json` | Compact complete `ClusterResult`, including `node_id` | Optional structured corroboration; do not repeat generation solely for it |

Use one actual remote generation with `--verbose` as the minimum proof set. It
visibly projects the declared node attribution without retaining a raw response
body. `--json` is useful only if a later proof needs a machine-readable
privacy-sanitized structural result; it should not require a second generation.

## Observation strategy and limit

Use existing operator surfaces only:

- Record one CLI invocation and its success/exit observation, not source or
  summary text.
- Temporarily observe the caller process access line for one
  `POST /v1/summarize` and the receiver process access line for one
  `POST /internal/cluster/request`; do not retain raw logs, addresses, or
  payloads.
- Keep exactly one declared remote and do not re-invoke the command.
- Record the verbose `Node` field as the sanitized declared node ID.
- Use the stopped caller runtime as the controlled pre-request condition, then
  restore it manually after the observation.

This establishes a real end-to-end execution and can observe one caller native
request and one receiver internal request. Current ordinary surfaces do not
provide correlated request IDs, durable attempt counters, or a public event for
the local adapter's precise pre-transmission exception. A temporary HTTP wrapper
is unnecessary and would not improve the ordinary proof. Exact-once traversal,
no retry, the narrow connection category, envelope shape, and caller-owned
attribution are instead established by existing focused automated tests,
especially `tests/test_ordered_remote_fallback.py`,
`tests/test_static_cluster.py`, `tests/test_routes.py`, and
`tests/test_summarize_command.py`.

## Privacy boundary

The later runbook and retained result must not retain source text, generated
summary, file path, base URL, LAN address, hostname, username, runtime URL,
raw exception, request or response payload, model path, credential,
authorization value, or hardware detail. Use a temporary public non-sensitive
UTF-8 file and remove it after the live observation.

Safe retained evidence is limited to command shapes with placeholders, stable
field names, declared node attribution, stable failure categories, success or
failure observations, and request-count observations without content. Do not
retain raw process logs; they may contain addresses or other private context.

## Decision matrix

| Question | Evidence | Conclusion | Change required? |
| --- | --- | --- | --- |
| File read location | `summarize_command.py`; focused file tests | Caller CLI only | No |
| Path transmission | Public/internal serializers and request models | No path leaves caller CLI | No |
| Caller-local endpoint | `_ORDINARY_SUMMARIZE_URL`; client tests | `POST 127.0.0.1:8000/v1/summarize` | No |
| Local pre-request failure | RFC-0028; ordered fallback tests | Only connection-unavailable condition advances | No |
| Remote request endpoint | `HttpRemoteTransport` | `POST <base-url>/internal/cluster/request` | No |
| Receiver execution | `internal_cluster_request`; route tests | Receiver executes locally through its runtime adapter | No |
| Remote attribution | RFC-0023; executor and fallback tests | Caller declaration supplies final `node_id` | No |
| Exact-once evidence | Focused orchestration tests; transient access observations | Tests prove exactness; live proof observes endpoints but lacks correlated counters | No |
| Privacy-safe retention | CLI failures, existing proof guidance, no-history tests | Retain structural observations only | No |
| RFC requirement | All behaviors are accepted and implemented | No new decision is exposed | No |

## Classification, RFC requirement, and recommendation

This is correctly classified as a **standalone post-roadmap native summarize
remote integration proof**, not Phase 19. It composes already accepted file
input, native summarize access, static topology, fallback, transport, receiver
execution, attribution, and output behavior. It adds no capability,
architecture, CLI behavior, transport, routing policy, fallback rule, or
Phase 19 scope.

No RFC is required if the proof stays within this composition. A new RFC would
be required only if execution exposes a contradiction needing a new durable
decision; none was found in this investigation.

**Outcome B — Proof-ready with evidence limitation.** The live path is
executable with the installed ordinary CLI and ordinary static-cluster process.
It can demonstrate one real file-backed remote generation and declared-node
attribution. Exact attempt counts and the pre-transmission classification should
be reported truthfully as a combination of controlled live observations and the
existing automated guarantees, not as new live telemetry.

If the later proof proceeds without implementation, create exactly these two
documentation artifacts then:

- `docs/remote-summarize-file-proof-runbook.md`
- `docs/remote-summarize-file-proof.md`
