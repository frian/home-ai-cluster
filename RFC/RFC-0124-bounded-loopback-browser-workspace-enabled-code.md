# RFC-0124: Bounded Loopback Browser Workspace-Enabled Code

Status: Draft

Date: 2026-09-13

## Summary

The existing loopback browser Code conversation should gain one explicit, optional workspace-enabled mode.

Ordinary browser Code remains text-only by default.

When the operator explicitly enables workspace access, provides one existing host workspace root, and selects one non-empty subset of the accepted `list`, `read`, `write`, and `create` grants, one submitted human turn may use the existing bounded native HAC workspace-aware Code interaction.

The browser does not gain direct filesystem operations. There are no browser `/list`, `/read`, `/write`, or `/create` endpoints.

Instead, each workspace-enabled human turn sends:

```text
explicit workspace root
explicit grants
successful current-page human/final Code history
new human instruction
```

to one browser-only loopback workspace-aware Code facade.

HAC validates that request, constructs one fresh caller-local `WorkspaceAuthority`, and runs one bounded RFC-0116 interaction using ordinary independently routed `capability=code` inference.

There is no server-side workspace session, conversation ID, workspace ID, token, retained grant, database, or workspace registry.

The official browser keeps one root and grant set fixed for workspace-enabled turns belonging to the same current-page Code conversation. That continuity belongs to browser state, not to a server-side security identity. The server independently validates and reconstructs workspace authority for every request.

Because filesystem effects may already have committed before a later inference or interaction failure, the browser response includes a bounded ordered summary of every workspace action whose RFC-0116 outcome was safely classified. This makes committed effects visible without creating an execution transcript or persistent activity system.

The workspace-bearing browser surface retains the existing native loopback Host and exact-same-origin Origin authority precedent and adds a cross-origin anti-framing requirement.

A confirmed browser disconnect also becomes a cancellation boundary for this route. After disconnect wins, HAC must not deliberately dispatch any new workspace action. Already dispatched or committed filesystem work remains governed by existing workspace semantics and is not rolled back or retried.

This RFC adds no new cluster capability, generic tool system, generic filesystem API, server session, authentication framework, persistence, streaming, browser filesystem API, shell authority, Git authority, or remote filesystem authority.

## Context

RFC-0067 defines `code` as bounded textual inference. The capability itself has no filesystem authority.

RFC-0070 adds the fixed loopback browser Code view.

RFC-0083 allows that browser view to retain one ordered ephemeral Code conversation in current-page JavaScript/DOM memory. Each later turn sends complete successful human/assistant Code history plus the new instruction. Conversation state belongs to the page; there is no server session or conversation identifier.

RFC-0114 introduces one separate HAC-owned local workspace authority based on:

- one explicit existing operator-selected root; and
- one explicit non-empty operation grant set.

RFC-0118 defines the current workspace operation vocabulary:

```text
list
read
write
create
```

RFC-0116 composes ordinary `capability=code` inference with one caller-local `WorkspaceAuthority`.

The model may request a bounded sequence of workspace operations, while HAC independently validates and performs those operations.

One RFC-0116 interaction permits at most:

```text
8 dispatched workspace actions
9 ordinary Code inferences
```

The workspace authority remains on the caller even when Code inference routes to a remote eligible node.

RFC-0117 exposes that interaction through one-shot `hac code-workspace`.

RFC-0123 adds interactive foreground `hac code-workspace`. One CLI invocation owns one fixed root, fixed grants, one process-local `WorkspaceAuthority`, successful human/final conversation history in memory, and one fresh bounded interaction per submitted human turn.

RFC-0123 explicitly leaves browser workspace authority for later architecture.

RFC-0112 and RFC-0113 establish the existing loopback browser mutation boundary:

```text
accepted native loopback authority
+
accepted Host
+
exact same-origin Origin
+
bounded non-simple JSON
+
no CORS authority
```

Those RFCs deliberately do not claim protection against arbitrary local same-user software capable of forging raw loopback requests.

RFC-0082 separately establishes confirmed client disconnect as the cancellation boundary for explicitly covered ordinary HTTP requests. Future routes are not covered automatically.

The project now has all semantic pieces needed for browser workspace-aware Code, but connecting them requires an explicit architecture because filesystem authority is materially stronger than existing browser Code.

## Problem

The current browser Code conversation can discuss source code but cannot operate on an explicitly granted local workspace.

An operator who wants bounded workspace-aware coding must currently use `hac code-workspace`.

Adding workspace access to the browser must not silently turn ordinary Code into filesystem-authorized Code.

It must also avoid creating:

- a generic filesystem HTTP API;
- a persistent workspace session;
- server-owned conversation state;
- opaque workspace tokens;
- browser-side filesystem authority;
- or a generic agent/tool architecture.

HTTP also introduces two truthfulness problems.

First, separate browser requests do not naturally share one process-local `WorkspaceAuthority`.

A server session could preserve such object identity, but no demonstrated safety property requires that identity. Each browser request can instead be treated as a fresh explicit authority grant.

Second, one or more filesystem actions may commit before a later inference or interaction failure.

A browser response that displays only a final generic failure could therefore misleadingly imply that no filesystem effect occurred.

The required separation is:

```text
Code capability
    !=
workspace authority

browser conversation state
    !=
workspace filesystem state

workspace filesystem state
    !=
WorkspaceAuthority object lifetime

WorkspaceAuthority object lifetime
    !=
server session identity
```

## Goals

This RFC should:

- extend the existing browser Code experience with explicit optional workspace access;
- preserve ordinary browser Code as text-only by default;
- require one explicit existing workspace root and explicit non-empty grants;
- keep root and grants outside capability routing and model authority;
- construct one fresh caller-local `WorkspaceAuthority` for each workspace-enabled human turn;
- reuse accepted RFC-0116/RFC-0118 interaction semantics;
- keep successful conversation history in current-page browser memory only;
- keep root and grants fixed for workspace-enabled continuation of one current-page Code conversation;
- preserve real committed filesystem effects independently of browser state;
- provide bounded post-turn transparency for classified workspace actions;
- preserve same-origin loopback authority and prevent cross-origin framing;
- stop dispatching new workspace actions after a confirmed client disconnect wins; and
- remain small, local-first, privacy-first, engine-independent, and understandable.

## Non-goals

This RFC does not introduce:

- a new cluster capability;
- filesystem methods on adapters;
- remote filesystem authority;
- generic filesystem HTTP operations;
- raw browser `list`, `read`, `write`, or `create` endpoints;
- a generic operation-dispatch endpoint;
- generic tools or function calling;
- MCP;
- an agent framework;
- shell or subprocess authority;
- command allowlists;
- test, compiler, formatter, linter, build, or Git authority;
- patch, diff, search, editor, or file-browser APIs;
- browser-side filesystem mutation;
- browser File System Access API authority;
- file/directory upload as workspace authority;
- workspace discovery;
- repository detection;
- implicit current-working-directory authority;
- a default workspace;
- retained workspace profiles;
- recently used workspace retention;
- server-side workspace sessions;
- workspace IDs;
- conversation IDs;
- opaque or signed workspace tokens;
- server-held workspace registries;
- cookies for workspace authority;
- server-side conversation persistence;
- database-backed state;
- recovery or resume;
- request-status lookup;
- rollback;
- retry;
- streaming;
- Server-Sent Events;
- WebSockets;
- generic event infrastructure;
- background work;
- concurrent workspace actions;
- workspace locking;
- generic authentication;
- accounts, login, OAuth, or ACLs;
- LAN browser workspace authority;
- CORS;
- Pi or OpenCode integration;
- harness selection or abstraction;
- node affinity or sticky execution;
- runtime/model selection changes;
- Docker; or
- Kubernetes.

This RFC does not change ordinary `hac code`, existing CLI `hac code-workspace`, `code-file`, Aider integration, adapter contracts, `ClusterRequest`, `ClusterResult`, remote request envelopes, receiver routes, static routing, capability declarations, or retained configuration.

## Proposal

### Existing Code surface with explicit workspace access

Workspace access belongs to the existing browser Code experience.

It is not a new cluster capability and does not require a second browser product surface.

Conceptually:

```text
Code

[ ] Enable workspace access

Workspace root: /some/explicit/path

Grants:
[x] list
[x] read
[ ] write
[ ] create
```

Exact labels, controls, layout, and styling remain implementation details.

Architecturally:

```text
workspace access disabled
    ->
existing RFC-0083 text-only Code behavior

workspace access enabled
    ->
explicit root
+
explicit grants
+
workspace-aware browser facade
```

Workspace access is disabled by default.

When disabled, ordinary RFC-0083 browser Code behavior remains unchanged.

Enabling workspace access does not alter the `code` capability.

It authorizes an additional caller-local workspace composition for that submitted human turn.

### Explicit workspace authority

A workspace-enabled turn requires:

- one explicit existing host workspace root; and
- one explicit non-empty subset of:

```text
list
read
write
create
```

There is no default root.

The browser must not infer:

- current working directory;
- repository root;
- home directory;
- HAC launch directory;
- retained configuration;
- previously used root; or
- any root suggested by model output.

A plain host-path input is sufficient for this architecture.

This RFC does not authorize browser filesystem handles or browser-specific directory authority.

The model cannot add, remove, replace, or escalate grants.

### Current-page workspace continuity

The official browser owns the ephemeral UX continuity of the Code conversation.

Before the first workspace-enabled turn, the operator may select the workspace root and grants.

Once workspace-enabled turns are part of the retained current-page Code conversation, that conversation has one fixed workspace root and grant set.

Any later workspace-enabled turn belonging to that same retained Code conversation must use the same root and grants.

Changing root or grants requires abandoning the current ephemeral Code conversation before beginning another workspace-enabled conversation.

Reloading or closing the page is sufficient to abandon the conversation. This RFC does not require a dedicated conversation-reset control.

This is a browser-owned product invariant.

It is not server-side session identity.

The server does not remember an earlier root/grant pair and does not compare one HTTP request with another.

A handcrafted later request containing a different otherwise-valid explicit root/grant pair is therefore a new explicit authority request, not corruption of a server session that does not exist.

### One request, one fresh authority

Each workspace-enabled human turn is independently authoritative.

Conceptually:

```text
current-page browser state
        |
        | explicit root
        | explicit grants
        | successful human/final Code history
        | new human instruction
        v
one browser-only loopback request
        |
        v
validate browser authority
        |
        v
validate request
        |
        v
construct fresh WorkspaceAuthority
        |
        v
run one bounded RFC-0116 interaction
        |
        v
final result or handled failure
+
bounded classified workspace activity
```

One `WorkspaceAuthority` exists only for that server interaction.

Its root and grants remain fixed for that interaction.

When the request ends, that authority object ends.

A later human turn constructs another fresh authority from the explicit request.

Filesystem continuity comes from the real filesystem.

Conversation continuity comes from the browser.

Neither requires server-side workspace object identity.

### Browser-only workspace-aware facade

Workspace-enabled Code uses one browser-only semantic facade.

Its exact HTTP path and JSON field names are implementation details.

The route exists only in the loopback browser application composition.

It must be absent from:

- API-only application composition;
- receiver-only application composition;
- trusted-LAN receiver surfaces;
- OpenAI-compatible application composition; and
- other generic native API surfaces not explicitly covered here.

One request represents one complete human-triggered bounded workspace-aware interaction.

The browser cannot directly request a filesystem operation through the facade.

No equivalent routes may be added for:

```text
/list
/read
/write
/create
```

and no generic operation-dispatch endpoint is authorized.

The existing `/v1/chat` contract remains unchanged.

Workspace root/grant authority must not be added to:

- ordinary `/v1/chat`;
- `ClusterRequest`;
- remote request envelopes; or
- adapter interfaces.

### Closed request domain

A workspace-enabled request carries only the semantic data needed for one interaction:

```text
workspace root
workspace grants
prior successful current-page human/final Code messages
new human instruction
```

It contains no:

- workspace ID;
- conversation ID;
- session ID;
- token;
- node selector;
- runtime selector;
- model selector;
- adapter selector;
- arbitrary options dictionary;
- raw filesystem operation requested by the browser; or
- prior workspace activity transcript.

The request shape is closed.

Unknown members fail locally before inference or workspace action.

Existing accepted semantic bounds remain authoritative, including:

- RFC-0067 Code message-content bounds;
- RFC-0114 workspace authority constraints;
- RFC-0116 interaction bounds; and
- RFC-0118 operation semantics.

This RFC introduces no additional architectural HTTP-body byte constant.

An implementation may use ordinary defensive transport limits provided they do not alter the accepted semantic contract or become a new user-facing authority rule.

### Physical root disclosure boundary

The physical workspace root exists only to construct the local authority.

It must not be forwarded merely because it appeared in the browser request to:

- an inference node;
- a remote request envelope;
- an adapter;
- workspace action outcome text sent to the model;
- a generated HAC activity summary;
- ordinary safe error responses;
- ordinary logs; or
- retained configuration.

The operator may independently mention physical paths in human conversation text. This RFC does not redact arbitrary operator/model content.

### Browser request authority

Every workspace-enabled browser request requires:

```text
loopback-browser composition
+
accepted actual native loopback authority
+
accepted Host authority
+
exact same-origin Origin
+
application/json non-simple request
+
closed request shape
+
no CORS authority
```

The accepted native authority comes from HAC's actual local server authority, following the RFC-0112 precedent.

Client-controlled Host and Origin values must not authenticate one another.

Requests are refused before workspace authority construction if required browser authority is absent or invalid, including:

- unacceptable Host;
- missing Origin;
- `Origin: null`;
- foreign Origin; or
- unacceptable request media type.

CORS preflight behavior is defense in depth, not authorization.

This RFC does not claim protection against arbitrary same-user local software capable of forging raw loopback HTTP requests.

That threat remains outside the accepted browser-origin boundary and generally already possesses equivalent host filesystem authority.

### Cross-origin framing boundary

The authority-bearing HAC browser page must not be usable as a cross-origin framed UI.

An unrelated Web origin must not be able to embed the real HAC page and trick the operator into interacting with genuine same-origin workspace controls through clickjacking or UI redressing.

The exact standards-compliant anti-framing mechanism is an implementation detail.

The requirement may apply to the complete fixed loopback page because the existing page contains multiple views and now includes an authority-bearing Code mode.

This does not create a general browser authentication framework.

### Native workspace interaction semantics

After request-authority and request validation, HAC constructs one local RFC-0114/RFC-0118 `WorkspaceAuthority`.

HAC then runs one fresh RFC-0116-style workspace-aware Code interaction.

Each human turn receives:

```text
at most 8 dispatched workspace actions
at most 9 ordinary Code inferences
```

The available workspace actions remain exactly:

```text
list
read
write
create
```

Actions remain sequential.

Every actually dispatched workspace action consumes one action-budget unit whether its RFC-0116 outcome is success or refusal.

The model cannot:

- reset the budget;
- change the root;
- change grants;
- replace the authority;
- create another authority;
- or request host paths outside the accepted logical-path contract.

This remains native HAC workspace orchestration.

No external harness is selected.

### Code capability and routing remain unchanged

Every inference inside the interaction remains one ordinary independently routed:

```text
capability=code
```

request.

Workspace access is not a cluster capability.

Workspace grants do not participate in:

- routing eligibility;
- static capability declarations;
- remote topology;
- fallback ordering;
- runtime selection; or
- adapter selection.

Different inferences inside one workspace turn may route to different eligible Code nodes.

Different human turns may also route independently.

There is no sticky node, model, runtime, adapter, or inference session.

The `WorkspaceAuthority` remains caller-local.

A remote Code node never receives:

- the authority object;
- physical workspace root;
- filesystem handles;
- executable grants;
- workspace token; or
- direct filesystem authority.

### Workspace-derived textual disclosure

RFC-0116's existing disclosure consequence remains explicit.

Workspace observations may become textual context for later Code inference during the same interaction.

Successful final answers may also contain information derived from workspace contents.

Because Code inference remains independently routed, an explicitly configured eligible remote Code node may receive that bounded textual context.

Likewise, a later browser Code turn may send earlier successful human/final conversation history to a newly selected remote Code node.

This is textual disclosure through existing Code routing.

It is not remote filesystem authority.

Enabling workspace access does not force Code inference to remain local.

### Browser conversation state

The browser retains successful Code conversation history according to RFC-0083, conceptually:

```text
human instruction
final assistant content

human instruction
final assistant content
...
```

Workspace-enabled Code reuses that same successful conversation.

A failed workspace-enabled turn is not successful conversation history.

Later Code context does not automatically include:

- workspace action requests;
- workspace action outcomes;
- list results merely because they appeared as activity;
- read contents merely because they appeared as activity;
- refusal records;
- orchestration messages;
- physical workspace root;
- grants; or
- failure records.

Workspace-derived information intentionally present in a successful final assistant answer remains part of that exact successful final answer and therefore remains conversation history.

The browser must not automatically summarize, truncate, prune, rewrite, or sanitize successful prior human/final conversation to make a later request fit.

Reloading or closing the page discards the ephemeral conversation and browser-owned workspace selection.

No server workspace session exists to clear.

### Code context bound

RFC-0067's aggregate 65,536 UTF-8-byte Code message-content bound remains authoritative before every ordinary Code inference.

For the first inference of a workspace-enabled turn, candidate Code context may contain:

- the RFC-0116 workspace interaction contract;
- prior successful human/final Code conversation history;
- the new human instruction; and
- accepted orchestration framing.

Later inferences may additionally contain current-turn workspace action requests and outcomes.

The server validates complete prospective Code message content before every inference.

The browser may provide matching early validation where it has enough information, but browser validation is not authoritative because later action/outcome context cannot be predicted in advance.

If the initial Code inference cannot fit:

```text
no inference
no workspace action
failed human turn not retained
prior successful history preserved
```

If one or more workspace actions already completed and a later continuation cannot fit:

```text
interaction fails
committed filesystem effects remain
prior successful history remains
failed human turn not retained
no retry
no truncation
no summarization
no rollback
```

### Final result

A valid non-empty RFC-0116 final answer becomes the assistant side of the successful browser Code turn.

The browser retains:

```text
exact human instruction
exact non-empty final assistant content
```

A valid RFC-0116 final envelope with empty final content remains valid for the underlying one-shot interaction grammar.

At the browser conversation boundary, however, empty final content cannot form a meaningful successful assistant conversation entry.

It is therefore a handled failed browser turn:

```text
pending human turn:                     not retained
synthetic assistant turn:               not retained
earlier successful human/final history: preserved
committed filesystem effects:           preserved
automatic retry:                        none
```

The final inference's existing `node_id` may remain visible as attribution for that final result.

It must not be presented as proof that one node handled every inference in the workspace interaction.

### Bounded workspace activity transparency

A workspace-aware turn may change the filesystem before the final result is known.

The browser must therefore preserve enough bounded post-turn activity to avoid presenting a later terminal failure as though no workspace activity occurred.

For each workspace action whose normal RFC-0116 outcome was safely classified, the response includes one ordered bounded activity entry containing only:

```text
operation
logical workspace path
RFC-0116 outcome
```

`operation` is one of:

```text
list
read
write
create
```

The normal outcome reuses RFC-0116's accepted distinction:

```text
success
refused
```

This RFC does not create another filesystem error taxonomy.

The bounded activity contains at most eight entries because RFC-0116 permits at most eight dispatched workspace actions.

An activity entry must not contain:

- physical workspace root;
- read file contents;
- write replacement contents;
- list entries;
- raw model response;
- raw exception;
- model identity;
- runtime identity;
- adapter identity;
- remote network address; or
- credentials.

A successful final response includes activity accumulated before the final answer.

A safely handled terminal failure includes whatever earlier action activity has already been truthfully classified and can be safely presented.

If an in-progress action cannot be truthfully classified because of an unexpected internal failure, HAC must not invent `success` or `refused` for it.

Terminal interaction failure remains a separate safe failure presentation.

Activity is operator-facing page state only.

It is not later Code conversation context.

This summary is not:

- a generic execution trace;
- a retained log;
- a model transcript;
- an event stream;
- observability infrastructure; or
- monitoring infrastructure.

### Failure and committed filesystem truth

A safely handled failed workspace-enabled human turn does not enter successful Code conversation history.

Earlier successful history remains.

Filesystem state is independent.

A successful committed `write` or `create` remains committed when a later stage fails, including:

- later inference failure;
- malformed model response;
- context overflow;
- budget exhaustion;
- empty final;
- presentation failure; or
- later browser disconnect.

There is no automatic rollback.

There is no automatic retry.

An RFC-0116 workspace refusal remains an intermediate outcome and may still allow a later action or final response within the remaining interaction budget.

An internal interaction failure terminates the turn.

No failure creates recovery state or server-side session state.

### Confirmed browser disconnect

The new workspace-enabled browser facade adopts RFC-0082's confirmed-disconnect principle.

A disconnect is confirmed only through the supported ASGI request boundary for that specific request.

If the workspace interaction already owns its terminal normal result when disconnect becomes observable, normal completion wins according to the RFC-0082 precedent.

Response delivery is not guaranteed and no retry occurs.

If confirmed disconnect wins while the workspace interaction is still pending, HAC must cancel or abandon its owned pending interaction work.

Most importantly:

```text
confirmed disconnect wins
    ->
no new list/read/write/create action
may be dispatched afterward
```

An action already dispatched before disconnect won is different.

Its filesystem semantics remain governed by RFC-0114/RFC-0118.

It may already have committed or may finish while cancellation unwinds.

Committed effects are not rolled back.

Ambiguous actions are not retried.

A later model/runtime result after disconnect must not restart the interaction or authorize another workspace action.

As in RFC-0082, downstream runtime work may continue outside HAC's control despite HAC cancellation.

A disconnected browser receives no guaranteed activity summary.

This RFC adds no:

- recovery ID;
- status lookup;
- durable action log;
- resumable request;
- reconnect protocol; or
- recovery database.

After transport loss, the browser may therefore be unable to know every filesystem effect that committed before disconnect.

That ambiguity is explicitly accepted rather than introducing recovery infrastructure.

### Privacy and retention

Workspace root, grants, logical paths, source contents, replacement contents, conversation text, outcomes, and final answers are private operator data or data derived from it.

The workspace-enabled browser surface adds no server persistence.

It adds no:

- prompt/result logging;
- workspace activity log;
- retained root;
- retained grants;
- request database;
- conversation database; or
- persistent browser workspace storage.

Current-page browser memory may contain:

```text
successful Code conversation history
current workspace root
current grants
rendered bounded activity
```

Reloading or closing the page discards that browser-owned state.

Real filesystem changes remain ordinary filesystem state.

No implicit sensitive-file filter is introduced.

Once `read` is explicitly granted, RFC-0114 remains authoritative about which logical files inside the workspace may be read.

## Compatibility

Ordinary browser Code remains available and text-only when workspace access is disabled.

Existing browser Chat, Summarize, Classify, retained configuration, and remote-node configuration behavior remain unchanged.

Existing `/v1/chat` semantics remain unchanged.

API-only and receiver applications gain no workspace route.

Existing `hac code-workspace` remains the CLI workspace-aware operator surface.

RFC-0114, RFC-0116, RFC-0118, and RFC-0123 keep their existing CLI/process semantics.

No operator is required to enable workspace access.

## Rationale

The smallest useful browser extension is not a new cluster capability or a separate coding product.

It is:

```text
existing Code
+
explicit optional caller-local workspace authority
```

Ordinary Code remains text-only.

Workspace authority is visible and opt-in.

Each browser request is a fresh explicit authority grant, so a server-held session contributes no required safety property.

The three relevant lifetimes remain separate:

```text
browser conversation continuity
    -> page memory

filesystem continuity
    -> real filesystem

workspace authority lifetime
    -> one submitted server interaction
```

No fourth server-session lifetime is required.

The bounded activity summary solves the primary truthfulness problem created by real filesystem effects: a later interaction failure cannot silently imply that already classified successful actions never happened.

The existing Host/Origin boundary protects against unrelated Web-origin direct requests.

Anti-framing closes the separate UI-redressing path in which another site embeds the genuine HAC page and induces genuine same-origin operator interaction.

Confirmed-disconnect cancellation prevents an abandoned browser request from deliberately continuing to dispatch new filesystem actions after its human consumer is gone.

All of this remains bounded without introducing sessions, accounts, authentication, generic tools, persistent logs, or streaming infrastructure.

## Alternatives considered

### Create a separate Workspace Code browser view

Rejected.

Workspace-aware Code still uses the `code` capability and the existing Code conversation.

The architectural difference is explicit local authority, not a second capability or product.

### Grant workspace authority to ordinary Code automatically

Rejected.

Filesystem authority must remain explicit and opt-in.

### Add workspace fields to `/v1/chat`

Rejected.

That would broaden an existing generic native Code path with physical filesystem authority and make the authority available outside the intended loopback-browser facade.

### Add raw filesystem browser endpoints

Rejected.

The demonstrated need is workspace-aware Code, not arbitrary browser filesystem access.

### Retain one WorkspaceAuthority across browser turns

Rejected.

No accepted invariant requires server-side authority object identity across human turns.

### Add a workspace session ID or opaque token

Rejected.

It introduces session lifecycle and hidden server ownership without a demonstrated need.

### Enforce root/grant equality server-side across requests

Rejected.

That requires server-owned conversation identity.

The official page owns its current-page continuity instead.

### Allow root/grant changes without abandoning the current workspace-enabled conversation

Rejected for the official browser behavior.

Presenting changing workspace authority as one continuous workspace-enabled conversation would make the authority boundary unnecessarily ambiguous.

### Use browser filesystem APIs

Rejected.

Browser handles introduce a second filesystem authority model and browser-specific semantics without being needed for HAC's existing native workspace boundary.

### Stream workspace activity

Rejected.

One human turn permits at most eight actions.

A bounded post-turn summary is sufficient for the first browser implementation.

### Return only final success or failure

Rejected.

A committed filesystem effect may precede later failure.

That would make failure presentation potentially misleading.

### Roll back workspace changes after later failure

Rejected.

Rollback would require transactional and destructive authority beyond the accepted workspace model.

### Add per-action confirmation

Deferred.

Explicit root and grants already define the accepted authority boundary.

Per-action approval would materially change the interaction lifecycle and is not required by this proposal.

### Persist workspace profiles

Rejected.

The first browser proof requires no retained workspace authority.

### Add authentication or browser secrets

Rejected.

The accepted threat boundary is unrelated Web origins, not arbitrary hostile software already operating as the same local user.

### Ignore cross-origin framing

Rejected.

Direct Origin validation alone does not prevent UI redressing through an embedded genuine HAC page.

### Continue autonomous workspace work after confirmed disconnect

Rejected.

Once the browser consumer is confirmed gone, HAC should not deliberately dispatch additional filesystem operations based on later model output.

## Trade-offs

The browser gains materially stronger local authority when the operator explicitly enables workspace access.

A selected remote Code node may receive workspace-derived textual context. This follows existing Code routing authority and does not grant remote filesystem access.

The official browser fixes root and grants for one current-page workspace-enabled conversation, but the server does not retain that continuity. That is intentional.

Post-turn activity is not live.

The operator learns classified workspace activity when the request completes normally or fails in a way that still permits safe response delivery.

Transport loss can leave already dispatched filesystem effects ambiguous from the browser's perspective.

This RFC explicitly accepts that limitation rather than introducing request identity, durable logs, or recovery machinery.

## Implementation boundary

If accepted, a later implementation may only add the smallest support required for this architecture:

- explicit workspace enablement inside the existing Code view;
- one explicit root input;
- explicit `list`, `read`, `write`, and `create` grant controls;
- current-page root/grant continuity;
- one browser-only workspace-aware Code route;
- accepted Host/Origin/media-type/request-shape validation;
- fresh per-request `WorkspaceAuthority` construction;
- reuse of existing native RFC-0116/RFC-0118 interaction code;
- bounded post-turn classified workspace activity;
- confirmed-disconnect cancellation behavior for the new route;
- anti-framing protection for the fixed loopback browser page;
- focused backend/frontend tests; and
- concise documentation.

A small extraction of existing private workspace-interaction code is acceptable only when required to reuse already accepted RFC-0116 semantics.

Implementation must return to architectural review if it appears to require:

- server sessions;
- workspace registries;
- generic filesystem HTTP operations;
- generic event infrastructure;
- streaming;
- persistent workspace state;
- browser filesystem APIs;
- external harness selection;
- authentication infrastructure;
- remote filesystem authority; or
- broader native API changes.

## Proof expectations

A later implementation should prove at minimum that:

1. ordinary browser Code remains text-only and unchanged with workspace access disabled;

2. workspace access is disabled by default and requires one explicit existing root plus one explicit non-empty accepted grant set;

3. no root is inferred from cwd, repository, home, launch location, retained configuration, or prior use;

4. the official browser keeps one root/grant pair for workspace-enabled turns belonging to one retained current-page Code conversation, and changing that authority requires abandoning that conversation;

5. there is no server-side workspace session, workspace/conversation ID, token, registry, retained grant, or persistent conversation;

6. every submitted workspace-enabled human turn constructs one fresh caller-local `WorkspaceAuthority` and receives one fresh RFC-0116 budget;

7. `list`, `read`, `write`, and `create` preserve RFC-0114/RFC-0118 semantics, remain sequential, and never become direct browser filesystem endpoints;

8. the workspace route exists only in loopback-browser composition and is absent from API-only, receiver, LAN receiver, and compatibility surfaces;

9. unacceptable Host, missing/null/foreign Origin, unacceptable media type, malformed/unknown request members, or invalid workspace authority fail before inference or workspace action;

10. the fixed loopback browser page cannot be used as a cross-origin framed authority-bearing UI;

11. physical workspace root and executable authority never reach remote Code nodes, adapters, remote request envelopes, activity summaries, or ordinary safe logs/errors merely because the browser supplied them;

12. every Code inference remains ordinary independently routed `capability=code` work with no node/model/runtime/adapter affinity;

13. RFC-0067's aggregate Code-context bound is enforced before every inference without automatic truncation, summarization, or pruning;

14. successful browser conversation retention contains only exact successful human instructions and exact non-empty final assistant content; failed turns and activity are not retained as Code conversation;

15. every safely classified dispatched workspace action appears once and in order in a bounded activity summary using only operation, logical path, and existing RFC-0116 success/refusal outcome;

16. committed filesystem effects survive later inference failure, context failure, empty final, presentation failure, and disconnect without rollback or retry;

17. after confirmed disconnect wins, no new workspace action can be dispatched, while already dispatched work remains governed by existing filesystem semantics;

18. disconnect creates no recovery identity, durable action record, status lookup, or automatic retry;

19. reload/close discards browser conversation/workspace/activity memory without altering committed filesystem state; and

20. no generic agent/tool system, shell/Git authority, generic filesystem API, browser filesystem authority, persistent session, streaming/event architecture, external harness abstraction, or remote filesystem authority is introduced.

Retained proof material must not contain real private workspace roots, file contents, replacement contents, prompts, credentials, private topology, runtime/model details, or raw private logs.

## Open questions

None within this bounded proposal.

Exact endpoint path, JSON field names, HTML arrangement, status wording, safe response-status choices, internal helper extraction, anti-framing header mechanism, and concrete activity-response representation remain implementation details provided they satisfy the accepted properties above.

Any future retained workspace profiles, server sessions, recoverable requests, persistent activity history, browser filesystem APIs, workspace discovery, remote workspace authority, streaming activity, per-action confirmation, external coding harnesses, shell/process execution, Git authority, or general authentication requires separate architectural consideration.

## Decision

Pending.
