# Phase 8 Canonical Operator Workflow Proof

Status: Pending operator verification

Date: 2026-07-16

## Purpose

This document records the verification boundary for the canonical operator
workflow accepted by RFC-0037.

The implemented canonical document is:

```text
docs/operator-workflow.md
```

## Documentation evidence

The canonical workflow:

- defines ordinary local-only operation;
- defines explicit two-machine proof operation;
- orders preparation, preflight, health, startup, request, shutdown, and recovery;
- keeps ordinary local preflight separate from runtime and network observation;
- states that local preflight does not validate the proof-specific remote
  declaration, supplied URL, LAN path, remote runtime, model, or execution;
- preserves external runtime ownership;
- introduces no command, endpoint, source code, configuration format, lifecycle
  automation, discovery, dashboard, daemon, container, or database.

## Required operator verification

The implementation is complete only after an operator confirms that they can:

1. follow the local-only path without consulting source code;
2. run preflight before health and understand the distinction;
3. start, request through, and stop the ordinary application;
4. follow the receiving-machine and calling-machine roles;
5. reproduce one routed request across two real machines on a trusted LAN;
6. stop the calling proof process before the receiving application;
7. remove temporary firewall exposure when one was created;
8. identify what local preflight did not validate;
9. avoid retaining real prompts, responses, addresses, paths, secrets, or private
   machine details.

## Repository checks

Run normal repository documentation and test checks from the repository root.

## Privacy boundary

The retained completion record must not contain:

- real private LAN addresses;
- prompts or generated responses;
- authorization values or credentials;
- real filesystem paths;
- raw exceptions;
- machine names or hardware details;
- personal account details or secrets.

## Completion record

Pending operator verification.

Update this section only after both canonical paths have been followed and the
real two-machine routed request has been reproduced.