# Aider Static-Cluster Compatibility Proof

Status: Completed

Execution date: 2026-07-18

## Purpose

This document retains the approved, privacy-safe structural result of one
bounded real two-machine Aider execution. It records no implementation or
architectural decision. The procedure is retained in the
[Aider static-cluster compatibility proof runbook](aider-static-cluster-proof-runbook.md).

## Execution basis

The physical caller and receiver roles were confirmed on one trusted LAN. Both
used this shared repository commit:

```text
6535fd3ba16ad57aa5d4d3cef86b089f1179702a
```

One declared remote node and the sanitized command forms were confirmed. The
caller compatibility listener remained loopback-only.

## Approved structural result

Before the one Aider submission, the receiver runtime was available and the
caller runtime was unavailable. Aider 0.86.2 was compatible with and completed
the bounded Aider 0.86.0-style configuration categories in the runbook.

Exactly one Aider submission was made. The caller produced exactly this one
sanitized RFC-0047 success observation:

```text
proof_observation accepted_request=1 outcome=success result_node_id=<DECLARED_REMOTE_NODE_ID>
```

The final caller-owned attribution matched the declared remote node. The
receiver observed one routed request. Aider received one successful unchanged
RFC-0031 compatibility response; that response remained topology-blind and
completed without a public routing extension. No additional accepted request,
proof-observation line, or retry was observed.

Cleanup was operator-owned. No repository proof artifact from the execution was
retained; this document contains only the approved structural evidence.

Outcome: **PASS**.

## What this proves

This execution proves one bounded path: one Aider submission reached the
caller-local compatibility edge, completed through the existing declaration-
backed static-cluster path after the caller-local runtime was unavailable, and
returned an unchanged topology-blind compatibility response. The caller's final
internal attribution was the declared remote node, and the receiver observed
the routed request.

## What this does not prove

This proof does not establish general Aider support, another Aider mode or
version, general OpenAI-compatible API support, production readiness,
performance, authentication, encryption, internet-facing operation, discovery,
scheduling, retries, multiple remotes, runtime lifecycle automation, or a
broader compatibility contract.

## Privacy boundary

This retained record contains only the execution date, shared revision,
sanitized roles, approved structural observations, Aider version, and the
placeholder `<DECLARED_REMOTE_NODE_ID>`. It retains no prompt, response,
generated content, address, URL, hostname, username, machine name, path,
declaration content, credential, token, raw log, command output, transcript,
screenshot, shell history, timing, or private node ID.
