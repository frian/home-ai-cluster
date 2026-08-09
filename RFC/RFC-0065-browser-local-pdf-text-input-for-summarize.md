# RFC-0065: Browser-Local PDF Text Input for Summarize

Status: Accepted

Date: 2026-08-09

## Summary

The loopback web client may select one local text-based PDF for Summarize. The
browser checks an 8 MiB limit, parses the file entirely locally with a narrowly
vendored PDF.js main/worker pair, copies extracted text into the existing
editable Summarize textarea, and submits only current textarea text through
unchanged `POST /v1/summarize`.

PDF is not a Home AI Cluster native document type.

## Problem

`pdftotext document.pdf - | hac summarize` remains sufficient for a technical
CLI operator, but is not usable PDF input for ordinary loopback-browser users.
The gap is caller-side usability, not a missing capability, route, transport, or
runtime feature.

## Goals

- Provide one explicit browser-local PDF-to-text convenience for Summarize.
- Keep PDF bytes and PDF-derived metadata in ephemeral browser memory.
- Preserve the existing text-only request, routing, transport, and result path.
- Make extraction visible and editable before submission.

## Non-goals

This RFC excludes PDF as cluster-native input, binary APIs, multipart/uploads,
server-side parsing, remote PDF transfer, PDF/MIME routing, runtime/model-native
handling, OCR, rendering/previews, annotations/forms/signatures, embedded files,
image or structured-table extraction, password input, metadata processing,
multiple files, drag-and-drop, background processing, generic ingestion,
document IDs/stores, indexing, embeddings, retrieval, RAG, persistence, browser
storage, CDN assets, frontend framework/build expansion, Classify PDF input,
Chat PDF/file input or document context, dashboard, Docker, and Kubernetes.

## Proposal

```text
one selected local PDF
  -> browser checks File.size <= 8 MiB
  -> browser reads and parses bytes locally with PDF.js
  -> extracted text populates existing Summarize textarea
  -> user inspects or edits text
  -> existing non-blank / 65,536-byte UTF-8 validation
  -> unchanged POST /v1/summarize {"text": "..."}
```

There is no automatic submission; only visible current textarea text is sent.
The first supported source is exactly one ordinary text-based PDF. OCR and
image-only/scanned interpretation are excluded. Text order is not guaranteed for
unusual or multi-column layouts, so editability is an accepted UX boundary.

### PDF.js ownership

Implementation may vendor only version-matched production assets:

```text
build/pdf.min.mjs
build/pdf.worker.min.mjs
```

They are fixed same-origin loopback assets, never CDN-loaded, and require no
runtime network access, frontend framework, or general build architecture. The
viewer and unrelated package assets are excluded. The pair is about 1.7 MiB
before HTTP compression. The version is deliberate project-owned vendored code;
upgrades are explicit maintenance work and main/worker always update together.

### Resource bounds

The pre-extraction maximum is **8 MiB (8,388,608 bytes)**, checked from
`File.size` before full-byte reading or PDF.js parsing. Larger files fail locally
and make no request. This conservative simple bound limits allocation and parser
work for one ordinary document.

The post-extraction boundary remains the existing non-blank strict-UTF-8
**65,536-byte** limit; text is not enlarged or truncated. Page count is not a
first contract: file size is known before parsing, while page count requires
parser work. Later evidence is needed before adding it.

### Failures and state

The browser locally and safely reports an oversized file, parse failure,
encrypted/password-protected PDF, no extractable text, blank text, or text over
65,536 bytes. Each makes no request, exposes no parser internals/stack trace,
and creates no large error taxonomy.

PDF bytes, filename, MIME value, page count, metadata, object structure, and
provenance remain ephemeral browser-only state. None enters `/v1/summarize`,
cluster models, history, remote transport, adapters, logs, or persistence. The
server never receives the PDF. Reload/tab close/fresh page discards this state.

## Rationale

Standard browser File APIs provide selected bytes but no PDF parser. The browser
PDF investigation found Mozilla PDF.js to be the focused maintained parser that
accepts local `Uint8Array` data and a worker without a server or network fetch.
Vending only matched minified main/worker assets avoids a viewer, CDN, or stack.

This follows accepted local text-file UX: choose locally, see/edit text, then
use the ordinary request. Parsing ends before an existing text request exists.

## Alternatives considered

Keep operator-owned `pdftotext`: valid for CLI but insufficient browser UX.

Browser-native extraction: rejected because File APIs do not parse PDF text.

Full `pdfjs-dist`/viewer: rejected as larger and broader than text extraction.

Server-side `pdftotext` or upload parsing: rejected because PDF binary reaches
the server and creates ingestion/lifetime/privacy/transport ownership.

Model-native PDF support: rejected as runtime/model dependent and incompatible
with text-only cluster requests and transport.

## Impact

If accepted, later work may vendor the two exact assets, add Summarize-only
browser extraction, enforce 8 MiB, populate the existing textarea, preserve
text validation/submission, add focused tests, and run one retained browser
proof. Classify needs a separate later small RFC or decision after that proof.

`SummarizeRequest`, `/v1/summarize`, the 65,536-byte bound, capabilities,
routing, eligibility, fallback, remote transport, adapters, attribution, and
request-history privacy rules remain unchanged.

## Proof obligations

A later proof must show local text-PDF selection/no-network parsing; visible
editable extraction; only textarea text reaching `/v1/summarize`; no PDF,
filename, or metadata submission; safe local oversized/malformed/encrypted/no-
text failures; existing over-limit rejection; reload clearing state; unchanged
text/text-file behavior; API-only receiver and compatibility process remaining
page-free; and no CORS, upload, multipart, server parser, persistence, OCR, or
document context. Retained evidence excludes private PDF/text, filename, path,
addresses, and runtime/model identity.

## Decision

Accepted.

The loopback web client may accept one explicitly selected local text-based PDF
for Summarize. PDF parsing occurs entirely in browser memory using Mozilla
PDF.js, with only matched vendored `build/pdf.min.mjs` and
`build/pdf.worker.min.mjs` authorized for the first implementation. The PDF is
limited to 8 MiB before parsing; extracted text must satisfy the existing
non-blank 65,536-byte UTF-8 source boundary, populate the existing editable
Summarize textarea, and be submitted only as current textarea text through the
unchanged `/v1/summarize` contract.

The PDF binary and metadata never reach the server, cluster request, remote
transport, runtime adapter, or model. This decision does not authorize OCR,
server-side parsing, upload or multipart input, persistence, document identity,
Classify PDF input, or Chat PDF/document-context support.
