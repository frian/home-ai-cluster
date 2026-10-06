# RFC-0149: Bounded Active-Process Actual-Request Explanation Carrier

Status: Accepted

Date: 2026-10-06

Author: frian

## Summary

Add one explicit, effectful `POST /diagnostics/actual-request-explanation` carrier to the already-running ordinary loopback application. It executes one ordinary request through that process's active composition and returns the ordinary result, or a bounded terminal-failure projection, alongside RFC-0145 facts captured during that same execution. The first carrier accepts Chat, Summarize, Classify, and Code. Image Generation remains within RFC-0145's semantic authority, but its binary result needs a separate public transport decision before admission to this JSON carrier.

## Context and problem

The historical `home-ai-cluster-explain-request` is a finite invocation. Its `--message` parser constructs a request, reloads retained Configuration, creates a local runtime app, composes remote wiring, owns a fresh execution-cardinality object, and executes and explains that invocation's request. It truthfully answers: *what happened to the request executed by this finite explanation invocation?* It cannot report the current permission state, bindings, topology, or transport of another already-running process. Its parser cannot express Classify labels and gives Image Generation only default geometry. Neither limit defines RFC-0145's capability scope.

RFC-0145 already accepts one request-scoped lifecycle explanation from ordinary orchestration: selection, permission, candidate-specific facts, consumed continuation reasons, final attribution, or terminal semantics, as applicable. The missing public authority is a carrier in the active ordinary process. RFC-0147 provides a useful loopback ownership precedent, but its static routing carrier is pre-execution and non-effectful. This carrier executes a real request, may invoke a runtime or declared remote, and may consume execution permission. RFC-0148 demonstrates that a client can follow a stable carrier; it supplies no client contract here.

Current native routes are `POST /v1/chat` for both Chat and Code, `/v1/summarize`, `/v1/classify`, and `/v1/image-generation`. Chat/Code carry ordered messages; Summarize carries bounded source text; Classify also requires ordered labels; Image Generation carries an instruction and optional paired dimensions. Ordinary Image Generation returns PNG bytes, while the other four return JSON. The closed internal remote-request union includes receiver-only and source-grounded shapes and is not a suitable public diagnostic input contract. The current ordinary app stores local composition and optional single or ordered remote wiring on `app.state`; receiver and trusted-LAN apps have separately constructed route sets. Ordinary one-remote fallback and ordered-remote fallback are currently distinct code paths. Only the ordered path presently accepts a private `OrdinaryRequestLifecycle` collector, so implementation must preserve each active ordinary path's behavior while adding the RFC-0145 request-scoped facts; it cannot silently replace one policy with the other.

## Goals

- Answer what happened when **this** request executed through **this already-running ordinary process**.
- Preserve its actual business result or terminal failure and expose bounded same-request lifecycle facts.
- Reuse active in-memory composition, ordinary routing, permission, continuation, and execution authority.
- Make exposure local, explicit, ephemeral, capability-centered, and engine-independent.
- Keep ordinary requests and their existing response contracts unchanged.

## Non-goals

No root or standalone client, `--explain` option, browser UI, historical command migration or deprecation, trusted-LAN or receiver explanation, remote diagnostic forwarding, OpenAI-compatible explanation, acquisition/workspace interaction account, generic request/result framework, tracing, telemetry, request lookup, history expansion, persistence, probes, retries, new timeout, or routing/fallback policy change is accepted here.

## Proposed decision

### Owner, route, and exposure

The ordinary loopback application alone owns `POST /diagnostics/actual-request-explanation`. The diagnostic namespace matches RFC-0147 and separates effectful, explicitly explained execution from unchanged native business endpoints. The endpoint exists in the ordinary local and static-cluster loopback applications. It is absent from the trusted-LAN browser app, the closed receiver app, OpenAI-compatible apps, and all compatibility applications, even when those apps share composition objects. App construction must enforce this route-set boundary; merely checking the peer address inside a shared route is insufficient. No receiver or remote transport endpoint for explanation is created. The business request may still execute on an operator-declared remote under existing ordinary policy.

### Closed request contract

The JSON body is a closed discriminated choice with exactly `kind`, `local_only`, and `request`. `kind` is one of `chat`, `summarize`, `classify`, `code`; `local_only` is an explicit strict Boolean routing constraint. `request` uses the semantic fields of the matching existing native public business body: Chat and Code use the ordered-message `/v1/chat` shape with `capability` required to equal `kind`; Summarize uses its bounded `text`; Classify uses its bounded `text` and ordered `labels`. The carrier applies the same accepted normalized business-request validation and capability bounds as ordinary execution, but does not promise identical HTTP parser behavior or byte-for-byte input acceptance at native endpoints. This carrier body is deliberately closed: unknown fields are invalid even where an existing native public model ignores them. This stricter carrier parsing does not change native endpoint parsing. Mismatched kinds/capabilities, malformed labels, and unsupported kinds are also invalid. No arbitrary dictionary, runtime/model selection, generic metadata, or extensible operation key is accepted. `local_only` is explicit because this diagnostic route must say whether ordinary remote continuation is permitted; it changes no accepted continuation rule. For example:

```json
{"kind":"classify","local_only":false,"request":{"text":"example","labels":["a","b"]}}
```

This choice covers all four currently JSON-result families without reducing ordered Chat or Code messages to one `--message` string. It does not reuse the internal remote-request union: that union contains `source-grounded-chat`, Image Generation, receiver transport details, and a different authority boundary. The public carrier is a closed choice over existing native shapes, not a universal request abstraction. Source-grounded Chat acquisition/evidence and whole workspace-aware Code interactions remain outside this first contract; an already-formed ordinary Chat or Code inference request is in scope.

Image Generation remains architecturally eligible for RFC-0145 explanation. The first **public** RFC-0149 contract excludes it. Its ordinary result is a cluster-validated still PNG of up to 41,943,040 encoded bytes. Putting that binary result in JSON/base64 merely for response symmetry would add a large diagnostic payload; omitting it would fail to preserve the successful business result. Multipart, paired retrieval, and a dedicated binary response each add a distinct public contract or retention question. A later RFC must decide its bounded result transport before `image-generation` can be admitted. An implementation may prove private RFC-0145 Image Generation lifecycle facts independently, but must reject that kind at this public route until a public result contract is accepted. This is a transport staging decision, not a permanent exception to RFC-0145.

### One active ordinary lifecycle

After validating the body, the route normalizes exactly one capability-specific request and invokes the same ordinary execution authority and active objects serving that process. It uses current local eligibility and bindings, caller-local restrictions, declared topology and order, process-owned remote transport, and the process's own execution cardinality. It must not call `load_retained_configuration()`, construct another runtime app or static composition, create replacement cardinality, or infer what the active process would have done. Where the ordinary local, one-remote, and ordered-remote branches currently differ, their accepted behaviors remain authoritative. The route requests bounded private lifecycle collection for that invocation only. Ordinary control flow writes facts as decisions occur, including a consumed continuation reason before the branch advances. It performs one routing selection and at most the ordinary permission check and candidate executions for that one request; it never replays, recomputes, probes, or explains from the final result alone.

### Completed response

A completed explained invocation returns HTTP `200` JSON with exactly four top-level semantic parts: `status` (`succeeded` or `failed`), `result`, `failure`, and `explanation`. `200` means that the carrier completed and returned an account, **not** that business execution succeeded. A successful account has its ordinary normalized JSON result in `result`, `failure: null`, and RFC-0145 facts in `explanation`. Chat, Code, and Summarize preserve `ClusterResult` content and its accepted node/adapter/model attribution; Classify preserves `ClassifyResult.selected_label` and node attribution. No result is silently discarded or merged into explanation metadata. These capability-specific results are a closed choice, not a universal result envelope in core.

`explanation` contains `requested_capability`, `local_only`, `initial_selection`, `candidate_facts`, `continuations`, and `final_node_id`. `initial_selection` is `null`, `{"kind":"local"}`, or `{"kind":"declared_remote","node_id":"..."}` according to the actual initial selection. Each candidate fact has exactly `family`, `node_id`, and `fact`; each consumed continuation has exactly `node_id` and `reason`. `final_node_id` is populated only for success and otherwise `null`. The historical RFC-0034 `routing` object is not copied into this carrier merely for compatibility.

The first public `candidate_facts[].family` vocabulary is exactly `local` or `declared-remote`. The first public `candidate_facts[].fact` vocabulary and its permitted family are:

| `fact` | Family | Meaning |
| --- | --- | --- |
| `execution-permission-granted` | `local` | The ordinary local execution-permission owner granted permission for this candidate during this request, before local adapter invocation. It does not assert adapter success. |
| `execution-permission-denied` | `local` | That owner denied permission. The same candidate cannot also have `adapter-invoked` in this request. |
| `adapter-invoked` | `local` | Ordinary control flow actually invoked the selected local adapter. This is not inferred from selection, permission, or final result. Where process-local permission applies, its granted fact precedes this fact. |
| `transport-invoked` | `declared-remote` | Ordinary control flow invoked the process-owned remote transport for this candidate. It asserts neither confirmed request transmission beyond accepted transport semantics nor remote adapter invocation, runtime engagement, or success. |
| `execution-permission-refused` | `declared-remote` | The declared remote returned the accepted pre-execution permission refusal for this request. Its `transport-invoked` fact precedes this fact; it does not assert remote adapter execution. |

The first public `continuations[].reason` vocabulary is exactly:

| `reason` | Meaning and corresponding candidate facts |
| --- | --- |
| `local-execution-permission-denied` | The named local candidate's denial was actually consumed to advance to a declared remote. Its facts contain `execution-permission-denied` and cannot contain `adapter-invoked`. |
| `local-runtime-connection-unavailable-before-request` | The named local candidate's adapter was invoked, and its accepted pre-transmission runtime-unavailability condition was consumed to advance. Its facts contain `adapter-invoked` and, where process-local permission applies, earlier `execution-permission-granted`. |
| `remote-runtime-connection-unavailable-before-request` | Transport was invoked for the named declared remote, and its accepted pre-transmission unavailability condition was consumed to advance to a later remote. Its facts contain `transport-invoked`; no stronger remote-execution fact is implied. |
| `remote-execution-permission-refused` | Transport was invoked for the named declared remote, and its accepted pre-execution permission refusal was consumed to advance to a later remote. Its facts contain `transport-invoked` followed by `execution-permission-refused`. |

Each continuation names the candidate ordinary control flow actually left for that concrete accepted reason. It exists only when control flow advanced to another candidate. A terminal condition on the final candidate does not create a continuation even if the same condition could have allowed advancement had another candidate existed. Neither raw exception text nor a hypothetical fallback enters this vocabulary.

`candidate_facts` is serialized in the order these bounded authoritative facts became true during ordinary control flow for this request. `continuations` is serialized in the order ordinary control flow consumed the reasons. For a continuation, its exposed establishing fact or facts occurred first; the continuation was consumed next; facts for the next candidate occurred afterward. In particular, local permission grant precedes local adapter invocation, remote transport invocation precedes remote permission refusal, and a later remote's facts cannot precede the facts that caused control flow to leave an earlier remote. The separate arrays do not form a merged event timeline.

Under accepted one-request routing and fallback, each concrete candidate is processed at most once. A completed account must not repeat the same `family` + `node_id` + `fact` combination, or the same `node_id` + `reason` continuation. These are carrier validation invariants, not new global node-identity or topology rules.

This closed projection adds no generic `attempted`, `started`, `engaged`, `executed`, `failed`, `healthy`, or `ready` fact, arbitrary internal event name, timestamp, or duration. Occurrence order preserves only bounded candidate progression; it is not tracing, telemetry, an event bus, or a generalized timeline. `final_node_id` owns successful final attribution. New public candidate facts or continuation reasons require compatibility treatment and, where their semantics change architecture, RFC consideration. Private classes and methods remain implementation details.

A completed ordinary terminal failure also returns HTTP `200`, with `status: failed`, `result: null`, the same bounded `explanation` collected before failure, and `failure: {"status":"..."}` containing only a safe route-owned terminal status. Its closed first vocabulary is `no-selectable-candidate`, `execution-permission-denied`, `runtime-unavailable`, or `execution-failed`, selected from the established ordinary terminal owner and existing safe HTTP/historical distinctions. Ordered remote exhaustion follows the existing terminal exception precedence; it is not assigned a new core failure class. `execution-failed` is the safe coarse projection for other terminal execution errors. This is a public projection at the diagnostic edge, not a change to core exceptions, an RFC-0034 compatibility promise, or a general failure taxonomy. No raw exception text or runtime/remote URL is returned. Facts may survive stack unwinding only until this same response is formed.

Invalid carrier JSON or a rejected kind/body returns `422` with a fixed safe invalid-input detail and **does not execute**. If the active ordinary composition is missing or contradictory before execution starts, return `503` with a fixed safe carrier-unavailable detail and do not execute. If the carrier cannot safely construct an account after execution or during projection, return `500` with a fixed safe carrier-failure detail; do not run the request again to repair the account. These carrier failures do not masquerade as completed ordinary execution failures. The owning ordinary route should normally have a valid composition; `503` is fail-closed handling for an invalid construction state, not a license to reconstruct it. Ordinary terminal failures cannot be relabeled `503` merely because a runtime was unavailable. The exact safe detail strings are implementation details; status meanings and absence of raw errors are not.

Unlike `422` and this pre-execution `503`, carrier `500` does not establish that the business request was not executed. After ordinary execution began, the request may have succeeded, failed terminally, or partially progressed under existing ordinary semantics without a trustworthy completed account reaching the caller. From the caller's perspective, business completion after carrier `500` is unknown unless independently established by another authority. The caller must not treat `500` as proof of non-execution: immediately repeating this effectful request may execute another business request. The carrier never retries or replays to repair the account; this RFC defines no automatic retry or idempotency mechanism.

### Privacy, cancellation, and retention

The carrier receives the business input only to execute it. Explanation metadata must not echo prompt or request content, Classify source text or labels, source evidence, workspace/file contents, credentials, retained Configuration, remote URLs, raw node or adapter objects, or raw exception text. Adapter/model identity may appear only where already part of an accepted ordinary business result, never as invented explanation detail. Returning generated content in `result` is ordinary execution semantics; copying input into `explanation` is not. The route writes no explanation facts or new lifecycle fields to RFC-0035 history. The historical command's optional `--record-history` behavior stays its own compatibility contract. Ordinary requests without explanation keep their existing history and response behavior and need no retained lifecycle account.

The route uses the existing RFC-0082 HTTP disconnect boundary for ordinary routable work. If a client disconnect wins, execution is abandoned under that boundary and there is no promised explanation response; this RFC adds no core disconnect fact. It adds no server-side execution deadline, client timeout, retry, or request replay. A later thin client may choose its own finite timeout under RFC-0060, but no such client is selected here.

## Rationale and alternatives

| Alternative | Assessment |
| --- | --- |
| Add an explanation flag to native routes | Same-request execution is possible, but changes several public response contracts and makes `/v1/image-generation`'s raw PNG response especially awkward. Existing non-explanation callers must keep their defaults. |
| One dedicated route with a closed capability choice | Explicit local authority and response meaning, one opt-in surface, reuse of ordinary execution, four existing JSON-result families; adds one public route. Chosen. |
| Separate explanation route per capability | Native bodies remain familiar, but duplicates route/exposure/failure contracts and does not solve binary Image Generation by itself. |
| Reuse the internal remote-request union | Already discriminated, but includes receiver-only and source-grounded shapes and accepts internal transport semantics. It crosses the wrong boundary. |
| Historical finite command only | Truthful for its own request and cardinality, but cannot answer active-process state. Preserved unchanged. |
| Generic root client or per-command `--explain` first | Client input and compatibility policy cannot substitute for a carrier in the active process. Deferred. |

The first route's four-capability scope keeps the result contract coherent. Its cost is that an operator cannot yet receive an active-process Image Generation result and explanation together. Silently returning only image metadata would make the diagnostic request effectful while withholding its product; the bounded binary transport decision remains separate.

## Existing authority and impact

RFC-0032 **Actual Request Routing Explanation** and RFC-0034 **Structured Actual Request Failures** remain historical finite-command authority. RFC-0035 **Bounded Local Request History** remains an unchanged allowlist. RFC-0145 **Ordinary Request Lifecycle Explanation** owns same-request lifecycle semantics; this RFC owns only its active-process public carrier. RFC-0146 **Bounded Static Routing Explanation Authority**, RFC-0147 **Loopback Static Routing Explanation Carrier**, and RFC-0148 **Active Routing Explanation Thin Client** remain separate pre-execution authority and client work.

The route must respect RFC-0102 **Local Execution Permission Policy**, RFC-0103 **Local Execution Permission Failure Contract**, RFC-0104 **Remote Pre-Execution Permission Refusal**, RFC-0028 **Minimal Pre-Execution Candidate Fallback**, RFC-0040 **Multiple explicit static remote nodes**, RFC-0109 **Explicit LAN Receiver Route Boundary**, RFC-0111 **Explicit Receiver Authority Activation**, RFC-0130 **Bounded Trusted-LAN Browser Authority**, RFC-0031 **Minimal OpenAI-Compatible Chat Access**, RFC-0061 **Bounded Text Classification**, RFC-0067 **Bounded Textual Code Assistance**, RFC-0120 **Bounded Local Image Generation**, RFC-0131 **Bounded Image Generation Dimensions**, and RFC-0135 **Bounded Remote Image Generation**. RFC-0045 **One-shot ordinary request command**, RFC-0060 **Explicit Native Client Timeout**, RFC-0085 **Explicit HAC-Owned HTTP Environment Boundary**, and RFC-0090 **Ordinary Loopback Port 25042** remain unchanged. These titles are the current repository titles; this RFC does not revise their authority.

Implementation will need a private route and enough request-scoped collection in the existing ordinary local, single-remote, and ordered-remote paths to satisfy RFC-0145 without changing their decisions. The command reference and clients are separate later work. This RFC changes no code, test, package entrypoint, or documentation outside this file.

## Falsifiable acceptance proof

Before implementation can claim this RFC, tests must demonstrate through the running ordinary loopback app:

1. One local successful request yields the same capability result and facts from that one execution, with one routing selection, permission evaluation, and adapter invocation.
2. Local permission denial with allowed remote continuation does not invoke the local adapter, records the denial and actual remote, and does not recheck permission for explanation.
3. Local pre-transmission unavailability preserves its consumed continuation reason; a non-fallback local failure stays terminal with no fabricated continuation.
4. Direct declared-remote success attributes the real remote; ordered continuation records the first consumed pre-engagement reason and subsequent actual remote without calling it local adapter execution.
5. Ordered remote exhaustion preserves existing terminal exception meaning/precedence and projects surviving consumed facts; `local_only` blocks remote continuation exactly as ordinary execution does.
6. Contention against the active process's own execution-cardinality object changes the observed permission outcome; an equivalent retained Configuration loaded in another process cannot substitute.
7. Chat and Code ordered messages, Summarize text, and Classify text plus ordered labels each validate, execute once, and preserve their capability-specific result. Image Generation is rejected before execution at this route until a later binary-result contract is accepted.
8. Input, labels, evidence, credentials, remote URLs, raw objects, and raw exception text are absent from explanation and safe failures; ordinary generated content appears only in the business result.
9. Invalid input, unavailable active composition, and projection failure use their distinct safe carrier responses and never trigger replay.
10. The route exists on ordinary loopback apps and is absent on receiver, trusted-LAN, OpenAI-compatible, and compatibility apps.
11. Explicit explanation writes no new history; non-explained native requests keep their response, execution, history, and overhead boundaries.
12. Confirmed disconnect follows the existing cancellation behavior and does not create a misleading completed account.
13. Every completed account uses only the closed public `family`, `fact`, and continuation `reason` values and their permitted family/reason relationships; an unsupported or arbitrary value cannot appear in a valid account.
14. Candidate facts preserve bounded occurrence order, continuations preserve consumed-reason order, and their cross-array relationship shows local permission denial before remote progression and remote transport/refusal before progression to the next remote. No identical candidate fact or identical continuation repeats for one candidate.
15. A terminal condition on the final candidate creates no fabricated continuation; neither array becomes a generic timeline or tracing stream.
16. Carrier `500` is never presented as proof that business execution did not occur, and projection failure never triggers replay. Invalid input `422` and pre-execution composition `503` retain their no-execution guarantee.

If these proofs require a second orchestrator, repeated permission check, new generic instrumentation, or a change to accepted fallback semantics, implementation must stop and return to architecture.

## Open questions

No architectural question remains for this proposed carrier decision. Private function/class placement and exact fixed safe-detail wording remain implementation choices.

## Decision

Accepted.
