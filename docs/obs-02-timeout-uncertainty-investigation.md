# OBS-02: Timeout Uncertainty Investigation

Status: Investigation

Date: 2026-10-12

## Question

Does an active-request explanation client timeout require a correction to the
current operator experience? This investigation uses verified
`origin/post-1.1-development` at `1333abf7abff6053a33bdbd4eaf70e8f4489655b`.
It establishes no new architecture.

## Observed evidence

On 2026-10-12, an operator submitted two overlapping local-only explained Chat
requests with `--timeout-seconds 180` in a real static cluster. Both clients
printed `error: request explanation timed out` and exited 1. A third explained
Chat request selected local, observed local `execution-permission-denied`,
continued within the same request to a declared remote, and succeeded there.
This demonstrates continuation after local permission denial. It does not
establish whether either timed-out request completed, was cancelled, or
continued in the runtime. No request lifecycle trace for those two requests was
retained, and none is reconstructed here.

## Accepted architectural contracts

- [RFC-0055](../RFC/RFC-0055-ordinary-native-client-timeout.md) and
  [RFC-0060](../RFC/RFC-0060-explicit-native-client-timeout.md) define the
  HTTPX scalar as separate pool, connect, write, and read timeouts, not a
  strict end-to-end deadline. A client timeout does not prove server or runtime
  cancellation.
- [RFC-0145](../RFC/RFC-0145-ordinary-request-lifecycle-explanation.md)
  owns facts from one ordinary request. [RFC-0149](../RFC/RFC-0149-bounded-active-process-actual-request-explanation-carrier.md)
  makes the active carrier effectful and requires the existing disconnect
  boundary. [RFC-0150](../RFC/RFC-0150-active-request-explanation-thin-client.md)
  fixes one POST, no retry, the safe timeout error, and a repeated invocation
  as a new business request. [RFC-0153](../RFC/RFC-0153-human-readable-active-diagnostics-output.md)
  changes presentation only; it explicitly leaves OBS-02 unanswered.
- [RFC-0082](../RFC/RFC-0082-client-disconnect-cancellation-for-ordinary-requests.md)
  cancels pending HAC-owned work only after the ASGI edge **confirms** that
  request's disconnect. An HTTPX timeout is not itself confirmation at that
  edge. An already terminal HAC result wins over a simultaneously observed
  disconnect. If disconnect wins, HAC cancels and unwinds its pending task and
  discards late results; downstream runtime termination is not guaranteed.
- [RFC-0105](../RFC/RFC-0105-bounded-hac-execution-concurrency-limit.md)
  counts HAC-owned execution intervals, not runtime work. An interval ends
  when HAC stops awaiting adapter invocation, even if underlying runtime work
  continues. A released interval can therefore permit another HAC request
  while earlier runtime work remains.

## Current implementation

The [CLI](../src/home_ai_cluster/commands/active_request_explanation.py)
parses one optional integer timeout through the shared RFC-0060 parser
(`1..3600`, default `120`), constructs `httpx.Client(timeout=<selected>,
follow_redirects=False, trust_env=False)`, and sends one POST. Any
`httpx.TimeoutException` maps to the exact safe timeout line, empty stdout,
and exit 1. There is no client retry. The line accurately describes failure
to obtain a completed account within an HTTPX timeout category; it makes no
claim about business completion or cancellation.

The [active carrier](../src/home_ai_cluster/api/actual_request_explanation.py)
validates before execution, uses the active local or static composition, and
passes that same business execution to
[`run_routable_execution`](../src/home_ai_cluster/api/client_disconnect.py).
That helper checks `Request.is_disconnected()`, observes for a confirmed
disconnect, gives an already completed execution priority, cancels a pending
execution task when disconnect wins, and discards its result. The carrier
propagates `ConfirmedClientDisconnect`; it does not turn cancellation into a
completed explanation account. The [local executor](../src/home_ai_cluster/core/executor.py)
releases a granted [execution interval](../src/home_ai_cluster/core/execution_intervals.py)
in `finally` when adapter awaiting unwinds. The
[remote transport](../src/home_ai_cluster/core/remote_transport.py) awaits its
outbound HTTP request; cancellation can propagate through that coroutine, but
neither the coordinator nor the receiver can infer runtime termination from
that propagation. The static-cluster remote client and local runtime adapter
inference clients use `timeout=None`; the CLI scalar is not their deadline.

## Client, HAC, and runtime ownership

After the two observed timeouts, the clients knew only that they received no
completed validated account and exited with the safe error. They could not
know whether the server had received or finished either request, whether an
ASGI disconnect was confirmed, or whether local or remote runtime work had
stopped. HAC's confirmed-disconnect rule applies if its own ASGI observation
occurs while execution is pending; the observed client exits alone do not
establish that precondition. HAC interval release records the end of HAC's
awaited adapter invocation, not runtime termination.

## Existing test evidence

[CLI tests](../tests/test_active_request_explanation.py) cover the one POST,
default and explicit scalar, invalid timeout rejection, safe `ReadTimeout`
translation, no retry, and empty stdout on client failure.
[Disconnect tests](../tests/test_client_disconnect_cancellation.py) cover
pre-existing disconnect, pending-task cancellation, completion precedence,
late-result discard, and parent cancellation.
[Carrier tests](../tests/test_actual_request_explanation_carrier.py) exercise
the active composition, local permission-denial continuation, and a confirmed
pre-execution disconnect without an account. [Route tests](../tests/test_client_disconnect_routes.py)
and [interval tests](../tests/test_execution_intervals.py) cover registered
ordinary disconnect handling and interval cardinality. These deterministic
tests support the implementation path; they do not establish what happened to
the two live timed-out requests or prove runtime termination.

## Operator documentation

The [command reference](command-reference.md#hac-explain-active-request)
states that this is a real business request, the timeout is client-side, there
is no automatic retry, execution may already have happened, and repeating the
command submits new work. The [Incus runbook](incus-loopback-receiver-runbook.md#troubleshooting)
names the exact error and warns against inferring completion, cancellation, or
a safe retry. The [operator workflow](operator-workflow.md) explains the same
timeout uncertainty for ordinary one-shot commands; it does not specifically
cover this diagnostic command, which the command reference already covers.
Together the current guidance is adequate for the observed operator case.

## Assessment

No evidence shows a violated accepted contract. The observed successful third
request is consistent with the accepted local-permission and remote-continuation
rules. The two timeout exits are consistent with the accepted client waiting
boundary and leave server and runtime outcomes unknown. The existing CLI error
is truthful and is an accepted public string under RFC-0150; changing it would
require a new RFC to amend that public client contract, but no such change is
justified by this evidence.

## Outcome

**A — Current behavior and documentation are sufficient.** Close OBS-02 with
no change beyond retaining this investigation. Outcome B is rejected because
the command reference and runbook already state the manual-repeat risk.
Outcome C is rejected because the accepted error makes no false lifecycle
claim. Outcome D is rejected because the active carrier uses the accepted
disconnect seam and no contrary source or test evidence was found.

## Recommended next step

Review and retain this record, then close OBS-02. No RFC or implementation
repair is supported by the available evidence.

## Non-goals

This investigation does not add request identity or tracking, polling,
persistence, background work, queues, distributed cancellation, retries,
runtime kill commands, server deadlines, new error infrastructure, a dashboard,
or prompt/response logging. It does not infer missing lifecycle events from a
client timeout.
