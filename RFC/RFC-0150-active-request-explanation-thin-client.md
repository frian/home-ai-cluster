# RFC-0150: Active Request Explanation Thin Client

Status: Accepted

Date: 2026-10-07

Author: frian

## Summary

Add one finite local operator client, `hac explain-active-request` (also `home-ai-cluster explain-active-request`), for the accepted RFC-0149 effectful carrier. One invocation submits one supported business request to the already-running ordinary loopback process, validates its complete actual-request account, prints that account as compact JSON, and exits. The running process remains the sole owner of routing, execution, failure, and lifecycle truth. This RFC proposes a client contract only; it implements nothing.

## Context and problem

RFC-0145 owns same-request ordinary lifecycle explanation. RFC-0149 now exposes that authority through `POST /diagnostics/actual-request-explanation` on the active ordinary loopback process. Its closed JSON carrier executes and explains Chat, Code, Summarize, or Classify using that process's active composition, local bindings, caller-local restrictions, declared remote topology and order, remote transport, and execution cardinality. Image Generation awaits a separate binary-result transport decision.

Direct operator use still requires constructing the URL, discriminated body, capability-specific request, and `local_only` field, then interpreting HTTP failures and validating the returned account. RFC-0148 provides the closest client precedent for a fixed loopback diagnostic carrier, but its static routing explanation has no business payload and does not execute a request. This client must preserve the stronger effectful boundaries of RFC-0149.

The historical `home-ai-cluster-explain-request` explains a request executed through the finite composition constructed by that invocation. It cannot explain a different already-running process's cardinality or other active state. Both surfaces remain truthful only when their authority is explicit.

## Goals

- Provide one bounded command for a person to submit and explain one actual request through the running ordinary process.
- Use familiar one-shot inputs for the four supported JSON-result capabilities.
- Preserve the complete RFC-0149 result or terminal failure and lifecycle account without client-side interpretation of routing.
- Give safe, stable client failures and finite waiting without implying that an effectful request did not run.
- Keep the client local, non-retaining, engine-independent, and additive.

## Decision

### Command and authority

The canonical form is `hac explain-active-request`; `home-ai-cluster explain-active-request` is equivalent. It is one root finite command with exactly four capability-specific subcommands:

```text
hac explain-active-request chat [MESSAGE | --message MESSAGE] [--local-only] [--timeout-seconds SECONDS]
hac explain-active-request code [MESSAGE | --message MESSAGE] [--local-only] [--timeout-seconds SECONDS]
hac explain-active-request summarize [--text TEXT | --file PATH | stdin] [--local-only] [--timeout-seconds SECONDS]
hac explain-active-request classify [--text TEXT | --file PATH | stdin] --label LABEL --label LABEL [--label LABEL ...] [--local-only] [--timeout-seconds SECONDS]
```

The same forms work under the long root command. No `home-ai-cluster-explain-active-request` standalone script is added. No `hac explain-request` alias is selected: its long form would be easily confused with `home-ai-cluster-explain-request`, which has different process authority. The capability subcommand is the client-side discriminator of RFC-0149's closed union; it does not create a universal request abstraction.

An already-running ordinary `hac local` or `hac static-cluster` loopback process is a precondition. This client does not start it, construct temporary runtime or remote wiring, load retained Configuration, infer topology, inspect process tables, or discover ports. If that process is unavailable, the client emits its bounded unavailable error.

### Capability-specific local input

`chat` accepts exactly one non-blank one-shot Chat message, either positional `MESSAGE` or one `--message MESSAGE`, with the existing one-shot Chat convention for exclusivity and validation. It sends one `user` message. It does not expose ordered role construction, interactive state, source-grounded Chat, or External Information acquisition.

`code` accepts exactly one non-blank one-shot Code instruction through the corresponding positional or `--message` form. It sends one `user` message and retains RFC-0067's 65,536 UTF-8 byte aggregate message-content bound. It does not expose interactive Code, workspace access, file replacement, Aider, or tools.

`summarize` reuses the existing operator source choice: one `--text`, one bounded regular UTF-8 `--file`, or bounded UTF-8 stdin if neither explicit source is given. `classify` uses the same source choice plus repeated `--label` options in supplied order. Text must be non-blank and at most 65,536 UTF-8 bytes. File and stdin reading use the accepted bounded raw-byte, strict UTF-8 behavior and existing explicit-source precedence; no new filesystem authority is created. Classify requires 2–32 labels, each non-empty and at most 128 UTF-8 bytes, with exact uniqueness and unchanged order. No input is silently truncated or normalized into different business content.

Each capability subcommand accepts `--local-only`. Absence sends the top-level strict Boolean `local_only: false`; presence sends `true`. No generic constraints dictionary, `prefer_fast_response`, `min_context_size`, node, adapter, runtime, or model choice is exposed. Local validation checks syntax and accepted static bounds only; it does not decide active capability eligibility or routing.

### Closed request and fixed target

After local validation, one invocation constructs exactly one RFC-0149 body and sends one HTTP POST to:

```text
http://127.0.0.1:25042/diagnostics/actual-request-explanation
```

Examples without `--local-only` are:

```json
{"kind":"chat","local_only":false,"request":{"capability":"chat","messages":[{"role":"user","content":"hello"}]}}
{"kind":"code","local_only":false,"request":{"capability":"code","messages":[{"role":"user","content":"explain this function"}]}}
{"kind":"summarize","local_only":false,"request":{"text":"source text"}}
{"kind":"classify","local_only":false,"request":{"text":"source text","labels":["a","b"]}}
```

The client exposes no arbitrary `--kind`, `--request-json`, `--body`, or carrier-internal dictionary input. RFC-0149 remains available directly to machine clients needing its richer ordered Chat or Code message shapes. This CLI deliberately offers a smaller operator convenience subset.

The target is literal and fixed. There is no host, port, URL, remote-node, receiver, trusted-LAN, compatibility, environment-variable, or retained-configuration target option. The HTTP client uses a finite timeout, `follow_redirects=False`, and `trust_env=False`; it does not inherit proxy settings for this loopback request or add TLS or remote authentication.

### One effectful request and timeout

One invocation performs local validation, constructs one body, makes one POST, validates one response or maps one HTTP/client failure, writes one account or one safe error, then exits. It does not retry, replay, poll, make a routing/status/health request first, probe capabilities, or perform client-side fallback. A repeated invocation is a new business request.

`--timeout-seconds SECONDS` follows RFC-0060's native one-shot convention: one base-10 integer in `1..3600`, default `120` seconds, passed as the HTTPX scalar timeout for the single request. Invalid or repeated values fail local validation before HTTP. The scalar applies to HTTPX timeout categories and is not a strict total command deadline, server execution deadline, routing constraint, or retry trigger.

Client timeout yields the stable timeout client error and no retry. It cannot establish whether the server received, began, or completed the business request before disconnect became authoritative under RFC-0082. The client cannot claim non-execution or safe repeatability. Carrier HTTP `500` has the same uncertainty under RFC-0149: an account may have failed to form after business execution. Neither case authorizes replay or automatic advice that retry is safe.

### Validate the complete public account

HTTP `200` alone is insufficient. Before printing, the client validates the complete RFC-0149 public representation, using the smallest private client-side validation needed. This is defensive validation of shape, vocabulary, request/response identity, capability-specific result form, status/result/failure consistency, visible within-array ordering, visible candidate progression, and visible reason/fact consistency. The running carrier remains authoritative for the truthfulness of the account it constructed from actual execution. The client must not load topology or active state, determine eligibility or whether process-local permission applies, import internal router objects, invoke routing helpers, reconstruct routing, recompute fallback, reconstruct hidden continuation positions, or reproduce carrier-private lifecycle validation.

The top-level object contains exactly `status`, `result`, `failure`, and `explanation`. `status` is only `succeeded` or `failed`. Success has a non-null capability-specific result and `failure: null`; failure has `result: null`, a closed `failure` object with only `status` in `no-selectable-candidate`, `execution-permission-denied`, `runtime-unavailable`, or `execution-failed`, and no final node. Chat, Code, and Summarize success preserve the accepted result fields `content`, `adapter`, `model`, and `node_id`; Classify success preserves `selected_label` and `node_id`. Result values must satisfy their accepted public shapes; a Classify selected label must be one supplied candidate. The success result's `node_id` equals `explanation.final_node_id`.

`explanation` contains exactly `requested_capability`, `local_only`, `initial_selection`, `candidate_facts`, `continuations`, and `final_node_id`. Capability and strict Boolean local-only values match this invocation. Initial selection is `null`, `{"kind":"local"}`, or `{"kind":"declared_remote","node_id":"..."}` with a non-empty node ID. Each candidate fact contains exactly `family`, `node_id`, and `fact`; each continuation exactly `node_id` and `reason`. Node IDs in these positions are non-empty. The first public family vocabulary is only `local` and `declared-remote`.

Permitted fact/family combinations are:

| Family | Facts |
| --- | --- |
| `local` | `execution-permission-granted`, `execution-permission-denied`, `adapter-invoked` |
| `declared-remote` | `transport-invoked`, `execution-permission-refused` |

Permitted continuation reasons and their establishing fact are:

| Reason | Required candidate fact |
| --- | --- |
| `local-execution-permission-denied` | same local candidate's `execution-permission-denied` |
| `local-runtime-connection-unavailable-before-request` | same local candidate's `adapter-invoked` |
| `remote-runtime-connection-unavailable-before-request` | same declared remote's `transport-invoked` |
| `remote-execution-permission-refused` | same declared remote's `execution-permission-refused`, after `transport-invoked` |

Validation preserves relationships visible in RFC-0149's public fields. Facts start with the selected candidate when facts exist; a null selection has no candidate facts. For the same local candidate, a grant must precede adapter invocation **if both facts are present**; denial contradicts either grant or adapter invocation. Adapter invocation without a public permission fact is not rejected solely for lacking a grant: the client cannot know whether process-local permission applied. For the same declared remote, permission refusal requires an earlier transport invocation. Identical `family` + `node_id` + `fact` combinations do not repeat. In the ordered `candidate_facts` array, a candidate identified by `family` + `node_id` cannot resume after facts for a different candidate appear.

Each continuation's closed reason determines its candidate family; its non-empty `node_id` identifies that candidate within the family, without assuming node IDs are globally unique across local and declared-remote candidates. The corresponding establishing fact in the table must exist for that candidate. In particular, `local-runtime-connection-unavailable-before-request` requires `adapter-invoked`, but does not itself require a grant; any grant present must precede that invocation. A continuation is valid only if the ordered candidate-fact progression identifies a later candidate after that candidate; this also rejects a continuation for the final represented candidate. Identical `node_id` + `reason` continuations do not repeat. The `continuations` array must correspond monotonically to the visible candidate progression: a later entry cannot name a candidate earlier in that progression. These checks do not establish the exact position at which any continuation occurred between candidate facts. Client validation can establish consistency between the two public projections, but cannot reconstruct their private cross-array event positions. A successful final node belongs to an invoked candidate. Validation rejects visible contradictions without deciding which candidate should have been eligible or selected.

### Output and client failure

Every valid HTTP `200` account prints exactly one compact JSON object and one newline on stdout, with the complete validated account, empty stderr, and exit `0`. This includes `status: failed`: the carrier successfully explained a completed business failure. The `status` and `failure` fields carry that business outcome; the client must not convert it to exit `1`. It does not print generated content alone, pretty-print, colorize, add prose/headings, timestamps, or metadata, hide failed accounts, or translate to historical RFC-0034 output.

For a client failure, stdout is empty and stderr contains exactly one of these safe lines plus a newline:

| Condition | stderr | Exit |
| --- | --- | --- |
| Invalid local CLI input | `error: invalid request explanation input` | 2 |
| Connection failure | `error: ordinary cluster unavailable` | 1 |
| Client timeout | `error: request explanation timed out` | 1 |
| HTTP 422 | `error: request explanation rejected` | 1 |
| HTTP 503 | `error: request explanation unavailable` | 1 |
| HTTP 500 or unexpected HTTP status | `error: request explanation failed` | 1 |
| Malformed or invalid HTTP 200 account | `error: invalid request explanation response` | 1 |
| Other client failure | `error: request explanation failed` | 1 |

The client never prints raw exceptions, traceback, response body, remote URL, retained Configuration, credentials, internal objects, or input text/labels in an error. `422` and pre-execution `503` preserve their RFC-0149 meaning. A `500` or timeout does not prove non-execution; the error line makes no such claim.

### Privacy and retention

Chat/Code messages, Summarize text, and Classify text/labels go only to the fixed ordinary loopback carrier. The client does not log or persist them, add them to explanation facts, write history, send them directly to a remote, cache them, or add telemetry, request IDs, account files, or later lookup. The active process may route the normalized business request to an operator-declared remote under existing ordinary authority when `local_only=false`; that is server-owned behavior. Bounded Summarize/Classify file input is accepted local preprocessing, not a new file or workspace service. The historical command's `--record-history` remains historical-only.

## Relationship to existing authority and compatibility

RFC-0145 owns ordinary lifecycle semantics; RFC-0149 owns the effectful carrier and its closed public account. RFC-0148 provides a fixed-loopback, one-request, non-retaining thin-client precedent, while its routing explanation stays non-effectful and payload-free. This RFC adds stricter no-replay and uncertainty handling because it submits real work. RFC-0045, RFC-0060, RFC-0061, RFC-0067, RFC-0082, RFC-0085, RFC-0090, and the accepted one-shot Summarize and Chat client contracts govern the reused local conventions. Small private HTTP/helper reuse is possible later; a generic diagnostics-client framework is not selected.

This proposal is additive. It leaves ordinary `hac chat`, `code`, `summarize`, and `classify` stdout/exit behavior, `hac explain-active-routing`, `home-ai-cluster-explain-routing`, RFC-0149 HTTP behavior, receiver and trusted-LAN authority, OpenAI compatibility, and history behavior unchanged. In particular, `home-ai-cluster-explain-request` keeps its parser, output, finite composition, `--record-history`, and installed spelling. It is neither aliased nor deprecated nor redirected to RFC-0149. Once accepted, the new root spelling, options, JSON output, safe errors, and exit semantics become public compatibility contracts.

Future implementation should update root help and the command reference to explain the running-process precondition, actual execution, capability inputs, `--local-only`, compact account output, exit `0` for a valid failed-business account, timeout and carrier-`500` uncertainty, no automatic retry, and the historical command distinction. This Draft PR changes no command documentation.

## Non-goals

This RFC does not implement the client or authorize Image Generation, binary/base64/multipart result transport, source-grounded Chat, External Information acquisition, interactive Chat or Code, workspace-aware Code, Aider, `code-file`, generic tools, a browser UI, trusted-LAN or receiver diagnostics, remote target selection, configurable host or port, process startup or discovery, retained Configuration interpretation, arbitrary request JSON passthrough, a generic HTTP client, retries, polling, monitoring, history, persistence, dashboard, database, Docker, Kubernetes, or modification/deprecation of historical explanation commands. Image Generation remains outside the CLI because RFC-0149 has no accepted public JSON result contract for it; the client must not write an image file, discard the image, or invent binary transport.

## Alternatives considered

| Alternative | Assessment |
| --- | --- |
| `hac explain-request` | Its long form, `home-ai-cluster explain-request`, is too easily confused with historical `home-ai-cluster-explain-request` despite different process authority. Reject for this first contract. |
| `--explain` on four ordinary commands | Convenient in principle, but changes four established output/exit contracts and mixes ordinary result presentation with diagnostic account presentation. Defer. |
| Four root explanation commands | Duplicates one carrier's surface and common failure contract. Reject. |
| Generic `--kind` plus `--request-json` or `--body` | Still makes operators manually build the carrier, weakens local input validation, exposes HTTP shape as CLI ergonomics, and invites a generic framework. Keep direct carrier access for advanced machine clients. |
| Raw curl only | Architecturally sufficient, but leaves repeated operator transport construction, HTTP interpretation, and response validation. Reject as the sole operator path. |
| Replace or alias historical standalone | Breaks compatibility and changes the authority of an established finite invocation. Reject. |

## Falsifiable acceptance proof

A future implementation must prove:

1. `hac` and `home-ai-cluster` expose the same `explain-active-request` root command with only `chat`, `code`, `summarize`, and `classify` kinds; no new standalone script is installed, and Image Generation is rejected at CLI parsing.
2. The historical `home-ai-cluster-explain-request` parser, output, finite composition, and history option remain unchanged.
3. One-shot Chat and Code inputs each produce exactly one matching RFC-0149 body with one user message, preserving the Code byte bound.
4. Summarize text/file/stdin and Classify text/file/stdin plus ordered labels each produce exactly one matching RFC-0149 body under existing input bounds and source semantics.
5. `--local-only` maps only to the carrier top-level Boolean, false by default and true when present.
6. Every valid invocation sends exactly one POST to `http://127.0.0.1:25042/diagnostics/actual-request-explanation`; it performs no probe, poll, retry, replay, fallback, process startup, or discovery.
7. The HTTP client uses the accepted bounded integer timeout, disables redirects, and ignores environment proxies.
8. Valid succeeded and failed business accounts each print complete compact JSON with one newline, empty stderr, and exit `0`; `status=failed` is not a client error.
9. Invalid local input yields only its stable safe error and exit `2` without HTTP.
10. Connection failure, timeout, HTTP `422`, `503`, `500`, unexpected status, malformed JSON, and malformed HTTP `200` account each map to the exact safe client category, empty stdout, and exit `1`, with no raw body or exception.
11. Timeout and HTTP `500` trigger no replay and are never presented as proof of business non-execution; a manual repeat is recognized as new work.
12. Public-account validation proves at least:
    - missing or extra account fields and the wrong capability-specific result form are rejected;
    - unknown family, fact, or continuation reason and a wrong fact/family combination are rejected;
    - a local grant followed by adapter invocation is accepted; invocation followed by grant, denial plus invocation, and grant plus denial for the same candidate are rejected; invocation without either permission fact is not rejected solely for lacking a grant;
    - remote permission refusal without earlier transport invocation is rejected, and transport invocation followed by refusal is accepted;
    - a duplicate candidate fact or a candidate resuming after progression to a different candidate is rejected;
    - a duplicate continuation, a continuation without its public establishing fact, or a continuation naming a candidate with no later candidate in the public fact progression is rejected; continuation reason/family mapping is checked without assuming global node-ID uniqueness, and continuation order is monotonic with visible candidate progression.
13. Response `requested_capability` and `local_only` match the submitted request; success final attribution agrees with the business result; a failed account has null result and final node with a closed safe failure status.
14. Input text and labels never enter client diagnostic errors; the client writes no history, telemetry, or retained account.
15. The client loads no retained Configuration, calls no routing helper, and constructs no active topology.
16. Interactive, source-grounded, workspace, and arbitrary JSON modes are absent; ordinary capability commands and RFC-0148 behavior remain unchanged.

If implementation requires changing RFC-0149, ordinary routing, a business-request contract, or generic client infrastructure, it must return to architecture before proceeding.

## Open questions

No implementation-blocking architectural question remains for this first client. Private Python placement, parser/helper reuse, and test organization are implementation choices. Richer message input, Image Generation transport, or integration into ordinary commands require later decisions if justified.

## Decision

Accepted.
