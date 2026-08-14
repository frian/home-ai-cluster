# Minimal Loopback Code View Proof

Status: Retained automated proof

Date: 2026-08-14

## Scope

This record retains focused evidence for accepted RFC-0070's fixed, text-only
loopback Code view. It does not claim a live runtime-model exercise, browser
filesystem behavior, file creation, execution, or compatibility expansion.

## Automated evidence

The focused browser test reads the packaged fixed page and script and verifies:

- exactly four fixed tabs and panels: Chat, Summarize, Classify, and Code;
- Code has one textarea, one ordinary submit button, one result output, and no
  file input;
- the Code handler submits the existing same-origin `/v1/chat` path with
  explicit `capability: "code"` and exactly one user message from the textarea;
- the handler does not append to or reuse Chat's multi-turn `messages` state;
- blank and over-limit UTF-8 input are rejected before submission;
- successful responses require textual `content` and `node_id` and reuse the
  existing text-safe `renderResult` path; and
- no `/v1/code`, persistence API, or HTML result rendering was added.

The focused native-path test sends one synthetic, non-sensitive request through
the existing in-process FastAPI `/v1/chat` route. Its deterministic existing
test seam observes the resulting `ClusterRequest` and returns a normalized
textual result. The test verifies explicit `code`, one user message, and the
textual-result plus `node_id` response contract without a public network
service or runtime model.

Existing loopback-browser tests continue to verify API-only application and
compatibility compositions are page-free, fixed same-origin assets are served,
and the existing Chat, Summarize, and Classify browser paths remain present.
Existing code-capability tests retain the RFC-0067 aggregate 65,536-byte
validation and static eligibility boundaries.

## Implementation inspection

The Code handler keeps only current textarea/result DOM state. It uses the
existing one-active-request, safe-failure, and text rendering mechanics. The
implementation adds no backend route, CORS, proxy, process, compatibility path,
storage, filesystem authority, file creation, Git, shell, tool, or execution
behavior. Reloading creates a fresh page and does not restore Code state because
no browser persistence is used.

## Evidence boundary

This record deliberately contains no real prompt, generated source, private
path, machine name, private address, model/runtime identity, credential, or raw
sensitive log. It distinguishes deterministic automated request-path evidence
from source-level browser behavior inspection.
