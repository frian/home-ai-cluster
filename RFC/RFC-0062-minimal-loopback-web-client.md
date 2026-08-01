# RFC-0062: Minimal Loopback Web Client

Status: Draft

Date: 2026-08-01

Author: @frian

## Summary

Home AI Cluster should serve one deliberately small browser client from the
existing native application. The client consists of fixed plain HTML, CSS, and
JavaScript assets and makes same-origin calls only to the existing native
`POST /v1/chat`, `POST /v1/summarize`, and `POST /v1/classify` routes.

The first surface is loopback-only through the ordinary application's existing
default `127.0.0.1:8000` bind. It adds neither CORS nor a proxy, second process,
authentication mechanism, persistent state, dashboard, operator console, or
new orchestration layer.

## Context

The current ordinary native application is the small capability-centered surface
for `chat`, `summarize`, and `classify`. Its normalized successful results
already provide content or an exact selected label and cluster-owned `node_id`
attribution. The ordinary local-only application is constructed by
`create_app(local_app_composition=...)`; ordinary static-cluster applications
are constructed by `create_static_cluster_app` or
`create_static_cluster_collection_app`, both of which call `create_app(...)`.
The generic `create_app` factory is also used by the dedicated compatibility
process, so it cannot itself become the unconditional page-serving seam.

The dedicated OpenAI-compatible process is a separate loopback process on port
8001. It adds its compatibility router to a separately created application and
is intentionally a distinct compatibility boundary.

The prior [minimal local web client investigation](../docs/minimal-local-web-client-investigation.md)
identified a same-origin fixed client served by the ordinary native application
as the smallest candidate. This RFC proposes that architectural choice; it does
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

### Page and asset ownership

The existing ordinary native application owns one browser page at the fixed path
`/`. That path is currently not an application route, so it is unambiguous and
does not replace an accepted behavior. The page is the only browser entry path;
no redirect is required.

The application also serves a fixed project-owned, read-only asset namespace at
`/assets/`. Those asset paths cannot collide with the existing `/v1/*` native
routes or `/internal/*` transport routes. Assets are packaged with Home AI
Cluster and the application serves only that fixed set. It exposes no arbitrary
filesystem path, directory listing, or user-provided file. Cache headers remain
an implementation detail unless they affect privacy or correctness.

There is no deep-link handling, client-side routing, single-page-application
router, or route fallback. A request for an unknown page or asset remains an
ordinary application miss.

The page and assets use plain HTML, CSS, and JavaScript. Their layout, styling,
accessibility details, and narrow cache behavior are implementation details;
they must not require a new runtime dependency or frontend toolchain.

### Existing application compositions

This RFC accepts one explicit **ordinary native application composition seam**:
a small application-construction step, following generic `create_app` creation,
that attaches the fixed browser page and assets only to an ordinary native
application. The ordinary local-only constructor and both ordinary
static-cluster constructors must use that same step. It is the exact accepted
boundary that makes the page available in both ordinary compositions without
changing request routing or creating composition-specific browser behavior.

The existing generic `home_ai_cluster.main.create_app` remains a lower-level
native-router factory and must not unconditionally attach the page, because the
dedicated compatibility process also uses it.

The dedicated `home-ai-cluster-openai-compatibility` process remains unchanged
and must not serve this page. It is a deliberately separate compatibility edge,
not a browser backend.

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

The page is served only by the existing ordinary application's loopback default:
`127.0.0.1:8000`. Its calls to `/v1/chat`, `/v1/summarize`, and `/v1/classify`
are direct same-origin browser calls. No CORS middleware, cross-origin
allow-list, proxy, second web-client process, additional port, or browser
backend is introduced.

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
dedicated compatibility process. It does not expose compatibility-only features,
including model identifiers, streaming, tools, or model listing.

Preflight, health, and static-cluster status remain explicit finite
operator commands. The page has no views for those surfaces, topology
declarations, lifecycle actions, nodes, runtimes, models, adapters, process
state, configuration, or capabilities other than its three fixed user request
views. It cannot inspect, select, or edit any of those things.

## First implementation proof

After implementation, the smallest retained proof must:

1. start the ordinary native application on its default loopback address;
2. open `/` and complete one real local chat request;
3. complete one real local summarize request from entered text;
4. complete one real local summarize request from one explicitly selected small
   UTF-8 text file;
5. complete one real local classify request with ordered labels;
6. confirm existing `node_id` attribution is displayed for each completion;
7. confirm one existing native safe failure is displayed without raw details;
8. confirm page reload clears chat state; and
9. confirm no CORS request, second process, proxy, storage, cookie, database,
   background polling, operator surface, or non-loopback exposure exists.

The retained artifact must not contain real prompts, responses, file contents,
labels, private addresses, machine names, paths, or raw logs.

## Implementation sequence

If accepted, implementation should use two small PRs:

1. add the fixed page/assets, serving seam, focused route/static-asset tests,
   and the minimal three capability views; and
2. after successful real use, add the privacy-safe proof and only the necessary
   documentation alignment.

The capability views belong together in the first PR because each is a direct
projection of an already executable native capability through one shared fixed
page and serving boundary. Splitting them would add review and temporary-surface
complexity without reducing architectural risk.

## Rationale

Serving fixed assets from the existing application is the smallest truthful
shape: one process, one loopback origin, and direct use of the current native
contracts. It avoids adding CORS or a request proxy, both of which create new
privacy and HTTP responsibilities. A small `node_id` display supports
transparency without expanding into topology or status visualization.

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

This is the accepted proposal because it has one origin and process, direct
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
or operational visibility. Serving assets from the native application modestly
expands its HTTP responsibility, which is why this is an RFC rather than an
implementation detail. The resulting single-origin boundary is simpler and
more private than the alternatives.

## Impact

If accepted, a later implementation changes the ordinary native application
only to serve fixed project assets and a page alongside unchanged native routes.
It adds tests and proof documentation, but no new API request or response
contract, dependency, runtime, process, database, CORS policy, compatibility
behavior, or network exposure. Existing ordinary local-only and static-cluster
processes share the page through the accepted ordinary-native composition seam;
the generic factory and dedicated compatibility process remain unchanged.

## Acceptance criteria

An implementation is acceptable only when it:

* serves `/` and fixed `/assets/` files from both ordinary native compositions
  through the same accepted ordinary-native composition seam;
* makes same-origin direct calls only to the three existing native endpoints;
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
