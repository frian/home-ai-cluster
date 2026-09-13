# RFC-0123: Bounded Interactive Workspace Coding

Status: Accepted

Date: 2026-09-13

## Summary

`hac code-workspace` already provides one explicit, one-shot bounded native HAC
workspace interaction. This proposal adds the smallest interactive form of that
operator activity: when no explicit message is supplied, a foreground TTY
invocation may accept human turns until the human exits.

One invocation has one explicit root, one fixed explicit grant set, and one
process-local `WorkspaceAuthority`. Each submitted human turn starts a fresh,
bounded RFC-0116-style native HAC interaction. Successful human/final exchanges
are retained only in process memory; action and outcome context is turn-local.
Committed workspace effects remain filesystem truth.

Existing explicit-message forms remain unchanged and one-shot. Native HAC is
the sole supported coding harness. This proposal preserves the durable
operator-facing `hac code-workspace` seam without harness selection or a harness
abstraction.

## Context

RFC-0114 established caller-local workspace authority. RFC-0116 composes it
with ordinary `capability=code` inference in a finite interaction. RFC-0117
exposes that interaction as `hac code-workspace`. RFC-0118 extends the accepted
operation vocabulary to `list`, `read`, `write`, and `create`.

RFC-0088 is the boring lifecycle precedent for a TTY-only, process-owned,
ephemeral native Code conversation. Its lifecycle is useful here, but it does
not grant workspace authority or change RFC-0116's interaction contract.

The durable operator concept is coding inside one explicitly authorized
workspace. `hac code-workspace` names that activity, not an implementation
choice. Today the only supported harness is native HAC: RFC-0116 workspace-aware
Code composition and ordinary HAC `capability=code` inference.

## Problem

The one-shot workspace surface requires a new foreground invocation for each
follow-up, even after a successful bounded turn. The answer must not turn
RFC-0116 into an indefinitely autonomous loop, retain a workspace session, or
create a generic agent or external-harness framework. A human must decide when
each next bounded autonomous period begins.

## Goals

This proposal aims to:

* add a TTY-only no-message interactive `hac code-workspace` form;
* preserve one explicit fixed caller-local root and grant set for the process;
* retain only successful human/final exchanges in ordinary process memory;
* start a fresh bounded native HAC interaction for every submitted human turn;
* preserve RFC-0067's Code-context bound and RFC-0116's per-turn bounds; and
* retain existing routing, timeout, disclosure, authority, and presentation.

## Non-goals

This RFC does not authorize Pi or OpenCode integration, changed Aider
integration, harness selection, a generic harness interface, generic agents,
generic tools/function calling, MCP, shell or process execution, Git authority,
test/compiler/formatter/linter/build authority, command allowlists, dynamic or
escalating grants, root changes, retained workspace profiles, persisted
conversation history, server sessions, session/conversation IDs, recovery or
resume, background work, concurrent turns, parallel workspace actions, sticky
routing, model/runtime-selection changes, remote filesystem authority, browser
workspace authority, a workspace HTTP API, database-backed state, automatic
context summarization or pruning, generic events, dashboards, Docker, or
Kubernetes.

It does not change ordinary `hac code`, `code-file`, existing Aider behavior,
adapters, cluster capability definitions, `ClusterRequest` / `ClusterResult`,
remote envelopes, topology, receiver routes, static routing, or runtime
composition.

## Proposal

### Invocation distinction and TTY admission

The existing explicit-message forms remain one-shot with all RFC-0117 semantics:

```text
hac code-workspace --root PATH --grant OP [--grant OP ...] MESSAGE
hac code-workspace --root PATH --grant OP [--grant OP ...] --message MESSAGE
```

Supplying both message forms remains invalid, and blank explicit messages remain
invalid. With neither positional `MESSAGE` nor `--message`, the command may
enter foreground interactive mode:

```text
hac code-workspace --root PATH --grant OP [--grant OP ...]
```

There is no `--interactive` flag. Entry requires both standard input and output
to be TTYs, conceptually:

```text
sys.stdin.isatty() and sys.stdout.isatty()
```

If either is false, HAC fails locally before reading input or sending inference.
This creates no piped-stdin protocol, NDJSON, JSON Lines, machine-facing
interactive API, daemon, listener, or persistent session service. RFC-0115
remains the separate machine-facing workspace carrier.

### Fixed foreground authority

One interactive invocation owns exactly one explicit workspace root, one
explicit fixed grant set, and one process-local `WorkspaceAuthority`. Root and
grants are selected before the first human turn and remain unchanged until exit.
There is no default grant; RFC-0117 duplicate-grant semantics remain unchanged.

No human turn or model output may change root, add or remove a grant, replace
authority, dynamically escalate authority, choose an arbitrary native host path,
or retain authority after exit. `list`, `read`, `write`, and `create` retain
their RFC-0114/RFC-0118 meanings.

### Human-controlled outer loop

```text
one foreground invocation
    |
    +-- fixed root, fixed grants, one WorkspaceAuthority
    |
    +-- human turn -> one bounded native HAC workspace interaction
    |                 -> final answer or handled failure
    |
    +-- next human turn -> fresh bounded native HAC workspace interaction
    |
    -> human exits
```

After a final answer, the model cannot autonomously continue. Only a newly
submitted human turn starts another bounded interaction. The model cannot
generate a human turn or reset its budget.

### Three distinct forms of state

```text
successful human conversation history
    != turn-local orchestration context
    != workspace filesystem state
```

#### Successful human conversation history

Across successful turns, retain only ordered successful human/final exchanges:

```text
human instruction 1
final answer 1

human instruction 2
final answer 2
```

The retained assistant side is the exact non-empty final human-visible
`content`, not the RFC-0116 internal closed JSON envelope. HAC does not rewrite,
summarize, clean up, strip Markdown from, or extract from that content before
retaining it. This state exists only in ordinary process memory: no server-side
owner, conversation ID, persistence, retained configuration, file/database
storage, or restart/recovery semantics. A failed turn does not join it.

RFC-0116 and existing explicit-message one-shot `hac code-workspace` behavior
continue to permit a valid final response with empty `content`:

```text
{"kind":"final","content":""}
```

This RFC does not change that final grammar or one-shot behavior. In interactive
`hac code-workspace`, however, such a final cannot become an assistant
conversation message because the existing `ChatMessage` assistant content is
non-empty. HAC therefore treats that submitted human turn as a handled failed
interactive turn at the local conversation boundary: it retains neither the
pending human instruction nor a synthetic assistant message; preserves earlier
successful history and any already committed `write`/`create` effects; performs
no automatic retry; presents one safe human-readable interaction failure through
existing CLI failure conventions; and keeps the foreground loop active when
safely possible.

#### Turn-local RFC-0116 orchestration state

One turn may accumulate its interaction contract, current instruction, model
workspace requests, HAC outcomes, returned `list`/`read` content,
`write`/`create` outcome context, and refusals. It is required to complete that
turn but must not automatically become retained conversation history.

A later turn starts conceptually from:

```text
earlier successful human/final history
+ new human instruction
+ fresh RFC-0116 interaction context
```

It does not receive the old complete action/outcome transcript. No generic
transcript or session object is introduced.

#### Real workspace filesystem state

Committed `write` or `create` effects remain physically true for later turns.
They are not rolled back because later inference or a later turn fails, context
becomes too large, a budget is exhausted, a response is malformed, presentation
fails, or the process exits.

### Native HAC action budget and Code context bound

For native HAC only, each submitted human turn gets a fresh RFC-0116 bound:

```text
at most 8 dispatched workspace actions
at most 9 ordinary Code inferences
```

Every actually dispatched `list`, `read`, `write`, or `create` consumes an
action. This bound applies to one human decision, not the complete foreground
invocation, and does not pre-decide limits for future Pi/OpenCode integration.

RFC-0067's 65,536 UTF-8-byte aggregate Code message-content bound remains
authoritative before every native Code inference. Candidate context may include
successful prior human/final history, the current instruction, current RFC-0116
contract, and current turn-local action/outcome context. HAC must not
automatically prune, summarize, truncate, roll context, drop prior successful
exchanges, drop action provenance, or raise the bound.

If a new turn cannot form its initial valid request within the bound, reject that
pending turn locally, do not retain it, preserve earlier successful history, and
keep the loop active when safely possible. If an action already committed and a
later continuation cannot fit, the turn may fail but committed filesystem truth
remains and is not rolled back.

### Routing, disclosure, and timeout

Every native inference remains one ordinary independently routed
`capability=code` request. No sticky node, node/model/runtime/adapter affinity,
session ownership, workspace capability routing, or transport change is added.
Internal inferences and different turns may use different eligible Code nodes.
Continuity is bounded caller-supplied text, not remote state.

`WorkspaceAuthority` remains caller-local. Remote Code nodes receive only the
ordinary textual context RFC-0116 permits; they never receive physical root,
executable grants as authority, filesystem handles, remote filesystem authority,
or workspace session objects.

That ordinary textual context can include successful human instructions and
exact successful final answers retained from earlier interactive turns. A final
answer may itself contain, quote, summarize, or otherwise derive from workspace
information observed during an earlier turn. A later independently selected
eligible remote Code node may therefore receive that bounded textual history
under the operator's existing Code routing configuration. Continuing the same
interactive `code-workspace` invocation accepts this conversational disclosure
consequence, just as independently routed interactive Code carries prior
successful conversation context. It is not remote filesystem authority and does
not provide direct workspace access.

One existing `--timeout-seconds` value applies independently to every ordinary
Code inference. It is not a human-input timeout, whole-turn/session deadline,
workspace-action deadline, watchdog, or queue timeout.

### Failure, blank input, termination, and presentation

For a safely handled failed human turn:

```text
pending human turn:                     not retained
synthetic assistant turn:               not retained
earlier successful human/final history: preserved
already committed filesystem effects:   preserved
automatic retry:                        none
```

Examples include local context rejection, a valid native final with empty
`content` at the interactive conversation boundary, Code timeout, ordinary
request, transport, or runtime failure, malformed/oversized workspace model
response, action-budget exhaustion, and an unfit continuation. A workspace
refusal is an RFC-0116 intermediate outcome; the model may continue within the
remaining per-turn budget and eventually give a valid final answer. Unexpected
failures that cannot be safely handled may terminate the invocation. There is
no rollback, retry framework, transaction model, checkpointing, or recovery
identity.

Blank or whitespace-only input is not a submitted turn: it sends no inference,
consumes no budget, changes no conversation state or authority, and leaves the
loop active. EOF terminates normally. Ctrl-C terminates cleanly without
traceback or persistence. Termination discards process-memory history,
turn-local state, and process-local authority; it does not undo committed
workspace changes.

Successful turns display their final answer on the ordinary human-readable
foreground result surface. Existing RFC-0117 safe foreground activity includes
`list`, `read`, `write`, and `create`. Prompts and minimal static guidance are
implementation detail. This authorizes no interactive JSON, JSON Lines, machine
event stream, saved transcript, verbose topology/model output, progress
framework, spinner, animation, streaming simulation, or TUI. Explicit-message
stdout/stderr semantics remain unchanged.

### Browser and future-harness boundary

Browser workspace authority is out of scope. This RFC does not select browser
roots or grants; transfer authority browser-to-server; create server-owned
authority, HTTP filesystem operations, browser workspace sessions/persistence;
or decide browser origin/security semantics. A browser workspace-coding surface
requires a separate RFC.

`hac code-workspace` names the operator-facing workspace-coding activity. Native
HAC is the only currently supported harness. Nothing here makes native HAC the
permanent or exclusive orchestration model for that activity. Alternative
harness integration and selection remain future RFC-governed architecture.

This does not define `--harness`, a harness identifier, `Harness`,
`HarnessProtocol`, `HarnessRegistry`, a base class, plugin system, executable
selection, external subprocess lifecycle, Pi/OpenCode configuration, generic
options dictionary, model-ownership abstraction, or generic machine protocol.
Pi and OpenCode are coupling falsification cases, not present features.

## Rationale

One fixed process-local authority makes a small interactive foreground workflow
useful without making it persistent or remotely owned. Preserving one RFC-0116
interaction inside a human-controlled outer loop keeps autonomous activity
explainable: one human decision permits at most eight workspace actions and nine
ordinary Code inferences, then control returns to the human.

Final exchanges provide useful follow-up context without a hidden tool history,
generic session substrate, or false claim that filesystem effects are
conversation state. Fixed authority and independently routed textual requests
retain established local-first, privacy, and capability-centered boundaries.

## Alternatives considered

### Keep workspace coding one-shot only

Rejected. It preserves existing safety boundaries but imposes needless restart
and restatement friction after successful bounded work.

### Make RFC-0116 an unlimited autonomous loop

Rejected. It removes the human decision boundary that gives the action budget
its meaning.

### Add `--interactive` or a piped protocol

Rejected. No-message TTY admission is the smaller familiar lifecycle. A machine
stream overlaps RFC-0115 and introduces protocol scope.

### Retain action transcripts or persist sessions

Rejected. They are unnecessary for follow-up and introduce privacy, storage,
recovery, and generic-session architecture.

### Add harness selection now

Rejected. One native implementation does not justify a selection framework.
Future alternatives require their own RFC.

### Give browser or remote nodes workspace authority

Rejected. Either materially changes the trusted authority boundary.

## Trade-offs

Successful conversation history can eventually consume RFC-0067's fixed bound.
This proposal chooses explicit local rejection of an unrepresentable new turn
over hidden history deletion or transformation. It accepts that a committed
filesystem effect may outlive a failed follow-up, because rollback adds broader
destructive and transactional authority.

Interactive workspace coding is native-HAC-only for now. That limits current
flexibility but keeps the operator surface durable without premature abstraction.

## Implementation boundary

If accepted, a later implementation may only:

* admit no-message TTY `hac code-workspace`;
* retain one fixed `WorkspaceAuthority` for the foreground process lifetime;
* retain successful human/final history in RAM;
* start one fresh bounded RFC-0116-style native interaction per submitted turn;
* provide successful prior human/final history while keeping action/outcome
  context turn-local;
* reset the native eight-action budget per human turn; and
* preserve ordinary Code routing, timeout, validation, safe errors, activity
  output, focused tests, and concise documentation.

A small extraction or parameterization of private workspace-interaction code is
acceptable only if needed for that narrow implementation. Work must return to
architectural review if it requires a generic harness interface, generic session
infrastructure, generic event system, agent framework, tool registry,
persistent state layer, or browser/server workspace architecture.

## Later implementation proof expectations

Later proof material must not retain private real workspace paths, source
content, prompts, credentials, secrets, topology, or model/runtime details. It
should show that:

1. explicit-message forms remain one-shot;
2. no-message interaction requires stdin and stdout TTYs and non-TTY fails
   locally before inference;
3. root/grants are explicit, mandatory, fixed, and unchanged;
4. all four operations preserve semantics and safe activity presentation;
5. blank input sends no inference;
6. every valid turn starts one bounded native interaction with fresh eight-action
   and at-most-nine-inference limits that the model cannot reset;
7. later successful turns receive prior successful human/final history plus the
   new instruction, retaining exact non-empty final content without automatic
   rewriting, summarization, cleanup, Markdown stripping, or extraction, and
   not retaining action/outcome transcripts;
8. a valid native empty final remains valid for explicit-message one-shot use,
   while an interactive empty final becomes a handled failed turn with no
   retained pending human/synthetic assistant message, no retry, preserved
   earlier history and committed effects, safe existing-style failure output,
   and an active loop when safely possible;
9. committed write/create effects remain real across later turns and failures;
10. failed turns are not retained while earlier successful history is preserved;
11. RFC-0067 is checked before every inference without automatic truncation,
    pruning, or summarization;
12. routing remains independent with no sticky node/model/runtime/adapter
    behavior; later eligible remote nodes may receive retained successful
    human/final textual history, including final answers derived from earlier
    workspace observations, but never physical root, `WorkspaceAuthority`,
    handles, executable authority, or direct workspace access;
13. timeout remains per ordinary Code inference;
14. EOF/Ctrl-C discard ephemeral history and authority without undoing effects;
15. no harness selector/abstraction, Pi/OpenCode implementation, browser
    authority, persistence, background work, shell/process/Git authority, or
    other excluded architecture appears; and
16. the full existing test suite is green.

## Open questions

None for this bounded proposal. Future browser workspace coding and alternative
coding harnesses, including Pi or OpenCode, require separate RFCs.

## Decision

Accepted. RFC-0123 accepts one TTY-only foreground interactive
`hac code-workspace` lifecycle when no explicit message is supplied, alongside
unchanged one-shot explicit-message forms. One invocation has fixed caller-local
root, grants, and process-local `WorkspaceAuthority`; it may contain multiple
explicit human turns, each starting one fresh bounded native RFC-0116-style
interaction with at most eight dispatched actions and nine ordinary Code
inferences. Successful human/final history is process-memory-only, retains exact
non-empty final content, and remains distinct from turn-local action/outcome
state; RFC-0067's aggregate Code bound remains unchanged. Ordinary Code
inferences remain independently routed, committed filesystem effects remain
truthful, and the specified interactive empty-final handling applies.

This decision accepts no persistence, sticky routing, dynamic authority, browser
workspace authority, harness-selection mechanism, generic harness abstraction,
Pi/OpenCode integration, shell/process/Git authority, or generic agent/tool
architecture.
