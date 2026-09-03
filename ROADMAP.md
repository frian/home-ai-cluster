# Roadmap

Status: Complete

This is the completed historical record of Home AI Cluster's formal roadmap.
It was never a release plan or promise. It records the progression used to
prove the original architecture; it is not an exhaustive ledger of later RFCs
or completed work.

For current product and operator state, see [README.md](README.md). For
architectural decisions, see [the RFC index](RFC/README.md). For retained
investigations, proofs, and operational documentation, see [the documentation
index](docs/README.md).

## Achieved founding milestone

> One endpoint. Two machines. One routed request.

This milestone was achieved. It established that multiple personal machines can
participate in one capability-centered local system without making the project
an infrastructure platform.

## Completed formal phases

| Phase | Purpose | Completion evidence |
| --- | --- | --- |
| Phase 0 — Foundations | Establish the project’s vocabulary, principles, and decision process before implementation. | [Vision](VISION.md) and [Foundations](FOUNDATIONS.md) |
| Phase 1 — Single-machine orchestrator | Establish one local endpoint, runtime adapter, request, and response. | [Phase 1 current state](docs/phase-1-current-state.md) |
| Phase 2 — Agent and node model | Define static node, availability, health, capability, and registry boundaries. | [RFC-0019 closeout](RFC/RFC-0019-phase-2-closeout-and-phase-3-entry.md) |
| Phase 3 — Two machines | Prove one endpoint can route one request across two explicit machines. | [RFC-0024 closeout](RFC/RFC-0024-phase-3-closeout-and-phase-4-entry.md) |
| Phase 4 — Capability-based routing | Route by capabilities with bounded fallback and explainable selection. | [RFC-0029 closeout](RFC/RFC-0029-phase-4-closeout-and-phase-5-entry.md) |
| Phase 5 — Runtime adapters | Keep cluster-facing concepts independent of concrete runtimes. | [Phase 5 current state](docs/phase-5-current-state.md) |
| Phase 6 — OpenAI-compatible access | Provide a narrow, separate compatibility edge for existing tools. | [Compatibility proof](docs/phase-6-openai-compatibility-proof.md) |
| Phase 7 — Observability and trust | Make routing, status, failures, and prompt-free history understandable. | [Phase 7 completion investigation](docs/phase-7-completion-and-next-phase-investigation.md) |
| Phase 8 — Operable local cluster | Establish the documented, repeatable static-cluster operator workflow. | [Phase 8 current state](docs/phase-8-current-state.md) |
| Phase 9 — Repeatable static cluster declaration | Add one explicit, operator-owned static declaration path. | [Phase 9 closeout](docs/phase-9-closeout.md) |
| Phase 10 — Multiple explicit static remote nodes | Extend explicit static topology to ordered multiple remotes. | [Phase 10 closeout](docs/phase-10-closeout.md) |
| Phase 11 — Explicit static cluster status | Add finite, read-only inspection of declared static-cluster status. | [Phase 11 closeout](docs/phase-11-closeout.md) |
| Phase 12 — Heterogeneous runtime cluster proof | Prove ordinary capability-centered operation across distinct runtimes. | [Phase 12 closeout](docs/phase-12-closeout.md) |
| Phase 13 — Explicit local runtime composition | Make one supported local runtime composition explicit at startup. | [Phase 13 closeout](docs/phase-13-closeout.md) |
| Phase 14 — Explicit static-cluster local composition | Apply the closed local-composition choice to static-cluster startup. | [Phase 14 closeout](docs/phase-14-closeout.md) |
| Phase 15 — Explicit static-cluster status composition | Apply the same closed local-composition choice to status inspection. | [Phase 15 closeout](docs/phase-15-closeout.md) |
| Phase 16 — Ordinary operator request access | Provide one installed, one-shot native request command. | [Phase 16 closeout](docs/phase-16-closeout.md) |
| Phase 17 — Human-readable operator inspection output | Make bounded inspection readable by default while preserving explicit JSON. | [Phase 17 closeout](docs/phase-17-closeout.md) |
| Phase 18 — Bounded text summarization | Prove a second executable capability through local and declared-remote paths. | [Phase 18 closeout](docs/phase-18-closeout.md) |

## Released 1.0 baseline

The completed historical phases culminated in Home AI Cluster 1.0.0. The
released baseline includes explicit static multi-node operation,
capability-centered routing with deterministic candidate order and bounded safe
fallback, retained operator configuration, finite operator inspection surfaces,
Ollama and llama-server adapter proof, bounded external-information and Chat
assistance, a fixed loopback browser interface, ephemeral interactive Chat and
Code, and supported Linux and Windows use.

This summary is not an exhaustive release ledger. Current product and operator
behavior remain documented in [README.md](README.md), the
[documentation index](docs/README.md), and accepted RFCs.

## Enduring boundaries

The completed progression preserves capability-centered routing and
engine-independent cluster-facing concepts. Topology remains explicit and
operator-owned; operation remains local-first and privacy-first; and routing,
status, and failures must remain understandable.

The project does not silently expand into discovery, scheduling, supervision,
lifecycle management, generic orchestration, Docker, Kubernetes, or dashboard
work. Architectural changes still require accepted RFCs.

## Post-1.0 direction

The next major problem area to investigate is execution availability and, only
if justified by later RFCs, bounded capacity-aware routing. Future work may
need to distinguish retained/configured state, capability eligibility,
reachability, HAC application availability, runtime availability, and whether a
candidate can accept additional work. Exact vocabulary, authority, freshness,
observation, concurrency, and routing behavior remain open RFC questions.

The product motivation is straightforward: equivalent capable machines should
eventually be able to share useful work, rather than merely exist as ordered
static candidates. This does not imply a general scheduler, GPU scoring,
predictive completion-time model, distributed orchestration platform, premature
queue, or speculative retry beyond the accepted request-engagement safety
boundary.

Future execution-state work should preserve understandable distinctions among
retained configuration, static coherence, local runtime health, and bounded
cluster status. It does not imply consolidation of those existing surfaces.

Additional runtimes may be investigated when they provide a concrete
architectural or concurrency proof; runtime-counting is not a milestone. Broader
capability composition likewise requires demonstrated additional use cases.
The existing bounded external-information, Chat assistance, browser, and
ephemeral interactive surfaces do not imply a generic orchestration framework,
dashboard, or persistent conversation storage.

## Possible 2.0 direction

Home AI Cluster 2.0 may represent a mature explicit local cluster that can
share work across equivalent capable nodes while remaining bounded,
deterministic, explainable, operator-controlled, local-first, privacy-first,
and engine-independent. This is direction, not a product contract: exact
execution availability, capacity, concurrency, fairness, and routing semantics
require accepted RFCs before implementation.

## Post-2.0 possibilities

Automatic discovery and dynamic membership are unpromised post-2.0
possibilities, not a 2.0 milestone. If ever investigated, they introduce
separate questions of identity, trust, authorization, membership, freshness,
announcements, network scope, and authority:

    discovered != trusted != authorized

Other later possibilities may be considered only through the same bounded,
evidence-led process. This is not an exhaustive backlog.

## Roadmap rule

Roadmap direction is not architectural authorization. Formal phases are
distinct from later investigations, accepted RFCs, implementation pull requests,
and retained evidence; this file must not become a second index.

Future changes involving execution-availability authority, concurrency or
capacity contracts, capacity-aware routing or load sharing, candidate ordering
or fairness, fallback/retry safety, status/health/preflight observation,
generalized capability composition, persistent conversations, dashboard or
operator-control browser behavior, discovery, identity, trust, authorization,
or dynamic membership require RFC consideration before implementation.

## Enduring principle

> Many machines. One AI.
