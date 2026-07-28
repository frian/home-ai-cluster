# Documentation Index

Status: Current

This index provides a human-readable path through Home AI Cluster documentation.
It separates current operator guidance from chronological project records without
renaming or moving existing files.

Architectural decisions remain indexed separately in
[the RFC index](../RFC/README.md). Accepted RFCs, not this index, define the
architecture.

## Start here

- [Project README](../README.md) — current project shape and basic commands.
- [Command reference](command-reference.md) — current lookup reference for
  ordinary installed commands, common forms, options, and boundaries.
- [Roadmap](../ROADMAP.md) — completed phases and future direction.
- [Canonical operator workflow](operator-workflow.md) — shortest supported
  operator path.
- [RFC index](../RFC/README.md) — proposed and accepted architectural decisions.

## Operator entry points

- [Command reference](command-reference.md) — current lookup reference for
  ordinary installed commands, common forms, options, and boundaries.
- [Canonical operator workflow](operator-workflow.md) — current ordinary
  local-only and explicit static-cluster operation, including human-readable
  inspection defaults and explicit structured `--json` forms.
- [Daily operator workflow investigation](daily-operator-workflow-investigation.md)
  — bounded investigation of repeatable local role operation; not a proposal or
  accepted workflow change.
- [Ordinary daily-use friction investigation](ordinary-daily-use-friction-investigation.md)
  — documentation-only evaluation of ordinary local and one-receiver static
  operation after the retained remote summarize-file proof.
- [Daily operator workflow evidence protocol](daily-operator-workflow-evidence-protocol.md)
  — privacy-safe protocol for gathering operator workflow evidence; not a
  proof, accepted workflow, or Phase 17 plan.
- [Daily operator workflow evidence result](daily-operator-workflow-evidence-result.md)
  — retained privacy-safe evidence from one native two-machine daily workflow
  exercise; not an accepted workflow change or Phase 17 plan.
- [Human-readable operator output investigation](human-readable-operator-output-investigation.md)
  — investigated the bounded presentation need for existing finite operator
  commands that led to RFC-0048; it is not itself the architectural decision.
- [Static two-machine proof runbook](static-two-machine-proof.md) — explicit
  historical LAN proof procedure.
- [First two-machine proof result](first-two-machine-proof-result.md) — retained
  result of the founding real two-machine proof.

The canonical operator workflow is the current supported path. The other entries
in this section are historical proof references. They describe what was
established at a specific stage and do not replace the current workflow.

## Project history

### Phase 1 — Single-machine orchestrator

- [Phase 1 current state](phase-1-current-state.md) — descriptive snapshot of the
  first ordinary single-machine shape.

### Phase 2 — Agent and node model

- [Phase 2 starting state](phase-2-starting-state.md) — historical starting
  snapshot.
- [Phase 2 current state](phase-2-current-state.md) — later descriptive snapshot
  of the accepted static node and agent boundaries.

### Founding multi-machine proof

- [Static two-machine proof runbook](static-two-machine-proof.md) — repeatable
  proof procedure.
- [First two-machine proof result](first-two-machine-proof-result.md) — retained
  successful real execution.

### Phase 6 — OpenAI-compatible access

- [OpenAI compatibility proof](phase-6-openai-compatibility-proof.md) — retained
  proof of the deliberately narrow compatibility endpoint.
- [Developer tool access investigation](phase-6-developer-tool-access-investigation.md)
  — investigation of ordinary tool access.
- [Aider access proof](phase-6-aider-access-proof.md) — retained real Aider
  integration evidence.
- [Aider static-cluster compatibility proof](aider-static-cluster-proof.md) —
  retained privacy-safe evidence of one bounded two-machine Aider execution.

### Phase 8 — Operable local cluster

- [Phase 8 current state](phase-8-current-state.md) — descriptive state after the
  operability work.
- [Canonical operator workflow proof](phase-8-canonical-operator-workflow-proof.md)
  — retained workflow evidence.
- [Ordinary static multi-node proof](phase-8-ordinary-static-multi-node-proof.md)
  — retained ordinary-mode proof record.

### Phase 10 — Multiple explicit static remote nodes

- [Multiple static remote nodes proof](phase-10-multiple-static-remote-nodes-proof.md)
  — retained real multi-node evidence.
- [Phase 10 closeout](phase-10-closeout.md) — completion summary.

### Phase 11 — Explicit static cluster status

- [Explicit static cluster status proof](phase-11-explicit-static-cluster-status-proof.md)
  — retained normalized status evidence.
- [Phase 11 closeout](phase-11-closeout.md) — completion summary.

### Phase 12 — Heterogeneous runtime cluster proof

- [Heterogeneous runtime cluster proof](phase-12-heterogeneous-runtime-cluster-proof.md)
  — retained engine-independent cluster evidence.
- [Phase 12 closeout](phase-12-closeout.md) — completion summary.

### Phase 13 — Explicit local runtime composition

- [Explicit local runtime composition proof](phase-13-explicit-local-runtime-composition-proof.md)
  — retained ordinary-node composition evidence.
- [Phase 13 closeout](phase-13-closeout.md) — completion summary.

### Phase 14 — Explicit static-cluster local composition

- [Static-cluster local composition proof](phase-14-static-cluster-local-composition-proof.md)
  — retained ordinary static-cluster evidence.
- [Phase 14 closeout](phase-14-closeout.md) — completion summary.

### Phase 15 — Explicit static-cluster status composition

- [Static-cluster status composition investigation](phase-15-static-cluster-status-composition-investigation.md)
  — evidence and recommendation before RFC-0044.
- [Static-cluster status composition proof](phase-15-static-cluster-status-composition-proof.md)
  — retained real status evidence.
- [Phase 15 closeout](phase-15-closeout.md) — completion summary.

### Phase 16 — Ordinary operator request access

- [Ordinary operator request access investigation](phase-16-ordinary-operator-request-access-investigation.md)
  — identified the smallest ordinary operator access path and established the
  need for RFC-0045.
- [Ordinary request access proof runbook](phase-16-ordinary-request-access-proof-runbook.md)
  — planned the real operator procedure and does not itself claim proof
  execution.
- [Ordinary request access retained proof](phase-16-ordinary-request-access-proof.md)
  — retains privacy-safe real observations of unavailable ordinary process,
  local-only success, runtime-unavailable failure, and explicit static-cluster
  success; the static-cluster observation selected `local`.
- [Phase 16 closeout](phase-16-closeout.md) — completion record for the bounded
  one-shot ordinary request access phase.

### Phase 17 — Human-readable operator inspection output

- [Human-readable operator output investigation](human-readable-operator-output-investigation.md)
  — investigation of the bounded presentation need that preceded the accepted
  decision.
- [Human-readable inspection output proof runbook](phase-17-human-readable-inspection-output-proof.md)
  — reusable procedure for collecting bounded presentation evidence.
- [Human-readable inspection output retained proof result](phase-17-human-readable-inspection-output-proof-result.md)
  — privacy-safe record of the completed live and automated proof evidence.
- [Phase 17 closeout](phase-17-closeout.md) — completion record for the bounded
  human-readable inspection output phase.

### Phase 18 — Bounded text summarization

- [Second capability investigation](second-capability-investigation.md) —
  investigated the smallest credible second executable capability before
  RFC-0051.
- [Remote summarize file proof investigation](remote-summarize-file-proof-investigation.md)
  — investigation of one standalone post-roadmap composition of regular-file
  input, ordinary static fallback, remote summarize execution, and
  caller-owned attribution; it does not run or retain that proof.
- [Remote summarize file proof runbook](remote-summarize-file-proof-runbook.md)
  — privacy-safe procedure for the standalone remote summarize-file integration
  proof.
- [Remote summarize file proof](remote-summarize-file-proof.md) — retained
  privacy-safe result of one real two-machine `hac summarize --file` execution
  through accepted local-first remote fallback.
- [Phase 18 two-machine summarize proof runbook](phase-18-two-machine-summarize-proof.md)
  — repeatable privacy-safe procedure for the bounded real two-machine
  summarize proof.
- [Phase 18 two-machine summarize retained proof result](phase-18-two-machine-summarize-proof-result.md)
  — retained privacy-safe evidence from the completed real two-machine remote
  and local-first summarize observations.
- [Phase 18 closeout](phase-18-closeout.md) — completion record for the bounded
  second executable capability phase.

## Document roles

- **Current operator guidance** describes the supported way to use the repository
  now.
- **Investigation** records evidence and a recommendation. It does not authorize an
  architectural change.
- **Runbook** records a repeatable procedure.
- **Proof** retains privacy-safe evidence of an observed behavior.
- **Closeout** summarizes completion of one roadmap phase.
- **RFC** proposes or records an architectural decision and remains indexed under
  [`RFC/`](../RFC/README.md).

## Maintenance

When adding a documentation file:

1. link it from the relevant phase or operator section in this index;
2. identify its role clearly in the file and link description;
3. keep current operator guidance separate from historical proof records;
4. do not rename older files merely to impose chronology; and
5. keep architectural decisions in RFCs rather than in this index.

The index may be expanded when older historical records become useful to navigate.
It should remain concise enough to answer two questions quickly:

> What should an operator read now?

and:

> In what order did the project establish its current shape?
