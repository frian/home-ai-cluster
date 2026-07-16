# Phase 8 Canonical Operator Workflow Investigation

Status: Investigation

Date: 2026-07-16

## Purpose

This document investigates the smallest useful Phase 8 increment after the
accepted static operator preflight.

It does not define a workflow contract, modify the existing two-machine proof,
authorize lifecycle automation, or introduce a new command.

Any stable operator contract still requires a separate RFC.

## Current Phase 8 position

Phase 8 aims to make the existing static local cluster understandable and
repeatable as an ordinary operator workflow.

The first increment is now complete:

- RFC-0036 is accepted;
- `home-ai-cluster-preflight` exists;
- the command validates ordinary local static node and adapter coherence;
- it performs no runtime or network observation;
- its retained proof is verified.

This closes the static-coherence gap, but not the broader operator-workflow gap.

## Current operator surfaces

The repository already provides separate truthful surfaces for different
questions:

- `home-ai-cluster-preflight` checks ordinary local static declaration coherence;
- `home-ai-cluster-health` combines declared local facts with direct adapter
  health observations;
- the ordinary FastAPI application exposes the native `/v1/chat` endpoint;
- `home-ai-cluster-static-proof <remote-base-url>` constructs the explicit
  two-machine proof path;
- `home-ai-cluster-explain-routing` and `home-ai-cluster-explain-request` explain
  routing and actual request outcomes;
- `home-ai-cluster-history` and `home-ai-cluster-clear-history` inspect and clear
  opt-in bounded request history;
- `home-ai-cluster-openai-compatibility` exposes the separate loopback-only
  compatibility process.

These surfaces remain intentionally separate. No single command should combine
them merely for convenience.

## Existing documentation

The repository already contains useful but separate instructions:

- `README.md` explains the ordinary local application and compatibility process;
- `docs/static-two-machine-proof.md` contains the RFC-0022 two-machine proof
  procedure;
- retained proof documents record successful milestones and narrow contracts;
- command-specific RFCs define exact machine-readable behavior.

The existing two-machine runbook is a proof runbook, not yet a canonical operator
workflow.

It assumes repository knowledge about:

- why the receiving machine starts the ordinary application;
- why the calling machine uses a proof-specific process;
- when static preflight is relevant;
- when health observation is relevant;
- which checks belong on which machine;
- how to distinguish static inconsistency, runtime unavailability, LAN failure,
  and request failure;
- which process owns which port;
- what local state may need clearing;
- what should be stopped and in which order.

## Remaining operator problem

After RFC-0036, an operator can answer:

> Are the ordinary local static declarations internally coherent?

The operator still lacks one canonical documented answer to:

> In what order should I prepare, inspect, start, verify, use, stop, and recover
> the existing local-only or explicit two-machine cluster?

The current documentation makes each individual step possible, but the sequence
still has to be reconstructed from repository-specific knowledge.

## Candidate next increments

### Candidate A: Universal start and stop commands

Assessment: rejected for the next increment.

Such commands would need to decide process ownership, external runtime ownership,
remote process control, already-running detection, log handling, port conflicts,
shutdown semantics, supervision, and operating-system behavior.

The current evidence still does not justify those architectural decisions.

### Candidate B: Extend preflight into runtime checks

Assessment: rejected.

RFC-0036 deliberately separates static coherence from runtime observation.
Adding runtime or network probes would violate the accepted preflight meaning.

The existing health command already owns direct local adapter observation.

### Candidate C: Add distributed mode to preflight

Assessment: deferred.

The first accepted preflight is explicitly local-only. A distributed-proof input
would require a separate contract and is not necessary to document the existing
proof procedure.

### Candidate D: Canonical operator workflow document

Assessment: recommended for architectural definition.

A canonical workflow can connect existing commands and process boundaries without
changing their behavior or taking ownership of external processes.

The smallest useful version should be documentation-first and should use only
already accepted commands, endpoints, and proof paths.

## Recommended next architectural question

The next narrow Phase 8 question should be:

> Should Home AI Cluster define one canonical, documentation-only operator
> workflow that orders the existing preparation, preflight, health, startup,
> request, shutdown, and recovery steps without introducing lifecycle ownership?

This question is smaller than lifecycle automation and larger than another
isolated command.

## Proposed workflow modes

A later RFC could define two explicitly separate paths in one operator document.

### Ordinary local-only path

This path would use the ordinary static local registries and one local runtime.

Candidate sequence:

1. synchronize dependencies;
2. confirm the external local runtime and required model are available;
3. run `home-ai-cluster-preflight`;
4. run `home-ai-cluster-health`;
5. start the ordinary application;
6. send one native `/v1/chat` request;
7. optionally use routing or actual-request explanation surfaces;
8. stop the application with ordinary process interruption;
9. clear opt-in history only when the operator explicitly wants to remove it.

This sequence is investigative, not accepted.

### Explicit two-machine proof path

This path would preserve the existing RFC-0022 roles:

- receiving machine: ordinary application plus local runtime;
- calling machine: explicit static proof process.

Candidate sequence:

1. verify both machines use the same repository revision;
2. synchronize dependencies on both machines;
3. verify trusted-LAN scope and receiving-machine address;
4. run local static preflight where ordinary local registries are constructed;
5. verify the receiving machine's local runtime health;
6. start the receiving ordinary application;
7. verify receiving-machine reachability;
8. start the calling proof process with the explicit remote base URL;
9. send one request to the calling machine's loopback endpoint;
10. confirm cluster-owned node attribution and visible failure behavior;
11. stop the calling proof process;
12. stop the receiving application;
13. remove any temporary firewall exception created for the proof.

This sequence is investigative, not accepted.

## Important preflight limitation

The existing preflight validates only ordinary local static registries.

It does not validate the proof-specific remote declaration created by
`home-ai-cluster-static-proof`.

A canonical two-machine workflow must state this limitation truthfully rather than
implying that local preflight validates the remote URL, LAN path, receiving
machine, model, or proof-specific node declaration.

This limitation does not block a documentation-only workflow.

It may later provide evidence for a separate distributed-proof preflight RFC, but
that decision should not be folded into the workflow contract now.

## Failure classification boundary

A canonical workflow should help the operator distinguish at least these existing
failure layers without inventing new machine-readable statuses:

- static declaration incoherence: reported by `home-ai-cluster-preflight`;
- local runtime observation failure: reported by `home-ai-cluster-health`;
- process startup or port conflict: reported by the invoked process;
- receiving-machine reachability failure: observed during the explicit LAN check;
- actual request routing or execution failure: reported by existing request
  surfaces;
- optional history state: inspected or cleared through existing history commands.

The workflow should point to the owning surface for each layer.

It should not duplicate or reinterpret command contracts.

## Recovery guidance boundary

The first canonical workflow should include only boring recovery actions already
supported by the repository and ordinary operating system behavior:

- correct static declarations in code before rerunning preflight;
- start or repair the externally owned runtime before rerunning health;
- ensure the required model is locally available;
- stop a conflicting local process when an accepted fixed port is occupied;
- verify the trusted-LAN address and temporary firewall scope;
- rerun the failed inspection step before repeating the request;
- stop proof processes with `Ctrl-C`;
- explicitly clear optional request history when desired.

It should not define automatic repair, retries, service restart, remote shutdown,
process supervision, or configuration mutation.

## Candidate document shape

A later accepted increment could add one concise document such as:

```text
docs/operator-workflow.md
```

The document could contain:

- scope and safety boundary;
- ordinary local-only workflow;
- explicit two-machine proof workflow;
- command ownership and port table;
- failure-layer lookup;
- shutdown order;
- recovery guidance;
- explicit non-goals;
- links to detailed proof and command documents.

The document should avoid copying full RFC contracts or retaining private machine
addresses, prompts, responses, runtime URLs, authorization values, or local
filesystem paths.

## Does this require an RFC?

Yes, if the repository calls the document canonical.

A canonical operator workflow establishes:

- an accepted ordering between existing operator surfaces;
- the supported distinction between local-only and proof-only operation;
- the official shutdown and recovery expectations;
- what an operator may reasonably treat as the reproducible Phase 8 path.

Those are project-level operational decisions even when no code changes.

The RFC can remain small because it need not change any command or endpoint.

## Recommended first RFC scope

A later RFC should decide only:

- whether one canonical workflow document exists;
- its two supported modes;
- the exact ordered stages for each mode;
- which existing surface owns each verification step;
- shutdown order;
- recovery guidance boundaries;
- privacy exclusions;
- proof requirements for reproducibility.

It should explicitly preserve all existing command contracts.

## Explicit non-goals

The next increment should not add:

- start or stop commands;
- process supervision;
- service installation;
- remote process control;
- automatic discovery;
- automatic repair;
- retries or fallback changes;
- a new configuration format;
- distributed-proof preflight;
- an HTTP workflow endpoint;
- a daemon;
- a dashboard;
- Docker or Kubernetes;
- a generic runbook framework.

## Proof candidate

A later documentation proof could demonstrate that a fresh operator session can:

1. follow the local-only path without consulting source code;
2. identify a static inconsistency at the preflight stage;
3. identify a runtime problem at the health stage;
4. start and stop the ordinary application using documented commands;
5. follow the two-machine proof roles and order from one canonical document;
6. reproduce one routed two-machine request on a trusted LAN;
7. stop both proof processes and remove temporary network exposure;
8. distinguish what was validated from what remained external or proof-only.

No new runtime implementation proof is required merely to write the workflow,
but the final reproducibility claim should be verified by an actual operator run.

## Recommended sequence

1. Review and merge this investigation.
2. Draft a narrow RFC for one canonical documentation-only operator workflow.
3. Review and merge the RFC proposal.
4. Accept the RFC separately.
5. Implement only the accepted document and focused documentation checks.
6. Reproduce the documented paths and retain a privacy-safe proof.
7. Reassess whether remaining evidence justifies any lifecycle automation.

## Conclusion

The static preflight closes one important Phase 8 gap without changing runtime
behavior.

The next gap is procedural rather than computational: existing truthful commands
and proof paths are not yet connected by one accepted operator sequence.

The boring next step is therefore one canonical documentation-only workflow, not
a supervisor, start command, distributed preflight, dashboard, or deployment
system.
