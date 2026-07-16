# Phase 8 Canonical Operator Workflow Proof

Status: Verified

Date: 2026-07-16

## Purpose

This document records the privacy-safe operator verification of the canonical
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

## Operator verification

The canonical workflow was followed as an operator procedure on 2026-07-16.

### Ordinary local-only operation

The operator:

1. synchronized the repository dependencies;
2. ran `home-ai-cluster-preflight` before runtime health observation;
3. observed a `coherent` local-only static report with the declared adapter
   resolving in the ordinary adapter registry;
4. ran `home-ai-cluster-health` and observed the local runtime adapter as
   available;
5. started the ordinary application using the documented command;
6. sent one real native `/v1/chat` request;
7. observed cluster-owned attribution to the ordinary local node;
8. stopped the ordinary application using normal process interruption.

This verified that preflight and health answer different questions: static
repository-owned coherence and real runtime observation respectively.

### Explicit two-machine proof operation

The operator used two real machines on one trusted LAN and confirmed that both
checkouts used the same repository revision.

The receiving machine:

1. synchronized dependencies;
2. ran ordinary local preflight and observed a coherent report;
3. ran ordinary health observation and observed the runtime adapter as available;
4. started the ordinary application using the documented trusted-LAN bind.

The calling machine then:

1. reached the receiving machine's native endpoint over the trusted LAN;
2. started `home-ai-cluster-static-proof` with the receiving base URL;
3. sent one real native request to the calling process's loopback endpoint;
4. observed successful execution through the receiving runtime;
5. observed cluster-owned attribution to `declared-remote`.

The proof process was stopped before the receiving ordinary application. No
operator-specific network value or machine detail is retained here. The
conditional temporary-firewall cleanup step applies only when such an allowance
was created; no firewall configuration detail is retained in this record.

## Verified boundaries

The operator confirmed that ordinary local preflight did not validate:

- the proof-specific remote node declaration;
- the supplied remote base URL;
- the LAN route;
- the receiving machine;
- the receiving runtime or model;
- remote request execution.

Those layers were verified separately by health observation, direct trusted-LAN
reachability, and the real routed request.

## Repository checks

The implementation branch passed:

```text
uv run ruff check .
uv run pytest
```

The test run reported 387 passing tests.

## Privacy boundary

This completion record intentionally does not retain:

- real private LAN addresses;
- prompts or generated responses;
- authorization values or credentials;
- real filesystem paths;
- raw exceptions;
- machine names or hardware details;
- personal account details or secrets.

## Completion record

RFC-0037 operator verification is complete.

Both canonical paths were followed without consulting source code for operational
steps, and one real routed request was reproduced across two machines on a
trusted LAN.
