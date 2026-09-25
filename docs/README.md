# Documentation Index

Status: Current

This page is the navigation entry point for Home AI Cluster documentation.
Current user and operator documentation explains how HAC works now. RFCs record
architectural decisions. Retained investigations, proofs, runbooks, validations,
and closeouts preserve the evidence and history behind the project.

Accepted RFCs, not this index, define the architecture.

## Use Home AI Cluster

- [Getting Started](getting-started.md) — installation, runtime prerequisites,
  first local use, and browser use.
- [Command Reference](command-reference.md) — exact ordinary command syntax,
  options, behavior, and boundaries.
- [Configuration Examples](configuration-examples.md) — concrete retained,
  local, and static configuration examples.
- [Canonical Operator Workflow](operator-workflow.md) — the supported
  local-only and explicit static-cluster operating sequence.

## Understand the project

- [Project README](../README.md) — a concise overview of HAC and its ordinary
  capabilities.
- [Vision](../VISION.md) — the project purpose and long-term user-centered
  direction.
- [Foundations](../FOUNDATIONS.md) — the stable ideas that guide the project.
- [Principles](../PRINCIPLES.md) — rules for decisions, reviews, and
  trade-offs.
- [Non-goals](../NON_GOALS.md) — deliberate scope boundaries and refusals.
- [RFC index](../RFC/README.md) — the architectural decision record and
  canonical RFC archive.
- [Roadmap](../ROADMAP.md) — project direction and history, not user
  documentation or architectural authorization.
- [Contributing](../CONTRIBUTING.md) — contribution workflow and review
  expectations.

## Selected deeper references

These are useful examples, not a complete historical index.

- [Explicit receiver authority proof](explicit-receiver-authority-proof.md) —
  real bounded receiver and network-authority evidence.
- [Loopback browser workspace Code](loopback-browser-workspace-code.md) — the
  current concise boundary for workspace-enabled browser Code.
- [stable-diffusion.cpp Image Generation proof](stable-diffusion-cpp-image-generation-proof.md)
  — real local Image Generation execution evidence.
- [Real vLLM validation](vllm-real-validation.md) — alternate-runtime and
  engine-independence validation.
- [Home AI Cluster 1.0 five-node validation](v1.0-five-node-cluster-validation.md)
  — validation of a larger explicit static cluster.
- [Workspace Code model compatibility investigation](workspace-code-model-compatibility-investigation.md)
  — bounded Workspace Code model interoperability observations.
- [Source-grounded Chat proof](source-grounded-chat-proof.md) — bounded
  evidence use and supplied-source provenance observations.

## Historical evidence

The `docs/` directory intentionally retains a much larger body of project
evidence. Browse that directory directly or search by topic when deeper context
is needed. Common document roles include:

- **Investigation** — evidence and analysis before a possible decision; it does
  not itself authorize architecture.
- **Runbook** — a repeatable procedure.
- **Proof / validation** — retained evidence of observed behavior.
- **Closeout** — a completion summary for a bounded phase or effort.
- **RFC** — an architectural proposal or decision, stored and indexed under
  [`RFC/`](../RFC/).

Useful filename patterns include `*-investigation.md`, `*-proof.md`,
`*-runbook.md`, `phase-*`, and `v*-validation.md`; they are conventions, not a
complete naming scheme.

## Maintenance guidance

Keep current operator guidance easy to find. Architectural decisions belong in
RFCs. Historical evidence may remain in `docs/` without being individually
added here; add a document only when it materially improves navigation. Do not
rename historical files merely to impose chronology.
