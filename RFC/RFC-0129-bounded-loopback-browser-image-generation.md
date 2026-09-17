# RFC-0129: Bounded Loopback Browser Image Generation

Status: Accepted

Date: 2026-09-17

Author: frian

## Summary

Home AI Cluster should expose the already accepted local Image Generation
operation through the existing fixed loopback browser application.

The browser gains one Image Generation request view that accepts exactly one
bounded textual instruction, sends the unchanged RFC-0127 same-origin request:

```text
POST /v1/image-generation
{"instruction":"<TEXT>"}
```

and displays the successful `image/png` response as the current generated
image.

This RFC does not change Image Generation semantics, request or result formats,
routing, runtime composition, retained configuration, remote transport, or
filesystem authority. It adds no gallery, history, persistence, download
service, dimensions, generation controls, generic media abstraction, or LAN
browser access.

The browser surface remains fixed, same-origin, loopback-only, and part of the
existing browser application composition. The API-only application and all LAN
receiver compositions remain browser-free.

## Context

RFC-0062 accepts one fixed loopback browser application over native HAC request
surfaces. It deliberately separates that browser composition from the API-only
application used by receiver and other non-browser paths. The browser uses
plain packaged HTML, CSS, and JavaScript and makes direct same-origin native
requests without CORS, proxying, a second process, a frontend framework, or
server-side browser state.

Later RFCs add Code, bounded browser conversation state, workspace-aware Code,
theme preference, and retained-configuration browser facades while preserving
that same basic composition and origin boundary.

RFC-0120 accepts the semantic capability `image-generation` with one bounded
textual instruction and exactly one bounded still-PNG result. It explicitly
leaves browser projection and generation controls for later decisions.

RFC-0127 then accepts the first human Image Generation operator edge:

```text
POST /v1/image-generation
    -> exact validated image/png bytes

hac image-generation "<INSTRUCTION>"
    -> exact PNG bytes on non-TTY stdout
```

The native route is already the appropriate browser-facing semantic operation.
It accepts only the bounded `instruction` JSON field, uses ordinary local
capability routing, preserves RFC-0059 static caller-local permission, and is
covered by RFC-0082 confirmed-disconnect cancellation.

RFC-0128 adds an optional retained local stable-diffusion.cpp companion for
ordinary local composition but explicitly adds no browser Image Generation
configuration or broader browser authority.

The remaining gap is therefore presentation and request access in the existing
loopback browser, not a new Image Generation execution path.

## Problem

A user can now generate an image through the native HTTP operation or the
one-shot CLI, but the fixed loopback browser has no Image Generation view.

Adding that view could be made unnecessarily broad by introducing any of the
following:

```text
browser-specific image API
JSON/base64 image envelopes
multipart responses
result URLs
temporary server files
galleries
history
filesystem destinations
generic Media / Asset / Blob abstractions
runtime or model controls
```

None is required.

The existing native operation already provides the complete semantic input and
validated image result. The smallest coherent browser step is to project that
operation directly into the existing same-origin user request surface.

## Goals

This RFC aims to:

- add one Image Generation request view to the existing loopback browser;
- reuse the unchanged RFC-0127 `POST /v1/image-generation` operation directly;
- accept only the existing bounded textual `instruction` input;
- display exactly one current successful generated image;
- keep all browser Image Generation state ephemeral and current-page-only;
- preserve the existing fixed same-origin loopback browser composition;
- preserve RFC-0127 routing, static permission, failure, and cancellation
  boundaries; and
- avoid storage, generic binary/media architecture, runtime controls, or
  broader browser authority.

## Non-goals

This RFC does not add or define:

- caller-selected width, height, aspect ratio, seed, sampler, steps,
  CFG/guidance, scheduler, negative prompt, style, quality, or other generation
  controls;
- model or runtime selection;
- multiple candidates, batch generation, galleries, history, favorites, or
  collections;
- server-side image storage, temporary files, result URLs, object storage, or
  asset identifiers;
- HAC-owned download paths, filenames, save destinations, overwrite behavior,
  workspace authority, or filesystem APIs;
- JSON/base64 Image Generation responses, multipart, data URLs, or generic
  `Media`, `Asset`, `Blob`, `Attachment`, or binary-result abstractions;
- image input, vision, OCR, image editing, image-to-image transformation, or
  multimodal Chat;
- Image Generation configuration editing in the browser;
- capability discovery, capability-dependent view hiding, health/status
  probing, runtime observation, or model inspection;
- responsive-layout redesign;
- LAN, Wi-Fi, remote, authenticated, or non-loopback browser access;
- CORS, proxying, a second browser process, frontend framework, Node.js,
  package manager, bundler, or build pipeline;
- simultaneous active requests across browser capability views, or any change
  to RFC-0062's existing browser-wide one-ordinary-request-at-a-time boundary;
- changes to existing browser Chat, Code, Summarize, Classify, workspace,
  configuration, or theme semantics; or
- remote/receiver Image Generation or transport changes.

Browser-native user actions outside HAC ownership, such as a browser's own
context-menu save behavior for a displayed image, are not HAC filesystem
authority and are not specified by this RFC.

## Proposal

### One fixed Image Generation view

The existing loopback browser application gains one fixed Image Generation
request view alongside the existing user request views.

The view contains only the controls needed for the accepted semantic operation:

```text
instruction
Generate
current image / safe failure
```

Exact labels, element types, layout, styling, and visual placement remain small
implementation details. Adding this view does not turn the page into a
dashboard, media library, runtime console, or configuration surface.

The view exists as a fixed part of the browser assets. The browser does not
probe current capabilities, runtime health, retained configuration, or
composition facts to decide whether to show it.

Presence of the view means only:

> this browser can submit the native Image Generation operation

It does not claim that the currently running composition has an eligible Image
Generation candidate.

### Unchanged request contract

Browser JavaScript sends a direct same-origin request only to the existing
native route:

```text
POST /v1/image-generation
Content-Type: application/json

{"instruction":"<TEXT>"}
```

The browser adds no alternate endpoint and no browser-private request shape.

`instruction` retains RFC-0120/RFC-0127 semantics and bounds. The browser may
perform small client-side blank-input checks for immediate usability, but the
native semantic validation remains authoritative.

No browser field exists for capability, dimensions, aspect ratio, model,
runtime, output format, file path, or generic options.

### Direct PNG success presentation

A successful response is the unchanged RFC-0127 success:

```text
Content-Type: image/png
body: exact validated ImageGenerationResult.image_bytes
```

The browser consumes those bytes only for local presentation and displays the
image in the Image Generation view. It does not ask HAC to convert, wrap,
store, name, or publish the result.

Browser-local decoding and presentation do not change the HAC result contract.
An implementation may use the browser's ordinary in-memory binary/image
facilities to attach the response to an image element. Any browser-local object
reference used only to render the current response is presentation state, not a
HAC result URL, asset identifier, persistence mechanism, or new core
abstraction.

The browser must not introduce a server result URL, JSON/base64 envelope, or
persistent image cache controlled by HAC. Visual CSS scaling to fit the current
view is presentation only and must not be interpreted as generation width or
height semantics.

RFC-0127 deliberately exposes only the primary PNG projection on this native
route. The browser therefore does not add `node_id`, adapter, model, runtime, or
other metadata by inventing headers, companion requests, multipart bodies, or
another response envelope.

### Ephemeral current-image state

The browser may retain at most one current successful generated image in the
current page's JavaScript/DOM state for display.

It does not retain an ordered image history, previous candidates, thumbnails,
prompts associated with prior images, server-side state, cookies, IndexedDB, or
application local storage for generated image content.

A later successful generation may replace the current displayed image. Page
reload or close clears the browser-owned current-image state. Implementations
must not accumulate unreachable prior generated images as application-retained
history.

Exact visual behavior while a replacement request is pending, and whether a
previous successful image remains visible after a later safe failure, are
presentation details provided the application still retains no more than one
current successful image.

### Request activity and cancellation

RFC-0062's existing browser-wide one-ordinary-request-at-a-time boundary
remains unchanged. The Image Generation view participates in that same
boundary; this RFC does not authorize simultaneous active requests across
capability views. Any future change to that concurrency boundary requires a
separate architectural decision.

It adds no background generation, polling, automatic retry, parallel candidate
generation, queue, job object, progress protocol, or cancellation button.

RFC-0127 already adds `POST /v1/image-generation` to RFC-0082 confirmed-client-
disconnect cancellation. Navigation, page close, or another genuine browser
disconnect may therefore trigger the existing HAC-side cancellation behavior.
This RFC adds no stronger promise that `sd-server` or another runtime stops
work.

### Failure presentation

Existing native Image Generation and browser safe-failure boundaries remain
authoritative.

The page may show a bounded safe failure derived from the native response or a
stable generic request-failed presentation when the response cannot be safely
interpreted. It must not expose raw exceptions, runtime addresses, model paths,
request/response bodies as diagnostics, transport internals, or runtime-private
errors.

A failed Image Generation request creates no stored image, history item,
temporary server file, or fallback representation.

### Loopback and same-origin boundary

RFC-0062 remains authoritative for browser composition.

The Image Generation view and its assets exist only in the existing loopback
browser application. The API-only application remains free of `/` and
`/assets/`, and receiver/LAN application compositions remain browser-free.

The browser calls the relative native route on the same origin. No CORS policy,
cross-origin allow-list, proxy, alternate browser backend, second port, or
network discovery is introduced.

This RFC does not authorize access to the browser from another machine,
smartphone, tablet, or LAN address. Such access changes the accepted browser
network-authority boundary and requires a separate RFC.

### Static-cluster behavior

The fixed browser assets may also be present in the existing loopback static-
cluster browser composition, as already accepted for other browser views.

That does not expand RFC-0059 caller-local static routing permission.
`image-generation` remains absent from that permission vocabulary. Therefore:

```text
fixed Image Generation browser view exists
    +
physical Image Generation binding may exist
    +
caller-local static permission excludes image-generation
    ->
ordinary no-capability failure
```

The browser must not route around that outcome, call a local adapter directly,
contact `sd-server`, use retained companion facts as permission, or attempt
remote Image Generation.

No capability probing or conditional hiding is required to conceal this honest
failure state.

### Privacy and retention

The textual instruction travels only through the existing native request body.
It must not be copied into URLs, query parameters, fragments, telemetry,
analytics, ordinary logs, filenames, or server-side image metadata because of
this browser view.

Generated PNG bytes receive no new server-side retention or logging treatment.
Browser display state remains local to the current page. Theme storage accepted
by RFC-0084 remains the only browser-local persistent presentation preference;
this RFC adds no persistent generated-content state.

## Compatibility and impact

Existing native HTTP, CLI, routing, adapter, runtime, retained configuration,
remote transport, receiver, filesystem, and Image Generation contracts remain
unchanged.

The only architectural addition is one fixed loopback-browser projection of the
already accepted native operation.

Implementation may therefore be limited to the existing packaged browser
assets and focused browser/application tests. It does not require core request
or result changes, adapter changes, runtime changes, retained configuration
changes, new dependencies, or protocol changes.

Exact browser navigation/button ordering is a presentation detail and may be
adjusted in the implementation without becoming part of this RFC, provided no
capability or authority semantics change.

## Proof expectations

A later implementation must prove at least that:

1. the loopback browser exposes one Image Generation request view;
2. one submitted instruction produces exactly one same-origin
   `POST /v1/image-generation` request using the existing closed JSON shape;
3. the implementation neither introduces nor relies on simultaneous active
   browser capability requests and preserves RFC-0062's existing browser-wide
   one-ordinary-request-at-a-time boundary;
4. one successful `image/png` response is displayed without a browser-specific
   server endpoint, JSON/base64 response, multipart body, result URL, temporary
   server file, or generic media abstraction;
5. browser state retains at most one current successful image and page reload
   clears it;
6. safe failure rendering does not expose raw runtime/transport details or
   create retained image state;
7. no `node_id`, adapter, model, runtime, or invented metadata envelope is added
   to the raw-PNG native projection;
8. existing RFC-0082 behavior remains applicable without adding jobs, polling,
   retry, or runtime-termination promises;
9. the API-only application and receiver/LAN compositions still expose no
   browser page or assets;
10. static-cluster browser submission does not bypass unchanged RFC-0059 caller-
   local permission and does not gain remote Image Generation;
11. no dimensions, generation controls, image input/editing, gallery/history,
    filesystem authority, Image Generation browser configuration, LAN browser
    access, CORS, proxy, frontend framework, dependency, or persistence surface
    is introduced.

## Alternatives considered

### Browser-specific JSON/base64 result

Rejected. RFC-0127 already provides the exact validated PNG representation.
Base64 would inflate and textualize it while creating a second result contract.

### Result URL or temporary file

Rejected. Either requires storage, naming, lifetime, cleanup, and additional
server authority that the current operation does not need.

### Gallery or history

Rejected. The demonstrated need is to generate and view one image, not to build
a media library or persistent application state.

### Add dimensions in the same RFC

Deferred. Width and height change the normalized Image Generation request
semantics accepted by RFC-0120 and the native contract projected by RFC-0127.
They are useful but architecturally distinct from exposing the already accepted
operation in the browser.

### Add responsive redesign now

Deferred as a separate user-interface step. Responsive presentation does not
need to be coupled to Image Generation semantics or this browser authority
change.

### Permit LAN browser access now

Deferred. RFC-0062 deliberately makes browser composition loopback-only and
keeps LAN receiver compositions API-only. Reaching HAC from another device is a
separate network-authority and security decision.

### Hide Image Generation when unavailable

Rejected for this step. Capability probing, runtime observation, or retained-
configuration inference would add a second concern. The fixed browser is a
request surface, not a live capability/status dashboard.

## Trade-offs

The fixed view can be visible when the running composition cannot currently
execute Image Generation, especially under the unchanged static-cluster
permission boundary. That may produce an ordinary safe no-capability failure.
This is preferable to adding capability discovery or status coupling merely to
hide a request control.

The browser exposes no cluster attribution for the generated image because the
accepted native projection is raw PNG only. Preserving that existing contract
keeps this step smaller than inventing metadata transport for one presentation
surface.

The page keeps only one current image, so it is not a gallery and provides no
built-in history. That limitation is deliberate and consistent with the
project's current ephemeral browser model.

## Open questions

None within this proposed bounded contract.

Responsive layout, browser navigation polish, non-loopback browser access,
caller-selected Image Generation dimensions, browser Image Generation
configuration, remote Image Generation, output persistence, and alternate image
formats remain separate possible decisions or implementation steps according to
their existing architectural boundaries.

## Decision

Home AI Cluster accepts one bounded Image Generation request view in the
existing fixed loopback browser application. It reuses the unchanged RFC-0127
same-origin `POST /v1/image-generation` operation, accepts only the existing
bounded textual instruction, displays the unchanged successful raw `image/png`
result, and retains at most one current successful image in ephemeral current-
page state. It preserves RFC-0062's browser-wide one-ordinary-request-at-a-time
boundary, loopback-only and same-origin browser composition, RFC-0059 static
caller-local permission and honest no-capability behavior, and RFC-0082
disconnect cancellation. It adds no dimensions, generation controls,
gallery/history, persistence, filesystem authority, browser Image Generation
configuration, remote Image Generation, generic media abstraction, responsive
redesign, or LAN/non-loopback browser access.
