# Post-Roadmap Direction Investigation

## Status and authority

Investigation only. This document establishes no accepted architecture or
behavior, creates no Phase 18, amends neither the roadmap nor an RFC, and
authorizes no implementation. It evaluates the current repository state after
Phases 0 through 17 and retained standalone proofs; it does not select a future
feature merely because additional work is possible.

## Current proven system

The current ordinary system is a capability-centered `chat` service. An
operator starts a local-only or explicitly static-cluster process; one native
loopback endpoint accepts a normalized request, and the running process owns
routing, execution, failures, and result validation. The installed one-shot
client is topology-blind. It sends one request to its caller-local endpoint and
does not select a node, runtime, adapter, model, topology, or fallback.

Implemented and accepted behavior includes:

- explicit static declarations with multiple ordered remote nodes, a local-first
  candidate, and bounded pre-execution fallback;
- two supported local runtime compositions, while runtime details remain behind
  adapters and outside requests and remote declarations;
- finite preflight, local-health, and static-status inspection, with explicit
  human-readable and stable JSON representations;
- truthful caller-owned node attribution and a separate bounded routing account;
- an opt-in, bounded local request-history facility that omits prompt and
  response content; and
- separate native and narrow loopback OpenAI-compatible access surfaces.

Retained evidence also establishes, rather than merely anticipates, a real
ordinary trusted-LAN remote request through the native one-shot client and a
bounded Aider request through the static-cluster compatibility composition.
The latter is evidence for one configured, non-streaming compatibility workflow,
not broad Aider support or a general API claim. RFC-0049's later one-shot
refinement changes successful CLI presentation only: default content, explicit
verbose attribution, and exact `--json` compatibility all leave request and
process boundaries unchanged.

The system remains deliberately static and operator-owned. It does not discover
nodes, supervise processes, change topology, schedule based on resources,
persist general cluster state, expose ordinary endpoints to the internet, or
manage runtimes, models, or credentials. Declarations describe topology only;
runtime lifecycle, trusted-LAN exposure, and external-tool configuration remain
operator responsibilities.

## What is already complete

The following should not be reopened simply because a larger product could be
imagined:

- the founding two-machine routed-request proof and static multi-node operation;
- heterogeneous runtime participation and explicit local runtime composition;
- finite operator preflight, health, and status inspection;
- ordinary one-shot native request access and its safe failure boundary;
- human-readable operator output with stable JSON alternatives;
- retained real ordinary remote-request evidence;
- retained Aider static-cluster compatibility evidence;
- the one-shot chat output refinement; and
- the stdin investigation, which selected no change pending a concrete operator
  scenario.

The older post-roadmap direction and real-tool investigations correctly treated
compatibility-over-static-cluster composition as an architectural gap. RFC-0046,
RFC-0047, the current compatibility command and its focused tests, and the
retained Aider static-cluster proof subsequently closed that gap. Repeating the
earlier gap as a current need would ignore repository evidence.

## Evidence-backed remaining friction

| Classification | Current evidence | Assessment |
| --- | --- | --- |
| Observed operator friction | RFC-0049 records that raw JSON obscured an ordinary one-shot answer; it is now addressed by the accepted output modes and retained proof. | Complete; do not reopen. |
| Documented accepted limitation | The operator prepares runtimes, trusted-LAN exposure, declarations, process startup/shutdown, and external-tool settings manually. The canonical workflow and proof runbooks make this explicit. | A limitation by design, not retained evidence that automation is needed. |
| First-use/onboarding burden | README and workflow guidance require a technical user to install Python tooling and an operator-managed runtime before using existing commands. | Plausible documentation concern, but no clean-environment failure or retained operator report identifies a specific missing step. |
| Missing proof evidence | No retained evidence establishes every future tool, capability, deployment environment, or runtime. | Absence is not a requirement; the bounded native and Aider proofs already establish their stated claims. |
| Architectural gap | Discovery, stronger network trust, scheduling, additional capabilities, and lifecycle automation are absent. | Deliberate exclusions, not defects demonstrated by the first-user evidence. |
| Speculative ideas | Dashboard, generic plug-ins, broad OpenAI compatibility, model inventory, downloads, and persistent cluster management. | No supporting problem evidence; reject for now. |

The smallest point at which the stated first user still needs substantial
repository knowledge is preparing and operating the environment: selecting and
installing an external runtime, deciding trusted-LAN policy, creating an
explicit declaration, and following the documented multi-process workflow.
That is a real technical burden, but the evidence does not yet distinguish a
missing explanation from a need for an installer, supervisor, generated
configuration, or other new authority. The project should not guess.

## Candidate directions

| Direction | Concrete problem and evidence | Impact and classification |
| --- | --- | --- |
| 1. Maintain the proven system | No retained unmet first-user workflow remains after the native remote and Aider proofs. | No compatibility or privacy impact; no RFC; appropriate now. |
| 2. Installation/first-use onboarding | Existing setup remains manual and technical, but README/workflow evidence does not identify a failed or ambiguous step. | Documentation-only improvement could be small and need no RFC; an installer, runtime/model management, or generated configuration would be architectural and need an RFC. Investigate only after a concrete onboarding report. |
| 3. Startup/lifecycle ergonomics | Operators manually start and stop runtimes and processes; this is explicit in workflows. No retained repeated lifecycle pain exists. | A checklist is documentation; any start/stop, restart, polling, repair, or supervision changes lifecycle authority and needs an RFC. Later possibility. |
| 4. Another bounded real-tool proof | The Aider static-cluster proof already establishes one bounded external-tool workflow. | Another tool would need a distinct demonstrated user problem, not proof repetition. Likely an investigation or standalone proof only if unchanged accepted surfaces compose; otherwise RFC first. |
| 5. Capability beyond `chat` | No named first-user need, normalized contract, or supported adapter intersection identifies a next capability. | Changes capabilities, request/result semantics, adapters, privacy inputs, and routing; RFC required. Later possibility, not a phase now. |
| 6. Dynamic discovery | No evidence that explicit static topology prevents the bounded first-user workflow. | Adds topology, trust, network, and lifecycle authority; RFC required. Reject for now. |
| 7. Stronger trusted-LAN security/authentication | Current proofs deliberately retain operator-owned trusted-LAN boundaries and loopback compatibility access. No concrete threat model is recorded here. | Changes network trust and security authority; requires a dedicated security investigation and RFC. Do not bundle it into another improvement. |
| 8. Scheduling/resource-aware routing | Existing local-first ordered selection and narrow fallback are accepted; no workload evidence identifies a scheduling problem. | Changes routing and possibly observability/persistence; RFC required. Reject for now. |
| 9. Dashboard/local web UI | Finite CLI inspection and documented workflows already cover the bounded operator surface. | Adds an interaction surface and likely state/maintenance burden; no evidence of need. Reject for now. |
| 10. Packaging, releases, or versioned distribution | The repository has package metadata and `uv`-based development guidance, but no retained distribution failure or release-user requirement. | A small packaging correction could be maintenance; a release channel or installer carries compatibility/support obligations and needs scoped evidence. Later possibility. |

## Architecture boundary and classification test

Any direction that grants the project authority over topology (discovery),
lifecycle (supervision), network trust (authentication or LAN policy),
configuration (generation or precedence), capabilities (new request/result
meaning), routing (scheduling), persistence (general state), runtime selection,
or operator interaction (a dashboard) is architectural. It must be
investigation-first and RFC-before-implementation.

The current candidate classifications are therefore:

- no new proof is missing for the founding native remote or bounded Aider
  workflow;
- onboarding and lifecycle checklists could be documentation gaps only after a
  concrete workflow identifies one;
- one-shot stdin is a bounded CLI refinement in theory, but the dedicated
  investigation found no selected scenario;
- capabilities, discovery, security, scheduling, dashboards, configuration,
  and distribution systems would be new architectural capabilities or durable
  support contracts; and
- a roadmap phase is not a reward for continued activity. None of the evidence
  establishes a formal Phase 18 problem.

## Recommendation

**No repository change for now.** The next action should occur only when one
privacy-safe report from the stated technical first user identifies a concrete
unmet workflow: for example, the exact existing onboarding step that cannot be
completed, a repeated manual lifecycle action, an external tool that cannot use
the bounded accepted surface, or a named capability need.

Current evidence justifies restraint: the previously identified ordinary-answer,
real remote-request, static compatibility, and stdin questions have either been
completed or deliberately deferred. A new generic investigation, installer,
workflow rewrite, proof repetition, or architecture proposal would not resolve
a demonstrated problem. The smaller alternative—using the documented current
workflow—is sufficient until such a report exists.

No RFC is needed for this conclusion, and it should not become Phase 18. The
stopping condition is immediate: retain no new project work unless the future
report is concrete enough to classify as a missing proof, documentation gap,
bounded refinement, or architectural question. If it is architectural, the
next bounded step is an investigation or RFC, never implementation by inference.

## Boundaries retained

This investigation does not bundle or authorize discovery, scheduling, process
supervision, remote process control, automatic topology mutation, internet
exposure, generic authentication, databases, dashboards, Docker, Kubernetes,
generic plug-in systems, automatic model inventory or downloads, sessions,
streaming, tools, multimodal behavior, prompt libraries, or generic
configuration frameworks.

## Files inspected

- Governing documents: `VISION.md`, `FOUNDATIONS.md`, `PRINCIPLES.md`,
  `NON_GOALS.md`, `ROADMAP.md`, `QUESTIONS.md`, `CONTRIBUTING.md`, `AGENTS.md`,
  and `RFC/README.md`.
- Relevant accepted contracts: RFC-0023, RFC-0028, RFC-0030 through RFC-0049,
  especially the static topology, composition, compatibility, observation,
  operator-output, and one-shot command RFCs.
- Retained evidence: Phase 14–17 investigations, proofs, and closeouts; the
  end-to-end ordinary remote-request proof; the Aider static-cluster proof and
  runbook; post-roadmap and real-tool investigations; RFC-0049 proof; and the
  stdin investigation.
- Current operator and implementation seams: `README.md`, `pyproject.toml`,
  `chat_command.py`, `static_cluster.py`, `local_runtime.py`,
  `openai_compatibility.py`, `status_command.py`, `static_preflight.py`,
  `local_health_snapshot.py`, `actual_request_explanation.py`,
  `request_history.py`, and their focused tests.
