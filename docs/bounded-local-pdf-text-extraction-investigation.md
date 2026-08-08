# Bounded Local PDF Text Extraction Investigation

Status: Complete

## Question

> What is the smallest caller-local PDF-to-text boundary that could feed the
> existing text-only Home AI Cluster operations without making PDF a
> cluster-native document type?

This is an investigation only. It authorizes no implementation, PDF contract,
dependency, browser change, or RFC.

## Established repository facts

The existing text-only operations have deliberately different caller contracts:

| Operation | Established caller contract | PDF consequence |
| --- | --- | --- |
| `summarize` | One non-blank strict-UTF-8 source of at most 65,536 bytes from `--text`, one regular `--file`, or stdin; only `text` enters the native request and remote transport. | External text extraction can feed stdin unchanged. |
| `classify` | The same bounded text-source forms plus explicit ordered labels; only `text` and `labels` enter the native request and remote transport. | External text extraction can feed stdin unchanged when labels are supplied. |
| `chat` | One non-blank positional or `--message` value; it has no file or stdin source contract. | There is no existing PDF-to-stdin or bounded-text preprocessing path to reuse as an ordinary chat invocation. |

[RFC-0051](../RFC/RFC-0051-bounded-text-summarization.md),
[RFC-0056](../RFC/RFC-0056-bounded-summarize-standard-input.md),
[RFC-0057](../RFC/RFC-0057-bounded-summarize-regular-file-input.md), and
[RFC-0061](../RFC/RFC-0061-bounded-text-classification.md) make the 65,536-byte
text boundary authoritative before routing, adapter, or remote-transport work.
[RFC-0045](../RFC/RFC-0045-one-shot-ordinary-request-command.md) remains the
separate one-message chat-client boundary. The native clients retain no input
file, path, filename, or source metadata in their request bodies. The remote
transport carries normalized text, not source files, as preserved by
[RFC-0013](../RFC/RFC-0013-minimal-remote-transport-boundary.md) and
[RFC-0014](../RFC/RFC-0014-minimal-concrete-transport-protocol.md).

The loopback browser client already demonstrates one narrower pattern: an
explicitly selected local UTF-8 *text* file may populate an editable textarea,
and only its current text is submitted through the existing JSON request. It
does not support binary parsing, uploads, multipart data, server-side files, or
browser/server persistence. [RFC-0062](../RFC/RFC-0062-minimal-loopback-web-client.md)
and [RFC-0063](../RFC/RFC-0063-classify-local-text-file-input.md) deliberately
exclude PDF and other document parsing.

The rejected public-URL work confirms a related boundary: operator-owned source
preparation can feed existing bounded text input without granting Home AI
Cluster a new retrieval or ingestion authority. [RFC-0064](../RFC/RFC-0064-bounded-public-url-summarization.md)
authorizes no web retrieval.

## Candidate approaches

### A. Operator-owned external extraction

```text
operator-selected local PDF
  -> external local extractor
  -> stdout UTF-8 text
  -> existing bounded stdin input
  -> existing routing and execution
```

**Established repository facts.** The following forms use existing source
selection and request contracts; normal client validation rejects invalid,
blank, non-UTF-8, or over-65,536-byte extracted output before any cluster
request:

```sh
pdftotext document.pdf - | hac summarize
pdftotext document.pdf - | hac classify --label <label> --label <label>
```

The repository's current environment has `pdftotext` installed, but that is a
local operator observation, not a Home AI Cluster dependency, portability
guarantee, or supported PDF contract.

**External/tool facts requiring separate verification.** An operator must
select, install, update, and understand their extractor. Whether a tool can
read a particular PDF, how it represents layout and encoding, and its failure
and resource behavior are tool-owned. No project evidence establishes a
cross-platform extractor, a safe universal PDF-size or page-count limit, or a
text-quality guarantee.

**Project inference and trade-offs.** This is useful now for text-based PDFs
when the operator accepts the extractor's local behavior. Extraction failure,
encryption, malformed input, image-only input, or empty output fail outside
Home AI Cluster; if text reaches the existing client, its normal text validation
is authoritative. The approach preserves local-first and privacy-first
boundaries, adds no dependency or request field, and leaves no PDF binary,
filename, path, page information, document metadata, or PDF property in the
cluster. It is less portable and less convenient than a project-owned feature,
but does not create a document-ingestion contract.

### B. Native CLI-owned extraction

**Established repository facts.** A new `--pdf` path would change an accepted
native input surface. It would need an explicit decision about extractor
ownership, supported platforms, dependency or system-tool requirement, PDF
byte bound, extraction error vocabulary, and whether output is editable before
submission. The existing 65,536-byte text limit is necessary after extraction,
but it does not bound the PDF bytes or extraction work performed beforehand.

**External/library facts requiring separate verification.** No repository
evidence establishes that an existing Python dependency can extract PDF text,
or that an external binary is present across supported operator systems. A new
library or mandatory tool would need primary-source and focused resource-bound
evidence before an RFC could choose it.

**Project inference and trade-offs.** This could preserve text-only requests
only by keeping the PDF entirely at the caller edge and sending extracted text
through the existing source model. It would nevertheless create a durable
user-facing file-type and failure contract. A PDF-byte limit is needed before
loading or delegating extraction; the existing text bound remains needed after
extraction. Page count is not justified as a first independent contract without
evidence that it improves resource control. Text-based PDFs only and no OCR are
the smallest credible scope. Encrypted, malformed, image-only, or empty-text
inputs should fail locally without a request, but defining stable project error
semantics requires an RFC.

### C. Browser-local extraction

**Established repository facts.** The browser client can locally read one
selected UTF-8 text file and submit only editable textarea text, but accepted
scope expressly excludes PDF parsing. It has no upload route, server file
state, persistent browser state, or document view.

**External/library facts requiring separate verification.** Browser file APIs
provide selected-file bytes, not a repository-proven PDF text-extraction
facility. A browser extractor would require an evaluated library or other
supported local mechanism, including its bundle size, text-PDF behavior,
resource limits, and failure cases. The investigation found no accepted project
dependency or evidence that makes such a browser addition smaller than
operator-owned extraction.

**Project inference and trade-offs.** If a future RFC justified it, the only
bounded shape would read one explicitly selected text-based PDF in the browser,
place extracted text into an existing editable Summarize or Classify textarea,
and submit only the edited text. It must not retain or submit the file,
filename, path, metadata, page data, or extraction provenance. OCR, previews,
multi-file selection, drag-and-drop, background processing, and reusable
document context remain out of scope. Even this narrow surface expands the
accepted browser contract and cannot be implemented as an unnoticed extension.

### D. Server-side PDF ingestion

**Established repository facts.** Existing native and remote contracts are
text-only; the browser client and file-input RFCs expressly exclude uploads,
multipart data, binary input, server-side file objects, and persistence.

**External/library facts requiring separate verification.** None are needed to
reject this candidate for the first increment: the existing accepted contracts
already exclude the binary-ingestion behavior it would require.

**Project inference and trade-offs.** Server ingestion would introduce a binary
endpoint or multipart contract, file lifetime and bounds, MIME and parser
ownership, privacy/error handling, and potentially remote PDF movement. It is
not a smaller route to the requested convenience. It is rejected for a first
increment; no evidence establishes a need to reopen those document-ingestion
boundaries.

## Chat is not a document-context exception

One-shot caller-local extraction whose resulting text becomes one explicit chat
message is conceptually possible only after a separately accepted chat input
boundary. The current `hac chat` contract intentionally has neither stdin nor
file input, and its message is not the bounded summarize/classify text source.

Persistent or reusable PDF context across turns is a different design. It would
need document identity, retention, attachment/context ownership, retrieval or
indexing semantics, and conversation-state decisions. This investigation finds
no evidence for that need and does not recommend it.

## Bounds, failures, and data handling

For current operator-owned extraction, Home AI Cluster owns only its existing
65,536-byte strict-UTF-8 result boundary. PDF size, page count, encryption,
malformation, image-only content, and extraction behavior remain outside the
project. OCR is not part of the current workflow.

For any future project-owned extraction, both a pre-extraction PDF byte bound
and the existing post-extraction text bound would be required. No evidence here
selects their values or justifies page count as another first boundary. All
non-text-based, encrypted, malformed, and empty-extraction cases should stop
locally before an existing text request is constructed; no PDF bytes or PDF
metadata should be retained or transported.

## Outcome

**Outcome A — current operator-owned external extraction is sufficient for now;
no Home AI Cluster PDF feature is justified yet.**

The smallest useful sequence is no project change: operators who have a local
text extractor can use its stdout with the existing bounded `summarize` and
`classify` stdin paths. There is no corresponding supported `chat` pipeline,
and no justification to create one incidentally through PDF work.

No RFC, implementation, dependency, browser change, or proof PR is
recommended. A future concrete operator need may justify a narrow RFC for one
caller-local surface only, beginning with text-based PDFs and no OCR; it must
preserve the text-only request and transport contracts.
