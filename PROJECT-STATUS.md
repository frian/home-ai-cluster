# Home AI Cluster — Project Status

**Status:** Proposed shared working index (not architectural authority)  
**Last reviewed:** 2026-10-16

This is a short, human-maintained coordination snapshot across independent HAC repositories and conversations. Read the linked source before acting: a status entry does not establish a Git fact, an accepted decision, or audit evidence. See [PROJECT-LOG.md](PROJECT-LOG.md) for dated updates.

## Workstreams

| ID | Scope | State | Evidence / reference | Next action |
| --- | --- | --- | --- | --- |
| HAC-W001 | Shared project coordination (CORE repository; documentation only) | In review | This Draft PR | Review the two-file convention; merge only after normal review. |
| HAC-W002 | Core external-information evidence enrichment | In review | [CORE PR #854](https://github.com/frian/home-ai-cluster/pull/854) (open, unmerged when checked 2026-10-16) | Complete independent review and decide disposition; do not infer acceptance from PR state. |
| HAC-W003 | Desktop request lifecycle reliability | Proposed | [Desktop main](https://github.com/frian/home-ai-cluster-desktop/tree/main) at `1ed626c2a7a1c98dc5bebcb1be509e2597130d05` | Review timeout and abandoned reply cleanup against accepted Desktop decisions before proposing a fix. |
| HAC-W004 | HAC-CAP toolkit follow-up | Proposed | [Audit repository](https://github.com/frian/home-ai-cluster-audit), `main` at `c73697679213df227d073f31a9467b45cb853026` when checked 2026-10-16 | Determine current audit-toolkit and review state from its repository and PRs before declaring a next milestone. |

These are **coordination IDs**, not RFC numbers, issue numbers, priority assignments or audit finding IDs. IDs are never reused. Avoid listing each PR or review as a separate workstream when it belongs to an existing one.

## Operating convention

- At the start of substantial work, read this file and verify the **relevant** linked repository branch, PR and accepted decisions. Do not assume project conversations or attached copies are synchronized.
- Each conversation focuses on one workstream. Architectural discussion, implementation and independent review have distinct responsibilities; agents do not adopt architecture, merge, or close work without operator approval.
- Prefer at most **three active implementation workstreams** as a soft planning preference, not a permission gate. Read-only reviews need not count against it.
- Use `Proposed`, `Active`, `In review`, `Blocked`, `Implemented`, or `Completed`. `Implemented` means integrated code with follow-up validation outstanding; `Completed` requires explicit closeout evidence. Use the audit protocol's own statuses for audit findings and challenge state.
- At a meaningful milestone, update this compact current snapshot **and** add a dated entry to the log. Avoid logging ordinary chat messages or pasting prompts. Only record independently verified facts as facts; label plans and operator-reported information.
- Re-read the current remote files before updating. Use a focused branch / Draft PR, preserve concurrent edits, and never silently push tracking changes directly to the base branch. A conflicting change requires reconciliation, not overwrite.
- Before closing a workstream, verify relevant accepted decision(s), PR merge/commit, required validation, and the next action or explicit closure. An open PR, green CI, or completed audit report does not alone establish completion.

## Authority and independence

Accepted RFCs, binding contracts, pinned Git revisions and immutable audit evidence remain authoritative within their domains. This index cannot accept a decision, authorize a network/test action, change a product boundary or supersede repository-specific `AGENTS.md`.

HAC-CAP `BLIND` reviewers must not read `PROJECT-STATUS.md` or `PROJECT-LOG.md` during their campaigns. These coordination documents are outside the authorized BLIND input set, regardless of their current content. Use a fresh unanchored session with only protocol-authorized inputs; no workflow convenience overrides audit independence.
