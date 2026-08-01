# Minimal Local Web Client Investigation

Status: Investigation

Date: 2026-08-01

## Question and scope

This investigation asks for the smallest truthful browser interface over the
current native capabilities: `chat`, `summarize`, and `classify`. It is not a
proposal to implement one. It does not change the native contracts, operator
surfaces, process ownership, or architecture; an accepted RFC is required
before implementation.

The intended distinction is important:

* a local web client submits one ordinary user request through an existing
  native capability;
* preflight, health, and static-cluster status remain explicit, finite,
  operator inspection surfaces; and
* neither category is a dashboard or a cluster-control interface.

## Facts observed

The ordinary local and static-cluster launchers bind to `127.0.0.1:8000` by
default. Their native application has these public routes:

| Capability | Native request | Successful response |
| --- | --- | --- |
| chat | `POST /v1/chat` with non-empty `messages` and a `capability` | `ClusterResult` |
| summarize | `POST /v1/summarize` with `{"text": "..."}` | `ClusterResult` |
| classify | `POST /v1/classify` with `{"text": "...", "labels": ["..."]}` | `ClassifyResult` |

These are the seams a client can reuse. The application construction includes
the native router but no static-file mount and no CORS middleware. The existing
one-shot clients also target these fixed loopback routes. See
[`api/routes.py`](../src/home_ai_cluster/api/routes.py),
[`main.py`](../src/home_ai_cluster/main.py), and the canonical
[operator workflow](operator-workflow.md).

`ClusterResult` contains `content`, `adapter`, optional `model`, and `node_id`.
`ClassifyResult` contains `selected_label` and `node_id`. The latter is
cluster-owned routing attribution, not a hostname or a claimed remote identity
([RFC-0023](../RFC/RFC-0023-result-node-attribution.md)). This is sufficient
for a small completed-request transparency line such as “Handled by node
`<node_id>`”; it does not justify a topology display or live monitoring.

The native routes already return their safe HTTP failures: malformed bounded
summarize or classify input is `422` with a stable detail; unavailable runtime
is `503`; unavailable capability is `404`; and classification execution
normalizes its internal label failure to `500` / `execution-failed`. A client
can show the status and safe response detail when present, with a generic
safe request-failed message for invalid or unavailable response bodies. It
should not expose raw exceptions, addresses, runtime details, request text, or
invent a separate UI error taxonomy.

## Capability representation

Each view submits the existing body unchanged and renders the existing result;
it adds no model, runtime, node, capability-routing, or generation selector.

* **Chat:** keep a browser-local sequence of existing `ChatMessage` objects and
  submit it with `capability: "chat"`. For the first proof this state is only
  JavaScript memory: no cookies, local storage, server session, request history,
  or server-side conversation record. Reloading clears it.
* **Summarize:** submit one text area value. File selection may use the browser
  `File` API to read a user-selected local file in the browser, decode it as
  UTF-8, check the existing 65,536-byte and non-blank limits, then submit only
  the resulting `text` body. The file is not uploaded as multipart data,
  retained, or sent anywhere other than the already selected native request.
  The native endpoint remains authoritative for validation.
* **Classify:** provide a deliberately plain ordered label entry control (for
  example, one input per row with add/remove actions). Submit the array in
  displayed order, without trimming, case-folding, sorting, deduplicating, or
  rewriting labels. Native validation remains authoritative: 2–32 unique,
  non-empty labels, each at most 128 UTF-8 bytes, with a non-blank source of at
  most 65,536 UTF-8 bytes. Render the exact returned `selected_label`.

The bounds and semantics above follow
[RFC-0051](../RFC/RFC-0051-bounded-text-summarization.md) and
[RFC-0061](../RFC/RFC-0061-bounded-text-classification.md). The first client
should make one ordinary request at a time and need not add streaming, retries,
cancellation, or client-side fallback. Existing one-shot-client timeout choices
are not a browser contract.

## Candidate shapes

### A. Files opened directly

```text
browser file:// page
  -> native Home AI Cluster endpoint
```

This has no page-serving process, but browser requests originate from the
opaque `file:` origin. They are cross-origin requests to the native loopback
application. Since the application currently sends no CORS policy, ordinary
browser `fetch` calls will not be a dependable usable interface. Enabling CORS
for an opaque file origin is a consequential HTTP/privacy boundary and remains
an architectural decision. This shape also leaves the user to locate and open
assets manually.

### B. Separate tiny loopback web-client process

```text
browser
  -> minimal local web-client process
  -> static assets
  -> native Home AI Cluster endpoint
```

If the page makes direct browser-to-native calls, its distinct loopback origin
(including a different port) requires a native CORS allow-list. If instead the
new process proxies requests, CORS can be avoided, but the process becomes a
request-handling proxy: it receives prompts and responses, needs error and
timeout behavior, and creates a new privacy and ownership boundary. Neither is
shown necessary by the current evidence. A second process also adds startup,
port, and lifecycle responsibility.

### C. Static assets served by the native application

```text
browser
  -> existing Home AI Cluster application
  -> static client and native endpoints on one origin
```

Serving a small fixed asset set from the existing loopback application makes
the page and its `POST /v1/*` calls same-origin. It therefore requires no CORS
change, proxy, second process, additional port, persistence, or dependency.
The application remains the sole process that handles native request contents.
Adding this user-facing HTTP surface is nevertheless an architectural decision,
not a hidden implementation detail.

## Recommendation for possible acceptance

Recommend **C: static assets served by the existing native application**, as a
loopback-only first proof, if and only if the project accepts an RFC defining
that surface.

* **Page owner and binding:** the existing ordinary native application owns a
  small fixed page and assets and binds them only where it already binds by
  default: `127.0.0.1:8000`.
* **Requests:** browser JavaScript calls the existing `/v1/chat`,
  `/v1/summarize`, and `/v1/classify` routes directly, on the same origin.
  No proxy is introduced and no CORS change is required.
* **State:** unsubmitted form data and chat messages exist only in the current
  browser page memory. Native requests retain their current behavior; no
  server-side history, account, cookie, database, or persistent browser state
  is added.
* **Authentication:** no authentication decision is needed for this narrow
  loopback proof. It does not authorize LAN or remote-client exposure. This is
  consistent with the existing loopback-only compatibility proof’s explicit
  separation of placeholder bearer handling from real authentication
  ([RFC-0031](../RFC/RFC-0031-minimal-openai-compatible-chat-access.md)).
* **Explicit exclusions:** node/runtime/model selection; topology editing;
  lifecycle controls; continuous monitoring or polling; operator status,
  health, or preflight views; server-side history; accounts or multi-user
  behavior; database; tool calling; web research; a generic agent interface;
  OpenAI-compatibility-only features; a UI framework; and a frontend build
  pipeline.

The recommendation keeps the user facing the cluster’s existing capability
surface, while retaining operator inspection as explicit command-owned work.
It is not a dashboard recommendation.

## Decision boundary

Local implementation details, after an accepted decision, include plain
HTML/CSS/JavaScript layout, accessible form controls, exact page text, local
form validation that mirrors (but never replaces) native validation, and
rendering existing successful or safe failed responses.

An RFC is required before implementation because it would decide a new
user-facing native HTTP surface and its ownership, static asset exposure and
path behavior, loopback and future network boundary, browser-origin/CORS
policy, privacy and retention expectations, and the strict separation from
operator inspection and compatibility access. It should also decide whether
the page is part of each ordinary application composition and the supported
manual proof. These choices affect native request surfaces, privacy boundaries,
operator workflow, and long-term compatibility; they are not merely assets.

## Smallest later implementation sequence

If the project accepts the recommendation, the smallest sequence is:

1. Propose and accept a narrowly scoped RFC for the loopback-only native
   static-client surface and its exclusions.
2. Add one small implementation PR: fixed plain assets served by the existing
   application, with no new API route contract, dependency, CORS policy,
   proxy, persistence, or framework; add focused tests.
3. Add a privacy-safe manual proof/runbook showing one request through each of
   the three native capabilities and one safe failure display, without
   retaining source text or generated content.

## Smallest manual proof

Start an existing ordinary local process on its default loopback address and
open its local page. Submit one operator-supplied chat message, one bounded
text summary, and one bounded text classification with two ordered labels.
For each successful response, verify the page shows the existing content or
exact selected label and the returned `node_id`. Then, with the external runtime
unavailable, submit one request and verify a safe native failure is displayed.
Confirm that a page reload clears the conversation and that no static-cluster
status, health, preflight, control, polling, network exposure, or retained
prompt/response data has appeared. Do not record prompt or response contents in
the proof artifact.
