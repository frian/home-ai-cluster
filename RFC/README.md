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

## Accepted RFCs

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
