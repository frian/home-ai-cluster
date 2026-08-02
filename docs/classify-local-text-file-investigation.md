# Classify local text-file input investigation

## Status

Investigation only. This document authorizes no implementation, test, API, or
RFC change.

## Context

The accepted loopback browser page provides three fixed user request views over
existing native JSON endpoints. Summarize can populate its text area from one
explicitly selected local UTF-8 text file. Classify currently accepts directly
entered source text and ordered labels, and has no file selector.

The narrow question is whether Classify should receive the same browser-local
text convenience. This is not an investigation of file ingestion, documents,
or uploads.

## Current accepted boundary

RFC-0062 permits Summarize to select one local UTF-8 text file, decode it in
the browser, and send only the decoded text through the existing summarize JSON
body. It expressly excludes file-upload endpoints, multipart data, arbitrary
binary input, multimodal behavior, persistence, and file retention.

For Classify, RFC-0062 instead specifies a directly entered bounded source and
an ordered label-entry control. The merged page and focused asset test reflect
that distinction: Classify has no file input. RFC-0061 owns the native
classification contract: one bounded non-blank text source and ordered labels.

The proposal would be browser-local file reading only. It would not be HTTP
file upload, multipart form submission, multimodal input, a server-side file
object, or a change from the existing JSON text submission.

## User need

A selector helps when the text to classify already exists as one small local
text file—for example, a note, exported plain-text message, or short document
that a user wants to categorize against an existing label set. It removes a
copy-and-paste step and aligns the source-selection experience with Summarize.

It does not unlock a different classification capability: users can already
copy the decoded text into the textarea. The value is therefore modest friction
reduction, not a new execution, routing, or document-processing workflow.
Keeping the selection explicit and limited to one UTF-8 text file avoids a
generic upload surface.

## Contract analysis

The smallest proposed behavior can preserve the exact existing request body:

```json
{
  "text": "<decoded text>",
  "labels": ["...", "..."]
}
```

It requires no change to `/v1/classify`, native validation, routing, adapters,
runtime contracts, internal transport, normalized results, safe failures, or
node attribution. The browser would set the existing textarea value before the
ordinary form submission; native validation would remain authoritative.

## Privacy and retention analysis

Under the proposed narrow behavior, the user explicitly chooses one file; the
browser strictly decodes it as UTF-8 and places the decoded value in the
existing textarea. Existing blank-text and 65,536-UTF-8-byte checks apply
before the existing JSON request. No multipart request, filename, file object,
file persistence, browser storage, history entry, logging, or retention change
is introduced.

For content transmission and server-side retention, this is materially the
same as pasting the same text: only text reaches the existing classification
path. The local browser briefly has access to the selected file and its
decoded text, which is the intentional user-selected convenience; the filename
must not be submitted or retained.

## UI consistency

The Classify selector could follow the existing Summarize pattern conceptually:
one ordinary file input, browser-local strict UTF-8 decoding, and assignment to
the text area. It should remain view-local unless later evidence shows a shared
abstraction is necessary.

It should not add drag-and-drop, multiple files, previews, filename display or
retention, binary formats, MIME sniffing, encoding choices, document parsing,
or background processing. The existing `accept` hint may guide a picker but is
not validation; strict decoding and native validation remain the boundary.

## Validation behavior

The expected later behavior is:

| Situation | Browser behavior | Authoritative boundary |
| --- | --- | --- |
| Invalid UTF-8 | Show the existing safe local invalid-text feedback; do not populate the textarea. | Browser decoding; no request is made. |
| Blank decoded text | Place it in the textarea if decoded; form submission gives existing local non-blank feedback. | Native validation remains authoritative. |
| Text over 65,536 UTF-8 bytes | Place it in the textarea if decoded; form submission gives existing local limit feedback. | Native validation remains authoritative. |
| Second selection | Replace the textarea with the newly decoded text. | No multi-file state exists. |
| Clear file input | Do not erase textarea text already populated from a prior selection. | Textarea remains the submitted source. |
| Edit populated textarea | Submit the edited textarea value. | Existing JSON text contract. |
| Classification failure | Retain ordinary page form state and show the existing safe failure presentation. | Existing native safe failure behavior. |

This deliberately does not require the browser to duplicate every native label
rule or to attach file provenance to submitted text.

## Architectural scope

This is a browser convenience over the existing text contract. It changes no
core, routing, adapter, transport, runtime, endpoint, or network-exposure
boundary. It nevertheless expands an accepted user-facing browser surface:
RFC-0062 deliberately grants this convenience to Summarize and deliberately
describes Classify differently. Treating that asymmetry as an implementation
detail would let code revise an accepted UI boundary without a recorded
decision.

The repository has successor RFC precedent for narrow changes to accepted RFC
clauses, while the RFC process describes accepted RFCs as architectural memory
and does not define in-place amendment mechanics. A new, narrowly scoped RFC
referencing RFC-0062 is therefore clearer than editing accepted RFC-0062. It
can supersede only the relevant Classify browser-input clause if accepted.

## Options considered

1. **No implementation and no RFC.** Keeps the current smallest surface and
   requires only copy and paste. This remains viable if observed friction is
   too small to justify another decision.
2. **Implement as an RFC-0062 detail.** Rejected. The RFC expressly gives the
   file path to Summarize and direct text to Classify; the current page, tests,
   proof, and operator documentation make the asymmetry observable.
3. **Amend accepted RFC-0062 in place.** Not recommended. Current repository
   conventions favor focused successor RFCs for accepted-decision adjustments;
   an in-place edit would weaken the historical boundary that was reviewed.
4. **New narrow RFC, then implement if accepted.** Recommended. It preserves
   the current architecture while making the user-surface decision explicit.

## Recommendation

Proceed only through a new narrow RFC that references RFC-0062; do not amend
RFC-0062 in place and do not implement before acceptance. The RFC should decide
whether the modest copy-and-paste friction justifies parity with Summarize and,
if so, authorize exactly one browser-local UTF-8 text-file selector for
Classify.

The likely later implementation is limited to the existing Classify markup and
plain JavaScript, focused browser-asset tests, and the smallest aligned current
documentation after implementation. It would use the existing JSON body,
strict browser-local UTF-8 decoding, the existing byte limit, and no
dependency, multipart upload, API change, persistence, or network-exposure
change.
