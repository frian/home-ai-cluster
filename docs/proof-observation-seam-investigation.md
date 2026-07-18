# Proof Observation Seam Investigation

Status: Investigation only

## 1. Purpose

This investigation examines the blocker in the planned Aider static-cluster
proof: how to establish, for one live two-machine Aider invocation, both one
accepted compatibility request and the caller-owned declared-node attribution
of its normalized result.

It does not execute a proof, change code, add a process mode, or decide an
architecture. The question is deliberately narrow:

> What is the smallest privacy-safe observation seam that can correlate one
> live accepted compatibility request with its internally attributed declared
> remote result without changing RFC-0031 or creating durable operational
> observability?

## 2. Current proof blocker

The planned runbook correctly requires more than evidence that a receiver was
available. A successful claim needs a causal chain from one accepted Aider
compatibility request to one caller-owned normalized `ClusterResult` whose
`node_id` is the declared remote node.

The public RFC-0031 response intentionally omits `node_id`, adapter, routing,
and topology. A successful compatibility HTTP response therefore proves only
that the edge completed a request. It cannot, by itself, establish that the
caller assigned the declared remote node ID to the result.

## 3. Required facts

The stronger proof requires these correlated facts for one process lifetime:

1. one RFC-0031 request passed strict compatibility validation;
2. that request entered the existing ordinary static-cluster request path;
3. its caller-local candidate failed under the existing pre-execution fallback
   condition;
4. existing traversal reached the one declared receiver; and
5. the returned normalized `ClusterResult` was caller-owned and had the
   declared remote node ID.

The observations have different owners:

| Fact | Owner | Required observation boundary |
| --- | --- | --- |
| Aider process started once | Aider client | Client process only |
| RFC-0031 request accepted | Compatibility HTTP edge | After strict validation |
| Cluster request executed | Caller application | `handle_chat_cluster_request()` path |
| Remote execution occurred | Receiver/runtime | Ordinary receiver path |
| Declared-node attribution | Caller application | Returned `ClusterResult` before projection |
| Compatibility response completed | Compatibility HTTP edge | RFC-0031 response projection |

Receiver activity alone does not join the first, third, fifth, and sixth facts
into one causal record.

## 4. Architectural and privacy boundaries

RFC-0031 remains a loopback-only, strict translation edge. Its response must
remain unchanged. RFC-0046 reuses ordinary static collection construction; it
does not make the compatibility layer routing, transport, fallback, lifecycle,
or topology owner.

Any acceptable direction must keep prompts, generated responses, authorization
values, declaration contents, addresses, remote URLs, and raw transport data
out of default retention. It must not expose topology to Aider, add a public
debug endpoint, rely on packet capture, introduce raw HTTP logging, or create
a generic event, tracing, telemetry, history, or plugin system.

## 5. Current implementation inspection

### Compatibility edge

`chat_completions()` performs authorization and strict request validation,
constructs a `ClusterRequest` for the fixed `chat` capability, then awaits
`handle_chat_cluster_request()`. It receives a complete `ClusterResult` in the
local variable `result` before `_compatibility_response()` projects only
content, model, completion identifier, and fixed response facts.

This is the only live point in the compatibility path where the accepted edge
request and its normalized result coexist. The route has no middleware,
counter, callback, app-state result value, dependency injection hook, or event
hook. Rejected requests return before that result exists. The route does not
store request content or result metadata.

The dedicated command constructs the ordinary static-collection application
when given `--declaration`, adds the unchanged compatibility router, and starts
Uvicorn on the fixed loopback listener. It supplies no observation option or
alternate process mode.

### Ordinary routing and attribution

`handle_chat_cluster_request()` selects the ordinary static collection path
when the application has static collection wiring. That path calls
`orchestrate_request_with_ordered_static_remote_fallback()`.

The ordered fallback first executes the local selected candidate. It advances
only on `RuntimeConnectionUnavailableBeforeRequestError` before useful request
execution. Each declared remote is then tried in declared order. Remote result
validation occurs in the existing remote transport.

Declared-node attribution is caller-owned in
`execute_declared_remote_routing_candidate()`: after remote transport returns
a normalized result, the caller returns a copy whose `node_id` is the declared
candidate node ID. Thus the receiver does not prove the attribution fact; the
caller assigns it before the compatibility route sees the result.

### Application state and lifecycle

`create_app()` stores composition and static wiring objects in application
state. The ordinary static collection constructor also stores its process-owned
HTTP client for lifespan cleanup. Neither state object records completed
requests, counts requests, stores results, or exposes a callback. Lifespan owns
client closure only.

### Access logging

The compatibility command invokes `uvicorn.run()` without an explicit logging
configuration. Uvicorn access logging is an external server behavior rather
than a Home AI Cluster observation contract. An access line can at most show an
HTTP method, path, and completion status. It cannot show the internally
attributed `ClusterResult.node_id`, distinguish all accepted semantic states,
or correlate the request with caller-owned attribution.

Using retained raw access logs would also be outside this proof's privacy
boundary. Access logs are therefore not a sufficient or recommended seam.

## 6. Existing observation seams

| Existing seam | What it observes | Live compatibility use | Why it is insufficient |
| --- | --- | --- | --- |
| RFC-0031 response | Projected completion response | Yes | Omits node and routing facts by design. |
| `handle_chat_cluster_request()` return | Full `ClusterResult` | Only inside process code | No shipped observer consumes or stores it. |
| Static collection wiring in app state | Startup topology objects | Yes | Contains declaration wiring, not execution outcome. |
| `home-ai-cluster-status` | One current local/remote readiness snapshot | Yes, separately | Does not observe a request or latest result. |
| `home-ai-cluster-health` | One local adapter health observation | Yes, separately | Establishes pre-request availability only. |
| `home-ai-cluster-explain-routing` | Synthetic selection explanation | No | Does not run the live compatibility composition. |
| `home-ai-cluster-explain-request` | A separate explicit local request account | No | It constructs and executes its own local command path. |
| RFC-0035 request history | Opt-in reduced account from the explanation command | No | It is not written by HTTP or compatibility requests and excludes node attribution. |
| Internal receiver status route | Receiver local runtime status | Yes, separately | Does not reveal caller request or caller attribution. |

No current accepted internal API carries a completed compatibility request count
and its result attribution to an operator. Using the in-process function return
in a real command would require a code or launcher change.

## 7. Receiver-side evidence limits

Receiver-side observations can establish useful but incomplete facts:

| Observation | Can establish | Cannot establish |
| --- | --- | --- |
| Receiver access log | An HTTP request reached the receiver | That it came from exactly one accepted Aider compatibility request or its caller attribution. |
| Runtime invocation count | A runtime was invoked | Caller topology, compatibility acceptance, and declared-node assignment. |
| Runtime output | Some execution produced content | Request identity and caller-owned attribution; retaining it is disallowed. |
| Receiver request count | One request reached the receiver | Whether it was the Aider request or whether the caller accepted and attributed its result. |
| Health before/after | Runtime availability | Any execution. |
| Caller local unavailability | The intended fallback precondition | Remote execution, response success, and attribution. |

Even a receiver count of one combined with controlled caller unavailability is
indirect. It does not correlate the Aider edge request with the returned
caller-owned result, and it cannot prove the caller applied the declared node
ID. It is not sufficient for the stronger claim.

## 8. Previous proof techniques

| Technique | Observes | Real two-machine suitability | Privacy/path assessment |
| --- | --- | --- | --- |
| Phase 6 inspection proxy | Compatibility request metadata and count | No for this runbook | A proxy and raw HTTP inspection are excluded here. |
| Native one-shot client output | Complete public `ClusterResult`, including node ID | No | It proves a different native client path, not Aider compatibility. |
| Caller normalized result in tests | Result and declared attribution | Test only | Test fakes and monkeypatches are valid tests, not live operator evidence. |
| Status snapshots | Static readiness | Yes, separately | Privacy-safe but non-execution evidence. |
| Request history | Reduced explicit explanation accounts | No | Not driven by HTTP requests and intentionally excludes node attribution. |
| Routing explanation | Candidate-selection reasoning | No | Synthetic and does not execute the live path. |
| Process-local middleware in tests | Selected request metadata | Test only | Demonstrates FastAPI capability but is absent from shipped app construction. |

The retained techniques establish components of the proof, not the required live
correlation under the current command.

## 9. Candidate A — existing seam

No existing seam is sufficient. The compatibility response omits attribution,
status observes readiness, request history does not receive compatibility
traffic and deliberately does not retain node IDs, and explanation commands do
not run the shipped compatibility process.

**Classification:** reject. No code change is possible only by weakening the
claim, not by satisfying the stated stronger proof.

## 10. Candidate B — proof-only harness

A temporary in-process harness could construct the compatibility application,
wrap or replace the routing function, and retain only an in-memory count and
declared node ID. Tests already use fakes, monkeypatches, ASGI transports, and
middleware to observe calls without retaining content.

That technique can observe both facts technically. It does not, however, run
the installed `home-ai-cluster-openai-compatibility --declaration` command
unchanged. It changes application construction or replaces a production seam,
requires a separate launcher or monkeypatching, and risks becoming a reusable
proof framework. It is an integration-test technique, not an operator proof of
the shipped command path.

**Classification:** reject for the real Aider proof. It is feasible and
privacy-safe in a test, but does not establish the requested live process fact.

## 11. Candidate C — bounded one-shot proof output

An explicitly enabled process-lifetime record could report only an accepted
request count, a sanitized declared node ID, and success or failure after the
compatibility route completes. It could avoid content retention and be disabled
by default.

Nevertheless, it needs a CLI flag or other mode, defines operator-visible
output and its timing, needs a correlation rule for rejected and auxiliary
requests, and creates a privacy-sensitive observation boundary. It is logging
or an operator observation contract even if only one line is emitted. A
non-default implementation does not remove that architectural decision.

**Classification:** feasible, but defer pending an RFC. It can prove both
facts only after a durable contract defines its scope and retention boundary.

## 12. Candidate D — bounded in-memory observation

An in-memory value queried after the request would require a query mechanism:
a CLI operation, signal, local socket, endpoint, shutdown summary, or another
operator protocol. Each would define result lifetime, overwrite and concurrency
rules, access scope, output shape, and privacy policy.

This would either extend RFC-0035's deliberately reduced history boundary or
create a second request-observation store. A process-lifetime-only value still
creates durable behavior if the shipped command exposes it.

**Classification:** feasible but disproportionate and RFC-required. It can
prove both facts only by adding a durable observation contract.

## 13. Candidate E — receiver-side-only evidence

Receiver counts, runtime observations, and controlled caller unavailability can
support a weaker operational narrative. They cannot join one accepted Aider
request to the caller's declared-node attribution. The caller owns that final
fact, and the compatibility response deliberately hides it.

**Classification:** reject for the stronger proof. It has low implementation
cost only because it omits required causal correlation.

## 14. Candidate F — weaker proof claim

A narrower claim could say that Aider received a successful compatibility
response while the caller runtime was unavailable and one receiver was
available. It could use existing preflight, status, health, and public response
facts without code changes.

It would not establish remote execution, exactly one accepted compatibility
request, bounded fallback, or caller-owned declared-node attribution. It would
be an edge-availability observation, not the intended static-cluster proof.

**Classification:** feasible with current code, but reject as a replacement for
the stronger claim. It may be useful only if explicitly documented as weaker.

## 15. Comparison

| Candidate | Current-code feasibility | Privacy risk | Path effect | Durable contract | RFC required | Proves both facts | Recommendation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A. Existing seam | No | Low | None | No | No | No | Reject |
| B. Proof-only harness | Test only | Low | Does not run shipped command unchanged | No, if discarded | No for test use | Technically, not as operator proof | Reject |
| C. One-shot output | Not present | Managed, but new | Adds process mode/output | Yes | Yes | Yes | Defer |
| D. In-memory query | Not present | Managed, but new | Adds query/lifetime behavior | Yes | Yes | Yes | Defer |
| E. Receiver-only | Partial | Medium if logs retained | None | No | No | No | Reject |
| F. Weaker claim | Yes | Low | None | No | No | No | Reject as replacement |

## 16. RFC threshold

A temporary external procedure needs no RFC only when it uses existing accepted
interfaces without changing shipped behavior. None of the current interfaces
correlates the required live facts.

A proposal that adds an operator-visible output, process mode, CLI flag,
observation API, status field, history field, shutdown summary, callback,
event, or logging policy establishes durable behavior and a privacy boundary.
That is architectural observability, not an unowned implementation detail, and
requires an RFC before implementation.

## 17. Recommended outcome

### Outcome 4 — a new architectural observation contract is required

The smallest unresolved question is:

> May the loopback compatibility process expose one explicitly opt-in,
> process-lifetime, content-free proof observation that correlates an accepted
> RFC-0031 request with the caller-owned declared-node attribution of its final
> normalized result, and if so through what operator-visible boundary?

The accepted RFCs determine routing and attribution ownership but do not decide
whether, how, or for whom a live compatibility process may expose that internal
fact. The answer affects process behavior, operator output, retention, privacy,
and future compatibility expectations. It needs a narrow RFC.

## 18. Exact next step

Do not execute the stronger Aider proof and do not implement an observation
mechanism yet. First create a narrow RFC that decides whether a one-shot,
explicitly opt-in proof observation contract is warranted, who may invoke it,
what bounded structural facts it can expose, how it correlates one accepted
request with one result, and how it is disabled, discarded, and kept separate
from normal operation.

The Aider runbook should remain blocked until that RFC is accepted and any
resulting implementation is independently reviewed. A later proof may then use
only the accepted mechanism; it must still retain no content or private
topology.

## 19. Explicit non-goals

This investigation does not add `node_id` to the compatibility response,
custom public routing fields, request or response logging, declaration or
remote URL logging, packet capture, a proxy, debug endpoint, dashboard,
database, telemetry, tracing, distributed observability, OpenTelemetry,
message bus, generic event system, persistent history, request replay, generic
hooks, production-wide debug mode, environment-driven behavior,
authentication, or LAN-facing compatibility access.

It does not implement a harness, output, query, counter, callback, middleware,
or event hook. It does not create a roadmap phase, run Aider, or weaken the
existing proof claim.
