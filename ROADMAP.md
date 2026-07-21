# Roadmap

Status: Draft

This roadmap describes the intended direction of Home AI Cluster.

It is not a release plan.

It is not a promise.

It is a way to keep the project aligned with its foundations while avoiding premature implementation.

The roadmap should remain small, readable, and easy to revise.

---

## Guiding milestone

The first meaningful proof of Home AI Cluster is:

> One endpoint. Two machines. One routed request.

This proves the core idea without pretending to solve the whole problem.

It shows that multiple personal machines can behave as one AI system.

---

## Phase 0 — Foundations

Goal:

Clarify the project before writing code.

Expected outcomes:

* founding questions;
* working answers;
* project foundations;
* project vision;
* RFC process;
* roadmap;
* non-goals;
* shared vocabulary.

Success means:

> The project can be explained clearly before it is implemented.

---

## Phase 1 — Single-machine orchestrator

Goal:

Create the smallest possible orchestrator on one machine.

The orchestrator should expose one API endpoint and route a request to a local runtime through a simple adapter.

Expected outcomes:

* one orchestrator process;
* one local runtime adapter;
* one chat request;
* one response;
* no distributed behavior yet.

This phase proves the shape of the system without adding network complexity.

---

## Phase 2 — Agent and node model

Goal:

Define what a node is.

A node should be represented by an explicit cluster-facing description,
including availability, supported capabilities, declared adapter names, and
basic health.

Expected outcomes:

* static local node announcement;
* node identity;
* node health;
* capability announcement;
* static in-memory node and adapter registries.

This phase starts by keeping the implementation single-process, local, static,
and non-distributed. It does not introduce an agent process, node discovery, or
a registration protocol yet.

This phase prepares the project to prove that machines can describe what they
can do.

---

## Phase 3 — Two machines

Goal:

Connect at least two machines.

The orchestrator should be able to see more than one node and route a request to one of them.

Expected outcomes:

* two running nodes;
* one orchestrator;
* one unified endpoint;
* one routed request;
* visible explanation of which node handled the request.

This is the first real proof of Home AI Cluster.

---

## Phase 4 — Capability-based routing

Goal:

Route requests based on capabilities rather than machine names, model names, or runtime names.

Expected outcomes:

* simple capability model;
* request constraints;
* node matching;
* fallback when a node is unavailable;
* basic explanation of routing decisions.

The cluster should ask:

> What does this request need?

not:

> Which machine should run this?

---

## Phase 5 — Runtime adapters

Goal:

Keep the core independent from specific AI engines.

Runtime-specific behavior should live behind adapters.

Expected outcomes:

* at least two runtime adapters;
* a minimal adapter interface;
* clear separation between core orchestration and runtime details.

The core should reason about capabilities, requests, constraints, results, health, and availability.

It should not be designed around one engine.

---

## Phase 6 — OpenAI-compatible access

Goal:

Allow existing tools to use Home AI Cluster without special integration.

Expected outcomes:

* OpenAI-compatible chat endpoint;
* simple configuration;
* local developer tools can point to the cluster instead of one machine.

The user should keep using familiar tools.

The cluster should decide where work runs.

---

## Phase 7 — Observability and trust

Goal:

Make automatic decisions understandable.

Expected outcomes:

* request history without prompt logging by default;
* routing explanation;
* node status;
* health view;
* failure visibility;
* clear privacy boundaries.

The system should not be magical.

It should be transparent.

---

## Phase 8 — Operable local cluster

Goal:

Make the existing static local cluster understandable and repeatable as an ordinary operator workflow.

Expected outcomes:

* one documented canonical operator workflow;
* static validation of configured cluster facts;
* one read-only operator preflight;
* one repeatable two-machine runbook;
* clear local-only and distributed-proof operation;
* recovery guidance;
* proof that the founding milestone can be reproduced from documented steps.

This phase should improve operation of the existing static architecture without introducing process supervision, remote process control, automatic discovery, containers, a dashboard, or a new configuration format.

Success means:

> One operator can reproduce the existing two-machine milestone without reconstructing the procedure from repository knowledge.

---

## Phase 9 — Repeatable static cluster declaration

Goal:

Make the verified ordinary static multi-node mode convenient to start repeatedly
without changing its static architecture.

Expected outcomes:

* one explicit local cluster declaration;
* one ordinary startup command;
* static validation before startup;
* no secret values in the retained declaration;
* no discovery, supervision, or remote process control;
* no automatic network observation while loading the declaration.

This phase should reduce repeated command-line reconstruction while preserving
operator ownership, explicit topology, local-first routing, and the accepted
narrow fallback.

The declaration format, location, precedence rules, validation behavior, and CLI
relationship are architectural decisions and must be defined by an accepted RFC
before implementation.

Success means:

> One operator can restart the same explicit static cluster without rebuilding
> its declaration by hand.

---

## Phase 10 — Multiple explicit static remote nodes

Goal:

Extend the verified static cluster shape beyond one explicitly declared remote
node while preserving explicit topology and operator control.

Expected outcomes:

* more than one remote node can be represented in one explicit static cluster declaration;
* all declared nodes remain statically validated before startup;
* routing continues to operate on capabilities rather than direct machine targeting;
* node attribution and routing explanation remain cluster-owned and understandable;
* no discovery, supervision, remote process control, or automatic topology mutation;
* no secrets or runtime credentials in the retained declaration;
* one repeatable real multi-machine operator proof.

This phase should test whether the accepted architecture scales from one local
plus one remote node to a small explicitly declared home cluster without turning
Home AI Cluster into a scheduler, service manager, or dynamic discovery system.

The declaration structure, supported node count, ordering semantics, duplicate
handling, validation rules, candidate selection, failure behavior, fallback
boundaries, CLI compatibility, and migration from RFC-0039 are architectural
decisions and must be defined by an accepted RFC before implementation.

Success means:

> One operator can declare and reproduce a small static cluster with multiple
> remote nodes while the user still addresses one capability-centered endpoint.

---

## Phase 11 — Explicit static cluster status

Goal:

Let an operator explicitly inspect the current runtime and network status of the
small declared static cluster before sending an ordinary request.

Expected outcomes:

* one read-only, operator-invoked cluster status operation;
* a clear distinction between static declaration coherence and observed runtime
  or network status;
* status for the fixed local node and each explicitly declared remote node;
* bounded execution with understandable, privacy-safe results;
* no prompt or generated-response logging;
* no background polling, discovery, supervision, remote process control, or
  automatic topology mutation;
* no routing, lifecycle, or declaration changes caused by status inspection.

This phase should reduce manual use of unrelated network and process tools while
keeping observation explicit, finite, and operator-owned. It should not turn
Home AI Cluster into a monitoring service, health-aware scheduler, or dynamic
cluster manager.

The observation target, status vocabulary, remote protocol, timeout behavior,
sequential or parallel execution, privacy boundary, CLI or endpoint shape, and
relationship to existing local health and static preflight behavior are
architectural decisions and must be defined by an accepted RFC before
implementation.

Success means:

> One operator can explicitly inspect the declared static cluster and understand
> which observations are static facts and which come from a bounded live check.

---

## Phase 12 — Heterogeneous runtime cluster proof

Goal:

Demonstrate that the ordinary static cluster can operate across nodes using
different runtime engines without changing the cluster-facing architecture.

Expected outcomes:

* at least two nodes in one explicitly declared static cluster use different
  runtime engines;
* one ordinary capability-centered request succeeds through the heterogeneous
  cluster;
* cluster-facing request, result, routing, attribution, and status concepts
  remain engine-independent;
* runtime-specific behavior remains confined to runtime adapters on the
  executing nodes;
* no runtime name, adapter name, or model name becomes a request-level routing
  selector;
* one retained privacy-safe real operator proof;
* no discovery, automatic runtime selection, model inventory, runtime lifecycle
  management, or new generic adapter abstraction.

This phase should connect the already-proven second runtime adapter boundary with
the already-proven ordinary static multi-node cluster. It should test whether
different runtime engines can participate in one cluster without making engine
identity part of the cluster-facing domain.

The concrete topology, runtime placement, proof path, required wiring changes,
compatibility expectations, and whether any architecture change is needed must
be investigated before implementation. Any new architectural decision requires
an accepted RFC.

A two-machine proof is sufficient if it exercises two different runtime engines.
A larger topology must not be required unless investigation shows that it is
necessary.

Success means:

> One ordinary request can execute through a statically declared cluster whose
> nodes use different runtime engines without changing the cluster-facing
> architecture.

---

## Phase 13 — Explicit local runtime composition

Goal:

Allow an operator to run an ordinary Home AI Cluster node with one explicitly
chosen supported local runtime-adapter composition, while keeping runtime
identity outside the cluster-facing request, routing, declaration, attribution,
and status domains.

Expected outcomes:

* one ordinary node startup path can use an explicitly configured supported
  local runtime adapter;
* the existing Ollama-backed ordinary behavior remains available and compatible;
* another already-supported runtime adapter can participate without a
  proof-specific application launcher;
* local runtime configuration remains operator-owned, explicit, static, and
  understandable;
* the node continues to announce capabilities and adapter-backed availability
  through existing cluster-facing concepts;
* remote declarations and ordinary requests contain no runtime, adapter, model,
  or node selector;
* no automatic runtime selection, discovery, model inventory, lifecycle
  management, or generic plugin system is introduced; and
* one retained real operator proof demonstrates ordinary heterogeneous node
  operation.

Local node composition is an operator-owned startup concern. Cluster-facing
behavior remains capability-centered and engine-independent; runtime choice is
not a request-level or routing-level feature, and the cluster does not
automatically choose among runtimes.

Configuration ownership and location, supported configuration shape, startup
command relationship, default and compatibility behavior, adapter construction
and validation, treatment of runtime-specific values such as base URLs and
model identifiers, the relationship to existing ordinary and proof-scoped
application composition, privacy boundaries, failure behavior, and any
migration or deprecation are architectural decisions. They require
investigation and an accepted RFC before implementation.

This phase does not add request-level runtime selection; adapter or model
selectors in ordinary requests; runtime identity in remote cluster declarations;
automatic runtime selection; engine-aware routing; model discovery or inventory;
runtime installation or downloads; runtime supervision, restart, or repair;
dynamic plugins; environment-variable magic as an assumed design;
database-backed configuration; Docker or Kubernetes; or dashboard work.

Success means:

> One operator can start an ordinary node with an explicitly chosen supported
> local runtime composition while the cluster continues to reason only about
> capabilities, availability, requests, results, and node attribution.

---

## Phase 14 — Explicit static-cluster local composition

Status: Complete

Phase 14 closed the ordinary static-cluster local-composition asymmetry through
accepted RFC-0043. The existing `home-ai-cluster-static-cluster` command now
constructs exactly one local composition with the closed choices `ollama` and
`llama-server`; no-option startup remains Ollama-backed and compatible.

Runtime validation and composition construction occur before endpoint binding
without a network probe. Remote declarations remain topology-only, and requests,
routing, fallback, status, and declared-node attribution remain
capability-centered and unchanged. One retained privacy-safe ordinary operator
proof covers explicit local llama-server, default-Ollama remote fallback, and
exhausted availability normalization.

No generic runtime architecture, retained configuration, discovery, inventory,
lifecycle management, scheduling, Docker, Kubernetes, dashboard, or runtime
fields in cluster-facing declarations or requests was introduced.

See [the Phase 14 closeout](docs/phase-14-closeout.md) and
[the retained proof](docs/phase-14-static-cluster-local-composition-proof.md).

---

## Phase 15 — Explicit static-cluster status composition

Status: Complete

Phase 15 closed the remaining operator asymmetry between explicit static-cluster
startup and finite static-cluster status inspection through accepted RFC-0044.
The existing `home-ai-cluster-status` command now accepts the same closed local
runtime composition choices, `ollama` and `llama-server`; no-option inspection
remains Ollama-backed and compatible.

The command validates the topology-only declaration before conditional runtime
validation and constructs exactly one existing `LocalAppComposition` before any
remote observation. Its fixed local node is inspected through that composition,
while declared remotes remain sequentially observed through the normalized Home
AI Cluster status protocol in declaration order.

The compact status result remains engine-independent and exposes no runtime,
adapter, model, URL, executable, path, or private machine identity. One retained
privacy-safe operator proof covers explicit llama-server availability,
unavailability after only that runtime stopped, and the no-option Ollama
compatibility path.

No runtime-aware routing, fallback, discovery, inventory, scheduling,
supervision, lifecycle management, monitoring, persistence, generic factory,
plugin system, database, dashboard, Docker, or Kubernetes behavior was
introduced.

See [the Phase 15 closeout](docs/phase-15-closeout.md) and
[the retained proof](docs/phase-15-static-cluster-status-composition-proof.md).

---

## Phase 16 — Ordinary operator request access

Status: Complete

Phase 16 fulfilled its original objective:

> One operator can send one ordinary capability-centered request without manually
> constructing HTTP transport details.

The installed `home-ai-cluster-chat` command accepts one required `--message`
value and sends one request to the already running ordinary process through the
fixed native loopback `/v1/chat` boundary. It constructs the fixed `chat`
capability, returns one complete normalized `ClusterResult`, and uses stable
privacy-safe failures.

The same client invocation works with local-only and explicit static-cluster
processes. The client adds no topology, routing, runtime, node, model,
declaration, retry, fallback, history, configuration, startup, or supervision
behavior; those concerns remain process-owned.

The retained proof used one physical machine and the Ollama runtime family. Its
static-cluster request selected `local`; it did not demonstrate remote execution
or real network transport. Remote execution was not a Phase 16 completion
criterion.

See [the investigation](docs/phase-16-ordinary-operator-request-access-investigation.md),
[RFC-0045](RFC/RFC-0045-one-shot-ordinary-request-command.md),
[the proof runbook](docs/phase-16-ordinary-request-access-proof-runbook.md),
[the retained proof](docs/phase-16-ordinary-request-access-proof.md), and
[the Phase 16 closeout](docs/phase-16-closeout.md).

---

## Phase 17 — Human-readable operator inspection output

Status: Complete

Accepted [RFC-0048](RFC/RFC-0048-human-readable-inspection-output.md) changed
exactly the finite `home-ai-cluster-preflight`, `home-ai-cluster-health`, and
`home-ai-cluster-status` command surfaces. Their ordinary default output is
human-readable plain text; explicit `--json` preserves the former compact
machine-readable representation byte-for-byte. Output selection is explicit and
never TTY-dependent.

Command-specific formatting occurs only at the CLI edge after one completed
result exists. Result fields, ordering, vocabularies, observation semantics,
stream allocation, and exit behavior remain unchanged. Health continues to keep
declared state separate from adapter observations. Status continues to keep the
fixed local node first and remotes in declaration order. Normalized unavailable
and observation-failure states remain result data rather than whole-command
failures.

One retained privacy-safe proof passed. Its live evidence covered supported
ordinary command states. Automated CLI tests covered the completed
incoherent-preflight result because supported ordinary inputs cannot construct
that state without changing accepted wiring; no production behavior was changed
merely to create proof evidence.

Success means:

> One operator can understand ordinary preflight, health, and status results
> directly in a terminal while one explicit stable machine-readable
> representation remains available.

See [the investigation](docs/human-readable-operator-output-investigation.md),
[RFC-0048](RFC/RFC-0048-human-readable-inspection-output.md),
[the proof runbook](docs/phase-17-human-readable-inspection-output-proof.md),
[the retained proof result](docs/phase-17-human-readable-inspection-output-proof-result.md),
and [the Phase 17 closeout](docs/phase-17-closeout.md).

---

## Standalone post-roadmap integration proof

Status: Complete

This work was deliberately not classified as a formal roadmap phase. It required
no new capability or architectural contract, and composed the existing accepted
Phase 12 remote-execution and Phase 16 one-shot-client surfaces. One unchanged
ordinary client invocation crossed a real trusted-LAN machine boundary after
accepted caller-local pre-request fallback, reached an ordinary receiver, and
returned a complete normalized result attributed to the declared remote node.

This standalone proof did not itself create, reopen, extend, or count as Phase
17. It remains separately classified; the later Phase 17 work was independent
presentation work.

This closes the retained evidence gap noted above: the earlier Phase 16
static-cluster proof selected `local` on one physical machine and did not
demonstrate real network transport. It does not change Phase 16 completion
criteria or reopen Phase 16.

See [the investigation](docs/phase-17-end-to-end-ordinary-remote-request-investigation.md),
[the runbook](docs/end-to-end-ordinary-remote-request-proof-runbook.md), and
[the retained proof](docs/end-to-end-ordinary-remote-request-proof.md).

The proof does not introduce or demonstrate discovery, scheduling, retries,
supervision, authentication, encryption, internet-safe operation, automatic
lifecycle, or production readiness.

---

## Standalone post-roadmap Aider static-cluster integration proof

Status: Complete

This work was deliberately not classified as a formal roadmap phase. It
introduced no new architectural contract and composed the accepted RFC-0031
loopback compatibility edge with the accepted explicit static-cluster path.

One bounded Aider 0.86.2 submission reached the caller-local compatibility
endpoint while the caller-local runtime was unavailable before the request. It
completed through one declared real remote receiver. The final internal result
was attributed to the caller-owned declared remote node, while the RFC-0031
response remained topology-blind. Exactly one accepted request and no retry
were observed. The retained evidence is privacy-safe.

See [the retained proof](docs/aider-static-cluster-proof.md) and
[the runbook](docs/aider-static-cluster-proof-runbook.md).

This proof does not establish general Aider support, production readiness,
discovery, scheduling, authentication, encryption, retries, supervision, or
internet-safe operation. It does not reopen or change any formal roadmap phase.

---

## Standalone post-roadmap one-shot chat output refinement

Status: Complete

This work was deliberately not classified as a formal roadmap phase. It
introduced no request, transport, routing, runtime, topology, fallback,
lifecycle, persistence, or supervision contract. Accepted
[RFC-0049](RFC/RFC-0049-one-shot-chat-output-modes.md) changed only successful
presentation at the `home-ai-cluster-chat` CLI edge: no-option success presents
generated content directly; `-v`/`--verbose` presents content plus truthful
cluster-owned execution attribution; and `--json` preserves the historical
compact complete `ClusterResult` representation. Selection is explicit and not
TTY-dependent; invalid verbose/JSON combinations fail locally before HTTP.

Existing RFC-0045 request, validation, failure, privacy, and process-ownership
boundaries remain unchanged. The retained privacy-safe proof covers both
ordinary local-only and ordinary explicit static-cluster processes. Its
static-cluster live evidence followed accepted local-first routing and does not
claim remote execution.

See [the investigation](docs/one-shot-chat-output-modes-investigation.md),
[RFC-0049](RFC/RFC-0049-one-shot-chat-output-modes.md), and [the retained
proof](docs/rfc-0049-one-shot-chat-output-modes-proof.md).

This work does not add or demonstrate sessions, streaming, standard-input or
file input, tools, direct node or model selection, discovery, scheduling,
supervision, topology mutation, persistence, history, TTY-dependent behavior,
a generic output framework, a dashboard, Docker, or Kubernetes.

---

## Later possibilities

These ideas may become useful later, but they are not required for the first proof:

* dashboard;
* automatic node discovery;
* automatic model discovery;
* model download helpers;
* scheduling policies;
* multi-model workflows;
* embeddings;
* vision;
* tool calling;
* local web UI;
* plugins;
* cluster-aware developer tools;
* optional cloud nodes;
* more advanced distributed inference experiments.

These ideas belong later unless they directly help prove the core abstraction.

---

## Roadmap rule

Every phase must preserve the core idea:

> Many machines. One AI.

If a phase does not make that idea clearer, simpler, or more useful, it should be postponed.
