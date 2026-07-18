# Post-Roadmap Next-Step Investigation

Status: Investigation only

Date: 2026-07-18

## Current post-roadmap state

The roadmap is complete through Phase 16. That completion remains closed.
Home AI Cluster has an ordinary local-only process, an ordinary explicit static
cluster process, capability-based local-first routing, bounded pre-execution
fallback, explicit static remote declarations, two runtime adapters, finite
operator status and preflight commands, and the native loopback
`POST /v1/chat` endpoint. `home-ai-cluster-chat` is an installed, one-shot,
topology-blind client of that native endpoint.

The retained post-roadmap proof establishes one real ordinary remote request:
an unchanged `home-ai-cluster-chat` invocation reached a receiver on a trusted
LAN through the caller-owned static-cluster path and returned a normalized
result attributed to the declared remote node. It is a standalone integration
proof, not a reopening of Phase 16 and not a formal Phase 17.

The repository also has a separate, deliberately narrow OpenAI-compatible
process. It is loopback-only, serves only `POST /v1/chat/completions`, accepts a
fixed endpoint identifier, and is not a general OpenAI-compatible API. Aider
has already been proved against that process using temporary client-side
configuration. That proof established compatibility with the accepted subset;
it did not establish ordinary static-cluster routing.

Current code supports this distinction. The compatibility command constructs
`create_app()` with its ordinary local wiring, whereas
`home-ai-cluster-static-cluster` constructs explicit static-cluster wiring. The
compatibility command has no declaration or composition-selection contract.
Consequently, an external OpenAI-compatible client cannot currently be shown to
benefit from ordinary remote routing merely by repeating the Aider proof.

## Decision question

> Now that the architectural core works in a real end-to-end ordinary remote
> request, which improvement would provide the most value to the first user
> without turning the prototype into a platform?

This investigation compares only these four directions:

1. integration with one real user tool;
2. reproducible installation and initial setup;
3. minimal operator lifecycle assistance; and
4. a second real capability.

It recommends a direction, not an architectural contract. Evidence below is
distinguished from inference: repository behavior and retained proofs are
evidence; value ranking is an inference for André to assess.

## Evaluation criteria

The first user is a technical individual who values local control, not an
infrastructure team. A candidate is stronger when it:

- makes the cluster useful from a familiar real workflow rather than merely
  adding machinery;
- reuses accepted request, routing, runtime-adapter, static-topology, and
  privacy boundaries;
- keeps the user addressing the cluster, never a selected machine;
- preserves local-first operation, no prompt or response logging by default,
  and operator ownership of runtimes and machines;
- remains engine-independent and capability-centered;
- introduces the least durable contract, automation, state, and support burden;
- can be proved with a small privacy-safe record; and
- has a clear stopping point if the value is not demonstrated.

## 1. Integration with one real user tool

### First-user problem and smallest useful proof

The first user needs to continue using one ordinary tool while Home AI Cluster,
not the tool or the user, decides where execution happens. The existing
one-shot client proves the operator-facing native path, but it is a Home AI
Cluster command rather than an independently useful user tool.

The smallest valuable proof would therefore be one existing, locally run user
tool sending one chat request to a caller-local cluster surface while an
unchanged ordinary static cluster makes the routing decision and the result
shows cluster-owned remote attribution. It must be one bounded workflow, not a
claim of broad compatibility.

The evidence does not yet identify a tool that can make that exact proof by
composition alone. Aider is a plausible tool category because it already fits
the accepted non-streaming, plain-text compatibility subset, but its retained
proof is loopback compatibility only. Repeating it against the existing
compatibility process would repeat completed compatibility evidence, not prove
cluster routing. A generic HTTP client or `home-ai-cluster-chat` can exercise
the native endpoint, but neither is the intended independent real-tool proof.

### Accepted surfaces and architectural assessment

Relevant accepted surfaces are:

- the native caller-loopback `/v1/chat` endpoint and `home-ai-cluster-chat`;
- ordinary static-cluster startup, explicit static declaration, capability
  routing, bounded fallback, remote transport, and result attribution;
- the dedicated narrow OpenAI-compatible process; and
- the Aider compatibility proof and its temporary client-side configuration.

The native endpoint and static-cluster path already compose, as the retained
two-machine ordinary-request proof demonstrates. The compatibility process and
the static-cluster path do not currently compose: its command creates the
ordinary local application and exposes no static declaration input. Allowing a
real OpenAI-compatible tool to reach an ordinary static cluster through that
process would therefore add a durable process-composition and operator-contract
decision. It is not a documentation-only configuration change and requires an
RFC before implementation.

### Boundaries, impact, and risks

Privacy remains favorable only if the proof uses a local tool, loopback access
at the tool edge, an operator-owned trusted-LAN static cluster where needed,
temporary non-secret client configuration, and redacted proof evidence. Tool
history, analytics, update checks, local caches, shell history, and source-file
access remain tool and operator concerns; they must not become Home AI Cluster
logging or persistence.

This direction can remain local-first when it neither requires an account nor
adds external services. It remains engine-independent when the tool sees only a
cluster access surface, while runtime selection stays inside existing process
composition. It remains capability-centered only if the integration has one
bounded `chat` purpose and does not expose node, adapter, runtime, model, or
machine selectors. The operator must continue to prepare, start, stop, and
protect runtimes and receiving processes; the integration must not infer
lifecycle ownership.

Repository impact before any implementation is one focused investigation. If
an RFC is later accepted, it would likely affect the compatibility process,
tests, operator workflow, and a proof record, but should not require a new
client SDK, plugin framework, model catalogue, or broad API. Principal risks
are making one tool's defaults define the compatibility edge, accepting fields
only to accommodate that tool, conflating client configuration with cluster
topology, and turning a narrow proof into a support promise.

It must explicitly avoid broad OpenAI compatibility, streaming, tools or
function calling, model discovery or aliases, request-level model/runtime/node
selection, LAN exposure of the compatibility process, real authentication,
client-side fallback, tool-specific code in the core, and a generic integration
framework. This direction provides direct user value if it proves a familiar
tool receives real cluster routing; until then, it is an evidence-seeking
investigation rather than infrastructure expansion.

## 2. Reproducible installation and initial setup

### First-user problem and smallest useful proof

The first user must currently prepare Python, `uv`, one or more external
runtimes, models, trusted-LAN exposure, and explicit declarations manually.
Reproducible setup could reduce onboarding friction. The smallest plausible
proof is a clean-machine, operator-followed setup record that reaches one
ordinary local request, then—only if needed—a separately documented static
cluster request, without automation beyond documented commands.

### Accepted surfaces and architectural assessment

The candidate could reuse `uv sync`, the README, canonical operator workflow,
preflight, health, status, ordinary local startup, static-cluster startup, and
the one-shot client. Clear documentation can be added without a new
architectural decision or RFC, provided it describes the existing process and
does not prescribe a new installation contract.

Packaging a runtime, installing models, writing declarations, selecting network
policy, or generating persistent configuration would go beyond documentation.
Those actions create ownership, compatibility, privacy, configuration, and
lifecycle questions. An RFC would be required before implementation if this
direction adds an enduring installer, configuration format, model-management
behavior, or service-installation behavior.

### Boundaries, impact, and risks

Documentation can preserve privacy by using placeholders and by warning that
commands, files, models, and runtime logs remain operator-owned. It remains
local-first when it does not download from or depend on a hosted control plane;
however, any installation path necessarily relies on the operator's chosen
runtime distribution and model source. It remains engine-independent only if it
describes supported compositions symmetrically and does not turn the default
runtime into project identity. It remains capability-centered if setup explains
how to make an existing capability available rather than selecting a machine
for each request.

The operator should continue to own runtime lifecycle, model acquisition,
trusted-LAN firewall policy, and declaration contents. A documentation proof
would affect operator guidance and perhaps a retained setup record, not code.
The principal risk is prematurely promising a universal or push-button install,
then accumulating platform, package-manager, hardware, model-source, and
security support obligations.

It must avoid an installer, model download or placement automation, generated
or persisted topology, service managers, Docker, Kubernetes, cloud accounts,
telemetry, and credentials. It offers real value, but presently mostly improves
entry friction after the user has already chosen a runtime and environment; it
does not itself demonstrate the distinctive cluster value.

## 3. Minimal operator lifecycle assistance

### First-user problem and smallest useful proof

An operator currently starts external runtimes and ordinary processes, runs
finite observations, manages trusted-LAN exposure, and cleans up manually.
The concrete problem would be repeated, demonstrated manual lifecycle pain.
No retained evidence shows that pain is currently the main reason the first
user cannot obtain value.

The smallest useful proof would be a manual, documented lifecycle checklist
using the existing workflow, not a helper that starts or stops anything. It can
measure where an operator actually struggles without claiming process control.

### Accepted surfaces and architectural assessment

The existing workflow, preflight, health, status, and separate startup commands
already provide explicit preparation and finite observation. A checklist or
proof using them needs no RFC. Any command that starts, stops, restarts,
supervises, repairs, discovers, polls, or owns a runtime or remote process
would change lifecycle authority and requires an RFC before implementation.

### Boundaries, impact, and risks

Manual guidance preserves privacy because it observes only current accepted
privacy-safe outputs. It stays local-first, engine-independent, and
capability-centered by leaving runtime details behind adapters and routing
unchanged. It also preserves explicit operator control: the operator remains
responsible for every process and network boundary.

A checklist would have a limited documentation impact. Automation would affect
commands, process boundaries, error semantics, tests, operator documentation,
and potentially configuration or persistence. The central scope risk is that a
small convenience wrapper becomes a service manager, monitor, supervisor,
discovery system, or hidden authority over remote machines.

It must avoid automatic lifecycle ownership, background polling, health-aware
routing, remote process control, repair, automatic discovery, persistent state,
Docker, Kubernetes, and a dashboard. Until repeated operator pain is observed,
this primarily expands infrastructure rather than proving new user value.

## 4. A second real capability

### First-user problem and smallest useful proof

A user may eventually need a cluster capability beyond `chat`, for example
embeddings, vision, or a distinct coding-oriented capability. No concrete
first-user need, normalized request semantics, supported runtime intersection,
or routing evidence identifies which one should be first.

The smallest useful proof would be one user-named capability with one
normalized request/result contract, one or more adapters that can truthfully
provide it, capability matching, and a privacy-safe real execution. That is
already an architectural increment, not a small post-roadmap composition.

### Accepted surfaces and architectural assessment

Existing node capabilities, routing candidates, adapter boundaries, local and
static composition, and result attribution are relevant. They do not define the
request and result contract, capability semantics, runtime-adapter obligations,
or tool access for another capability. A new enduring capability therefore
requires an RFC before implementation.

### Boundaries, impact, and risks

Privacy depends on the chosen input: images, documents, embeddings, files, and
tool context may be more sensitive than plain chat. Local-first remains
possible, but each new capability must establish its own local input and remote
transport boundaries. Engine independence requires a normalized capability that
does not leak one runtime's API into the core. Capability-centered design is the
main benefit, but only after a concrete, user-valued capability is defined.

The operator would still own models, runtimes, and networks; the project must
not infer downloads, placement, or lifecycle management. Repository impact is
substantial: models, routing and adapter tests, endpoint or command contract,
documentation, proofs, and potentially transport and result boundaries. The
principal risk is choosing a capability because it is technically interesting,
then importing file handling, large payload, model-selection, multimodal, or
provider-specific complexity before one ordinary chat workflow is useful.

It must avoid a capability taxonomy, generic plugin system, runtime-specific
core APIs, automatic model discovery or placement, broad multimodal API, and
new infrastructure. It could create genuine value later, but now it is more
likely to expand the platform than to validate the existing promise.

## Direct comparison

| Direction | First-user value now | Smallest credible next step | RFC before implementation? | Main risk |
| --- | --- | --- | --- | --- |
| One real user tool | Highest potential: familiar workflow plus cluster-owned routing. | Investigate one tool and the missing compatibility/static-composition boundary. | Yes, if it must make the compatibility process serve an ordinary static cluster. | Broadening the compatibility edge to fit a tool. |
| Reproducible setup | Moderate: lowers entry friction. | Clean-environment documentation proof of the current workflow. | No for documentation; yes for an installer, config, model, or service behavior. | Accidental platform-specific installer and lifecycle promises. |
| Lifecycle assistance | Low until repeated pain is evidenced. | Manual checklist and evidence of actual friction. | Yes for any process ownership or automation. | Becoming a supervisor or dynamic cluster manager. |
| Second capability | Potentially high, but ungrounded. | Identify one concrete user need before defining any proof. | Yes. | Premature request, adapter, and runtime-surface expansion. |

## Risks of choosing too much too soon

The core has just been proved in a real ordinary remote request. Treating that
evidence as a mandate for a platform would replace a clear static, operator-led
system with contracts that have not earned their complexity. In particular,
automatic setup or lifecycle behavior could obscure ownership; a broad
compatibility layer could let a third-party API define the project; and a second
capability could turn a simple chat proof into a premature general-purpose AI
surface.

The safer sequence is to establish one visible first-user workflow, preserve its
limits, and only then decide whether the observed friction is installation,
lifecycle, capability, or tool-contract related.

## Recommendation

Prioritize **one real-tool integration investigation**, with the explicit goal
of determining whether one ordinary external tool can use real cluster routing
without broadening the project into a general integration platform.

This is the strongest direction because the project promise is not merely that
a request can cross two machines; it is that the user can continue using a tool
while the cluster decides execution. The current post-roadmap proof establishes
the routing half. A real tool would make the first-user value visible.

The recommendation is not to repeat the completed Aider compatibility proof or
to expand the OpenAI-compatible endpoint automatically. The investigation must
first decide whether a carefully bounded tool and accepted surfaces can provide
new evidence. Current evidence suggests that a tool using the compatibility
edge to reach ordinary static-cluster routing needs a new composition contract,
so no implementation should be inferred.

## Smallest recommended follow-up

Create one documentation-only, tool-specific decision-framing investigation.
It should use Aider only as an evidence-backed reference point, compare it with
at most a small number of equally concrete local-tool candidates, and answer:

1. Does the tool need the narrow compatibility edge, or can it use an accepted
   native surface without a new client contract?
2. Can the desired ordinary static-cluster path be composed from accepted
   processes exactly as they exist?
3. If not, what is the minimum enduring composition question—for example,
   whether the dedicated compatibility process may select an existing ordinary
   static-cluster composition—without proposing its implementation?
4. Is the resulting user benefit worth an RFC and one bounded implementation
   later?

This follow-up needs **no RFC** because it is investigation only. It is not a
runbook or proof yet: current accepted surfaces do not establish an external
tool-to-ordinary-static-cluster composition. If the investigation confirms that
new composition is needed and worthwhile, an RFC must precede implementation.
If it instead finds a real tool that composes unchanged accepted surfaces, the
next step can be an investigation-specific runbook and a privacy-safe proof
only.

No formal Phase 17 is recommended. The work should remain a standalone
post-roadmap investigation unless André later decides that a broader roadmap
change is justified.

## Explicit non-recommendations

- Do not repeat the Aider loopback compatibility proof as if it established
  static-cluster routing.
- Do not automatically broaden OpenAI compatibility, add model discovery,
  aliases, streaming, tools, generation controls, or request-level selectors.
- Do not implement installation automation, model management, generated
  configuration, lifecycle helpers, supervision, discovery, scheduling, load
  balancing, Docker, Kubernetes, a dashboard, database, or plugin framework.
- Do not add a second capability before a concrete first-user workflow names
  the need and an RFC defines its contract.
- Do not reopen Phase 16 or create a formal Phase 17 merely to track this
  investigation.

## Open questions requiring André's decision

1. Is the intended first user primarily a developer using a coding assistant,
   or another user with a different ordinary local tool? This determines which
   tool is credible enough to investigate.
2. Is the value of a real-tool-to-remote-cluster proof sufficient to justify a
   future RFC for narrowly composing the compatibility edge with an existing
   ordinary static cluster, if investigation confirms that no unchanged surface
   can do it?
3. Should the project first collect a clean-environment setup proof instead,
   accepting that it improves onboarding but does not yet show a familiar tool
   benefiting from cluster routing?

## Evidence consulted

- Project foundations, principles, non-goals, roadmap, questions, contribution
  guidance, and accepted RFCs, especially RFC-0031, RFC-0038 through RFC-0045.
- Current README, documentation index, canonical operator workflow, current
  command entry points, and implementation wiring.
- Phase 6 Aider investigation and retained proof.
- Phase 16 investigation, runbook, retained proof, and closeout.
- Post-roadmap ordinary-request-input and end-to-end ordinary-remote-request
  investigations, runbook, and retained proof.

No private addresses, prompts, generated responses, usernames, machine names,
credentials, or local filesystem paths are retained here.
