# RFC-0037: Canonical operator workflow

Status: Draft

Date: 2026-07-16

Author: frian

## Summary

Home AI Cluster should define one canonical documentation-only operator workflow:

```text
docs/operator-workflow.md
```

The document should connect the repository's existing operator surfaces into two
explicitly separate paths:

1. ordinary local-only operation;
2. explicit two-machine proof operation.

The workflow should define the supported order for preparation, static preflight,
runtime health observation, process startup, request verification, shutdown, and
recovery.

It must not add a command, endpoint, configuration format, process supervisor,
remote-control behavior, discovery mechanism, or runtime behavior.

## Problem

Phase 8 aims to make the existing static local cluster understandable and
repeatable as an ordinary operator workflow.

The repository already provides truthful but separate surfaces:

- `home-ai-cluster-preflight` for ordinary local static coherence;
- `home-ai-cluster-health` for ordinary local runtime health observation;
- the ordinary FastAPI application and native `/v1/chat` endpoint;
- `home-ai-cluster-static-proof <remote-base-url>` for the explicit two-machine
  proof path;
- routing and actual-request explanation commands;
- opt-in bounded request-history commands;
- the separate loopback-only OpenAI-compatible process.

Each surface has a narrow accepted meaning. An operator can use them, but the
supported order still has to be reconstructed from repository-specific knowledge.

The existing two-machine runbook proves RFC-0022. It does not yet serve as one
canonical workflow that explains how local-only and proof-only operation relate,
which inspection owns each failure layer, how processes should be stopped, or
what recovery steps remain supported.

## Goals

This RFC should:

- establish one canonical operator document;
- define two explicitly separate workflow modes;
- order existing preparation, inspection, startup, request, shutdown, and recovery
  steps;
- identify which existing command or process owns each verification layer;
- preserve the exact meanings of preflight, health, requests, explanations, and
  proof commands;
- state the limitations of ordinary local preflight in the two-machine path;
- keep process and runtime ownership explicit;
- provide boring recovery guidance using existing behavior only;
- require an actual privacy-safe reproducibility proof.

## Non-goals

This RFC does not add or define:

- start or stop commands;
- process supervision;
- service installation;
- remote process control;
- automatic discovery;
- automatic repair;
- automatic retries;
- fallback changes;
- a new configuration format;
- distributed-proof preflight;
- new machine-readable statuses;
- a workflow command;
- an HTTP workflow endpoint;
- a daemon;
- a dashboard;
- Docker or Kubernetes;
- a generic runbook framework;
- changes to existing ports, commands, endpoints, adapters, routing, or privacy
  contracts.

## Proposal

Add one canonical document:

```text
docs/operator-workflow.md
```

The document should be the shortest supported path for an operator who wants to:

- run the ordinary local-only cluster;
- reproduce the explicit two-machine proof;
- identify which layer failed;
- stop the processes safely;
- recover using supported manual actions.

It should link to detailed RFCs and proof records instead of copying their full
contracts.

## Supported modes

The canonical document should define exactly two modes.

### Mode 1: ordinary local-only operation

This mode uses:

- the ordinary static local node registry;
- the ordinary static runtime-adapter registry;
- one externally owned local runtime;
- the ordinary FastAPI application;
- the native `/v1/chat` endpoint.

The canonical order should be:

1. use a supported Python version and synchronize dependencies with `uv sync`;
2. ensure the externally owned local runtime is installed and running;
3. ensure the adapter's currently required local model is available;
4. run `home-ai-cluster-preflight`;
5. stop and correct repository-owned static declarations if preflight reports
   `incoherent`;
6. run `home-ai-cluster-health`;
7. stop and repair the externally owned runtime or model if health is not usable;
8. start the ordinary application with the documented `uvicorn` command;
9. send one native `/v1/chat` request;
10. optionally use existing routing, actual-request explanation, or opt-in history
    surfaces;
11. stop the ordinary application with normal process interruption;
12. clear opt-in history only when the operator explicitly wants to remove it.

The workflow should not imply that Home AI Cluster starts, supervises, repairs,
or stops the external runtime.

### Mode 2: explicit two-machine proof operation

This mode preserves the accepted RFC-0022 roles:

- receiving machine: ordinary application plus externally owned local runtime;
- calling machine: explicit static proof process.

Both machines must remain on the same trusted LAN for this proof.

The canonical order should be:

1. verify both machines use the same repository revision;
2. use supported Python versions and run `uv sync` on both machines;
3. confirm the trusted-LAN boundary;
4. determine the receiving machine's current LAN address without retaining it in
   repository documentation;
5. on the receiving machine, ensure the externally owned runtime is installed,
   running, and has the required model;
6. on the receiving machine, run `home-ai-cluster-preflight`;
7. on the receiving machine, run `home-ai-cluster-health`;
8. start the receiving machine's ordinary application on the documented LAN bind;
9. if needed, create only a temporary host-firewall allowance scoped to the
   trusted LAN and documented proof port;
10. from the calling machine, verify the receiving ordinary endpoint is reachable;
11. on the calling machine, start
    `home-ai-cluster-static-proof <remote-base-url>`;
12. send one native `/v1/chat` request to the calling process's documented
    loopback endpoint;
13. confirm the expected cluster-owned node attribution and visible failure
    behavior;
14. stop the calling proof process with normal process interruption;
15. stop the receiving ordinary application;
16. remove any temporary firewall allowance created for the proof.

The workflow should state that this remains a proof-only path, not ordinary
distributed activation.

## Preflight limitation in two-machine mode

`home-ai-cluster-preflight` validates only the ordinary local static registries
constructed on the machine where it runs.

It does not validate:

- the proof-specific remote node declaration;
- the supplied remote base URL;
- the LAN route;
- the receiving machine;
- the receiving runtime;
- the receiving model;
- remote request execution.

The canonical workflow must state this limitation immediately beside the
preflight step in the two-machine path.

It must not suggest that RFC-0036 provides distributed-proof validation.

## Verification ownership

The canonical document should map each layer to its current owning surface:

- repository-owned static declaration coherence:
  `home-ai-cluster-preflight`;
- ordinary local adapter health observation:
  `home-ai-cluster-health`;
- process startup and fixed-port conflicts:
  the invoked process and operating system;
- receiving-machine reachability:
  the explicit trusted-LAN request described by the workflow;
- routing and execution outcome:
  the existing request and explanation surfaces;
- optional retained request history:
  `home-ai-cluster-history` and `home-ai-cluster-clear-history`.

The workflow should not duplicate, reinterpret, or merge the machine-readable
contracts of these surfaces.

## Ports and process ownership

The canonical document should include one concise table that names only accepted
processes and ports already documented by the repository.

It should distinguish:

- externally owned AI runtimes;
- the ordinary Home AI Cluster application;
- the explicit proof process;
- the optional OpenAI-compatible process.

The table must not imply process supervision or automatic lifecycle ownership.

The compatibility process may be referenced as an optional separate access path,
but it should not be inserted into either canonical native workflow.

## Shutdown order

For local-only operation:

1. stop the ordinary application;
2. leave the external runtime running or stop it manually according to the
   operator's own runtime policy.

For the two-machine proof:

1. stop the calling proof process;
2. stop the receiving ordinary application;
3. remove temporary firewall exposure;
4. leave or stop the external runtime manually according to operator policy.

Home AI Cluster should not claim ownership of runtime shutdown.

## Recovery guidance

The first workflow should include only manual recovery actions already supported
by current behavior:

- correct repository-owned static declarations before rerunning preflight;
- start or repair the external runtime before rerunning health;
- ensure the required model is locally available;
- stop a conflicting process when an accepted fixed port is occupied;
- verify the trusted-LAN address and temporary firewall scope;
- rerun the failed inspection step before repeating a request;
- stop Home AI Cluster processes with normal process interruption;
- explicitly clear optional request history when desired.

It must not prescribe automatic repair, retries, service restart, remote shutdown,
configuration mutation, or process supervision.

## Privacy boundary

The canonical document and retained proof may include:

- repository command names;
- accepted endpoint paths;
- accepted loopback and example addresses already used by documentation;
- process roles;
- ordered stages;
- stable public failure categories already owned by existing contracts.

They must not retain:

- real private LAN addresses;
- authorization values;
- prompts or responses;
- generated content;
- real filesystem paths;
- raw exceptions;
- machine names;
- hardware details;
- personal account details;
- secrets or runtime credentials.

The workflow should use placeholders for operator-specific network values.

## Documentation boundary

Implementation should add or update only documentation and focused documentation
checks where useful.

It should not add source code merely to make the documentation easier to test.

The canonical document should remain concise and point to:

- `README.md` for project entry and ordinary application context;
- `docs/static-two-machine-proof.md` for the detailed RFC-0022 proof procedure;
- RFC-0036 for static preflight semantics;
- existing health, explanation, history, and compatibility RFCs where relevant.

Existing detailed proof documents should remain retained history, not be rewritten
as the canonical workflow.

## Rationale

The next Phase 8 gap is procedural rather than computational.

One accepted document can reduce hidden repository knowledge without changing the
architecture or pretending that Home AI Cluster owns external runtimes and remote
processes.

Keeping the two modes separate preserves the project's local-only default and the
explicit opt-in nature of distributed proof wiring.

Documentation-first is the boring solution. It provides evidence about the real
operator pain before lifecycle automation is considered.

## Alternatives considered

### Add a universal start command

Rejected.

It would require decisions about process ownership, remote execution, service
installation, already-running detection, logs, shutdown, supervision, and
operating-system behavior.

### Extend preflight into runtime or distributed checks

Rejected.

RFC-0036 deliberately defines ordinary local static coherence only. Runtime health
already belongs to `home-ai-cluster-health`, while distributed-proof validation
would require a separate contract.

### Merge health, preflight, and request checks into one command

Rejected.

The existing surfaces answer different truthful questions. Combining them would
blur ownership and create a larger compatibility contract.

### Treat the existing proof runbook as already canonical

Rejected.

The current runbook proves RFC-0022 but does not define the relationship between
local-only operation, preflight, health, shutdown, recovery, and optional operator
surfaces.

### Add a generic runbook framework

Rejected.

One workflow document does not justify a reusable documentation system.

## Trade-offs

A documentation-only workflow does not remove manual process startup or network
setup.

It may reveal that some steps are repetitive. That evidence is useful, but it
does not by itself justify automation.

The document creates a maintenance obligation: when accepted commands or proof
paths change through later RFCs, the canonical workflow must be reviewed.

The workflow cannot guarantee that an external runtime, model, LAN, firewall, or
operating system behaves correctly. It can only order existing checks and state
which layer owns each failure.

## Impact

This RFC affects:

- one future canonical operator document;
- links from `README.md` or other entry documentation;
- one privacy-safe reproducibility proof;
- optional focused checks for documented command names and paths.

It does not affect:

- application code;
- adapters;
- routing or fallback;
- HTTP contracts;
- CLI contracts;
- process ports;
- external runtime ownership;
- distributed activation;
- configuration formats;
- request history behavior.

## Proof requirements

Implementation should not be considered complete until a retained privacy-safe
proof demonstrates that an operator can:

1. follow the local-only path from `docs/operator-workflow.md` without consulting
   source code;
2. run preflight before health and understand the distinction;
3. start, request through, and stop the ordinary application using documented
   steps;
4. follow the documented receiving and calling roles for the two-machine proof;
5. reproduce one routed request across two real machines on a trusted LAN;
6. stop the calling process before the receiving application;
7. remove temporary firewall exposure, when one was created;
8. identify which checks did not validate the remote proof declaration, LAN,
   runtime, or model;
9. avoid retaining real prompts, responses, addresses, filesystem paths, secrets,
   or private machine details.

Normal repository documentation checks should also pass.

## Open questions

The following remain deferred:

- whether evidence later justifies start or stop helpers;
- whether distributed-proof preflight should exist;
- whether packaging or service installation should be investigated;
- whether the compatibility process should later have its own canonical workflow;
- whether Phase 8 needs additional recovery documentation after real operator use.

These questions do not block the documentation-only workflow.

## Decision

Pending.
