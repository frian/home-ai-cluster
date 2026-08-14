# RFC-0070: Minimal Loopback Code View

Status: Draft

Date: 2026-08-14

Author: @frian

## Summary

Home AI Cluster should extend the fixed loopback browser surface accepted by
RFC-0062 with exactly one fourth user-facing view, **Code**. The view accepts
one textual instruction, sends one same-origin native `POST /v1/chat` request
with explicit `capability: "code"`, and renders the existing free-form textual
`ClusterResult.content` plus existing `node_id` attribution.

This is a narrow additive browser-surface decision. It reuses RFC-0067's
already accepted bounded textual `code` capability and RFC-0062's existing
loopback composition. It creates no capability, route, request or result type,
transport shape, adapter method, routing policy, persistence, or authority.

## Problem

RFC-0067 accepts `code` as an explicit, bounded, text-only semantic capability,
but deliberately leaves the loopback browser unchanged and defers a Code page
to a separate convenience decision. RFC-0062 deliberately defines the initial
loopback browser surface as three fixed views: Chat, Summarize, and Classify.

The existing browser-code-view investigation confirms that the underlying native
seam is already truthful: `POST /v1/chat` accepts ordered messages and an
explicit capability, constructs the accepted `ClusterRequest`, and revalidates
the RFC-0067 `code` aggregate byte bound. The browser may therefore reuse the
accepted request/result path, but widening the fixed browser surface is an
architectural decision that must be made explicitly before implementation.

## Goals

- Authorize exactly one additional fixed loopback browser view named Code.
- Reuse the existing native `/v1/chat` request path with explicit `code`
  semantics.
- Preserve RFC-0067's text-only, 65,536-byte, explicit-capability boundary.
- Preserve RFC-0062's loopback-only same-origin, fixed-asset, non-dashboard,
  privacy, and API-only composition boundaries.
- Keep a later implementation small, understandable, and independently
  testable.

## Non-goals

This RFC does not authorize:

- a generic or dynamically enumerated browser capability UI, capability
  registry, discovery, or arbitrary capability request construction;
- a new `/v1/code` endpoint, request type, result type, transport envelope,
  adapter method, routing policy, or model/runtime selector;
- a browser editor, Monaco, CodeMirror, syntax highlighting, markdown or
  code-block parsing, patch/diff interpretation, or structured editor content;
- Code file upload, Download, Save As, file creation, browser filesystem APIs,
  filesystem editing, repository context, multi-file work, or Aider
  integration;
- multi-turn Code conversation, interactive coding sessions, streaming,
  retries, cancellation, fallback, polling, background work, persistent
  conversations, cookies, localStorage, IndexedDB, server sessions, history,
  metrics containing content, or a dashboard;
- filesystem, repository, Git, shell, command or test execution, tools or
  function calling, agents, autonomous loops, web retrieval, RAG, indexing,
  runtime/model selection, or execution authority; or
- OpenAI-compatible Code access, CORS, a proxy, a second browser process, a new
  port, LAN browser exposure, or an authentication mechanism.

## Proposal

### Fourth fixed browser view

The loopback browser application gains one explicitly designed fixed **Code**
view alongside Chat, Summarize, and Classify:

```text
Code tab
  -> one textual instruction textarea
  -> one explicit user message
  -> same-origin POST /v1/chat
       capability = code
  -> existing ClusterResult
  -> text display plus existing node_id attribution
```

The resulting fixed view set is exactly Chat, Summarize, Classify, and Code.
The browser must not dynamically enumerate capabilities, derive a capability
from user text, or provide a generic capability control. Code remains one
explicitly designed view for one already accepted semantic operation.

### Existing native request path

The Code view reuses the existing native route:

```json
POST /v1/chat
{
  "capability": "code",
  "messages": [
    {"role": "user", "content": "..."}
  ]
}
```

This body enters the existing `ClusterRequest` path with explicit `code`
semantics. It does not require or authorize `POST /v1/code`, request
translation, an internal envelope constructed by browser JavaScript, direct
runtime access, or browser routing choices.

### Input semantics and bound

The first Code view accepts exactly one explicit textual instruction and creates
exactly one `user` message. It has no multi-turn Code conversation state.

RFC-0067's authoritative aggregate message-content limit of **65,536 UTF-8
bytes** remains unchanged. For this one-message view, browser validation may
check the same non-blank and byte-limit conditions for prompt feedback. Native
and core validation remain authoritative. The browser does not count tokens,
inspect model context, detect a language, truncate input, or rewrite the
instruction.

### Result presentation

The Code view renders only the existing free-form textual
`ClusterResult.content` and the existing cluster-owned `node_id` attribution.
It renders content as text; it does not interpret the response as HTML, a file,
a patch, a diff, executable code, or structured editor content.

The view promises neither one code block nor one language, syntax validity,
compilation, execution, correctness, security, or a filename. Generated code
and commands remain response text only.

### Existing browser mechanics

Later implementation may reuse existing fixed tabs and panels, same-origin JSON
request handling, one-active-request handling, safe failure rendering, textual
result rendering, `node_id` attribution, and ephemeral current-page state.
These are direct implementation consequences of the fixed view, not a new
frontend abstraction, generic browser capability component, framework, dynamic
schema, plugin system, or browser capability registry.

### Network, composition, and compatibility boundary

The Code view inherits RFC-0062's loopback browser application boundary:

- only launcher-owned loopback browser compositions may serve it;
- it makes direct same-origin requests to the existing native route;
- no CORS, proxy, second browser process, new port, LAN browser exposure, or
  authentication mechanism is introduced;
- API-only receiver compositions, including LAN receivers, remain page-free;
  and
- the separate OpenAI-compatible process remains unchanged, API-only, and
  Chat-only.

This RFC does not alter application composition, socket-binding ownership, or
the fixed read-only asset namespace; it only authorizes the additional fixed
view within the existing loopback browser application.

### State, privacy, and safe failures

The entered instruction and generated result may exist only in ordinary
current-page DOM/runtime state. Reloading or closing the tab may discard them.
The view adds no cookie, localStorage, IndexedDB, browser-cache application
state, server session, server-side conversation storage, request-history
expansion, prompt/response logging, or metrics containing content.

Existing native/core validation and safe failures remain authoritative. The
browser may present immediate local feedback for blank or over-limit input, and
may render existing safe failures. It must not create a Code-specific public
error taxonomy or expose raw exceptions, model/runtime identity, transport
details, private topology, or request contents.

### File convenience remains separate

This decision authorizes only:

```text
prompt -> textual code response -> browser display
```

It does not decide or authorize a later caller/browser-side convenience such
as:

```text
textual response -> Download -> Save As -> file creation
```

Download, Save As, and browser filesystem API use are out of scope. This RFC
does not grant Home AI Cluster server-side file creation authority or treat a
free-form `ClusterResult` as a file contract. Any future file convenience needs
its own bounded investigation and decision.

## Rationale

The accepted `code` contract already represents the required semantic request,
bounded validation, routing eligibility, execution mechanics, textual result,
and absence of authority. The accepted loopback browser already represents the
required serving, origin, privacy, state, safe-failure, and attribution
boundaries. A fourth fixed view is therefore the smallest truthful connection
between two existing decisions.

Keeping Code fixed rather than generic protects the capability-centered design:
the browser explicitly requires one project-defined semantic capability and
does not become a UI for arbitrary capability names. Reusing `/v1/chat` avoids
duplicating the accepted ordered-message path or creating a misleading
code-specific HTTP contract. Rendering plain text preserves the line between
textual assistance and file or execution authority.

## Alternatives considered

### Leave the browser unchanged

The native `home-ai-cluster code` and `hac code` surfaces remain valid. This
does not provide the small loopback browser convenience addressed by this RFC.

### Add a generic capability browser UI

Rejected. It would turn a deliberately fixed client into a dynamic capability
surface, hide capability-specific decisions, and create a broader UI contract.

### Add `POST /v1/code`

Rejected. The existing `/v1/chat` route truthfully carries the accepted ordered
message `ClusterRequest(capability=code)` and retains authoritative validation.
A new route would duplicate that contract without a demonstrated need.

### Add an editor or file-saving workflow

Rejected. Editor behavior and file convenience introduce separate response,
browser, filesystem, and authority questions. Free-form textual results do not
establish a file or editing contract.

### Use the OpenAI-compatible process

Rejected. It is deliberately a separate Chat-only compatibility edge. Reusing
it would change the compatibility boundary rather than use the accepted native
Code request path.

## Trade-offs

The browser becomes modestly more convenient for one accepted text operation,
but it remains deliberately limited to four fixed views with no saved state,
remote browser access, editor, or operational control. Adding one tab and
handler is small implementation work, but it requires this RFC because it
expands a deliberately fixed browser contract. The explicit boundary prevents
convenience from silently becoming a generic coding interface or agent.

## Relationship to prior RFCs

RFC-0062 remains authoritative for loopback browser composition, launcher-owned
loopback exposure, same-origin behavior, fixed assets, privacy, safe failures,
API-only receiver compositions, and the non-dashboard shape. RFC-0070 extends
only its fixed view set from three views to four by adding Code.

RFC-0067 remains authoritative for `code` semantics, the ordered-message
`ClusterRequest`, free-form `ClusterResult`, the 65,536-byte aggregate bound,
routing, eligibility, static declarations, adapter and internal transport
reuse, node attribution, privacy, and absence of filesystem or execution
authority.

RFC-0070 does not supersede either RFC. It is the narrow additive decision that
connects their already accepted browser and textual-Code contracts.

## Impact

If accepted, the only architectural change is:

```text
RFC-0062 fixed browser surface
  Chat, Summarize, Classify
    ->
  Chat, Summarize, Classify, Code
```

The following remain unchanged: `code` capability semantics; `ClusterRequest`;
`ClusterResult`; the 65,536-byte bound; routing; eligibility; static capability
declarations; local-first selection; fallback; adapters; internal remote
transport; node attribution; OpenAI compatibility; API-only receiver
compositions; loopback exposure; persistence; filesystem authority; and
execution authority.

## Proof expectations

A later implementation proof must show:

1. the loopback browser exposes the fourth fixed Code view;
2. one real text-only Code request reaches native `/v1/chat` with explicit
   `capability=code`;
3. returned textual content and `node_id` attribution are displayed;
4. an over-limit input is rejected without execution;
5. one existing safe native failure is rendered safely;
6. page reload clears Code state;
7. API-only and LAN receiver compositions still do not expose the page;
8. compatibility remains Chat-only; and
9. no filesystem, file creation, shell, Git, tools, persistence, CORS, proxy,
   second process, or new endpoint exists.

Retained evidence must not include real prompts, generated source code, private
paths, machine names, private addresses, model/runtime identities, credentials,
or raw sensitive logs.

## Implementation boundary after acceptance

A later implementation PR may remain limited to one new fixed Code tab/panel,
one narrow submit handler, reuse of the existing browser request/result/failure
mechanics, focused browser tests, and privacy-safe proof material. It must make
no core, runtime, transport, API, compatibility, filesystem, or execution
architecture changes.

This RFC itself authorizes no implementation.

## Open questions

None within this narrow browser-view scope. A later browser-owned file
convenience requires a separate bounded investigation and decision.

## Decision

Pending.
