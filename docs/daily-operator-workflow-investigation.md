# Daily Operator Workflow Investigation

Status: Investigation

This document investigates an operator workflow problem. It is not a proposal,
accepted design, implementation plan, or roadmap change.

## 1. Context

Formal roadmap work is complete through Phase 16. The ordinary native command
and the static-cluster compatibility path have each crossed a real trusted-LAN
boundary, and the bounded Aider static-cluster proof succeeded. Those records
demonstrate the architecture; they do not establish general Aider support or
production readiness.

Repeated ordinary operation nevertheless still asks an operator to reconstruct
substantial parts of proof runbooks: which machine prepares which runtime,
which inspection answers which question, which foreground process to start,
which fixed endpoint to use, and what to stop afterward.

## 2. Investigation question

> How can one operator start, inspect, use, and stop an ordinary Home AI
> Cluster role repeatedly without reconstructing the proof runbooks?

“One command starts the whole cluster” is not an assumed goal. A more realistic
candidate direction to investigate is: on each machine, one explicit and
repeatable command starts its ordinary role. That is a hypothesis, not a
decision.

## 3. Current operator workflow inventory

### Receiving machine

- Prepare the repository and dependencies with `uv sync`.
- Prepare, start, and verify the external local runtime and its required local
  model through that runtime's own procedure.
- Run `home-ai-cluster-preflight` for static declaration coherence and
  `home-ai-cluster-health` for a local runtime observation where applicable.
- Start the ordinary receiving application explicitly, for example
  `uv run home-ai-cluster-local --host 0.0.0.0 --port 8000` or the documented
  ordinary Uvicorn form. The default ordinary bind is loopback; trusted-LAN
  exposure is an explicit operator choice.
- Know the selected bind address and port, constrain any firewall allowance to
  the trusted LAN, and remove that allowance after use.
- Interrupt the receiving application normally and stop the external runtime
  separately only if the operator chooses to do so.

### Calling machine

- Prepare the repository and dependencies with `uv sync`; optionally prepare a
  local runtime when the local-first candidate is intended to be usable.
- Create and retain an operator-owned static-cluster declaration containing
  only declared remote node identities and transport URLs.
- Validate it with `home-ai-cluster-preflight --declaration <path>` and inspect
  it with `home-ai-cluster-status --declaration <path>`; these are distinct
  static and live-observation boundaries.
- Start `home-ai-cluster-static-cluster --declaration <path>` for native
  static-cluster operation. It binds the caller endpoint to loopback port
  `8000`. The separate compatibility command binds only loopback port `8001`.
- Use native chat directly or through the one-shot command. Configure Aider
  only as a separate, temporary client-side concern when using the bounded
  proven setup.
- Interrupt the calling process normally, then remove temporary client
  configuration and declarations when they are no longer needed.

### Client usage

These are separate contracts, not one generic client contract:

- `home-ai-cluster-chat` sends one native request to an already-running caller
  loopback endpoint.
- Native `POST /v1/chat` is the cluster-native request boundary.
- Loopback compatibility `POST /v1/chat/completions` is the narrow RFC-0031
  compatibility boundary on the separate port.
- Aider is one bounded proven client configuration, not general Aider support
  and not core configuration.

## 4. Ownership boundaries

| Lifecycle domain | Current ownership and boundary |
| --- | --- |
| External runtime lifecycle | Operator-owned, machine-local, and outside Home AI Cluster. Installation, model preparation, startup, repair, restart, supervision, and shutdown are retained external-runtime procedures. |
| Home AI Cluster process lifecycle | An operator explicitly starts each foreground application or finite command. The application owns resources it creates inside that process, such as its static-cluster HTTP client, but the repository has no lifecycle controller, detached-process state, remote lifecycle authority, or runtime ownership. |
| Client lifecycle and configuration | Operator- and client-owned. The one-shot native client is finite; direct native callers are independent; compatibility clients remain loopback clients. Aider settings, histories, and cleanup remain client-side and temporary. |

Static declarations are operator-owned retained configuration. They are
machine-local startup inputs, not runtime configuration, remote control, or a
source of remote lifecycle authority. A receiving machine continues to be
operated locally on that machine. Home AI Cluster owns only the process it
starts in the ordinary invocation; it must not infer authority over an external
runtime, another machine, or a process started independently by the operator.

## 5. Concrete friction inventory

| Friction | Classification |
| --- | --- |
| Remembering command sequences and the distinction between documented entry points and internal application wiring | Documentation discoverability |
| Remembering bind addresses, fixed ports, and which endpoint is loopback-only | Home AI Cluster process lifecycle |
| Starting a runtime, receiving application, caller application, and optional client in separate terminals | Runtime lifecycle |
| Finding, retaining, and safely recreating declaration paths | Retained operator configuration |
| Separating declaration coherence from local runtime health and static-cluster status | Inspection |
| Identifying which process owns an occupied port | Shutdown and recovery |
| Maintaining temporary Aider model settings, history suppression, and placeholder credentials | Client usage |
| Knowing whether a process was started by the current workflow or independently | Home AI Cluster process lifecycle |
| Repeating the same role-specific preparation on each machine | Documentation discoverability |
| Recovering after one part starts while another fails | Shutdown and recovery |
| Avoiding private addresses, paths, prompts, responses, and client values in shell history or retained evidence | Retained operator configuration |

None of these frictions by itself establishes that code is required.

## 6. Existing reusable seams

| Existing seam | Already solves | Deliberately does not solve |
| --- | --- | --- |
| Retained static-cluster declarations | Explicit, ordered remote topology as an operator startup input | Default locations, profiles, secrets, lifecycle, or remote authority |
| Declaration validation and static preflight | Declaration shape and static coherence before runtime or network work | Runtime availability, reachability, process detection, or startup |
| Local health snapshot | A one-time local adapter observation | Remote health, supervision, repair, or routing change |
| Explicit static-cluster status | Finite normalized local and declared-remote observation | Polling, monitoring, startup, shutdown, or persistence |
| `home-ai-cluster-chat` | One ordinary native request to a running loopback process | Starting, configuring, inspecting, or managing that process |
| Explicit receiver and local composition | One visible ordinary receiver composition and optional supported local runtime selection | Runtime installation, model management, or lifecycle control |
| Explicit static-cluster and compatibility composition | A caller-owned static topology and distinct loopback compatibility edge | Discovery, remote startup, service management, or general client integration |
| Console entry points and safe errors | Narrow installed command surfaces with privacy-safe errors | A unified daily role launcher or stop contract |
| Current workflow and retained runbooks | Accurate current commands, roles, and cleanup boundaries | A short repeatable daily workflow contract |

## 7. Options considered

### Option A — Documentation and stable shell commands

A shorter daily workflow, documented shell functions, or stable command
sequences is the smallest and most portable option. It keeps ownership visible,
but may merely relocate reconstruction into personal shell configuration rather
than create a repository contract.

### Option B — Retained operator configuration files

Retained local facts could plausibly include an already accepted declaration
path or role-local values. Explicit file selection preserves visibility; default
paths raise privacy, precedence, ownership, and portability questions. A new
file may either extend an existing declaration or create a new configuration
domain; this investigation does not select either and proposes no schema.

### Option C — Bounded local CLI commands that start one role

One explicit local command per role could hide internal application wiring while
keeping role selection visible. It would need to define process ownership,
foreground versus detached behavior, and startup-failure behavior. Any new
long-lived start command or changed startup contract requires an RFC. No command
name or semantics is selected here.

### Option D — Bounded local stop behavior

Foreground interruption already gives an operator a simple stop path. Stopping
only processes started by Home AI Cluster raises distinct questions about child
ownership, PID or retained identity, stale state, already-stopped processes,
crash recovery, and privacy-safe errors. External runtimes must remain
excluded. Stop semantics may be a separate architectural decision from start
semantics.

### Option E — Optional `systemd --user` integration

This could be an explicit Linux-only operator integration with OS-owned
supervision. It raises questions about whether the project documents, generates,
or avoids owning units, and about logs and restart policy. It must remain
optional; it cannot become a mandatory daemon or internal service manager.

### Option F — Explicit separate startup on every machine

Keeping every machine locally and explicitly started preserves the clearest
ownership and trusted-LAN boundaries. It may pair well with better local role
invocation, but does not itself remove command-discoverability friction.

### Option G — Documented status quo

The present workflow preserves explicit control, local-first behavior, and
minimal architecture. It remains acceptable if any automation creates
disproportionate lifecycle, state, or compatibility complexity.

## 8. Comparison criteria

The comparison uses operator simplicity, architectural impact, privacy impact,
local-first behavior, engine independence, explicitness, process-ownership
clarity, portability, failure and recovery complexity, retained state,
compatibility with the static architecture, reversibility, implementation size,
documentation burden, and whether an RFC would be required.

| Option | Simplicity and portability | Architectural and privacy impact | State, recovery, and RFC signal |
| --- | --- | --- | --- |
| A | High portability; limited convenience | Minimal; preserves explicitness | Little retained state; usually documentation-only |
| B | Can reduce repetition | Configuration ownership and privacy risks | Precedence/default paths likely need an RFC |
| C | Clear local roles; portability depends on contract | Changes process-facing surface | Startup, foreground, and ownership likely need an RFC |
| D | Potentially convenient but failure-prone | Risks lifecycle authority | PID/state/recovery semantics need an RFC |
| E | Useful only on supporting systems | OS-specific; must remain optional | Unit, logging, and restart policy need an RFC |
| F | Explicit and reversible | Strongest local-first ownership boundary | No new state; may combine with A |
| G | Lowest implementation size | No new impact | Documentation burden remains; no RFC required |

This comparison is qualitative: compatibility with the existing static
architecture, reversibility, implementation size, documentation burden,
process-ownership clarity, and failure complexity matter more than a false
numeric score.

## 9. Architectural decisions that may require RFCs

An RFC is required before implementation if Home AI Cluster would start a
long-lived process through a new command, start child processes, retain process
identity after the invoking shell exits, define stop behavior, retain PID or
lifecycle state, introduce a default configuration path or new configuration
shape, or define configuration precedence.

The same is true for foreground versus detached operation, optional service
manager integration, logging ownership, startup aggregation, partial-startup
rollback, already-running detection, fixed versus configurable bind/port
behavior, receiver exposure, or restart behavior. These alter lifecycle,
configuration, compatibility, or privacy boundaries.

By contrast, correcting links, making current commands easier to find, or
documenting a personal alias as non-contractual guidance can remain a small
documentation improvement when it adds no repository-owned behavior, default,
or promise.

## 10. Evidence needed before a proposal

Collect privacy-safe operator evidence before choosing an option:

- the exact command and terminal count for each current role;
- which values repeat, where they are stored, and which are sensitive;
- the most common partial-startup, port-conflict, and cleanup failures;
- whether foreground operation is sufficient and whether detached operation is
  genuinely needed;
- whether child-process stopping is necessary;
- whether `systemd --user` materially reduces work for the intended operators;
- whether one accepted configuration domain can cover retained facts without
  creating precedence rules; and
- whether the workflow is Linux-only or must work across platforms.

Evidence must not retain real private addresses, machine names, usernames,
paths, prompts, responses, or client secrets.

## 11. Assessment of a possible Phase 17

A Phase 17 appears provisionally justified because the architecture proofs are
complete while recurring ordinary operation still lacks a bounded daily-role
workflow. This is not a roadmap decision.

- Provisional name: **Daily operator workflow**.
- Provisional question: how can an operator repeat one local role without
  reconstructing proof procedures?
- Possible goal: make the accepted ordinary role boundaries and repeatable local
  invocation discoverable without adding remote lifecycle authority.
- Exclusions: remote startup or shutdown, discovery, daemon or service-manager
  mandate, runtime lifecycle ownership, configuration schema expansion,
  dashboard, database, Docker, Kubernetes, engine-aware routing, and core
  Aider configuration.
- Success shape: an operator can prepare, inspect, start, use, interrupt, and
  clean up one local role with explicit ownership boundaries and no new hidden
  lifecycle state.

The evidence may instead justify smaller standalone investigations if start and
stop turn out to have materially different ownership requirements.

## 12. Recommended next decision step

Perform one small, privacy-safe evidence-gathering exercise that records the
current command count, terminal count, repeated values, and common recovery
cases for one receiving role and one calling role. Then decide whether improved
documentation is sufficient or whether to draft one narrowly scoped RFC.

Do not combine startup and stop semantics by assumption. Do not implement a
new lifecycle or configuration surface before an RFC accepts the relevant
architectural decision.
