# RFC-0155: Ephemeral Desktop Chat Conversation

Status: Accepted

Date: 2026-10-14

Author: frian

## Summary

RFC-0151 establishes an independent PySide6 / Qt Widgets Desktop thin client
for ordinary Chat.  It deliberately requires each Send to contain exactly one
new user message, even when earlier exchanges remain visible.  This RFC
proposes a narrow amendment to that Desktop-specific requirement: one Desktop
window should instead own one ephemeral, in-memory Chat conversation by
default.

Each Send remains one independent ordinary `POST /v1/chat` request with
`capability=chat`.  The first request contains one user message.  A later
request contains the ordered successful user/assistant pairs from that window,
followed by the new user message.  No session, conversation identifier,
endpoint, `ClusterRequest` or `ClusterResult` change, persistent store, or
sticky routing is introduced.

This accepted decision authorizes a separate Desktop implementation only.
It makes no change to HAC core.

## Existing authority and problem

RFC-0151 remains authoritative for the independent repository and process
boundary, PySide6 / Qt Widgets first window, direct ordinary loopback client,
proxy bypass, redirect rejection, one outstanding request, client-owned wait,
safe failures, and HAC authority.  Its current one-new-user-message-per-Send
rule intentionally prevents its visible transcript from becoming hidden
context.  That rule makes ordinary follow-up questions lack the context the
window displays.

RFC-0045 establishes the ordinary one-shot native Chat request.  RFC-0060
keeps the client wait client-owned, and RFC-0082 makes no promise that a
caller which stops waiting stopped downstream work.  RFC-0087 provides the
closest Chat precedent: an ephemeral CLI-owned successful-exchange sequence,
one independent native request per turn, failed-turn rollback, and a 65,536
UTF-8-byte aggregate candidate bound.  RFC-0062 provides current-page
ephemeral browser Chat precedent; RFC-0083 provides the corresponding bounded
browser conversation pattern.  RFC-0134 is a separate, explicitly authorized
automatic External Information behavior and does not authorize Desktop
conversation or disclosure changes.

Those precedents do not amend Desktop behavior.  A new RFC is needed because
including earlier prompt and response content changes the Desktop disclosure
and lifecycle contract.

## Proposed decision

### Window-owned ephemeral conversation

Desktop operates in conversational Chat mode by default.  There is no
single-request/conversation selector.  One running Desktop window owns one
ordered sequence of complete successful Chat exchanges in its process memory.
Closing the process discards it.

The state is not owned by HAC, a node, runtime, adapter, server, or transport.
It creates no server session, conversation ID, cookie, database, file, export,
telemetry, prompt log, response log, synchronization, restart recovery, or
multi-window coordination.  This is not a claim of secure memory erasure,
which Python and Qt cannot guarantee.

### Ordinary request contract and disclosure

Every Send constructs exactly one existing ordinary request to `POST /v1/chat`
with `capability=chat`.  The first Send contains exactly the new `user`
message.  A later Send contains, in chronological order, every retained
successful user message, its corresponding retained assistant response, and
the new user message.  Desktop neither adds a system message nor transforms,
summarizes, truncates, prunes, reconstructs, or retries content.

This keeps each turn an independent HAC request.  HAC retains capability
admission, routing, node selection, runtime and adapter selection, execution,
results, and failure classification.  No affinity follows from the
conversation: a later eligible node may receive earlier content only because
Desktop explicitly included it in that new request.  Desktop must not infer
routing or availability from the conversation or add another endpoint,
generic session API, or generic Chat SDK.

The retained content must be the original submitted user content and original
validated `ClusterResult.content`.  It must not be reconstructed from
`QTextEdit.toPlainText()`, rendered Markdown, clipboard data, or visible widget
text.  Markdown presentation remains presentation only under the existing
Desktop decision.

### Successful and failed turns

Only a complete successful user/assistant pair is committed to the ordered
conversation after Desktop has received a successful HTTP response valid under
the existing native `ClusterResult` contract.  Visible messages and request
status presentation are separate from retained conversational context.

Network failure, unsuccessful HTTP status, invalid `ClusterResult`, client
timeout, and Stop waiting leave all earlier successful pairs intact; they do
not retain the submitted user message, invent an assistant message, or retry.
They retain the existing bounded safe failure presentation.  A late response
for a request after timeout or Stop waiting is abandoned presentation and
conversation state: it cannot append a pair, mutate state, or affect a later
request.

An otherwise valid result with empty `ClusterResult.content` remains an
ordinary one-shot success under the existing contract, but cannot represent a
retained assistant `ChatMessage`.  Consistent with RFC-0087, this proposal
treats it as a Desktop conversational-turn failure: preserve earlier context,
retain neither side of the submitted turn, use the existing safe invalid-result
presentation, and do not retry.  This narrower representability rule changes
neither `ClusterResult` nor one-shot semantics.

### Aggregate context bound

Desktop adopts RFC-0087's existing interactive-client convention of
**65,536 UTF-8 bytes of aggregate message content**.  It is a
Desktop-owned candidate-request bound, not a universal native Chat protocol or
runtime-context-window limit.

Before sending, Desktop counts the UTF-8 bytes of all retained successful user
messages, all retained successful assistant messages, and the new user
message.  If the aggregate exceeds the bound, it rejects the candidate locally,
sends no HAC request, leaves earlier context unchanged, and preserves the new
input for correction.  It must not truncate, summarize, prune, or rewrite any
content.  A successful assistant response may make a later candidate impossible
within the bound; that response remains intact, and New conversation is the
explicit fresh start.  The proposal imposes no output limit, token counting, or
runtime context-window discovery.

Adopting the CLI convention is appropriate as a small, familiar finite
Desktop-owned disclosure bound while engines remain independent.  It is a
client-owned limit, not evidence that all Chat clients or HAC itself already
have this limit.

### New conversation

Desktop adds one explicit **New conversation** action.  It discards the
window's retained successful context and clears the visible conversation and
request-status messages, while preserving unsent input so an operator can
reuse or edit it deliberately.  The next Send is therefore a fresh first Send.

For the first implementation, this RFC proposes disabling New conversation
while a Desktop request awaits completion.  The operator must wait for its
terminal outcome or choose Stop waiting first.  After timeout or Stop waiting,
New conversation is available.  An abandoned late result is tied to the old
request and cannot repopulate either the old display or the new conversation.
This simple policy avoids ambiguous commitment and stale-callback ownership;
its exact UI wording remains a Desktop implementation detail.

### Preserved Desktop behavior and exclusions

This proposal preserves native Qt Markdown presentation, resource blocking and
plain-text fallback, centered conversation layout, message-width limits, 130%
line spacing, selection and clipboard behavior, active capability presentation,
one outstanding request, client-owned timeout, Stop waiting, no automatic
retry, proxy bypass, and redirect rejection.  It adds no capability,
Summarize, External Information control, streaming, agent or tool behavior.

It explicitly excludes server-owned sessions; persistence; databases;
conversation IDs; lists, tabs, saved history, or management infrastructure;
multi-window synchronization; node/model/runtime affinity; automatic
summarization, pruning, truncation, or rewriting; token counting;
context-window discovery; new HAC endpoints; generic SDKs; and any additional
networking or cloud disclosure.

## Relationship to RFC-0151

This RFC replaces RFC-0151's Desktop-specific requirements that
each Send contain exactly one newly submitted user message, that displayed
exchanges never become context, and that the visible Desktop window is not a
multi-turn conversation.  The replacement is this RFC's complete
successful-context rule.  RFC-0151's falsifiable implementation proof item 5
is likewise replaced by this RFC's first-turn and subsequent-turn proof
expectations.

RFC-0151's exclusion of server-owned sessions and persistent conversations
remains authoritative: this Desktop-owned ephemeral conversation is not a
server session, and every Send remains one independent ordinary HAC request.
All other RFC-0151 boundaries remain unchanged, including the independent
Desktop repository and process boundary and HAC authority.  RFC-0087 and
RFC-0062 are precedents, not automatic authorization for Desktop.  The
existing native Chat contract remains authoritative.

## Alternatives considered

| Alternative | Assessment |
| --- | --- |
| Keep Desktop one-shot only | Preserves the current explicit rule, but leaves the displayed transcript unable to inform a follow-up request. |
| Add a one-shot/conversation selector | Makes disclosure mode visible but creates a persistent mode choice for an otherwise ordinary Chat window and increases state and test surface. |
| Client-owned ephemeral conversation | Accepted. Keeps the smallest lifecycle in the visible owning window while preserving ordinary requests and independent routing. |
| Server-owned sessions | Requires identifiers, retention, lifecycle, concurrency, recovery, and privacy policy beyond this need. |
| Persistent Desktop conversations | Adds storage, retention, recovery, and history-management authority contrary to the local ephemeral scope. |
| Automatic truncation or summarization | Hides content loss or rewrites operator content and introduces policy and model behavior not needed for a clear local refusal. |

## Consequences and implementation boundary

Later turns disclose their retained earlier context to whichever eligible HAC
path independently receives the new ordinary request.  They can be larger and
may reach the proposed local bound.  The benefit is a truthful conversational
experience without giving Desktop orchestration authority or creating retained
history.

Implementation belongs only in the independent Desktop repository
and should use small window-owned in-memory state, not a reusable conversation
framework.  It must not modify HAC models, routes, routing, topology,
adapters, runtimes, Configuration, browser behavior, or compatibility behavior.
If implementation exposes a missing native contract, that requirement returns
to HAC architecture rather than receiving a Desktop workaround.

## Falsifiable implementation proof

A later implementation must demonstrate at minimum that:

1. the first Send issues one ordinary `chat` request containing exactly one user message;
2. the second successful Send includes the first original user/assistant pair and second user message in order;
3. failed, timed-out, stopped, invalid, and empty-content turns do not enter future context;
4. late results cannot mutate a newer conversation or its presentation;
5. New conversation resets the approved state, cannot leak old context, and is unavailable during an outstanding wait;
6. the aggregate byte calculation is local, includes all candidate content, rejects before transport, and preserves input and prior context;
7. original assistant Markdown is sent unchanged despite rendering;
8. each Send causes no extra HAC request, and routing remains independent and non-sticky;
9. no persistence, session, conversation ID, additional disclosure path, or HAC contract change appears; and
10. existing Desktop features and Linux and Windows regression coverage remain functional.

## Confirmed owner choices

The project owner has confirmed these proposal details: the aggregate bound is
exactly 65,536 UTF-8 bytes of message content; New conversation clears the
visible conversation and request-status messages while preserving unsent input;
and it is unavailable while a request awaits completion.  The operator may
wait or choose Stop waiting; after timeout or Stop waiting, New conversation
is available and an abandoned late response cannot repopulate or mutate it.

These confirmed choices are part of this accepted Desktop conversation contract.

## Decision

Accepted. This RFC authorizes a later, separate implementation of the bounded
window-owned Desktop conversation described above. It narrowly amends RFC-0151
as specified, preserves all other HAC authority and client boundaries, and
does not itself implement any Desktop changes or modify HAC core.
