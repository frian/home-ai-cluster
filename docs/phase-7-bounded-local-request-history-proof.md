# Phase 7 Bounded Local Request History Proof

Date: 2026-07-16

## Purpose

This document records the explicit local proof required by RFC-0035.

The proof used an isolated temporary XDG state directory. No real user state path was retained.

## Observed results

The proof confirmed:

1. clearing missing history succeeds;
2. inspecting missing history returns an empty JSON array;
3. one successful local request can be recorded with exit zero;
4. one unsupported-capability request can be recorded as `no-selectable-candidate` with non-zero exit;
5. inspection returns the failed record first and the successful record second;
6. each retained record contains only:
   - `status`;
   - `requested_capability`;
   - `selected_candidate_family`;
   - `outcome_rule`;
   - `failure_status`;
7. no prompt, generated content, node id, adapter, model, timestamp, request id, runtime URL, or private machine detail was retained;
8. clearing removes the retained history;
9. inspection after clearing returns an empty JSON array.

## Retained proof shape

Newest record:

```json
{
  "status": "failed",
  "requested_capability": "unsupported-proof-capability",
  "selected_candidate_family": null,
  "outcome_rule": "no-selectable-candidate",
  "failure_status": "no-selectable-candidate"
}
```

Older record:

```json
{
  "status": "succeeded",
  "requested_capability": "chat",
  "selected_candidate_family": "local",
  "outcome_rule": "local-only",
  "failure_status": null
}
```

## Privacy boundary

This proof record intentionally excludes:

- prompt content;
- generated content;
- raw command output;
- real filesystem paths;
- runtime URLs;
- private machine details.
