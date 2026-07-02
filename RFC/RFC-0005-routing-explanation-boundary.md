# RFC-0005: Routing Explanation Boundary

Status: Accepted

Date: 2026-07-02

Author: frian

## Summary

Home AI Cluster routing decisions must be explainable internally without changing normal user-facing responses.

For Phase 1, routing explanations remain internal. The public `/v1/chat` response must not include routing metadata by default.

Any future public explanation surface requires a separate RFC.

## Problem

Home AI Cluster is built around routing requests by capability rather than by a specific machine, model, or runtime.

As soon as routing exists, users and developers need to understand why a route was selected. This supports transparency and keeps routing from becoming magic.

At the same time, exposing routing metadata directly in normal responses would create a public API contract too early. It could also leak internal topology, adapter names, or future implementation details before the project has decided how explanation should work.

If we do nothing, routing explanations may drift into public responses, logs, debug output, or ad hoc formats without an explicit architectural decision.

## Goals

* Keep routing decisions explainable internally.
* Prevent accidental public API drift.
* Keep normal `/v1/chat` responses stable.
* Preserve privacy-first behavior by avoiding prompt, response, or routing history logs by default.
* Leave room for a future explicit explanation surface.

## Non-goals

This RFC does not define:

* a public routing explanation API;
* a debug endpoint;
* a dashboard;
* telemetry;
* persistent routing logs;
* request or response logging;
* routing history;
* scoring;
* fallback policy;
* health-based routing;
* model-based routing;
* multi-node discovery;
* an agent protocol.

## Proposal

Routing decisions may include internal explanation data.

For Phase 1, the internal routing decision may record a short factual reason describing why the selected node and adapter were chosen.

Normal user-facing responses must not expose this routing explanation by default.

The public `/v1/chat` response shape remains focused on the normalized result. It must not gain fields such as:

* `routing`;
* `reason`;
* `node`;
* `selected_node`;
* `selected_adapter`.

A future public explanation surface may be added only after a separate RFC defines its boundary, privacy behavior, and compatibility impact.

## Rationale

This supports transparency over magic without turning internal routing state into a premature public contract.

It keeps the current Phase 1 implementation boring and local-first:

* one public chat endpoint;
* one static local node;
* one runtime adapter;
* one internal routing decision;
* no public routing metadata by default.

It also protects privacy. Routing explanations should not become a hidden logging or telemetry mechanism.

## Alternatives considered

### Expose routing metadata in `/v1/chat`

This would make routing visible immediately, but it would also change the public response shape too early.

It would create compatibility pressure before the project has decided how user-visible explanations should work.

### Add a debug endpoint now

A debug endpoint may be useful later, but it is not needed for the current Phase 1 proof.

Adding it now would introduce new API surface area before the explanation boundary is settled.

### Log routing decisions

Logging could help debugging, but it risks becoming telemetry or persistent request history.

This conflicts with privacy-first defaults unless a future RFC defines the exact boundary.

### Do not record explanations at all

This would avoid API drift, but it would weaken internal transparency and make routing behavior harder to inspect during development.

## Trade-offs

This RFC makes the normal API safer and more stable.

It makes immediate user-visible debugging less convenient because routing explanations stay internal.

That trade-off is acceptable for Phase 1 because the project is still proving the minimal local architecture, not designing observability or public explanation APIs.

## Impact

This RFC affects routing architecture and public API boundaries.

It does not require a public API change.

It confirms that internal routing explanation is allowed, while public exposure of routing metadata is deferred.

Future work that exposes routing decisions to users, tools, logs, dashboards, or APIs must reference this RFC and propose an explicit boundary.

## Open questions

* Should future routing explanations be exposed through an explicit debug request option, a separate endpoint, or a local developer tool?
* What routing metadata is safe to expose without leaking private topology or runtime details?
* Should public explanations use stable identifiers, human-readable labels, or both?
* Should explanation behavior differ between local developer mode and normal user mode?

## Decision

Accepted.

For Phase 1, routing explanations remain internal.

The public `/v1/chat` response does not expose routing metadata by default.

Any future public explanation surface requires a separate RFC.
