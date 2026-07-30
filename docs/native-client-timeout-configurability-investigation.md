# Native Client Timeout Configurability Investigation

Status: Complete

## Context

RFC-0055 establishes one shared, fixed, implementation-owned 120.0-second
HTTPX scalar timeout for the ordinary native `chat` and `summarize` clients.
It deliberately rejected an operator timeout option, environment setting,
configuration-file setting, and capability-, runtime-, or model-specific
policy. This investigation follows a concrete ordinary operator observation;
it does not change that accepted contract, create an RFC, or authorize
implementation.

## Concrete operator observation

The caller ran ordinary `hac static-cluster` with a caller-local `chat`
restriction and one declared `summarize` remote. A legitimate summarize request
was therefore routed directly to the eligible declared remote, without a local
summarize attempt, fallback, selector, or scheduler.

That request reached the current ordinary-client timeout on three separate
command invocations. The retained observation identifies neither the receiver
nor its address, runtime, model, hardware, input, output, path, timestamp, or
log data.

## Investigation question

> Does the concrete slow-remote summarize observation establish a bounded need
> to make the ordinary native client waiting timeout operator-configurable, and
> what is the smallest coherent contract boundary if it does?

## Current accepted contract

RFC-0055 is implemented directly in `chat_command.py`: its shared
`_REQUEST_TIMEOUT_SECONDS` is `120.0`, and `summarize_command.py` imports and
uses that same value. Both synchronous clients pass the scalar to
`httpx.Client`, make exactly one fixed-loopback request to an already-running
ordinary process, do not retry, and translate every `httpx.TimeoutException`
to `error: ordinary request timed out`. `httpx.ConnectError` remains
`error: ordinary cluster unavailable`.

The default is topology-blind: the client has no declared-remote, runtime,
model, capability, or routing option. It works the same against local-only and
static-cluster caller processes. RFC-0055 does not promise cancellation when a
client stops waiting.

## Current implementation ownership

The current source has distinct timeout owners. They are not one end-to-end
deadline:

| Boundary | Current owner and behavior |
| --- | --- |
| One-shot client to its loopback caller process | `chat_command` owns the shared 120.0 scalar; `summarize_command` reuses it. |
| Static caller to declared remote internal request | `create_static_cluster_http_client()` constructs `httpx.AsyncClient(timeout=None)`. `HttpRemoteTransport` supplies no per-request timeout. |
| Receiver adapter to its runtime inference request | Both Ollama and llama-server adapters use `httpx.AsyncClient(timeout=None)` for chat and summarize inference. |
| Remote status observation | `HttpRemoteStatusTransport` owns a separate fixed 5.0-second observation timeout. |
| Local health observation | Adapter health uses an ordinary synchronous HTTPX client with its library default timeout; it is a finite probe, not inference execution. |

Status and health are finite, read-only observations. Their short observation
boundaries neither govern an accepted request nor demonstrate that a request
will later finish in the same interval.

## End-to-end timeout path

For the reported topology, the relevant path is:

```text
hac summarize
  -> fixed caller loopback native endpoint
  -> static-cluster capability routing
  -> eligible declared remote
  -> receiver internal endpoint
  -> receiver-local runtime adapter
  -> normalized response
```

The caller-local capability declaration excludes the caller-local node before
selection, so this case does not depend on local runtime failure or fallback.
The caller-to-remote and receiver-to-runtime request clients are currently
unbounded. Consequently the first explicit waiting boundary on that path is
the one-shot client's 120.0-second loopback wait. It is the most plausible
source of the reported client failure.

That is a reasoned inference, not complete lifecycle observation. Current
output and source do not establish whether the remote request was transmitted,
whether the receiver had begun inference, or whether work stopped after the
caller-side client stopped waiting.

## Current observability limits

The clients safely report only a timeout category. They do not expose or retain
request content, response content, addresses, runtime details, or exception
details. There is no project-owned request-stage log, correlated request ID,
idempotency key, cancellation protocol, or completion observation after a
client timeout.

Those limits are intentional privacy and lifecycle boundaries. Better
diagnosis must not be smuggled in through prompt logging, response logging, or
request tracking.

## Repeated invocation consequences

Each command invocation creates one new ordinary request. It is not an accepted
retry of a known request, and no invocation is correlated with a previous one.
Because timeout does not prove cancellation at the caller, receiver, or
runtime, immediately invoking the command three times may create additional
runtime work while earlier work may still exist.

This is an operational caution, not evidence for automatic retry, idempotency,
cancellation, queues, background jobs, supervision, or lifecycle ownership.
Each of those would be a separate architectural question.

## Candidate configuration boundaries

| Candidate | Ownership and meaning | Assessment |
| --- | --- | --- |
| One explicit per-invocation ordinary-client input shared by chat and summarize | How long this one loopback client waits for one complete result; preserves topology blindness and leaves server/runtime behavior untouched. | Smallest credible contract to investigate. It needs RFC-defined syntax, finite validation, and default behavior. |
| Summarize-only input or capability-specific values | Makes the waiting contract depend on capability rather than the common non-streaming client boundary. | Not justified by one slow summarize observation; it would make the two ordinary clients drift. |
| Environment value or project configuration file | Creates ambient or durable policy, precedence, discovery, and documentation questions beyond one invocation. | Larger configuration authority without evidence that a per-invocation need cannot be met. |
| Static-cluster startup input | Configures a long-running caller process rather than the one-shot client that timed out. | Wrong owner for the observed boundary and changes process behavior for every caller. |
| Static topology TOML or remote-node field | Would associate waiting policy with a declared remote address or expected hardware behavior. | Wrong hop and wrong data domain; see the static declaration assessment. |
| More specific read timeout | Can better express response waiting but changes the established scalar semantics and requires a distinct HTTP contract. | Not selected merely because the observed non-streaming wait is plausibly a read wait. |
| Strict total deadline | Has a materially different meaning from HTTPX's current scalar and needs cancellation/elapsed-time semantics to be stated honestly. | Separate architectural decision; do not relabel a scalar as a total deadline. |
| Different fixed default only | Keeps RFC-0055's implementation-owned boundary. | A credible RFC alternative: the repeated observation establishes that the current fixed boundary is insufficient, but does not select a replacement or configurability. |
| No public configuration | Retains the existing accepted fixed contract. | Insufficient for the demonstrated legitimate request that repeatedly exceeds it. |

Every public configuration alternative changes the ordinary client contract and
therefore requires an RFC before implementation. A familiar spelling such as
`--timeout` is not itself a decision.

## Static declaration assessment

Static remote declarations own caller-authorized eligibility and a transport
address. They do not describe measured hardware performance, runtime policy,
or a one-shot client's waiting preference. A timeout in a `[[remote_nodes]]`
entry would incorrectly make expected remote performance into topology data and
would still not configure the timed-out loopback client hop.

The relevant distinction is:

```text
remote declaration
  -> caller-owned eligibility and transport address

ordinary client waiting timeout
  -> how long one one-shot client waits for its local caller process
```

No static declaration, remote transport, receiver adapter, runtime, model, or
hardware field should be added for this correction.

## Shared versus capability-specific policy

RFC-0055 deliberately uses one shared value because both clients await one
complete non-streaming result from the same ordinary process boundary. The new
observation proves that the current common fixed value can be too short in a
valid routed summarize case. It does not prove that summarize needs a different
policy, that chat would not also need more time, or that runtime/model facts
belong at the client edge.

One shared optional per-invocation ordinary-client waiting value is the leading
smallest credible RFC candidate, with omission preserving 120.0. It would apply
identically through `hac` and `home-ai-cluster`, and preserve chat/summarize
output, failure, routing, and fallback behavior. A revised implementation-owned
fixed default remains an RFC alternative. This investigation selects neither
alternative, syntax, nor value.

## HTTPX semantic considerations

The installed dependency is HTTPX 0.28.1. Direct inspection confirms that
`httpx.Timeout(120.0)` sets pool, connect, write, and read to 120.0 seconds.
Accordingly, `httpx.Client(timeout=<scalar>)` is a per-operation scalar, not a
strict total command deadline. Total elapsed time can span those operations and
multiple reads.

An operator entering a number might reasonably expect a total deadline, a read
timeout, or the existing scalar semantics. An RFC must choose and document one
truthful meaning rather than silently changing the current one. Retaining the
existing scalar is the smallest compatibility-preserving candidate; selecting
a read-only or total-deadline contract would be a different decision.

## Validation and finite-boundary considerations

Any later public input must preserve finite commands. The RFC should decide a
small validation contract, including units, integer or decimal representation,
minimum and maximum finite values, zero, negative and malformed input,
excessively large values, safe local failure output, and whether omission keeps
the accepted 120.0 default. It should also require invalid input to fail before
HTTP client construction.

This does not call for a generic duration parser, environment precedence,
per-runtime policy, or a timeout framework.

## Compatibility

A shared optional per-invocation value could preserve existing invocations by
leaving omission at 120.0. It must preserve both root executable names, one
request/no retry, fixed loopback destination, topology blindness, local-only
and static-cluster behavior, existing routing and fallback, success output,
safe timeout text, and exit behavior. It must not imply runtime cancellation
or alter the unbounded caller-to-remote and receiver-to-runtime ownership.

## Privacy and security

The retained observation contains only the structural caller-local/eligible
remote topology and repeated-timeout fact. This document contains no real
address, machine name, username, credential, token, prompt, source text,
generated response, path, model identifier, runtime URL, hardware identity,
timestamp, or raw log.

## Testability and later proof boundary

If an RFC accepts a public ordinary-client timeout input, a later small
implementation should add only focused evidence that:

- omission retains 120.0;
- one valid explicit finite value reaches ordinary HTTPX client construction;
- invalid values fail before client construction;
- chat and summarize share the accepted input contract;
- timeout text and exit behavior remain unchanged;
- each invocation still sends at most one request and no topology or runtime
  option reaches the clients; and
- a privacy-safe real slow remote request exceeding 120 seconds completes
  within one explicit larger finite client boundary.

The proof must retain no request/response content, topology values, paths,
model/runtime identifiers, hardware identity, or raw logs. It must not claim
cancellation or absence of server-side work after client timeout.

## RFC classification

**Outcome C — a bounded architectural contract change is required.**

The concrete repeated timeout of a legitimate ordinary routed request
establishes that the accepted fixed 120.0-second boundary is insufficient for
at least one accepted ordinary use. Any change to that accepted fixed timeout
contract changes public waiting, validation, and compatibility behavior and
therefore requires an RFC before implementation.

One shared explicit per-invocation finite timeout is the smallest credible
candidate identified here. A revised implementation-owned fixed boundary
remains an RFC alternative. This investigation does not select between them.

The smallest RFC question is:

> What is the smallest finite shared ordinary native-client waiting contract
> that supports demonstrated slow-but-valid workloads: an explicit
> operator-selected timeout preserving the 120-second default, or a revised
> implementation-owned fixed boundary, while preserving topology blindness, no
> retry, and unchanged server/runtime timeout ownership without capability-,
> model-, runtime-, remote-, or topology-specific policy?

## Conclusion

The observation does not justify remote topology timeout data, capability-
specific policy, environment/configuration policy, retries, cancellation,
streaming, background work, or runtime lifecycle changes. It does justify a
narrow RFC to reconsider the shared ordinary-client waiting boundary. Shared
per-invocation configurability is the leading candidate, not a selected
solution; a revised implementation-owned fixed boundary remains an alternative.
No behavior is changed by this document.
