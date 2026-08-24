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

## Enduring boundaries

The completed progression preserves capability-centered routing and
engine-independent cluster-facing concepts. Topology remains explicit and
operator-owned; operation remains local-first and privacy-first; and routing,
status, and failures must remain understandable.

The project does not silently expand into discovery, scheduling, supervision,
lifecycle management, generic orchestration, Docker, Kubernetes, or dashboard
work. Architectural changes still require accepted RFCs.

## Later work and retained evidence

Formal phases are distinct from later standalone integration evidence. Work
after the completed roadmap is intentionally tracked through bounded
investigations, accepted RFCs, implementation pull requests, and retained
evidence—not by turning this file into a second index. See the
[RFC index](RFC/README.md), [documentation index](docs/README.md), and
[project README](README.md).

## Non-binding future possibilities

No item here is approved work, a priority, a schedule, or an implementation
authorization. If useful after separate investigation and accepted decisions,
possibilities may include a broader local web UI beyond the implemented bounded
loopback client, a generic plugin ecosystem beyond the implemented bounded
acquisition-plugin boundary, optional cloud nodes, or further distributed
inference experiments. This is not an exhaustive backlog.

## Enduring principle

> Many machines. One AI.
