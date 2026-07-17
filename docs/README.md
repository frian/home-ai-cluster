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
- [Roadmap](../ROADMAP.md) — completed phases and future direction.
- [Canonical operator workflow](operator-workflow.md) — shortest supported
  operator path.
- [RFC index](../RFC/README.md) — proposed and accepted architectural decisions.

## Current operator documentation

- [Canonical operator workflow](operator-workflow.md) — ordinary local-only and
  explicit static-cluster operation.
- [Static two-machine proof runbook](static-two-machine-proof.md) — explicit
  historical LAN proof procedure.
- [First two-machine proof result](first-two-machine-proof-result.md) — retained
  result of the founding real two-machine proof.

Current operator guidance should be read before historical investigations and
proof records. Historical documents describe what was demonstrated at a specific
stage; they do not automatically replace the current workflow.

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
