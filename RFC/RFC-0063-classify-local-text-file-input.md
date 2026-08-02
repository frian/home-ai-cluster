# RFC-0063: Classify Local Text File Input

Status: Accepted

Date: 2026-08-02

Author: @frian

## Summary

Home AI Cluster should extend the accepted RFC-0062 loopback browser surface so
the Classify view may let a user explicitly select one local UTF-8 text file.
The browser reads the file locally, strictly decodes it as UTF-8, and places the
decoded text in the existing Classify source textarea. The ordinary form then
submits the current textarea value through the unchanged native JSON contract:

```json
{
  "text": "<current textarea text>",
  "labels": ["...", "..."]
}
```

This is a small browser convenience over the existing bounded text source. It
does not create a classification capability, file-ingestion architecture, HTTP
upload mechanism, or server-side file contract.

## Problem

RFC-0062 permits the Summarize view to populate its bounded text area from one
explicitly selected local UTF-8 text file. Classify instead accepts directly
entered source text and ordered labels. A user who already has a small local
text file must copy and paste it before using Classify.

Copy and paste remains usable, and the convenience is modest. But the present
asymmetry is explicit accepted browser-surface scope, rather than an unrecorded
implementation detail. Adding the Classify selector therefore needs a narrow
decision before code changes.

## Goals

- Remove one small copy-and-paste inconvenience for existing local UTF-8 text.
- Make Summarize and Classify source entry consistent where that is appropriate.
- Preserve the existing bounded text, JSON, privacy, and local-first model.
- Keep the addition plain, local, explicit, dependency-free, and limited to
  one user-selected file.

## Non-goals

This RFC does not authorize:

- PDF, DOCX, HTML, image, audio, archive, spreadsheet, or other document
  parsing; binary input; MIME-based behavior; encoding selection; or automatic
  encoding detection;
- multiple files, directory selection, drag-and-drop, file previews,
  project-rendered filename metadata, remote URLs, cloud storage, or clipboard
  monitoring;
- multipart forms, upload endpoints, server-side temporary files, document
  chunking, batch classification, background work, polling, persistence, or
  history;
- a classification contract change, generic shared file-processing
  architecture, frontend framework, build tooling, LAN browser access, or
  compatibility API expansion; or
- changes to browser composition, loopback ownership, API-only receivers,
  static-cluster boundaries, same-origin behavior, routing, runtime adapters,
  transport, or network exposure.

## Proposal

### Explicit selection and source behavior

The Classify view may expose one native file input. The browser reads a file
only after explicit user selection, and only one file may be selected at a
time. Selecting another valid file replaces the Classify source textarea with
newly decoded text. Clearing the native file input does not erase text already
present in that textarea.

The user may edit text populated from a file before submitting. The submitted
source is always the current textarea value, never a retained file object.

### Text validation boundary

The browser must strictly decode selected content as UTF-8. It must not use
fallback encoding detection or replacement-character decoding. The existing
Classify source limit of 65,536 UTF-8 bytes and existing non-blank source rule
remain unchanged. Native request validation remains authoritative.

### Request and execution boundary

The only ordinary request remains `POST /v1/classify` with its existing JSON
body, current textarea text, and exact ordered labels. No filename, file
object, MIME type, path, modification time, or other file metadata is included
in that request.

This RFC preserves exact ordered-label handling, exact selected-label behavior,
native safe failures, routing, capability eligibility, runtime adapters,
internal transport, and normalized result attribution. It creates no endpoint,
request-contract, result-contract, or execution change.

### Privacy and retention

Selected content is read locally by the browser; only the current decoded
textarea text reaches the existing native Classify endpoint. No multipart
submission or file-upload endpoint is introduced, and no server-side file
object exists.

No selected file or filename is persisted. This adds no browser storage,
cookie, server session, database, history, telemetry, or analytics. It also
authorizes no new logging of source text, labels, filename, path, or selected
label.

A native HTML file input may display its selected filename as browser-controlled
local UI. The project adds no separate rendered filename metadata, and project
code neither submits nor retains the filename.

### Error behavior

If strict UTF-8 decoding fails, the page shows safe local feedback and does not
replace the existing textarea text. A valid but blank decoded value, or a valid
decoded value above the existing byte limit, may populate the textarea; the
ordinary existing blank-text and size validation applies before or during
submission.

A later request failure leaves the current form values available and uses the
existing safe failure presentation. The page adds no public error taxonomy and
must not expose raw exceptions, file content, paths, runtime details, or
transport details.

### Relationship to RFC-0062

RFC-0062 remains accepted architectural history and is not edited in place. If
accepted, this RFC supersedes only RFC-0062's Classify browser-input asymmetry:
the absence of a Classify local UTF-8 text-file selector. It does not supersede
RFC-0062 as a whole.

All other RFC-0062 decisions remain unchanged, including Summarize behavior,
browser composition, exact-loopback launcher ownership, API-only receiver
boundaries, static-cluster boundaries, compatibility boundaries, and same-origin
behavior.

## Rationale

The proposal uses the same bounded-text path a user already reaches by pasting
text. Keeping the textarea as the only submitted source means the browser does
not need an upload protocol, a server-side file representation, or a new
classification contract. It remains local-first and privacy-first because no
additional process, origin, storage, or recipient is introduced.

The narrow decision also preserves an important project rule: an accepted
user-facing boundary should not be changed implicitly by a later implementation
PR. A focused successor RFC is clearer than rewriting accepted RFC-0062.

## Alternatives considered

### Keep copy and paste only

This is the smallest possible surface and remains sufficient for every current
workflow. It does not remove the modest friction for a user with local text
already in a file.

### Treat the selector as an RFC-0062 implementation detail

Rejected. RFC-0062 expressly permits the file convenience for Summarize and
specifies direct text plus labels for Classify. The existing page, tests, proof,
and documentation make that asymmetry observable.

### Edit accepted RFC-0062 in place

Rejected. Accepted RFCs are project memory. Editing its reviewed text would
erase the boundary that was accepted; this focused successor can supersede only
the relevant clause while preserving the rest.

### Add a generic shared file-input abstraction

Rejected. One additional local control does not justify a shared frontend
framework or file-processing architecture. Any reuse can remain conceptual or
local unless later duplication proves materially harmful.

### Add a new narrow successor RFC

Recommended. It makes the small user-surface extension explicit while keeping
all existing execution, privacy, and exposure boundaries intact.

## Trade-offs

The convenience is modest, and another control slightly increases the browser
surface plus its test and documentation burden. A native file input may also
visually expose the selected filename to the local user as browser UI.

Those costs are acceptable for the bounded consistency and reduced copy-paste
friction. Preserving the textarea as the only submitted source keeps the
implementation simple and prevents the control from becoming a generic file
surface.

## Impact

If accepted, the smallest implementation may add one native file input to the
Classify view, minimal plain JavaScript local reading and strict UTF-8 decoding,
and textarea population. It may reuse existing size and safe-feedback patterns
where practical, add focused browser-asset contract tests, and align the
smallest current documentation after implementation.

It does not require a shared abstraction between Summarize and Classify. It
does not change current behavior until a later implementation PR is accepted.

## First implementation proof

After implementation, a small retained proof must confirm that:

1. entered-text Classify still works;
2. one explicitly selected small UTF-8 file populates the Classify textarea;
3. populated text can be edited before submission;
4. the existing JSON request completes with ordered labels;
5. node attribution is displayed;
6. selecting a second valid file replaces the textarea;
7. invalid UTF-8 does not replace existing textarea text and shows safe
   feedback;
8. reload clears page state; and
9. no multipart request, filename submission, persistence, background polling,
   new endpoint, or network-exposure change exists.

The retained proof must not contain real source text, labels, selected results,
filenames, paths, node identifiers, screenshots, or raw logs.

## Implementation sequence

If accepted:

1. make one small implementation PR for the HTML, JavaScript, focused tests,
   and current user documentation; and
2. perform a brief real-browser verification and update retained proof only if
   repository conventions require a separate proof PR.

The work need not be split unnecessarily when implementation and current
documentation remain one very small coherent change.

## Open questions

None. Implementation-level visual details remain ordinary implementation
decisions within this RFC's boundaries.

## Decision

Home AI Cluster accepts one explicit browser-local strict UTF-8 text-file
selection convenience for the Classify view. Decoded text populates the existing
Classify textarea, which remains the sole submitted source; `POST /v1/classify`
and its JSON contract remain unchanged. No multipart request, upload endpoint,
filename submission, persistence, dependency, or exposure change is introduced.

RFC-0063 supersedes only RFC-0062's Classify browser-input asymmetry, not
RFC-0062 as a whole.
