# RFC-0083: Bounded Ephemeral Browser Code Conversation

Status: Accepted

Date: 2026-08-23

Author: frian

## Summary

The fixed loopback browser Code view should be allowed to retain one ordered,
ephemeral Code conversation in current-page JavaScript and DOM memory. Each
submitted turn would send the complete successful Code conversation plus one
new user instruction through the existing native `POST /v1/chat` request with
explicit `capability=code`. A successful textual result would append one
assistant message; a failed pending turn would roll back without changing
earlier successful turns.

This narrowly amends RFC-0070's one-instruction, replaced-result interaction
shape. It does not change the `code` capability, `ClusterRequest`,
`ClusterResult`, routing, endpoint, browser exposure, or text-only authority
defined by RFC-0067, RFC-0062, and RFC-0070. It authorizes no implementation.

## Problem

RFC-0070 deliberately gives the browser Code view one instruction, one native
request, and one replaced textual result. That is sufficient for a first small
script request, but not for a bounded correction such as asking to change the
generated script to accept two arguments. The later request needs the earlier
instruction and generated result to be meaningful.

Retaining old entries only as visible browser output would not solve that
problem: sending only the newest instruction would leave the selected node
without the prior Code context. Requiring an operator to manually paste prior
content repeatedly is possible, but is unnecessary friction for the same
current-page interaction.

The project needs an explicit decision before changing RFC-0070's deliberately
one-shot browser Code interaction into a multi-turn request shape.

## Goals

This RFC proposes to:

* allow one current-page, ordered, browser-only Code conversation;
* send complete successful Code context on every later Code turn through the
  existing native `capability=code` path;
* preserve one ordinary native request per submitted turn and existing
  capability-centered routing;
* preserve RFC-0067's aggregate 65,536 UTF-8 byte input bound without
  truncation, summarization, or automatic pruning;
* retain plain-text result rendering and per-result `node_id` attribution;
* make pending-turn rollback and input restoration explicit; and
* preserve local-first, privacy, fixed-loopback, and text-only boundaries.

## Non-goals

This RFC does not authorize filesystem or repository access; file creation,
modification, upload, download, or Save As; `hac code-file` changes; Aider
changes; shell, command, test, Git, or generated-code execution; patches,
editors, syntax highlighting, Markdown rendering, or a patch viewer.

It does not authorize tools or function calling, agents, autonomous loops,
planning, retries, correction requests, web access, RAG, indexing, retrieval,
model or runtime selection, node affinity, sticky sessions, a new endpoint,
request/result type, transport shape, adapter method, or OpenAI-compatible
Code behavior.

It does not authorize LAN browser exposure, CORS, authentication, proxying, a
second browser process, persistence, cookies, localStorage, sessionStorage,
IndexedDB, browser-owned persistent cache, server sessions, a database,
prompt/response logging, content metrics, conversation identifiers, or
cross-tab/process synchronization.

`hac code`, `hac code-file`, `hac aider`, native APIs, compatibility,
Summarize, Classify, and Chat semantics remain unchanged. This RFC also does
not decide whether browser capability views may have simultaneous active
requests; existing global request-active behavior is a separate concern.

## Proposal

### Browser-only Code conversation

The fixed loopback Code view may keep exactly one ordered Code conversation in
ordinary current-page JavaScript and DOM memory. The first successful turn
remains:

```text
user instruction
  -> one native capability=code request
  -> one assistant textual result
```

A later turn becomes:

```text
prior ordered user/assistant messages
  + new user instruction
  -> one native capability=code request
  -> one new assistant textual result
```

Each submission sends exactly one ordinary same-origin request:

```text
POST /v1/chat
capability = code
```

No submitted turn automatically causes a second request, correction request,
retry, planning step, agent loop, or tool call.

### Conversation request contents

For every submitted turn, the browser constructs one ordered message list from
every previously successful Code `user` message, every corresponding successful
Code `assistant` result, and the new pending `user` instruction. It sends that
complete ordered list in the one native request.

The browser must not send only the newest instruction; summarize, silently omit,
truncate, prune, or otherwise rewrite old turns; invent a system message; or
transform an assistant result into a patch, file, editor, or other
representation. RFC-0067's existing `ClusterRequest` message roles and native
validation remain authoritative.

### Success, attribution, and routing

A valid existing textual `ClusterResult.content` becomes the next `assistant`
message in the ephemeral Code conversation. The existing `node_id` remains
visible as attribution for that individual assistant result. Successful turns
append in chronological user/assistant order.

The browser displays and appends every valid ordinary textual result unchanged,
even when that result makes the retained successful conversation too large for
any later RFC-0067-compliant request. This proposal adds no Code output-size
contract, response truncation, response summarization, partial display,
rejection of an otherwise valid `ClusterResult`, silent omission from later
context, or automatic removal of earlier successful turns.

Every turn remains an independent ordinary `capability=code` request. Existing
routing independently selects an eligible node for each turn; no node affinity,
sticky session, model selection, or same-node guarantee is introduced. A later
eligible node may therefore receive the earlier Code instructions and results
because the browser includes the complete current conversation. Existing
local-first selection, static declaration order, eligibility, fallback, and
transport behavior remain unchanged.

### Failure behavior

The new user instruction may be shown provisionally while its request is
active. If the request fails or returns an invalid ordinary result, the browser
removes only that provisional user message, preserves all earlier successful
Code turns, restores the failed instruction to the Code textarea when it has
not been replaced by newer operator input, and uses the existing safe error
presentation.

A failure is not a Code conversation entry. The browser adds no synthetic
assistant result and makes no retry or corrective request.

### Aggregate bound

RFC-0067's existing aggregate limit of 65,536 UTF-8 bytes applies to the whole
ordered Code message list on every turn: retained user messages, retained
assistant results, and the new user instruction. Before sending, the browser
should provide matching local validation, while native/core validation remains
authoritative.

If the candidate conversation exceeds that existing limit, the browser rejects
the new submission before network transmission. It retains the successful
conversation unchanged and keeps the new instruction for operator correction.
It must not truncate, summarize, prune, or discard earlier turns automatically.

This calculation occurs normally on the next attempted turn, including every
retained successful user message, every retained successful assistant result,
and the new user instruction. A valid assistant result can therefore leave the
current ephemeral Code conversation terminal for further turns under the
existing aggregate request bound. That is an accepted bounded trade-off, not an
execution failure and not permission to alter the successful result. The
operator may reload or close the page to discard the ephemeral conversation and
begin again. This RFC adds no conversation-reset control, output bound, or
conversation-management system.

### Presentation

The Code view should present its ephemeral conversation above its composer,
using the existing plain-text, bounded, independently scrollable interaction
demonstrated by Chat where appropriate. It keeps chronological user/assistant
order, reveals the newest entry, keeps the composer readily accessible,
preserves useful keyboard focus and per-result node attribution, and remains
usable at narrow viewport widths. The composer must not overlay or hide
conversation content.

This does not authorize a generic conversation component, capability-driven UI
registry, frontend framework, Markdown renderer, syntax highlighter, code
editor, or broad browser refactor. Exact CSS values and status wording are
later implementation details.

### Ephemeral state and privacy

The Code conversation exists only in ordinary current-page memory. Reloading
or closing the page may discard it. It adds no cookie, localStorage,
sessionStorage, IndexedDB, browser-owned persistent cache, server session,
database, request-history expansion, prompt/response log, content metric,
conversation identifier, or cross-tab/process synchronization.

This state is distinct from RFC-0035's explicit prompt-free operator request
history. RFC-0035 remains an operator inspection surface and gains neither
Code conversation content nor automatic ordinary-browser request records.

### Relationship to RFC-0070 and prior decisions

RFC-0083 amends only RFC-0070's browser Code interaction shape:

```text
one instruction -> one replaced result
```

becomes:

```text
one ephemeral ordered Code conversation
  -> one native code request per submitted turn
  -> one appended textual assistant result
```

RFC-0070 remains authoritative for the fixed Code view; same-origin,
loopback-only exposure; native `/v1/chat`; explicit `capability=code`;
plain-text results; absence of filesystem and execution authority; fixed
browser composition; API-only receiver behavior; and compatibility remaining
Chat-only.

RFC-0067 remains authoritative for Code semantics, request representation,
aggregate byte bound, eligibility, routing, and text-only authority. RFC-0080
and RFC-0081 remain authoritative only for their separate `code-file` caller
edge and are unchanged. RFC-0072 remains the separate bounded Aider caller
edge and is unchanged.

## Rationale

One ordered current-page conversation is the smallest truthful way to make a
Code follow-up meaningful: it retains exactly the context needed by the next
native request, without creating a server session, browser persistence, or a
general coding-agent lifecycle. The complete-list request makes the state
ownership visible: browser memory owns the transient context, and the existing
native request continues to own validation, routing, execution, and safe
results.

The existing aggregate limit is the necessary bound. Refusing an over-limit
candidate leaves the operator in control and avoids hidden history policy.
Appending only valid results and rolling back a failed pending message keeps a
conversation an honest record of successful exchanges rather than an error
ledger.

## Alternatives considered

### Retain the one-shot Code view

Rejected for this proposal. It remains the smallest existing surface, but does
not support the demonstrated contextual follow-up need.

### Retain multiple results visually but send only the latest instruction

Rejected. Visible history does not supply earlier instruction/result context to
the newly selected eligible node, so it would make the conversation appearance
misleading.

### Require the operator to paste generated code into every follow-up

Rejected. It preserves existing behavior but repeatedly asks the operator to
reconstruct context that is already present in ephemeral page memory.

### Automatically summarize or truncate earlier turns

Rejected. Either behavior changes content without operator direction and adds
summary quality, information-loss, and history-policy decisions. The existing
aggregate bound should instead reject the candidate intact.

### Use Aider for every iterative Code interaction

Rejected. RFC-0072's optional Aider caller edge has a distinct external
subprocess, target-edit, and at-most-two-request lifecycle. It is not a smaller
browser text-conversation boundary.

### Use `hac code-file` instead

Rejected. RFC-0080 and RFC-0081 are explicit caller-owned whole-file edges
with selected filesystem authority. They do not replace a browser-only,
text-only conversation.

### Introduce persistent or server-owned Code sessions

Rejected. Sessions require identifiers, lifecycle, retention, privacy,
concurrency, and recovery decisions beyond the current-page use case.

### Introduce a generic conversational-capability frontend abstraction

Rejected. Only Code needs this new interaction shape, and a generic component
or registry would broaden the fixed browser surface without a demonstrated
need.

## Trade-offs

Later turns can contain increasing context, consume more local inference work,
and eventually reach the existing aggregate bound. A new eligible node may see
all currently retained Code content. The browser implementation would need a
small separate ephemeral message sequence and focused rollback/validation
coverage.

In particular, one valid assistant response can make the current ephemeral Code
conversation terminal for later turns because RFC-0067 bounds request-message
input, not Code output. The response remains displayed and retained unchanged;
the next instruction is locally non-sendable until the operator discards the
ephemeral conversation by reloading or closing the page.

Those costs are bounded by one page, one ordered conversation, existing message
roles and byte validation, one request per turn, no persistence, no automatic
history modification, and unchanged capability-centered routing. They are
smaller and clearer than a session, agent, file-edit, or generic frontend
system.

## Impact and proof expectations

Acceptance would authorize only a later, separate implementation PR. That
implementation must not change core Code semantics, APIs, routing, adapters,
transport, compatibility, filesystem authority, execution authority, or
browser exposure.

Focused proof would need to demonstrate:

1. first-turn Code behavior remains valid;
2. a second turn includes the first user instruction and first assistant result;
3. successful turns append in chronological order;
4. each turn sends exactly one native `capability=code` request;
5. aggregate-size validation includes retained assistant results;
6. an over-limit follow-up is rejected without truncation or network transmission;
7. a valid assistant result that makes later candidate input over-limit remains
   appended and displayed unchanged with its attribution;
8. a later submitted instruction is rejected before network transmission while
   that successful conversation remains unchanged and the instruction remains
   available to the operator;
9. that terminal condition adds no truncation, pruning, output limit, or
   automatic reset;
10. failure rolls back only the pending turn and restores its instruction;
11. previous successful turns remain intact after failure;
12. per-response node attribution remains visible;
13. reload clears Code state;
14. no persistence or server session exists;
15. routing and node selection remain unchanged and non-sticky;
16. Chat, Summarize, and Classify remain unchanged;
17. Code remains plain text with no filesystem or execution authority; and
18. narrow viewport and keyboard behavior remain usable.

Retained proof material must not contain real prompts, generated private code,
private paths, node addresses, model/runtime identities, credentials, or other
sensitive content.

## Open questions

None within this bounded proposal. Exact layout values, status wording, and
local validation implementation are later implementation details. Any broader
conversation lifecycle, persistence, history policy, UI framework, routing
rule, or authority expansion requires a separate decision.

## Decision

Accepted. RFC-0083 narrowly amends RFC-0070 so the fixed loopback Code view
may retain one bounded, ephemeral ordered Code conversation and send its
complete successful context in one existing native `capability=code` request
per submitted turn. RFC-0067's existing aggregate request bound remains
authoritative; no persistence, filesystem, execution, routing, API, or browser
exposure boundary changes.
