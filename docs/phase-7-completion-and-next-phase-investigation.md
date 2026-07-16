# Phase 7 Completion and Next Phase Investigation

Status: Investigation

Date: 2026-07-16

## Purpose

This document closes the factual review of Phase 7 and investigates the smallest useful next project phase.

It does not modify the roadmap, select a Phase 8, or authorize implementation.

Any architectural decision still requires an RFC.

## Current milestone status

The guiding milestone is:

> One endpoint. Two machines. One routed request.

The repository has now demonstrated:

- one native endpoint;
- two explicit nodes;
- capability-based routing;
- automatic candidate selection;
- one real request routed to a selected node;
- fallback and failure classification;
- separate Ollama and llama-server runtime adapters;
- a separate OpenAI-compatible process;
- routing explanation;
- local node and adapter health inspection;
- structured actual-request failures;
- explicit bounded prompt-free request history.

The milestone is therefore proven at the architecture and proof level.

The project should not keep treating the first milestone as unfinished merely because ordinary daily operation remains manual.

## Phase 7 completion

Phase 7 expected:

- request history without prompt logging by default;
- routing explanation;
- node status;
- health view;
- failure visibility;
- clear privacy boundaries.

These outcomes now exist through RFC-0032, RFC-0033, RFC-0034, and RFC-0035.

Phase 7 is complete.

This does not mean the system is production-ready, broadly distributed, or convenient for every user. It means the accepted observability and trust outcomes have been implemented and proved within their explicit boundaries.

## The next problem should be an operator problem

The largest remaining gap is not another AI capability.

It is the distance between:

> the repository can prove the cluster architecture

and:

> one person can start, inspect, use, stop, and recover the existing local cluster without reconstructing the proof procedure from repository knowledge.

The next phase should improve operation of the architecture that already exists before adding new architecture.

## Evidence from the current system

The current proofs rely on explicit operator knowledge about:

- which processes must be started;
- which runtime must already be running;
- which node and adapter declarations must be selected;
- which opt-in distributed settings are required;
- which command or endpoint verifies each layer;
- how to distinguish configuration failure from runtime failure;
- how to stop or reset local state;
- how to repeat a two-machine proof safely.

This is acceptable for architecture development, but it is not yet a coherent daily operator workflow.

The repository has multiple truthful inspection surfaces, but no single documented operational path connecting them.

## Candidate next-phase directions

### Candidate A: More AI capabilities

Examples:

- vision;
- embeddings;
- tool calling;
- multi-model workflows.

Assessment:

Deferred. These expand what the cluster can do but do not make the existing cluster easier to operate or trust.

### Candidate B: Automatic node or model discovery

Assessment:

Deferred. Discovery introduces ownership, trust, freshness, conflict, authentication, and network-lifecycle decisions. The project does not yet have evidence that manual static declarations are the primary operational pain.

### Candidate C: Dashboard or web UI

Assessment:

Rejected for the next phase. A UI would hide unresolved operator workflows rather than define them. Existing CLI and JSON surfaces are sufficient for the next proof.

### Candidate D: Packaging and deployment system

Examples:

- Docker;
- Kubernetes;
- installation bundles;
- automatic service management.

Assessment:

Deferred. The project should first define the smallest correct operational workflow before packaging it.

### Candidate E: Operable local cluster

Make the already-proven architecture straightforward to start, inspect, use, stop, and recover in ordinary local two-machine use.

Assessment:

Recommended for further architectural definition.

This direction improves usefulness without changing the cluster abstraction.

## Proposed Phase 8 question

The smallest useful roadmap question is:

> How can one operator run the existing local two-machine cluster predictably without introducing automatic discovery, a daemon architecture, a dashboard, containers, or new AI capabilities?

A possible phase title is:

> Phase 8 — Operable local cluster

This title is provisional. The investigation does not modify the roadmap.

## Candidate Phase 8 goal

A possible goal is:

> Make the existing static local cluster understandable and repeatable as an ordinary operator workflow.

The phase should preserve static declarations and explicit process boundaries while reducing hidden procedural knowledge.

## Candidate outcomes

A later roadmap change could consider these outcomes:

- one documented canonical startup order;
- one documented canonical shutdown order;
- one explicit configuration validation command;
- one operator preflight view that composes existing static facts without probing or mutating the cluster;
- one repeatable two-machine runbook;
- clear recovery guidance for unavailable runtimes and nodes;
- explicit separation between local-only mode and opt-in two-machine mode;
- one concise current-state document describing what runs where;
- proof that a fresh operator session can reproduce the existing milestone from documented commands.

These are candidate outcomes, not accepted contracts.

## Important distinction: operability is not orchestration architecture

A next phase should not turn startup convenience into a service manager, deployment platform, or agent control plane.

The project should distinguish:

- documenting an existing process boundary;
- validating static configuration;
- presenting existing facts together;
- starting or supervising external processes;
- discovering or registering nodes dynamically.

The first three may be small operator improvements.

The latter two introduce substantial architecture and must not be assumed.

## Smallest plausible first increment

The smallest plausible increment is not a universal `start` command.

It is an investigation and then, if accepted, one read-only local preflight command that answers whether the statically configured cluster is internally coherent before a request is sent.

Such a command might eventually report only facts already owned by the repository, for example:

- configured node families;
- declared capabilities;
- declared adapters;
- whether every node adapter name resolves in the local adapter registry;
- whether the selected operating mode is local-only or distributed-proof mode;
- configuration inconsistencies that can be determined without network access.

This is only a candidate. It requires an RFC because it defines a new operator contract.

It must not silently become:

- a runtime health probe;
- a network scanner;
- node discovery;
- process supervision;
- configuration mutation;
- a deployment system.

## Why not start with a `start cluster` command

A start command would immediately need to decide:

- which processes it owns;
- whether it starts external runtimes;
- whether it starts remote processes;
- how it detects already-running processes;
- where logs go;
- how shutdown works;
- how failures are surfaced;
- whether it becomes a long-running supervisor;
- how it behaves across operating systems.

Those decisions are much larger than the current evidence.

The boring next step is to make the manual workflow explicit and validate static inputs before automating lifecycle ownership.

## Configuration questions still unresolved

Before any implementation, a focused RFC or prior investigation must decide:

1. Which current configuration sources are authoritative?
2. What configuration errors can be determined without runtime or network access?
3. Should a preflight command read only default static registries or accept an explicit proof configuration?
4. What is the exact difference between configuration validation and health observation?
5. Which output fields are stable operator contract and which remain implementation details?
6. Should preflight failure be one non-zero status or have stable categories?
7. How should private runtime URLs and machine details remain hidden?
8. Does the first increment need any new configuration format?
9. Can the first increment avoid changing application startup entirely?
10. What evidence would justify lifecycle automation later?

## Recommended boundaries

Any proposed Phase 8 should initially preserve:

- local-first and privacy-first operation;
- engine independence;
- capability-centered routing;
- static node and adapter declarations;
- local-only behavior by default;
- distributed behavior only through explicit proof configuration;
- existing native and OpenAI-compatible process separation;
- no database;
- no dashboard;
- no Docker or Kubernetes;
- no automatic discovery;
- no automatic model discovery;
- no service supervisor;
- no remote process control;
- no new public HTTP contracts unless separately justified;
- no generic configuration framework without evidence;
- no attempt to hide external runtime ownership.

## Deferred directions

The following should remain deferred unless new evidence changes priorities:

- automatic node discovery;
- automatic model discovery;
- service supervision;
- remote start and stop;
- installation packaging;
- container orchestration;
- dashboard or web UI;
- scheduling policies;
- vision;
- embeddings;
- tool calling;
- multi-model workflows;
- plugins;
- cloud nodes;
- advanced distributed inference.

## Recommended next decision sequence

The project should proceed in this order:

1. accept that Phase 7 is complete;
2. review and merge this investigation;
3. update `ROADMAP.md` in a separate proposal PR to add a narrowly worded Phase 8;
4. accept that roadmap change separately;
5. investigate the first Phase 8 increment in repository detail;
6. write an RFC only after the exact first operator contract is understood;
7. let an implementation agent implement the accepted RFC.

## Conclusion

The founding milestone is proven and Phase 7 is complete.

The project should now improve the ordinary operation of the architecture it already has rather than add new capabilities or infrastructure.

The strongest next-phase candidate is an operable local cluster: a small, explicit, repeatable operator workflow for the existing static two-machine architecture.

The first likely increment is static configuration preflight, not lifecycle automation.

This direction is not yet accepted. The roadmap must be changed separately before implementation work begins.
