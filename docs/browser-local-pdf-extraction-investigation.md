# Browser-Local PDF Extraction Investigation

Status: Complete

## Question

Which browser-local PDF text-extraction option is small, maintainable,
privacy-preserving, and sufficient for the existing loopback web client?

This investigation does not authorize PDF support, an RFC, or an implementation.

## Established Home AI Cluster facts

The accepted browser client reads one user-selected UTF-8 text file locally,
populates an editable Summarize or Classify textarea, and submits only current
text through unchanged JSON. It has no upload route, multipart body, server-side
file, browser persistence, document identifier, or metadata submission.
[RFC-0062](../RFC/RFC-0062-minimal-loopback-web-client.md) and
[RFC-0063](../RFC/RFC-0063-classify-local-text-file-input.md) deliberately
exclude PDF and other document parsing.

`summarize` and `classify` retain non-blank strict-UTF-8 65,536-byte source
validation before routing or transport. The PDF must remain entirely in browser
memory; only user-visible current textarea text may reach existing endpoints.
[RFC-0051](../RFC/RFC-0051-bounded-text-summarization.md) and
[RFC-0061](../RFC/RFC-0061-bounded-text-classification.md) remain authoritative.
Chat is outside this investigation.

The prior [bounded local PDF investigation](bounded-local-pdf-text-extraction-investigation.md)
found external extraction sufficient for CLI users but not a usable browser
experience. It also preserves no OCR, no ingestion, and no document context.

## External technical evidence

### A. Browser-native functionality only

The standard browser [File API](https://developer.mozilla.org/en-US/docs/Web/API/File)
gives JavaScript a user-selected `File` and its bytes, but no PDF text-extraction
API. Browser-native selection is sufficient for local byte access, not parsing;
a dependency is required.

### B. Focused dependency: Mozilla PDF.js / `pdfjs-dist`

PDF.js is a Mozilla-supported JavaScript PDF parser and renderer. Its official
project publishes the prebuilt [`pdfjs-dist`](https://github.com/mozilla/pdf.js#using-pdfjs-in-a-web-application)
distribution under Apache-2.0. Its [API](https://mozilla.github.io/pdf.js/api/draft/module-pdfjsLib.html)
accepts caller-provided `Uint8Array` data, exposes a `PDFWorker`, and supplies
page text-content items. A selected file can remain local: no URL, network
fetch, server component, or PDF upload is required.

Current official package metadata observed on 2026-08-08 reports version
`6.2.108`, 550 package files, 8.4 MB packed, and 34.5 MB unpacked. The full
distribution is not an acceptable web-client asset choice. Its two minified
production modules are materially smaller: `build/pdf.min.mjs` is about 455 KB
and `build/pdf.worker.min.mjs` about 1.26 MB (roughly 1.7 MB before HTTP
compression). The package declares no runtime dependencies. Releases remain
active through 2026-07-28; its [license](https://github.com/mozilla/pdf.js/blob/master/LICENSE)
is Apache-2.0.

PDF.js documents separate main and worker builds. A future implementation must
vendor exactly those version-matched minified modules as fixed loopback assets,
configure the worker URL to the same-origin worker asset, and never use a CDN.
This adds two reviewed assets but no frontend framework, Node runtime, bundler,
or project-wide frontend build architecture. It must not ship the viewer, CMaps,
fonts, WASM, source maps, or the rest of the package without new evidence.

The needed surface is small: validate `File.size`; read a selected file to a
`Uint8Array`; load it; iterate pages; obtain text content; join text items;
destroy document/worker; and populate the existing textarea. This is parsing,
not rendering, preview, annotation, attachment, metadata, or a document app.

PDF.js can extract text objects from ordinary text-based PDFs. It cannot create
text from image-only scans without OCR. Password-protected documents require a
password API and must fail locally in a first increment. Malformed parse
failures, empty text, and blank/over-limit text must show safe local feedback
and make no request. Text-item order is not a reading-order guarantee for
multi-column or unusual layouts, making the editable textarea essential.

### C. System extractor via browser/server

A browser cannot invoke an installed extractor without a server, native bridge,
or upload-like handoff. Giving the loopback process the PDF would be server-side
binary ingestion, contrary to the established browser-local boundary. Reject it.

### D. Upload or server-side parsing

This would require multipart or a binary endpoint, temporary server files,
parser/lifetime/error ownership, and potentially remote PDF transport. It is
not smaller and remains rejected.

## Resource, privacy, and UX boundary

```text
one selected PDF
  -> browser checks File.size before ArrayBuffer allocation and parsing
  -> PDF.js parses only browser-memory bytes
  -> browser writes extracted text to existing Summarize textarea
  -> user inspects or edits it
  -> existing 65,536-byte UTF-8 validation
  -> unchanged /v1/summarize JSON request
```

A future RFC must decide a conservative pre-extraction PDF-byte limit and
retain the post-extraction 65,536-byte text limit. It should not invent a page
limit first: `File.size` is known before parsing, while document page count
needs parsing. Revisit page count only if resource evidence shows byte limits
are insufficient.

Filename, MIME value, page count, PDF metadata, object structure, and extraction
provenance need not leave browser memory or enter application state. The native
input may display a filename as browser-controlled local UI only. Reload/tab
close can discard PDF and text just as current page state does. There is no
automatic submission: failures and strange layout remain visible, and only
edited text is sent.

One local helper may be reused later, but it must remain a PDF-specific browser
function, not a generic loader/parser/ingestion abstraction. Summarize comes
first; Classify is a separate later decision.

## Project inference

PDF.js is the smallest acceptable credible choice. Browser-native APIs cannot
parse PDF text; the full distribution is disproportionately broad, but the two
matched minified main/worker assets are a bounded approximately 1.7-MB addition
with no runtime dependency tree or framework. The worker is asset packaging,
not a second process or network recipient.

The boundary preserves local-first, privacy-first, engine-independent, and
capability-centered architecture: no PDF binary reaches requests, transport,
runtimes, or models. It creates no PDF capability/type, MIME routing,
persistence, indexing, embeddings, retrieval, RAG, OCR, streaming, dashboard,
or chat-document context.

## Outcome

**Outcome B — one specific lightweight browser-side dependency is a credible
fit: Mozilla PDF.js (`pdfjs-dist`), vendored as only its matched minified main
and worker modules.**

Recommend this sequence only:

1. narrow RFC for browser-local PDF-to-text preprocessing;
2. Summarize-only implementation with a decided PDF-byte limit, text-based PDF
   extraction, existing editable textarea, and unchanged request;
3. focused browser proof; and
4. separate small Classify reuse PR only if that proof succeeds.

The RFC must decide the byte limit, exact asset/version/update ownership, safe
local failure presentation, and test evidence. It must not authorize PDF as a
cluster-native document type.
