# RFC-0062: Minimal Loopback Web Client

Status: Accepted

Date: 2026-08-01

Author: @frian

## Summary

Home AI Cluster should define two explicit application-composition outcomes:
the **native API application** and the **loopback browser application**. The
browser application consists of fixed plain HTML, CSS, and JavaScript assets and
makes same-origin calls only to the existing native `POST /v1/chat`,
`POST /v1/summarize`, and `POST /v1/classify` routes.

Only the loopback browser application serves the page and assets, and only
loopback-owned launch paths may construct it. The native API application serves
the existing native and internal routes only and remains suitable for explicitly
authorized trusted-LAN receiver binds. Route ownership and socket binding are
separate concerns. This decision therefore adds neither CORS nor a proxy, second
process, authentication mechanism, persistent state, dashboard, operator
console, or new orchestration layer.

## Context

The current native API application is the small capability-centered surface
for `chat`, `summarize`, and `classify`. Its normalized successful results
already provide content or an exact selected label and cluster-owned `node_id`
attribution. The ordinary local-only application is constructed by
`create_app(local_app_composition=...)`; ordinary static-cluster applications
are constructed by `create_static_cluster_app` or
`create_static_cluster_collection_app`, both of which call `create_app(...)`.
The generic `create_app` factory is also used by the dedicated compatibility
process, proof applications, and module-level `home_ai_cluster.main:app`.
The latter is documented both for local development and for historical
trusted-LAN receiver operation. It cannot itself become the unconditional
page-serving seam.

The current `home-ai-cluster-local` launcher accepts an operator-supplied
`--host`; the canonical receiver workflow deliberately uses `--host 0.0.0.0`.
The static-cluster launcher itself has a fixed `127.0.0.1` bind, but its
`create_static_cluster_app` and `create_static_cluster_collection_app` factory
functions are reused by the compatibility composition. Current construction
therefore cannot truthfully add browser routes to those generic factories.

The dedicated OpenAI-compatible process is a separate loopback process on port
8001. It adds its compatibility router to a separately created application and
is intentionally a distinct compatibility boundary.

The prior [minimal local web client investigation](../docs/minimal-local-web-client-investigation.md)
identified a same-origin fixed client served by the ordinary native application
as the smallest candidate. This RFC records that architectural choice; it does
not implement it.

## Problem

The existing native capabilities are usable through HTTP and one-shot CLI
clients, but there is no small browser surface for a person who wishes to use
those same capabilities without constructing HTTP requests. A browser client
must not turn Home AI Cluster into a dashboard, cluster manager, or separate
request-processing layer, and it must preserve local-first, privacy-first,
capability-centered operation.

## Goals

This RFC should:

* define one fixed, loopback-only browser surface over the three existing native
  capabilities;
* reuse existing request, routing, success, attribution, and safe failure
  boundaries without changing them;
* keep browser-origin and privacy boundaries simple by using one origin and one
  existing process;
* retain the distinction between user request views and explicit operator
  inspection surfaces; and
* leave visual design and small static implementation details open.

## Non-goals

This RFC does not define or authorize a dashboard, cluster manager, operator
console, generic agent interface, compatibility client, node/runtime/model/
adapter selector, topology or configuration editor, lifecycle control,
continuous monitoring, polling, background work, streaming, cancellation,
retry, fallback, accounts, multi-user behavior, persistence, database,
prompt/response logging, web research, tools or function calling, file upload
endpoints, multimodal behavior, CORS, proxying, authentication, LAN exposure,
or a frontend framework, Node.js dependency, package manager, bundler, or build
pipeline.

## Decision

### Application composition and launcher ownership

This RFC defines two outcomes with an explicit relationship:

* The **native API application** is the existing lower-level
  `home_ai_cluster.main.create_app` outcome. It exposes the existing native and
  internal routers only. It never serves `/` or `/assets/`. All existing
  generic factories, the module-level `home_ai_cluster.main:app`, compatibility
  construction, proof construction, and LAN receiver construction retain this
  API-only outcome unless a later RFC says otherwise.
* The **loopback browser application** reuses one already composed native API
  application and adds only the fixed page and asset routes defined below. It
  does not alter native routers, orchestration, routing, request/response
  contracts, or application state. It must be constructed only by a launcher
  whose bind is owned as loopback, not by a FastAPI request-time check.

Route ownership and socket binding are separate concerns. A route attached to a
generic FastAPI object does not itself constrain Uvicorn's bind address. The
architectural guarantee is therefore composition plus launcher ownership: no
runtime socket inspection from FastAPI, host-header or client-IP check,
middleware authorization, CORS, token, second server, or network heuristic is
introduced.

The future implementation has one narrow launcher decision in scope:

* `home-ai-cluster-local` constructs the loopback browser application only when
  its selected host is exactly its existing `LOCAL_RUNTIME_HOST`,
  `127.0.0.1`; every other `--host` value constructs the native API application.
  Thus the documented receiver form `home-ai-cluster-local --host 0.0.0.0`
  cannot expose the browser surface.
* `home-ai-cluster-static-cluster` constructs the loopback browser application
  because its existing launcher owns a fixed `STATIC_CLUSTER_HOST` of
  `127.0.0.1`. Its reusable `create_static_cluster_app` and
  `create_static_cluster_collection_app` factories remain API-only, so the
  compatibility composition that calls them cannot receive the page.

No new process or second server is required. This is a narrow application and
launcher-composition change, not a new host option, runtime inspection, or
network-control mechanism.

### Page and asset ownership

The loopback browser application owns one browser page at the fixed path `/`.
That path is currently not an application route, so it is unambiguous and does
not replace an accepted behavior. The page is the only browser entry path; no
redirect is required. The native API application has no route at `/`.

Only the loopback browser application serves a fixed project-owned, read-only
asset namespace at `/assets/`. Those asset paths cannot collide with the
existing `/v1/*` native routes or `/internal/*` transport routes. Assets are
packaged with Home AI Cluster and the application serves only that fixed set. It
exposes no arbitrary filesystem path, directory listing, or user-provided file.
The native API application has no `/assets/` namespace. Cache headers remain an
implementation detail unless they affect privacy or correctness.

There is no deep-link handling, client-side routing, single-page-application
router, or route fallback. A request for an unknown page or asset remains an
ordinary application miss.

The page and assets use plain HTML, CSS, and JavaScript. Their layout, styling,
accessibility details, and narrow cache behavior are implementation details;
they must not require a new runtime dependency or frontend toolchain.

### Existing application compositions

The exact API-only composition boundary is
`home_ai_cluster.main.create_app`: it remains the lower-level factory for native
and internal routes and never attaches browser assets. The exact loopback-browser
composition boundary is a new wrapper applied to an already constructed
API-only application by the two launcher-owned loopback paths above. It alone
attaches `/` and `/assets/`.

The ordinary local-only default launcher and the ordinary static-cluster
launcher are therefore the only ordinary launch paths covered by the first
browser proof. A local runtime receiver started with any non-default host,
including the documented trusted-LAN `0.0.0.0` form, remains API-only. The
module-level `home_ai_cluster.main:app` is API-only; repository documentation
uses that same object for both local development and documented LAN receiver
examples, so it must remain free of the page and assets.

The dedicated `home-ai-cluster-openai-compatibility` process remains unchanged
and API-only except for its existing compatibility router. Its static-cluster
composition must use the API-only static factories and must not serve this page.
It is a deliberately separate compatibility edge, not a browser backend.

### Capability behavior

Browser JavaScript sends direct same-origin requests only to the existing native
endpoints. It does not construct an internal transport envelope, call a runtime,
or make routing choices.

| View | Existing request | Existing successful facts rendered |
| --- | --- | --- |
| Chat | `POST /v1/chat` | returned content and `node_id` |
| Summarize | `POST /v1/summarize` | returned content and `node_id` |
| Classify | `POST /v1/classify` | exact `selected_label` and `node_id` |

The first page deliberately does not display adapter or model fields. They are
already returned for textual results, but they are runtime-specific facts and
are not needed for the smallest user-facing transparency display. `node_id` is
the existing cluster-owned attribution, not a hostname, address, or target
selection control.

Chat keeps an existing-message sequence only in the current page's JavaScript
memory. Reloading or closing the page clears it. The page creates no cookie,
local storage, IndexedDB, browser-cache application state, server session,
server-side conversation history, or database.

Summarize accepts directly entered bounded text. It may also let a user
explicitly select one local UTF-8 text file, read that file in the browser, and
submit only its decoded text in the existing JSON `text` body. It does not use
multipart upload or introduce a file endpoint; the file is not retained or
served back. Client-side byte, decoding, and blank-text checks may give prompt
feedback, but existing native validation remains authoritative.

Classify uses an ordered label-entry control. It submits labels in exactly their
entered and displayed order. The browser must not trim, case-fold,
Unicode-normalize, sort, deduplicate, repair, or otherwise rewrite labels.
Client-side checks may improve immediate usability but do not replace the
existing native validation of source and ordered labels.

The page permits one ordinary request at a time. It adds no streaming,
cancellation protocol, retry, client-side fallback, polling, or background
request behavior.

### Network and origin boundary

The loopback browser application is served only by launcher paths that own the
existing `127.0.0.1:8000` bind. Its calls to `/v1/chat`, `/v1/summarize`, and
`/v1/classify` are direct same-origin browser calls. The API-only application
remains the only application object available to LAN receiver binds. No CORS
middleware, cross-origin allow-list, proxy, second web-client process,
additional port, or browser backend is introduced.

This RFC does not authorize LAN or any non-loopback browser access. It also
introduces no authentication, authorization, token, identity, or account
mechanism for the loopback-only proof. Any change to exposure or access control
requires a separate RFC.

### Error behavior

Existing native safe response failures remain authoritative. The page may render
the returned safe HTTP status and safe response detail, or a stable generic
request-failed presentation when the response cannot be safely interpreted. It
must not add a new public error taxonomy, expose raw exceptions, runtime or
transport addresses, request bodies, response bodies in an error display, or
internal validation details.

## State and retention

The browser client adds no server-side retention. Request text remains on the
existing native request path; chat and summary response content, classification
source text and labels, and selected labels receive no new history, metrics, or
logging treatment.

The page may appear in browser history as a loopback URL, but no request content
may appear in page or asset URLs, query parameters, fragments, or path segments.
In particular, the selected summarize file is read only after explicit user
selection, and only its decoded text travels in the existing summarize JSON
request. The browser sends classification text and labels only in the existing
classify JSON request.

Ordinary logs must not gain prompts, responses, source-file contents, labels,
private addresses, raw exceptions, or authorization values because of this
surface.

## Privacy boundary

The native application remains the only server-side process that receives
ordinary request contents. Same-origin static serving creates no intermediary
that can retain, transform, or forward them. No page analytics, telemetry,
logging, server session, user file retention, or request URL encoding is added.

This retains the existing local-first rule that request content does not leave
the local cluster without an explicit project decision. It also preserves the
existing privacy-safe native validation and error boundaries.

## Compatibility and operator-surface boundary

The page is not OpenAI-compatible access and must not call or be served by the
dedicated compatibility process or any API-only receiver composition. It does
not expose compatibility-only features, including model identifiers, streaming,
tools, or model listing.

Preflight, health, and static-cluster status remain explicit finite
operator commands. The page has no views for those surfaces, topology
declarations, lifecycle actions, nodes, runtimes, models, adapters, process
state, configuration, or capabilities other than its three fixed user request
views. It cannot inspect, select, or edit any of those things.

## First implementation proof

After implementation, the smallest retained proof must:

1. start the loopback-browser composition through one ordinary default
   loopback launcher;
2. open `/` and complete one real local chat request;
3. complete one real local summarize request from entered text;
4. complete one real local summarize request from one explicitly selected small
   UTF-8 text file;
5. complete one real local classify request with ordered labels;
6. confirm existing `node_id` attribution is displayed for each completion;
7. confirm one existing native safe failure is displayed without raw details;
8. confirm page reload clears chat state; and
9. verify that the API-only composition has no `/` or `/assets/` routes,
    including the documented LAN receiver construction; and
10. confirm no CORS request, second process, proxy, storage, cookie, database,
    background polling, operator surface, or non-loopback browser exposure
    exists.

The retained artifact must not contain real prompts, responses, file contents,
labels, private addresses, machine names, paths, or raw logs.

## Implementation sequence

Implementation should use two small PRs:

1. add the API-only and loopback-browser composition seam, narrow launcher
   ownership described above, fixed page/assets, focused composition and
   route/static-asset tests, and the minimal three capability views; and
2. after successful real use, add the privacy-safe proof and only the necessary
   documentation alignment.

The capability views belong together in the first PR because each is a direct
projection of an already executable native capability through one shared fixed
page and serving boundary. Splitting them would add review and temporary-surface
complexity without reducing architectural risk.

## Rationale

Serving fixed assets from a distinct loopback browser composition is the
smallest truthful shape: one process, one loopback origin, and direct use of the
current native contracts. It avoids adding CORS or a request proxy, both of
which create new privacy and HTTP responsibilities, without accidentally
placing browser routes on a deliberate LAN receiver bind. A small `node_id`
display supports transparency without expanding into topology or status
visualization.

The narrow state and file rules make a browser convenient without introducing a
history, upload service, or additional retention surface. Keeping operator and
compatibility access separate preserves the project's explicit boundaries.

## Alternatives considered

### Direct `file://` assets

Directly opened files have an opaque browser origin and require a consequential
cross-origin policy for reliable native `fetch` use. They also leave asset
location and opening workflow outside the existing process. This is not smaller
than same-origin serving.

### Separate loopback web-client process with direct CORS calls

A separate port is a different origin and requires CORS changes to the native
application. It adds process, port, lifecycle, and browser-origin ownership
without providing a needed capability.

### Separate loopback proxy process

A proxy avoids browser CORS only by becoming an additional recipient of prompts
and responses. It would own forwarding, timeout, failure, and privacy behavior,
which is broader than this RFC's purpose.

### Assets served by the existing native application

This is the accepted shape because it has one origin and process, direct
native calls, and no new dependency or request-handling boundary.

### Adopt a frontend framework immediately

A framework, Node.js, package manager, bundler, and build pipeline solve no
identified first-proof problem. Fixed plain assets are sufficient.

### Add a dashboard

A dashboard would blur user requests with monitoring, topology, configuration,
and lifecycle concerns. It exceeds the smallest useful browser surface.

### Use the OpenAI-compatible process as the browser backend

The compatibility process is a separate chat-only translation edge. Reusing it
would couple this native-capability client to compatibility behavior and exclude
the existing summarize and classify seams.

### Delay the UI entirely

The existing HTTP and CLI surfaces remain valid. However, this RFC permits a
small browser proof now without changing their contracts or taking on dashboard
architecture.

## Trade-offs

The page gives a convenient browser surface but deliberately exposes only three
fixed request views. It does not provide persistent conversation, remote access,
or operational visibility. The explicit composition split adds a small launcher
responsibility and makes the default local launcher's selected host meaningful
to application construction. That cost is necessary: mounting page routes alone
cannot guarantee loopback exposure. The resulting API-only receiver and
single-origin browser boundaries are simpler and more private than the
alternatives.

## Impact

A later implementation preserves `create_app` as the API-only
factory and adds a loopback-browser wrapper plus the narrow launcher selection
above. It adds fixed project assets, tests, and proof documentation, but no new
API request or response contract, dependency, runtime, process, database, CORS
policy, compatibility behavior, or LAN exposure. API-only receiver and
compatibility constructions remain unchanged and page-free.

## Acceptance criteria

An implementation is acceptable only when it:

* preserves `create_app` as the API-only native/internal-route factory, with no
  `/` or `/assets/` routes;
* serves `/` and fixed `/assets/` files only from the loopback-browser wrapper
  used by the default local and fixed-loopback static-cluster launchers;
* ensures `home-ai-cluster-local --host 0.0.0.0`, module-level `main:app`,
  reusable static-cluster factories, proof constructions, and compatibility
  constructions remain API-only and page-free;
* makes same-origin direct calls only to the three existing native endpoints;
* prevents LAN browser exposure structurally through composition and launcher
  ownership, not FastAPI bind inspection or request-time network heuristics;
* remains loopback-only by default with no CORS, proxy, second process, or
  authentication;
* preserves native validation, safe failures, routing, and result contracts;
* retains chat only in current page memory and adds no browser or server
  persistence;
* reads a selected summarize file only client-side and submits only decoded text;
* preserves classification labels exactly and in order;
* displays only the accepted successful facts and safe failures;
* contains none of the excluded dashboard, operator, compatibility, lifecycle,
  selector, framework, retention, or background behavior; and
* completes the privacy-safe proof above without retaining sensitive content.

## Decision

Pending.
