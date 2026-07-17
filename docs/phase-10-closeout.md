# Phase 10 Closeout

Status: Complete

Date: 2026-07-17

## Purpose

Record completion of Phase 10 — Multiple explicit static remote nodes — against
the current roadmap outcomes and the accepted RFC-0040 decisions.

This closeout records three distinct kinds of evidence:

1. architectural acceptance in RFC-0040;
2. implementation and automated verification in the repository; and
3. retained real operator verification.

## Roadmap outcome review

Phase 10 required a small explicit static cluster to extend beyond one remote
node while preserving operator control, capability-centered routing, static
validation, understandable attribution, and the accepted narrow fallback.

The following roadmap outcomes are complete:

- More than one remote node can be represented in one explicit static cluster
  declaration.
- All declared nodes are statically validated before startup.
- Routing remains capability-centered; requests do not directly target a
  machine.
- Successful results retain cluster-owned node attribution.
- Ordered fallback advances only after the accepted
  connection-unavailable-before-request failure.
- Duplicate normalized remote node identifiers and base URLs are rejected.
- Declaration order is the only remote priority.
- The prior flat one-remote declaration remains supported.
- Inline CLI topology remains limited to one remote.
- The real three-machine operator proof is retained in
  `docs/phase-10-multiple-static-remote-nodes-proof.md`.

## Accepted architectural boundaries

RFC-0040 is accepted and defines one fixed local node plus one or more explicit,
process-local remote declarations. It retains local-first capability eligibility
and makes declaration order the sole remote priority rule.

The accepted traversal is finite and sequential. An eligible local candidate is
attempted first. Eligible remotes are then attempted in declaration order only
after the accepted pre-request connection-unavailable condition. Each candidate
is attempted at most once; the first success returns immediately; and any other
failure stops traversal.

The phase did not introduce:

- discovery, dynamic membership, or automatic topology mutation;
- supervision, remote process control, or automatic runtime lifecycle actions;
- load balancing, scoring, scheduling, parallel execution, fan-out, or quorum
  behavior;
- a general retry policy or a retry of the same candidate;
- live reload, file watching, configuration merging, precedence, or a generic
  configuration system; or
- secret handling in the declaration.

Remote runtimes, remote applications, declarations, and process lifecycle
remain operator-owned.

## Implementation and verification summary

The repository implements both accepted declaration shapes: the RFC-0039 flat
single-remote form and the RFC-0040 ordered `remote_nodes` form. Multi-remote
declarations require at least one entry, validate node identity and normalized
endpoint uniqueness, and reject unsupported or mixed shapes before startup.

The ordinary static cluster entry point preserves the existing inline mode for
exactly one remote. Multiple remotes are available through the explicit
declaration-file mode only. Declaration mode and inline topology arguments
remain mutually exclusive.

The ordinary `/v1/chat` application path retains its existing precedence and
uses the ordered static remote fallback only when collection wiring is present.
It constructs the collection request with remote execution permitted while
preserving the local-only path when no explicit remote wiring is active.

Focused automated tests cover ordered declaration retention, static preflight,
duplicate rejection, inline compatibility, collection wiring, route behavior,
the accepted connection-unavailable transport mapping, bounded ordered fallback,
and the composition from declaration loading through the ordinary application
route. Those tests also preserve the stop-on-other-failure boundary.

## Operator proof

The retained proof in `docs/phase-10-multiple-static-remote-nodes-proof.md`
records successful real operator verification on three machines on one trusted
LAN.

It verifies an explicit declaration ordered as `remote-a`, then `remote-b`; a
separate real `remote-a` machine unavailable before request transmission; and a
separate real `remote-b` machine receiving exactly one successful internal
request after fallback. The final result retained cluster-owned attribution to
`remote-b`, and no retry loop or repeated successful remote request was
observed.

The proof also distinguishes static declaration preflight from later runtime and
network behavior: preflight validated static coherence without network probing;
the later trusted-LAN request demonstrated the accepted runtime fallback path.

## Deferred work

The following remain outside Phase 10 and unchanged by this closeout:

- automatic discovery or dynamic membership;
- health polling or health-aware routing;
- runtime, model, capacity, or latency-based selection;
- scheduling, load balancing, and parallel request behavior;
- broad retry or recovery policy;
- remote process supervision, control, or repair;
- topology reload, mutation, or configuration precedence; and
- credentials, secret management, or a generic configuration system.

Any future change in these areas requires its own architectural review and, when
applicable, an RFC.

## Conclusion

Phase 10 is complete.

The project now supports a small, explicit, ordered static remote collection
while preserving the accepted local-first, privacy-first, capability-centered,
operator-owned architecture. The implementation, automated verification, and
retained three-machine operator proof together demonstrate the Phase 10 roadmap
outcomes without expanding into dynamic topology, scheduling, supervision, or
general retries.
