# Phase 8 Canonical Operator Workflow Investigation

Status: Investigation

Date: 2026-07-16

## Purpose

This document investigates the smallest useful Phase 8 increment after the
accepted static operator preflight.

It does not define a workflow contract, modify the two-machine proof, authorize
lifecycle automation, or introduce a new command.

Any stable operator contract still requires a separate RFC.

## Current Phase 8 position

The first Phase 8 increment is complete:

- RFC-0036 is accepted;
- `home-ai-cluster-preflight` exists;
- it validates ordinary local static node and adapter coherence;
- it performs no runtime or network observation;
- its retained proof is verified.

This closes the static-coherence gap, but not the broader operator-workflow gap.

## Existing operator surfaces

The repository already provides separate truthful surfaces:

- `home-ai-cluster-preflight` checks ordinary local static declarations;
- `home-ai-cluster-health` observes declared local adapters directly;
- the ordinary FastAPI application exposes `/v1/chat`;
- `home-ai-cluster-static-proof <remote-base-url>` runs the explicit two-machine
  proof path;
- routing and actual-request explanation commands expose decisions and failures;
- history commands inspect and clear opt-in bounded request history;
- the OpenAI-compatible process remains separate and loopback-only.

These surfaces should remain separate. A workflow document may order them without
combining their behavior.

## Existing documentation gap

`README.md` explains ordinary local operation and compatibility access.

`docs/static-two-machine-proof.md` explains the RFC-0022 proof procedure.

The repository still lacks one accepted document that explains:

- when preflight is relevant;
- when health observation is relevant;
- which checks belong on which machine;
- startup and shutdown order;
- how to classify static, runtime, LAN, port, and request failures;
- how to recover using only already-supported actions.

The operator can perform each step, but must still reconstruct the sequence from
repository-specific knowledge.

## Candidate next increments

### Universal start and stop commands

Rejected for the next increment.

They would require process ownership, external-runtime ownership, remote control,
already-running detection, logging, shutdown semantics, supervision, and
operating-system decisions.

### Extend preflight into runtime checks

Rejected.

RFC-0036 deliberately separates static coherence from runtime observation.
`home-ai-cluster-health` already owns direct local adapter observation.

### Add distributed mode to preflight

Deferred.

The accepted preflight is explicitly local-only. Distributed-proof validation is
a separate architectural question and is not required to document the existing
proof procedure.

### Canonical operator workflow document

Recommended for architectural definition.

A documentation-only workflow can connect existing commands and process
boundaries without changing them or taking ownership of external processes.

## Recommended architectural question

> Should Home AI Cluster define one canonical, documentation-only operator
> workflow that orders preparation, preflight, health, startup, request,
> shutdown, and recovery without introducing lifecycle ownership?

## Candidate workflow modes

A later RFC could define two explicit paths in one document.

### Ordinary local-only path

Candidate stages:

1. synchronize dependencies;
2. confirm the externally owned local runtime and required model;
3. run `home-ai-cluster-preflight`;
4. run `home-ai-cluster-health`;
5. start the ordinary application;
6. send one native `/v1/chat` request;
7. optionally inspect routing, actual-request explanation, or opt-in history;
8. stop the application through ordinary process interruption;
9. clear optional history only when explicitly desired.

This sequence is investigative, not accepted.

### Explicit two-machine proof path

Preserve the existing roles:

- receiving machine: ordinary application plus local runtime;
- calling machine: explicit static proof process.

Candidate stages:

1. verify both machines use the same repository revision;
2. synchronize dependencies on both machines;
3. confirm trusted-LAN scope and the receiving address;
4. run ordinary local preflight where ordinary registries are constructed;
5. verify receiving-machine local runtime health;
6. start the receiving ordinary application;
7. verify receiving-machine reachability;
8. start the calling proof process with the explicit remote base URL;
9. send one request to the calling loopback endpoint;
10. confirm cluster-owned attribution and visible failure behavior;
11. stop the calling proof process;
12. stop the receiving application;
13. remove any temporary firewall exception.

This sequence is investigative, not accepted.

## Important preflight limitation

The existing preflight validates only ordinary local static registries.

It does not validate the proof-specific remote declaration, remote URL, LAN path,
receiving machine, runtime, or model.

A canonical workflow must state this limitation rather than silently broadening
RFC-0036.

## Failure-layer boundary

A canonical workflow should point to the existing owning surface for each layer:

- static incoherence: `home-ai-cluster-preflight`;
- local runtime observation: `home-ai-cluster-health`;
- process startup or port conflict: the invoked process;
- receiving-machine reachability: the explicit LAN check;
- routing or execution failure: existing request and explanation surfaces;
- optional history state: existing history commands.

The workflow should not invent new machine-readable statuses or reinterpret
existing command contracts.

## Recovery boundary

The first workflow should include only boring supported actions:

- correct static declarations before rerunning preflight;
- start or repair the externally owned runtime before rerunning health;
- ensure the required model is locally available;
- stop a conflicting local process when a fixed port is occupied;
- verify the trusted-LAN address and temporary firewall scope;
- rerun the failed inspection step before repeating the request;
- stop proof processes with `Ctrl-C`;
- explicitly clear optional history when desired.

It should not define automatic repair, retries, service restart, remote shutdown,
process supervision, or configuration mutation.

## Candidate document

A later accepted increment could add:

```text
docs/operator-workflow.md
```

It could contain:

- scope and safety boundary;
- local-only workflow;
- explicit two-machine proof workflow;
- command ownership and port table;
- failure-layer lookup;
- shutdown order;
- recovery guidance;
- explicit non-goals;
- links to detailed proof and RFC documents.

It should not retain private addresses, prompts, responses, authorization values,
runtime URLs, or local filesystem paths.

## Why an RFC is required

Calling a workflow canonical establishes:

- accepted ordering between existing operator surfaces;
- supported local-only and proof-only modes;
- official shutdown and recovery expectations;
- the reproducible Phase 8 path.

Those are project-level operational decisions even when no code changes.

## Recommended RFC scope

A later RFC should decide only:

- whether one canonical workflow document exists;
- its two supported modes;
- exact ordered stages for each mode;
- which existing surface owns each verification step;
- shutdown order;
- recovery boundaries;
- privacy exclusions;
- reproducibility proof requirements.

It should preserve every existing command and endpoint contract.

## Explicit non-goals

The next increment should not add:

- start or stop commands;
- supervision or remote process control;
- service installation;
- automatic discovery or repair;
- retries or fallback changes;
- distributed-proof preflight;
- a new configuration format;
- an HTTP workflow endpoint;
- a daemon or dashboard;
- Docker or Kubernetes;
- a generic runbook framework.

## Proof candidate

A later documentation proof could demonstrate that an operator can:

1. follow the local-only path without consulting source code;
2. identify static and runtime problems at their owning stages;
3. start and stop the ordinary application from documented commands;
4. follow the two-machine roles and order from one document;
5. reproduce one routed request on a trusted LAN;
6. stop both proof processes and remove temporary network exposure;
7. distinguish what was validated from what remained external or proof-only.

The final reproducibility claim should be verified by an actual operator run.

## Recommended sequence

1. Review and merge this investigation.
2. Draft a narrow RFC for one canonical documentation-only workflow.
3. Review and merge the RFC proposal.
4. Accept the RFC separately.
5. Implement only the accepted document and focused documentation checks.
6. reproduce the documented paths and retain a privacy-safe proof.
7. Reassess whether evidence justifies lifecycle automation.

## Conclusion

The next Phase 8 gap is procedural, not computational.

The boring next step is one canonical documentation-only workflow, not a
supervisor, start command, distributed preflight, dashboard, or deployment
system.
