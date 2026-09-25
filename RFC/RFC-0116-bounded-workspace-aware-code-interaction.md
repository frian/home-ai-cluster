# RFC-0116: Bounded Workspace-Aware Code Interaction

Status: Accepted

Date: 2026-09-10

Author: frian

## Summary

Home AI Cluster should provide one distinct, explicitly workspace-enabled,
foreground Code interaction.  It composes ordinary `capability=code` textual
inference with one directly constructed, process-local RFC-0114
`WorkspaceAuthority`, one closed model-response grammar, and a finite
action-and-continue loop.

The interaction begins with one operator instruction and fixed trusted inputs:
an existing workspace root, a non-empty subset of `{list, read, write}`, and a
hard budget of eight workspace actions.  The model may return either one final
textual answer or one requested workspace action.  HAC validates the closed
response, independently asks the already-granted local authority to perform
the action, then may provide a deterministic textual outcome in a subsequent
ordinary Code request.  The interaction ends after a final answer, malformed
response, terminal failure, or exhausted action budget.

This is a dedicated composition around ordinary Code inference.  It does not
make `code` an authority-bearing or tool-enabled cluster capability, and it
does not change RFC-0067, adapters, routing, `ClusterRequest`, `ClusterResult`,
remote envelopes, `/v1/chat`, or existing Code surfaces.

## Problem

RFC-0067 deliberately defines `code` as bounded textual generation,
transformation, and explanation.  RFC-0088 adds an ephemeral human/textual
conversation for no-message native Code, while RFC-0080 and RFC-0081 retain
one operator-selected target and one bounded transformation.  None supplies a
HAC-owned action-and-continue seam in which inference can work against a
bounded local workspace rather than only text supplied by a human.

RFC-0114 now supplies the required local authority: one fixed existing root,
one explicit operation grant, closed logical paths, and bounded `list`, `read`,
and existing-file `write` behavior.  RFC-0115 supplies a separate one-shot
process carrier for genuinely separate local integrations.  Neither decides
the smallest same-process interaction that may connect ordinary textual Code
inference to an already-granted RFC-0114 authority.

The project needs that narrow composition without changing ordinary Code,
creating a generic tool or agent framework, or transferring filesystem
authority to a selected local or remote inference node.

## Goals

- Define one explicitly workspace-enabled, HAC-owned Code interaction.
- Keep `capability=code` bounded textual inference under RFC-0067.
- Use exactly one ephemeral, process-local RFC-0114 authority held for one
  foreground interaction.
- Define an exact, closed final-or-single-workspace-action response grammar.
- Permit only sequential `list`, `read`, and `write` requests, with RFC-0114
  retaining all filesystem and grant enforcement.
- Keep the interaction finite with a fixed maximum of eight action requests.
- Preserve existing Code routing while making any resulting workspace-data
  disclosure to an eligible remote Code node explicit.
- Keep outcome reinjection inside existing ordered textual Code messages.

## Non-goals

This RFC does not change ordinary `code` or RFC-0067; give adapters filesystem
methods or authority; add generic tools, function calling, tool IDs, call IDs,
parallel calls, registries, streaming, negotiation, an agent or
planner/executor framework, plugins, or MCP; or use RFC-0115 internally.

It does not authorize shell, subprocess, compiler, formatter, test, Git,
`hac_exec`, arbitrary-command, repository, filesystem-search, patch, diff, or
edit abstractions.  It does not add file creation beyond RFC-0114, directory
creation, delete, rename, move, append, or range operations.

It does not add retained workspace configuration, dynamic grants, policy,
ACLs, roles, credentials, sessions, persistence, background work, queues,
concurrent actions, parallel inference, transcript/history retention, a
dashboard/browser workspace UI, HTTP workspace transport, special remote
workspace protocol, remote filesystem authority, a database, Docker, or
Kubernetes.  It does not make workspace operations cluster capabilities or
change topology, routing, fallback, status, capability bindings, or receiver
advertisement.  It does not select a final human CLI spelling.

## Proposal

### Dedicated composition and preserved ordinary Code boundary

The project should add one new, distinct workspace-aware Code interaction.  It
is not ordinary `hac code`, existing interactive `hac code`, browser Code,
`/v1/chat`, or `code-file`.  Its exact command spelling is intentionally open.

The composition uses ordinary `capability=code` requests and their existing
textual request/result, adapter, routing, and remote-execution semantics.
It adds a caller-local interpretation layer around selected Code results:

```text
trusted composition inputs
  -> one local RFC-0114 WorkspaceAuthority
  -> ordinary Code inference
  -> closed final response, or one workspace request
  -> direct WorkspaceAuthority operation
  -> deterministic textual outcome in next ordinary Code request
```

`capability=code` remains bounded textual inference.  A normal Code request
outside this composition cannot cause filesystem action.  No adapter gains
filesystem methods or workspace authority, and no remote receiver receives a
`WorkspaceAuthority`.  The composition merely interprets a closed subset of
untrusted textual Code results as requests against separate, pre-existing
local authority.  It must not be described as `code` gaining tools.

Existing `hac code MESSAGE`, interactive `hac code`, browser Code,
`/v1/chat`, adapters, `ClusterRequest`, `ClusterResult`, and ordinary remote
envelopes remain semantically unchanged.

### Authority construction, locality, and lifecycle

Before the initial inference, trusted composition/operator input fixes all of:

- workspace enablement;
- one existing RFC-0114 workspace root;
- one non-empty subset of `{list, read, write}`; and
- the fixed workspace-action budget of eight.

The composition constructs and retains exactly one RFC-0114
`WorkspaceAuthority` directly.  Its root, grants, and action budget remain
fixed for the complete foreground interaction; the model cannot see a physical
root through the authority contract or modify any of them.  The authority is
local, process-local, ephemeral, non-retained, sequential, and ends with the
interaction.  Workspace roots and grants must not enter retained `hac config`.

RFC-0115 is not invoked internally: a same-process HAC-owned composition does
not need a subprocess JSON/I/O carrier to reach an authority it already owns.
RFC-0115 remains unchanged as the supported one-shot process boundary for a
genuinely separate local integration.  This RFC does not make that carrier
mandatory for other future workspace consumers.

### Trusted and untrusted data

The model may choose only whether its next response is final or a workspace
action; for an action, one of `list`, `read`, or `write`; one logical path; and
replacement `content` only for `write`.  Prompt text, workspace content, and
model output are untrusted data and cannot grant authority.

The model does not choose the workspace root, grant, routing, remote node,
runtime, model, executable, process, shell, network destination, action budget,
or any new authority.  RFC-0114 exclusively defines path syntax, root
confinement, redirection handling, file eligibility, operation bounds, text
handling, and publication semantics.  The composition must not duplicate,
loosen, or repair that policy.

### Closed model-response contract

Before its initial ordinary `capability=code` inference, the composition must
construct deterministic HAC-generated textual interaction instructions using
the existing ordered textual Code message representation.  The instructions
must tell inference that every response in this interaction is exactly one
closed `kind=final` JSON form or one closed `kind=workspace` JSON form using
only `list`, `read`, or `write`; that prose outside that JSON, Markdown fences,
and more than one action are invalid; and that HAC, not the model, owns the
authority and may refuse a requested workspace operation.

These instructions are interaction-specific HAC-generated control text, not a
new message role, generic prompt-template framework, or filesystem authority.
The model may ignore them, so validation remains fail-closed.  They need not
disclose the physical workspace root: the model operates on RFC-0114 logical
paths, while the actual root and grants remain trusted composition state
enforced independently by `WorkspaceAuthority`.  Whether the instructions
name the currently granted operations remains an implementation/product detail.

The interaction instructions count toward RFC-0067's existing 65,536-byte
aggregate Code request-content bound.  Before the initial inference, the
complete initial request—including the operator instruction and every
HAC-generated interaction instruction—must fit that bound.  If it cannot,
HAC terminates locally before routing or inference; it must not truncate either
the operator instruction or interaction contract, or raise RFC-0067's limit.
Every later inference participating in the interaction must receive sufficient
retained HAC-generated contract context to know the same closed grammar.  The
architecture does not require duplicating those instructions on every turn
when the complete existing textual interaction context already retains them.

Every Code result interpreted by this interaction must be exactly one JSON
document containing exactly one of the following closed top-level forms.  JSON
leading/trailing whitespace is permitted; Markdown fences, prose, a second
document, and arbitrary non-JSON text are not part of the contract.

A final response requires exactly `kind` and `content`:

```json
{"kind":"final","content":"..."}
```

`kind` is exactly `final`; `content` is a string.  No other member is allowed.

A `list` or `read` action requires exactly `kind`, `operation`, and `path`:

```json
{"kind":"workspace","operation":"read","path":"src/example.py"}
```

A `write` action requires exactly `kind`, `operation`, `path`, and `content`:

```json
{"kind":"workspace","operation":"write","path":"src/example.py","content":"..."}
```

For workspace actions, `kind` is exactly `workspace`; `operation` is exactly
one of RFC-0114's closed `list`, `read`, or `write` vocabulary; `path` is a
string; and `content` is required and a string only for `write`.  It is
forbidden for `list` and `read`.  Missing, unknown, or wrong-typed members
fail validation.

Duplicate decoded JSON member names are invalid before interpretation,
including escaped-equivalent names.  For example, `"kind"` and
`"k\\u0069nd"` are duplicates.  A malformed, ambiguous, or otherwise invalid
model response fails closed and terminates the interaction.  HAC neither
treats it as a final textual answer nor infers an action from natural-language
prose.

Before JSON parsing or semantic interpretation, the composition must measure
the complete `ClusterResult.content` UTF-8 byte length.  A result this
interaction intends to interpret is at most 8 MiB (`8 * 1024 * 1024` bytes),
whether it ultimately encodes `kind=final` or `kind=workspace`.  If it exceeds
that fixed interaction-only bound, HAC must not parse it, execute a workspace
action, truncate it, summarize it, retry automatically, or reinterpret it as
final text; it terminates with a truthful local interaction failure.

This bound applies only after ordinary Code result receipt and before this
composition's interpretation.  It does not change RFC-0067, ordinary `hac
code`, `ClusterResult`, adapters, remote envelopes, transports, runtimes, or
ordinary Code output limits.  It does not claim to bound memory already used
by an adapter or transport before `ClusterResult` reaches the composition.
After a valid final response is parsed, its `content` is presented through the
foreground interaction without creating a retained output surface.

This is one interaction-owned grammar, not a generic function-calling or tool
protocol.  It adds no tool names, generic parameters, IDs, parallel actions,
version negotiation, or extensible registry.

### Action execution and outcomes

For a valid workspace request selected while action budget remains, HAC must:

1. validate the closed interaction response;
2. consume one action-budget unit;
3. call the already-constructed local `WorkspaceAuthority` directly;
4. classify its outcome; and
5. if continuation remains possible, construct the next ordinary Code request
   with deterministic HAC-owned textual outcome context.

There are three distinct outcomes.

- **Success:** RFC-0114 completed the operation.  A `list` reinjection carries
  its bounded entries; a `read` reinjection carries its bounded text; a `write`
  records that replacement completed.
- **Refused:** the RFC-0114 workspace-authority call did not produce a
  successful operation result through its ordinary bounded failure/refusal
  surface.  This normal authority non-success is unambiguously distinct from
  success and may be reinjected so the model can request another
  already-authorized operation or finish.  It does not imply HAC can classify
  the exact underlying reason; no stable grant, path, host-I/O, or error-code
  taxonomy is introduced.
- **Internal interaction failure:** an unexpected composition/HAC failure is
  not a refusal.  HAC terminates and must not manufacture a successful or
  refused result.

HAC must not automatically retry a refusal, silently repair a model request,
or perform a different action after refusal.  A successful RFC-0114 write
remains committed if later context construction or inference fails; no rollback
or automatic retry is permitted.

### Deterministic textual outcome reinjection and existing Code bound

After success or refusal, HAC may issue another ordinary `capability=code`
request.  It must use the existing ordered plain-text message representation,
not a new cluster `tool` role, and must add deterministic HAC-generated
user-role textual context that unambiguously represents:

- the untrusted assistant action request;
- the HAC-owned outcome;
- whether the outcome was success or refusal; and
- returned list/read data where applicable.

Workspace content remains explicitly untrusted data in that context; it must
not be elevated into a system-style authority message.  Exact whitespace and
private helper structure are implementation details, provided provenance and
success/refusal cannot be ambiguous.

For every valid RFC-0114 textual result, arbitrary workspace content must not
forge, terminate, or become structurally indistinguishable from the HAC-owned
outcome metadata surrounding it.  The representation must preserve an
unambiguous distinction among the requested action, HAC-owned success/refusal
state, and returned untrusted data, including when that data deliberately
imitates HAC framing text.  An injective textual encoding is required, but its
exact escaping, quoting, length-delimiting, or equivalent mechanism remains an
implementation detail.  This is a structural provenance property, not a claim
to prevent prompt injection or control what inference believes about the data.

RFC-0067's 65,536-byte aggregate Code message-content bound remains unchanged.
The entire prospective subsequent message set must satisfy it before HAC makes
that request.  HAC must neither raise that limit, silently truncate a workspace
result, nor automatically summarize or prune it.  If a completed successful
`list` or `read` result cannot fit in the next complete Code request, HAC must
truthfully terminate with an interaction failure that continuation cannot fit
the accepted Code bound.  It must not claim that the workspace action failed.

### Finite action budget and foreground lifecycle

The initial proposed hard maximum is eight budget-consuming, dispatched
workspace action attempts per interaction.  Each valid workspace request
selected while budget remains consumes one unit before RFC-0114 execution,
whether the authority later succeeds or refuses; malformed model output
terminates immediately without consume-and-continue behavior.

At most nine ordinary Code inferences occur: one initial inference and at most
one after each of eight outcomes.  After the eighth outcome, one final Code
inference may still produce a final response.  If it instead produces another
otherwise-valid workspace request, HAC recognizes it as such but must not
dispatch it or attempt any RFC-0114 operation; the interaction terminates for
exhausted action budget.  The model cannot extend or change the budget.  No
token budget, scheduler, queue, background supervisor, or hidden autonomous
loop is added.

The first interaction is local, foreground, ephemeral, single-user, and
sequential.  It permits no concurrent workspace actions, parallel model
requests, session recovery, restart semantics, persistence, or human follow-up
turns.  It starts from one initial user coding instruction and exits after a
final textual result or terminal failure.

### Routing, remote inference, and disclosure

Each ordinary Code request in this composition retains existing RFC-0067 and
accepted HAC capability routing.  There is no workspace routing, local-only
override, new capability, static-topology declaration, receiver advertisement,
or fallback behavior.  An eligible `code` request may execute locally or on an
explicitly configured eligible remote HAC node according to existing rules.

The workspace authority always remains caller-local.  A remote selected Code
node receives only the ordinary textual Code message context.  It never
receives a `WorkspaceAuthority`, advertises no workspace grant, and cannot
directly list, read, or write the caller workspace.

Enabling this interaction explicitly authorizes its composition to include
bounded workspace outcomes in ordinary Code requests under the operator's
existing Code routing configuration.  If routing selects a configured remote
Code node, textual workspace data may be disclosed to it, including successful
`read` content, `list` names, and prior action/write context.  That is bounded
data disclosure to the existing selected execution node, not remote filesystem
authority.  This RFC adds no transport, credential, or remote-trust semantics.

### Compatibility and explainability

RFC-0080 and RFC-0081 remain unchanged: `code-file` retains one
operator-selected target, one bounded Code transformation, caller-owned
publication, and no model-selected path or filesystem operation.  This
interaction is intentionally different only because its model may choose a
logical path and operation within a separately pre-granted RFC-0114 namespace.

RFC-0088 remains unchanged: current no-message `hac code` is an ephemeral
textual human/model conversation, not a workspace interaction.  Browser Code
remains unchanged.  RFC-0096 is only precedent that HAC can own one closed
model decision, one bounded caller-owned action, and later inference without a
generic agent framework; its external-information semantics are not reused.

Foreground presentation must distinguish at least final answer; action
requested; action succeeded; action refused; malformed-model-response terminal
failure; model response exceeding the workspace-aware interaction response
bound; action-budget exhaustion; failure because continued Code context would
exceed RFC-0067's bound; and unexpected internal failure.  This adds no
retained history, status, or observability subsystem.  Exact terminal
formatting is an implementation detail.

## Security and privacy consequences

The model/action requester may be buggy, adversarial, prompt-injected, or
influenced by malicious workspace contents.  HAC independently enforces the
fixed root, fixed grants, RFC-0114 path and operation semantics, and the finite
action budget.  Workspace contents may influence later model output but cannot
alter authority.

This proposal does not claim prompt-injection prevention, sandboxing, or
protection from a malicious same-OS-user beyond RFC-0114.  It does not claim a
remote inference node that receives textual workspace data obtains filesystem
authority.  It adds no default logging, content/path cache, transcript, or
retained configuration.

## Rationale

Direct same-process composition is the smallest seam that turns RFC-0114's
accepted local authority into a useful bounded coding workflow while keeping
ordinary Code textual and engine-independent.  A closed one-action response
grammar makes model-directed requests explicit and rejectable without creating
a reusable tool vocabulary.  The eight-action hard limit permits useful
multi-step work but refuses an open-ended autonomous loop.

Reinjection as deterministic user-role text preserves the existing Code request
representation and accurately marks workspace data as untrusted.  Preserving
normal Code routing avoids a special local-execution policy, while explicit
disclosure wording lets the operator understand the privacy consequence.

The fixed 8 MiB interaction-response ceiling keeps the new parsing surface
finite without changing ordinary Code output.  It accommodates an RFC-0114
one-MiB `write` value even when JSON escaping substantially expands its textual
representation, without formula-derived dynamic limits or coupling to model
token limits.

## Alternatives considered

### Change ordinary `code` to have filesystem tools

Rejected.  It would silently revise RFC-0067 and make ordinary Code
authority-bearing.

### Make `list`, `read`, and `write` cluster capabilities

Rejected.  They are local authority permissions, not RFC-0066 node-eligibility
semantics.

### Invoke RFC-0115 internally

Rejected.  Same-process trusted composition can call RFC-0114 directly;
subprocess framing adds machinery without a new authority boundary.

### Generic tool/function-calling or agent framework

Rejected.  One closed workspace vocabulary has not demonstrated a need for
generic tools, planners, registries, IDs, sessions, or extensibility.

### External OpenCode, Pi, or Aider harness

Not selected as product architecture.  Separate local consumers may use
RFC-0115 independently, but this HAC composition must not depend on them.

### Process execution, retained grants, or unlimited looping

Deferred or rejected.  Shell/process authority needs separate evidence;
ephemeral explicit construction is smaller than retention; and eight actions
are safer and more understandable than an unlimited loop.

### Force Code inference to remain local

Not selected.  The authority is local, but existing Code routing remains
unchanged; the resulting text-data disclosure is documented explicitly.

## Consequences

The proposal enables a real, bounded multi-step workspace coding workflow while
keeping filesystem authority HAC-owned and local, `code` textual and
engine-independent, and external harnesses unnecessary.  It adds no new
filesystem policy layer or generic agent architecture, and existing remote Code
routing may continue.

The trade-offs are deliberate: structured model output may be malformed and
then fails closed; only `list`, `read`, and `write` are available; there is no
create/delete/Git/shell/test execution; the maximum is eight actions; a large
successful list/read result may be impossible to reinject under RFC-0067's
bound; an oversized model result terminates before interaction parsing; a write
can remain committed after later failure; workspace text can be disclosed to an
existing configured remote Code node; model compliance with the closed grammar
is required; and no prompt-injection prevention is claimed.

## Implementation boundary

This accepted RFC authorizes only a later separate implementation that proves
this narrow interaction: one small composition
or state-machine module, direct `WorkspaceAuthority`, ordinary existing Code
caller, closed parser/serializer, and focused tests.  It must not thereby
authorize final CLI spelling, browser support, retained configuration, generic
tools, process execution, remote workspace authority, or any changed accepted
RFC text.

Module/class/function names, exact terminal presentation, parser helper
structure, state-machine representation, and deterministic outcome-message
whitespace remain open implementation details.  The response grammar, budget,
authority lifecycle, action semantics, and remote textual-disclosure boundary
must remain as specified here.

## Open questions

- What exact human CLI spelling can expose this composition without changing
  the established ordinary or interactive Code semantics?
- What narrow implementation proof best demonstrates the closed grammar,
  duplicate-key rejection, budget boundary, outcome provenance, and Code-bound
  termination without generalizing the composition?

## Decision

Accepted.  HAC accepts one bounded workspace-aware Code interaction that
preserves ordinary textual `code` inference and composes it with one ephemeral
local RFC-0114 authority, the closed final/workspace response grammar, and at
most eight budget-consuming workspace action attempts.  It retains existing
Code request bounds plus the interaction-only model-result bound, sequential
action-and-continue behavior, existing routing, and explicit remote textual
workspace-data disclosure semantics.  It introduces no generic tools or agent
framework, process execution, retained workspace authority, or remote
filesystem authority.
