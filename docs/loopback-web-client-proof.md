# Loopback web client proof

## Status

Current retained proof of the accepted RFC-0062 loopback browser surface,
accepted RFC-0063 Classify local UTF-8 text-file convenience, and merged
empty-result presentation correction.

## Date

2026-08-02

## Scope

This record covers the fixed same-origin browser page for `chat`, `summarize`,
and `classify`, including the accepted browser-local Classify UTF-8 text-file
convenience. It does not change architecture, application behavior, request
contracts, routing, runtime, transport, composition, compatibility, or network
exposure.

## Evidence sources

This record distinguishes three evidence sources:

* **Reproduced process and HTTP evidence:** the checks below were run against
  merged `main` with harmless synthetic requests. No request or response
  content, selected label, file content, address, path, process detail, or node
  identifier is retained.
* **User-performed browser evidence:** the repository owner performed the
  browser checks below in Firefox during final review. They are not claims of
  Codex or automated-browser execution.
* **Static implementation and test evidence:** merged focused tests and the
  fixed implementation establish route, composition, and script contracts.
  They are not browser-runtime evidence. Merged PR #410 reported three focused
  loopback browser tests passing, Ruff passing, and 1,153 full-suite tests
  passing.

## Environment

The ordinary local launcher was reproduced with its exact loopback host value,
`127.0.0.1`. Its normal port was unavailable because of a process not owned by
this proof, so the launcher used a supported alternate port. The proof-owned
processes and transient files were removed after each check.

## Ordinary local loopback results

The ordinary local launcher on its exact loopback host produced these observed
HTTP results:

* `GET /` returned the fixed HTML page.
* `GET /assets/app.css` and `GET /assets/app.js` returned the fixed assets.
* An unknown page and the generic assets directory were ordinary misses; no
  generic static-directory exposure was observed.
* One harmless Chat request completed.
* One harmless Summarize request completed.
* One harmless Classify request completed.
* Each normalized successful result included node attribution.
* One malformed native Chat request returned a safe client-facing validation
  failure with no raw exception or transport detail retained.

For the normal local launcher and default port, open:

```text
http://127.0.0.1:8000/
```

When an operator selects a supported alternate port, use the same `/` path on
that port.

## Manual browser results

The repository owner manually confirmed in Firefox that:

* the page rendered through the ordinary local loopback launcher;
* Chat completed with visually differentiated user and assistant messages and
  without raw protocol role prefixes;
* each assistant response displayed discreet node attribution, including after
  later turns;
* `Sending…`, `Summarizing…`, and `Classifying…`, each with its CSS spinner,
  appeared while the corresponding request was active and cleared afterward;
* entered-text Summarize completed, and one explicitly selected UTF-8 text file
  was read locally and summarized;
* the Classify view contained one native file input; one explicitly selected
  valid UTF-8 text file populated its existing editable textarea; the populated
  text could be edited before submission; and classification completed through
  the existing Classify path with labels preserved in displayed order and node
  attribution displayed;
* selecting a second valid UTF-8 file replaced the Classify textarea content;
  invalid UTF-8 showed safe local feedback without replacing the existing
  textarea text; and clearing or cancelling selection did not erase textarea
  text;
* reload cleared browser page state;
* empty Summarize and Classify result outputs were hidden before their first
  successful result; successful results became visible and remained visible
  after rendering; and the global semantic `[hidden]` CSS correction worked in
  Firefox; and
* the empty Chat conversation container was hidden before the first message.

No prompt, response, summary, label, selected classification result, file
content, filename, path, screenshot, raw log, or node identifier is retained
here.

## Static implementation and test evidence

Merged PR #410 added the native Classify file input and a browser-local
`TextDecoder("utf-8", { fatal: true })` path. The fixed script assigns valid
decoded text to the existing Classify textarea, then submits only that current
textarea text and the existing ordered labels. It contains no `FormData`,
multipart request, filename field, browser storage, or polling.

The fixed markup initially marks both Summarize and Classify result outputs as
hidden. The existing result renderer reveals an output only when rendering a
successful result, and the stylesheet contains the strong semantic
`[hidden] { display: none !important; }` rule. Focused asset tests cover those
boundaries. Merged validation reported three focused loopback browser tests
passing, Ruff passing, and 1,153 full-suite tests passing. These are static
implementation and test facts, not browser runtime evidence.

## API-only receiver boundary

The ordinary local launcher was reproduced with `--host 0.0.0.0` on a supported
alternate port. Its native API remained available, while `GET /`,
`GET /assets/app.css`, and `GET /assets/app.js` were all ordinary misses.

The accepted boundary is exact: the browser page is attached only when the
selected local-launcher host value is exactly `127.0.0.1`. All other values are
API-only, including `0.0.0.0`, `localhost`, and `::1`. This receiver mode is
for explicitly authorized trusted-LAN operation, not arbitrary untrusted
network exposure.

## Static-cluster result

The ordinary static-cluster executable owns a fixed loopback bind and therefore
uses the browser composition; its reusable application factories remain
API-only. Its required fixed port was unavailable because of a process not
owned by this proof, so the real executable reproduction was not repeated.
No process was stopped or interrupted. The merged static route and composition
tests remain the static contract evidence for this boundary.

## Compatibility boundary

The dedicated OpenAI-compatible application was constructed in process through
its documented composition. `GET /`, `GET /assets/app.css`, and
`GET /assets/app.js` were ordinary misses; the existing compatibility route
remained present with its existing client-error behavior for malformed input.
The loopback browser page is not part of the compatibility surface.

## State and retention

Selected files are read only in the browser after explicit selection and are not
retained by project code. Filenames and other file metadata are neither
submitted nor retained. Only decoded textarea text follows the existing JSON
request path; Classify continues to send its current textarea text and ordered
labels to the existing `POST /v1/classify` endpoint. It sends no multipart
request, file object, filename, or metadata, and no upload endpoint exists.
The native file input may show a selected filename as browser-controlled UI, but
the project adds no separate rendered filename metadata.

No persistent browser storage or project history is implemented by the merged
fixed script. Chat state is held only in the page's JavaScript memory, and the
repository owner manually confirmed reload clearing. Static evidence confirms
no `localStorage`, `sessionStorage`, IndexedDB, `FormData`, multipart request,
filename field, or polling. The implementation adds no cookie, server session,
database, telemetry, analytics, logging, or background request loop.

This record does not claim browser-cache or storage forensics, or network-panel
observation.

## Known limitations

This proof does not establish arbitrary file upload, binary or document
parsing, multiple files, directories, drag-and-drop, file previews, LAN browser
access, authentication, authorization, persistence, history, streaming,
cancellation, retries, polling, tools, web research, dashboard or operator
functions, topology inspection, status/health/preflight display, model/runtime/
adapter/node selection, arbitrary static-file serving, or OpenAI-compatible
browser access.

The page contains only Chat, Summarize, and Classify, and calls their existing
native same-origin endpoints. Summarize and Classify each permit one explicitly
selected local UTF-8 text file to populate the relevant editable textarea.
Classify submits only the current textarea text with unchanged ordered labels;
it adds no filename or metadata submission, multipart request, upload endpoint,
persistence, or additional retention.

## Conclusion

The retained evidence supports the accepted RFC-0062 loopback browser surface,
the accepted RFC-0063 Classify local UTF-8 text-file convenience, and the merged
empty-result presentation correction. Native JSON, privacy, retention,
composition, compatibility, and exposure boundaries remain unchanged.

This remains neither a generic upload system, dashboard, operator console,
cluster manager, compatibility interface, nor remote browser interface.
