# RFCs

RFC stands for Request for Comments.

In Home AI Cluster, RFCs are used to document important decisions before they become architecture, protocol, or long-term project rules.

An RFC is not a blog post.

An RFC is not a TODO list.

An RFC is not documentation for users.

An RFC explains a problem, proposes a decision, records the reasoning, and makes trade-offs visible.

---

## When to write an RFC

Write an RFC when a decision may affect the long-term direction of the project.

Examples:

* core architecture;
* agent/orchestrator responsibilities;
* node discovery;
* capability model;
* runtime adapter design;
* privacy boundaries;
* security model;
* configuration format;
* protocol design;
* breaking changes;
* project governance.

Do not write an RFC for small implementation details, typos, trivial refactors, or temporary experiments.

---

## RFC status

Each RFC must have one status:

* `Draft`
* `Accepted`
* `Rejected`
* `Superseded`

A draft RFC is a proposal.

An accepted RFC becomes part of the project’s architectural memory.

A rejected RFC remains useful because it explains what was considered and why it was not chosen.

A superseded RFC has been replaced by a newer RFC.

## Rejected RFCs

- [RFC-0064: Bounded Public URL Summarization](RFC-0064-bounded-public-url-summarization.md)
  — considered caller-local bounded URL summarization; hostname safety could
  not be guaranteed with the existing high-level stack, and the literal-IP-only
  narrowing was not useful enough. No implementation was authorized.

## Accepted RFCs

- [RFC-0068: One-Shot Aider Code Caller Edge](RFC-0068-one-shot-aider-code-caller-edge.md)
  — accepts one optional Aider-specific one-shot caller edge that coordinates
  external Aider with a private loopback translation to explicit native `code`,
  while keeping target edits caller-owned and RFC-0031 Chat-only.
- [RFC-0067: Bounded Textual Code Assistance](RFC-0067-bounded-textual-code-assistance.md)
  — accepts one explicit bounded textual `code` capability using the shared
  ordered-message representation and existing Chat-like execution mechanics,
  without tools or execution authority.
- [RFC-0066: Capability Admission Semantics](RFC-0066-capability-admission-semantics.md)
  — accepts a closed, explicit, model-independent admission rule for future
  capability proposals without authorizing a new capability or implementation.
- [RFC-0065: Browser-Local PDF Text Input for Summarize](RFC-0065-browser-local-pdf-text-input-for-summarize.md)
  — accepts one 8 MiB-bounded browser-local PDF.js preprocessing path for the
  existing Summarize textarea and unchanged text-only request.
- [RFC-0063: Classify Local Text File Input](RFC-0063-classify-local-text-file-input.md)
  — accepts one browser-local UTF-8 text-file convenience for Classify while
  preserving the existing JSON contract and exposure boundaries.
- [RFC-0062: Minimal Loopback Web Client](RFC-0062-minimal-loopback-web-client.md)
  — accepts one fixed same-origin browser client over existing native
  capabilities, without changing network exposure.
- [RFC-0061: Bounded Text Classification](RFC-0061-bounded-text-classification.md)
  — accepts one bounded `classify` capability with an exact operator-supplied
  selected-label result and explicit static eligibility.
- [RFC-0060: Explicit Native Client Timeout](RFC-0060-explicit-native-client-timeout.md)
  — accepts one shared finite per-invocation timeout for ordinary native clients
  while preserving the 120.0-second default and existing timeout ownership
  boundaries.
- [RFC-0059: Caller-local static capabilities](RFC-0059-caller-local-static-capabilities.md)
  — accepts bounded caller-local routing capabilities for ordinary static
  clusters while preserving local-first routing and receiver behavior.
- [RFC-0058: Explicit static remote capabilities](RFC-0058-explicit-static-remote-capabilities.md)
  — accepts bounded operator-declared capabilities for ordinary static remote
  nodes while preserving existing routing and compatibility boundaries.

---

## File naming

RFC files should use this format:

```text
RFC-0001-title.md
RFC-0002-title.md
RFC-0003-title.md
```

Use lowercase words separated by hyphens.

The number never changes.

---

## RFC template

```md
# RFC-0000: Title

Status: Draft

Date: YYYY-MM-DD

Author: Name or GitHub handle

## Summary

A short explanation of the proposal.

The summary should be understandable without reading the whole RFC.

## Problem

What problem are we trying to solve?

Why does this problem matter?

What happens if we do nothing?

## Goals

What should this RFC achieve?

## Non-goals

What is deliberately outside the scope of this RFC?

## Proposal

What are we proposing?

Describe the decision clearly.

Avoid implementation details unless they are essential to the decision.

## Rationale

Why this proposal?

Why is it better than the alternatives?

What project principles does it support?

## Alternatives considered

What other options were considered?

Why were they not chosen?

## Trade-offs

What does this proposal make easier?

What does it make harder?

What complexity does it introduce?

Why is that complexity acceptable?

## Impact

What documents, architecture, or future implementation work does this affect?

Does it affect users?

Does it affect developers?

Does it affect future compatibility?

## Open questions

What is still undecided?

What needs more research or discussion?

## Decision

For accepted or rejected RFCs, summarize the final decision here.

For drafts, leave this section empty or write:

Pending.
```

---

## Rules

RFCs should be clear, boring, and explicit.

A good RFC makes disagreement easier.

A good RFC explains trade-offs.

A good RFC can be understood months later by someone who was not part of the original discussion.

If an architectural decision cannot be explained in an RFC, it is not ready.
