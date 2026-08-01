# Loopback web client proof

## Status

Current retained proof of the accepted minimal RFC-0062 surface.

## Date

2026-08-01

## Scope

This record covers only the fixed same-origin browser page for `chat`,
`summarize`, and `classify`. It does not change architecture, application
behavior, request contracts, or network exposure.

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
  They are not browser-runtime evidence. The merged implementation suite
  reported 1,153 passing tests.

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
* entered-text Summarize completed, and an explicitly selected UTF-8 README
  file was read locally and summarized;
* Classify completed with ordered labels and had no file selector;
* reload cleared the in-memory Chat conversation; and
* the empty Chat conversation container was hidden before the first message.

No prompt, response, summary, label, file content, screenshot, or node
identifier is retained here.

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

No persistent browser storage is implemented by the merged fixed script. Chat
state is held only in the page's JavaScript memory; the user manually confirmed
that reload clears it. Focused static tests confirm that the script does not
reference `localStorage`, `sessionStorage`, or `indexedDB`.

The implementation contains no polling or background request loop. This record
does not claim browser storage forensics or network-panel observation.

## Known limitations

This proof validates only the accepted minimal RFC-0062 surface. It does not
establish LAN browser access, authentication, authorization, persistent
history, streaming, cancellation, retries, polling, tools, web research,
multimodal input, arbitrary binary file upload, dashboard or operator
functions, topology inspection, status/health/preflight display, model/runtime/
adapter/node selection, arbitrary static-file serving, or OpenAI-compatible
browser access.

The page contains only Chat, Summarize, and Classify, and calls their existing
native same-origin endpoints. Summarize accepts explicitly selected valid UTF-8
text files, reads them locally into its text input, and submits existing JSON
text rather than multipart data. Classify accepts entered text and labels in
displayed order exactly as entered; it has no file selector. The future
Classify file-input question remains separate scope work.

## Conclusion

The retained evidence supports the accepted RFC-0062 minimal loopback browser
surface only. It adds no dashboard, operator console, cluster manager, generic
file-upload system, compatibility interface, or network-exposure change.
